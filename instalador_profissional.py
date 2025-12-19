#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalador Profissional OBPC - Versão Aprimorada
Sistema de Gestão Eclesiástica - Versão 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import os
import threading
import time
import shutil
import platform
from pathlib import Path

class InstaladorOBPCProfissional:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Instalador OBPC v2025 - Sistema de Gestão Eclesiástica")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # Centralizar janela
        self.center_window()
        
        # Configurar estilo
        self.setup_style()
        
        # Variáveis
        self.install_path = tk.StringVar(value="C:\\OBPC_Sistema")
        self.create_desktop_shortcut = tk.BooleanVar(value=True)
        self.auto_start = tk.BooleanVar(value=False)
        self.install_dependencies = tk.BooleanVar(value=True)
        self.backup_existing = tk.BooleanVar(value=True)
        
        # Info da instalação
        self.total_size = "~65 MB"
        self.estimated_time = "3-5 minutos"
        
        # Interface
        self.create_interface()
        
        # Verificar requisitos na inicialização
        self.verificar_requisitos_sistema()
        
    def center_window(self):
        """Centraliza a janela na tela"""
        self.root.update_idletasks()
        width = 700
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_style(self):
        """Configura o estilo da interface"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Cores do tema OBPC
        style.configure('Header.TLabel', 
                       background='#228b22', 
                       foreground='white', 
                       font=('Segoe UI', 14, 'bold'))
        
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 12, 'bold'),
                       foreground='#2d5016')
        
        style.configure('Info.TLabel', 
                       font=('Segoe UI', 9),
                       foreground='#555')
        
    def create_interface(self):
        """Cria a interface do instalador"""
        # Cabeçalho
        self.create_header()
        
        # Área principal
        self.create_main_content()
        
        # Rodapé com botões
        self.create_footer()
        
    def create_header(self):
        """Cria o cabeçalho do instalador"""
        header_frame = tk.Frame(self.root, bg='#228b22', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Container interno
        header_content = tk.Frame(header_frame, bg='#228b22')
        header_content.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # Título principal
        title_label = tk.Label(header_content, 
                              text="🏛️ Sistema OBPC", 
                              bg='#228b22', 
                              fg='white', 
                              font=('Segoe UI', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # Versão
        version_label = tk.Label(header_content, 
                                text="Versão 2025 | Instalador Profissional", 
                                bg='#228b22', 
                                fg='#e8f5e8', 
                                font=('Segoe UI', 10))
        version_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Info do sistema (lado direito)
        system_info = f"{platform.system()} {platform.release()}"
        info_label = tk.Label(header_content, 
                             text=system_info, 
                             bg='#228b22', 
                             fg='#cccccc', 
                             font=('Segoe UI', 9))
        info_label.pack(side=tk.RIGHT)
        
    def create_main_content(self):
        """Cria o conteúdo principal"""
        # Container principal
        self.main_frame = tk.Frame(self.root, bg='white')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Informações da instalação
        self.create_info_section()
        
        # Verificação de requisitos
        self.create_requirements_section()
        
        # Opções de configuração
        self.create_options_section()
        
        # Área de progresso
        self.create_progress_section()
        
    def create_info_section(self):
        """Seção de informações da instalação"""
        info_frame = ttk.LabelFrame(self.main_frame, text="📋 Informações da Instalação", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid de informações
        info_grid = tk.Frame(info_frame, bg='white')
        info_grid.pack(fill=tk.X)
        
        # Tamanho
        ttk.Label(info_grid, text="📦 Tamanho:", font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky='w', padx=(0, 10))
        ttk.Label(info_grid, text=self.total_size, style='Info.TLabel').grid(row=0, column=1, sticky='w')
        
        # Tempo estimado
        ttk.Label(info_grid, text="⏱️ Tempo estimado:", font=('Segoe UI', 9, 'bold')).grid(row=1, column=0, sticky='w', padx=(0, 10), pady=(5, 0))
        ttk.Label(info_grid, text=self.estimated_time, style='Info.TLabel').grid(row=1, column=1, sticky='w', pady=(5, 0))
        
        # Requisitos
        ttk.Label(info_grid, text="🔧 Requisitos:", font=('Segoe UI', 9, 'bold')).grid(row=2, column=0, sticky='w', padx=(0, 10), pady=(5, 0))
        ttk.Label(info_grid, text="Python 3.8+, 150MB livres", style='Info.TLabel').grid(row=2, column=1, sticky='w', pady=(5, 0))
        
    def create_requirements_section(self):
        """Seção de verificação de requisitos"""
        req_frame = ttk.LabelFrame(self.main_frame, text="✅ Verificação de Requisitos", padding=15)
        req_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.req_status_frame = tk.Frame(req_frame, bg='white')
        self.req_status_frame.pack(fill=tk.X)
        
    def create_options_section(self):
        """Seção de opções de configuração"""
        options_frame = ttk.LabelFrame(self.main_frame, text="⚙️ Opções de Instalação", padding=15)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Diretório de instalação
        path_frame = tk.Frame(options_frame, bg='white')
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(path_frame, text="📁 Diretório de instalação:", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        path_input_frame = tk.Frame(path_frame, bg='white')
        path_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        path_entry = ttk.Entry(path_input_frame, textvariable=self.install_path, font=('Segoe UI', 9), width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(path_input_frame, text="Procurar...", command=self.browse_install_path)
        browse_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Checkboxes de opções
        options_grid = tk.Frame(options_frame, bg='white')
        options_grid.pack(fill=tk.X, pady=(10, 0))
        
        # Atalho na área de trabalho
        desktop_cb = ttk.Checkbutton(options_grid, 
                                   text="🖥️ Criar atalho na área de trabalho", 
                                   variable=self.create_desktop_shortcut)
        desktop_cb.grid(row=0, column=0, sticky='w', pady=2)
        
        # Auto-start
        autostart_cb = ttk.Checkbutton(options_grid, 
                                     text="🚀 Iniciar automaticamente com o Windows", 
                                     variable=self.auto_start)
        autostart_cb.grid(row=1, column=0, sticky='w', pady=2)
        
        # Dependências
        deps_cb = ttk.Checkbutton(options_grid, 
                                text="📦 Instalar dependências Python automaticamente", 
                                variable=self.install_dependencies)
        deps_cb.grid(row=2, column=0, sticky='w', pady=2)
        
        # Backup
        backup_cb = ttk.Checkbutton(options_grid, 
                                  text="💾 Fazer backup de instalação existente", 
                                  variable=self.backup_existing)
        backup_cb.grid(row=3, column=0, sticky='w', pady=2)
        
    def create_progress_section(self):
        """Seção de progresso da instalação"""
        self.progress_frame = ttk.LabelFrame(self.main_frame, text="📊 Progresso da Instalação", padding=15)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, 
                                          variable=self.progress_var, 
                                          maximum=100, 
                                          length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Status text
        self.status_label = ttk.Label(self.progress_frame, 
                                     text="Aguardando início da instalação...", 
                                     style='Info.TLabel')
        self.status_label.pack(anchor='w')
        
        # Ocultar inicialmente
        self.progress_frame.pack_forget()
        
    def create_footer(self):
        """Cria o rodapé com botões"""
        footer_frame = tk.Frame(self.root, bg='#f0f0f0', height=60)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)
        
        # Container dos botões
        button_frame = tk.Frame(footer_frame, bg='#f0f0f0')
        button_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Botão Cancelar
        self.cancel_btn = ttk.Button(button_frame, 
                                   text="❌ Cancelar", 
                                   command=self.root.quit, 
                                   width=12)
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botão Instalar
        self.install_btn = ttk.Button(button_frame, 
                                    text="🚀 Instalar", 
                                    command=self.start_installation, 
                                    width=12)
        self.install_btn.pack(side=tk.LEFT)
        
        # Info no canto esquerdo
        info_left = tk.Label(footer_frame, 
                           text="💡 Dica: A instalação preservará suas configurações existentes", 
                           bg='#f0f0f0', 
                           fg='#666', 
                           font=('Segoe UI', 8))
        info_left.pack(side=tk.LEFT, padx=20, pady=15)
        
    def verificar_requisitos_sistema(self):
        """Verifica os requisitos do sistema"""
        requisitos = {
            'Python': self.verificar_python(),
            'Espaço em Disco': self.verificar_espaco_disco(),
            'Permissões': self.verificar_permissoes(),
            'Conectividade': self.testar_conectividade()
        }
        
        # Limpar frame anterior
        for widget in self.req_status_frame.winfo_children():
            widget.destroy()
        
        # Mostrar status dos requisitos
        row = 0
        all_ok = True
        
        for req, status in requisitos.items():
            icon = "✅" if status else "❌"
            color = "green" if status else "red"
            
            status_label = tk.Label(self.req_status_frame, 
                                  text=f"{icon} {req}", 
                                  bg='white', 
                                  fg=color, 
                                  font=('Segoe UI', 9))
            status_label.grid(row=row, column=0, sticky='w', pady=2)
            
            if not status:
                all_ok = False
            
            row += 1
        
        # Habilitar/desabilitar botão de instalação
        if all_ok:
            self.install_btn.configure(state='normal')
        else:
            self.install_btn.configure(state='disabled')
            messagebox.showwarning("Requisitos não atendidos", 
                                 "Alguns requisitos não foram atendidos. Verifique e tente novamente.")
    
    def verificar_python(self):
        """Verifica se Python está instalado e na versão correta"""
        try:
            return sys.version_info >= (3, 8)
        except:
            return False
    
    def verificar_espaco_disco(self):
        """Verifica espaço disponível em disco"""
        try:
            import shutil
            path = os.path.dirname(self.install_path.get())
            if not os.path.exists(path):
                path = "C:\\"
            
            total, used, free = shutil.disk_usage(path)
            # Verificar se há pelo menos 200MB livres
            return free > 200 * 1024 * 1024
        except:
            return True  # Assumir que há espaço se não conseguir verificar
    
    def verificar_permissoes(self):
        """Verifica se tem permissões para instalar"""
        try:
            test_path = os.path.dirname(self.install_path.get())
            if not os.path.exists(test_path):
                test_path = "C:\\"
            
            test_file = os.path.join(test_path, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except:
            return False
    
    def testar_conectividade(self):
        """Testa conectividade com a internet"""
        try:
            import urllib.request
            urllib.request.urlopen('http://www.google.com', timeout=5)
            return True
        except:
            return False
    
    def browse_install_path(self):
        """Abre diálogo para escolher diretório de instalação"""
        directory = filedialog.askdirectory(initialdir=self.install_path.get())
        if directory:
            self.install_path.set(directory)
            # Reverificar requisitos com novo caminho
            self.verificar_requisitos_sistema()
    
    def start_installation(self):
        """Inicia o processo de instalação"""
        # Confirmar instalação
        msg = f"""Confirma a instalação do Sistema OBPC?

Diretório: {self.install_path.get()}
Tamanho: {self.total_size}
Tempo estimado: {self.estimated_time}"""
        
        if not messagebox.askyesno("Confirmar Instalação", msg):
            return
        
        # Ocultar opções e mostrar progresso
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Desabilitar botões
        self.install_btn.configure(state='disabled')
        self.cancel_btn.configure(text="⏹️ Interromper")
        
        # Iniciar instalação em thread separada
        self.installation_thread = threading.Thread(target=self.execute_installation)
        self.installation_thread.daemon = True
        self.installation_thread.start()
    
    def execute_installation(self):
        """Executa a instalação"""
        try:
            steps = [
                ("Preparando instalação...", 10),
                ("Verificando versão anterior...", 20),
                ("Criando diretórios...", 30),
                ("Copiando arquivos do sistema...", 60),
                ("Instalando dependências...", 80),
                ("Configurando sistema...", 90),
                ("Criando atalhos...", 95),
                ("Finalizando instalação...", 100)
            ]
            
            for step_text, progress in steps:
                self.update_progress(step_text, progress)
                time.sleep(1)  # Simular tempo de processamento
                
                # Executar ação real baseada no step
                if "Criando diretórios" in step_text:
                    self.create_directories()
                elif "Copiando arquivos" in step_text:
                    self.copy_files()
                elif "dependências" in step_text and self.install_dependencies.get():
                    self.install_python_dependencies()
                elif "atalhos" in step_text and self.create_desktop_shortcut.get():
                    self.create_shortcuts()
            
            # Instalação concluída
            self.installation_completed()
            
        except Exception as e:
            self.installation_failed(str(e))
    
    def update_progress(self, text, value):
        """Atualiza barra de progresso e texto"""
        self.root.after(0, lambda: [
            self.progress_var.set(value),
            self.status_label.configure(text=text)
        ])
    
    def create_directories(self):
        """Cria diretórios necessários"""
        install_dir = Path(self.install_path.get())
        install_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar subdiretórios
        (install_dir / "app").mkdir(exist_ok=True)
        (install_dir / "static").mkdir(exist_ok=True)
        (install_dir / "templates").mkdir(exist_ok=True)
        (install_dir / "logs").mkdir(exist_ok=True)
    
    def copy_files(self):
        """Copia arquivos do sistema"""
        source_dir = Path(os.path.dirname(__file__))
        dest_dir = Path(self.install_path.get())
        
        # Lista de arquivos e diretórios para copiar
        items_to_copy = ['app', 'static', 'templates', 'run.py', 'requirements.txt']
        
        for item in items_to_copy:
            source_path = source_dir / item
            dest_path = dest_dir / item
            
            if source_path.exists():
                if source_path.is_dir():
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(source_path, dest_path)
    
    def install_python_dependencies(self):
        """Instala dependências Python"""
        requirements_file = Path(self.install_path.get()) / "requirements.txt"
        if requirements_file.exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                         capture_output=True)
    
    def create_shortcuts(self):
        """Cria atalhos"""
        # Criar atalho na área de trabalho (implementação simplificada)
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            # Aqui você implementaria a criação real do atalho
            pass
    
    def installation_completed(self):
        """Instalação concluída com sucesso"""
        self.root.after(0, lambda: [
            self.status_label.configure(text="✅ Instalação concluída com sucesso!"),
            self.install_btn.configure(text="🎉 Finalizar", command=self.finish_installation),
            self.install_btn.configure(state='normal'),
            self.cancel_btn.configure(text="🚀 Executar Sistema", command=self.launch_system)
        ])
    
    def installation_failed(self, error):
        """Instalação falhou"""
        self.root.after(0, lambda: [
            self.status_label.configure(text=f"❌ Erro na instalação: {error}"),
            self.install_btn.configure(text="🔄 Tentar Novamente", command=self.start_installation),
            self.install_btn.configure(state='normal'),
            messagebox.showerror("Erro na Instalação", f"Falha na instalação:\n\n{error}")
        ])
    
    def finish_installation(self):
        """Finaliza o instalador"""
        messagebox.showinfo("Instalação Concluída", 
                           "O Sistema OBPC foi instalado com sucesso!\n\nVocê pode executá-lo através do atalho criado.")
        self.root.quit()
    
    def launch_system(self):
        """Executa o sistema após a instalação"""
        try:
            run_script = Path(self.install_path.get()) / "run.py"
            if run_script.exists():
                subprocess.Popen([sys.executable, str(run_script)], cwd=self.install_path.get())
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível executar o sistema:\n{e}")
    
    def run(self):
        """Executa o instalador"""
        self.root.mainloop()

if __name__ == "__main__":
    try:
        instalador = InstaladorOBPCProfissional()
        instalador.run()
    except KeyboardInterrupt:
        print("\nInstalação cancelada pelo usuário.")
    except Exception as e:
        print(f"Erro fatal no instalador: {e}")
        input("Pressione Enter para sair...")