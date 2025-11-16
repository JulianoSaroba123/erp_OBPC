from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, session
from flask_login import login_required
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.financeiro_model import ConciliacaoHistorico, ConciliacaoPar
from app.financeiro.despesas_fixas_model import DespesaFixaConselho
from app.configuracoes.configuracoes_model import Configuracao
from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro, gerar_nome_arquivo_relatorio
from datetime import datetime, date
from sqlalchemy import extract, or_, func
from decimal import Decimal
import os
from werkzeug.utils import secure_filename
import io
import csv
import re
from flask import Response
from difflib import SequenceMatcher

financeiro_bp = Blueprint('financeiro', __name__, template_folder='templates')

@financeiro_bp.route('/financeiro/dashboard')
@login_required
def dashboard_moderno():
    """Dashboard financeiro com visual moderno e métricas"""
    try:
        # Obter mês e ano atual
        hoje = datetime.now()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        # Calcular totais do mês atual
        lancamentos_mes = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes_atual,
            extract('year', Lancamento.data) == ano_atual
        ).all()
        
        total_entradas = sum(l.valor for l in lancamentos_mes if l.tipo.lower() == 'entrada')
        total_saidas = sum(l.valor for l in lancamentos_mes if l.tipo.lower() in ['saída', 'saida'])
        total_nao_conciliados = len([l for l in lancamentos_mes if not l.conciliado])
        
        # Últimos 10 lançamentos
        ultimos_lancamentos = Lancamento.query.order_by(
            Lancamento.criado_em.desc()
        ).limit(10).all()
        
        # Entradas por categoria (top 5)
        categorias_entradas = db.session.query(
            Lancamento.categoria,
            func.sum(Lancamento.valor).label('total'),
            func.count(Lancamento.id).label('count')
        ).filter(
            Lancamento.tipo.ilike('entrada'),
            extract('month', Lancamento.data) == mes_atual,
            extract('year', Lancamento.data) == ano_atual
        ).group_by(Lancamento.categoria).order_by(
            func.sum(Lancamento.valor).desc()
        ).limit(5).all()
        
        return render_template('financeiro/dashboard_moderno.html',
                             total_entradas=total_entradas,
                             total_saidas=total_saidas,
                             total_nao_conciliados=total_nao_conciliados,
                             ultimos_lancamentos=ultimos_lancamentos,
                             categorias_entradas=categorias_entradas)
                             
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/lista-moderna')
@login_required
def lista_lancamentos_moderno():
    """Lista de lançamentos com visual moderno"""
    try:
        # Parâmetros de filtro
        search = request.args.get('search', '')
        tipo = request.args.get('tipo', '')
        categoria = request.args.get('categoria', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        page = request.args.get('page', 1, type=int)
        
        # Construir query
        query = Lancamento.query
        
        if search:
            query = query.filter(Lancamento.descricao.contains(search))
        if tipo:
            query = query.filter(Lancamento.tipo == tipo)
        if categoria:
            query = query.filter(Lancamento.categoria == categoria)
        if data_inicio:
            query = query.filter(Lancamento.data >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
        if data_fim:
            query = query.filter(Lancamento.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())
            
        # Paginação
        lancamentos = query.order_by(Lancamento.criado_em.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Métricas
        total_lancamentos = query.count()
        total_conciliados = query.filter(Lancamento.conciliado == True).count()
        total_pendentes = total_lancamentos - total_conciliados
        
        # Saldo total
        entradas = sum(l.valor for l in query.all() if l.tipo.lower() == 'entrada')
        saidas = sum(l.valor for l in query.all() if l.tipo.lower() in ['saída', 'saida'])
        saldo_total = entradas - saidas
        
        # Categorias disponíveis
        categorias_disponiveis = db.session.query(Lancamento.categoria).distinct().filter(
            Lancamento.categoria.isnot(None)
        ).all()
        categorias_disponiveis = [c[0] for c in categorias_disponiveis if c[0]]
        
        return render_template('financeiro/lista_lancamentos_moderno.html',
                             lancamentos=lancamentos,
                             total_lancamentos=total_lancamentos,
                             total_conciliados=total_conciliados,
                             total_pendentes=total_pendentes,
                             saldo_total=saldo_total,
                             categorias_disponiveis=categorias_disponiveis)
                             
    except Exception as e:
        flash(f'Erro ao carregar lançamentos: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/conciliacao-moderna')
@login_required
def conciliacao_moderno():
    """Conciliação com visual moderno"""
    try:
        # Buscar dados existentes (mesma lógica da rota original)
        importados = Lancamento.query.filter(
            Lancamento.origem == 'importado',
            Lancamento.conciliado == False
        ).all()
        
        historicos = ConciliacaoHistorico.query.order_by(
            ConciliacaoHistorico.data_conciliacao.desc()
        ).limit(10).all()
        
        # Buscar sugestões se existirem na sessão
        sugestoes = session.get('sugestoes_conciliacao', [])
        
        # Calcular taxa de conciliação
        total_lancamentos = Lancamento.query.count()
        total_conciliados = Lancamento.query.filter(Lancamento.conciliado == True).count()
        taxa_conciliacao = (total_conciliados / total_lancamentos * 100) if total_lancamentos > 0 else 0
        
        return render_template('financeiro/conciliacao_moderno.html',
                             importados=importados,
                             historicos=historicos,
                             sugestoes=sugestoes,
                             taxa_conciliacao=taxa_conciliacao)
                             
    except Exception as e:
        flash(f'Erro ao carregar conciliação: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))

# Configurações para upload de arquivos
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processar_upload_comprovante(file):
    """Processa upload do arquivo de comprovante"""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        flash('Tipo de arquivo não permitido. Use: JPG, PNG ou PDF', 'danger')
        return None
    
    try:
        # Gerar nome único para o arquivo
        import uuid
        filename = secure_filename(file.filename)
        nome_unico = f"{uuid.uuid4().hex}_{filename}"
        
        # Criar diretório se não existir
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'comprovantes')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Salvar arquivo
        file_path = os.path.join(upload_dir, nome_unico)
        file.save(file_path)
        
        # Retornar caminho relativo para salvar no banco
        return f"/static/uploads/comprovantes/{nome_unico}"
        
    except Exception as e:
        flash(f'Erro ao fazer upload do comprovante: {str(e)}', 'danger')
        return None

@financeiro_bp.route('/financeiro')
@login_required
def lista_lancamentos():
    """Lista todos os lançamentos com filtros avançados - VERSÃO MODERNA"""
    try:
        # Obter filtros da query string
        categoria_filtro = request.args.get('categoria', '').strip()
        tipo_filtro = request.args.get('tipo', '').strip()
        conta_filtro = request.args.get('conta', '').strip()
        
        # Novos filtros avançados
        data_inicial = request.args.get('data_inicial', '').strip()
        data_final = request.args.get('data_final', '').strip()
        valor_min = request.args.get('valor_min', '').strip()
        valor_max = request.args.get('valor_max', '').strip()
        busca_texto = request.args.get('busca_texto', '').strip()
        
        # Query base
        query = Lancamento.query
        
        # Aplicar filtro por categoria
        if categoria_filtro:
            query = query.filter(Lancamento.categoria.ilike(f'%{categoria_filtro}%'))
        
        # Aplicar filtro por tipo
        if tipo_filtro:
            query = query.filter(Lancamento.tipo == tipo_filtro)
        
        # Aplicar filtro por conta
        if conta_filtro:
            query = query.filter(Lancamento.conta.ilike(f'%{conta_filtro}%'))
            
        # Aplicar filtro por data inicial
        if data_inicial:
            try:
                from datetime import datetime
                data_ini = datetime.strptime(data_inicial, '%Y-%m-%d').date()
                query = query.filter(Lancamento.data >= data_ini)
            except ValueError:
                flash('Data inicial inválida', 'warning')
                
        # Aplicar filtro por data final
        if data_final:
            try:
                from datetime import datetime
                data_fim = datetime.strptime(data_final, '%Y-%m-%d').date()
                query = query.filter(Lancamento.data <= data_fim)
            except ValueError:
                flash('Data final inválida', 'warning')
                
        # Aplicar filtro por valor mínimo
        if valor_min:
            try:
                val_min = float(valor_min.replace(',', '.'))
                query = query.filter(Lancamento.valor >= val_min)
            except ValueError:
                flash('Valor mínimo inválido', 'warning')
                
        # Aplicar filtro por valor máximo
        if valor_max:
            try:
                val_max = float(valor_max.replace(',', '.'))
                query = query.filter(Lancamento.valor <= val_max)
            except ValueError:
                flash('Valor máximo inválido', 'warning')
                
        # Aplicar busca textual (descrição e observações)
        if busca_texto:
            query = query.filter(
                or_(
                    Lancamento.descricao.ilike(f'%{busca_texto}%'),
                    Lancamento.observacoes.ilike(f'%{busca_texto}%')
                )
            )
        
        # Buscar lançamentos filtrados ordenados por data decrescente
        lancamentos_filtrados = query.order_by(Lancamento.data.desc(), Lancamento.criado_em.desc()).all()
        
        # Calcular totais gerais (sem filtro)
        totais_gerais = Lancamento.calcular_totais()
        
        # Calcular totais dos lançamentos filtrados
        totais_filtrados = {
            'entradas': sum(l.valor for l in lancamentos_filtrados if l.tipo == 'Entrada'),
            'saidas': sum(l.valor for l in lancamentos_filtrados if l.tipo == 'Saída'),
            'saldo': 0
        }
        totais_filtrados['saldo'] = totais_filtrados['entradas'] - totais_filtrados['saidas']
        
        # Obter todas as categorias únicas para o filtro
        categorias_todas = db.session.query(Lancamento.categoria).distinct().filter(
            Lancamento.categoria.is_not(None), 
            Lancamento.categoria != ''
        ).order_by(Lancamento.categoria).all()
        categorias_unicas = [cat[0] for cat in categorias_todas]
        
        # Obter todas as contas únicas para o filtro
        contas_todas = db.session.query(Lancamento.conta).distinct().filter(
            Lancamento.conta.is_not(None), 
            Lancamento.conta != ''
        ).order_by(Lancamento.conta).all()
        contas_unicas = [conta[0] for conta in contas_todas]
        
        # Obter todas as contas únicas para o filtro
        contas_todas = db.session.query(Lancamento.conta).distinct().filter(
            Lancamento.conta.is_not(None),
            Lancamento.conta != ''
        ).order_by(Lancamento.conta).all()
        contas_unicas = [conta[0] for conta in contas_todas]
        
        # Calcular totais por categoria para exibição
        totais_por_categoria = {}
        for categoria in categorias_unicas:
            lancamentos_cat = [l for l in lancamentos_filtrados if l.categoria == categoria]
            if lancamentos_cat:
                entradas_cat = sum(l.valor for l in lancamentos_cat if l.tipo == 'Entrada')
                saidas_cat = sum(l.valor for l in lancamentos_cat if l.tipo == 'Saída')
                totais_por_categoria[categoria] = {
                    'entradas': entradas_cat,
                    'saidas': saidas_cat,
                    'saldo': entradas_cat - saidas_cat,
                    'total_registros': len(lancamentos_cat)
                }
        
        # Última conciliação registrada
        ultima_conciliacao = ConciliacaoHistorico.query.order_by(ConciliacaoHistorico.data_conciliacao.desc()).first()
        conciliacao_info = {
            'total_conciliados': ultima_conciliacao.total_conciliados if ultima_conciliacao else 0,
            'total_pendentes': ultima_conciliacao.total_pendentes if ultima_conciliacao else 0,
            'ultima_data': ultima_conciliacao.data_conciliacao if ultima_conciliacao else None
        }

        return render_template('financeiro/lista_lancamentos.html', 
                             lancamentos=lancamentos_filtrados,
                             totais_gerais=totais_gerais,
                             totais_filtrados=totais_filtrados,
                             totais_por_categoria=totais_por_categoria,
                             categorias_unicas=categorias_unicas,
                             contas_unicas=contas_unicas,
                             filtros={
                                 'categoria': categoria_filtro,
                                 'tipo': tipo_filtro,
                                 'conta': conta_filtro,
                                 'data_inicial': data_inicial,
                                 'data_final': data_final,
                                 'valor_min': valor_min,
                                 'valor_max': valor_max,
                                 'busca_texto': busca_texto
                             },
                             conciliacao_info=conciliacao_info)
                             
    except Exception as e:
        flash(f'Erro ao carregar lançamentos: {str(e)}', 'danger')
        return render_template('financeiro/lista_lancamentos.html', 
                             lancamentos=[], 
                             totais_gerais={'entradas': 0, 'saidas': 0, 'saldo': 0},
                             totais_filtrados={'entradas': 0, 'saidas': 0, 'saldo': 0},
                             totais_por_categoria={},
                             categorias_unicas=[],
                             contas_unicas=[],
                             filtros={
                                 'categoria': '', 'tipo': '', 'conta': '',
                                 'data_inicial': '', 'data_final': '',
                                 'valor_min': '', 'valor_max': '', 'busca_texto': ''
                             })

@financeiro_bp.route('/financeiro/novo')
@login_required
def novo_lancamento():
    """Exibe formulário para cadastro de novo lançamento"""
    return render_template('financeiro/cadastro_lancamento.html', today=date.today())


@financeiro_bp.route('/financeiro/importar', methods=['GET', 'POST'])
@login_required
def importar_extrato():
    """Formulário para importar extrato bancário (CSV/XLSX)"""
    if request.method == 'POST':
        # Processar upload do arquivo
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
        
        file = request.files['arquivo']
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
        
        # Verificar tipo de arquivo
        tipo_arquivo = request.form.get('tipo_arquivo', '')
        if not tipo_arquivo:
            flash('Selecione o tipo de arquivo', 'warning')
            return redirect(request.url)
        
        # Redirecionar para preview com os dados
        try:
            # Criar um form data temporário para a função de preview
            from werkzeug.datastructures import FileStorage
            from io import BytesIO
            
            # Ler o arquivo
            file_content = file.read()
            file.seek(0)  # Reset para uso posterior
            
            # Criar novo FileStorage para preview
            temp_file = FileStorage(
                stream=BytesIO(file_content),
                filename=file.filename,
                content_type=file.content_type
            )
            
            # Chamar a função de preview diretamente
            return importar_extrato_preview_internal(temp_file, tipo_arquivo)
            
        except Exception as e:
            flash(f'Erro ao processar arquivo: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('financeiro/importar_extrato.html')


def importar_extrato_preview_internal(file, tipo_arquivo):
    """Função interna para processar preview de importação"""
    try:
        try:
            import pandas as pd
        except ImportError:
            flash('Pandas não está instalado no ambiente. A importação de extratos requer pandas.', 'warning')
            return redirect(url_for('financeiro.importar_extrato'))
        import io
        
        # Mapear tipo de arquivo para banco
        banco_map = {
            'extrato_bb': 'bancodobrasil',
            'extrato_itau': 'itau', 
            'extrato_caixa': 'caixa',
            'extrato_bradesco': 'bradesco',
            'extrato_santander': 'santander',
            'extrato_pagbank': 'pagbank',
            'ofx_generico': 'ofx',
            'csv_generico': 'generico',
            'txt_generico': 'generico'
        }
        banco = banco_map.get(tipo_arquivo, 'generico')
        
        # Ler arquivo baseado na extensão
        filename = file.filename.lower()
        try:
            if filename.endswith('.csv') or filename.endswith('.txt'):
                # Tentar diferentes encodings para CSV
                file.seek(0)
                content = file.read()
                
                # Tentar UTF-8 primeiro
                try:
                    content_str = content.decode('utf-8')
                    file_obj = io.StringIO(content_str)
                    df = pd.read_csv(file_obj, sep=';')
                    if len(df.columns) == 1:
                        file_obj = io.StringIO(content_str)
                        df = pd.read_csv(file_obj, sep=',')
                except UnicodeDecodeError:
                    # Tentar Latin-1
                    content_str = content.decode('latin-1')
                    file_obj = io.StringIO(content_str)
                    df = pd.read_csv(file_obj, sep=';')
                    if len(df.columns) == 1:
                        file_obj = io.StringIO(content_str)
                        df = pd.read_csv(file_obj, sep=',')
            else:
                file.seek(0)
                df = pd.read_excel(file)
        except Exception as e:
            flash(f'Erro ao ler arquivo: {str(e)}', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))

        # Aplicar mapeamento específico do banco com detecção inteligente
        def encontrar_coluna(df, palavras_chave):
            """Encontra coluna baseada em palavras-chave"""
            # Primeiro tenta encontrar com nomes exatos (case insensitive)
            for col in df.columns:
                for palavra in palavras_chave:
                    if str(col).lower() == palavra.lower():
                        return col
            
            # Se não encontrou, tenta busca parcial sem espaços
            for col in df.columns:
                col_lower = str(col).lower().replace(' ', '').replace('_', '')
                for palavra in palavras_chave:
                    if palavra.lower().replace(' ', '') in col_lower:
                        return col
            return None
        
        # Mapeamento inteligente baseado no banco
        if banco in ['bancodobrasil', 'bb']:
            data_cols = ['data', 'dataoperacao', 'datamovimentacao']
            desc_cols = ['descricao', 'historico', 'memo', 'complemento']
            valor_cols = ['valor', 'valormovimentacao', 'amount']
            tipo_cols = ['natureza', 'tipo', 'credito', 'debito']
        elif banco == 'itau':
            data_cols = ['data', 'dataoperacao', 'date']
            desc_cols = ['descricao', 'historico', 'description']
            valor_cols = ['valor', 'amount', 'montante']
            tipo_cols = ['natureza', 'tipo', 'credito', 'debito']
        elif banco == 'bradesco':
            data_cols = ['data', 'dataoperacao', 'date']
            desc_cols = ['descricao', 'historico', 'memo', 'description']
            valor_cols = ['valor', 'amount', 'montante']
            tipo_cols = ['tipo', 'natureza', 'credito', 'debito']
        elif banco == 'pagbank':
            # Mapeamento específico do PagBank - nomes exatos das colunas
            data_cols = ['DATA', 'data', 'datatransacao', 'dataoperacao', 'date', 'created_at']
            desc_cols = ['DESCRICAO', 'descricao', 'descricaotransacao', 'historico', 'description', 'memo', 'reference']
            valor_cols = ['VALOR', 'valor', 'valortransacao', 'amount', 'montante', 'quantia', 'gross_amount']
            tipo_cols = ['TIPO', 'tipo', 'tipotransacao', 'credito', 'debito', 'natureza', 'transaction_type']
        else:
            # Mapeamento genérico
            data_cols = ['data', 'date', 'fecha']
            desc_cols = ['descricao', 'description', 'memo', 'historico']
            valor_cols = ['valor', 'value', 'amount', 'montante']
            tipo_cols = ['tipo', 'type', 'natureza']
        
        # Encontrar colunas automaticamente
        col_data = encontrar_coluna(df, data_cols)
        col_desc = encontrar_coluna(df, desc_cols)
        col_valor = encontrar_coluna(df, valor_cols)
        col_tipo = encontrar_coluna(df, tipo_cols)
        
        # Verificar se encontrou pelo menos data, descrição e valor
        if not all([col_data, col_desc, col_valor]):
            colunas_encontradas = [f"'{col}'" for col in df.columns]
            flash(f'Arquivo sem colunas essenciais. Colunas encontradas: {", ".join(colunas_encontradas)}. '
                  f'Precisa ter colunas relacionadas a: data, descrição e valor', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))

        # Preparar lista de registros
        registros = []
        for index, row in df.iterrows():
            try:
                data_raw = row.get(col_data)
                descricao = str(row.get(col_desc) or '')
                valor_raw = row.get(col_valor)
                tipo_raw = row.get(col_tipo) if col_tipo else None
                
                # Normalizar data
                try:
                    if pd.isna(data_raw):
                        data_str = None
                    else:
                        # Tentar vários formatos de data
                        data_obj = pd.to_datetime(data_raw, dayfirst=True, errors='coerce')
                        if pd.isna(data_obj):
                            # Tentar formato americano
                            data_obj = pd.to_datetime(data_raw, dayfirst=False, errors='coerce')
                        
                        if not pd.isna(data_obj):
                            data_str = data_obj.strftime('%Y-%m-%d')
                        else:
                            data_str = None
                except Exception:
                    data_str = None

                # Normalizar valor
                try:
                    if pd.isna(valor_raw):
                        valor = 0.0
                    else:
                        # Remover caracteres especiais e normalizar
                        valor_str = str(valor_raw).replace(',', '.').replace(' ', '').replace('R$', '').replace('$', '')
                        # Remover outros caracteres não numéricos exceto ponto e sinal
                        import re
                        valor_str = re.sub(r'[^\d\.\-\+]', '', valor_str)
                        valor = float(valor_str) if valor_str else 0.0
                except Exception:
                    valor = 0.0

                # Determinar tipo baseado no valor ou coluna tipo
                if tipo_raw and not pd.isna(tipo_raw):
                    tipo_str = str(tipo_raw).upper()
                    if 'CREDIT' in tipo_str or 'ENTRADA' in tipo_str:
                        tipo = 'Entrada'
                        valor = abs(valor)
                    elif 'DEBIT' in tipo_str or 'SAIDA' in tipo_str:
                        tipo = 'Saída'
                        valor = abs(valor)
                    else:
                        tipo = 'Entrada' if valor >= 0 else 'Saída'
                        valor = abs(valor)
                else:
                    # Baseado no sinal do valor
                    tipo = 'Entrada' if valor >= 0 else 'Saída'
                    valor = abs(valor)

                # Buscar possível match no sistema
                match = None
                if data_str and valor > 0:
                    match = Lancamento.query.filter(
                        Lancamento.data == data_str,
                        Lancamento.valor == valor
                    ).first()

                registros.append({
                    'data': data_str,
                    'descricao': descricao[:200],  # Limitar tamanho
                    'valor': valor,
                    'tipo': tipo,
                    'banco': banco,
                    'match_id': match.id if match else None,
                    'match_desc': match.descricao if match else None,
                    'linha': index + 1
                })
                
            except Exception as e:
                flash(f'Erro na linha {index + 1}: {str(e)}', 'warning')
                current_app.logger.error(f'Erro linha {index + 1}: {str(e)}')

        # Salvar dados na sessão para confirmação posterior
        session['registros_import'] = registros
        session['banco_import'] = banco

        # Render preview
        return render_template('financeiro/import_preview.html', 
                             registros=registros,
                             banco=banco,
                             total_registros=len(registros))

    except Exception as e:
        flash(f'Erro ao processar arquivo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.importar_extrato'))

@financeiro_bp.route('/financeiro/conciliacao')
@login_required
def conciliacao():
    """Tela para conciliação manual/automática"""
    # Buscar importados e manuais não conciliados
    importados = Lancamento.query.filter_by(origem='importado', conciliado=False).order_by(Lancamento.data.desc()).all()
    manuais = Lancamento.query.filter_by(origem='manual', conciliado=False).order_by(Lancamento.data.desc()).all()
    # última conciliação para permitir undo
    ultima = ConciliacaoHistorico.query.order_by(ConciliacaoHistorico.data_conciliacao.desc()).first()
    # últimos históricos para permitir desfazer por registro
    historicos = ConciliacaoHistorico.query.order_by(ConciliacaoHistorico.data_conciliacao.desc()).limit(20).all()
    return render_template('financeiro/conciliacao.html', importados=importados, manuais=manuais, ultima_conciliacao=ultima, historicos=historicos)

@financeiro_bp.route('/financeiro/conciliacao/auto', methods=['POST'])
@login_required
def conciliacao_auto():
    """Executa conciliação automática: casa importados com manuais por data e valor exato"""
    try:
        conciliados = 0
        # Buscar importados pendentes
        importados = Lancamento.query.filter_by(origem='importado', conciliado=False).all()
        for imp in importados:
            # tentar encontrar manual correspondente
            match = Lancamento.query.filter_by(origem='manual', conciliado=False, data=imp.data, valor=imp.valor, tipo=imp.tipo).first()
            if match:
                imp.conciliado = True
                match.conciliado = True
                conciliados += 1
                db.session.add(imp)
                db.session.add(match)

        db.session.commit()

        # Registrar histórico
        from flask_login import current_user
        usuario_nome = str(getattr(current_user, 'username', 'system'))
        total_pendentes = Lancamento.query.filter_by(origem='importado', conciliado=False).count()
        historico = ConciliacaoHistorico(
            data_conciliacao=datetime.now(),
            usuario=usuario_nome,
            total_conciliados=conciliados,
            total_pendentes=total_pendentes,
            observacao=f'Conciliação automática: {conciliados} conciliados'
        )
        db.session.add(historico)
        db.session.commit()

        flash(f'Conciliação automática concluída: {conciliados} conciliados.', 'success')
        return redirect(url_for('financeiro.conciliacao'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro na conciliação automática: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


def similaridade(a, b):
    """Retorna similaridade entre duas strings 0..1"""
    try:
        return SequenceMatcher(None, (a or '').lower(), (b or '').lower()).ratio()
    except Exception:
        return 0.0


def gerar_sugestoes(importados, manuais, days_window=2, value_tol_pct=0.02, desc_thresh=0.35):
    """Gera uma lista de sugestões de conciliação entre listas de lançamentos.
    Parameters:
      importados, manuais: listas de Lancamento
      days_window: nº de dias para considerar perto da data
      value_tol_pct: tolerância percentual para valores (ex: 0.02 = 2%)
      desc_thresh: limiar mínimo para considerar descrição relevante
    Retorna: lista de dicts {imp: Lancamento, man: Lancamento, score: float, details...}
    """
    suggestions = []
    for imp in importados:
        for man in manuais:
            try:
                # diferença de dias
                delta_days = abs((imp.data - man.data).days) if imp.data and man.data else 9999

                # diferença percentual de valor
                if man.valor and man.valor != 0:
                    value_diff_pct = abs(imp.valor - man.valor) / abs(man.valor)
                else:
                    value_diff_pct = 0 if imp.valor == man.valor else 1

                # similaridade de descrição
                desc_score = similaridade(imp.descricao or '', man.descricao or '')

                # pontuação composta (valores menores são melhores)
                score = 0.0
                # start from description weight
                score += desc_score * 0.6
                # value similarity
                score += max(0, (1 - min(1, value_diff_pct))) * 0.3
                # date proximity bonus
                score += max(0, (1 - min(1, delta_days / max(1, days_window)))) * 0.1

                # filtrar por limiares razoáveis
                if delta_days <= max(7, days_window*3) and value_diff_pct <= 0.5 and desc_score >= 0.05:
                    suggestions.append({
                        'imp_id': imp.id,
                        'man_id': man.id,
                        'imp': imp,
                        'man': man,
                        'score': round(score, 4),
                        'delta_days': delta_days,
                        'value_diff_pct': round(value_diff_pct, 4),
                        'desc_score': round(desc_score, 4)
                    })
            except Exception:
                continue

    suggestions.sort(key=lambda x: x['score'], reverse=True)
    return suggestions


@financeiro_bp.route('/financeiro/conciliacao/sugerir', methods=['POST'])
@login_required
def conciliacao_sugerir():
    """Gera sugestões com base em parâmetros enviados no formulário."""
    try:
        days_window = int(request.form.get('days_window', 2))
        value_tol_pct = float(request.form.get('value_tol_pct', 0.02))
        desc_thresh = float(request.form.get('desc_thresh', 0.35))

        importados = Lancamento.query.filter_by(origem='importado', conciliado=False).all()
        manuais = Lancamento.query.filter_by(origem='manual', conciliado=False).all()

        sugestoes = gerar_sugestoes(importados, manuais, days_window, value_tol_pct, desc_thresh)

        return render_template('financeiro/conciliacao.html', importados=importados, manuais=manuais, sugestoes=sugestoes, params={'days_window':days_window,'value_tol_pct':value_tol_pct,'desc_thresh':desc_thresh})
    except Exception as e:
        flash(f'Erro ao gerar sugestões: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/conciliacao/aceitar', methods=['POST'])
@login_required
def conciliacao_aceitar():
    """Aceita um par sugerido: marca ambos como conciliado e registra histórico"""
    try:
        imp_id = int(request.form.get('imp_id'))
        man_id = int(request.form.get('man_id'))

        imp = Lancamento.query.get_or_404(imp_id)
        man = Lancamento.query.get_or_404(man_id)

        if imp.conciliado or man.conciliado:
            flash('Um dos lançamentos já está conciliado.', 'warning')
            return redirect(url_for('financeiro.conciliacao'))

        # marcar conciliado e persistir
        imp.conciliado = True
        man.conciliado = True
        db.session.add(imp)
        db.session.add(man)
        db.session.commit()

        # registrar histórico e par
        from flask_login import current_user
        usuario_nome = str(getattr(current_user, 'username', 'system'))
        total_pendentes = Lancamento.query.filter_by(origem='importado', conciliado=False).count()
        historico = ConciliacaoHistorico(data_conciliacao=datetime.now(), usuario=usuario_nome, total_conciliados=1, total_pendentes=total_pendentes, observacao=f'Conciliado manual: imp {imp.id} <> man {man.id}')
        db.session.add(historico)
        db.session.commit()

        par = ConciliacaoPar(historico_id=historico.id, imp_id=imp.id, man_id=man.id, score=request.form.get('score', None), regra=request.form.get('regra', 'manual'), usuario=usuario_nome)
        db.session.add(par)
        db.session.commit()

        flash('Par conciliado com sucesso.', 'success')
        return redirect(url_for('financeiro.conciliacao'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao aceitar sugestão: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/conciliacao/aceitar_todos', methods=['POST'])
@login_required
def conciliacao_aceitar_todos():
    """Aceita todos os pares enviados como JSON no corpo da requisição."""
    try:
        import json
        data = None
        if request.is_json:
            data = request.get_json()
        else:
            payload = request.form.get('pairs')
            if payload:
                data = json.loads(payload)

        if not data:
            flash('Nenhum par enviado para conciliação.', 'warning')
            return redirect(url_for('financeiro.conciliacao'))

        conciliados = 0
        pairs_created = []
        for p in data:
            imp = Lancamento.query.get(p.get('imp_id'))
            man = Lancamento.query.get(p.get('man_id'))
            if not imp or not man:
                continue
            if imp.conciliado or man.conciliado:
                continue
            imp.conciliado = True
            man.conciliado = True
            db.session.add(imp)
            db.session.add(man)
            conciliados += 1

        db.session.commit()

        from flask_login import current_user
        usuario_nome = str(getattr(current_user, 'username', 'system'))
        historico = ConciliacaoHistorico(data_conciliacao=datetime.now(), usuario=usuario_nome, total_conciliados=conciliados, total_pendentes=Lancamento.query.filter_by(origem='importado', conciliado=False).count(), observacao=f'Conciliar todos via sugestões: {conciliados} pares')
        db.session.add(historico)
        db.session.commit()

        # registrar pares ligados ao historico
        for p in data:
            try:
                imp_id = int(p.get('imp_id'))
                man_id = int(p.get('man_id'))
            except Exception:
                continue
            par = ConciliacaoPar(historico_id=historico.id, imp_id=imp_id, man_id=man_id, score=p.get('score', None), regra='sugestao', usuario=usuario_nome)
            db.session.add(par)
        db.session.commit()

        flash(f'{conciliados} pares conciliados.', 'success')
        return redirect(url_for('financeiro.conciliacao'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao aceitar todos: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/conciliacao/undo_ultimo', methods=['POST'])
@login_required
def conciliacao_undo_ultimo():
    """Desfaz a última conciliação registrada (reverte conciliado e remove pares/historico)."""
    try:
        ultima = ConciliacaoHistorico.query.order_by(ConciliacaoHistorico.data_conciliacao.desc()).first()
        if not ultima:
            flash('Não há conciliações para desfazer.', 'warning')
            return redirect(url_for('financeiro.conciliacao'))

        # obter pares ligados
        pares = ConciliacaoPar.query.filter_by(historico_id=ultima.id).all()
        revertidos = 0
        for par in pares:
            imp = Lancamento.query.get(par.imp_id)
            man = Lancamento.query.get(par.man_id)
            if imp and imp.conciliado:
                imp.conciliado = False
                db.session.add(imp)
                revertidos += 1
            if man and man.conciliado:
                man.conciliado = False
                db.session.add(man)
                revertidos += 1

        # remover registros de pares e historico
        for par in pares:
            db.session.delete(par)

        db.session.delete(ultima)
        db.session.commit()

        flash(f'Última conciliação desfeita. {revertidos} marcações revertidas.', 'success')
        return redirect(url_for('financeiro.conciliacao'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desfazer última conciliação: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/conciliacao/export_pairs', methods=['POST'])
@login_required
def conciliacao_export_pairs():
    """Exporta os pares selecionados como CSV para download."""
    try:
        import json
        payload = None
        if request.is_json:
            payload = request.get_json()
        else:
            payload = request.form.get('pairs')
            if payload:
                payload = json.loads(payload)

        if not payload:
            flash('Nenhum par selecionado para exportação.', 'warning')
            return redirect(url_for('financeiro.conciliacao'))

        # criar CSV em memória
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['imp_id', 'man_id', 'imp_data', 'man_data', 'imp_valor', 'man_valor', 'score'])
        for p in payload:
            imp = Lancamento.query.get(p.get('imp_id'))
            man = Lancamento.query.get(p.get('man_id'))
            writer.writerow([
                p.get('imp_id'),
                p.get('man_id'),
                imp.data.isoformat() if imp and imp.data else '',
                man.data.isoformat() if man and man.data else '',
                f"{imp.valor:.2f}" if imp else '',
                f"{man.valor:.2f}" if man else '',
                p.get('score', '')
            ])

        output = si.getvalue()
        mem = io.BytesIO()
        mem.write(output.encode('utf-8'))
        mem.seek(0)

        filename = f"conciliacao_pares_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=filename)

    except Exception as e:
        flash(f'Erro ao exportar pares: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/conciliacao/undo/<int:historico_id>', methods=['POST'])
@login_required
def conciliacao_undo(historico_id):
    """Desfaz uma conciliação específica pelo id do histórico."""
    try:
        historico = ConciliacaoHistorico.query.get_or_404(historico_id)
        pares = ConciliacaoPar.query.filter_by(historico_id=historico.id).all()
        revertidos = 0
        for par in pares:
            imp = Lancamento.query.get(par.imp_id)
            man = Lancamento.query.get(par.man_id)
            if imp and imp.conciliado:
                imp.conciliado = False
                db.session.add(imp)
                revertidos += 1
            if man and man.conciliado:
                man.conciliado = False
                db.session.add(man)
                revertidos += 1

        for par in pares:
            db.session.delete(par)

        db.session.delete(historico)
        db.session.commit()

        flash(f'Conciliação {historico_id} desfeita. {revertidos} marcações revertidas.', 'success')
        return redirect(url_for('financeiro.conciliacao'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desfazer conciliação {historico_id}: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao'))


@financeiro_bp.route('/financeiro/importar/confirmar', methods=['POST'])
@login_required
def confirmar_importacao():
    """Confirma e processa a importação dos registros"""
    try:
        import json
        
        # Recuperar dados da sessão
        registros = session.get('registros_import', [])
        banco = session.get('banco_import', 'generico')
        ignorar_duplicatas = request.form.get('ignorar_duplicatas') == 'on'
        
        if not registros:
            flash('Nenhum registro para importar.', 'warning')
            return redirect(url_for('financeiro.importar_extrato'))
        
        importados = 0
        ignorados = 0
        erros = 0
        
        for registro in registros:
            try:
                # Verificar se é duplicata
                if registro.get('match_id') and not ignorar_duplicatas:
                    ignorados += 1
                    continue
                
                # Validar dados obrigatórios
                if not registro.get('data') or not registro.get('valor'):
                    erros += 1
                    continue
                
                # Criar novo lançamento
                novo_lancamento = Lancamento(
                    data=registro['data'],
                    descricao=registro['descricao'][:500],  # Limitar tamanho
                    valor=abs(float(registro['valor'])),
                    tipo=registro['tipo'],
                    categoria='Importação Bancária',
                    observacoes=f'Importado do banco {banco.upper()}',
                    banco_origem=banco,
                    documento_ref=f"Import_{banco}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                db.session.add(novo_lancamento)
                importados += 1
                
            except Exception as e:
                erros += 1
                current_app.logger.error(f'Erro ao importar registro: {str(e)}')
        
        # Salvar no banco
        try:
            db.session.commit()
            
            # Limpar sessão
            session.pop('registros_import', None)
            session.pop('banco_import', None)
            
            # Mensagem de sucesso
            msg = f'Importação concluída: {importados} registros importados'
            if ignorados > 0:
                msg += f', {ignorados} duplicatas ignoradas'
            if erros > 0:
                msg += f', {erros} registros com erro'
            
            flash(msg, 'success')
            return redirect(url_for('financeiro.lancamentos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar no banco: {str(e)}', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))
        
    except Exception as e:
        flash(f'Erro ao processar importação: {str(e)}', 'danger')
        return redirect(url_for('financeiro.importar_extrato'))


@financeiro_bp.route('/financeiro/importar/preview', methods=['POST'])
@login_required
def importar_extrato_preview():
    """Preview dos registros importados e tentativa de sugestão de conciliação"""
    try:
        try:
            import pandas as pd
        except ImportError:
            flash('Pandas não está instalado no ambiente. A importação de extratos requer pandas.', 'warning')
            return redirect(url_for('financeiro.importar_extrato'))
        
        # Pegar arquivo e banco selecionado
        file = request.files.get('arquivo') or request.files.get('file')
        banco = request.form.get('banco', 'generico')
        
        if not file or file.filename == '':
            flash('Selecione um arquivo CSV ou XLSX para importar.', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))

        # Ler arquivo baseado na extensão
        filename = file.filename.lower()
        try:
            if filename.endswith('.csv'):
                # Tentar diferentes encodings para CSV
                file.seek(0)
                content = file.read()
                
                # Tentar UTF-8 primeiro
                try:
                    content_str = content.decode('utf-8')
                    file_obj = io.StringIO(content_str)
                    df = pd.read_csv(file_obj, sep=';')
                    if len(df.columns) == 1:
                        file_obj = io.StringIO(content_str)
                        df = pd.read_csv(file_obj, sep=',')
                except UnicodeDecodeError:
                    # Tentar Latin-1
                    content_str = content.decode('latin-1')
                    file_obj = io.StringIO(content_str)
                    df = pd.read_csv(file_obj, sep=';')
                    if len(df.columns) == 1:
                        file_obj = io.StringIO(content_str)
                        df = pd.read_csv(file_obj, sep=',')
            else:
                df = pd.read_excel(file)
        except Exception as e:
            flash(f'Erro ao ler arquivo: {str(e)}', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))

        # Aplicar mapeamento específico do banco com detecção inteligente
        df_original = df.copy()
        
        def encontrar_coluna(df, palavras_chave):
            """Encontra coluna baseada em palavras-chave"""
            for col in df.columns:
                col_lower = str(col).lower().replace(' ', '').replace('_', '')
                for palavra in palavras_chave:
                    if palavra.lower().replace(' ', '') in col_lower:
                        return col
            return None
        
        # Mapeamento inteligente baseado no banco
        if banco == 'pagbank':
            # Palavras-chave específicas do PagBank
            data_cols = ['data', 'datatransacao', 'dataoperacao', 'date']
            desc_cols = ['descricao', 'descricaotransacao', 'historico', 'description', 'memo']
            valor_cols = ['valor', 'valortransacao', 'amount', 'montante', 'quantia']
            tipo_cols = ['tipo', 'tipotransacao', 'credito', 'debito', 'natureza']
        elif banco == 'bradesco':
            data_cols = ['data', 'dataoperacao', 'date']
            desc_cols = ['descricao', 'historico', 'memo', 'description']
            valor_cols = ['valor', 'amount', 'montante']
            tipo_cols = ['tipo', 'natureza', 'credito', 'debito']
        else:
            # Mapeamento genérico
            data_cols = ['data', 'date', 'fecha']
            desc_cols = ['descricao', 'description', 'memo', 'historico']
            valor_cols = ['valor', 'value', 'amount', 'montante']
            tipo_cols = ['tipo', 'type', 'natureza']
        
        # Encontrar colunas automaticamente
        col_data = encontrar_coluna(df, data_cols)
        col_desc = encontrar_coluna(df, desc_cols)
        col_valor = encontrar_coluna(df, valor_cols)
        col_tipo = encontrar_coluna(df, tipo_cols)
        
        # Verificar se encontrou pelo menos data, descrição e valor
        if not all([col_data, col_desc, col_valor]):
            colunas_encontradas = [f"'{col}'" for col in df.columns]
            flash(f'Arquivo sem colunas essenciais. Colunas encontradas: {", ".join(colunas_encontradas)}. '
                  f'Precisa ter colunas relacionadas a: data, descrição e valor', 'danger')
            return redirect(url_for('financeiro.importar_extrato'))

        # Preparar lista de registros
        registros = []
        for index, row in df.iterrows():
            try:
                data_raw = row.get(col_data)
                descricao = str(row.get(col_desc) or '')
                valor_raw = row.get(col_valor)
                tipo_raw = row.get(col_tipo) if col_tipo else None
                
                # Normalizar data
                try:
                    if pd.isna(data_raw):
                        data_str = None
                    else:
                        # Tentar vários formatos de data
                        data_obj = pd.to_datetime(data_raw, dayfirst=True, errors='coerce')
                        if pd.isna(data_obj):
                            # Tentar formato americano
                            data_obj = pd.to_datetime(data_raw, dayfirst=False, errors='coerce')
                        
                        if not pd.isna(data_obj):
                            data_str = data_obj.strftime('%Y-%m-%d')
                        else:
                            data_str = None
                except Exception:
                    data_str = None

                # Normalizar valor
                try:
                    if pd.isna(valor_raw):
                        valor = 0.0
                    else:
                        # Remover caracteres especiais e normalizar
                        valor_str = str(valor_raw).replace(',', '.').replace(' ', '').replace('R$', '').replace('$', '')
                        # Remover outros caracteres não numéricos exceto ponto e sinal
                        import re
                        valor_str = re.sub(r'[^\d\.\-\+]', '', valor_str)
                        valor = float(valor_str) if valor_str else 0.0
                except Exception:
                    valor = 0.0

                # Determinar tipo baseado no valor ou coluna tipo
                if tipo_raw and not pd.isna(tipo_raw):
                    tipo_str = str(tipo_raw).upper()
                    if 'CREDIT' in tipo_str or 'ENTRADA' in tipo_str:
                        tipo = 'Entrada'
                        valor = abs(valor)
                    elif 'DEBIT' in tipo_str or 'SAIDA' in tipo_str:
                        tipo = 'Saída'
                        valor = abs(valor)
                    else:
                        tipo = 'Entrada' if valor >= 0 else 'Saída'
                        valor = abs(valor)
                else:
                    # Baseado no sinal do valor
                    tipo = 'Entrada' if valor >= 0 else 'Saída'
                    valor = abs(valor)

                # Buscar possível match no sistema
                match = None
                if data_str and valor > 0:
                    match = Lancamento.query.filter(
                        Lancamento.data == data_str,
                        Lancamento.valor == valor
                    ).first()

                registros.append({
                    'data': data_str,
                    'descricao': descricao[:200],  # Limitar tamanho
                    'valor': valor,
                    'tipo': tipo,
                    'banco': banco,
                    'match_id': match.id if match else None,
                    'match_desc': match.descricao if match else None,
                    'linha': index + 1
                })
                
            except Exception as e:
                flash(f'Erro na linha {index + 1}: {str(e)}', 'warning')
                current_app.logger.error(f'Erro linha {index + 1}: {str(e)}')

        # Salvar dados na sessão para confirmação posterior
        session['registros_import'] = registros
        session['banco_import'] = banco

        # Render preview
        return render_template('financeiro/import_preview.html', 
                             registros=registros,
                             banco=banco,
                             total_registros=len(registros))

    except Exception as e:
        flash(f'Erro ao processar arquivo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.importar_extrato'))


@financeiro_bp.route('/financeiro/importar/confirmar', methods=['POST'])
@login_required
def importar_extrato_confirmar():
    """Confirma importação: insere lançamentos não casados e registra conciliação"""
    try:
        import json
        dados = request.form.get('registros')
        if not dados:
            flash('Nenhum registro para importar.', 'warning')
            return redirect(url_for('financeiro.importar_extrato'))

        registros = json.loads(dados)
        criados = 0
        conciliados = 0
        for r in registros:
            if r.get('match_id'):
                conciliados += 1
                continue
            # criar novo lancamento
            data_obj = None
            if r.get('data'):
                try:
                    data_obj = datetime.strptime(r.get('data'), '%Y-%m-%d').date()
                except Exception:
                    data_obj = date.today()
            else:
                data_obj = date.today()

            novo = Lancamento(
                data=data_obj,
                tipo='Entrada' if float(r.get('valor', 0)) >= 0 else 'Saída',
                categoria=None,
                descricao=r.get('descricao'),
                valor=abs(float(r.get('valor', 0))),
                conta=None,
                observacoes=f'Importado via extrato: origem arquivo',
                comprovante=None
            )
            novo.origem = 'importado'
            db.session.add(novo)
            criados += 1

        db.session.commit()

        # Registrar histórico de conciliação
        from flask_login import current_user
        usuario_nome = str(getattr(current_user, 'username', 'import'))
        historico = ConciliacaoHistorico(
            data_conciliacao=datetime.now(),
            usuario=usuario_nome,
            total_conciliados=conciliados,
            total_pendentes=criados,
            observacao=f'Importação de extrato: {criados} criados, {conciliados} conciliados'
        )
        db.session.add(historico)
        db.session.commit()

        flash(f'Importação concluída: {criados} criados, {conciliados} conciliados.', 'success')
        return redirect(url_for('financeiro.lista_lancamentos'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao confirmar importação: {str(e)}', 'danger')
        return redirect(url_for('financeiro.importar_extrato'))

@financeiro_bp.route('/financeiro/salvar', methods=['POST'])
@login_required
def salvar_lancamento():
    """Salva novo lançamento ou atualiza lançamento existente"""
    try:
        # Captura dados do formulário
        lancamento_id = request.form.get('id')
        data_str = request.form.get('data')
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria', '').strip()
        descricao = request.form.get('descricao', '').strip()
        valor_str = request.form.get('valor', '').strip()
        conta = request.form.get('conta')
        observacoes_raw = request.form.get('observacoes', '').strip()
        
        # Limpar observações - garantir que None ou strings vazias sejam tratadas adequadamente
        observacoes = None
        if observacoes_raw and observacoes_raw.lower() != 'none' and observacoes_raw.strip():
            observacoes = observacoes_raw
        
        # Processar upload de comprovante
        file = request.files.get('comprovante')
        caminho_comprovante = None
        if file:
            caminho_comprovante = processar_upload_comprovante(file)
        
        # Validações básicas
        if not tipo or tipo not in ['Entrada', 'Saída']:
            flash('Tipo é obrigatório (Entrada ou Saída)!', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
        if not valor_str:
            flash('Valor é obrigatório!', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
        # Conversão de valor
        try:
            # Remove formatação brasileira e converte para float
            valor_limpo = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
            valor = float(valor_limpo)
            if valor <= 0:
                flash('Valor deve ser maior que zero!', 'danger')
                return redirect(url_for('financeiro.novo_lancamento'))
        except ValueError:
            flash('Valor inválido! Use formato: 1.000,50', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
        # Conversão de data
        data_obj = None
        if data_str:
            try:
                data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data inválida!', 'danger')
                return redirect(url_for('financeiro.novo_lancamento'))
        else:
            data_obj = date.today()

        if lancamento_id:
            # Atualizar lançamento existente
            lancamento = Lancamento.query.get_or_404(lancamento_id)
            lancamento.data = data_obj
            lancamento.tipo = tipo
            lancamento.categoria = categoria if categoria else None
            lancamento.descricao = descricao if descricao else None
            lancamento.valor = valor
            lancamento.conta = conta
            lancamento.observacoes = observacoes
            # Atualizar comprovante apenas se um novo foi enviado
            if caminho_comprovante:
                lancamento.comprovante = caminho_comprovante
            flash('Lançamento atualizado com sucesso! Você pode continuar lançando ou clicar em "Voltar" para ver a lista.', 'success')
        else:
            # Validação de duplicidade
            duplicado = Lancamento.query.filter_by(
                data=data_obj,
                tipo=tipo,
                categoria=categoria if categoria else None,
                descricao=descricao if descricao else None,
                valor=valor,
                conta=conta
            ).first()
            if duplicado:
                flash('Já existe um lançamento igual cadastrado! Verifique os dados.', 'danger')
                return redirect(url_for('financeiro.novo_lancamento'))
            # Criar novo lançamento
            novo_lancamento = Lancamento(
                data=data_obj,
                tipo=tipo,
                categoria=categoria if categoria else None,
                descricao=descricao if descricao else None,
                valor=valor,
                conta=conta,
                observacoes=observacoes,
                comprovante=caminho_comprovante
            )
            novo_lancamento.origem = 'manual'
            db.session.add(novo_lancamento)
            flash('Lançamento cadastrado com sucesso! Você pode continuar lançando ou clicar em "Voltar" para ver a lista.', 'success')

        db.session.commit()

        return redirect(url_for('financeiro.novo_lancamento'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar lançamento: {str(e)}', 'danger')
        return redirect(url_for('financeiro.novo_lancamento'))

@financeiro_bp.route('/financeiro/editar/<int:id>')
@login_required
def editar_lancamento(id):
    """Carrega dados do lançamento para edição"""
    try:
        lancamento = Lancamento.query.get_or_404(id)
        return render_template('financeiro/cadastro_lancamento.html', lancamento=lancamento)
    except Exception as e:
        flash(f'Erro ao carregar dados do lançamento: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/excluir/<int:id>')
@login_required
def excluir_lancamento(id):
    """Exclui um lançamento"""
    try:
        lancamento = Lancamento.query.get_or_404(id)
        descricao_lancamento = lancamento.descricao or f"{lancamento.tipo} de {lancamento.valor_formatado}"
        
        db.session.delete(lancamento)
        db.session.commit()
        
        flash(f'Lançamento excluído', 'info')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir lançamento: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/excluir-comprovante/<int:id>', methods=['POST'])
@login_required
def excluir_comprovante(id):
    """Exclui apenas o comprovante de um lançamento"""
    try:
        import os
        from flask import current_app
        
        lancamento = Lancamento.query.get_or_404(id)
        
        if lancamento.tem_comprovante():
            # Tentar excluir o arquivo físico
            try:
                caminho_completo = os.path.join(current_app.root_path, lancamento.comprovante.lstrip('/'))
                if os.path.exists(caminho_completo):
                    os.remove(caminho_completo)
            except Exception as e:
                current_app.logger.warning(f'Erro ao excluir arquivo físico: {str(e)}')
            
            # Limpar referência no banco
            lancamento.comprovante = None
            db.session.commit()
            
            flash('Comprovante excluído com sucesso!', 'success')
        else:
            flash('Este lançamento não possui comprovante.', 'warning')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir comprovante: {str(e)}', 'danger')
    
    # Redirecionar de volta para a edição
    return redirect(url_for('financeiro.editar_lancamento', id=id))

@financeiro_bp.route('/financeiro/relatorio')
@login_required
def gerar_relatorio():
    """Gera relatório dos lançamentos"""
    try:
        # Buscar todos os lançamentos
        lancamentos = Lancamento.query.order_by(Lancamento.data.desc()).all()
        totais = Lancamento.calcular_totais()
        
        # Por enquanto, vamos gerar um relatório simples em HTML
        # que pode ser impresso ou salvo como PDF pelo browser
        return render_template('financeiro/relatorio.html', 
                             lancamentos=lancamentos, 
                             totais=totais,
                             data_geracao=datetime.now())
        
    except Exception as e:
        flash(f'Erro ao gerar relatório: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/relatorio-caixa')
@login_required
def relatorio_caixa():
    """Gera relatório de caixa interno mensal"""
    try:
        # Pegar mês e ano atual ou da query string
        mes = request.args.get('mes', datetime.now().month, type=int)
        ano = request.args.get('ano', datetime.now().year, type=int)
        
        # Filtrar lançamentos do mês
        lancamentos = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes,
            extract('year', Lancamento.data) == ano
        ).all()
        
        # Inicializar totais
        totais = {
            'entradas_banco': 0,
            'entradas_dinheiro': 0,
            'entradas_pix': 0,
            'dizimos_banco': 0,
            'dizimos_dinheiro': 0,
            'dizimos_pix': 0,
            'ofertas_banco': 0,
            'ofertas_dinheiro': 0,
            'ofertas_pix': 0,
            'saidas_banco': 0,
            'saidas_dinheiro': 0,
            'descontos': 0,
            'total_entradas': 0,
            'total_saidas': 0,
            'saldo_anterior': Lancamento.calcular_saldo_ate_mes_anterior(mes, ano),
            'saldo_mes': 0,
            'saldo_acumulado': 0
        }
        
        # Processar lançamentos
        for lancamento in lancamentos:
            conta = lancamento.conta.lower() if lancamento.conta else 'dinheiro'
            categoria = lancamento.categoria.lower() if lancamento.categoria else ''
            valor = lancamento.valor or 0
            
            if lancamento.tipo == 'Entrada':
                # Entradas por conta
                if 'banco' in conta:
                    totais['entradas_banco'] += valor
                elif 'pix' in conta:
                    totais['entradas_pix'] += valor
                else:
                    totais['entradas_dinheiro'] += valor
                
                # Dízimos por conta
                if 'dízimo' in categoria or 'dizimo' in categoria:
                    if 'banco' in conta:
                        totais['dizimos_banco'] += valor
                    elif 'pix' in conta:
                        totais['dizimos_pix'] += valor
                    else:
                        totais['dizimos_dinheiro'] += valor
                
                # Ofertas por conta
                elif 'oferta' in categoria:
                    if 'banco' in conta:
                        totais['ofertas_banco'] += valor
                    elif 'pix' in conta:
                        totais['ofertas_pix'] += valor
                    else:
                        totais['ofertas_dinheiro'] += valor
                
                totais['total_entradas'] += valor
            
            elif lancamento.tipo == 'Saída':
                # Saídas por conta
                if 'banco' in conta:
                    totais['saidas_banco'] += valor
                else:
                    totais['saidas_dinheiro'] += valor
                
                totais['total_saidas'] += valor
                
                # Descontos (categorias específicas)
                if 'desconto' in categoria or 'taxa' in categoria:
                    totais['descontos'] += valor
        
        # Calcular saldos
        totais['saldo_mes'] = totais['total_entradas'] - totais['total_saidas']
        totais['saldo_acumulado'] = totais['saldo_anterior'] + totais['saldo_mes']
        
        # Buscar dados de configuração da igreja
        config = Configuracao.obter_configuracao()
        dados_igreja = {
            'dirigente': config.presidente if config.presidente else 'Pastor Responsável',
            'tesoureiro': config.primeiro_tesoureiro if config.primeiro_tesoureiro else 'Tesoureiro(a)'
        }
        
        return render_template('financeiro/relatorio_caixa.html',
                             totais=totais,
                             mes=mes,
                             ano=ano,
                             dados_igreja=dados_igreja,
                             data_geracao=datetime.now())
        
    except Exception as e:
        flash(f'Erro ao gerar relatório de caixa: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/relatorio-sede')
@login_required
def relatorio_sede():
    """Gera relatório oficial para igreja sede"""
    try:
        # Pegar mês e ano atual ou da query string
        mes = request.args.get('mes', datetime.now().month, type=int)
        ano = request.args.get('ano', datetime.now().year, type=int)
        
        # Filtrar lançamentos do mês
        lancamentos = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes,
            extract('year', Lancamento.data) == ano
        ).all()
        
        # Buscar dados de configuração da igreja
        config = Configuracao.obter_configuracao()
        dados_igreja = {
            'cidade': config.cidade if config.cidade else 'Tietê',
            'bairro': config.bairro if config.bairro else 'Centro',
            'dirigente': config.dirigente if config.dirigente else 'Pastor Responsável',
            'tesoureiro': config.tesoureiro if config.tesoureiro else 'Tesoureiro(a)',
            'saldo_anterior': Lancamento.calcular_saldo_ate_mes_anterior(mes, ano)
        }
        
        # Inicializar totais
        totais = {
            'dizimos': 0,
            'ofertas_alcadas': 0,
            'outras_ofertas': 0,
            'total_geral': 0,
            'despesas_financeiras': 0,
            'saldo_mes': 0,
            'valor_conselho': 0
        }
        
        # Envios fixos obtidos da base de dados
        envios = DespesaFixaConselho.obter_despesas_para_relatorio()
        
        # Processar lançamentos
        for lancamento in lancamentos:
            categoria = lancamento.categoria.lower() if lancamento.categoria else ''
            valor = lancamento.valor or 0
            
            if lancamento.tipo == 'Entrada':
                if 'dízimo' in categoria or 'dizimo' in categoria:
                    totais['dizimos'] += valor
                elif 'oferta' in categoria:
                    # Lógica padronizada das ofertas:
                    if 'omn' in categoria:
                        # OFERTA OMN - direcionada à convenção
                        totais['ofertas_alcadas'] += valor
                    elif categoria == 'oferta':
                        # OFERTA regular - verificar descrição
                        descricao = lancamento.descricao.lower() if lancamento.descricao else ''
                        if 'oferta' in descricao and 'outras' not in descricao:
                            # Ofertas do ofertório durante cultos
                            totais['ofertas_alcadas'] += valor
                        else:
                            # Ofertas externas, doações, projetos
                            totais['outras_ofertas'] += valor
                    else:
                        # Outras categorias de oferta
                        totais['outras_ofertas'] += valor
                else:
                    totais['outras_ofertas'] += valor
                
                totais['total_geral'] += valor
            
            elif lancamento.tipo == 'Saída':
                totais['despesas_financeiras'] += valor
        
        # Calcular valores finais
        totais['saldo_mes'] = totais['total_geral'] - totais['despesas_financeiras']
        
        # Buscar percentual do conselho das configurações
        config = Configuracao.obter_configuracao()
        percentual = config.percentual_conselho / 100  # Converter para decimal
        totais['valor_conselho'] = totais['total_geral'] * percentual
        
        # Calcular total de envios (envios fixos + valor do conselho)
        total_envio_sede = sum(envios.values()) + totais['valor_conselho']
        
        return render_template('financeiro/relatorio_sede.html',
                             dados_igreja=dados_igreja,
                             totais=totais,
                             envios=envios,
                             total_envio_sede=total_envio_sede,
                             mes=mes,
                             ano=ano,
                             data_geracao=datetime.now())
        
    except Exception as e:
        flash(f'Erro ao gerar relatório da sede: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/despesas-fixas')
@login_required
def gerenciar_despesas_fixas():
    """Interface para gerenciar despesas fixas do conselho"""
    try:
        # Buscar todas as despesas
        despesas_todas = DespesaFixaConselho.query.order_by(DespesaFixaConselho.nome).all()
        despesas_ativas = DespesaFixaConselho.obter_despesas_ativas()
        total_despesas = DespesaFixaConselho.obter_total_despesas_fixas()
        
        # Processar ações de POST
        if request.method == 'POST':
            acao = request.form.get('acao')
            
            if acao == 'criar':
                nova_despesa = DespesaFixaConselho(
                    nome=request.form.get('nome'),
                    descricao=request.form.get('descricao'),
                    categoria=request.form.get('categoria'),
                    valor_padrao=float(request.form.get('valor_padrao', 0)),
                    ativo=True
                )
                db.session.add(nova_despesa)
                db.session.commit()
                flash('Despesa fixa criada com sucesso!', 'success')
                
            elif acao == 'editar':
                despesa_id = request.form.get('id')
                despesa = DespesaFixaConselho.query.get_or_404(despesa_id)
                
                despesa.nome = request.form.get('nome')
                despesa.descricao = request.form.get('descricao')
                despesa.categoria = request.form.get('categoria')
                despesa.valor_padrao = float(request.form.get('valor_padrao', 0))
                despesa.ativo = bool(request.form.get('ativo'))
                
                db.session.commit()
                flash('Despesa fixa atualizada com sucesso!', 'success')
            
            return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
        
        return render_template('financeiro/gerenciar_despesas_fixas.html',
                             despesas_todas=despesas_todas,
                             despesas_ativas=despesas_ativas,
                             total_despesas=total_despesas)
    
    except Exception as e:
        flash(f'Erro ao gerenciar despesas fixas: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

# Permitir POST no método acima
gerenciar_despesas_fixas.methods = ['GET', 'POST']

@financeiro_bp.route('/financeiro/despesas-fixas/toggle/<int:id>')
@login_required
def toggle_despesa_fixa(id):
    """Alterna o status ativo/inativo de uma despesa fixa"""
    try:
        despesa = DespesaFixaConselho.query.get_or_404(id)
        despesa.ativo = not despesa.ativo
        
        db.session.commit()
        
        status = "ativada" if despesa.ativo else "desativada"
        flash(f'Despesa "{despesa.nome}" {status} com sucesso!', 'info')
        
    except Exception as e:
        flash(f'Erro ao alterar status da despesa: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

@financeiro_bp.route('/financeiro/relatorio-caixa/preview')
@login_required
def relatorio_caixa_preview():
    """Preview HTML do relatório de caixa antes de gerar PDF"""
    try:
        # Pegar mês e ano atual ou da query string
        mes = request.args.get('mes', datetime.now().month, type=int)
        ano = request.args.get('ano', datetime.now().year, type=int)
        
        # Filtrar lançamentos do mês
        lancamentos = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes,
            extract('year', Lancamento.data) == ano
        ).all()
        
        # Calcular totais (usando mesma lógica da rota principal)
        totais = {
            'entradas_banco': 0,
            'entradas_dinheiro': 0,
            'entradas_pix': 0,
            'total_entradas': 0,
            'saidas_banco': 0,
            'saidas_dinheiro': 0,
            'saidas_pix': 0,
            'total_saidas': 0,
            'saldo_periodo': 0,
            'entradas_por_categoria': {},
            'saidas_por_categoria': {}
        }
        
        # Processar lançamentos para calcular totais
        for lancamento in lancamentos:
            valor = lancamento.valor or 0
            conta = lancamento.conta.lower() if lancamento.conta else ''
            categoria = lancamento.categoria or 'Outros'
            
            if lancamento.tipo == 'Entrada':
                if 'banco' in conta:
                    totais['entradas_banco'] += valor
                elif 'pix' in conta:
                    totais['entradas_pix'] += valor
                else:
                    totais['entradas_dinheiro'] += valor
                
                totais['total_entradas'] += valor
                
                # Agrupar por categoria
                if categoria not in totais['entradas_por_categoria']:
                    totais['entradas_por_categoria'][categoria] = 0
                totais['entradas_por_categoria'][categoria] += valor
                
            elif lancamento.tipo == 'Saída':
                if 'banco' in conta:
                    totais['saidas_banco'] += valor
                elif 'pix' in conta:
                    totais['saidas_pix'] += valor
                else:
                    totais['saidas_dinheiro'] += valor
                
                totais['total_saidas'] += valor
                
                # Agrupar por categoria
                if categoria not in totais['saidas_por_categoria']:
                    totais['saidas_por_categoria'][categoria] = 0
                totais['saidas_por_categoria'][categoria] += valor
        
        # Calcular saldo do período
        totais['saldo_periodo'] = totais['total_entradas'] - totais['total_saidas']
        
        # Buscar configuração da igreja
        config = Configuracao.obter_configuracao()
        dados_igreja = {
            'nome': config.nome_igreja if config else 'Igreja OBPC',
            'endereco': config.endereco if config else '',
            'cidade': config.cidade if config else '',
            'pastor': config.pastor if config else '',
            'tesoureiro': config.tesoureiro if config else '',
            'logo': config.logo_igreja if config else None
        }
        
        return render_template('financeiro/relatorio_caixa_preview.html',
                             lancamentos=lancamentos,
                             mes=mes,
                             ano=ano,
                             totais=totais,
                             dados_igreja=dados_igreja,
                             data_geracao=datetime.now())
    
    except Exception as e:
        flash(f'Erro ao gerar preview do relatório: {str(e)}', 'danger')
        return redirect(url_for('financeiro.relatorio_caixa', mes=mes, ano=ano))

@financeiro_bp.route('/financeiro/relatorio-sede/preview')
@login_required  
def relatorio_sede_preview():
    """Preview HTML do relatório oficial para sede"""
    try:
        # Pegar mês e ano atual ou da query string
        mes = request.args.get('mes', datetime.now().month, type=int)
        ano = request.args.get('ano', datetime.now().year, type=int)
        
        # Filtrar lançamentos do mês
        lancamentos = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes,
            extract('year', Lancamento.data) == ano
        ).all()
        
        # Calcular totais específicos para sede usando a mesma lógica da rota principal
        totais = {
            'dizimos': 0,
            'ofertas_alcadas': 0,
            'outras_ofertas': 0,
            'total_entradas': 0,
            'total_saidas': 0,
            'saidas_por_categoria': {},
            'saldo_final': 0,
            'valor_conselho': 0,
            'trinta_porcento_conselho': 0,
            'despesas_fixas_conselho': 0,
            'total_envio_sede': 0
        }
        
        # Processar lançamentos
        for lancamento in lancamentos:
            categoria = lancamento.categoria.lower() if lancamento.categoria else ''
            valor = lancamento.valor or 0
            
            if lancamento.tipo == 'Entrada':
                if 'dízimo' in categoria or 'dizimo' in categoria:
                    totais['dizimos'] += valor
                elif 'oferta' in categoria:
                    # Lógica padronizada das ofertas:
                    if 'omn' in categoria:
                        # OFERTA OMN - direcionada à convenção
                        totais['ofertas_alcadas'] += valor
                    elif categoria == 'oferta':
                        # OFERTA regular - verificar descrição
                        descricao = lancamento.descricao.lower() if lancamento.descricao else ''
                        if 'oferta' in descricao and 'outras' not in descricao:
                            # Ofertas do ofertório durante cultos
                            totais['ofertas_alcadas'] += valor
                        else:
                            # Ofertas externas, doações, projetos
                            totais['outras_ofertas'] += valor
                    else:
                        # Outras categorias de oferta
                        totais['outras_ofertas'] += valor
                else:
                    totais['outras_ofertas'] += valor
                
                totais['total_entradas'] += valor
            
            elif lancamento.tipo == 'Saída':
                totais['total_saidas'] += valor
                # Agrupar saídas por categoria
                if categoria not in totais['saidas_por_categoria']:
                    totais['saidas_por_categoria'][categoria] = 0
                totais['saidas_por_categoria'][categoria] += valor
        
        # Calcular valores finais
        totais['saldo_final'] = totais['total_entradas'] - totais['total_saidas']
        
        # Buscar percentual do conselho das configurações
        config = Configuracao.obter_configuracao()
        percentual = config.percentual_conselho / 100 if config else 0.30  # Default 30%
        totais['valor_conselho'] = totais['total_entradas']
        totais['trinta_porcento_conselho'] = totais['total_entradas'] * percentual
        
        # Buscar despesas fixas do conselho
        despesas_fixas = DespesaFixaConselho.query.filter_by(ativo=True).all()
        totais['despesas_fixas_conselho'] = sum(d.valor for d in despesas_fixas)
        
        # Calcular total de envio para sede
        totais['total_envio_sede'] = totais['trinta_porcento_conselho'] + totais['despesas_fixas_conselho']
        
        # Buscar configuração da igreja
        config = Configuracao.obter_configuracao()
        dados_igreja = {
            'nome': config.nome_igreja if config else 'Igreja OBPC',
            'endereco': config.endereco if config else '',
            'cidade': config.cidade if config else '',
            'pastor': config.pastor if config else '',
            'tesoureiro': config.tesoureiro if config else '',
            'logo': config.logo_igreja if config else None
        }
        
        return render_template('financeiro/relatorio_sede_preview.html',
                             lancamentos=lancamentos,
                             mes=mes,
                             ano=ano,
                             totais=totais,
                             dados_igreja=dados_igreja,
                             data_geracao=datetime.now())
    
    except Exception as e:
        flash(f'Erro ao gerar preview do relatório: {str(e)}', 'danger')
        return redirect(url_for('financeiro.relatorio_sede', mes=mes, ano=ano))

@financeiro_bp.route('/financeiro/relatorio-caixa/pdf')
@login_required
def relatorio_caixa_pdf():
    """Gera PDF do relatório de caixa interno"""
    try:
        # Pegar mês e ano atual ou da query string
        mes = request.args.get('mes', datetime.now().month, type=int)
        ano = request.args.get('ano', datetime.now().year, type=int)
        
        # Filtrar lançamentos do mês
        lancamentos = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes,
            extract('year', Lancamento.data) == ano
        ).all()
        
        # Inicializar totais (mesmo código da rota HTML)
        totais = {
            'entradas_banco': 0,
            'entradas_dinheiro': 0,
            'entradas_pix': 0,
            'dizimos_banco': 0,
            'dizimos_dinheiro': 0,
            'dizimos_pix': 0,
            'ofertas_banco': 0,
            'ofertas_dinheiro': 0,
            'ofertas_pix': 0,
            'saidas_banco': 0,
            'saidas_dinheiro': 0,
            'descontos': 0,
            'total_entradas': 0,
            'total_saidas': 0,
            'saldo_anterior': Lancamento.calcular_saldo_ate_mes_anterior(mes, ano),
            'saldo_mes': 0,
            'saldo_acumulado': 0
        }
        
        # Processar lançamentos (mesmo código da rota HTML)
        for lancamento in lancamentos:
            conta = lancamento.conta.lower() if lancamento.conta else 'dinheiro'
            categoria = lancamento.categoria.lower() if lancamento.categoria else ''
            valor = lancamento.valor or 0
            
            if lancamento.tipo == 'Entrada':
                # Entradas por conta
                if 'banco' in conta:
                    totais['entradas_banco'] += valor
                elif 'pix' in conta:
                    totais['entradas_pix'] += valor
                else:
                    totais['entradas_dinheiro'] += valor
                
                # Dízimos por conta
                if 'dízimo' in categoria or 'dizimo' in categoria:
                    if 'banco' in conta:
                        totais['dizimos_banco'] += valor
                    elif 'pix' in conta:
                        totais['dizimos_pix'] += valor
                    else:
                        totais['dizimos_dinheiro'] += valor
                
                # Ofertas por conta
                elif 'oferta' in categoria:
                    if 'banco' in conta:
                        totais['ofertas_banco'] += valor
                    elif 'pix' in conta:
                        totais['ofertas_pix'] += valor
                    else:
                        totais['ofertas_dinheiro'] += valor
                
                totais['total_entradas'] += valor
            
            elif lancamento.tipo == 'Saída':
                # Saídas por conta
                if 'banco' in conta:
                    totais['saidas_banco'] += valor
                else:
                    totais['saidas_dinheiro'] += valor
                
                totais['total_saidas'] += valor
                
                # Descontos (categorias específicas)
                if 'desconto' in categoria or 'taxa' in categoria:
                    totais['descontos'] += valor
        
        # Calcular saldos
        totais['saldo_mes'] = totais['total_entradas'] - totais['total_saidas']
        totais['saldo_acumulado'] = totais['saldo_anterior'] + totais['saldo_mes']
        
        # Obter configurações do sistema
        config = Configuracao.obter_configuracao()
        
        # Gerar PDF com ReportLab profissional
        relatorio = RelatorioFinanceiro(config)
        pdf_buffer = relatorio.gerar_relatorio_caixa(lancamentos, mes, ano, totais['saldo_anterior'])
        
        # Gerar nome do arquivo
        nome_arquivo = gerar_nome_arquivo_relatorio('caixa', mes, ano)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Erro ao gerar PDF do relatório de caixa: {str(e)}', 'danger')
        return redirect(url_for('financeiro.relatorio_caixa'))

@financeiro_bp.route('/financeiro/relatorio-sede/pdf')
@login_required
def relatorio_sede_pdf():
    """Gera PDF do relatório oficial para sede"""
    try:
        # Pegar mês e ano atual ou da query string
        mes = request.args.get('mes', datetime.now().month, type=int)
        ano = request.args.get('ano', datetime.now().year, type=int)
        
        # Filtrar lançamentos do mês
        lancamentos = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes,
            extract('year', Lancamento.data) == ano
        ).all()
        
        # Buscar dados de configuração da igreja
        config = Configuracao.obter_configuracao()
        dados_igreja = {
            'cidade': config.cidade if config.cidade else 'Tietê',
            'bairro': config.bairro if config.bairro else 'Centro',
            'dirigente': config.dirigente if config.dirigente else 'Pastor Responsável',
            'tesoureiro': config.tesoureiro if config.tesoureiro else 'Tesoureiro(a)',
            'saldo_anterior': Lancamento.calcular_saldo_ate_mes_anterior(mes, ano)
        }
        
        # Inicializar totais (mesmo código da rota HTML)
        totais = {
            'dizimos': 0,
            'ofertas_alcadas': 0,
            'outras_ofertas': 0,
            'total_geral': 0,
            'despesas_financeiras': 0,
            'saldo_mes': 0,
            'valor_conselho': 0
        }
        
        # Envios fixos obtidos da base de dados
        envios = DespesaFixaConselho.obter_despesas_para_relatorio()
        
        # Processar lançamentos (mesmo código da rota HTML)
        for lancamento in lancamentos:
            categoria = lancamento.categoria.lower() if lancamento.categoria else ''
            valor = lancamento.valor or 0
            
            if lancamento.tipo == 'Entrada':
                if 'dízimo' in categoria or 'dizimo' in categoria:
                    totais['dizimos'] += valor
                elif 'oferta' in categoria:
                    # Lógica padronizada das ofertas:
                    if 'omn' in categoria:
                        # OFERTA OMN - direcionada à convenção
                        totais['ofertas_alcadas'] += valor
                    elif categoria == 'oferta':
                        # OFERTA regular - verificar descrição
                        descricao = lancamento.descricao.lower() if lancamento.descricao else ''
                        if 'oferta' in descricao and 'outras' not in descricao:
                            # Ofertas do ofertório durante cultos
                            totais['ofertas_alcadas'] += valor
                        else:
                            # Ofertas externas, doações, projetos
                            totais['outras_ofertas'] += valor
                    else:
                        # Outras categorias de oferta
                        totais['outras_ofertas'] += valor
                else:
                    totais['outras_ofertas'] += valor
                
                totais['total_geral'] += valor
            
            elif lancamento.tipo == 'Saída':
                totais['despesas_financeiras'] += valor
        
        # Calcular valores finais
        totais['saldo_mes'] = totais['total_geral'] - totais['despesas_financeiras']
        
        # Buscar percentual do conselho das configurações
        config = Configuracao.obter_configuracao()
        percentual = config.percentual_conselho / 100  # Converter para decimal
        totais['valor_conselho'] = totais['total_geral'] * percentual
        
        # Calcular total de envios (envios fixos + valor do conselho)
        total_envio_sede = sum(envios.values()) + totais['valor_conselho']
        
        # Obter configurações do sistema
        config = Configuracao.obter_configuracao()
        
        # Gerar PDF com ReportLab profissional
        relatorio = RelatorioFinanceiro(config)
        pdf_buffer = relatorio.gerar_relatorio_sede(lancamentos, mes, ano, dados_igreja['saldo_anterior'])
        
        # Gerar nome do arquivo
        nome_arquivo = gerar_nome_arquivo_relatorio('sede', mes, ano)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Erro ao gerar PDF do relatório da sede: {str(e)}', 'danger')
        return redirect(url_for('financeiro.relatorio_sede'))

@financeiro_bp.route('/financeiro/conciliacao/dashboard')
@login_required
def dashboard_conciliacao():
    """Dashboard básico de conciliação - versão temporária"""
    try:
        # Estatísticas básicas
        total_lancamentos = Lancamento.query.count()
        manuais = Lancamento.query.filter_by(origem='manual').count()
        importados = Lancamento.query.filter_by(origem='importado').count()
        conciliados = Lancamento.query.filter_by(conciliado=True).count()
        
        # Lançamentos pendentes
        manuais_pendentes = Lancamento.query.filter_by(origem='manual', conciliado=False).limit(10).all()
        importados_pendentes = Lancamento.query.filter_by(origem='importado', conciliado=False).limit(10).all()
        
        indicadores = {
            'totais': {
                'lancamentos': total_lancamentos,
                'manuais': manuais,
                'importados': importados,
                'conciliados': conciliados,
                'pendentes': total_lancamentos - conciliados,
                'duplicatas': 0
            },
            'percentuais': {
                'conciliado': round((conciliados / total_lancamentos * 100) if total_lancamentos > 0 else 0, 1),
                'importados': round((importados / total_lancamentos * 100) if total_lancamentos > 0 else 0, 1),
                'pendentes': round(((total_lancamentos - conciliados) / total_lancamentos * 100) if total_lancamentos > 0 else 0, 1)
            },
            'historicos_recentes': [],
            'top_regras': []
        }
        
        return render_template('financeiro/dashboard_conciliacao.html',
                             indicadores=indicadores,
                             manuais_pendentes=manuais_pendentes,
                             importados_pendentes=importados_pendentes,
                             importacoes_recentes=[],
                             discrepancias=[])
        
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))