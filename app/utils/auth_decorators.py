"""
Sistema de Controle de Acesso - Decoradores
Sistema OBPC - Organização Brasileira de Pastores e Cooperadores
"""

from functools import wraps
try:
    from flask import redirect, url_for, flash, abort, request, jsonify
    from flask_login import current_user, login_required
except ImportError:
    # Fallback para casos onde os imports falham
    pass

def requer_nivel_acesso(*niveis_permitidos):
    """
    Decorador que requer níveis específicos de acesso
    
    Uso:
    @requer_nivel_acesso('master', 'administrador')
    @requer_nivel_acesso('tesoureiro')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not current_user.is_authenticated:
                    # Verifica se é uma requisição AJAX/JSON
                    if request.is_json or request.headers.get('Content-Type') == 'application/json':
                        return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
                    return redirect(url_for('usuario.login'))
                
                if current_user.nivel_acesso not in niveis_permitidos:
                    # Verifica se é uma requisição AJAX/JSON
                    if request.is_json or request.headers.get('Content-Type') == 'application/json':
                        return jsonify({
                            'success': False, 
                            'message': f'Acesso negado. Nível necessário: {", ".join(niveis_permitidos)}'
                        }), 403
                    flash(f'Acesso negado. Nível necessário: {", ".join(niveis_permitidos)}', 'danger')
                    return redirect(url_for(current_user.get_menu_principal()))
                
                return f(*args, **kwargs)
            except Exception as e:
                # Fallback em caso de erro
                if request.is_json or request.headers.get('Content-Type') == 'application/json':
                    return jsonify({'success': False, 'message': 'Erro ao processar requisição'}), 500
                return redirect(url_for('usuario.login'))
        return decorated_function
    return decorator

def requer_gerencia_usuarios(f):
    """Decorador para gerenciamento de usuários"""
    @wraps(f)
    @login_required  # Adicionar login_required explicitamente
    def decorated_function(*args, **kwargs):
        try:
            from flask import session
            import sys
            # Debug: Log informações de autenticação
            print(f"AUTH_CHECK: Path={request.path} Authenticated={current_user.is_authenticated}", flush=True)
            if hasattr(current_user, 'id'):
                print(f"AUTH_USER: ID={current_user.id} Email={current_user.email} Nivel={current_user.nivel_acesso}", flush=True)
            print(f"AUTH_SESSION: user_id={session.get('_user_id', 'N/A')} keys={list(session.keys())}", flush=True)
            sys.stdout.flush()
            
            # A verificação de is_authenticated já foi feita pelo @login_required
            # Apenas verificar permissão
            pode_gerenciar = current_user.pode_gerenciar_usuarios()
            print(f"PERMISSION_CHECK: nivel_acesso={current_user.nivel_acesso} pode_gerenciar={pode_gerenciar}", flush=True)
            sys.stdout.flush()
            
            if not pode_gerenciar:
                # Verifica se é uma requisição AJAX/JSON
                if request.is_json or request.headers.get('Content-Type') == 'application/json':
                    return jsonify({'success': False, 'message': 'Acesso negado. Apenas administradores podem gerenciar usuários.'}), 403
                flash('Acesso negado. Apenas administradores podem gerenciar usuários.', 'danger')
                return redirect(url_for(current_user.get_menu_principal()))
            
            return f(*args, **kwargs)
        except Exception as e:
            import sys
            print(f"AUTH_ERROR: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'message': 'Erro ao processar requisição'}), 500
            flash('Erro ao verificar permissões. Tente fazer login novamente.', 'danger')
            return redirect(url_for('usuario.login'))
    return decorated_function

# Simplificação dos outros decoradores para evitar conflitos
def requer_acesso_financeiro(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not current_user.is_authenticated or not current_user.tem_acesso_financeiro():
                flash('Acesso negado ao módulo financeiro.', 'danger')
                return redirect(url_for('usuario.login'))
            return f(*args, **kwargs)
        except:
            return redirect(url_for('usuario.login'))
    return decorated_function

def requer_acesso_secretaria(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not current_user.is_authenticated or not current_user.tem_acesso_secretaria():
                flash('Acesso negado ao módulo secretaria.', 'danger')
                return redirect(url_for('usuario.login'))
            return f(*args, **kwargs)
        except:
            return redirect(url_for('usuario.login'))
    return decorated_function

def requer_acesso_midia(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not current_user.is_authenticated or not current_user.tem_acesso_midia():
                flash('Acesso negado ao módulo mídia.', 'danger')
                return redirect(url_for('usuario.login'))
            return f(*args, **kwargs)
        except:
            return redirect(url_for('usuario.login'))
    return decorated_function

def requer_master(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not current_user.is_authenticated or current_user.nivel_acesso != 'master':
                # Verifica se é uma requisição AJAX/JSON
                if request.is_json or request.headers.get('Content-Type') == 'application/json':
                    return jsonify({'success': False, 'message': 'Acesso negado. Apenas usuários master.'}), 403
                flash('Acesso negado. Apenas usuários master.', 'danger')
                return redirect(url_for('usuario.login'))
            return f(*args, **kwargs)
        except:
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'message': 'Erro ao processar requisição'}), 500
            return redirect(url_for('usuario.login'))
    return decorated_function