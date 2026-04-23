import tkinter as tk
from tkinter import messagebox

class GameView:
    """
    Camada View responsável puramente por desenhar a interface gráfica, Canvas e HUD.
    Totalmente abstrata das regras de negócio do jogo (passiva).
    """
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        
        self.root.title("Bombardeio 1000Grau - AD2 Edição TK")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        self.root.configure(bg="#212121")
        
        # Paleta de Cores (Design Dinâmico Moderno)
        self.cores = {
            "bg": "#212121",
            "canvas_bg": "#121212",
            "texto": "#FFFFFF",
            "texto_secundario": "#B0B0B0",
            "btn_bg": "#3D5AFE",
            "btn_hover": "#536DFE",
            "obstaculo_indestrutivel": "#424242",
            "obstaculo_destrutivel": "#FF8A65",
            "jogador": "#00E5FF",      # Ciano Neon
            "inimigo": "#FF1744",      # Vermelho Neon
            "bomba": "#FFFF00",        # Amarelo
            "explosao": "#FF9100",     # Laranja Viva
        }
        
        self.font_title = ("Helvetica", 36, "bold")
        self.font_subtitle = ("Helvetica", 20)
        self.font_text = ("Helvetica", 14)
        
        # Container Root
        self.container = tk.Frame(self.root, bg=self.cores["bg"])
        self.container.pack(fill=tk.BOTH, expand=True)

        # Referências visuais
        self.canvas = None
        self.hud_texto = tk.StringVar()
        
        # Cache de animações e entidades na view (dicionários mapeando IDs logicos para IDs do Canvas)
        self.visual_ids = {} # armazena {obj_id_memoria: tag_do_canvas}

    # ==========================================
    # TELAS
    # ==========================================

    def limpar_tela(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def mostrar_menu(self, globais):
        self.limpar_tela()
        
        frame = tk.Frame(self.container, bg=self.cores["bg"])
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(frame, text="BOMBARDEIO 1000GRAU", font=self.font_title, bg=self.cores["bg"], fg=self.cores["jogador"]).pack(pady=(0, 10))
        tk.Label(frame, text="AD2 - Tkinter Edition", font=self.font_subtitle, bg=self.cores["bg"], fg=self.cores["texto_secundario"]).pack(pady=(0, 40))
        
        # Botões
        btn_jogar = self._criar_botao(frame, "Iniciar Nova Partida", command=self.controller.iniciar_jogo)
        btn_jogar.pack(pady=10, fill=tk.X)
        
        btn_sair = self._criar_botao(frame, "Encerrar", command=self.root.quit, bg_color="#D50000", hover_color="#FF1744")
        btn_sair.pack(pady=10, fill=tk.X)
        
        # Estatísticas (Persistência)
        stats_text = (
            f"Partidas Jogadas: {globais.get('partidas_jogadas', 0)}\n"
            f"Média Turnos Sobrevividos: {globais.get('media_turnos', 0.0)}\n"
            f"Taxa Média de Desmatamento (Global): {globais.get('taxa_destruicao_media', 0.0)}%"
        )
        tk.Label(frame, text=stats_text, font=self.font_text, bg=self.cores["bg"], fg=self.cores["texto"], justify=tk.CENTER).pack(pady=(40, 0))

    def mostrar_jogo(self):
        self.limpar_tela()
        
        # Topo: HUD Superior
        hud_frame = tk.Frame(self.container, bg="#111111", height=60)
        hud_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.hud_texto.set("Inicializando os sistemas de partida...")
        tk.Label(hud_frame, textvariable=self.hud_texto, font=self.font_text, bg="#111111", fg=self.cores["texto"]).pack(side=tk.LEFT, padx=20, pady=15)
        
        # Info comandos
        tk.Label(hud_frame, text="Controles - W/A/S/D: Mover | B: Plantar Bomba | Q: Abandonar Incursão", font=("Helvetica", 10), bg="#111111", fg=self.cores["texto_secundario"]).pack(side=tk.RIGHT, padx=20, pady=20)
        
        # Centro: Área do Canvas (Grid do Jogo)
        self.canvas_frame = tk.Frame(self.container, bg=self.cores["canvas_bg"])
        self.canvas_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.cores["canvas_bg"], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind Evento de Redimensionamento (Requisito AD2)
        self.canvas.bind("<Configure>", self._redimensionar_canvas)
        
        # Faz a janela central (canvas base) pegar foco para captura rápida de keybindings definidos no controller
        self.canvas.focus_set()

    # ==========================================
    # RENDERIZAÇÃO E GAME LOOP VISUAL
    # ==========================================

    def atualizar_hud(self, turno_atual, turnos_limite, total_inimigos, status="EM EXECUÇÃO"):
        text = f"Turno: {turno_atual}/{turnos_limite}  |  Inimigos: {total_inimigos}  |  Status: {status}"
        self.hud_texto.set(text)

    def desenhar_mapa(self, mapa):
        """
        Recebe o modelo de Mapa (que agora possui .linhas e .colunas publicos via properties) 
        e plota de forma passiva no Canvas, limpando o anterior ou movendo elementos se desejar.
        Como testaremos animação, vamos primeiro limpar tudo para desenhar terreno e atualizar tags móveis.
        """
        if not self.canvas:
            return

        # Pega dimensões atuais do Canvas validáveis
        self.canvas_w = self.canvas.winfo_width()
        self.canvas_h = self.canvas.winfo_height()
        
        # Evita erro de divisão antes do pack total
        if self.canvas_w <= 1 or self.canvas_h <= 1:
            return 
            
        self.cell_w = self.canvas_w / mapa.colunas
        self.cell_h = self.canvas_h / mapa.linhas
        
        self.canvas.delete("all")
        
        # Desenhar Grade (Terreno) e Objetos
        for l in range(mapa.linhas):
            for c in range(mapa.colunas):
                # Desenhar Célula Chao Opcional (Linhas Finas)
                x1 = c * self.cell_w
                y1 = l * self.cell_h
                x2 = x1 + self.cell_w
                y2 = y1 + self.cell_h
                
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="#1E1E1E", fill="", tags="chao")
                
                # Ler conteúdo
                conteudo = mapa.celulas[l][c]
                
                # Para evitar conflito cirurgico com importacoes do model na view (Loose Coupling), 
                # deduzimos pelo nome da class se possivel ou atributos:
                if conteudo is not None:
                    nome_classe = conteudo.__class__.__name__
                    
                    if nome_classe == "Obstaculo":
                        if conteudo.tipo == "indestrutivel":
                            self.canvas.create_rectangle(x1+2, y1+2, x2-2, y2-2, fill=self.cores["obstaculo_indestrutivel"], outline="", tags=f"obs_{l}_{c}")
                        else:
                            self.canvas.create_rectangle(x1+4, y1+4, x2-4, y2-4, fill=self.cores["obstaculo_destrutivel"], outline="", tags=f"obs_{l}_{c}")
                    
                    elif nome_classe == "Inimigo":
                         # Redondo
                         self.canvas.create_oval(x1+8, y1+8, x2-8, y2-8, fill=self.cores["inimigo"], outline="", tags="inimigo")
                         
                    elif nome_classe == "Jogador":
                         # Redondo neon diferente
                         self.canvas.create_oval(x1+6, y1+6, x2-6, y2-6, fill=self.cores["jogador"], outline="#FFFFFF", width=2, tags="jogador")
                         
        # Desenhar as bombas pelo array de bombas, já que elas ficam sob o chao independentemente do map content
        for bomba in mapa.bombas:
            x1 = bomba.y * self.cell_w
            y1 = bomba.x * self.cell_h
            x2 = x1 + self.cell_w
            y2 = y1 + self.cell_h
            self.canvas.create_oval(x1+12, y1+12, x2-12, y2-12, fill=self.cores["bomba"], outline="#FF3D00", width=3, tags="bomba")
            
            # TicTac Visual (Texto)
            self.canvas.create_text(x1 + (self.cell_w/2), y1 + (self.cell_h/2), text=str(bomba.tempo), fill="#000", font=("Helvetica", 10, "bold"), tags="bomba")

    # ==========================================
    # ANIMAÇÕES GERAIS (Efeitos) E HELPERS
    # ==========================================

    def calcular_trilhas_fogo(self, bombas_list, mapa):
        """
        Dada uma lista de bombas a explodir e o mapa ANTES da destruição visual,
        calcula as coordenadas que sofrerão o efeito da explosão para demarcar.
        """
        trilhas = []
        for bx, by, alcance in bombas_list:
            trilhas.append((bx, by)) # Centro
            
            direcoes = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dx, dy in direcoes:
                for dist in range(1, alcance + 1):
                    nx, ny = bx + (dx * dist), by + (dy * dist)
                    if 0 <= nx < mapa.linhas and 0 <= ny < mapa.colunas:
                        conteudo = mapa.celulas[nx][ny]
                        nome_classe = conteudo.__class__.__name__ if conteudo else ""
                        
                        if nome_classe == "Obstaculo":
                            if conteudo.tipo == "indestrutivel":
                                # Fogo não invade espaços indestrutíveis, para de vez antes de desenhar
                                break
                            else:
                                # Fogo invade o bloco destrutível (para mostrar que o destruiu), e então para
                                trilhas.append((nx, ny))
                                break
                        else:
                            # Espaço vazio, jogador ou inimigo sofrem dano normalmente
                            trilhas.append((nx, ny))
                    else:
                        break # fora do mapa
        return trilhas

    def desenhar_fogo(self, trilhas):
        """Desenha a animação de fogo vetorial nas células da trilha."""
        for l, c in trilhas:
            x1 = c * self.cell_w
            y1 = l * self.cell_h
            x2 = x1 + self.cell_w
            y2 = y1 + self.cell_h
            
            # Retângulo amarelo com borda vermelha conforme combinado
            self.canvas.create_rectangle(
                x1 + 2, y1 + 2, x2 - 2, y2 - 2, 
                fill="#FFFF00", outline="#FF0000", width=4, tags="fogo"
            )
            
        # Agendar uma chamada Tkinter para apagar as labaredas sozinhas
        # Dando aquele efeito de lampejo animado!
        self.root.after(450, lambda: self.canvas.delete("fogo"))

    def _redimensionar_canvas(self, event):
        """Disparado toda vez que a janela muda de tamanho. Pede pro controller atualizar o draw se jogando."""
        if self.canvas and self.controller.mapa_atual:
            self.desenhar_mapa(self.controller.mapa_atual)

    def _criar_botao(self, parent, texto, command, bg_color="#3D5AFE", hover_color="#536DFE"):
        btn = tk.Button(parent, text=texto, font=self.font_text, bg=bg_color, fg="#FFF", 
                        activebackground=hover_color, activeforeground="#FFF", 
                        relief=tk.FLAT, borderwidth=0, padx=20, pady=10, cursor="hand2", command=command)
        
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_color))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_color))
        return btn

    def mostrar_mensagem_gui(self, titulo, mensagem, tipo="info"):
        if tipo == "info":
            messagebox.showinfo(titulo, mensagem)
        elif tipo == "error":
            messagebox.showerror(titulo, mensagem)
        elif tipo == "warning":
            messagebox.showwarning(titulo, mensagem)

    def exibir_game_over(self, texto, subtitulo, eh_vitoria=False):
        """Sobrepõe o canvas com tela gráfica de Fim de Jogo."""
        cor = "#00E676" if eh_vitoria else "#FF1744"
        bg_transp = self.cores["bg"]
        
        overlay = tk.Frame(self.canvas_frame, bg=bg_transp)
        overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(overlay, text=texto, font=("Helvetica", 40, "bold"), bg=bg_transp, fg=cor).pack(pady=10)
        tk.Label(overlay, text=subtitulo, font=self.font_subtitle, bg=bg_transp, fg="#FFF").pack(pady=10)
        
        self._criar_botao(overlay, "Voltar ao Menu", command=self.controller.finalizar_volta_menu).pack(pady=20)
