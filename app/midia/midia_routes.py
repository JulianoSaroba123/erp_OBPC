"""
Rotas do Módulo Mídia - Sistema OBPC
Unifica todas as rotas: Agenda, Certificados e Carteiras
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app, abort
from app import db
from flask_login import login_required
from .midia_model import AgendaSemanal, Certificado, CarteiraMembro
from datetime import date, datetime, timedelta
import calendar
import os
from pathlib import Path, PurePosixPath
from werkzeug.exceptions import HTTPException
from uuid import uuid4

from PIL import Image
from app.utils.seguranca_modulos import proteger_modulo_legado

midia_bp = Blueprint('midia', __name__, url_prefix='/midia', template_folder='templates')


_SEEDS_CERTIFICADOS = {"midia.criar_exemplos", "midia.criar_certificados_exemplo"}
_FORMATOS_FOTO = {"PNG": ".png", "JPEG": ".jpg", "GIF": ".gif"}
_EXTENSOES_FOTO = set(_FORMATOS_FOTO.values()) | {".jpeg"}
_LIMITE_FOTO = 5 * 1024 * 1024
_MAX_PIXELS_FOTO = 25_000_000
_PASTA_FOTOS = "uploads/fotos_membros"


@midia_bp.before_request
def _proteger_midia():
    endpoint = request.endpoint or ""
    if endpoint in _SEEDS_CERTIFICADOS:
        if not _rotas_seed_habilitadas():
            abort(404)
        return proteger_modulo_legado("tem_acesso_configuracoes")
    if endpoint in {
        "midia.listar_carteiras", "midia.nova_carteira", "midia.salvar_carteira",
        "midia.editar_carteira", "midia.excluir_carteira", "midia.carteira_pdf", "midia.foto_carteira",
    }:
        return proteger_modulo_legado("tem_acesso_secretaria")
    if endpoint in {
        "midia.listar_certificados", "midia.novo_certificado", "midia.salvar_certificado",
        "midia.editar_certificado", "midia.excluir_certificado",
        "midia.visualizar_certificado", "midia.certificado_pdf",
    }:
        return proteger_modulo_legado("tem_acesso_certificados")
    return proteger_modulo_legado("tem_acesso_midia")


def _nome_foto_carteira(caminho):
    if not caminho:
        return None
    foto = PurePosixPath(caminho)
    if (foto.parent.as_posix() != _PASTA_FOTOS or "\\" in foto.name
            or foto.suffix.lower() not in _EXTENSOES_FOTO):
        return None
    return foto.name


def _rotas_seed_habilitadas():
    """Habilita rotas de seed apenas em ambiente de desenvolvimento explícito."""
    env = (os.environ.get('FLASK_ENV') or os.environ.get('APP_ENV') or '').strip().lower()
    ambiente_local = current_app.testing or env in {'development', 'dev', 'local'}
    return ambiente_local and current_app.config.get('ALLOW_DEV_SEED_ROUTES') is True

# ============================================================================
# ROTAS DOS CERTIFICADOS MODERNOS
# ============================================================================

@midia_bp.route('/certificados/pdf/<int:certificado_id>')
@login_required
def certificado_pdf(certificado_id):
    """Gera PDF do certificado - modelo genérico para batismo, alegre com cores para apresentação"""
    try:
        certificado = Certificado.query.get_or_404(certificado_id)
        
        # Buscar configurações da igreja (dados pastorais)
        from app.configuracoes.configuracoes_model import Configuracao
        config_obj = Configuracao.query.first()
        
        # Escolher template baseado no tipo de certificado
        if certificado.tipo_certificado == 'Apresentação':
            # Apresentação usa modelo alegre com cores por gênero
            template_name = 'certificados/certificado_apresentacao_alegre.html'
        else:
            # Batismo usa modelo genérico azul (sem distinção de gênero)
            template_name = 'certificados/certificado_modelo_azul.html'
        
        return render_template(template_name, 
                             certificado=certificado, 
                             config=config_obj)
    except HTTPException:
        raise
    except Exception as e:
        current_app.logger.error('Erro ao gerar PDF do certificado (%s)', type(e).__name__)
        flash('Erro ao gerar PDF do certificado.', 'danger')
        return redirect(url_for('midia.listar_certificados'))

# ============================================================================
# ROTAS DA AGENDA SEMANAL
# ============================================================================

@midia_bp.route('/agenda')
@midia_bp.route('/agenda/')
@login_required
def listar_agenda():
    """Lista agenda semanal com filtros"""
    try:
        # Obter filtros
        semana = request.args.get('semana', type=int)
        ano = request.args.get('ano', type=int)
        tipo_evento = request.args.get('tipo_evento', '')
        
        # Data atual como padrão
        hoje = date.today()
        iso_atual = hoje.isocalendar()
        semana = semana or iso_atual.week
        ano = ano or iso_atual.year
        inicio_semana = date.fromisocalendar(ano, semana, 1)
        fim_semana = inicio_semana + timedelta(days=6)
        
        # Query base
        query = AgendaSemanal.query.filter(AgendaSemanal.ativo == True)
        
        # Aplicar filtros apenas se especificados na URL
        if request.args.get('semana') and request.args.get('ano'):
            query = query.filter(
                AgendaSemanal.data_evento >= inicio_semana,
                AgendaSemanal.data_evento <= fim_semana
            )
        
        if tipo_evento:
            query = query.filter(AgendaSemanal.tipo_evento == tipo_evento)
            
        agenda = query.order_by(AgendaSemanal.data_evento.asc(), AgendaSemanal.titulo.asc()).all()
        
        # Tipos de evento para o filtro
        tipos_evento = ['Culto', 'Reunião', 'Evento', 'Anúncio']
        
        # Semanas do ano para o filtro
        semanas_ano = list(range(1, date(ano, 12, 28).isocalendar().week + 1))
        
        return render_template('agenda/lista_agenda.html',
                             agenda=agenda,
                             tipos_evento=tipos_evento,
                             semanas_ano=semanas_ano,
                             semana_atual=semana,
                             ano_atual=ano,
                             tipo_evento_atual=tipo_evento,
                             inicio_semana=inicio_semana,
                             fim_semana=fim_semana)
                             
    except HTTPException:
        raise
    except Exception as e:
        current_app.logger.error('Erro ao carregar agenda (%s)', type(e).__name__)
        flash('Erro ao carregar agenda.', 'danger')
        return redirect(url_for('usuario.index'))


@midia_bp.route('/agenda/novo')
@login_required
def novo_agenda():
    """Formulário para novo item da agenda"""
    tipos_evento = ['Culto', 'Reunião', 'Evento', 'Anúncio']
    return render_template('agenda/cadastro_agenda.html', tipos_evento=tipos_evento)


@midia_bp.route('/agenda/salvar', methods=['POST'])
@login_required
def salvar_agenda():
    """Salva item da agenda"""
    try:
        # Obter dados do formulário
        item_id = request.form.get('id')
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        data_evento = request.form.get('data_evento')
        hora_inicio = request.form.get('hora_inicio')
        hora_fim = request.form.get('hora_fim')
        local = request.form.get('local', '').strip()
        tipo_evento = request.form.get('tipo_evento')
        responsavel = request.form.get('responsavel', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        
        # Validações
        if not titulo:
            flash('Título é obrigatório!', 'danger')
            return redirect(url_for('midia.novo_agenda'))
            
        if not data_evento:
            flash('Data do evento é obrigatória!', 'danger')
            return redirect(url_for('midia.novo_agenda'))
            
        if not tipo_evento:
            flash('Tipo de evento é obrigatório!', 'danger')
            return redirect(url_for('midia.novo_agenda'))
        
        # Converter datas
        try:
            data_evento = datetime.strptime(data_evento, '%Y-%m-%d').date()
        except ValueError:
            flash('Data inválida!', 'danger')
            return redirect(url_for('midia.novo_agenda'))
        
        # Converter horários (opcional)
        hora_inicio_obj = None
        hora_fim_obj = None
        if hora_inicio:
            try:
                hora_inicio_obj = datetime.strptime(hora_inicio, '%H:%M').time()
            except ValueError:
                flash('Hora de início inválida!', 'danger')
                return redirect(url_for('midia.novo_agenda'))
                
        if hora_fim:
            try:
                hora_fim_obj = datetime.strptime(hora_fim, '%H:%M').time()
            except ValueError:
                flash('Hora de fim inválida!', 'danger')
                return redirect(url_for('midia.novo_agenda'))
        
        # Salvar ou atualizar
        if item_id:
            # Atualizar
            item = AgendaSemanal.query.get(item_id)
            if not item:
                flash('Item não encontrado!', 'danger')
                return redirect(url_for('midia.listar_agenda'))
        else:
            # Criar novo
            item = AgendaSemanal()
        
        # Atribuir dados
        item.titulo = titulo
        item.descricao = descricao
        item.data_evento = data_evento
        item.hora_inicio = hora_inicio_obj
        item.hora_fim = hora_fim_obj
        item.local = local
        item.tipo_evento = tipo_evento
        item.responsavel = responsavel
        item.observacoes = observacoes
        
        if not item_id:
            db.session.add(item)
        
        db.session.commit()
        
        flash('Item da agenda salvo com sucesso!', 'success')
        return redirect(url_for('midia.listar_agenda'))
        
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Erro ao salvar item (%s)', type(e).__name__)
        flash('Erro ao salvar item.', 'danger')
        return redirect(url_for('midia.novo_agenda'))


@midia_bp.route('/agenda/editar/<int:item_id>')
@login_required
def editar_agenda(item_id):
    """Formulário para editar item da agenda"""
    item = AgendaSemanal.query.get_or_404(item_id)
    tipos_evento = ['Culto', 'Reunião', 'Evento', 'Anúncio']
    return render_template('agenda/cadastro_agenda.html', item=item, tipos_evento=tipos_evento)


@midia_bp.route('/agenda/excluir/<int:item_id>', methods=['POST'])
@login_required
def excluir_agenda(item_id):
    """Exclui item da agenda (soft delete)"""
    try:
        item = AgendaSemanal.query.get_or_404(item_id)
        item.ativo = False
        db.session.commit()
        
        flash('Item da agenda excluído com sucesso!', 'success')
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Erro ao excluir item (%s)', type(e).__name__)
        flash('Erro ao excluir item.', 'danger')
    
    return redirect(url_for('midia.listar_agenda'))


@midia_bp.route('/agenda/pdf')
@login_required
def agenda_pdf():
    """Gera PDF da agenda semanal"""
    try:
        # Obter filtros
        semana = request.args.get('semana', type=int)
        ano = request.args.get('ano', type=int)
        
        # Data atual como padrão
        hoje = date.today()
        iso_atual = hoje.isocalendar()
        semana = semana or iso_atual.week
        ano = ano or iso_atual.year
        inicio_semana = date.fromisocalendar(ano, semana, 1)
        fim_semana = inicio_semana + timedelta(days=6)
        
        # Buscar agenda
        agenda = AgendaSemanal.query.filter(
            AgendaSemanal.ativo == True,
            AgendaSemanal.data_evento >= inicio_semana,
            AgendaSemanal.data_evento <= fim_semana
        ).order_by(AgendaSemanal.data_evento.asc(), AgendaSemanal.id.asc()).all()
        
        return render_template('agenda/agenda_pdf.html',
                             agenda=agenda,
                             semana=semana,
                             ano=ano,
                             dias_semana_datas=[inicio_semana + timedelta(days=i) for i in range(7)],
                             hoje=hoje,
                             gerado_em=datetime.now(),
                             inicio_semana=inicio_semana,
                             fim_semana=fim_semana)
    except HTTPException:
        raise
    except Exception as e:
        current_app.logger.error('Erro ao gerar PDF da agenda (%s)', type(e).__name__)
        flash('Erro ao gerar PDF da agenda.', 'danger')
        return redirect(url_for('midia.listar_agenda'))


@midia_bp.route('/agenda/visualizar/<int:item_id>')
@login_required
def visualizar_agenda(item_id):
    """Visualiza item da agenda em tela"""
    try:
        item = AgendaSemanal.query.get_or_404(item_id)
        return render_template('agenda/visualizar_agenda.html', item=item)
    except HTTPException:
        raise
    except Exception as e:
        current_app.logger.error('Erro ao visualizar item da agenda (%s)', type(e).__name__)
        flash('Erro ao visualizar item da agenda.', 'danger')
        return redirect(url_for('midia.listar_agenda'))


# ============================================================================
# ROTAS DOS CERTIFICADOS
# ============================================================================

@midia_bp.route('/certificados')
@midia_bp.route('/certificados/')
@login_required
def listar_certificados():
    """Lista certificados"""
    try:
        # Filtros
        tipo = request.args.get('tipo', '')
        nome = request.args.get('nome', '')
        
        # Query base
        query = Certificado.query
        
        # Aplicar filtros
        if tipo:
            query = query.filter(Certificado.tipo_certificado == tipo)
        if nome:
            query = query.filter(Certificado.nome_pessoa.ilike(f'%{nome}%'))
            
        certificados = query.order_by(Certificado.data_evento.desc()).all()
        
        # Tipos de certificado para o filtro
        tipos_certificado = ['Batismo', 'Apresentação']
        
        return render_template('certificados/lista_certificados.html',
                             certificados=certificados,
                             tipos_certificado=tipos_certificado,
                             tipo_atual=tipo,
                             nome_atual=nome,
                             mes_atual=None,
                             ano_atual=None)
    except HTTPException:
        raise
    except Exception as e:
        current_app.logger.error('Erro ao carregar certificados (%s)', type(e).__name__)
        flash('Erro ao carregar certificados.', 'danger')
        return render_template('certificados/lista_certificados.html',
                             certificados=[],
                             tipos_certificado=['Batismo', 'Apresentação'],
                             tipo_atual='',
                             nome_atual='',
                             mes_atual=None,
                             ano_atual=None)


@midia_bp.route('/certificados/criar-exemplos', methods=['POST'])
@login_required
def criar_exemplos():
    """Cria certificados de exemplo para teste"""
    try:
        # Verificar quantos certificados existem
        total_atual = Certificado.query.count()
        
        # Sempre criar alguns exemplos novos para teste
        flash(f'Sistema tinha {total_atual} certificados. Adicionando mais exemplos...', 'info')
        
        # Criar certificados de exemplo novos
        certificados = [
            Certificado(
                nome_pessoa="Lucas Gabriel Santos",
                tipo_certificado="Apresentação",
                genero="Masculino",
                data_evento=date(2025, 11, 10),
                pastor_responsavel="Pastor João Carlos",
                local_evento="Igreja OBPC - Tietê/SP",
                filiacao="Gabriel Santos e Lucia Maria Santos",
                padrinhos="André Costa e Priscila Costa",
                numero_certificado="APRES-M-003",
                observacoes="Apresentação especial - Nova criança"
            ),
            Certificado(
                nome_pessoa="Valentina Rosa Silva",
                tipo_certificado="Apresentação",
                genero="Feminino",
                data_evento=date(2025, 11, 15),
                pastor_responsavel="Pastor João Carlos",
                local_evento="Igreja OBPC - Tietê/SP",
                filiacao="Ricardo Silva e Rosa Maria Silva",
                padrinhos="Fernando Lima e Carla Lima",
                numero_certificado="APRES-F-003",
                observacoes="Apresentação especial - Bebê"
            ),
            Certificado(
                nome_pessoa="Miguel Angel Pereira",
                tipo_certificado="Batismo",
                genero="Masculino",
                data_evento=date(2025, 11, 5),
                pastor_responsavel="Pastor João Carlos",
                local_evento="Igreja OBPC - Tietê/SP",
                filiacao="Angel Pereira e Miriam Santos Pereira",
                numero_certificado="BAT-M-003",
                observacoes="Batismo por imersão - Jovem"
            )
        ]
        
        # Adicionar todos ao banco
        for cert in certificados:
            db.session.add(cert)
        
        db.session.commit()
        
        # Verificar total final
        total_final = Certificado.query.count()
        flash(f'✅ {len(certificados)} novos certificados adicionados! Total: {total_final}', 'success')
        return redirect(url_for('midia.listar_certificados'))
        
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Erro ao criar certificados (%s)', type(e).__name__)
        flash('Erro ao criar certificados.', 'danger')
        return redirect(url_for('midia.listar_certificados'))


@midia_bp.route('/certificados/novo')
@login_required
def novo_certificado():
    """Formulário para novo certificado"""
    tipos_certificado = ['Batismo', 'Apresentação']
    return render_template('certificados/cadastro_certificado.html', tipos_certificado=tipos_certificado)


@midia_bp.route('/certificados/salvar', methods=['POST'])
@login_required
def salvar_certificado():
    """Salva certificado"""
    try:
        # Obter dados do formulário
        certificado_id = request.form.get('id')
        nome_pessoa = request.form.get('nome_pessoa', '').strip()
        tipo_certificado = request.form.get('tipo_certificado')
        genero = request.form.get('genero')  # Reativado para cores azul/rosa
        data_evento = request.form.get('data_evento')
        pastor_responsavel = request.form.get('pastor_responsavel', '').strip()
        local_evento = request.form.get('local_evento', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        numero_certificado = request.form.get('numero_certificado', '').strip()
        padrinhos = request.form.get('padrinhos', '').strip()
        filiacao = request.form.get('filiacao', '').strip()
        genero = request.form.get('genero', '').strip()
        
        # Validações
        if not nome_pessoa:
            flash('Nome da pessoa é obrigatório!', 'danger')
            return redirect(url_for('midia.novo_certificado'))
            
        if not tipo_certificado:
            flash('Tipo de certificado é obrigatório!', 'danger')
            return redirect(url_for('midia.novo_certificado'))
            
        # if not genero:  # Temporariamente removido - Reativado para cores
        #     flash('Gênero é obrigatório!', 'danger')
        #     return redirect(url_for('midia.novo_certificado'))
            
        if not data_evento:
            flash('Data do evento é obrigatória!', 'danger')
            return redirect(url_for('midia.novo_certificado'))
            
        if not pastor_responsavel:
            flash('Pastor responsável é obrigatório!', 'danger')
            return redirect(url_for('midia.novo_certificado'))
        
        # Converter data
        try:
            data_evento = datetime.strptime(data_evento, '%Y-%m-%d').date()
        except ValueError:
            flash('Data inválida!', 'danger')
            return redirect(url_for('midia.novo_certificado'))
        
        # Salvar ou atualizar
        if certificado_id:
            certificado = Certificado.query.get(certificado_id)
            if not certificado:
                flash('Certificado não encontrado!', 'danger')
                return redirect(url_for('midia.listar_certificados'))
        else:
            certificado = Certificado()
        
        # Atribuir dados
        certificado.nome_pessoa = nome_pessoa
        certificado.tipo_certificado = tipo_certificado
        certificado.genero = genero  # Reativado para cores azul/rosa
        certificado.data_evento = data_evento
        certificado.pastor_responsavel = pastor_responsavel
        certificado.local_evento = local_evento
        certificado.observacoes = observacoes
        certificado.numero_certificado = numero_certificado
        certificado.padrinhos = padrinhos
        certificado.filiacao = filiacao
        
        if not certificado_id:
            db.session.add(certificado)
        
        db.session.commit()
        
        flash('Certificado salvo com sucesso!', 'success')
        return redirect(url_for('midia.listar_certificados'))
        
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Erro ao salvar certificado (%s)', type(e).__name__)
        flash('Erro ao salvar certificado.', 'danger')
        return redirect(url_for('midia.novo_certificado'))


@midia_bp.route('/certificados/editar/<int:certificado_id>')
@login_required
def editar_certificado(certificado_id):
    """Formulário para editar certificado"""
    certificado = Certificado.query.get_or_404(certificado_id)
    tipos_certificado = ['Batismo', 'Apresentação']
    return render_template('certificados/cadastro_certificado.html', 
                         certificado=certificado, tipos_certificado=tipos_certificado)


@midia_bp.route('/certificados/excluir/<int:certificado_id>', methods=['POST'])
@login_required
def excluir_certificado(certificado_id):
    """Exclui certificado"""
    try:
        certificado = Certificado.query.get_or_404(certificado_id)
        db.session.delete(certificado)
        db.session.commit()
        
        flash('Certificado excluído com sucesso!', 'success')
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Erro ao excluir certificado (%s)', type(e).__name__)
        flash('Erro ao excluir certificado.', 'danger')
    
    return redirect(url_for('midia.listar_certificados'))


@midia_bp.route('/certificados/visualizar/<int:certificado_id>')
@midia_bp.route('/certificados/visualizar/<int:certificado_id>/<template_style>')
@login_required
def visualizar_certificado(certificado_id, template_style=None):
    """Visualiza certificado em tela - modelo específico por tipo"""
    try:
        certificado = Certificado.query.get_or_404(certificado_id)
        
        # Buscar configurações da igreja (dados de assinaturas)
        from app.configuracoes.configuracoes_model import Configuracao
        config = Configuracao.query.first()
        
        # Escolher template baseado no tipo de certificado e estilo
        if certificado.tipo_certificado == 'Apresentação':
            if template_style == 'alegre':
                template_name = 'certificados/certificado_apresentacao_alegre.html'
            elif template_style == 'minimalista':
                template_name = 'certificados/certificado_apresentacao_minimalista.html'
            else:
                # Padrão para apresentação é o alegre e colorido
                template_name = 'certificados/certificado_apresentacao_alegre.html'
        else:
            template_name = 'certificados/visualizar_certificado.html'
            
        return render_template(template_name, certificado=certificado, config=config)
    except HTTPException:
        raise
    except Exception as e:
        current_app.logger.error('Erro ao visualizar certificado (%s)', type(e).__name__)
        flash('Erro ao visualizar certificado.', 'danger')
        return redirect(url_for('midia.listar_certificados'))


# ============================================================================
# ROTAS DAS CARTEIRAS DE MEMBRO
# ============================================================================

@midia_bp.route('/carteiras')
@midia_bp.route('/carteiras/')
@login_required
def listar_carteiras():
    """Lista carteiras de membro"""
    try:
        # Filtros
        nome = request.args.get('nome', '')
        numero = request.args.get('numero', '')
        
        # Query base
        query = CarteiraMembro.query.filter(CarteiraMembro.ativo == True)
        
        # Aplicar filtros
        if nome:
            query = query.filter(CarteiraMembro.nome_completo.ilike(f'%{nome}%'))
        if numero:
            query = query.filter(CarteiraMembro.numero_carteira.ilike(f'%{numero}%'))
            
        carteiras = query.order_by(CarteiraMembro.numero_carteira.asc()).all()
        
        return render_template('carteiras/lista_carteiras.html',
                             carteiras=carteiras,
                             nome_atual=nome,
                             numero_atual=numero)
                             
    except HTTPException:
        raise
    except Exception as e:
        current_app.logger.error('Erro ao carregar carteiras (%s)', type(e).__name__)
        flash('Erro ao carregar carteiras.', 'danger')
        return redirect(url_for('usuario.index'))


@midia_bp.route('/carteiras/nova')
@login_required
def nova_carteira():
    """Formulário para nova carteira"""
    proximo_numero = CarteiraMembro.gerar_proximo_numero()
    return render_template('carteiras/cadastro_carteira.html', proximo_numero=proximo_numero)


@midia_bp.route('/carteiras/salvar', methods=['POST'])
@login_required
def salvar_carteira():
    """Salva carteira de membro"""
    foto_nova = None
    foto_anterior = None
    try:
        # Obter dados do formulário
        carteira_id = request.form.get('id')
        numero_carteira = request.form.get('numero_carteira', '').strip()
        nome_completo = request.form.get('nome_completo', '').strip()
        data_nascimento = request.form.get('data_nascimento')
        telefone = request.form.get('telefone', '').strip()
        endereco = request.form.get('endereco', '').strip()
        data_batismo = request.form.get('data_batismo')
        cargo_funcao = request.form.get('cargo_funcao', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        
        # Validações
        if not numero_carteira:
            flash('Número da carteira é obrigatório!', 'danger')
            return redirect(url_for('midia.nova_carteira'))
            
        if not nome_completo:
            flash('Nome completo é obrigatório!', 'danger')
            return redirect(url_for('midia.nova_carteira'))
            
        if not data_nascimento:
            flash('Data de nascimento é obrigatória!', 'danger')
            return redirect(url_for('midia.nova_carteira'))
        
        # Converter datas
        try:
            data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        except ValueError:
            flash('Data de nascimento inválida!', 'danger')
            return redirect(url_for('midia.nova_carteira'))
        
        data_batismo_obj = None
        if data_batismo:
            try:
                data_batismo_obj = datetime.strptime(data_batismo, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de batismo inválida!', 'danger')
                return redirect(url_for('midia.nova_carteira'))
        
        # Verificar se número já existe (para novas carteiras)
        if not carteira_id:
            existe = CarteiraMembro.query.filter_by(numero_carteira=numero_carteira).first()
            if existe:
                flash('Número de carteira já existe!', 'danger')
                return redirect(url_for('midia.nova_carteira'))
        
        # Salvar ou atualizar
        if carteira_id:
            carteira = CarteiraMembro.query.get(carteira_id)
            if not carteira:
                flash('Carteira não encontrada!', 'danger')
                return redirect(url_for('midia.listar_carteiras'))
        else:
            carteira = CarteiraMembro()
        
        # Atribuir dados
        carteira.numero_carteira = numero_carteira
        carteira.nome_completo = nome_completo
        carteira.data_nascimento = data_nascimento
        carteira.telefone = telefone
        carteira.endereco = endereco
        carteira.data_batismo = data_batismo_obj
        carteira.cargo_funcao = cargo_funcao
        carteira.observacoes = observacoes
        
        foto = request.files.get('foto')
        if foto and foto.filename:
            try:
                foto.stream.seek(0, os.SEEK_END)
                if foto.stream.tell() > _LIMITE_FOTO:
                    raise ValueError
                foto.stream.seek(0)
                with Image.open(foto.stream) as imagem:
                    extensao = _FORMATOS_FOTO.get(imagem.format)
                    if not extensao or imagem.width * imagem.height > _MAX_PIXELS_FOTO:
                        raise ValueError
                    imagem.verify()
                foto.stream.seek(0)
            except (OSError, ValueError, Image.DecompressionBombError):
                db.session.rollback()
                flash('Envie uma imagem PNG, JPG ou GIF válida de até 5 MB.', 'warning')
                return redirect(url_for('midia.editar_carteira', carteira_id=carteira_id)
                                if carteira_id else url_for('midia.nova_carteira'))

            pasta = Path(current_app.static_folder) / _PASTA_FOTOS
            pasta.mkdir(parents=True, exist_ok=True)
            nome_anterior = _nome_foto_carteira(carteira.foto_caminho)
            if nome_anterior:
                foto_anterior = pasta / nome_anterior
            nome = f'carteira_{uuid4().hex}{extensao}'
            foto_nova = pasta / nome
            foto.save(foto_nova)
            carteira.foto_caminho = f'{_PASTA_FOTOS}/{nome}'

        if not carteira_id:
            db.session.add(carteira)
        
        db.session.commit()
        if foto_anterior:
            try:
                foto_anterior.unlink(missing_ok=True)
            except OSError:
                current_app.logger.warning('Não foi possível limpar a foto anterior da carteira.')

        flash('Carteira salva com sucesso!', 'success')
        return redirect(url_for('midia.listar_carteiras'))
        
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        if foto_nova:
            try:
                foto_nova.unlink(missing_ok=True)
            except OSError:
                current_app.logger.warning('Não foi possível limpar a foto não vinculada.')
        current_app.logger.error('Erro ao salvar carteira (%s)', type(e).__name__)
        flash('Erro ao salvar carteira.', 'danger')
        return redirect(url_for('midia.nova_carteira'))


@midia_bp.route('/carteiras/editar/<int:carteira_id>')
@login_required
def editar_carteira(carteira_id):
    """Formulário para editar carteira"""
    carteira = CarteiraMembro.query.get_or_404(carteira_id)
    return render_template('carteiras/cadastro_carteira.html', carteira=carteira)


@midia_bp.route('/carteiras/excluir/<int:carteira_id>', methods=['POST'])
@login_required
def excluir_carteira(carteira_id):
    """Exclui carteira (soft delete)"""
    try:
        carteira = CarteiraMembro.query.get_or_404(carteira_id)
        carteira.ativo = False
        db.session.commit()
        
        flash('Carteira excluída com sucesso!', 'success')
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Erro ao excluir carteira (%s)', type(e).__name__)
        flash('Erro ao excluir carteira.', 'danger')
    
    return redirect(url_for('midia.listar_carteiras'))


@midia_bp.route('/carteiras/foto/<int:carteira_id>')
@login_required
def foto_carteira(carteira_id):
    carteira = CarteiraMembro.query.filter_by(id=carteira_id, ativo=True).first_or_404()
    nome = _nome_foto_carteira(carteira.foto_caminho)
    if not nome:
        abort(404)

    pasta_fotos = os.path.join(current_app.static_folder, _PASTA_FOTOS)
    if os.path.islink(os.path.join(pasta_fotos, nome)):
        abort(404)

    resposta = send_from_directory(pasta_fotos, nome, conditional=False)
    resposta.headers["Cache-Control"] = "private, no-store"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    return resposta


@midia_bp.route('/carteiras/pdf/<int:carteira_id>')
@login_required
def carteira_pdf(carteira_id):
    """Visualiza/Gera PDF da carteira"""
    try:
        carteira = CarteiraMembro.query.get_or_404(carteira_id)
        return render_template('carteiras/visualizar_carteira.html', carteira=carteira)
    except HTTPException:
        raise
    except Exception as e:
        current_app.logger.error('Erro ao visualizar carteira (%s)', type(e).__name__)
        flash('Erro ao visualizar carteira.', 'danger')
        return redirect(url_for('midia.listar_carteiras'))


# ============================================================================
# ROTAS AUXILIARES
# ============================================================================

@midia_bp.route('/api/membros')
@login_required
def api_membros():
    """API para buscar membros (para autocomplete)"""
    termo = request.args.get('q', '')
    if len(termo) < 2:
        return jsonify([])
    
    # Implementar busca de membros
    # Por enquanto retorna lista vazia
    return jsonify([])


@midia_bp.route('/certificados/criar_exemplos', methods=['POST'])
@login_required
def criar_certificados_exemplo():
    """Rota especial para criar certificados de exemplo"""
    try:
        # Verificar se já existem certificados
        total_atual = Certificado.query.count()
        
        if total_atual > 0:
            flash(f'Já existem {total_atual} certificados no sistema!', 'info')
        else:
            # Criar certificados de exemplo
            certificados = [
                Certificado(
                    nome_pessoa="Ana Sofia Mendes",
                    tipo_certificado="Apresentação",
                    genero="Feminino",
                    data_evento=date(2025, 10, 15),
                    pastor_responsavel="Pastor João Carlos",
                    local_evento="Igreja OBPC - Tietê/SP",
                    filiacao="Roberto Mendes e Sofia Cristina Mendes",
                    padrinhos="Paulo Santos e Maria Santos",
                    numero_certificado="APRES-F-001",
                    observacoes="Certificado de exemplo - tema rosa"
                ),
                Certificado(
                    nome_pessoa="Pedro Henrique Costa",
                    tipo_certificado="Apresentação",
                    genero="Masculino",
                    data_evento=date(2025, 10, 20),
                    pastor_responsavel="Pastor João Carlos",
                    local_evento="Igreja OBPC - Tietê/SP",
                    filiacao="Carlos Costa e Helena Silva Costa",
                    padrinhos="José Roberto e Ana Carolina",
                    numero_certificado="APRES-M-001",
                    observacoes="Certificado de exemplo - tema azul"
                ),
                Certificado(
                    nome_pessoa="Isabella Santos",
                    tipo_certificado="Apresentação",
                    genero="Feminino",
                    data_evento=date(2025, 11, 1),
                    pastor_responsavel="Pastor João Carlos",
                    local_evento="Igreja OBPC - Tietê/SP",
                    filiacao="Fernando Santos e Isabela Oliveira",
                    padrinhos="Marcos Silva e Fernanda Silva",
                    numero_certificado="APRES-F-002",
                    observacoes="Certificado de exemplo - tema rosa"
                ),
                Certificado(
                    nome_pessoa="Carlos Roberto Silva",
                    tipo_certificado="Batismo",
                    genero="Masculino",
                    data_evento=date(2025, 9, 15),
                    pastor_responsavel="Pastor João Carlos",
                    local_evento="Igreja OBPC - Tietê/SP",
                    filiacao="Roberto Carlos Silva e Maria Silva",
                    numero_certificado="BAT-M-001",
                    observacoes="Certificado de exemplo - batismo"
                )
            ]
            
            # Adicionar todos ao banco
            for cert in certificados:
                db.session.add(cert)
            
            db.session.commit()
            
            flash(f'✅ {len(certificados)} certificados de exemplo criados com sucesso!', 'success')
        
        return redirect(url_for('midia.listar_certificados'))
        
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Erro ao criar certificados de exemplo (%s)', type(e).__name__)
        flash('Erro ao criar certificados de exemplo.', 'danger')
        return redirect(url_for('midia.listar_certificados'))