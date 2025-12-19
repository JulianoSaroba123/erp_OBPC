"""
Rotas adicionais para funcionalidades avançadas de conciliação bancária
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento, ConciliacaoHistorico, ConciliacaoPar, ImportacaoExtrato
from app.financeiro.utils.conciliacao_avancada import ConciliadorAvancado, ImportadorExtrato, GeradorRelatorios
from app.configuracoes.configuracoes_model import Configuracao

conciliacao_bp = Blueprint('conciliacao', __name__, template_folder='templates')

UPLOAD_FOLDER = 'app/static/uploads/extratos'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@conciliacao_bp.route('/financeiro/conciliacao/dashboard')
@login_required
def dashboard_conciliacao():
    """Dashboard principal de conciliação bancária"""
    try:
        # Gerar indicadores
        indicadores = GeradorRelatorios.gerar_dashboard_indicadores()
        
        # Lançamentos pendentes de conciliação
        manuais_pendentes = Lancamento.query.filter_by(
            origem='manual', conciliado=False
        ).order_by(Lancamento.data.desc()).limit(10).all()
        
        importados_pendentes = Lancamento.query.filter_by(
            origem='importado', conciliado=False
        ).order_by(Lancamento.data.desc()).limit(10).all()
        
        # Últimas importações
        importacoes_recentes = ImportacaoExtrato.query.order_by(
            ImportacaoExtrato.data_importacao.desc()
        ).limit(5).all()
        
        # Possíveis discrepâncias
        discrepancias = GeradorRelatorios.gerar_relatorio_discrepancias()
        
        return render_template('financeiro/dashboard_conciliacao.html',
                             indicadores=indicadores,
                             manuais_pendentes=manuais_pendentes,
                             importados_pendentes=importados_pendentes,
                             importacoes_recentes=importacoes_recentes,
                             discrepancias=discrepancias[:5])  # Limitar a 5 discrepâncias
        
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@conciliacao_bp.route('/financeiro/conciliacao/importar-extrato')
@login_required
def importar_extrato():
    """Página para importar extratos bancários"""
    return render_template('financeiro/importar_extrato.html')

@conciliacao_bp.route('/financeiro/conciliacao/upload-extrato', methods=['POST'])
@login_required
def upload_extrato():
    """Processa upload de arquivo de extrato"""
    try:
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(url_for('conciliacao.importar_extrato'))
        
        file = request.files['arquivo']
        banco = request.form.get('banco', 'generico')
        
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(url_for('conciliacao.importar_extrato'))
        
        if not allowed_file(file.filename):
            flash('Tipo de arquivo não permitido. Use CSV, XLS ou XLSX', 'danger')
            return redirect(url_for('conciliacao.importar_extrato'))
        
        # Salvar arquivo temporariamente
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Importar extrato
        importador = ImportadorExtrato()
        resultado = importador.importar_arquivo(
            file_path, 
            banco, 
            current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        )
        
        # Remover arquivo temporário
        try:
            os.remove(file_path)
        except:
            pass
        
        if resultado['sucesso']:
            flash(f"Extrato importado com sucesso! "
                  f"Processados: {resultado['registros_processados']}, "
                  f"Duplicados: {resultado['registros_duplicados']}, "
                  f"Erros: {resultado['registros_erro']}", 'success')
                  
            # Executar conciliação automática se houver registros processados
            if resultado['registros_processados'] > 0:
                return redirect(url_for('conciliacao.executar_conciliacao_auto', 
                                      importacao_id=resultado['importacao_id']))
        else:
            flash(f"Erro na importação: {'; '.join(resultado['erros'])}", 'danger')
        
        return redirect(url_for('conciliacao.dashboard_conciliacao'))
        
    except Exception as e:
        flash(f'Erro no upload: {str(e)}', 'danger')
        return redirect(url_for('conciliacao.importar_extrato'))

@conciliacao_bp.route('/financeiro/conciliacao/executar-automatica')
@conciliacao_bp.route('/financeiro/conciliacao/executar-automatica/<int:importacao_id>')
@login_required
def executar_conciliacao_auto(importacao_id=None):
    """Executa conciliação automática"""
    try:
        conciliador = ConciliadorAvancado()
        resultado = conciliador.conciliar_automatico(
            current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        )
        
        if 'erro' in resultado:
            flash(f"Erro na conciliação: {resultado['erro']}", 'danger')
        else:
            if resultado['conciliados'] > 0:
                flash(f"Conciliação automática concluída! "
                      f"Conciliados: {resultado['conciliados']} pares "
                      f"em {resultado['tempo_execucao']:.2f} segundos", 'success')
            else:
                flash("Nenhum par para conciliação automática encontrado", 'info')
        
        return redirect(url_for('conciliacao.dashboard_conciliacao'))
        
    except Exception as e:
        flash(f'Erro na conciliação automática: {str(e)}', 'danger')
        return redirect(url_for('conciliacao.dashboard_conciliacao'))

@conciliacao_bp.route('/financeiro/conciliacao/manual')
@login_required
def conciliacao_manual():
    """Interface para conciliação manual"""
    try:
        # Parâmetros de filtro
        data_inicial = request.args.get('data_inicial', '')
        data_final = request.args.get('data_final', '')
        valor_min = request.args.get('valor_min', '')
        valor_max = request.args.get('valor_max', '')
        
        # Query base para lançamentos não conciliados
        query_manuais = Lancamento.query.filter_by(origem='manual', conciliado=False)
        query_importados = Lancamento.query.filter_by(origem='importado', conciliado=False)
        
        # Aplicar filtros se fornecidos
        if data_inicial:
            try:
                data_ini = datetime.strptime(data_inicial, '%Y-%m-%d').date()
                query_manuais = query_manuais.filter(Lancamento.data >= data_ini)
                query_importados = query_importados.filter(Lancamento.data >= data_ini)
            except ValueError:
                pass
        
        if data_final:
            try:
                data_fim = datetime.strptime(data_final, '%Y-%m-%d').date()
                query_manuais = query_manuais.filter(Lancamento.data <= data_fim)
                query_importados = query_importados.filter(Lancamento.data <= data_fim)
            except ValueError:
                pass
        
        if valor_min:
            try:
                val_min = float(valor_min)
                query_manuais = query_manuais.filter(Lancamento.valor >= val_min)
                query_importados = query_importados.filter(Lancamento.valor >= val_min)
            except ValueError:
                pass
        
        if valor_max:
            try:
                val_max = float(valor_max)
                query_manuais = query_manuais.filter(Lancamento.valor <= val_max)
                query_importados = query_importados.filter(Lancamento.valor <= val_max)
            except ValueError:
                pass
        
        # Executar queries
        manuais = query_manuais.order_by(Lancamento.data.desc()).limit(50).all()
        importados = query_importados.order_by(Lancamento.data.desc()).limit(50).all()
        
        return render_template('financeiro/conciliacao_manual.html',
                             manuais=manuais,
                             importados=importados,
                             filtros={
                                 'data_inicial': data_inicial,
                                 'data_final': data_final,
                                 'valor_min': valor_min,
                                 'valor_max': valor_max
                             })
        
    except Exception as e:
        flash(f'Erro ao carregar conciliação manual: {str(e)}', 'danger')
        return redirect(url_for('conciliacao.dashboard_conciliacao'))

@conciliacao_bp.route('/financeiro/conciliacao/criar-par', methods=['POST'])
@login_required
def criar_par_conciliacao():
    """Cria par de conciliação manual"""
    try:
        manual_id = request.form.get('manual_id', type=int)
        importado_id = request.form.get('importado_id', type=int)
        
        if not manual_id or not importado_id:
            return jsonify({'success': False, 'error': 'IDs inválidos'})
        
        # Buscar lançamentos
        manual = Lancamento.query.get(manual_id)
        importado = Lancamento.query.get(importado_id)
        
        if not manual or not importado:
            return jsonify({'success': False, 'error': 'Lançamentos não encontrados'})
        
        if manual.conciliado or importado.conciliado:
            return jsonify({'success': False, 'error': 'Um dos lançamentos já está conciliado'})
        
        # Criar histórico
        historico = ConciliacaoHistorico(
            usuario=current_user.nome if hasattr(current_user, 'nome') else 'Sistema',
            tipo_conciliacao='manual',
            total_conciliados=1,
            total_pendentes=0
        )
        db.session.add(historico)
        db.session.flush()
        
        # Criar par
        par = ConciliacaoPar(
            historico_id=historico.id,
            lancamento_manual_id=manual_id,
            lancamento_importado_id=importado_id,
            score_similaridade=1.0,  # Manual = 100%
            regra_aplicada='manual',
            metodo_conciliacao='manual',
            usuario=current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        )
        
        # Marcar como conciliados
        manual.conciliado = True
        manual.conciliado_em = datetime.now()
        manual.conciliado_por = current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        
        importado.conciliado = True
        importado.conciliado_em = datetime.now()
        importado.conciliado_por = current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        
        db.session.add(par)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Par de conciliação criado com sucesso',
            'par_id': par.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@conciliacao_bp.route('/financeiro/conciliacao/desfazer-par/<int:par_id>', methods=['POST'])
@login_required
def desfazer_par_conciliacao(par_id):
    """Desfaz um par de conciliação"""
    try:
        par = ConciliacaoPar.query.get(par_id)
        if not par:
            return jsonify({'success': False, 'error': 'Par não encontrado'})
        
        if not par.ativo:
            return jsonify({'success': False, 'error': 'Par já foi desfeito'})
        
        par.desfazer()
        
        return jsonify({
            'success': True,
            'message': 'Conciliação desfeita com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@conciliacao_bp.route('/financeiro/conciliacao/historico')
@login_required
def historico_conciliacao():
    """Histórico de conciliações realizadas"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        historicos = ConciliacaoHistorico.query.order_by(
            ConciliacaoHistorico.data_conciliacao.desc()
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('financeiro/historico_conciliacao.html',
                             historicos=historicos)
        
    except Exception as e:
        flash(f'Erro ao carregar histórico: {str(e)}', 'danger')
        return redirect(url_for('conciliacao.dashboard_conciliacao'))

@conciliacao_bp.route('/financeiro/conciliacao/relatorio-discrepancias')
@login_required
def relatorio_discrepancias():
    """Relatório detalhado de discrepâncias"""
    try:
        discrepancias = GeradorRelatorios.gerar_relatorio_discrepancias()
        
        return render_template('financeiro/relatorio_discrepancias.html',
                             discrepancias=discrepancias)
        
    except Exception as e:
        flash(f'Erro ao gerar relatório: {str(e)}', 'danger')
        return redirect(url_for('conciliacao.dashboard_conciliacao'))

@conciliacao_bp.route('/financeiro/conciliacao/api/sugestoes/<int:lancamento_id>')
@login_required
def api_sugestoes_conciliacao(lancamento_id):
    """API para obter sugestões de conciliação para um lançamento"""
    try:
        lancamento = Lancamento.query.get(lancamento_id)
        if not lancamento:
            return jsonify({'error': 'Lançamento não encontrado'})
        
        # Buscar lançamentos de origem oposta
        origem_oposta = 'importado' if lancamento.origem == 'manual' else 'manual'
        candidatos = Lancamento.query.filter_by(
            origem=origem_oposta, 
            conciliado=False
        ).all()
        
        # Calcular scores usando o conciliador
        conciliador = ConciliadorAvancado()
        sugestoes = []
        
        for candidato in candidatos:
            for regra in conciliador.regras_conciliacao:
                if lancamento.origem == 'manual':
                    score, regra_nome = regra(lancamento, candidato)
                else:
                    score, regra_nome = regra(candidato, lancamento)
                
                if score >= 0.7:  # Apenas sugestões com score razoável
                    sugestoes.append({
                        'lancamento': candidato.to_dict(),
                        'score': round(score, 2),
                        'regra': regra_nome,
                        'compatibilidade': 'alta' if score >= 0.9 else 'media' if score >= 0.8 else 'baixa'
                    })
                    break  # Usar apenas a primeira regra que retorna score válido
        
        # Ordenar por score decrescente
        sugestoes.sort(key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            'sugestoes': sugestoes[:10],  # Limitar a 10 sugestões
            'total': len(sugestoes)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@conciliacao_bp.route('/financeiro/conciliacao/exportar-dados')
@login_required
def exportar_dados_conciliacao():
    """Exporta dados de conciliação em CSV"""
    try:
        # Buscar todos os pares ativos
        pares = db.session.query(ConciliacaoPar).join(
            Lancamento, ConciliacaoPar.lancamento_manual_id == Lancamento.id
        ).filter(ConciliacaoPar.ativo == True).all()
        
        # Criar CSV em memória
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow([
            'ID Par', 'Data Conciliação', 'Usuário', 'Método',
            'Manual ID', 'Manual Data', 'Manual Descrição', 'Manual Valor',
            'Importado ID', 'Importado Data', 'Importado Descrição', 'Importado Valor',
            'Score', 'Regra Aplicada'
        ])
        
        # Dados
        for par in pares:
            manual = par.lancamento_manual
            importado = par.lancamento_importado
            
            writer.writerow([
                par.id,
                par.criado_em.strftime('%Y-%m-%d %H:%M:%S'),
                par.usuario,
                par.metodo_conciliacao,
                manual.id if manual else '',
                manual.data.strftime('%Y-%m-%d') if manual and manual.data else '',
                manual.descricao if manual else '',
                manual.valor if manual else '',
                importado.id if importado else '',
                importado.data.strftime('%Y-%m-%d') if importado and importado.data else '',
                importado.descricao if importado else '',
                importado.valor if importado else '',
                par.score_similaridade,
                par.regra_aplicada
            ])
        
        # Preparar resposta
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=conciliacao_dados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
        
    except Exception as e:
        flash(f'Erro ao exportar dados: {str(e)}', 'danger')
        return redirect(url_for('conciliacao.dashboard_conciliacao'))