#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema OBPC - Executável Profissional
Iniciador avançado com tela de carregamento e verificações de sistema
"""

import subprocess
import sys
import os
import time
import webbrowser
import socket
import threading
from tela_carregamento import TelaCarregamento
from utils_sistema import verificar_dependencias, verificar_banco, porta_disponivel

class SistemaOBPC:
    def __init__(self):
        self.processo_servidor = None
        self.tela_loading = None
        self.porta = 5000
        self.url_sistema = f'http://127.0.0.1:{self.porta}'
        
    def verificar_sistema(self):
        """Verifica se o sistema está pronto para execução"""
        print("🔍 Verificando sistema...")
        
        # Verificar dependências
        try:
            verificar_dependencias()
            print("✅ Dependências OK")
        except SystemExit:
            return False
            
        # Verificar banco de dados
        if not verificar_banco():
            print("❌ Banco de dados não encontrado!")
            print("💡 Execute primeiro: InstalarOBPC.bat")
            return False
        print("✅ Banco de dados OK")
        
        # Encontrar porta disponível
        while not porta_disponivel(self.porta) and self.porta < 5010:
            self.porta += 1
        
        if self.porta >= 5010:
            print("❌ Nenhuma porta disponível encontrada!")
            return False
            
        self.url_sistema = f'http://127.0.0.1:{self.porta}'
        print(f"✅ Porta {self.porta} disponível")
        
        return True
    
    def iniciar_servidor(self):
        """Inicia o servidor Flask com configurações otimizadas"""
        env = os.environ.copy()
        env['FLASK_RUN_PORT'] = str(self.porta)
        env['FLASK_ENV'] = 'production'
        
        # Iniciar servidor sem console visível
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        self.processo_servidor = subprocess.Popen(
            [sys.executable, 'run.py'],
            env=env,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return self.processo_servidor
    
    def aguardar_servidor(self, timeout=45):
        """Aguarda o servidor Flask ficar disponível"""
        import requests
        inicio = time.time()
        
        while time.time() - inicio < timeout:
            try:
                response = requests.get(self.url_sistema, timeout=5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        return False
    
    def mostrar_tela_carregamento(self):
        """Mostra tela de carregamento em thread separada"""
        def executar_tela():
            self.tela_loading = TelaCarregamento()
            self.tela_loading.mainloop()
        
        thread_tela = threading.Thread(target=executar_tela, daemon=True)
        thread_tela.start()
        return thread_tela
    
    def fechar_tela_carregamento(self):
        """Fecha a tela de carregamento"""
        if self.tela_loading:
            try:
                self.tela_loading.after(0, self.tela_loading.destroy)
            except:
                pass
    
    def abrir_navegador(self):
        """Abre o sistema no navegador padrão"""
        time.sleep(1)  # Pequena pausa para estabilizar
        webbrowser.open(self.url_sistema)
    
    def ocultar_console(self):
        """Oculta a janela do console"""
        try:
            import ctypes
            # Obter handle da janela do console
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                # Ocultar a janela (SW_HIDE = 0)
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass  # Se não conseguir ocultar, continua normalmente
    
    def mostrar_console(self):
        """Mostra a janela do console novamente"""
        try:
            import ctypes
            # Obter handle da janela do console
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                # Mostrar a janela (SW_SHOW = 5)
                ctypes.windll.user32.ShowWindow(hwnd, 5)
        except Exception:
            pass
    
    def executar(self):
        """Executa o sistema completo"""
        print("🚀 Iniciando Sistema OBPC Profissional...")
        print("=" * 50)
        
        # Verificações do sistema
        if not self.verificar_sistema():
            input("\n❌ Sistema não pode ser iniciado. Pressione Enter para sair...")
            return False
        
        # Mostrar tela de carregamento
        print("📱 Exibindo tela de carregamento...")
        thread_tela = self.mostrar_tela_carregamento()
        time.sleep(2)  # Dar tempo para a tela aparecer
        
        # Ocultar console após mostrar a tela de carregamento
        print("🔍 Ocultando console...")
        self.ocultar_console()
        
        try:
            # Iniciar servidor
            print("🌐 Iniciando servidor Flask...")
            proc = self.iniciar_servidor()
            
            # Aguardar servidor ficar pronto
            print("⏳ Aguardando servidor ficar disponível...")
            if self.aguardar_servidor():
                print("✅ Servidor iniciado com sucesso!")
                
                # Fechar tela de carregamento
                self.fechar_tela_carregamento()
                
                # Abrir navegador
                print("🌐 Abrindo sistema no navegador...")
                self.abrir_navegador()
                
                # Mensagem final pode ser vista se o usuário mostrar o console novamente
                print(f"🎯 Sistema disponível em: {self.url_sistema}")
                print("📋 LOGIN PADRÃO:")
                print("   Email: admin@obpc.com")
                print("   Senha: 123456")
                print("\n⚠️  Para fechar o sistema, pressione Ctrl+C ou feche esta janela")
                
                # Manter servidor ativo
                try:
                    proc.wait()
                except KeyboardInterrupt:
                    print("\n🛑 Encerrando sistema...")
                    proc.terminate()
                    
                return True
                
            else:
                print("❌ Erro: Servidor não conseguiu iniciar!")
                # Mostrar console novamente em caso de erro
                self.mostrar_console()
                self.fechar_tela_carregamento()
                proc.terminate()
                return False
                
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")
            # Mostrar console novamente em caso de erro
            self.mostrar_console()
            self.fechar_tela_carregamento()
            if self.processo_servidor:
                self.processo_servidor.terminate()
            return False

if __name__ == '__main__':
    # Configurar codificação
    if sys.platform == "win32":
        os.system('chcp 65001 >nul')
    
    # Executar sistema
    sistema = SistemaOBPC()
    sucesso = sistema.executar()
    
    if not sucesso:
        input("\n⚠️  Pressione Enter para sair...")
    
    sys.exit(0 if sucesso else 1)
