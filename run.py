import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Configuração para desenvolvimento
    app.run(debug=True, host='127.0.0.1', port=5000)
else:
    # Configuração para produção (Render, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
