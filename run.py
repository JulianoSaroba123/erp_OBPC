import os
import sys
import traceback
from app import create_app

# Configurar encoding UTF-8 para evitar erros com caracteres especiais no Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

try:
    app = create_app()
except Exception as e:
    print("Falha ao criar a aplicação Flask:")
    traceback.print_exc()
    raise

if __name__ == '__main__':
    try:
        # Configuração para desenvolvimento
        app.run(debug=True, host='127.0.0.1', port=5000)
    except Exception as e:
        print("Erro ao iniciar o servidor de desenvolvimento:")
        traceback.print_exc()
        raise
else:
    # Configuração para produção (Render, Heroku, etc.)
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print("Erro ao iniciar o servidor em produção:")
        traceback.print_exc()
        raise
