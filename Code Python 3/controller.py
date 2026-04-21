import tkinter as tk
from tkinter import simpledialog
from classes import Mapa, Jogador
from persistencia import GerenciadorEstado

class GameController:
    """
    Camada Controller responsável por gerenciar a View via chamadas, instanciar a lógica da AD1 (Models)
    e efetuar a transição do Loop 'While' para Binds Dirigidos a Eventos do Tkinter.
    """
    def __init__(self, root, view_class):
        self.root = root
        
        # Referência viva pro Modelo
        self.mapa_atual = None
        self.jogador_atual = None
        
        # Injeção de dependência pra View
        self.view = view_class(root, self)
        
        # Init de Estados Globais de AD1
        GerenciadorEstado.inicializar_arquivos()
        
        # Carrega Menu Principal
        self.voltar_menu_principal()

    def voltar_menu_principal(self):
        # Lê persistência pro menu
        globais = GerenciadorEstado.ler_global()
        self.view.mostrar_menu(globais)
        
        # Remove binds de grid de jogo, evita memory leak se menu for chamado várias vezes
        self.root.unbind("<w>")
        self.root.unbind("<a>")
        self.root.unbind("<s>")
        self.root.unbind("<d>")
        self.root.unbind("<b>")
        self.root.unbind("<q>")

    def iniciar_jogo(self):
        # 1. Obter Escolhas do Jogador (Substituindo input() de terminal)
        nome = simpledialog.askstring("Novo Jogo", "Digite o nome do jogador:", parent=self.root)
        if not nome: 
            nome = "Heroi"

        # Substituindo console inputs: 1=Pequeno(8x7), 2=Medio(12x11), 3=Grande(16x14)
        tamanho = simpledialog.askinteger("Tamanho do Mapa", "Escolha o tamanho (1-Pequeno, 2-Médio, 3-Grande):", minvalue=1, maxvalue=3, initialvalue=2, parent=self.root)
        
        if tamanho == 1:
            l, c = 8, 7
            fator_area = 0.5
        elif tamanho == 3:
            l, c = 16, 14
            fator_area = 1.5
        else:
            l, c = 12, 11
            fator_area = 1.0

        # Regras Clássicas (Modelo de AD1)
        configs_globais = GerenciadorEstado.ler_global()
        media_turnos = configs_globais.get("media_turnos", 0)
        qtd_inimigos_base = int(((media_turnos // 20) + 3) * fator_area)
        qtd_inimigos_base = max(1, qtd_inimigos_base)
        
        densidade_obs = configs_globais.get("densidade_obstaculos", 0.48)

        # 2. Instanciar Modelos
        self.mapa_atual = Mapa(linhas=l, colunas=c, config_dificuldade={
            "inimigos_iniciais": qtd_inimigos_base,
            "densidade_obstaculos": densidade_obs
        })
        
        self.jogador_atual = Jogador(nome)
        self.mapa_atual.adicionar_jogador(self.jogador_atual)
        
        # 3. Mudar View
        self.view.mostrar_jogo()
        
        # Atualiza a primeira call de layout com um mini delay pra render engine do Tk estabilizar
        self.root.after(50, self._renderizar_rodada_atual)
        
        # 4. Bind Controller de Teclas (Substitui get_key() do while)
        self.root.bind("<w>", lambda e: self.processar_comando("w"))
        self.root.bind("<a>", lambda e: self.processar_comando("a"))
        self.root.bind("<s>", lambda e: self.processar_comando("s"))
        self.root.bind("<d>", lambda e: self.processar_comando("d"))
        self.root.bind("<b>", lambda e: self.processar_comando("b"))
        self.root.bind("<q>", lambda e: self.processar_comando("q"))
        
        # Para compatibilidade também com maiúsculas
        self.root.bind("<W>", lambda e: self.processar_comando("w"))
        self.root.bind("<A>", lambda e: self.processar_comando("a"))
        self.root.bind("<S>", lambda e: self.processar_comando("s"))
        self.root.bind("<D>", lambda e: self.processar_comando("d"))
        self.root.bind("<B>", lambda e: self.processar_comando("b"))
        self.root.bind("<Q>", lambda e: self.processar_comando("q"))

    def _renderizar_rodada_atual(self, msg_alerta=None, trilhas_fogo=None):
        if not self.mapa_atual: return
        
        # Resgata estado
        sessao = GerenciadorEstado.ler_sessao()
        cfgs = GerenciadorEstado.ler_global()
        
        turno_atual = sessao.get('turno_atual', 0)
        limit = cfgs.get('limite_max_turnos', 100)
        qnt_inimigos = len(self.mapa_atual.inimigos)
        
        # Manda HUD Atualizar
        self.view.atualizar_hud(turno_atual, limit, qnt_inimigos)
        
        # Redesenha a Grid
        self.view.desenhar_mapa(self.mapa_atual)
        
        # Se existem trilhas de bombásticas a desenhar, desenha por cima chamando o efx
        if trilhas_fogo:
            self.view.desenhar_fogo(trilhas_fogo)
        
        # Se tem msg vinda das regras de negocio, lança
        if msg_alerta:
            # Usando barra de título temporária ou messagebox pra n bloquear jogo fluido
            self.view.hud_texto.set(f"{self.view.hud_texto.get()} | MSG: {msg_alerta}")

    def processar_comando(self, comando):
        # Semelhante ao Core Logic do While
        direcao = None
        plantou_bomba = False
        passa_turno = False
        mensagem = None
        
        if comando == "q":
            GerenciadorEstado.registrar_fim_partida_atualizacao_global("quit", self.mapa_atual)
            self.root.unbind("<w>")
            self.root.unbind("<a>") # Trava input pós jogo
            self.view.mostrar_mensagem_gui("Abandono", "Você abandonou o mapa.")
            self.finalizar_volta_menu()
            return
            
        elif comando == "w": direcao = "cima"
        elif comando == "s": direcao = "baixo"
        elif comando == "a": direcao = "esquerda"
        elif comando == "d": direcao = "direita"
        elif comando == "b": plantou_bomba = True
        
        if plantou_bomba:
            cfgs = GerenciadorEstado.ler_global()
            t_bomba = cfgs.get("tempo_detonacao_bomba", 3)
            a_bomba = cfgs.get("alcance_bomba", 2)
            
            sucesso = self.jogador_atual.plantar_bomba(self.mapa_atual, t_bomba, a_bomba)
            if sucesso:
                mensagem = "Bomba armada!"
            else:
                mensagem = "Falhou em armar bomba!"
            passa_turno = False # Regra: plantar não gasta turno
            self._renderizar_rodada_atual(mensagem) # Renderiza bomba instalada
            return 
            
        elif direcao:
            sucesso_movimento = self.jogador_atual.movimentar(self.mapa_atual, direcao)
            passa_turno = sucesso_movimento
            if not sucesso_movimento and not passa_turno:
                mensagem = "Bloqueado."
                self._renderizar_rodada_atual(mensagem)
                return
                
        if passa_turno:
            self._executar_passagem_turno()

    def _executar_passagem_turno(self):
        """Metodo de update global chamado quando um turno é consumido"""
        # Incrementa Turno
        GerenciadorEstado.incrementar_sessao("turno_atual", 1)
        
        # 0. MAPEAR FÍSICA VISUAL (Fogo)
        # Precisa acontecer ANTES do mapa processar a bomba e destruir objetos
        bombas_a_explodir = [(b.x, b.y, b.alcance) for b in self.mapa_atual.bombas if b.tempo <= 1]
        trilhas_fogo = self.view.calcular_trilhas_fogo(bombas_a_explodir, self.mapa_atual)
        
        # 1. BOMBAS
        jogador_vivo = self.mapa_atual.processar_bombas()
        if not jogador_vivo:
            GerenciadorEstado.registrar_fim_partida_atualizacao_global("explosao", self.mapa_atual)
            self._renderizar_rodada_atual(trilhas_fogo=trilhas_fogo) # Redesenha estado da cratera + fogo
            self.desatar_inputs()
            self.view.exibir_game_over("GAME OVER", "Você explodiu na própria bomba!", eh_vitoria=False)
            return

        # 2. INIMIGOS e CONDIÇÕES
        sessao = GerenciadorEstado.ler_sessao()
        globais = GerenciadorEstado.ler_global()
        turno_atual = sessao.get("turno_atual", 0)
        limit = globais.get("limite_max_turnos", 100)
        
        if turno_atual >= limit:
            GerenciadorEstado.registrar_fim_partida_atualizacao_global("vitoria", self.mapa_atual)
            self._renderizar_rodada_atual(trilhas_fogo=trilhas_fogo)
            self.desatar_inputs()
            self.view.exibir_game_over("VITÓRIA!", "Resgate garantido - Tempo limite alcançado", eh_vitoria=True)
            return
            
        taxa = sessao.get("taxa_spawn_atual", 10.0)
        base = sessao.get("taxa_spawn_base", 10.0)
        
        jogo_ativo, code_spwn = self.mapa_atual.processar_turno_inimigos(turno_atual, taxa)
        
        if not jogo_ativo:
            GerenciadorEstado.registrar_fim_partida_atualizacao_global("inimigo", self.mapa_atual)
            self._renderizar_rodada_atual(trilhas_fogo=trilhas_fogo)
            self.desatar_inputs()
            self.view.exibir_game_over("GAME OVER", "O inimigo te atingiu!.", eh_vitoria=False)
            return
            
        if code_spwn == "SPAWN_SUCESSO":
            GerenciadorEstado.atualizar_sessao("taxa_spawn_base", base + 2.0)
            GerenciadorEstado.atualizar_sessao("taxa_spawn_atual", base + 2.0)
        elif code_spwn == "SPAWN_FALHA":
            GerenciadorEstado.atualizar_sessao("taxa_spawn_atual", taxa + 5.0)

        # Fim seguro: Turno passou sem gameover
        msg = "Alerta: Inimigo Spawnado!" if code_spwn == "SPAWN_SUCESSO" else None
        self._renderizar_rodada_atual(msg_alerta=msg, trilhas_fogo=trilhas_fogo)

    def desatar_inputs(self):
        """Remove os controles de jogatina para não dar outofbounds após morrer"""
        for k in ["<w>", "<a>", "<s>", "<d>", "<b>", "<q>", "<W>", "<A>", "<S>", "<D>", "<B>", "<Q>"]:
            try: self.root.unbind(k)
            except: pass

    def finalizar_volta_menu(self):
        self.mapa_atual = None
        self.jogador_atual = None
        self.voltar_menu_principal()
