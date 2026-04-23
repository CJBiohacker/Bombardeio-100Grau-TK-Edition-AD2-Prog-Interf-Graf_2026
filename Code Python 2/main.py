#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from classes import Mapa, Jogador
from persistencia import GerenciadorEstado
import sys
import os
import codecs

# Garante que sys.stdout use UTF-8 para evitar erros de encoding ao imprimir Unicode
if sys.stdout.encoding is None or sys.stdout.encoding == 'ASCII':
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout)
    except Exception:
        pass # Se falhar, segue o padrão

# Detecção de Sistema Operacional para Input
if os.name == 'nt':
    import msvcrt
    def get_key():
        """Lê uma única tecla no Windows."""
        return msvcrt.getch().decode('utf-8')
else:
    import tty
    import termios
    def get_key():
        """Lê uma única tecla no Linux/macOS."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def limpar_tela():
    """Limpa o console para atualizar o visual do jogo."""
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    
    # 1. Inicializa o estado persistente
    GerenciadorEstado.inicializar_arquivos()
    
    # 2. Carrega configurações globais para dificuldade
    configs_globais = GerenciadorEstado.ler_global()

    try:
        nome_jogador = raw_input("Digite o nome do jogador: ").decode(sys.stdin.encoding or 'utf-8')
    except AttributeError:
        # Fallback caso sys.stdin.encoding seja None
        nome_jogador = raw_input("Digite o nome do jogador: ").decode('utf-8')
        
    if not nome_jogador:
        nome_jogador = "Heroi"

    # Seleção de Mapa
    print("\nEscolha o tamanho do mapa:")
    print("1 - Pequeno (8x7)")
    print("2 - Médio (12x11)")
    print("3 - Grande (16x14)")
    
    # Codifica o prompt para bytes para evitar erro no raw_input do Python 2
    prompt = "Opção: ".encode(sys.stdout.encoding or 'utf-8')
    escolha_mapa = raw_input(prompt).strip()

    if escolha_mapa == "1":
        l, c = 8, 7
        fator_area = 0.5
    elif escolha_mapa == "3":
        l, c = 16, 14
        fator_area = 1.5
    else:
        l, c = 12, 11
        fator_area = 1.0

    # Ajusta inimigos base pela área do mapa e dificuldade histórica
    media_turnos = configs_globais.get("media_turnos", 0)
    qtd_inimigos_base = int(((media_turnos // 20) + 3) * fator_area)
    qtd_inimigos_base = max(1, qtd_inimigos_base) # Mínimo 1 inimigo
    
    # Ajusta densidade de obstáculos baseada na persistência (balanceamento implementado no persistencia.py)
    densidade_obs = configs_globais.get("densidade_obstaculos", 0.48)

    mapa = Mapa(linhas=l, colunas=c, config_dificuldade={
        "inimigos_iniciais": qtd_inimigos_base,
        "densidade_obstaculos": densidade_obs
    })

    # Adicionando o jogador no mapa
    
    jogador = Jogador(nome_jogador)
    mapa.adicionar_jogador(jogador)

    print("\n Olá {}! Bem-vindo ao Bombardeio 1000Grau.".format(nome_jogador))
    print("\nVisualização do Mapa Inicial:")

    # Mensagens de feedback para o jogador
    mensagem = "\n Olá {}! Bem-vindo ao Bombardeio 1000Grau.".format(nome_jogador)

    # Loop principal
    while True:
        limpar_tela()
        
        # 1. Mostrar Mapa e Status
        print("\nTurno: {} | Inimigos: {}".format(
            GerenciadorEstado.ler_sessao().get('turno_atual', 0), 
            len(mapa.inimigos)
        ))
        print(mapa)
        
        # Exibe mensagens acumuladas da rodada anterior
        if mensagem:
            print("\n[AVISO]: {}".format(mensagem))
            mensagem = "" # Limpa após exibir
        
        # 2. Input do Jogador (Lê apenas um caractere sem enter)
        print("\nComandos: w/a/s/d mover, 'b' bomba, 'q' sair")
        try:
            comando = get_key().lower()
        except:
            comando = ""
        
        if comando == "q":
            GerenciadorEstado.registrar_fim_partida_atualizacao_global("quit", mapa)
            print("Jogo encerrado pelo usuário.")
            break

        direcao = None
        plantou_bomba = False
        passa_turno = False
        
        if comando == "w": direcao = "cima"
        elif comando == "s": direcao = "baixo"
        elif comando == "a": direcao = "esquerda"
        elif comando == "d": direcao = "direita"
        elif comando == "b": plantou_bomba = True

        if plantou_bomba:
            # Pega configs para a bomba
            configs_globais = GerenciadorEstado.ler_global() # Re-ler configs se necessario
            tempo_bomba = configs_globais.get("tempo_detonacao_bomba", 3)
            alcance_bomba = configs_globais.get("alcance_bomba", 2)
            
            sucesso = jogador.plantar_bomba(mapa, tempo_bomba, alcance_bomba)
            if sucesso:
                # Plantar bomba não conta como turno apenas ação livre
                mensagem = "Bomba Plantada! Agora mova-se para sair de cima."
            else:
                # Mensagem de erro já é dada no método adicionar_bomba
                mensagem = "Ação de bomba falhou (local ocupado ou erro)."
            passa_turno = False # Nunca passa turno ao plantar
        
        elif direcao:
            # B. Movimento do Jogador
            sucesso_movimento = jogador.movimentar(mapa, direcao)
            passa_turno = sucesso_movimento
            if not sucesso_movimento and not passa_turno:
                 mensagem = "Movimento inválido ou bloqueado."
        elif comando != "":
            mensagem = "Comando inválido!"
            passa_turno = False

        if passa_turno:
            # 1. Incrementa turno na persistência
            GerenciadorEstado.incrementar_sessao("turno_atual", 1)
            
            # PRIMEIRO: Processa Bombas
            jogador_vivo = mapa.processar_bombas()
            if not jogador_vivo:
                print("\n==================================")
                print("Fim de Jogo! Explodido!")
                print("==================================\n")
                GerenciadorEstado.registrar_fim_partida_atualizacao_global("explosao", mapa)
                break
            
            # 2. Ler dados para processar inimigos
            sessao = GerenciadorEstado.ler_sessao()
            taxa_spawn = sessao.get("taxa_spawn_atual", 10.0)
            base_spawn = sessao.get("taxa_spawn_base", 10.0)
            turno_atual = sessao.get("turno_atual", 0)

            # --- VERIFICAÇÃO DE VITÓRIA ---
            # A partida termina com sucesso se o jogador não for eliminado após uma quantidade determinada de turnos.
            limite_turnos = configs_globais.get("limite_max_turnos", 100)
            if turno_atual >= limite_turnos:
                limpar_tela()
                print("\nTurno Final: {}".format(turno_atual))
                print(mapa)
                print("\n==================================")
                print("PARABÉNS! Você sobreviveu ao Bombardeio!")
                print("Você resistiu por {} turnos.".format(limite_turnos))
                print("==================================\n")
                GerenciadorEstado.registrar_fim_partida_atualizacao_global("vitoria", mapa)
                break

            # 3. Processar Inimigos (Mover + Spawn)
            jogo_ativo, codigo_spawn = mapa.processar_turno_inimigos(turno_atual, taxa_spawn)
            
            if not jogo_ativo:
                print("\n==================================")
                print("Fim de Jogo! Você foi pego!")
                print("==================================\n")
                GerenciadorEstado.registrar_fim_partida_atualizacao_global("inimigo", mapa)
                break
                
            # 4. Atualizar Taxa de Spawn
            if codigo_spawn == "SPAWN_SUCESSO":
                nova_base = base_spawn + 2.0
                GerenciadorEstado.atualizar_sessao("taxa_spawn_base", nova_base)
                GerenciadorEstado.atualizar_sessao("taxa_spawn_atual", nova_base)
            elif codigo_spawn == "SPAWN_FALHA":
                nova_taxa = taxa_spawn + 5.0
                GerenciadorEstado.atualizar_sessao("taxa_spawn_atual", nova_taxa)
