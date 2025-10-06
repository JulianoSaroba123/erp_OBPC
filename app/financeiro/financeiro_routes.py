from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from app.configuracoes.configuracoes_model import Configuracao
from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro, gerar_nome_arquivo_relatorio
from datetime import datetime, date
from sqlalchemy import extract, or_
from decimal import Decimal

financeiro_bp = Blueprint('financeiro', __name__, template_folder='templates')

@financeiro_bp.route('/financeiro')
@login_required
def lista_lancamentos():
    """Lista todos os lançamentos com filtros avançados"""
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
                             })
                             
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
    return render_template('financeiro/cadastro_lancamento.html')

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
        observacoes = request.form.get('observacoes', '').strip()
        
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
            lancamento.observacoes = observacoes if observacoes else None
            
            flash('Lançamento atualizado', 'info')
        else:
            # Criar novo lançamento
            novo_lancamento = Lancamento(
                data=data_obj,
                tipo=tipo,
                categoria=categoria if categoria else None,
                descricao=descricao if descricao else None,
                valor=valor,
                conta=conta,
                observacoes=observacoes if observacoes else None
            )
            
            db.session.add(novo_lancamento)
            flash('Lançamento cadastrado', 'info')
        
        db.session.commit()
        return redirect(url_for('financeiro.lista_lancamentos'))
        
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
        
        return render_template('financeiro/relatorio_caixa.html',
                             totais=totais,
                             mes=mes,
                             ano=ano,
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
        
        # Dados fixos da igreja
        dados_igreja = {
            'cidade': 'Tietê',
            'bairro': 'Centro',
            'dirigente': 'Pastor João Silva',
            'tesoureiro': 'Maria Santos',
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
        
        # Envios fixos (valores configuráveis)
        envios = {
            'oferta_voluntaria_conchas': 50.00,
            'site': 25.00,
            'projeto_filipe': 100.00,
            'forca_para_viver': 30.00,
            'contador_sede': 150.00
        }
        
        # Processar lançamentos
        for lancamento in lancamentos:
            categoria = lancamento.categoria.lower() if lancamento.categoria else ''
            valor = lancamento.valor or 0
            
            if lancamento.tipo == 'Entrada':
                if 'dízimo' in categoria or 'dizimo' in categoria:
                    totais['dizimos'] += valor
                elif 'oferta' in categoria and ('alçada' in categoria or 'alcada' in categoria):
                    totais['ofertas_alcadas'] += valor
                else:
                    totais['outras_ofertas'] += valor
                
                totais['total_geral'] += valor
            
            elif lancamento.tipo == 'Saída':
                totais['despesas_financeiras'] += valor
        
        # Calcular valores finais
        totais['saldo_mes'] = totais['total_geral'] - totais['despesas_financeiras']
        totais['valor_conselho'] = totais['total_geral'] * 0.10
        
        # Calcular total de envios
        total_envio_sede = sum(envios.values())
        
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
        
        # Dados fixos da igreja
        dados_igreja = {
            'cidade': 'Tietê',
            'bairro': 'Centro',
            'dirigente': 'Pastor João Silva',
            'tesoureiro': 'Maria Santos',
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
        
        # Envios fixos (valores configuráveis)
        envios = {
            'oferta_voluntaria_conchas': 50.00,
            'site': 25.00,
            'projeto_filipe': 100.00,
            'forca_para_viver': 30.00,
            'contador_sede': 150.00
        }
        
        # Processar lançamentos (mesmo código da rota HTML)
        for lancamento in lancamentos:
            categoria = lancamento.categoria.lower() if lancamento.categoria else ''
            valor = lancamento.valor or 0
            
            if lancamento.tipo == 'Entrada':
                if 'dízimo' in categoria or 'dizimo' in categoria:
                    totais['dizimos'] += valor
                elif 'oferta' in categoria and ('alçada' in categoria or 'alcada' in categoria):
                    totais['ofertas_alcadas'] += valor
                else:
                    totais['outras_ofertas'] += valor
                
                totais['total_geral'] += valor
            
            elif lancamento.tipo == 'Saída':
                totais['despesas_financeiras'] += valor
        
        # Calcular valores finais
        totais['saldo_mes'] = totais['total_geral'] - totais['despesas_financeiras']
        totais['valor_conselho'] = totais['total_geral'] * 0.10
        
        # Calcular total de envios
        total_envio_sede = sum(envios.values())
        
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