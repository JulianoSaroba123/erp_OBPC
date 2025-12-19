"""
Utilitário de Conciliação Bancária Avançada para OBPC
Suporte para importação de extratos CSV/XLSX e conciliação automática inteligente
"""

try:
    import pandas as pd
    import numpy as np
except Exception:
    pd = None
    np = None
from datetime import datetime, timedelta
import re
import difflib
import hashlib
from typing import List, Dict, Tuple, Optional
from flask import current_app
import os

from app.financeiro.financeiro_model import Lancamento, ConciliacaoHistorico, ConciliacaoPar, ImportacaoExtrato
from app.extensoes import db


class ConciliadorAvancado:
    """Classe principal para conciliação bancária inteligente"""
    
    def __init__(self):
        self.regras_conciliacao = [
            self._regra_exata,
            self._regra_valor_data_similar,
            self._regra_valor_descricao_similar,
            self._regra_valor_proxima_data,
            self._regra_descricao_fuzzy
        ]
        
        self.scores_minimos = {
            'exata': 1.0,
            'valor_data_similar': 0.95,
            'valor_descricao_similar': 0.85,
            'valor_proxima_data': 0.80,
            'descricao_fuzzy': 0.75
        }
    
    def conciliar_automatico(self, usuario: str = "Sistema") -> Dict:
        """
        Executa conciliação automática entre lançamentos manuais e importados
        """
        inicio = datetime.now()
        resultado = {
            'conciliados': 0,
            'pares_criados': [],
            'tempo_execucao': 0,
            'regras_aplicadas': {},
            'log': []
        }
        
        try:
            # Buscar lançamentos não conciliados
            manuais = Lancamento.query.filter_by(origem='manual', conciliado=False).all()
            importados = Lancamento.query.filter_by(origem='importado', conciliado=False).all()
            
            if not manuais or not importados:
                resultado['log'].append("Nenhum lançamento disponível para conciliação")
                return resultado
            
            # Criar histórico
            historico = ConciliacaoHistorico(
                usuario=usuario,
                tipo_conciliacao='automatica',
                total_pendentes=len(manuais) + len(importados)
            )
            db.session.add(historico)
            db.session.flush()
            
            # Aplicar regras de conciliação
            for manual in manuais:
                if manual.conciliado:
                    continue
                    
                melhor_match = None
                melhor_score = 0
                melhor_regra = ""
                
                for importado in importados:
                    if importado.conciliado:
                        continue
                    
                    # Aplicar todas as regras
                    for regra in self.regras_conciliacao:
                        score, regra_nome = regra(manual, importado)
                        
                        if score > melhor_score and score >= self.scores_minimos.get(regra_nome, 0.7):
                            melhor_match = importado
                            melhor_score = score
                            melhor_regra = regra_nome
                
                # Se encontrou match válido, criar par
                if melhor_match and melhor_score >= 0.7:
                    par = self._criar_par_conciliacao(
                        manual, melhor_match, melhor_score, 
                        melhor_regra, usuario, historico.id
                    )
                    
                    resultado['pares_criados'].append(par.to_dict())
                    resultado['conciliados'] += 1
                    
                    # Atualizar contadores de regras
                    if melhor_regra not in resultado['regras_aplicadas']:
                        resultado['regras_aplicadas'][melhor_regra] = 0
                    resultado['regras_aplicadas'][melhor_regra] += 1
                    
                    resultado['log'].append(
                        f"Conciliado: Manual {manual.id} <-> Importado {melhor_match.id} "
                        f"(Score: {melhor_score:.2f}, Regra: {melhor_regra})"
                    )
            
            # Finalizar histórico
            historico.total_conciliados = resultado['conciliados']
            historico.tempo_execucao = (datetime.now() - inicio).total_seconds()
            historico.regras_aplicadas = str(resultado['regras_aplicadas'])
            
            db.session.commit()
            
            resultado['tempo_execucao'] = historico.tempo_execucao
            resultado['historico_id'] = historico.id
            
        except Exception as e:
            db.session.rollback()
            resultado['erro'] = str(e)
            resultado['log'].append(f"Erro durante conciliação: {str(e)}")
        
        return resultado
    
    def _criar_par_conciliacao(self, manual: Lancamento, importado: Lancamento, 
                              score: float, regra: str, usuario: str, historico_id: int) -> ConciliacaoPar:
        """Cria par de conciliação e atualiza status dos lançamentos"""
        
        # Marcar como conciliados
        manual.conciliado = True
        manual.conciliado_em = datetime.now()
        manual.conciliado_por = usuario
        
        importado.conciliado = True
        importado.conciliado_em = datetime.now()
        importado.conciliado_por = usuario
        
        # Criar par
        par = ConciliacaoPar(
            historico_id=historico_id,
            lancamento_manual_id=manual.id,
            lancamento_importado_id=importado.id,
            score_similaridade=score,
            regra_aplicada=regra,
            metodo_conciliacao='automatico',
            usuario=usuario
        )
        
        db.session.add(par)
        return par
    
    def _regra_exata(self, manual: Lancamento, importado: Lancamento) -> Tuple[float, str]:
        """Regra para match exato: mesma data, valor e tipo"""
        if (manual.data == importado.data and 
            abs(manual.valor - importado.valor) < 0.01 and
            manual.tipo == importado.tipo):
            return 1.0, "exata"
        return 0.0, "exata"
    
    def _regra_valor_data_similar(self, manual: Lancamento, importado: Lancamento) -> Tuple[float, str]:
        """Regra para valor igual e data próxima (±3 dias)"""
        if abs(manual.valor - importado.valor) < 0.01 and manual.tipo == importado.tipo:
            diff_dias = abs((manual.data - importado.data).days)
            if diff_dias <= 3:
                score = 0.95 - (diff_dias * 0.05)  # Desconta 5% por dia de diferença
                return score, "valor_data_similar"
        return 0.0, "valor_data_similar"
    
    def _regra_valor_descricao_similar(self, manual: Lancamento, importado: Lancamento) -> Tuple[float, str]:
        """Regra para valor igual e descrição similar"""
        if abs(manual.valor - importado.valor) < 0.01 and manual.tipo == importado.tipo:
            sim_descricao = self._calcular_similaridade_descricao(
                manual.descricao or "", importado.descricao or ""
            )
            if sim_descricao >= 0.7:
                score = 0.85 + (sim_descricao - 0.7) * 0.1
                return min(score, 0.95), "valor_descricao_similar"
        return 0.0, "valor_descricao_similar"
    
    def _regra_valor_proxima_data(self, manual: Lancamento, importado: Lancamento) -> Tuple[float, str]:
        """Regra para valor similar (±5%) e data próxima (±7 dias)"""
        if manual.tipo == importado.tipo:
            diff_valor = abs(manual.valor - importado.valor) / max(manual.valor, importado.valor)
            diff_dias = abs((manual.data - importado.data).days)
            
            if diff_valor <= 0.05 and diff_dias <= 7:
                score = 0.80 - (diff_valor * 2) - (diff_dias * 0.01)
                return max(score, 0.7), "valor_proxima_data"
        return 0.0, "valor_proxima_data"
    
    def _regra_descricao_fuzzy(self, manual: Lancamento, importado: Lancamento) -> Tuple[float, str]:
        """Regra para descrição muito similar (fuzzy matching)"""
        if manual.tipo == importado.tipo:
            sim_descricao = self._calcular_similaridade_descricao(
                manual.descricao or "", importado.descricao or ""
            )
            if sim_descricao >= 0.85:
                diff_valor = abs(manual.valor - importado.valor) / max(manual.valor, importado.valor)
                if diff_valor <= 0.1:  # Valor até 10% diferente
                    score = 0.75 + (sim_descricao - 0.85) * 0.2
                    return min(score, 0.90), "descricao_fuzzy"
        return 0.0, "descricao_fuzzy"
    
    def _calcular_similaridade_descricao(self, desc1: str, desc2: str) -> float:
        """Calcula similaridade entre duas descrições usando múltiplas técnicas"""
        if not desc1 or not desc2:
            return 0.0
        
        # Normalizar textos
        desc1_norm = re.sub(r'[^\w\s]', '', desc1.lower().strip())
        desc2_norm = re.sub(r'[^\w\s]', '', desc2.lower().strip())
        
        if desc1_norm == desc2_norm:
            return 1.0
        
        # Similaridade usando difflib
        seq_match = difflib.SequenceMatcher(None, desc1_norm, desc2_norm)
        similarity = seq_match.ratio()
        
        # Bonus para palavras-chave em comum
        palavras1 = set(desc1_norm.split())
        palavras2 = set(desc2_norm.split())
        
        if palavras1 and palavras2:
            palavras_comuns = len(palavras1.intersection(palavras2))
            total_palavras = len(palavras1.union(palavras2))
            bonus_palavras = palavras_comuns / total_palavras * 0.2
            similarity += bonus_palavras
        
        return min(similarity, 1.0)


class ImportadorExtrato:
    """Classe para importar extratos bancários de arquivos CSV/XLSX"""
    
    def __init__(self):
        self.formatos_suportados = {
            'csv': self._ler_csv,
            'xlsx': self._ler_excel,
            'xls': self._ler_excel
        }
        
        self.mapeamentos_banco = {
            'bradesco': self._mapear_bradesco,
            'itau': self._mapear_itau,
            'santander': self._mapear_santander,
            'bb': self._mapear_bb,
            'caixa': self._mapear_caixa,
            'nubank': self._mapear_nubank,
            'pagbank': self._mapear_pagbank,
            'generico': self._mapear_generico
        }
    
    def importar_arquivo(self, arquivo_path: str, banco: str = 'generico', 
                        usuario: str = 'Sistema') -> Dict:
        """
        Importa arquivo de extrato bancário
        """
        resultado = {
            'sucesso': False,
            'total_registros': 0,
            'registros_processados': 0,
            'registros_duplicados': 0,
            'registros_erro': 0,
            'erros': [],
            'importacao_id': None
        }
        
        try:
            # Verificar se arquivo já foi importado
            hash_arquivo = self._calcular_hash_arquivo(arquivo_path)
            importacao_existente = ImportacaoExtrato.query.filter_by(hash_arquivo=hash_arquivo).first()
            
            if importacao_existente:
                resultado['erros'].append("Arquivo já foi importado anteriormente")
                return resultado
            
            # Ler arquivo
            extensao = arquivo_path.split('.')[-1].lower()
            if extensao not in self.formatos_suportados:
                resultado['erros'].append(f"Formato {extensao} não suportado")
                return resultado
            
            df = self.formatos_suportados[extensao](arquivo_path)
            
            # Mapear colunas do banco
            if banco not in self.mapeamentos_banco:
                banco = 'generico'
            
            df_mapeado = self.mapeamentos_banco[banco](df)
            
            # Criar registro de importação
            importacao = ImportacaoExtrato(
                nome_arquivo=os.path.basename(arquivo_path),
                hash_arquivo=hash_arquivo,
                banco=banco,
                usuario=usuario,
                total_registros=len(df_mapeado),
                status='processando'
            )
            db.session.add(importacao)
            db.session.flush()
            
            # Processar registros
            for index, row in df_mapeado.iterrows():
                try:
                    sucesso = self._processar_registro(row, banco, importacao.id)
                    if sucesso:
                        resultado['registros_processados'] += 1
                    else:
                        resultado['registros_duplicados'] += 1
                        
                except Exception as e:
                    resultado['registros_erro'] += 1
                    resultado['erros'].append(f"Linha {index + 1}: {str(e)}")
            
            # Finalizar importação
            importacao.registros_processados = resultado['registros_processados']
            importacao.registros_duplicados = resultado['registros_duplicados']
            importacao.registros_erro = resultado['registros_erro']
            importacao.status = 'concluido'
            importacao.log_detalhado = '\n'.join(resultado['erros'])
            
            resultado['total_registros'] = len(df_mapeado)
            resultado['sucesso'] = True
            resultado['importacao_id'] = importacao.id
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            resultado['erros'].append(f"Erro geral: {str(e)}")
        
        return resultado
    
    def _calcular_hash_arquivo(self, arquivo_path: str) -> str:
        """Calcula hash SHA256 do arquivo"""
        sha256_hash = hashlib.sha256()
        with open(arquivo_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _ler_csv(self, arquivo_path: str):
        """Lê arquivo CSV com encoding automático"""
        if pd is None:
            raise ImportError("pandas é necessário para processar arquivos CSV")
        
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                return pd.read_csv(arquivo_path, encoding=encoding, sep=';')
            except:
                try:
                    return pd.read_csv(arquivo_path, encoding=encoding, sep=',')
                except:
                    continue
        
        raise ValueError("Não foi possível ler o arquivo CSV")
    
    def _ler_excel(self, arquivo_path: str):
        """Lê arquivo Excel"""
        if pd is None:
            raise ImportError("pandas é necessário para processar arquivos Excel")
        return pd.read_excel(arquivo_path)
    
    def _processar_registro(self, row, banco: str, importacao_id: int) -> bool:
        """Processa um registro individual do extrato"""
        try:
            # Criar lançamento
            lancamento = Lancamento(
                data=row['data'],
                tipo=row['tipo'],
                descricao=row['descricao'],
                valor=abs(float(row['valor'])),
                conta='Banco',
                origem='importado',
                banco_origem=banco,
                documento_ref=row.get('documento', None)
            )
            
            # Gerar hash de duplicata
            temp_hash = hashlib.sha256(
                f"{lancamento.data.strftime('%Y-%m-%d')}|{lancamento.valor:.2f}|{lancamento.descricao.strip().lower()}".encode()
            ).hexdigest()
            lancamento.hash_duplicata = temp_hash
            
            # Verificar duplicata usando query direta
            try:
                duplicata_existente = db.session.query(Lancamento).filter(
                    Lancamento.hash_duplicata == temp_hash
                ).first()
                
                if duplicata_existente:
                    current_app.logger.info(f"Registro duplicado encontrado: {lancamento.descricao}")
                    return False  # Registro duplicado
                    
            except Exception as dup_error:
                current_app.logger.warning(f"Erro ao verificar duplicata, prosseguindo: {dup_error}")
            
            # Salvar lançamento
            db.session.add(lancamento)
            db.session.commit()
            
            current_app.logger.info(f"Lançamento importado: {lancamento.descricao} - R$ {lancamento.valor}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Erro ao processar registro: {str(e)}")
            db.session.rollback()
            raise Exception(f"Erro ao processar registro: {str(e)}")
    
    def _mapear_generico(self, df):
        """Mapeamento genérico - assume colunas padrão"""
        colunas_esperadas = ['data', 'descricao', 'valor', 'tipo']
        colunas_df = df.columns.str.lower()
        
        mapeamento = {}
        
        # Tentar mapear automaticamente
        for col_esperada in colunas_esperadas:
            for col_df in colunas_df:
                if col_esperada in col_df or col_df in col_esperada:
                    mapeamento[col_esperada] = df.columns[colunas_df.tolist().index(col_df)]
                    break
        
        # Aplicar mapeamento
        df_mapeado = pd.DataFrame()
        for col_nova, col_original in mapeamento.items():
            df_mapeado[col_nova] = df[col_original]
        
        # Processar dados
        df_mapeado['data'] = pd.to_datetime(df_mapeado['data']).dt.date
        df_mapeado['valor'] = pd.to_numeric(df_mapeado['valor'], errors='coerce')
        
        # Determinar tipo baseado no valor
        df_mapeado['tipo'] = df_mapeado['valor'].apply(
            lambda x: 'Entrada' if x > 0 else 'Saída'
        )
        
        return df_mapeado.dropna()
    
    def _mapear_bradesco(self, df):
        """Mapeamento específico para extratos do Bradesco"""
        mapeamento = {
            'data': 'Data',
            'descricao': 'Histórico',
            'valor': 'Valor',
            'documento': 'Número'
        }
        
        df_mapeado = pd.DataFrame()
        for col_nova, col_original in mapeamento.items():
            if col_original in df.columns:
                df_mapeado[col_nova] = df[col_original]
        
        # Processar dados do Bradesco
        df_mapeado['data'] = pd.to_datetime(df_mapeado['data']).dt.date
        df_mapeado['valor'] = pd.to_numeric(df_mapeado['valor'], errors='coerce')
        df_mapeado['tipo'] = df_mapeado['valor'].apply(
            lambda x: 'Entrada' if x > 0 else 'Saída'
        )
        
        return df_mapeado.dropna()
    
    def _mapear_itau(self, df):
        """Mapeamento específico para extratos do Itaú"""
        return self._mapear_generico(df)  # Implementar específico se necessário
    
    def _mapear_santander(self, df):
        """Mapeamento específico para extratos do Santander"""
        return self._mapear_generico(df)
    
    def _mapear_bb(self, df):
        """Mapeamento específico para extratos do Banco do Brasil"""
        return self._mapear_generico(df)
    
    def _mapear_caixa(self, df):
        """Mapeamento específico para extratos da Caixa"""
        return self._mapear_generico(df)
    
    def _mapear_nubank(self, df):
        """Mapeamento específico para extratos do Nubank"""
        return self._mapear_generico(df)
    
    def _mapear_pagbank(self, df):
        """Mapeamento específico para extratos do PagBank"""
        # PagBank geralmente tem formato: Data, Descrição, Valor, Saldo
        mapeamento = {
            'data': 'Data',
            'descricao': 'Descrição',
            'valor': 'Valor',
            'saldo': 'Saldo'
        }
        
        # Tentar mapear com nomes alternativos comuns do PagBank
        colunas_df = df.columns.str.lower()
        mapeamento_alternativo = {
            'data': ['data', 'dt_transacao', 'data_transacao', 'date'],
            'descricao': ['descrição', 'descricao', 'histórico', 'historico', 'description'],
            'valor': ['valor', 'vlr_transacao', 'valor_transacao', 'amount'],
            'saldo': ['saldo', 'saldo_final', 'balance']
        }
        
        df_mapeado = pd.DataFrame()
        
        # Mapear colunas
        for col_nova, col_opcoes in mapeamento_alternativo.items():
            col_encontrada = None
            for opcao in col_opcoes:
                for col_df in df.columns:
                    if opcao in col_df.lower():
                        col_encontrada = col_df
                        break
                if col_encontrada:
                    break
            
            if col_encontrada:
                df_mapeado[col_nova] = df[col_encontrada]
        
        # Se não conseguiu mapear, tentar método genérico
        if df_mapeado.empty:
            return self._mapear_generico(df)
        
        # Processar dados do PagBank
        df_mapeado['data'] = pd.to_datetime(df_mapeado['data'], errors='coerce').dt.date
        df_mapeado['valor'] = pd.to_numeric(df_mapeado['valor'], errors='coerce')
        
        # PagBank pode ter valores positivos e negativos
        # Determinar tipo baseado no sinal do valor
        df_mapeado['tipo'] = df_mapeado['valor'].apply(
            lambda x: 'Entrada' if x > 0 else 'Saída'
        )
        
        # Adicionar documento de referência se disponível
        if 'saldo' in df_mapeado.columns:
            df_mapeado['documento'] = 'PagBank-' + df_mapeado.index.astype(str)
        
        return df_mapeado.dropna(subset=['data', 'valor'])


class GeradorRelatorios:
    """Gerador de relatórios de conciliação bancária"""
    
    @staticmethod
    def gerar_dashboard_indicadores() -> Dict:
        """Gera indicadores para dashboard de conciliação"""
        
        # Estatísticas gerais
        total_lancamentos = Lancamento.query.count()
        total_importados = Lancamento.query.filter_by(origem='importado').count()
        total_manuais = Lancamento.query.filter_by(origem='manual').count()
        
        conciliados = Lancamento.query.filter_by(conciliado=True).count()
        pendentes = total_lancamentos - conciliados
        
        # Percentuais
        perc_conciliado = (conciliados / total_lancamentos * 100) if total_lancamentos > 0 else 0
        perc_importados = (total_importados / total_lancamentos * 100) if total_lancamentos > 0 else 0
        
        # Histórico de conciliações (últimos 30 dias)
        data_limite = datetime.now() - timedelta(days=30)
        historicos_recentes = ConciliacaoHistorico.query.filter(
            ConciliacaoHistorico.data_conciliacao >= data_limite
        ).order_by(ConciliacaoHistorico.data_conciliacao.desc()).all()
        
        # Top regras utilizadas
        from sqlalchemy import func
        top_regras = db.session.query(
            ConciliacaoPar.regra_aplicada,
            func.count(ConciliacaoPar.id).label('quantidade')
        ).filter(
            ConciliacaoPar.ativo == True
        ).group_by(
            ConciliacaoPar.regra_aplicada
        ).order_by(
            func.count(ConciliacaoPar.id).desc()
        ).limit(5).all()
        
        # Duplicatas detectadas
        duplicatas = Lancamento.query.filter(
            Lancamento.hash_duplicata.in_(
                db.session.query(Lancamento.hash_duplicata)
                .group_by(Lancamento.hash_duplicata)
                .having(func.count(Lancamento.id) > 1)
                .subquery()
            )
        ).count()
        
        return {
            'totais': {
                'lancamentos': total_lancamentos,
                'importados': total_importados,
                'manuais': total_manuais,
                'conciliados': conciliados,
                'pendentes': pendentes,
                'duplicatas': duplicatas
            },
            'percentuais': {
                'conciliado': round(perc_conciliado, 1),
                'importados': round(perc_importados, 1),
                'pendentes': round(100 - perc_conciliado, 1)
            },
            'historicos_recentes': [h.to_dict() for h in historicos_recentes],
            'top_regras': [{'regra': r[0], 'quantidade': r[1]} for r in top_regras]
        }
    
    @staticmethod
    def gerar_relatorio_discrepancias() -> List[Dict]:
        """Identifica possíveis discrepâncias e lançamentos suspeitos"""
        discrepancias = []
        
        # Lançamentos com valores muito altos
        from sqlalchemy import func
        media_valores = db.session.query(func.avg(Lancamento.valor)).scalar() or 0
        limite_alto = media_valores * 5  # 5x a média
        
        valores_altos = Lancamento.query.filter(
            Lancamento.valor > limite_alto,
            Lancamento.conciliado == False
        ).all()
        
        for lanc in valores_altos:
            discrepancias.append({
                'tipo': 'valor_alto',
                'lancamento': lanc.to_dict(),
                'descricao': f'Valor {lanc.valor_formatado} acima da média (>{Lancamento.formatar_valor(limite_alto)})'
            })
        
        # Lançamentos duplicados não conciliados
        duplicatas = db.session.query(
            Lancamento.hash_duplicata,
            func.count(Lancamento.id).label('quantidade')
        ).filter(
            Lancamento.hash_duplicata.isnot(None),
            Lancamento.conciliado == False
        ).group_by(
            Lancamento.hash_duplicata
        ).having(
            func.count(Lancamento.id) > 1
        ).all()
        
        for dup in duplicatas:
            lancamentos_dup = Lancamento.query.filter_by(
                hash_duplicata=dup.hash_duplicata,
                conciliado=False
            ).all()
            
            discrepancias.append({
                'tipo': 'duplicata',
                'lancamentos': [l.to_dict() for l in lancamentos_dup],
                'descricao': f'{dup.quantidade} lançamentos idênticos não conciliados'
            })
        
        return discrepancias