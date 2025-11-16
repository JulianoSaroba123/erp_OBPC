#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tela de Carregamento Profissional - Sistema OBPC
Interface gráfica moderna com animações e feedback visual
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import os

class TelaCarregamento(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Configurações da janela
        self.title('Sistema OBPC - Iniciando...')
        self.geometry('480x300')
        self.configure(bg='#1a237e')  # Azul escuro profissional
        self.resizable(False, False)
        
        # Centralizar na tela
        self.center_window()
        
        # Remover barra de título (opcional)
        self.overrideredirect(False)
        
        # Variáveis de controle
        self.progress_value = 0
        self.loading_steps = [
            "Inicializando sistema...",
            "Verificando dependências...",
            "Carregando módulos...",
            "Configurando banco de dados...",
            "Preparando interface web...",
            "Iniciando servidor Flask...",
            "Finalizando configurações...",
            "Sistema pronto!"
        ]
        self.current_step = 0
        
        self.create_widgets()
        self.start_loading_animation()
        
    def center_window(self):
        """Centraliza a janela na tela"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (480 // 2)
        y = (self.winfo_screenheight() // 2) - (300 // 2)
        self.geometry(f'480x300+{x}+{y}')
        
    def create_widgets(self):
        """Cria os componentes visuais da tela"""
        
        # Frame principal
        main_frame = tk.Frame(self, bg='#1a237e')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Logo/Ícone do sistema
        logo_frame = tk.Frame(main_frame, bg='#1a237e')
        logo_frame.pack(pady=(0, 20))
        
        # Ícone principal (pode ser substituído por imagem)
        self.logo_icon = tk.Label(
            logo_frame, 
            text='⛪', 
            font=('Arial', 48), 
            bg='#1a237e', 
            fg='#ffffff'
        )
        self.logo_icon.pack()
        
        # Título do sistema
        title_label = tk.Label(
            main_frame,
            text='SISTEMA OBPC',
            font=('Arial', 24, 'bold'),
            bg='#1a237e',
            fg='#ffffff'
        )
        title_label.pack(pady=(0, 5))
        
        # Subtítulo
        subtitle_label = tk.Label(
            main_frame,
            text='O Brasil Para Cristo - Tietê/SP',
            font=('Arial', 12),
            bg='#1a237e',
            fg='#bbbbbb'
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Status de carregamento
        self.status_label = tk.Label(
            main_frame,
            text='Iniciando sistema...',
            font=('Arial', 11),
            bg='#1a237e',
            fg='#ffeb3b'
        )
        self.status_label.pack(pady=(0, 15))
        
        # Barra de progresso moderna
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#303f9f',
            background='#4caf50',
            lightcolor='#4caf50',
            darkcolor='#4caf50',
            borderwidth=0,
            focuscolor='none'
        )
        
        self.progress_bar = ttk.Progressbar(
            main_frame,
            style="Custom.Horizontal.TProgressbar",
            length=380,
            mode='determinate',
            maximum=100
        )
        self.progress_bar.pack(pady=(0, 10))
        
        # Percentual
        self.percent_label = tk.Label(
            main_frame,
            text='0%',
            font=('Arial', 10),
            bg='#1a237e',
            fg='#ffffff'
        )
        self.percent_label.pack()
        
        # Versão do sistema
        version_label = tk.Label(
            main_frame,
            text='Versão 2025.1 - Sistema Administrativo',
            font=('Arial', 8),
            bg='#1a237e',
            fg='#666666'
        )
        version_label.pack(side='bottom', pady=(20, 0))
        
    def start_loading_animation(self):
        """Inicia a animação de carregamento"""
        self.animate_logo()
        self.update_progress()
        
    def animate_logo(self):
        """Anima o ícone do logo"""
        icons = ['⛪', '🏛️', '⛪']
        current_icon = icons[int(time.time()) % len(icons)]
        self.logo_icon.config(text=current_icon)
        self.after(1000, self.animate_logo)
        
    def update_progress(self):
        """Atualiza a barra de progresso e status"""
        if self.progress_value < 100:
            # Incremento variável para parecer mais natural
            increment = 2 if self.progress_value < 70 else 1
            self.progress_value += increment
            
            # Atualizar barra de progresso
            self.progress_bar['value'] = self.progress_value
            self.percent_label.config(text=f'{self.progress_value}%')
            
            # Atualizar status baseado no progresso
            step_size = 100 / len(self.loading_steps)
            step_index = min(int(self.progress_value / step_size), len(self.loading_steps) - 1)
            
            if step_index != self.current_step:
                self.current_step = step_index
                self.status_label.config(text=self.loading_steps[step_index])
            
            # Tempo variável entre atualizações
            delay = 150 if self.progress_value < 30 else 100 if self.progress_value < 80 else 200
            self.after(delay, self.update_progress)
        else:
            # Carregamento concluído
            self.status_label.config(text='Sistema carregado com sucesso!')
            self.percent_label.config(text='100%')
            self.after(1500, self.fade_out)
            
    def fade_out(self):
        """Efeito de fade out antes de fechar"""
        self.attributes('-alpha', 0.8)
        self.after(100, lambda: self.attributes('-alpha', 0.6))
        self.after(200, lambda: self.attributes('-alpha', 0.4))
        self.after(300, lambda: self.attributes('-alpha', 0.2))
        self.after(400, self.destroy)

def mostrar_tela_carregamento():
    """Função para mostrar a tela de carregamento em thread separada"""
    def executar_tela():
        try:
            tela = TelaCarregamento()
            tela.mainloop()
        except Exception as e:
            print(f"Erro na tela de carregamento: {e}")
    
    thread = threading.Thread(target=executar_tela, daemon=True)
    thread.start()
    time.sleep(0.5)  # Aguardar tela aparecer
    return thread

# Teste da tela de carregamento
if __name__ == '__main__':
    tela = TelaCarregamento()
    tela.mainloop()
