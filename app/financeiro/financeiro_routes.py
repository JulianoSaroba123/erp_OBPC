from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, session
from flask_login import login_required
from app.extensoes import db
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.financeiro_model import ConciliacaoHistorico, ConciliacaoPar
from app.financeiro.projeto_model import Projeto
from app.financeiro.despesas_fixas_model import DespesaFixaConselho
from app.configuracoes.configuracoes_model import Configuracao
from app.utils.gerar_pdf_reportlab import RelatorioFinanceiro, gerar_nome_arquivo_relatorio
from datetime import datetime, date
from sqlalchemy import extract, or_, and_, func
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

# ========== ROTAS ESPECÍFICAS (devem vir ANTES de /financeiro) ==========

@financeiro_bp.route('/financeiro/caixa-destinacoes', endpoint='caixa_destinacoes')
@login_required
def caixa_destinacoes():
    """Caixa separado para controlar valores destinados a projetos específicos"""
    print(">>> ROTA CAIXA_DESTINACOES CHAMADA!")
    try:
        # Obter filtros
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int, default=datetime.now().year)
        projeto_id = request.args.get('projeto_id', type=int)
        
        # Buscar todos os projetos
        projetos = Projeto.query.order_by(Projeto.nome).all()
        
        # Calcular totais por projeto
        projetos_com_totais = []
        for projeto in projetos:
            totais_projeto = projeto.calcular_totais()
            
            # Filtrar lançamentos do projeto
            query = Lancamento.query.filter(Lancamento.projeto_id == projeto.id)
            
            # Aplicar filtro de período
            if mes:
                query = query.filter(
                    extract('month', Lancamento.data) == mes,
                    extract('year', Lancamento.data) == ano
                )
            elif ano:
                query = query.filter(extract('year', Lancamento.data) == ano)
            
            lancamentos_projeto = query.order_by(Lancamento.data.asc()).all()
            
            if lancamentos_projeto or (not mes and not projeto_id):  # Mostrar projetos sem lançamentos apenas na visão geral
                projetos_com_totais.append({
                    'projeto': projeto,
                    'totais': totais_projeto,
                    'lancamentos': lancamentos_projeto
                })
        
        # Buscar lançamentos sem projeto (legado)
        query_sem_projeto = Lancamento.query.filter(Lancamento.projeto_id == None)
        
        # Aplicar filtro de período
        if mes:
            query_sem_projeto = query_sem_projeto.filter(
                extract('month', Lancamento.data) == mes,
                extract('year', Lancamento.data) == ano
            )
        elif ano:
            query_sem_projeto = query_sem_projeto.filter(extract('year', Lancamento.data) == ano)
        
        # Filtrar apenas OUTRAS OFERTAS e DESTINAÇÃO para lançamentos sem projeto
        lancamentos_sem_projeto = query_sem_projeto.filter(
            or_(
                and_(
                    Lancamento.tipo == 'Entrada',
                    func.upper(Lancamento.categoria) == 'OUTRAS OFERTAS'
                ),
                and_(
                    Lancamento.tipo == 'Saída',
                    func.upper(Lancamento.categoria) == 'DESTINAÇÃO'
                )
            )
        ).order_by(Lancamento.data.asc()).all()
        
        # Calcular totais gerais
        totais_geral = {
            'entradas': sum(p['totais']['entradas'] for p in projetos_com_totais),
            'saidas': sum(p['totais']['saidas'] for p in projetos_com_totais),
            'saldo': sum(p['totais']['saldo'] for p in projetos_com_totais)
        }
        
        # Adicionar lançamentos sem projeto aos totais
        if lancamentos_sem_projeto:
            totais_sem_projeto = {
                'entradas': sum(l.valor for l in lancamentos_sem_projeto if l.tipo == 'Entrada'),
                'saidas': sum(l.valor for l in lancamentos_sem_projeto if l.tipo == 'Saída')
            }
            totais_sem_projeto['saldo'] = totais_sem_projeto['entradas'] - totais_sem_projeto['saidas']
            
            totais_geral['entradas'] += totais_sem_projeto['entradas']
            totais_geral['saidas'] += totais_sem_projeto['saidas']
            totais_geral['saldo'] += totais_sem_projeto['saldo']
        
        return render_template('financeiro/caixa_destinacoes.html',
                             projetos=projetos_com_totais,
                             lancamentos_sem_projeto=lancamentos_sem_projeto,
                             totais=totais_geral,
                             mes=mes,
                             ano=ano,
                             projeto_id=projeto_id,
                             todos_projetos=projetos)
    
    except Exception as e:
        import traceback
        print(f">>> ERRO em caixa_destinacoes: {str(e)}")
        print(traceback.format_exc())
        flash(f'Erro ao carregar caixa de destinações: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

# ========== ROTAS DE CRUD DE PROJETOS ==========

@financeiro_bp.route('/financeiro/projetos', endpoint='lista_projetos')
@login_required
def lista_projetos():
    """Lista todos os projetos cadastrados"""
    print(">>> ROTA LISTA_PROJETOS CHAMADA!")
    try:
        projetos = Projeto.query.order_by(Projeto.status.desc(), Projeto.nome).all()
        
        # Calcular totais para cada projeto
        projetos_com_totais = []
        for projeto in projetos:
            totais = projeto.calcular_totais()
            projetos_com_totais.append({
                'projeto': projeto,
                'totais': totais
            })
        
        return render_template('financeiro/lista_projetos.html', 
                             projetos=projetos_com_totais)
    except Exception as e:
        import traceback
        print(f">>> ERRO em lista_projetos: {str(e)}")
        print(traceback.format_exc())
        flash(f'Erro ao listar projetos: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/projetos/novo', methods=['GET', 'POST'])
@login_required
def novo_projeto():
    """Cadastra novo projeto"""
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            tipo = request.form.get('tipo', '').strip()
            status = request.form.get('status', 'Ativo')
            meta_valor_str = request.form.get('meta_valor', '').strip()
            
            # Validações
            if not nome:
                flash('Nome do projeto é obrigatório!', 'danger')
                return redirect(url_for('financeiro.novo_projeto'))
            
            # Verifica duplicidade
            existe = Projeto.query.filter_by(nome=nome).first()
            if existe:
                flash(f'Já existe um projeto com o nome "{nome}"!', 'danger')
                return redirect(url_for('financeiro.novo_projeto'))
            
            # Converter meta_valor
            meta_valor = None
            if meta_valor_str:
                try:
                    meta_valor = float(meta_valor_str.replace('.', '').replace(',', '.'))
                except:
                    pass
            
            # Criar projeto
            projeto = Projeto(
                nome=nome,
                descricao=descricao if descricao else None,
                tipo=tipo if tipo else None,
                status=status,
                meta_valor=meta_valor
            )
            
            db.session.add(projeto)
            db.session.commit()
            
            flash(f'Projeto "{nome}" cadastrado com sucesso!', 'success')
            return redirect(url_for('financeiro.lista_projetos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar projeto: {str(e)}', 'danger')
            return redirect(url_for('financeiro.novo_projeto'))
    
    return render_template('financeiro/cadastro_projeto.html')

@financeiro_bp.route('/financeiro/projetos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_projeto(id):
    """Edita projeto existente"""
    projeto = Projeto.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            tipo = request.form.get('tipo', '').strip()
            status = request.form.get('status', 'Ativo')
            meta_valor_str = request.form.get('meta_valor', '').strip()
            
            if not nome:
                flash('Nome do projeto é obrigatório!', 'danger')
                return redirect(url_for('financeiro.editar_projeto', id=id))
            
            # Verifica duplicidade (exceto o próprio)
            existe = Projeto.query.filter(Projeto.nome == nome, Projeto.id != id).first()
            if existe:
                flash(f'Já existe outro projeto com o nome "{nome}"!', 'danger')
                return redirect(url_for('financeiro.editar_projeto', id=id))
            
            # Converter meta_valor
            meta_valor = None
            if meta_valor_str:
                try:
                    meta_valor = float(meta_valor_str.replace('.', '').replace(',', '.'))
                except:
                    pass
            
            # Atualizar
            projeto.nome = nome
            projeto.descricao = descricao if descricao else None
            projeto.tipo = tipo if tipo else None
            projeto.status = status
            projeto.meta_valor = meta_valor
            projeto.updated_at = datetime.now()
            
            db.session.commit()
            flash(f'Projeto "{nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('financeiro.lista_projetos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar projeto: {str(e)}', 'danger')
            return redirect(url_for('financeiro.editar_projeto', id=id))
    
    return render_template('financeiro/cadastro_projeto.html', projeto=projeto)

@financeiro_bp.route('/financeiro/projetos/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_projeto(id):
    """Exclui projeto (apenas se não tiver lançamentos)"""
    try:
        projeto = Projeto.query.get_or_404(id)
        
        # Verifica se tem lançamentos
        if projeto.lancamentos.count() > 0:
            flash(f'Não é possível excluir o projeto "{projeto.nome}" pois existem lançamentos vinculados!', 'danger')
            return redirect(url_for('financeiro.lista_projetos'))
        
        nome = projeto.nome
        db.session.delete(projeto)
        db.session.commit()
        
        flash(f'Projeto "{nome}" excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir projeto: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.lista_projetos'))

# ========== FIM ROTAS DE PROJETOS ==========

# ========== ROTA GENÉRICA (deve vir DEPOIS das específicas) ==========

@financeiro_bp.route('/financeiro/lancamentos')
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
        importacao_recente = request.args.get('importacao_recente', '').strip()
        
        # Query base
        query = Lancamento.query
        
        # Se veio de uma importação recente, mostrar primeiro os importados
        mostrar_importados_primeiro = importacao_recente == 'true'
        
        # Aplicar filtro por categoria (com lógica especial para ofertas)
        if categoria_filtro:
            if categoria_filtro == 'Ofertas Alçadas':
                # Ofertas Alçadas = Ofertas normais do ofertório (30% para conselho)
                # Exclui: OMN, Outras Ofertas, Especiais, Voluntárias
                query = query.filter(
                    Lancamento.categoria.ilike('%oferta%')
                ).filter(
                    ~Lancamento.categoria.ilike('%omn%')
                ).filter(
                    ~Lancamento.categoria.ilike('%missionaria%')
                ).filter(
                    ~Lancamento.categoria.ilike('%outras%')
                ).filter(
                    ~Lancamento.categoria.ilike('%especial%')
                ).filter(
                    ~Lancamento.categoria.ilike('%voluntaria%')
                )
            elif categoria_filtro == 'Oferta OMN':
                # Buscar ofertas OMN
                query = query.filter(
                    or_(
                        Lancamento.categoria.ilike('%omn%'),
                        Lancamento.categoria.ilike('%missionaria%')
                    )
                )
            elif categoria_filtro == 'Outras Ofertas':
                # Buscar outras ofertas
                query = query.filter(
                    Lancamento.categoria.ilike('%oferta%')
                ).filter(
                    or_(
                        Lancamento.categoria.ilike('%outras%'),
                        Lancamento.categoria.ilike('%especial%'),
                        Lancamento.categoria.ilike('%voluntaria%')
                    )
                )
            else:
                # Filtro padrão para outras categorias
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
        
        # Buscar lançamentos filtrados com ordenação especial
        if mostrar_importados_primeiro:
            # Priorizar lançamentos importados no topo da lista
            from sqlalchemy import case
            order_by_clause = [
                case((Lancamento.origem == 'importado', 0), else_=1),
                Lancamento.data.desc(), 
                Lancamento.criado_em.desc()
            ]
            lancamentos_filtrados = query.order_by(*order_by_clause).all()
        else:
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
        
        # Obter todas as categorias únicas para o filtro (organizadas)
        categorias_todas = db.session.query(Lancamento.categoria).distinct().filter(
            Lancamento.categoria.is_not(None), 
            Lancamento.categoria != ''
        ).order_by(Lancamento.categoria).all()
        
        # Organizar categorias de forma estruturada
        categorias_organizadas = []
        categorias_brutas = [cat[0] for cat in categorias_todas]
        
        # Separar e organizar por tipo
        # CATEGORIAS DE OFERTAS:
        # 1. Ofertas Alçadas = Ofertas do ofertório (30% para conselho)
        # 2. Oferta OMN = Ofertas missionárias (NÃO computa conselho)
        # 3. Outras Ofertas = Especiais, Voluntárias (NÃO computa conselho)
        for categoria in sorted(categorias_brutas):
            cat_lower = categoria.lower()
            
            # Verificar se é oferta e especificar o tipo
            if 'oferta' in cat_lower:
                if 'omn' in cat_lower or 'missionaria' in cat_lower:
                    # Oferta OMN - não computa para conselho
                    categorias_organizadas.append('Oferta OMN')
                elif any(x in cat_lower for x in ['outras', 'especial', 'voluntaria']):
                    # Outras Ofertas - não computa para conselho
                    categorias_organizadas.append('Outras Ofertas')
                else:
                    # Ofertas Alçadas (unifica "Oferta" e "Oferta Alçada")
                    # Computa 30% para conselho administrativo
                    categorias_organizadas.append('Ofertas Alçadas')
            else:
                # Não é oferta, manter como está
                categorias_organizadas.append(categoria)
        
        # Remover duplicatas e manter ordem
        categorias_unicas = list(dict.fromkeys(categorias_organizadas))
        
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
            # Função auxiliar para verificar se um lançamento pertence à categoria
            def pertence_categoria(lanc, cat):
                cat_lower = cat.lower()
                lanc_cat_lower = lanc.categoria.lower() if lanc.categoria else ''
                
                if cat == 'Ofertas Alçadas':
                    # Ofertas Alçadas = Ofertas do ofertório (30% para conselho)
                    # Exclui: OMN, Outras Ofertas, Especiais, Voluntárias
                    return ('oferta' in lanc_cat_lower and 
                            'omn' not in lanc_cat_lower and 
                            'missionaria' not in lanc_cat_lower and
                            'outras' not in lanc_cat_lower and
                            'especial' not in lanc_cat_lower and
                            'voluntaria' not in lanc_cat_lower)
                elif cat == 'Oferta OMN':
                    # Ofertas OMN
                    return 'omn' in lanc_cat_lower or 'missionaria' in lanc_cat_lower
                elif cat == 'Outras Ofertas':
                    # Outras ofertas especiais
                    return ('oferta' in lanc_cat_lower and 
                            ('outras' in lanc_cat_lower or 'especial' in lanc_cat_lower or 'voluntaria' in lanc_cat_lower))
                else:
                    # Comparação direta
                    return lanc.categoria == cat
            
            lancamentos_cat = [l for l in lancamentos_filtrados if pertence_categoria(l, categoria)]
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
                             conciliacao_info=conciliacao_info,
                             importacao_recente=mostrar_importados_primeiro)
                             
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
                             },
                             conciliacao_info={'total_conciliados': 0, 'total_pendentes': 0, 'ultima_data': None},
                             importacao_recente=False)

@financeiro_bp.route('/financeiro/novo')
@login_required
def novo_lancamento():
    """Exibe formulário para cadastro de novo lançamento"""
    # Buscar projetos ativos para o dropdown
    projetos = Projeto.query.filter_by(status='Ativo').order_by(Projeto.nome).all()
    return render_template('financeiro/cadastro_lancamento.html', 
                         today=date.today(), 
                         projetos=projetos)


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


@financeiro_bp.route('/financeiro/importar/confirmar-old', methods=['POST'])
@login_required
def confirmar_importacao_DEPRECATED():
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
    print("DEBUG: Função importar_extrato_confirmar iniciada")
    
    dados = request.form.get('registros')
    print(f"DEBUG: Dados recebidos: {bool(dados)}")
    
    if not dados:
        flash('Nenhum registro para importar.', 'warning')
        return redirect(url_for('financeiro.importar_extrato'))

    try:
        import json
        registros = json.loads(dados)
        print(f"DEBUG: {len(registros)} registros para processar")
        
        criados = 0
        conciliados = 0
        
        # Processar cada registro
        for i, r in enumerate(registros):
            try:
                print(f"DEBUG: Processando registro {i+1}")
                print(f"DEBUG: Registro completo: {r}")
                
                if r.get('match_id'):
                    print(f"DEBUG: Registro {i+1} tem match_id, pulando para conciliação")
                    conciliados += 1
                    continue
                    
                # Processar data
                data_obj = date.today()
                if r.get('data'):
                    try:
                        data_obj = datetime.strptime(r.get('data'), '%Y-%m-%d').date()
                    except:
                        pass  # Usa data atual se houver erro
                
                # Processar valor e tipo
                valor_raw = r.get('valor', '0')
                valor_float = float(str(valor_raw).replace(',', '.'))
                valor_abs = abs(valor_float)
                
                # USAR O TIPO QUE VEM DO PREVIEW, NÃO RECALCULAR!
                tipo = r.get('tipo', 'Entrada')  # Usar tipo do preview
                
                print(f"DEBUG: Registro {i+1} - Valor raw: {valor_raw}, Float: {valor_float}, Abs: {valor_abs}, Tipo do preview: {tipo}")
                
                if tipo == 'Saída':
                    print(f"DEBUG: *** SAÍDA DETECTADA *** - Registro {i+1}: {r.get('descricao', 'Sem descrição')}")
                
                # Criar lançamento
                novo = Lancamento(
                    data=data_obj,
                    tipo=tipo,
                    categoria='Importação',
                    descricao=str(r.get('descricao', '')[:190]),  # Limitar tamanho
                    valor=valor_abs,
                    conta='Extrato',
                    observacoes='Importado via extrato',
                    origem='importado',
                    conciliado=False
                )
                
                print(f"DEBUG: Objeto criado - Tipo: {novo.tipo}, Valor: {novo.valor}, Desc: {novo.descricao[:30]}...")
                
                if novo.tipo == 'Saída':
                    print(f"DEBUG: *** SALVANDO SAÍDA *** - {novo.descricao[:50]}")
                
                db.session.add(novo)
                criados += 1
                print(f"DEBUG: Lançamento {i+1} adicionado à sessão - TIPO: {tipo}")
                
            except Exception as e:
                print(f"DEBUG: Erro no registro {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue  # Pula este registro e continua
        
        print(f"DEBUG: Fazendo commit de {criados} registros...")
        db.session.commit()
        print(f"DEBUG: Commit realizado")
        
        # Verificar resultado imediatamente após commit
        total_importados = Lancamento.query.filter_by(origem='importado').count()
        entradas_importadas = Lancamento.query.filter_by(origem='importado', tipo='Entrada').count()  
        saidas_importadas = Lancamento.query.filter_by(origem='importado', tipo='Saída').count()
        
        print(f"DEBUG: Total importados no banco: {total_importados}")
        print(f"DEBUG: Entradas importadas: {entradas_importadas}")
        print(f"DEBUG: Saídas importadas: {saidas_importadas}")
        
        # Verificar últimos registros salvos
        ultimos_salvos = Lancamento.query.filter_by(origem='importado').order_by(Lancamento.id.desc()).limit(5).all()
        print(f"DEBUG: Últimos 5 salvos:")
        for lanc in ultimos_salvos:
            print(f"   ID {lanc.id}: {lanc.tipo} - {lanc.descricao[:30]}... - R$ {lanc.valor}")
        
        # Mensagem de sucesso
        mensagem = f'Importação concluída: {criados} lançamentos criados'
        if conciliados > 0:
            mensagem += f', {conciliados} conciliados'
        
        flash(mensagem, 'success')
        print(f"DEBUG: Redirecionando para lista de lançamentos")
        return redirect(url_for('financeiro.lista_lancamentos'))

    except Exception as e:
        print(f"DEBUG: Erro na função: {e}")
        try:
            db.session.rollback()
        except:
            pass
        flash(f'Erro ao processar importação: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))


@financeiro_bp.route('/debug/importacao')
@login_required 
def debug_importacao():
    """Função temporária para debug da importação"""
    from flask import jsonify
    
    # Verificar quantos lançamentos importados existem
    total_importados = Lancamento.query.filter_by(origem='importado').count()
    entradas_importadas = Lancamento.query.filter_by(origem='importado', tipo='Entrada').count()
    saidas_importadas = Lancamento.query.filter_by(origem='importado', tipo='Saída').count()
    
    # Pegar últimos 10 lançamentos importados
    ultimos = Lancamento.query.filter_by(origem='importado').order_by(Lancamento.id.desc()).limit(10).all()
    
    dados_ultimos = []
    for lanc in ultimos:
        dados_ultimos.append({
            'id': lanc.id,
            'data': lanc.data.strftime('%Y-%m-%d') if lanc.data else None,
            'tipo': lanc.tipo,
            'descricao': lanc.descricao,
            'valor': float(lanc.valor),
            'origem': lanc.origem
        })
    
    resultado = {
        'total_importados': total_importados,
        'entradas': entradas_importadas, 
        'saidas': saidas_importadas,
        'ultimos_registros': dados_ultimos
    }
    
    return jsonify(resultado)


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
        projeto_id_str = request.form.get('projeto_id', '').strip()
        
        # Processar projeto_id
        projeto_id = None
        if projeto_id_str and projeto_id_str.isdigit():
            projeto_id = int(projeto_id_str)
            # Validar se o projeto existe e está ativo
            projeto = Projeto.query.filter_by(id=projeto_id, status='Ativo').first()
            if not projeto:
                flash('Projeto selecionado inválido ou inativo!', 'danger')
                return redirect(url_for('financeiro.novo_lancamento'))
        
        # Validar se projeto é obrigatório para DESTINAÇÃO e GASTO PROJETO
        if categoria in ['DESTINAÇÃO', 'GASTO PROJETO'] and not projeto_id:
            flash('Projeto é obrigatório para lançamentos de DESTINAÇÃO e GASTO PROJETO!', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
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
            lancamento.projeto_id = projeto_id  # Atualizar projeto
            # Atualizar comprovante apenas se um novo foi enviado
            if caminho_comprovante:
                lancamento.comprovante = caminho_comprovante
            flash('Lançamento atualizado com sucesso!', 'success')
            
            # Após editar, salvar e redirecionar para a lista de lançamentos
            db.session.commit()
            return redirect(url_for('financeiro.lista_lancamentos'))
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
                comprovante=caminho_comprovante,
                projeto_id=projeto_id  # Vincular ao projeto
            )
            novo_lancamento.origem = 'manual'
            db.session.add(novo_lancamento)
            flash('Lançamento cadastrado com sucesso! Você pode continuar lançando ou clicar em "Voltar" para ver a lista.', 'success')
            
            # Para novos lançamentos, salvar e continuar no formulário
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
        # Buscar projetos ativos para o dropdown
        projetos = Projeto.query.filter_by(status='Ativo').order_by(Projeto.nome).all()
        return render_template('financeiro/cadastro_lancamento.html', 
                             lancamento=lancamento, 
                             projetos=projetos)
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
        # Pegar mês e ano da query string com validação
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        # Se não foram fornecidos na URL, usar o mês/ano padrão
        if mes is None:
            mes = 12
        if ano is None:
            ano = 2025
        
        # Validar valores
        if mes < 1 or mes > 12:
            mes = 12
        if ano < 2020 or ano > 2030:
            ano = 2025
        
        # Filtrar lançamentos do mês
        lancamentos = Lancamento.query.filter(
            extract('month', Lancamento.data) == mes,
            extract('year', Lancamento.data) == ano
        ).all()
        
        # Inicializar totais (PIX agrupado com BANCO)
        totais = {
            'entradas_banco': 0,
            'entradas_dinheiro': 0,
            'dizimos_banco': 0,
            'dizimos_dinheiro': 0,
            'ofertas_banco': 0,
            'ofertas_dinheiro': 0,
            'outras_ofertas_banco': 0,
            'outras_ofertas_dinheiro': 0,
            'oferta_omn_banco': 0,
            'oferta_omn_dinheiro': 0,
            'saidas_banco': 0,
            'saidas_dinheiro': 0,
            'descontos': 0,
            'total_entradas': 0,
            'total_saidas': 0,
            'total_dizimos': 0,
            'total_ofertas': 0,
            'total_outras_ofertas': 0,
            'total_oferta_omn': 0,
            'total_dizimos_ofertas': 0,
            'percentual_30': 0,
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
                # Entradas por conta (PIX agrupado com BANCO)
                if 'banco' in conta or 'pix' in conta:
                    totais['entradas_banco'] += valor
                else:
                    totais['entradas_dinheiro'] += valor
                
                # Dízimos por conta (PIX agrupado com BANCO)
                if 'dízimo' in categoria or 'dizimo' in categoria:
                    if 'banco' in conta or 'pix' in conta:
                        totais['dizimos_banco'] += valor
                    else:
                        totais['dizimos_dinheiro'] += valor
                
                # Verificar primeiro as categorias específicas (mais restritivas)
                # Oferta OMN (verificar primeiro para evitar confusão)
                elif 'omn' in categoria or 'missionaria' in categoria or 'missionária' in categoria:
                    if 'banco' in conta or 'pix' in conta:
                        totais['oferta_omn_banco'] += valor
                    else:
                        totais['oferta_omn_dinheiro'] += valor
                
                # Outras ofertas (verificar antes das ofertas normais)
                elif 'oferta' in categoria and any(x in categoria for x in ['outras', 'especial', 'voluntaria', 'voluntária']):
                    if 'banco' in conta or 'pix' in conta:
                        totais['outras_ofertas_banco'] += valor
                    else:
                        totais['outras_ofertas_dinheiro'] += valor
                
                # Ofertas Alçadas (ofertas normais do ofertório - só o que sobrou)
                elif 'oferta' in categoria:
                    if 'banco' in conta or 'pix' in conta:
                        totais['ofertas_banco'] += valor
                    else:
                        totais['ofertas_dinheiro'] += valor
                
                totais['total_entradas'] += valor
            
            elif lancamento.tipo == 'Saída':
                # Verificar se é uma "Destinação" (não afeta saldo do caixa)
                # Destinações são registros de onde o dinheiro foi destinado,
                # mas já entrou no caixa como entrada, então não deve sair novamente
                eh_destinacao = any(x in categoria for x in [
                    'destinação', 'destinacao', 
                    'transferência interna', 'transferencia interna'
                ])
                
                # Apenas contabilizar como saída se NÃO for destinação
                if not eh_destinacao:
                    # Saídas por conta (PIX agrupado com BANCO)
                    if 'banco' in conta or 'pix' in conta:
                        totais['saidas_banco'] += valor
                    else:
                        totais['saidas_dinheiro'] += valor
                    
                    totais['total_saidas'] += valor
                    
                    # Descontos (categorias específicas)
                    if 'desconto' in categoria or 'taxa' in categoria:
                        totais['descontos'] += valor
        
        # Calcular totais consolidados
        totais['total_dizimos'] = totais['dizimos_banco'] + totais['dizimos_dinheiro']
        totais['total_ofertas'] = totais['ofertas_banco'] + totais['ofertas_dinheiro']
        totais['total_outras_ofertas'] = totais['outras_ofertas_banco'] + totais['outras_ofertas_dinheiro']
        totais['total_oferta_omn'] = totais['oferta_omn_banco'] + totais['oferta_omn_dinheiro']
        
        # Total para cálculo dos 30% (apenas dízimos + ofertas normais)
        totais['total_dizimos_ofertas'] = totais['total_dizimos'] + totais['total_ofertas']
        
        # Calcular 30% sobre dízimos e ofertas (excluindo outras ofertas e OMN)
        totais['percentual_30'] = totais['total_dizimos_ofertas'] * 0.30
        
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
        print("DEBUG: Inicio relatorio_sede")
        
        # Obter parâmetros da URL ou valores padrão
        mes = int(request.args.get('mes', 12))
        ano = int(request.args.get('ano', 2025))
        
        print(f"DEBUG: Processando mês {mes}, ano {ano}")
        print(f"DEBUG: Parâmetros da URL: {dict(request.args)}")
        
        print(f"DEBUG: Mês: {mes}, Ano: {ano}")
        print(f"DEBUG: Mês: {mes}, Ano: {ano}")
        
        print("DEBUG: Criando dados básicos")
        
        # Buscar dados da configuração
        try:
            from app.configuracoes.configuracoes_model import Configuracao
            config = Configuracao.obter_configuracao_atual()
            if config:
                dados_igreja = {
                    'cidade': config.cidade or 'Tietê',
                    'bairro': config.bairro or 'Centro', 
                    'dirigente': config.pastor or 'Pastor Responsável',
                    'tesoureiro': config.tesoureiro or 'Tesoureiro(a)',
                    'saldo_anterior': 0.0
                }
            else:
                dados_igreja = {
                    'cidade': 'Tietê',
                    'bairro': 'Centro', 
                    'dirigente': 'Pastor Responsável',
                    'tesoureiro': 'Tesoureiro(a)',
                    'saldo_anterior': 0.0
                }
        except Exception as e:
            print(f"DEBUG: Erro ao buscar configuração: {e}")
            dados_igreja = {
                'cidade': 'Tietê',
                'bairro': 'Centro', 
                'dirigente': 'Pastor Responsável',
                'tesoureiro': 'Tesoureiro(a)',
                'saldo_anterior': 0.0
            }
        
        # Buscar lançamentos do mês/ano
        try:
            from app.financeiro.financeiro_model import Lancamento
            from sqlalchemy import and_, extract
            
            lancamentos = Lancamento.query.filter(
                and_(
                    extract('month', Lancamento.data) == mes,
                    extract('year', Lancamento.data) == ano
                )
            ).all()
            
            print(f"DEBUG: Encontrados {len(lancamentos)} lançamentos")
            
            # Calcular totais com lógica corrigida
            total_dizimos = sum(l.valor for l in lancamentos if l.tipo == 'Entrada' and l.categoria and 'dízimo' in l.categoria.lower())
            
            # Ofertas Alçadas: Primeiro verificar se NÃO é OMN ou Outras Ofertas
            total_ofertas_alcadas = sum(
                l.valor for l in lancamentos 
                if l.tipo == 'Entrada' and l.categoria and 'oferta' in l.categoria.lower()
                and not ('omn' in l.categoria.lower() or 'missionaria' in l.categoria.lower())
                and not any(x in l.categoria.lower() for x in ['outras', 'especial', 'voluntaria', 'voluntária'])
            )
            
            # Outras Ofertas: Apenas ofertas com palavras-chave específicas
            total_outras_ofertas = sum(
                l.valor for l in lancamentos 
                if l.tipo == 'Entrada' and l.categoria and 'oferta' in l.categoria.lower() 
                and any(x in l.categoria.lower() for x in ['outras', 'especial', 'voluntaria', 'voluntária'])
            )
            
            # Oferta OMN: Apenas com OMN ou missionária
            total_ofertas_omn = sum(
                l.valor for l in lancamentos 
                if l.tipo == 'Entrada' and l.categoria 
                and ('omn' in l.categoria.lower() or 'missionaria' in l.categoria.lower() or 'missionária' in l.categoria.lower())
            )
            total_despesas = sum(l.valor for l in lancamentos if l.tipo == 'Saída')
            
            # Total para cálculo dos 30% do Conselho Administrativo
            # IMPORTANTE: Apenas Dízimos + Ofertas Alçadas computam para o conselho
            # Outras Ofertas e Oferta OMN NÃO computam
            total_dizimos_ofertas = total_dizimos + total_ofertas_alcadas
            
            # Calcular 30% sobre dízimos e ofertas alçadas (base do conselho)
            valor_conselho_30 = total_dizimos_ofertas * 0.30
            
        except Exception as e:
            print(f"DEBUG: Erro ao buscar lançamentos: {e}")
            lancamentos = []
            total_dizimos = 0
            total_ofertas_alcadas = 0
            total_outras_ofertas = 0
            total_ofertas_omn = 0
            total_despesas = 0
            total_dizimos_ofertas = 0
            valor_conselho_30 = 0
        
        # Total geral de entradas
        total_entradas = total_dizimos + total_ofertas_alcadas + total_outras_ofertas + total_ofertas_omn
        saldo_mes = total_entradas - total_despesas
        
        # Totais básicos
        totais = {
            'dizimos': total_dizimos,
            'ofertas_alcadas': total_ofertas_alcadas,
            'outras_ofertas': total_outras_ofertas,
            'oferta_omn': total_ofertas_omn,
            'total_geral': total_entradas,
            'despesas_financeiras': total_despesas,
            'saldo_mes': saldo_mes,
            'valor_conselho': valor_conselho_30,
            'total_dizimos_ofertas': total_dizimos_ofertas,
            'percentual_30': valor_conselho_30
        }
        
        # Buscar envios para sede baseados nas saídas
        try:
            # Buscar lançamentos de saída que correspondem aos envios
            lancamentos_saida = [l for l in lancamentos if l.tipo == 'Saída']
            
            envios = {
                'oferta_voluntaria_conchas': 0.0,
                'site': 0.0,
                'projeto_filipe': 0.0,
                'forca_para_viver': 0.0,
                'contador_sede': 0.0
            }
            
            # Lista detalhada para o PDF
            envios_detalhados = {
                'oferta_voluntaria_conchas': [],
                'site': [],
                'projeto_filipe': [],
                'forca_para_viver': [],
                'contador_sede': [],
                'omn': []
            }
            
            # Mapear descrições para chaves
            mapeamento_envios = {
                'oferta_voluntaria_conchas': ['conchas', 'voluntaria conchas', 'oferta voluntaria conchas'],
                'site': ['site'],
                'projeto_filipe': ['projeto filipe', 'filipe'],
                'forca_para_viver': ['força para viver', 'forca para viver'],
                'contador_sede': ['contador sede', 'contador']
            }
            
            # Buscar valores nos lançamentos de saída
            for lancamento in lancamentos_saida:
                if lancamento.descricao:
                    descricao_lower = lancamento.descricao.lower()
                    
                    # Verificar cada tipo de envio
                    for chave, termos_busca in mapeamento_envios.items():
                        for termo in termos_busca:
                            if termo in descricao_lower:
                                envios[chave] += lancamento.valor
                                # Adicionar detalhes para o PDF
                                envios_detalhados[chave].append({
                                    'data': lancamento.data,
                                    'descricao': lancamento.descricao,
                                    'valor': lancamento.valor,
                                    'conta': lancamento.conta
                                })
                                break  # Para evitar dupla contagem
            
            total_envio_sede = sum(envios.values())
            
            # Adicionar ofertas OMN automaticamente aos envios detalhados
            for lancamento in lancamentos:
                if lancamento.tipo == 'Entrada' and lancamento.categoria:
                    categoria_lower = lancamento.categoria.lower()
                    if 'omn' in categoria_lower or 'missionaria' in categoria_lower:
                        envios_detalhados['omn'].append({
                            'data': lancamento.data,
                            'descricao': lancamento.categoria,
                            'conta': getattr(lancamento, 'conta', None),
                            'valor': float(lancamento.valor) if lancamento.valor else 0
                        })
            
            print(f"DEBUG: Envios encontrados: {envios}")
            print(f"DEBUG: Total envio sede: {total_envio_sede}")
            
        except Exception as e:
            print(f"DEBUG: Erro ao buscar envios: {e}")
            envios = {
                'oferta_voluntaria_conchas': 0.0,
                'site': 0.0,
                'projeto_filipe': 0.0,
                'forca_para_viver': 0.0,
                'contador_sede': 0.0
            }
            envios_detalhados = {
                'oferta_voluntaria_conchas': [],
                'site': [],
                'projeto_filipe': [],
                'forca_para_viver': [],
                'contador_sede': [],
                'omn': []
            }
            total_envio_sede = 0
        
        print("DEBUG: Tentando renderizar template")
        
        from datetime import date
        
        return render_template('financeiro/relatorio_sede.html',
                             dados_igreja=dados_igreja,
                             totais=totais,
                             envios=envios,
                             envios_detalhados=envios_detalhados,
                             total_envio_sede=total_envio_sede,
                             mes=mes,
                             ano=ano,
                             data_geracao=date.today())
        
    except Exception as e:
        print(f"DEBUG: ERRO: {e}")
        import traceback
        print(f"DEBUG: TRACEBACK: {traceback.format_exc()}")
        flash(f'Erro ao gerar relatório da sede: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

@financeiro_bp.route('/financeiro/despesas-fixas', methods=['GET', 'POST'])
@login_required
def gerenciar_despesas_fixas():
    """Interface para gerenciar despesas fixas do conselho"""
    try:
        # Processar ações de POST
        if request.method == 'POST':
            acao = request.form.get('acao')
            
            if acao == 'criar':
                nova_despesa = DespesaFixaConselho(
                    nome=request.form.get('nome', '').strip(),
                    descricao=request.form.get('descricao', '').strip(),
                    categoria=request.form.get('categoria', '').strip(),
                    valor_padrao=float(request.form.get('valor_padrao', 0)),
                    ativo=True
                )
                
                # Validar antes de salvar
                erros = nova_despesa.validar()
                if erros:
                    for erro in erros:
                        flash(erro, 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
                
                db.session.add(nova_despesa)
                db.session.commit()
                flash(f'Despesa fixa "{nova_despesa.nome}" criada com sucesso!', 'success')
                
            elif acao == 'editar':
                despesa_id = request.form.get('id')
                despesa = DespesaFixaConselho.query.get_or_404(despesa_id)
                
                despesa.nome = request.form.get('nome', '').strip()
                despesa.descricao = request.form.get('descricao', '').strip()
                despesa.categoria = request.form.get('categoria', '').strip()
                despesa.valor_padrao = float(request.form.get('valor_padrao', 0))
                despesa.ativo = bool(request.form.get('ativo'))
                
                # Validar antes de salvar
                erros = despesa.validar()
                if erros:
                    for erro in erros:
                        flash(erro, 'danger')
                    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
                
                db.session.commit()
                flash(f'Despesa fixa "{despesa.nome}" atualizada com sucesso!', 'success')
            
            return redirect(url_for('financeiro.gerenciar_despesas_fixas'))
        
        # Buscar todas as despesas para exibição
        despesas_todas = DespesaFixaConselho.query.order_by(DespesaFixaConselho.nome).all()
        despesas_ativas = DespesaFixaConselho.obter_despesas_ativas()
        total_despesas = DespesaFixaConselho.obter_total_despesas_fixas()
        
        return render_template('financeiro/gerenciar_despesas_fixas.html',
                             despesas_todas=despesas_todas,
                             despesas_ativas=despesas_ativas,
                             total_despesas=total_despesas)
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao gerenciar despesas fixas: {str(e)}', 'danger')
        return redirect(url_for('financeiro.lista_lancamentos'))

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

@financeiro_bp.route('/financeiro/despesas-fixas/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_despesa_fixa(id):
    """Exclui permanentemente uma despesa fixa do banco de dados"""
    try:
        despesa = DespesaFixaConselho.query.get_or_404(id)
        nome_despesa = despesa.nome
        
        # Remover a despesa do banco de dados
        db.session.delete(despesa)
        db.session.commit()
        
        flash(f'Despesa fixa "{nome_despesa}" excluída com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir despesa fixa: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.gerenciar_despesas_fixas'))

@financeiro_bp.route('/financeiro/relatorio-caixa/preview')
@login_required
def relatorio_caixa_preview():
    """Preview HTML do relatório de caixa antes de gerar PDF"""
    try:
        # Pegar mês e ano da query string com validação
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        # Se não foram fornecidos na URL, usar o mês/ano atual
        if mes is None:
            mes = datetime.now().month
        if ano is None:
            ano = datetime.now().year
        
        # Validar valores
        if mes < 1 or mes > 12:
            mes = datetime.now().month
        if ano < 2020 or ano > 2030:
            ano = datetime.now().year
        
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
                # Verificar se é uma "Destinação" (não afeta saldo do caixa)
                eh_destinacao = any(x in categoria for x in [
                    'destinação', 'destinacao', 
                    'transferência interna', 'transferencia interna'
                ])
                
                # Apenas contabilizar como saída se NÃO for destinação
                if not eh_destinacao:
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
        # Pegar mês e ano da query string com validação
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        # Se não foram fornecidos na URL, usar o mês/ano atual
        if mes is None:
            mes = datetime.now().month
        if ano is None:
            ano = datetime.now().year
        
        # Validar valores
        if mes < 1 or mes > 12:
            mes = datetime.now().month
        if ano < 2020 or ano > 2030:
            ano = datetime.now().year
        
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
                    # Lógica corrigida e padronizada das ofertas:
                    # 1º: Verificar se é OMN (não computa no conselho, mas registrado)
                    if 'omn' in categoria or 'missionaria' in categoria or 'missionária' in categoria:
                        totais['ofertas_alcadas'] += valor  # Mantido por compatibilidade do preview
                    # 2º: Verificar se é "Outras Ofertas" (não computa no conselho)
                    elif any(x in categoria for x in ['outras', 'especial', 'voluntaria', 'voluntária']):
                        totais['outras_ofertas'] += valor
                    # 3º: O resto são Ofertas Alçadas (computa 30% conselho)
                    else:
                        # Ofertas Alçadas = ofertas normais do ofertório
                        totais['ofertas_alcadas'] += valor
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
        # Calcular 30% excluindo "OUTRAS OFERTAS"
        valor_para_conselho = totais['total_entradas'] - totais.get('outras_ofertas', 0)
        totais['trinta_porcento_conselho'] = valor_para_conselho * percentual
        
        # Buscar despesas fixas do conselho
        despesas_fixas = DespesaFixaConselho.query.filter_by(ativo=True).all()
        totais['despesas_fixas_conselho'] = sum(d.valor for d in despesas_fixas)
        
        # Calcular total de envio para sede
        totais['total_envio_sede'] = totais['trinta_porcento_conselho'] + totais['despesas_fixas_conselho']
        
        # Buscar envios para sede baseados nas saídas
        try:
            # Buscar lançamentos de saída que correspondem aos envios
            lancamentos_saida = [l for l in lancamentos if l.tipo == 'Saída']
            
            envios = {
                'oferta_voluntaria_conchas': 0.0,
                'site': 0.0,
                'projeto_filipe': 0.0,
                'forca_para_viver': 0.0,
                'contador_sede': 0.0
            }
            
            # Lista detalhada para o PDF
            envios_detalhados = {
                'oferta_voluntaria_conchas': [],
                'site': [],
                'projeto_filipe': [],
                'forca_para_viver': [],
                'contador_sede': [],
                'omn': []
            }
            
            # Mapear descrições para chaves
            mapeamento_envios = {
                'oferta_voluntaria_conchas': ['conchas', 'voluntaria conchas', 'oferta voluntaria conchas'],
                'site': ['site'],
                'projeto_filipe': ['projeto filipe', 'filipe'],
                'forca_para_viver': ['força para viver', 'forca para viver'],
                'contador_sede': ['contador sede', 'contador']
            }
            
            # Buscar valores nos lançamentos de saída
            for lancamento in lancamentos_saida:
                if lancamento.descricao:
                    descricao_lower = lancamento.descricao.lower()
                    
                    # Verificar cada tipo de envio
                    for chave, termos_busca in mapeamento_envios.items():
                        for termo in termos_busca:
                            if termo in descricao_lower:
                                envios[chave] += lancamento.valor
                                # Adicionar detalhes para o PDF
                                envios_detalhados[chave].append({
                                    'data': lancamento.data,
                                    'descricao': lancamento.descricao,
                                    'valor': lancamento.valor,
                                    'conta': lancamento.conta
                                })
                                break  # Para evitar dupla contagem
            
            total_envio_sede = sum(envios.values())
            
            # Adicionar ofertas OMN automaticamente aos envios detalhados
            for lancamento in lancamentos:
                if lancamento.tipo == 'Entrada' and lancamento.categoria:
                    categoria_lower = lancamento.categoria.lower()
                    if 'omn' in categoria_lower or 'missionaria' in categoria_lower:
                        envios_detalhados['omn'].append({
                            'data': lancamento.data,
                            'descricao': lancamento.categoria,
                            'conta': getattr(lancamento, 'conta', None),
                            'valor': float(lancamento.valor) if lancamento.valor else 0
                        })
            
        except Exception as e:
            print(f"DEBUG: Erro ao buscar envios: {e}")
            envios = {
                'oferta_voluntaria_conchas': 0.0,
                'site': 0.0,
                'projeto_filipe': 0.0,
                'forca_para_viver': 0.0,
                'contador_sede': 0.0
            }
            envios_detalhados = {
                'oferta_voluntaria_conchas': [],
                'site': [],
                'projeto_filipe': [],
                'forca_para_viver': [],
                'contador_sede': [],
                'omn': []
            }
            total_envio_sede = 0
        
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
                             envios=envios,
                             envios_detalhados=envios_detalhados,
                             total_envio_sede=total_envio_sede,
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
        # Pegar mês e ano da query string com validação
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        # Se não foram fornecidos na URL, usar o mês/ano atual
        if mes is None:
            mes = datetime.now().month
        if ano is None:
            ano = datetime.now().year
        
        # Validar valores
        if mes < 1 or mes > 12:
            mes = datetime.now().month
        if ano < 2020 or ano > 2030:
            ano = datetime.now().year
        
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
                # Verificar se é uma "Destinação" (não afeta saldo do caixa)
                eh_destinacao = any(x in categoria for x in [
                    'destinação', 'destinacao', 
                    'transferência interna', 'transferencia interna'
                ])
                
                # Apenas contabilizar como saída se NÃO for destinação
                if not eh_destinacao:
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
            as_attachment=False,
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
        # Pegar mês e ano da query string com validação
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        # Se não foram fornecidos na URL, usar o mês/ano atual
        if mes is None:
            mes = datetime.now().month
        if ano is None:
            ano = datetime.now().year
        
        # Validar valores
        if mes < 1 or mes > 12:
            mes = datetime.now().month
        if ano < 2020 or ano > 2030:
            ano = datetime.now().year
        
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
                    # Lógica corrigida e padronizada das ofertas:
                    # 1º: Verificar se é OMN (não computa no conselho, mas registrado)
                    if 'omn' in categoria or 'missionaria' in categoria or 'missionária' in categoria:
                        totais['ofertas_alcadas'] += valor  # Mantido por compatibilidade
                    # 2º: Verificar se é "Outras Ofertas" (não computa no conselho)
                    elif any(x in categoria for x in ['outras', 'especial', 'voluntaria', 'voluntária']):
                        totais['outras_ofertas'] += valor
                    # 3º: O resto são Ofertas Alçadas (computa 30% conselho)
                    else:
                        # Ofertas Alçadas = ofertas normais do ofertório
                        totais['ofertas_alcadas'] += valor
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
        # Calcular valor do conselho excluindo "OUTRAS OFERTAS"
        valor_para_conselho = totais['total_geral'] - totais.get('outras_ofertas', 0)
        totais['valor_conselho'] = valor_para_conselho * percentual
        
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
            as_attachment=False,
            download_name=nome_arquivo,
            mimetype='application/pdf'
        )

    except Exception as e:
        flash(f'Erro ao gerar PDF do relatório da sede: {str(e)}', 'danger')
        return redirect(url_for('financeiro.relatorio_sede'))