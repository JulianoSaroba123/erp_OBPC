#!/usr/bin/env python3
"""
TESTE DIRETO DE UPLOAD - MODO EMERGENCY
"""

from flask import Flask, render_template_string

app = Flask(__name__)

TEMPLATE_TESTE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚨 TESTE EMERGENCIAL DE UPLOAD</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .upload-area {
            border: 3px dashed #007bff;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover {
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="alert alert-danger">
            <h3>🚨 MODO EMERGENCIAL - TESTE DIRETO</h3>
            <p>Este é um teste isolado para verificar se o JavaScript funciona</p>
        </div>
        
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5><i class="fas fa-upload me-2"></i>Teste de Upload</h5>
                    </div>
                    <div class="card-body">
                        <!-- Área de Upload -->
                        <div id="uploadArea" class="upload-area">
                            <i class="fas fa-cloud-upload-alt fa-4x text-primary mb-3"></i>
                            <h4>CLIQUE AQUI PARA TESTAR</h4>
                            <p class="text-muted">Selecione qualquer arquivo</p>
                        </div>
                        
                        <!-- Input File -->
                        <input type="file" id="arquivo" class="d-none" accept=".csv,.xls,.xlsx">
                        
                        <!-- Resultado -->
                        <div id="resultado" class="mt-4"></div>
                        
                        <!-- Botão -->
                        <button id="btnTeste" class="btn btn-success btn-lg mt-3" disabled>
                            <i class="fas fa-check"></i> ARQUIVO SELECIONADO!
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5><i class="fas fa-bug me-2"></i>Debug</h5>
                    </div>
                    <div class="card-body">
                        <div id="debug">
                            <p>🔄 Aguardando ação...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        console.log('🚀 TESTE EMERGENCIAL INICIADO');
        
        let debugDiv = document.getElementById('debug');
        let resultadoDiv = document.getElementById('resultado');
        
        function log(msg) {
            console.log(msg);
            debugDiv.innerHTML += '<p>' + msg + '</p>';
        }
        
        function testarArquivo() {
            log('📁 Função testarArquivo() chamada');
            
            const input = document.getElementById('arquivo');
            const file = input.files[0];
            
            log('📄 Input files length: ' + input.files.length);
            
            if (file) {
                log('✅ ARQUIVO ENCONTRADO!');
                log('📂 Nome: ' + file.name);
                log('📦 Tamanho: ' + file.size + ' bytes');
                log('🏷️ Tipo: ' + file.type);
                
                // Mostrar resultado visual
                resultadoDiv.innerHTML = `
                    <div class="alert alert-success">
                        <h5>🎉 SUCESSO!</h5>
                        <p><strong>Nome:</strong> ${file.name}</p>
                        <p><strong>Tamanho:</strong> ${(file.size / 1024 / 1024).toFixed(2)} MB</p>
                        <p><strong>Tipo:</strong> ${file.type}</p>
                    </div>
                `;
                
                // Habilitar botão
                document.getElementById('btnTeste').disabled = false;
                
                // Esconder área de upload
                document.getElementById('uploadArea').innerHTML = `
                    <div class="alert alert-success">
                        <h4>✅ ARQUIVO CARREGADO!</h4>
                        <p>${file.name}</p>
                        <button onclick="resetar()" class="btn btn-warning">Escolher Outro</button>
                    </div>
                `;
                
            } else {
                log('❌ NENHUM ARQUIVO ENCONTRADO');
                resultadoDiv.innerHTML = '<div class="alert alert-danger">❌ Erro: Nenhum arquivo</div>';
            }
        }
        
        function resetar() {
            document.getElementById('arquivo').value = '';
            document.getElementById('btnTeste').disabled = true;
            resultadoDiv.innerHTML = '';
            document.getElementById('uploadArea').innerHTML = `
                <i class="fas fa-cloud-upload-alt fa-4x text-primary mb-3"></i>
                <h4>CLIQUE AQUI PARA TESTAR</h4>
                <p class="text-muted">Selecione qualquer arquivo</p>
            `;
            log('🔄 Reset realizado');
        }
        
        // SETUP
        document.addEventListener('DOMContentLoaded', function() {
            log('📋 DOM carregado');
            
            // Clique na área
            document.getElementById('uploadArea').onclick = function() {
                log('🖱️ Clique na área detectado');
                document.getElementById('arquivo').click();
            };
            
            // Mudança no input
            document.getElementById('arquivo').onchange = function() {
                log('🔄 Change event detectado');
                testarArquivo();
            };
            
            log('✅ Eventos configurados');
            log('🎯 TUDO PRONTO - CLIQUE NA ÁREA AZUL!');
        });
    </script>
</body>
</html>
"""

@app.route('/teste-upload')
def teste_upload():
    return render_template_string(TEMPLATE_TESTE)

if __name__ == '__main__':
    print("🚨 SERVIDOR DE TESTE EMERGENCIAL")
    print("📍 Acesse: http://127.0.0.1:5001/teste-upload")
    print("🎯 Este teste vai mostrar EXATAMENTE onde está o problema!")
    app.run(host='127.0.0.1', port=5001, debug=True)