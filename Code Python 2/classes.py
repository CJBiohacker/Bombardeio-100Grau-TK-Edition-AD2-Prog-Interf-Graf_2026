#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import random
from persistencia import GerenciadorEstado

class Mapa(object):
    def __init__(self, linhas=8, colunas=7, config_dificuldade=None):
        self.__linhas = linhas
        self.__colunas = colunas
        self.__config = config_dificuldade if config_dificuldade else {}
        
        # Inicializa a matriz com None (espaço vazio)
        self.__celulas = [[None for _ in range(colunas)] for _ in range(linhas)]
        self.__jogadores = []
        self.__inimigos = []
        self.__bombas = []
        
        # Estatísticas do mapa para a persistência
        self.total_obstaculos_destrutiveis_iniciais = 0

        # Etapa 1: Paredes Fixas (Indestrutíveis)
        self.__gerar_paredes_fixas()

        # Etapa 2: Obstáculos Destrutíveis (Aleatoriedade Controlada)
        densidade_base = config_dificuldade.get("densidade_obstaculos", 0.48)
        self.__gerar_obstaculos_destrutiveis(densidade_base)

        # Etapa 3: Inimigos Iniciais
        qtd_inimigos = self.__config.get("inimigos_iniciais", 3)
        self.__spawn_inimigos_inicial(qtd_inimigos)

    def __gerar_paredes_fixas(self):
        """
        Gera as paredes indestrutíveis fixas conforme o padrão do Bomberman:
        Linhas alternadas e colunas alternadas.
        """
        for l in range(0, self.__linhas, 2):  # Linhas: 0, 2, 4, 6
            for c in range(1, self.__colunas, 2):  # Colunas: 1, 3, 5
                self.adicionar_obstaculo(Obstaculo("indestrutivel"), l, c)

    def __gerar_obstaculos_destrutiveis(self, densidade):
        """
        Gera Obstáculos destrutíveis aleatoriamente com densidade controlada pelo estado persistente.
        Regras:
        - Não pode spawnar em (0,0), (0,1), (1,0) e (1,1) [Área segura do jogador].
        - Tenta evitar grandes blocos adjacentes (máximo 3 Obstáculos juntos).
        """
        # Área segura do jogador
        safe_zone = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]

        # Lista de células vazias candidatas
        candidatos = []
        for l in range(self.__linhas):
            for c in range(self.__colunas):
                # Se estiver vazio e não for zona segura
                if self.__celulas[l][c] is None and (l, c) not in safe_zone:
                    candidatos.append((l, c))

        # Define quantidade baseada na densidade
        qtd_obstaculos = int(len(candidatos) * densidade)
        random.shuffle(candidatos)  # Embaralha para aleatoriedade

        count = 0
        for l, c in candidatos:
            if count >= qtd_obstaculos:
                break

            # Verificação de adjacência (heurística simples)
            # Conta quantos Obstáculos (de qualquer tipo) existem ao redor (cima, baixo, esq, dir)
            adjacentes = 0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = l + dx, c + dy
                if self.posicao_valida(nx, ny) and isinstance(
                    self.__celulas[nx][ny], Obstaculo
                ):
                    adjacentes += 1

            # Se tiver menos de 3 vizinhos Obstáculos, pode colocar
            if adjacentes < 3:
                self.adicionar_obstaculo(Obstaculo("destrutivel"), l, c)
                count += 1
        
        # Registra total gerado para estatísticas
        self.total_obstaculos_destrutiveis_iniciais = count

    def __spawn_inimigos_inicial(self, qtd_inimigos):
        """
        Gera inimigos iniciais em posições aleatórias vazias (longe da safe zone).
        Quantidade baseada na configuração de dificuldade.
        """
        
        # Área segura estendida para inimigos (para não morrer logo de cara)
        safe_zone = [
            (0, 0),
            (0, 1),
            (0, 2),
            (1, 0),
            (1, 1),
            (1, 2),
            (2, 0),
            (2, 2),
            (3, 0),
        ]

        candidatos = []
        for l in range(self.__linhas):
            for c in range(self.__colunas):
                if self.__celulas[l][c] is None and (l, c) not in safe_zone:
                    candidatos.append((l, c))

        random.shuffle(candidatos)

        for i in range(min(qtd_inimigos, len(candidatos))):
            l, c = candidatos[i]
            # Cria e posiciona o inimigo
            inimigo = Inimigo("Inimigo_{}".format(i+1))
            self.adicionar_inimigo(inimigo, l, c)

    def adicionar_obstaculo(self, obstaculo, x, y):
        if self.posicao_valida(x, y) and self.__celulas[x][y] is None:
            self.__celulas[x][y] = obstaculo
            return True
        return False

    def posicao_valida(self, x, y):
        """Verifica se a coordenada está dentro dos limites do mapa."""
        return 0 <= x < self.__linhas and 0 <= y < self.__colunas

    def __unicode__(self):
        """Retorna uma representação visual do mapa para o terminal (Unicode)."""
        # Cabeçalho das colunas (0 a N-1)
        visual = "  " + " ".join(str(i) for i in range(self.__colunas)) + "\n"
        for i, linha in enumerate(self.__celulas):
            visual += "{} ".format(i)  # Índice da linha
            for j, cell in enumerate(linha):
                # Prioridade: Jogador > Inimigo > Obstáculo > Bomba > Vazio
                symbol = "_ "
                
                # Check da BOMBA (camada "chão")
                has_bomb = False
                for b in self.__bombas:
                    if b.x == i and b.y == j:
                        has_bomb = True
                        break
                
                if has_bomb:
                    symbol = "O "
                
                # Check dos Objetos da Célula (camada "topo")
                if cell is not None:
                    if isinstance(cell, Obstaculo):
                        symbol = "# " if cell.tipo == "indestrutivel" else "▢ "
                    elif isinstance(cell, Jogador):
                        symbol = "@ "
                    elif isinstance(cell, Inimigo):
                        symbol = "E "
                
                visual += symbol
            visual += "\n"
        return visual

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def adicionar_jogador(self, jogador):
        # Define posição inicial (0,0) se estiver vazia
        if self.__celulas[0][0] is None:
            self.__celulas[0][0] = jogador
            jogador.x = 0
            jogador.y = 0
            self.__jogadores.append(jogador)
        else:
            print("Erro: Posição inicial (0,0) ocupada!")

    # [AD2-GUI-FIX]: Expõe as propriedades privadas estritamente para a camada View conseguir desenhar.
    @property
    def linhas(self): return self.__linhas
    
    @property
    def colunas(self): return self.__colunas
    
    @property
    def celulas(self): return self.__celulas
    
    @property
    def bombas(self): return self.__bombas
    
    @property
    def jogadores(self): return self.__jogadores

    @property
    def inimigos(self):
        return self.__inimigos

    def adicionar_inimigo(self, inimigo, x, y):
        # Tenta posicionar o inimigo na coordenada especificada
        if self.posicao_valida(x, y) and self.__celulas[x][y] is None:
            self.__celulas[x][y] = inimigo
            inimigo.x = x
            inimigo.y = y
            self.__inimigos.append(inimigo)
            return True
        return False

    def processar_turno_inimigos(self, turno_atual, base_spawn_rate):
        """
        Move todos os inimigos e tenta spawnar novos.
        Retorna:
        - True: Jogo continua
        - False: Game Over (Inimigo atingiu jogador)
        - novo_base_rate: Taxa de spawn atualizada para o próximo turno
        """
        # 1. Movimentação dos inimigos
        for inimigo in self.__inimigos:
            # Calcula movimentos possíveis
            possiveis = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]: # Cima, Baixo, Esq, Dir
                nx, ny = inimigo.x + dx, inimigo.y + dy
                
                if not self.posicao_valida(nx, ny):
                    continue
                
                conteudo = self.__celulas[nx][ny]
                
                # Se for o jogador -> Fim de Jogo IMEDIATO
                if isinstance(conteudo, Jogador):
                    print("Fim de Jogo: O inimigo o alcançou na coordenada ({}, {})!".format(nx, ny))
                    return False, base_spawn_rate
                
                # Se for vazio, é um movimento válido
                if conteudo is None:
                    # Verifica se tem bomba (Inimigo não passa por cima de bomba)
                    tem_bomba = False
                    for b in self.__bombas:
                        if b.x == nx and b.y == ny:
                            tem_bomba = True
                            break
                    
                    if not tem_bomba:
                        possiveis.append((nx, ny))
            
            # Se tiver movimentos, escolhe um aleatório
            if possiveis:
                dest_x, dest_y = random.choice(possiveis)
                # Atualiza grid
                self.__celulas[inimigo.x][inimigo.y] = None
                self.__celulas[dest_x][dest_y] = inimigo
                # Atualiza objeto
                inimigo.x = dest_x
                inimigo.y = dest_y

        # 2. Lógica de Spawn de Novos Inimigos
        novo_base_rate = base_spawn_rate
        limite_inimigos = 3 + (turno_atual // 2)
        
        if len(self.__inimigos) < limite_inimigos:
            # Chance % de aparecer novo
            chance = random.random() * 100
            
            # Se a chance for menor que a taxa base atual, spawna
            if chance < base_spawn_rate:
                # Spawnar
                spawnou = self.__tentar_spawnar_inimigo_extra()
                if spawnou:
                    print("Alerta: Um novo inimigo surgiu no mapa! (Turno {})".format(turno_atual))
                    return True, "SPAWN_SUCESSO"
            else:
                # Não spawnou -> Aumenta chance para próxima
                return True, "SPAWN_FALHA" # Falha por sorteio
        
        return True, "SPAWN_LIMITE" # Falha por limite populacional

    def __tentar_spawnar_inimigo_extra(self):
        """Tenta encontrar um lugar vazio longe do jogador para nascer inimigo."""
        # Encontra posição do jogador
        px, py = -1, -1
        if self.__jogadores:
            px, py = self.__jogadores[0].x, self.__jogadores[0].y
            
        candidatos = []
        for l in range(self.__linhas):
            for c in range(self.__colunas):
                if self.__celulas[l][c] is None:
                    # Distância de Manhattan segura (ex: > 2 casas)
                    dist = abs(l - px) + abs(c - py)
                    if dist > 2:
                        candidatos.append((l, c))
        
        if candidatos:
            lx, ly = random.choice(candidatos)
            novo_inimigo = Inimigo("Inimigo_Extra") # Nome genérico
            self.adicionar_inimigo(novo_inimigo, lx, ly)
            return True
        return False

    def adicionar_bomba(self, x, y, tempo, alcance):
        # Verifica se já existe uma bomba nesta posição visual ou na lista
        for b in self.__bombas:
            if b.x == x and b.y == y:
                print("Você já posicionou uma bomba neste espaço; por favor, realize um movimento.")
                return False

        if self.posicao_valida(x, y):
            print("Bomba armada na coordenada ({}, {})".format(x, y))
            nova_bomba = Bomba(x, y, tempo, alcance)
            self.__bombas.append(nova_bomba)
            GerenciadorEstado.incrementar_sessao("bombas_plantadas_sessao", 1)
            return True
        return False

    def processar_bombas(self):
        """
        Atualiza timer das bombas e explode as que zeraram.
        Retorna:
        - True: Jogo segue.
        - False: Jogo acabou (Jogador morreu na explosão).
        """
        if not self.__bombas:
            return True

        bombas_para_explodir = []
        
        # Copia da lista para não modificar durante iteração
        for bomba in list(self.__bombas):
            if bomba.tick():
                bombas_para_explodir.append(bomba)
        
        # Processa explosões
        jogador_vivo = True
        
        for bomba in bombas_para_explodir:
            print("Detonação ocorrida na coordenada ({}, {})!".format(bomba.x, bomba.y))
            
            # Remove da lista
            self.__bombas.remove(bomba)
            
            # Remove da matriz se estiver "sozinha" (sem jogador em cima)
            if self.__celulas[bomba.x][bomba.y] is None: 
                pass 
            
            # Calcular explosão
            if self.calcular_explosao(bomba):
                jogador_vivo = False
        
        return jogador_vivo

    def calcular_explosao(self, bomba):
        """
        Aplica dano da explosão em cruz (cima, baixo, esq, dir).
        Retorna True se jogador morrer.
        """
        # Centro também é atingido
        if self.verificar_dano_celula(bomba.x, bomba.y):
            return True

        direcoes = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dx, dy in direcoes:
            for dist in range(1, bomba.alcance + 1):
                nx, ny = bomba.x + (dx * dist), bomba.y + (dy * dist)
                
                # Se saiu do mapa, para essa direção
                if not self.posicao_valida(nx, ny):
                    break
                
                # Verifica se atingiu jogador nessa célula
                if self.verificar_dano_celula(nx, ny):
                    return True
                
                # Trata efeitos na célula (destrói obstáculo, remove inimigo)
                # Retorna True se a explosão deve PARAR nessa direção
                bloqueou = self.tratar_explosao_celula(nx, ny)
                
                if bloqueou:
                    break
        return False

    def verificar_dano_celula(self, x, y):
        """Verifica se algum jogador está na coordenada e printa morte."""
        for jog in self.__jogadores:
            if jog.x == x and jog.y == y:
                print("Fim de Jogo: Você foi atingido por uma explosão na coordenada ({}, {})!".format(x, y))
                return True
        return False

    def tratar_explosao_celula(self, x, y):
        """
        Aplica efeito da explosão na célula (destrói obstáculo, mata inimigo).
        Retorna True se a explosão deve PARAR nessa direção (parede/obstáculo).
        """
        conteudo = self.__celulas[x][y]
        
        # Verifica Inimigos (pode ter vários?) - Assume 1 por célula
        # Se tiver inimigo, remove ele
        for inimigo in list(self.__inimigos): # Copia para evitar erro de iteração
            if inimigo.x == x and inimigo.y == y:
                print("Um inimigo foi eliminado na coordenada ({}, {})!".format(x, y))
                self.__inimigos.remove(inimigo)
                self.__celulas[x][y] = None
                GerenciadorEstado.incrementar_sessao("total_inimigos_vivos", -1) 
                # (Não para a explosão)
                continue

        # Verifica Obstáculos
        if isinstance(conteudo, Obstaculo):
            if conteudo.tipo == "indestrutivel":
                 return True # Para a explosão
            else:
                 # Destrutível: Destrói e Para a explosão
                 print("Obstáculo destruído na coordenada ({}, {})".format(x, y))
                 self.__celulas[x][y] = None
                 GerenciadorEstado.incrementar_sessao("obstaculos_destruidos_sessao", 1)
                 return True 
        
        return False # Continua (vazio ou inimigo morto)

    def mover_jogador(self, jogador, direcao):
        """
        Tenta mover o jogador na direção especificada.
        Retorna True se o movimento foi realizado (turno deve passar).
        Retorna False se o movimento foi inválido (turno não passa).
        """
        direcoes = {
            "cima": (-1, 0),
            "baixo": (1, 0),
            "esquerda": (0, -1),
            "direita": (0, 1),
        }

        if direcao not in direcoes:
            print("Direção inválida: {}".format(direcao))
            return False

        dx, dy = direcoes[direcao]
        novo_x = jogador.x + dx
        novo_y = jogador.y + dy

        # 1. Validar limites do mapa
        if not self.posicao_valida(novo_x, novo_y):
            print("\nMovimento inválido: posição fora dos limites do mapa. (Você perdeu o turno aguardando).")
            return True # Conta como turno

        # 2. Verificar conteúdo da célula destino
        conteudo_destino = self.__celulas[novo_x][novo_y]

        if isinstance(conteudo_destino, Obstaculo):
            print("\nMovimento inválido: obstáculo no caminho. (Você perdeu o turno aguardando).")
            return True

        if isinstance(conteudo_destino, Bomba):
            print("\nMovimento bloqueado: existe uma bomba armada nesta posição.")
            return False

        if isinstance(conteudo_destino, Inimigo):
            print("\nFim de Jogo: O inimigo o capturou!")
            return True

        # 3. Realizar movimento (se destino livre)
        # Remove da posição anterior
        self.__celulas[jogador.x][jogador.y] = None

        # Atualiza coordenadas do jogador
        jogador.x = novo_x
        jogador.y = novo_y

        # Coloca na nova posição
        self.__celulas[novo_x][novo_y] = jogador
        return True


class Jogador(object):
    def __init__(self, nome):
        self.__nome = nome
        self.x = 0
        self.y = 0

    def salvar_posicao(self, posicao_atual):
        return print("Coordenadas {} salvas.".format(posicao_atual))

    def movimentar(self, mapa, direcao):
        return mapa.mover_jogador(self, direcao)

    def plantar_bomba(self, mapa, tempo=3, alcance=2):
        return mapa.adicionar_bomba(self.x, self.y, tempo, alcance)


class Bomba(object):
    def __init__(self, x, y, tempo, alcance):
        self.x = x
        self.y = y
        self.tempo = tempo
        self.alcance = alcance

    def tick(self):
        """Reduz o tempo da bomba. Retorna True se explodiu."""
        self.tempo -= 1
        return self.tempo <= 0

class Obstaculo(object):
    def __init__(self, tipo):
        self.__tipo = tipo

    @property
    def tipo(self):
        return self.__tipo

    def destruir(self):
        if self.__tipo == "destrutível":
            return print("O obstáculo foi completamente destruído.")
        else:
            return print("Este obstáculo é de natureza indestrutível.")


class Inimigo(object):
    def __init__(self, nome):
        self.__nome = nome
        self.x = 0
        self.y = 0

    def movimentar(self):
        return print("{} realizou um movimento.".format(self.__nome))
