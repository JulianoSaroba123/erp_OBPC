// SCRIPT DE DEBUG PARA CONSOLE DO NAVEGADOR
// Cole este código no console (F12) para diagnosticar problemas

console.log('🔍 DIAGNÓSTICO DO SISTEMA DE IMPORTAÇÃO');
console.log('=' * 50);

// Verificar elementos DOM
const elementos = {
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('arquivo'),
    fileInfo: document.getElementById('fileInfo'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    btnImportar: document.getElementById('btnImportar'),
    formUpload: document.getElementById('formUpload')
};

console.log('📋 Elementos encontrados:');
Object.keys(elementos).forEach(key => {
    const existe = !!elementos[key];
    console.log(`   ${existe ? '✅' : '❌'} ${key}: ${existe ? 'OK' : 'NÃO ENCONTRADO'}`);
});

// Verificar event listeners
console.log('\n🎯 Testando event listeners:');

if (elementos.uploadArea) {
    console.log('   ✅ uploadArea.onclick:', typeof elementos.uploadArea.onclick);
}

if (elementos.fileInput) {
    console.log('   ✅ fileInput.onchange:', typeof elementos.fileInput.onchange);
}

// Verificar funções globais
console.log('\n🔧 Funções globais:');
console.log('   ✅ removerArquivo:', typeof window.removerArquivo);
console.log('   ✅ resetForm:', typeof window.resetForm);

// Teste de seleção de arquivo
console.log('\n🧪 Para testar seleção de arquivo, execute:');
console.log('document.getElementById("arquivo").click()');

// Função de teste
window.testarImportacao = function() {
    console.log('🧪 Iniciando teste de importação...');
    
    // Simular clique no input
    if (elementos.fileInput) {
        elementos.fileInput.click();
        console.log('✅ Clique simulado no input de arquivo');
    } else {
        console.log('❌ Input de arquivo não encontrado');
    }
};

console.log('\n💡 Para testar, execute: testarImportacao()');
console.log('💡 Ou simplesmente tente selecionar um arquivo manualmente');

// Monitorar mudanças no input
if (elementos.fileInput) {
    elementos.fileInput.addEventListener('change', function() {
        console.log('🔔 ARQUIVO SELECIONADO!');
        console.log('   📄 Nome:', this.files[0]?.name);
        console.log('   📦 Tamanho:', this.files[0]?.size);
    });
}

console.log('\n✅ Diagnóstico completo - Execute testarImportacao() para testar');