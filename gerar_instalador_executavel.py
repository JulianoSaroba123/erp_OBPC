#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Instalador Executável OBPC
Cria um executável auto-extraível
"""

import os
import zipfile
import shutil
import subprocess
from pathlib import Path
import base64

def create_self_extracting_installer():
    """Cria um instalador auto-extraível"""
    
    print("🔨 Criando instalador auto-extraível...")
    
    # 1. Criar arquivo ZIP com todos os componentes
    zip_path = "OBPC_Sistema.zip"
    create_system_zip(zip_path)
    
    # 2. Converter ZIP para base64
    with open(zip_path, 'rb') as f:
        zip_data = base64.b64encode(f.read()).decode('utf-8')
    
    # 3. Criar script Python auto-extraível
    installer_script = create_installer_script(zip_data)
    
    # 4. Salvar script
    with open("InstaladorOBPC_AutoExtraivel.py", 'w', encoding='utf-8') as f:
        f.write(installer_script)
    
    # 5. Tentar criar executável
    try_create_exe()
    
    # 6. Limpar arquivos temporários
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    print("✅ Instalador criado com sucesso!")

def create_system_zip(zip_path):
    """Cria ZIP com o sistema completo"""
    
    files_to_include = [
        "app/",
        "static/", 
        "instance/",
        "run.py",
        "requirements.txt",
        "criar_admin.py",
        "verificar_banco.py",
        "instalador_rapido.py",
        "InstalarOBPC.bat"
    ]
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in files_to_include:
            item_path = Path(item)
            if item_path.exists():
                if item_path.is_file():
                    zipf.write(item_path, item_path.name)
                else:
                    for root, dirs, files in os.walk(item_path):
                        for file in files:
                            file_path = Path(root) / file
                            try:
                                arc_path = file_path.relative_to(Path.cwd())
                                zipf.write(file_path, str(arc_path))
                            except ValueError:
                                # Se não conseguir calcular relative_to, usar caminho simples
                                zipf.write(file_path, str(file_path))

def create_installer_script(zip_data_b64):
    """Cria o script instalador auto-extraível"""
    
    script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalador Auto-Extraível OBPC
Sistema de Gestão Eclesiástica
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import zipfile
import base64
import io
import os
import sys
import threading
import subprocess
import webbrowser
from pathlib import Path

# Dados do sistema (base64)
SYSTEM_DATA = """{zip_data_b64}"""

class InstaladorAutoExtraivel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Instalador OBPC v2.0")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        self.root.configure(bg='white')
        
        # Centralizar
        self.center_window()
        
        # Variáveis
        self.install_path = tk.StringVar(value="C:\\\\OBPC_Sistema")
        
        # Interface
        self.create_interface()
        
    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (250)
        y = (self.root.winfo_screenheight() // 2) - (200)
        self.root.geometry(f'500x400+{{x}}+{{y}}')
        
    def create_interface(self):
        # Header
        header_frame = tk.Frame(self.root, bg='#228b22', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="Sistema OBPC", 
                              font=('Arial', 18, 'bold'), 
                              fg='#FFD700', bg='#228b22')
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(header_frame, text="O Brasil Para Cristo - Tietê/SP", 
                                 font=('Arial', 10), 
                                 fg='white', bg='#228b22')
        subtitle_label.pack()
        
        # Content
        content_frame = tk.Frame(self.root, bg='white', padx=30, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Descrição
        desc_text = """Sistema completo de gestão eclesiástica com:
        
✅ Controle de membros e obreiros
✅ Gestão financeira completa  
✅ Relatórios profissionais
✅ Controle de eventos
✅ Interface moderna e intuitiva"""
        
        desc_label = tk.Label(content_frame, text=desc_text, 
                             font=('Arial', 10), justify=tk.LEFT,
                             bg='white', fg='#333')
        desc_label.pack(pady=(0, 15))
        
        # Pasta de instalação
        path_frame = tk.Frame(content_frame, bg='white')
        path_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(path_frame, text="Pasta de instalação:", 
                bg='white', font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        path_entry_frame = tk.Frame(path_frame, bg='white')
        path_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        path_entry = tk.Entry(path_entry_frame, textvariable=self.install_path, 
                             font=('Arial', 10), width=40)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = tk.Button(path_entry_frame, text="...", 
                              command=self.browse_folder, width=3)
        browse_btn.pack(side=tk.RIGHT)
        
        # Progresso
        self.progress_frame = tk.Frame(content_frame, bg='white')
        self.progress_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.status_label = tk.Label(self.progress_frame, text="Pronto para instalar", 
                                    bg='white', font=('Arial', 10))
        self.status_label.pack(pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Botões
        button_frame = tk.Frame(content_frame, bg='white')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.install_btn = tk.Button(button_frame, text="Instalar Sistema", 
                                    command=self.start_installation,
                                    bg='#228b22', fg='white', 
                                    font=('Arial', 12, 'bold'),
                                    width=15, height=2)
        self.install_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = tk.Button(button_frame, text="Cancelar", 
                              command=self.root.quit,
                              width=10, height=2)
        cancel_btn.pack(side=tk.RIGHT)
        
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.install_path.get())
        if folder:
            self.install_path.set(folder)
            
    def start_installation(self):
        self.install_btn.config(state='disabled')
        thread = threading.Thread(target=self.install_system)
        thread.daemon = True
        thread.start()
        
    def install_system(self):
        try:
            # Decodificar dados
            self.update_progress("Extraindo arquivos...", 20)
            zip_data = base64.b64decode(SYSTEM_DATA)
            
            # Criar diretório
            install_dir = Path(self.install_path.get())
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Extrair arquivos
            self.update_progress("Instalando sistema...", 50)
            with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zipf:
                zipf.extractall(install_dir)
            
            # Instalar dependências
            self.update_progress("Instalando dependências...", 75)
            os.chdir(install_dir)
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                          capture_output=True, timeout=60)
            
            # Configurar sistema
            self.update_progress("Configurando banco...", 90)
            subprocess.run([sys.executable, "verificar_banco.py"], 
                          capture_output=True, timeout=30)
            subprocess.run([sys.executable, "criar_admin.py"], 
                          capture_output=True, timeout=30)
            
            # Concluído
            self.update_progress("Instalação concluída!", 100)
            
            # Mostrar sucesso
            self.show_success(install_dir)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na instalação:\\n{{str(e)}}")
            self.install_btn.config(state='normal')
            
    def update_progress(self, status, progress):
        def update():
            self.status_label.config(text=status)
            self.progress_bar['value'] = progress
        self.root.after(0, update)
        
    def show_success(self, install_dir):
        def show():
            result = messagebox.askyesno("Sucesso!", 
                f"""Sistema OBPC instalado com sucesso!

📁 Local: {{install_dir}}

👤 Login padrão:
   Usuário: admin@obpc.com
   Senha: admin123

Deseja iniciar o sistema agora?""")
            
            if result:
                subprocess.Popen([sys.executable, "run.py"], cwd=install_dir)
                webbrowser.open('http://127.0.0.1:5000')
                
            self.root.quit()
            
        self.root.after(0, show)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = InstaladorAutoExtraivel()
    app.run()
'''
    return script

def try_create_exe():
    """Tenta criar executável com PyInstaller"""
    try:
        # Verificar se PyInstaller está disponível
        result = subprocess.run(["pip", "show", "pyinstaller"], 
                               capture_output=True, text=True)
        
        if result.returncode != 0:
            print("📦 Instalando PyInstaller...")
            subprocess.run(["pip", "install", "pyinstaller"], check=True)
        
        print("🔨 Criando executável...")
        
        # Criar executável
        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed", 
            "--name=InstaladorOBPC",
            "--icon=static/logo_obpc.ico" if Path("static/logo_obpc.ico").exists() else None,
            "InstaladorOBPC_AutoExtraivel.py"
        ]
        
        # Remover None da lista
        cmd = [arg for arg in cmd if arg is not None]
        
        subprocess.run(cmd, check=True)
        
        print("✅ Executável criado: dist/InstaladorOBPC.exe")
        
    except Exception as e:
        print(f"⚠️  Não foi possível criar executável: {e}")
        print("💡 Você pode usar o arquivo .py diretamente")

def main():
    print("🚀 GERADOR DE INSTALADOR AUTO-EXTRAÍVEL")
    print("=" * 45)
    
    if not Path("run.py").exists():
        print("❌ Este script deve ser executado na pasta do projeto OBPC")
        return
    
    create_self_extracting_installer()
    
    print("\\n✅ Processo concluído!")
    print("\\n📁 Arquivos gerados:")
    print("   - InstaladorOBPC_AutoExtraivel.py (script)")
    if Path("dist/InstaladorOBPC.exe").exists():
        print("   - dist/InstaladorOBPC.exe (executável)")
    
    print("\\n💡 Para distribuir, use o arquivo .exe ou .py")

if __name__ == "__main__":
    main()