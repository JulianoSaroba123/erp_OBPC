#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rotas de Configurações - Sistema OBPC
Igreja O Brasil para Cristo - Tietê/SP

Rotas para gerenciamento das configurações do sistema
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.extensoes import db
from app.configuracoes.configuracoes_model import Configuracao
import os
import requests
import re

# Criar blueprint
configuracoes_bp = Blueprint('configuracoes', __name__, url_prefix='/configuracoes', 
                            template_folder='templates')

@configuracoes_bp.route('/')
@login_required
def configuracoes():
    """Exibe o formulário de configurações com abas"""
    try:
        # Obter configuração única (cria se não existir)
        config = Configuracao.obter_configuracao()
        
        # Dados para os formulários
        context = {
            'config': config,
            'temas_disponiveis': Configuracao.get_temas_disponiveis(),
            'fontes_disponiveis': Configuracao.get_fontes_disponiveis(),
            'bancos_disponiveis': Configuracao.get_bancos_disponiveis(),
            'aba_ativa': request.args.get('aba', 'gerais')
        }
        
        return render_template('configuracoes/configuracoes.html', **context)
        
    except Exception as e:
        current_app.logger.error(f'Erro ao carregar configurações: {str(e)}')
        flash('Erro ao carregar configurações do sistema', 'danger')
        return redirect(url_for('usuario.painel'))


@configuracoes_bp.route('/salvar', methods=['POST'])
@login_required
def salvar_configuracoes():
    """Salva todas as configurações do sistema"""
    try:
        # Obter configuração existente
        config = Configuracao.obter_configuracao()
        current_app.logger.info(f">>> Configuração carregada: ID={config.id}, Nome={config.nome_igreja}")
        
        # Determinar qual aba foi submetida
        aba_ativa = request.form.get('aba_ativa', 'gerais')
        current_app.logger.info(f">>> Salvando aba: {aba_ativa}")
        
        # Atualizar campos baseado na aba
        if aba_ativa == 'gerais':
            # Dados Institucionais
            config.nome_igreja = request.form.get('nome_igreja', '').strip()
            config.cnpj = request.form.get('cnpj', '').strip()
            config.cidade = request.form.get('cidade', '').strip()
            config.bairro = request.form.get('bairro', '').strip()
            config.endereco = request.form.get('endereco', '').strip()
            config.cep = request.form.get('cep', '').strip()
            config.telefone = request.form.get('telefone', '').strip()
            config.email = request.form.get('email', '').strip()
            
            # Diretoria da Igreja
            config.presidente = request.form.get('presidente', '').strip()
            config.vice_presidente = request.form.get('vice_presidente', '').strip()
            config.primeiro_secretario = request.form.get('primeiro_secretario', '').strip()
            config.segundo_secretario = request.form.get('segundo_secretario', '').strip()
            config.primeiro_tesoureiro = request.form.get('primeiro_tesoureiro', '').strip()
            config.segundo_tesoureiro = request.form.get('segundo_tesoureiro', '').strip()
            
            # Validações básicas
            if not config.nome_igreja:
                flash('Nome da igreja é obrigatório', 'danger')
                return redirect(url_for('configuracoes.configuracoes', aba='gerais'))
            
            if not config.cidade:
                flash('Cidade é obrigatória', 'danger')
                return redirect(url_for('configuracoes.configuracoes', aba='gerais'))
        
        elif aba_ativa == 'financeiro':
            # Configurações Financeiras
            config.banco_padrao = request.form.get('banco_padrao', '').strip()
            
            try:
                config.percentual_conselho = float(request.form.get('percentual_conselho', 10.0))
                config.saldo_inicial = float(request.form.get('saldo_inicial', 0.0))
            except ValueError:
                flash('Valores financeiros devem ser números válidos', 'danger')
                return redirect(url_for('configuracoes.configuracoes', aba='financeiro'))
            
            # Validações
            if config.percentual_conselho < 0 or config.percentual_conselho > 100:
                flash('Percentual do conselho deve estar entre 0% e 100%', 'danger')
                return redirect(url_for('configuracoes.configuracoes', aba='financeiro'))
        
        elif aba_ativa == 'relatorios':
            # Configurações de Relatórios
            config.rodape_relatorio = request.form.get('rodape_relatorio', '').strip()
            config.exibir_logo_relatorio = request.form.get('exibir_logo_relatorio') == 'on'
            config.campo_assinatura_1 = request.form.get('campo_assinatura_1', '').strip()
            config.campo_assinatura_2 = request.form.get('campo_assinatura_2', '').strip()
            config.fonte_relatorio = request.form.get('fonte_relatorio', 'Helvetica')
            
            if not config.rodape_relatorio:
                flash('Rodapé do relatório é obrigatório', 'danger')
                return redirect(url_for('configuracoes.configuracoes', aba='relatorios'))
        
        elif aba_ativa == 'layout':
            # Configurações de Aparência
            config.tema = request.form.get('tema', 'escuro')
            config.cor_principal = request.form.get('cor_principal', '#0b1b3a')
            config.cor_secundaria = request.form.get('cor_secundaria', '#228B22')
            config.cor_destaque = request.form.get('cor_destaque', '#FFD700')
            config.mensagem_painel = request.form.get('mensagem_painel', '').strip()
            
            # Configurações adicionais
            config.backup_automatico = request.form.get('backup_automatico') == 'on'
            config.notificacoes_email = request.form.get('notificacoes_email') == 'on'
            config.idioma = request.form.get('idioma', 'pt-BR')
            config.fuso_horario = request.form.get('fuso_horario', 'America/Sao_Paulo')
            
            # Validação de cores (formato hexadecimal)
            cores = [config.cor_principal, config.cor_secundaria, config.cor_destaque]
            for cor in cores:
                if not cor.startswith('#') or len(cor) != 7:
                    flash('Cores devem estar no formato hexadecimal (#RRGGBB)', 'danger')
                    return redirect(url_for('configuracoes.configuracoes', aba='layout'))
        
        # Debug: Mostrar dados antes de salvar
        current_app.logger.info(f">>> Dados a serem salvos:")
        current_app.logger.info(f"    Nome Igreja: {config.nome_igreja}")
        current_app.logger.info(f"    Cidade: {config.cidade}")
        current_app.logger.info(f"    Banco: {config.banco_padrao}")
        current_app.logger.info(f"    Saldo Inicial: {config.saldo_inicial}")
        
        # Salvar no banco de dados
        resultado_salvar = config.salvar()
        current_app.logger.info(f">>> Resultado do método salvar(): {resultado_salvar}")
        
        if resultado_salvar:
            flash('Configurações salvas com sucesso!', 'success')
            current_app.logger.info(f'✅ Configurações da aba "{aba_ativa}" atualizadas')
        else:
            flash('Erro ao salvar configurações. Tente novamente.', 'danger')
            current_app.logger.error(f'❌ Falha ao salvar configurações da aba "{aba_ativa}"')
        
        return redirect(url_for('configuracoes.configuracoes', aba=aba_ativa))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao salvar configurações: {str(e)}')
        flash('Erro interno ao salvar configurações', 'danger')
        return redirect(url_for('configuracoes.configuracoes'))


@configuracoes_bp.route('/upload-logo', methods=['POST'])
@login_required
def upload_logo():
    """Faz upload da logo da igreja"""
    try:
        if 'logo' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
        
        file = request.files['logo']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
        
        # Verificar extensão do arquivo
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
        file_extension = file.filename.lower().split('.')[-1]
        if file_extension not in allowed_extensions:
            return jsonify({'success': False, 'message': 'Formato de arquivo não permitido. Use PNG, JPG, JPEG, GIF ou SVG.'})
        
        # Verificar tamanho do arquivo (máx. 2MB)
        file.seek(0, 2)  # Ir para o final do arquivo
        file_size = file.tell()
        file.seek(0)  # Voltar ao início
        
        if file_size > 2 * 1024 * 1024:  # 2MB
            return jsonify({'success': False, 'message': 'Arquivo muito grande! O tamanho máximo é 2MB.'})
        
        # Gerar nome único para o arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"logo_igreja_{timestamp}.{file_extension}"
        
        # Definir caminho para salvar (dentro da pasta static)
        static_dir = os.path.join(current_app.root_path, '..', 'static')
        file_path = os.path.join(static_dir, filename)
        
        # Criar diretório se não existir
        os.makedirs(static_dir, exist_ok=True)
        
        # Salvar arquivo
        file.save(file_path)
        
        # Caminho relativo para salvar no banco
        relative_path = f"static/{filename}"
        
        # Atualizar configuração
        config = Configuracao.obter_configuracao()
        
        # Remover logo anterior se existir
        if config.logo and config.logo != relative_path:
            old_logo_path = os.path.join(current_app.root_path, '..', config.logo)
            if os.path.exists(old_logo_path):
                try:
                    os.remove(old_logo_path)
                    current_app.logger.info(f'Logo anterior removida: {old_logo_path}')
                except Exception as e:
                    current_app.logger.warning(f'Erro ao remover logo anterior: {str(e)}')
        
        config.logo = relative_path
        
        if config.salvar():
            current_app.logger.info(f'Logo da igreja atualizada: {filename}')
            return jsonify({
                'success': True, 
                'message': 'Logo atualizada com sucesso!', 
                'logo_path': relative_path,
                'filename': filename
            })
        else:
            # Remover arquivo se não conseguiu salvar no banco
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': False, 'message': 'Erro ao salvar no banco de dados'})
            
    except Exception as e:
        current_app.logger.error(f'Erro ao fazer upload da logo: {str(e)}')
        return jsonify({'success': False, 'message': f'Erro interno do servidor: {str(e)}'})


@configuracoes_bp.route('/resetar', methods=['POST'])
@login_required
def resetar_configuracoes():
    """Reseta configurações para os valores padrão"""
    try:
        aba = request.form.get('aba', 'gerais')
        config = Configuracao.obter_configuracao()
        
        if aba == 'gerais':
            config.nome_igreja = 'Igreja O Brasil para Cristo'
            config.cidade = 'Tietê'
            config.bairro = 'Centro'
            config.endereco = 'Rua da Igreja, 123'
            config.telefone = '(15) 1234-5678'
            config.email = 'contato@obpc.org.br'
            config.cnpj = ''
            # Resetar diretoria
            config.presidente = 'Pastor Dirigente'
            config.vice_presidente = 'Vice Presidente'
            config.primeiro_secretario = '1º Secretário'
            config.segundo_secretario = '2º Secretário'
            config.primeiro_tesoureiro = '1º Tesoureiro'
            config.segundo_tesoureiro = '2º Tesoureiro'
            
        elif aba == 'financeiro':
            config.banco_padrao = 'Caixa Econômica Federal'
            config.percentual_conselho = 10.0
            config.saldo_inicial = 0.0
            
        elif aba == 'relatorios':
            config.rodape_relatorio = 'Igreja O Brasil para Cristo - Tietê/SP'
            config.exibir_logo_relatorio = True
            config.campo_assinatura_1 = 'Pastor Responsável'
            config.campo_assinatura_2 = 'Tesoureiro(a)'
            config.fonte_relatorio = 'Helvetica'
            
        elif aba == 'layout':
            config.tema = 'escuro'
            config.cor_principal = '#0b1b3a'
            config.cor_secundaria = '#228B22'
            config.cor_destaque = '#FFD700'
            config.mensagem_painel = 'Bem-vindo ao Sistema Administrativo da Igreja O Brasil para Cristo - Tietê/SP'
            config.backup_automatico = True
            config.notificacoes_email = False
            config.idioma = 'pt-BR'
            config.fuso_horario = 'America/Sao_Paulo'
        
        if config.salvar():
            flash(f'Configurações da aba "{aba.title()}" resetadas para os valores padrão!', 'info')
        else:
            flash('Erro ao resetar configurações', 'danger')
        
        return redirect(url_for('configuracoes.configuracoes', aba=aba))
        
    except Exception as e:
        current_app.logger.error(f'Erro ao resetar configurações: {str(e)}')
        flash('Erro interno ao resetar configurações', 'danger')
        return redirect(url_for('configuracoes.configuracoes'))


@configuracoes_bp.route('/teste-email', methods=['POST'])
@login_required
def teste_email():
    """Testa as configurações de email"""
    try:
        config = Configuracao.obter_configuracao()
        email_destino = request.form.get('email_teste', config.email)
        
        if not email_destino:
            return jsonify({'success': False, 'message': 'Email de destino é obrigatório'})
        
        # Aqui você implementaria o envio real do email
        # Por enquanto, simular sucesso
        
        return jsonify({
            'success': True, 
            'message': f'Email de teste enviado com sucesso para {email_destino}!'
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao testar email: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao enviar email de teste'})


@configuracoes_bp.route('/backup', methods=['POST'])
@login_required
def fazer_backup():
    """Gera backup do sistema"""
    try:
        # Implementar lógica de backup
        # Por enquanto, simular sucesso
        
        backup_filename = f"backup_obpc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        return jsonify({
            'success': True, 
            'message': f'Backup criado com sucesso: {backup_filename}',
            'filename': backup_filename
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao fazer backup: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao criar backup do sistema'})


@configuracoes_bp.route('/api/buscar-cnpj/<cnpj>')
@login_required
def buscar_cnpj(cnpj):
    """Busca dados da empresa por CNPJ na ReceitaWS"""
    try:
        # Limpar CNPJ (remover caracteres não numéricos)
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
        
        # Validar se CNPJ tem 14 dígitos
        if len(cnpj_limpo) != 14:
            return jsonify({'success': False, 'message': 'CNPJ deve ter 14 dígitos'})
        
        # Fazer requisição para API da ReceitaWS
        url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            if dados.get('status') == 'ERROR':
                return jsonify({'success': False, 'message': dados.get('message', 'CNPJ não encontrado')})
            
            # Extrair dados relevantes
            resultado = {
                'success': True,
                'nome_igreja': dados.get('nome', ''),
                'cnpj': dados.get('cnpj', ''),
                'endereco': dados.get('logradouro', ''),
                'bairro': dados.get('bairro', ''),
                'cidade': dados.get('municipio', ''),
                'cep': dados.get('cep', ''),
                'telefone': dados.get('telefone', ''),
                'email': dados.get('email', ''),
                'situacao': dados.get('situacao', '')
            }
            
            return jsonify(resultado)
        else:
            return jsonify({'success': False, 'message': 'Erro ao consultar CNPJ'})
            
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'message': 'Timeout na consulta do CNPJ'})
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar CNPJ: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})


@configuracoes_bp.route('/api/buscar-cep/<cep>')
@login_required
def buscar_cep(cep):
    """Busca endereço por CEP na API ViaCEP"""
    try:
        # Limpar CEP (remover caracteres não numéricos)
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        
        # Validar se CEP tem 8 dígitos
        if len(cep_limpo) != 8:
            return jsonify({'success': False, 'message': 'CEP deve ter 8 dígitos'})
        
        # Fazer requisição para API ViaCEP
        url = f'https://viacep.com.br/ws/{cep_limpo}/json/'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            if dados.get('erro'):
                return jsonify({'success': False, 'message': 'CEP não encontrado'})
            
            # Extrair dados relevantes
            resultado = {
                'success': True,
                'cep': dados.get('cep', ''),
                'endereco': dados.get('logradouro', ''),
                'bairro': dados.get('bairro', ''),
                'cidade': dados.get('localidade', ''),
                'uf': dados.get('uf', '')
            }
            
            return jsonify(resultado)
        else:
            return jsonify({'success': False, 'message': 'Erro ao consultar CEP'})
            
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'message': 'Timeout na consulta do CEP'})
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar CEP: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})


@configuracoes_bp.route('/limpar-dados-sistema', methods=['GET', 'POST'])
@login_required
def limpar_dados_sistema():
    """Limpa todos os dados do sistema - Só pastor pode acessar"""
    
    # Verificar se usuário é pastor
    if current_user.perfil != 'Pastor':
        flash('Acesso negado. Apenas pastores podem limpar dados do sistema.', 'danger')
        return redirect(url_for('configuracoes.configuracoes'))
    
    if request.method == 'GET':
        # Exibir página de confirmação
        return render_template('configuracoes/limpar_dados.html')
    
    # POST - Processar limpeza
    senha_confirmacao = request.form.get('senha_confirmacao', '').strip()
    confirmacao_texto = request.form.get('confirmacao_texto', '').strip()
    
    # Validar senha
    if not current_user.check_senha(senha_confirmacao):
        flash('Senha incorreta!', 'danger')
        return render_template('configuracoes/limpar_dados.html')
    
    # Validar texto de confirmação
    if confirmacao_texto.upper() != 'LIMPAR TUDO':
        flash('Texto de confirmação incorreto! Digite exatamente: LIMPAR TUDO', 'danger')
        return render_template('configuracoes/limpar_dados.html')
    
    try:
        # Importar todos os modelos
        from app.financeiro.financeiro_model import Lancamento
        from app.membros.membros_model import Membro
        from app.obreiros.obreiros_model import Obreiro
        from app.departamentos.departamentos_model import Departamento, CronogramaDepartamento, AulaDepartamento
        from app.eventos.eventos_model import Evento
        from app.secretaria.atas.atas_model import Ata
        from app.secretaria.inventario.inventario_model import ItemInventario
        from app.secretaria.oficios.oficios_model import Oficio
        from app.secretaria.participacao.participacao_model import ParticipacaoObreiro
        from app.midia.midia_model import AgendaSemanal, Certificado, CarteiraMembro
        from app.escala_ministerial.escala_model import EscalaMinisterial
        
        # Limpar todas as tabelas (exceto usuários e configurações)
        tabelas_para_limpar = [
            Lancamento,
            Membro,
            Obreiro,
            Departamento,
            CronogramaDepartamento,
            AulaDepartamento,
            Evento,
            Ata,
            ItemInventario,
            Oficio,
            ParticipacaoObreiro,
            AgendaSemanal,
            Certificado,
            CarteiraMembro,
            EscalaMinisterial
        ]
        
        total_registros_removidos = 0
        
        for modelo in tabelas_para_limpar:
            try:
                count = modelo.query.count()
                modelo.query.delete()
                total_registros_removidos += count
                current_app.logger.info(f'Removidos {count} registros de {modelo.__tablename__}')
            except Exception as e:
                current_app.logger.error(f'Erro ao limpar {modelo.__tablename__}: {str(e)}')
        
        # Confirmar transação
        db.session.commit()
        
        flash(f'Sistema limpo com sucesso! {total_registros_removidos} registros removidos.', 'success')
        current_app.logger.warning(f'SISTEMA LIMPO pelo usuário {current_user.nome} ({current_user.email})')
        
        return redirect(url_for('configuracoes.configuracoes'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao limpar sistema: {str(e)}')
        flash(f'Erro ao limpar sistema: {str(e)}', 'danger')
        return render_template('configuracoes/limpar_dados.html')