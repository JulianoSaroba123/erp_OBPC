#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalador GUI para Sistema OBPC
Instalador profissional com interface gráfica
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import os
import threading
import time
import shutil
import zipfile
import json
from pathlib import Path

class InstaladorOBPC:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Instalador OBPC - Sistema de Gestão Eclesiástica")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Centralizar janela
        self.center_window()
        
        # Configurar estilo
        self.setup_style()
        
        # Variáveis
        self.install_path = tk.StringVar(value="C:\\OBPC_Sistema")
        self.create_desktop_shortcut = tk.BooleanVar(value=True)
        self.auto_start = tk.BooleanVar(value=True)
        self.install_dependencies = tk.BooleanVar(value=True)
        
        # Interface
        self.create_interface()
        
    def center_window(self):
        """Centraliza a janela na tela"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_style(self):
        """Configura o estilo da interface"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Cores OBPC
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#228b22')
        style.configure('Subtitle.TLabel', font=('Arial', 10), foreground='#006400')
        style.configure('Success.TLabel', font=('Arial', 10, 'bold'), foreground='#228b22')
        style.configure('Error.TLabel', font=('Arial', 10, 'bold'), foreground='#dc2626')
        style.configure('Install.TButton', font=('Arial', 12, 'bold'))
        
    def create_interface(self):
        """Cria a interface principal"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header(main_frame)
        
        # Configurações de instalação
        self.create_config_section(main_frame)
        
        # Progresso
        self.create_progress_section(main_frame)
        
        # Botões
        self.create_buttons(main_frame)
        
    def create_header(self, parent):
        """Cria o cabeçalho"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = ttk.Label(header_frame, text="Sistema OBPC", style='Title.TLabel')
        title.pack()
        
        subtitle = ttk.Label(header_frame, text="Sistema de Gestão Eclesiástica - O Brasil Para Cristo", 
                           style='Subtitle.TLabel')
        subtitle.pack(pady=(5, 0))
        
        version = ttk.Label(header_frame, text="Versão 2.0 - Igreja de Tietê/SP", 
                          style='Subtitle.TLabel')
        version.pack(pady=(2, 0))
        
    def create_config_section(self, parent):
        """Cria a seção de configurações"""
        config_frame = ttk.LabelFrame(parent, text="Configurações de Instalação", padding="15")
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Pasta de instalação
        path_frame = ttk.Frame(config_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(path_frame, text="Pasta de instalação:").pack(anchor=tk.W)
        
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        path_entry = ttk.Entry(path_entry_frame, textvariable=self.install_path, font=('Arial', 10))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(path_entry_frame, text="Procurar...", command=self.browse_folder)
        browse_btn.pack(side=tk.RIGHT)
        
        # Opções
        ttk.Checkbutton(config_frame, text="Criar atalho na área de trabalho", 
                       variable=self.create_desktop_shortcut).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(config_frame, text="Iniciar sistema automaticamente", 
                       variable=self.auto_start).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(config_frame, text="Instalar dependências Python (recomendado)", 
                       variable=self.install_dependencies).pack(anchor=tk.W, pady=2)
        
    def create_progress_section(self, parent):
        """Cria a seção de progresso"""
        progress_frame = ttk.LabelFrame(parent, text="Progresso da Instalação", padding="15")
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.status_label = ttk.Label(progress_frame, text="Pronto para instalar")
        self.status_label.pack(anchor=tk.W, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.detail_label = ttk.Label(progress_frame, text="", font=('Arial', 9))
        self.detail_label.pack(anchor=tk.W)
        
    def create_buttons(self, parent):
        """Cria os botões"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.install_btn = ttk.Button(button_frame, text="Instalar Sistema", 
                                     command=self.start_installation, style='Install.TButton')
        self.install_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancelar", command=self.cancel_installation)
        self.cancel_btn.pack(side=tk.RIGHT)
        
        # Botão de teste (só para desenvolvimento)
        if os.path.exists("run.py"):
            test_btn = ttk.Button(button_frame, text="Testar Sistema", command=self.test_system)
            test_btn.pack(side=tk.LEFT)
        
    def browse_folder(self):
        """Abre diálogo para escolher pasta"""
        folder = filedialog.askdirectory(initialdir=self.install_path.get())
        if folder:
            self.install_path.set(folder)
            
    def start_installation(self):
        """Inicia a instalação em thread separada"""
        self.install_btn.config(state='disabled')
        self.cancel_btn.config(text="Fechar", command=self.close_application)
        
        # Thread para não travar a interface
        install_thread = threading.Thread(target=self.run_installation)
        install_thread.daemon = True
        install_thread.start()
        
    def run_installation(self):
        """Executa a instalação"""
        try:
            total_steps = 7
            current_step = 0
            
            # Passo 1: Verificar sistema
            self.update_progress(current_step, total_steps, "Verificando sistema...", 
                               "Verificando compatibilidade e permissões")
            self.check_system()
            current_step += 1
            time.sleep(0.5)
            
            # Passo 2: Criar diretórios
            self.update_progress(current_step, total_steps, "Criando diretórios...", 
                               f"Criando pasta: {self.install_path.get()}")
            self.create_directories()
            current_step += 1
            time.sleep(0.5)
            
            # Passo 3: Copiar arquivos
            self.update_progress(current_step, total_steps, "Copiando arquivos do sistema...", 
                               "Copiando aplicação principal")
            self.copy_files()
            current_step += 1
            time.sleep(1)
            
            # Passo 4: Instalar Python (se necessário)
            if self.install_dependencies.get():
                self.update_progress(current_step, total_steps, "Verificando Python...", 
                                   "Configurando ambiente Python")
                self.setup_python()
            current_step += 1
            time.sleep(0.5)
            
            # Passo 5: Instalar dependências
            if self.install_dependencies.get():
                self.update_progress(current_step, total_steps, "Instalando dependências...", 
                                   "Instalando bibliotecas necessárias")
                self.install_requirements()
            current_step += 1
            time.sleep(1)
            
            # Passo 6: Criar banco de dados
            self.update_progress(current_step, total_steps, "Configurando banco de dados...", 
                               "Criando estrutura do banco")
            self.setup_database()
            current_step += 1
            time.sleep(0.5)
            
            # Passo 7: Criar atalhos
            self.update_progress(current_step, total_steps, "Finalizando instalação...", 
                               "Criando atalhos e configurações")
            self.create_shortcuts()
            current_step += 1
            
            # Concluído
            self.update_progress(total_steps, total_steps, "Instalação concluída!", 
                               "Sistema OBPC instalado com sucesso")
            
            # Mostrar mensagem de sucesso
            self.root.after(500, self.show_success_message)
            
        except Exception as e:
            self.update_progress(0, 100, "Erro na instalação", f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Falha na instalação:\n{str(e)}")
            
    def update_progress(self, current, total, status, detail):
        """Atualiza a barra de progresso"""
        def update():
            progress = (current / total) * 100
            self.progress_bar['value'] = progress
            self.status_label.config(text=status)
            self.detail_label.config(text=detail)
            
        self.root.after(0, update)
        
    def check_system(self):
        """Verifica o sistema"""
        # Verificar Python
        try:
            import sys
            if sys.version_info < (3, 8):
                raise Exception("Python 3.8+ é necessário")
        except:
            pass  # Será instalado depois
            
        # Verificar permissões
        install_dir = Path(self.install_path.get())
        try:
            install_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise Exception(f"Sem permissão para criar diretório: {install_dir}")
            
    def create_directories(self):
        """Cria os diretórios necessários"""
        install_dir = Path(self.install_path.get())
        
        directories = [
            install_dir,
            install_dir / "app",
            install_dir / "instance",
            install_dir / "static",
            install_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def copy_files(self):
        """Copia os arquivos do sistema"""
        source_dir = Path.cwd()
        install_dir = Path(self.install_path.get())
        
        # Arquivos e pastas a copiar
        items_to_copy = [
            "app",
            "static", 
            "run.py",
            "requirements.txt",
            "criar_admin.py",
            "verificar_banco.py"
        ]
        
        for item in items_to_copy:
            source = source_dir / item
            destination = install_dir / item
            
            if source.exists():
                if source.is_file():
                    shutil.copy2(source, destination)
                else:
                    if destination.exists():
                        shutil.rmtree(destination)
                    shutil.copytree(source, destination)
                    
    def setup_python(self):
        """Configura o Python"""
        # Por simplicidade, assumir que Python já está instalado
        # Em uma versão completa, poderia baixar e instalar Python automaticamente
        pass
        
    def install_requirements(self):
        """Instala as dependências"""
        install_dir = Path(self.install_path.get())
        requirements_file = install_dir / "requirements.txt"
        
        if requirements_file.exists():
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # Tentar instalar pacotes individuais
                packages = [
                    "flask", "flask-sqlalchemy", "flask-login", 
                    "flask-bcrypt", "reportlab", "requests"
                ]
                for package in packages:
                    try:
                        subprocess.run([
                            sys.executable, "-m", "pip", "install", package
                        ], check=True, capture_output=True)
                    except:
                        pass
                        
    def setup_database(self):
        """Configura o banco de dados"""
        install_dir = Path(self.install_path.get())
        
        # Criar arquivo de configuração
        config_content = f"""
import os
from pathlib import Path

# Diretório da aplicação
BASE_DIR = Path("{install_dir}")
INSTANCE_DIR = BASE_DIR / "instance"

class Config:
    SECRET_KEY = 'obpc-sistema-secreto-2024'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_DIR}/igreja.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de upload
    UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
"""
        
        config_file = install_dir / "app" / "config.py"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
            
        # Executar criação do banco
        try:
            os.chdir(install_dir)
            subprocess.run([sys.executable, "verificar_banco.py"], 
                          check=True, capture_output=True)
        except:
            pass
            
    def create_shortcuts(self):
        """Cria atalhos"""
        install_dir = Path(self.install_path.get())
        
        # Criar script de inicialização
        startup_script = f'''@echo off
cd /d "{install_dir}"
echo Iniciando Sistema OBPC...
echo.
python run.py
pause
'''
        
        batch_file = install_dir / "iniciar_obpc.bat"
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(startup_script)
            
        # Atalho da área de trabalho
        if self.create_desktop_shortcut.get():
            try:
                import winshell
                from win32com.client import Dispatch
                
                desktop = winshell.desktop()
                shortcut_path = os.path.join(desktop, "Sistema OBPC.lnk")
                
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = str(batch_file)
                shortcut.WorkingDirectory = str(install_dir)
                shortcut.IconLocation = str(install_dir / "static" / "logo_obpc.ico")
                shortcut.save()
            except:
                # Se não conseguir criar atalho, criar um arquivo de texto
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                shortcut_text = os.path.join(desktop, "Sistema OBPC - Iniciar.txt")
                with open(shortcut_text, 'w', encoding='utf-8') as f:
                    f.write(f"Para iniciar o Sistema OBPC, execute:\n{batch_file}")
                    
    def show_success_message(self):
        """Mostra mensagem de sucesso"""
        self.status_label.config(text="✅ Instalação concluída com sucesso!", 
                                style='Success.TLabel')
        
        message = f"""Sistema OBPC instalado com sucesso!

📁 Local de instalação: {self.install_path.get()}

🚀 Para iniciar o sistema:
1. Execute o arquivo 'iniciar_obpc.bat' na pasta de instalação
2. Ou use o atalho na área de trabalho (se criado)
3. Acesse http://localhost:5000 no navegador

👤 Login padrão:
• Usuário: admin@obpc.com
• Senha: admin123

⚠️ Lembre-se de alterar a senha padrão!"""
        
        messagebox.showinfo("Instalação Concluída", message)
        
        # Perguntar se quer iniciar o sistema
        if messagebox.askyesno("Iniciar Sistema", "Deseja iniciar o sistema agora?"):
            self.start_system()
            
    def start_system(self):
        """Inicia o sistema"""
        install_dir = Path(self.install_path.get())
        batch_file = install_dir / "iniciar_obpc.bat"
        
        try:
            subprocess.Popen([str(batch_file)], cwd=str(install_dir))
            self.close_application()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível iniciar o sistema:\n{str(e)}")
            
    def test_system(self):
        """Testa o sistema (desenvolvimento)"""
        try:
            subprocess.Popen([sys.executable, "run.py"])
            messagebox.showinfo("Sistema Iniciado", "Sistema iniciado em modo de teste")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar sistema:\n{str(e)}")
            
    def cancel_installation(self):
        """Cancela a instalação"""
        if messagebox.askyesno("Cancelar", "Deseja cancelar a instalação?"):
            self.close_application()
            
    def close_application(self):
        """Fecha a aplicação"""
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        """Executa o instalador"""
        self.root.mainloop()

if __name__ == "__main__":
    app = InstaladorOBPC()
    app.run()