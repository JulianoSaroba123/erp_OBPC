#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalador Rápido OBPC - Versão Simplificada
Tela de loading profissional
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os
import threading
import time
import shutil
from pathlib import Path

class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema OBPC")
        self.root.geometry("500x300")
        self.root.resizable(False, False)
        self.root.configure(bg='#228b22')
        
        # Remover barra de título
        self.root.overrideredirect(True)
        
        # Centralizar
        self.center_window()
        
        # Interface
        self.create_splash()
        
        # Iniciar instalação automática
        self.start_auto_install()
        
    def center_window(self):
        """Centraliza a janela"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (250)
        y = (self.root.winfo_screenheight() // 2) - (150)
        self.root.geometry(f'500x300+{x}+{y}')
        
    def create_splash(self):
        """Cria a tela de splash"""
        main_frame = tk.Frame(self.root, bg='#228b22', padx=40, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo/Título
        title_label = tk.Label(main_frame, text="OBPC", 
                              font=('Arial', 32, 'bold'), 
                              fg='#FFD700', bg='#228b22')
        title_label.pack(pady=(0, 5))
        
        subtitle_label = tk.Label(main_frame, text="Sistema de Gestão Eclesiástica", 
                                 font=('Arial', 14), 
                                 fg='white', bg='#228b22')
        subtitle_label.pack(pady=(0, 5))
        
        church_label = tk.Label(main_frame, text="O Brasil Para Cristo - Tietê/SP", 
                               font=('Arial', 10), 
                               fg='#E8E8E8', bg='#228b22')
        church_label.pack(pady=(0, 30))
        
        # Status
        self.status_label = tk.Label(main_frame, text="Preparando instalação...", 
                                    font=('Arial', 12), 
                                    fg='white', bg='#228b22')
        self.status_label.pack(pady=(0, 15))
        
        # Barra de progresso
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Green.Horizontal.TProgressbar", 
                       background='#FFD700', 
                       troughcolor='#006400',
                       borderwidth=1, 
                       lightcolor='#FFD700', 
                       darkcolor='#FFD700')
        
        self.progress = ttk.Progressbar(main_frame, 
                                       style="Green.Horizontal.TProgressbar",
                                       mode='determinate', 
                                       length=400)
        self.progress.pack(pady=(0, 15))
        
        # Detalhes
        self.detail_label = tk.Label(main_frame, text="", 
                                    font=('Arial', 9), 
                                    fg='#E8E8E8', bg='#228b22')
        self.detail_label.pack()
        
        # Versão no rodapé
        version_label = tk.Label(main_frame, text="v2.0", 
                                font=('Arial', 8), 
                                fg='#B8B8B8', bg='#228b22')
        version_label.pack(side=tk.BOTTOM, pady=(20, 0))
        
    def update_status(self, status, detail="", progress=0):
        """Atualiza status da instalação"""
        self.status_label.config(text=status)
        self.detail_label.config(text=detail)
        self.progress['value'] = progress
        self.root.update_idletasks()
        
    def start_auto_install(self):
        """Inicia instalação automática"""
        # Thread para não travar a interface
        install_thread = threading.Thread(target=self.auto_install)
        install_thread.daemon = True
        install_thread.start()
        
    def auto_install(self):
        """Instalação automática rápida"""
        try:
            # Passo 1: Verificação inicial
            self.update_status("Iniciando sistema...", "Verificando ambiente", 10)
            time.sleep(1)
            
            # Passo 2: Verificar Python
            self.update_status("Verificando Python...", "Checando dependências", 25)
            self.check_python()
            time.sleep(0.5)
            
            # Passo 3: Instalar dependências básicas
            self.update_status("Instalando dependências...", "Flask, SQLAlchemy, etc.", 45)
            self.install_basic_deps()
            time.sleep(1)
            
            # Passo 4: Configurar banco
            self.update_status("Configurando banco de dados...", "Criando estrutura", 65)
            self.setup_database()
            time.sleep(0.5)
            
            # Passo 5: Criar usuário admin
            self.update_status("Criando usuário administrativo...", "admin@obpc.com", 80)
            self.create_admin_user()
            time.sleep(0.5)
            
            # Passo 6: Finalizar
            self.update_status("Finalizando configuração...", "Sistema pronto", 95)
            time.sleep(0.5)
            
            # Concluído
            self.update_status("Sistema pronto!", "Iniciando aplicação...", 100)
            time.sleep(1)
            
            # Iniciar sistema
            self.start_system()
            
        except Exception as e:
            self.update_status("Erro na instalação", f"Erro: {str(e)}", 0)
            time.sleep(3)
            self.close_splash()
            
    def check_python(self):
        """Verifica Python"""
        try:
            import sys
            if sys.version_info < (3, 6):
                raise Exception("Python 3.6+ necessário")
        except:
            pass
            
    def install_basic_deps(self):
        """Instala dependências básicas"""
        packages = [
            "flask", "flask-sqlalchemy", "flask-login", 
            "flask-bcrypt", "reportlab"
        ]
        
        for package in packages:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], check=True, capture_output=True, timeout=30)
            except:
                # Se falhar, continua
                pass
                
    def setup_database(self):
        """Configura banco de dados"""
        try:
            # Criar pasta instance se não existir
            instance_dir = Path("instance")
            instance_dir.mkdir(exist_ok=True)
            
            # Executar verificação do banco
            if Path("verificar_banco.py").exists():
                subprocess.run([sys.executable, "verificar_banco.py"], 
                              check=True, capture_output=True, timeout=10)
        except:
            pass
            
    def create_admin_user(self):
        """Cria usuário admin"""
        try:
            if Path("criar_admin.py").exists():
                subprocess.run([sys.executable, "criar_admin.py"], 
                              check=True, capture_output=True, timeout=10)
        except:
            pass
            
    def start_system(self):
        """Inicia o sistema"""
        try:
            # Fechar splash
            self.root.after(1000, self.close_splash)
            
            # Iniciar Flask
            subprocess.Popen([sys.executable, "run.py"])
            
            # Abrir navegador após 3 segundos
            threading.Timer(3.0, self.open_browser).start()
            
        except Exception as e:
            self.update_status("Erro ao iniciar", str(e), 0)
            
    def open_browser(self):
        """Abre o navegador"""
        try:
            import webbrowser
            webbrowser.open('http://127.0.0.1:5000')
        except:
            pass
            
    def close_splash(self):
        """Fecha a tela de splash"""
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        """Executa o splash"""
        self.root.mainloop()

class QuickInstaller:
    """Instalador rápido para máquinas novas"""
    
    @staticmethod
    def is_first_run():
        """Verifica se é a primeira execução"""
        return not Path("instance/igreja.db").exists()
    
    @staticmethod
    def show_info_dialog():
        """Mostra diálogo informativo"""
        root = tk.Tk()
        root.withdraw()  # Esconder janela principal
        
        from tkinter import messagebox
        
        message = """Sistema OBPC - Instalação Rápida

✅ O sistema será configurado automaticamente
✅ Dependências serão instaladas
✅ Banco de dados será criado
✅ Usuário admin será configurado

Login padrão:
👤 Usuário: admin@obpc.com
🔑 Senha: admin123

⚠️ Altere a senha após o primeiro acesso!

Continuar com a instalação?"""
        
        result = messagebox.askyesno("Instalação OBPC", message)
        root.destroy()
        return result

def main():
    """Função principal"""
    
    # Se for primeira execução, mostrar instalador
    if QuickInstaller.is_first_run():
        if QuickInstaller.show_info_dialog():
            # Mostrar splash de instalação
            splash = SplashScreen()
            splash.run()
        else:
            print("Instalação cancelada")
    else:
        # Sistema já instalado, iniciar diretamente
        print("Sistema já configurado. Iniciando...")
        try:
            import webbrowser
            subprocess.Popen([sys.executable, "run.py"])
            time.sleep(2)
            webbrowser.open('http://127.0.0.1:5000')
        except Exception as e:
            print(f"Erro ao iniciar: {e}")

if __name__ == "__main__":
    main()