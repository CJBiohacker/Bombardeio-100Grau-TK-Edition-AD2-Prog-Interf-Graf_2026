#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import json
import os
import io
import sys

class GerenciadorEstado(object):
    # Define o diretório base como o diretório onde este arquivo (persistencia.py) está
    # Decodifica para unicode usando a codificação do sistema de arquivos
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)).decode(sys.getfilesystemencoding())
    
    ARQUIVO_SESSAO = os.path.join(BASE_DIR, "sessao_atual.json")
    ARQUIVO_GLOBAL = os.path.join(BASE_DIR, "estatisticas_globais.json")

    # =========================================================================
    # CONFIGURAÇÕES PADRÃO
    # =========================================================================
    
    # Valores iniciais para uma nova sessão (reset)
    PADRAO_SESSAO = {
        "turno_atual": 0,
        "taxa_spawn_base": 10.0,    # 10%
        "taxa_spawn_atual": 10.0,   # Começa igual a base
        "inimigos_iniciais": 3,
        "total_inimigos_vivos": 3,
        "bombas_plantadas_sessao": 0,
        "obstaculos_destruidos_sessao": 0
    }

    # Valores iniciais caso o arquivo global não exista
    PADRAO_GLOBAL = {
        "partidas_jogadas": 0,
        "soma_turnos_sobrevividos": 0,
        "soma_bombas_utilizadas": 0,
        "soma_obstaculos_destruidos": 0,
        "historico_causas_termino": [], # Lista de strings
        "historico_turnos_sobrevividos": [], # Lista de int (turnos de cada partida)
        "historico_total_obstaculos": [], # Lista de int (qtd de obstaculos destrutiveis gerados)
        "historico_obstaculos_destruidos_partida": [], # Lista de int

        # Estatísticas Calculadas (Médias)
        "media_turnos": 0.0,
        "media_bombas": 0.0,
        "taxa_destruicao_media": 0.0, # (Total Destruído / Total Gerado) * 100

        # Parâmetros de Balanceamento (Dificuldade)
        "alcance_bomba": 2,
        "tempo_detonacao_bomba": 3,
        "limite_max_turnos": 100,
        "fator_dificuldade_inimigos": 1.0,
        "densidade_obstaculos": 0.48 # 48% (Novo Parâmetro Dinâmico)
    }

    # =========================================================================
    # MÉTODOS DE GERENCIAMENTO DE ARQUIVOS (IO)
    # =========================================================================

    @classmethod
    def inicializar_arquivos(cls):
        """
        Verifica se os arquivos existem. 
        Se não, cria com valores padrão.
        Sempre reseta a sessão ao iniciar o jogo.
        """
        # Sempre reseta a sessão ao abrir o jogo
        cls.__salvar_arquivo(cls.ARQUIVO_SESSAO, cls.PADRAO_SESSAO)

        # Só cria o global se não existir
        if not os.path.exists(cls.ARQUIVO_GLOBAL):
            cls.__salvar_arquivo(cls.ARQUIVO_GLOBAL, cls.PADRAO_GLOBAL)
        else:
            # Opcional: Validar se todas as chaves existem (migração simples)
            dados = cls.ler_global()
            modificado = False
            for chave, valor in cls.PADRAO_GLOBAL.items():
                if chave not in dados:
                    dados[chave] = valor
                    modificado = True
            if modificado:
                cls.__salvar_arquivo(cls.ARQUIVO_GLOBAL, dados)

    @staticmethod
    def __salvar_arquivo(caminho, dados):
        try:
            with io.open(caminho, 'w', encoding='utf-8') as f:
                # ensure_ascii=False para salvar acentos corretamente
                f.write(json.dumps(dados, indent=4, ensure_ascii=False))
        except IOError as e:
            print("Erro ao salvar arquivo {}: {}".format(caminho, e))

    @staticmethod
    def __ler_arquivo(caminho):
        try:
            with io.open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        # Python 2 não tem json.JSONDecodeError, usa ValueError
        except (IOError, ValueError) as e:
            print("Erro ao ler arquivo {}: {}".format(caminho, e))
            return {}

    # =========================================================================
    # MÉTODOS DE LEITURA
    # =========================================================================

    @classmethod
    def ler_sessao(cls):
        return cls.__ler_arquivo(cls.ARQUIVO_SESSAO)

    @classmethod
    def ler_global(cls):
        return cls.__ler_arquivo(cls.ARQUIVO_GLOBAL)

    # =========================================================================
    # MÉTODOS DE ESCRITA / ATUALIZAÇÃO LÓGICA
    # =========================================================================

    @classmethod
    def atualizar_sessao(cls, chave, valor):
        """Atualiza um valor específico da sessão atual."""
        dados = cls.ler_sessao()
        if chave in dados:
            dados[chave] = valor
            cls.__salvar_arquivo(cls.ARQUIVO_SESSAO, dados)
        else:
            print("Chave '{}' não existe na sessão.".format(chave))

    @classmethod
    def incrementar_sessao(cls, chave, qtd=1):
        """Incrementa um valor numérico da sessão."""
        dados = cls.ler_sessao()
        if chave in dados and isinstance(dados[chave], (int, float)):
            dados[chave] += qtd
            cls.__salvar_arquivo(cls.ARQUIVO_SESSAO, dados)

    @classmethod
    def registrar_fim_partida_atualizacao_global(cls, causa_termino, mapa=None):
        """
        Consolida os dados da sessão no arquivo global e recalcula médias.
        Chamado apenas quando o jogo acaba.
        Necessita do objeto 'mapa' para saber quantos obstáculos foram gerados.
        """
        sessao = cls.ler_sessao()
        global_stats = cls.ler_global()

        # 1. Atualizar Acumuladores e Históricos
        global_stats["partidas_jogadas"] += 1
        global_stats["soma_turnos_sobrevividos"] += sessao["turno_atual"]
        global_stats["soma_bombas_utilizadas"] += sessao["bombas_plantadas_sessao"]
        
        # Histórico de Turnos (Requisito 1)
        if "historico_turnos_sobrevividos" not in global_stats: global_stats["historico_turnos_sobrevividos"] = []
        global_stats["historico_turnos_sobrevividos"].append(sessao["turno_atual"])
        
        if "historico_causas_termino" not in global_stats: global_stats["historico_causas_termino"] = []
        global_stats["historico_causas_termino"].append(causa_termino)

        # Taxa de Destruição (Requisito 2: Melhor cálculo)
        destruidos = sessao["obstaculos_destruidos_sessao"]
        total_gerados = 0 
        if mapa:
            total_gerados = mapa.total_obstaculos_destrutiveis_iniciais
        
        # Salvar histórico de obstáculos para média real
        if "historico_total_obstaculos" not in global_stats: global_stats["historico_total_obstaculos"] = []
        if "historico_obstaculos_destruidos_partida" not in global_stats: global_stats["historico_obstaculos_destruidos_partida"] = []
        
        global_stats["historico_total_obstaculos"].append(total_gerados)
        global_stats["historico_obstaculos_destruidos_partida"].append(destruidos)
        global_stats["soma_obstaculos_destruidos"] += destruidos

        # 2. Recalcular Médias
        total_partidas = global_stats["partidas_jogadas"]
        if total_partidas > 0:
            global_stats["media_turnos"] = round(float(global_stats["soma_turnos_sobrevividos"]) / total_partidas, 2)
            global_stats["media_bombas"] = round(float(global_stats["soma_bombas_utilizadas"]) / total_partidas, 2)
            
            # Taxa de Destruição Global = Soma Destruídos / Soma Gerados
            soma_gerados = sum(global_stats.get("historico_total_obstaculos", []))
            soma_destruidos = sum(global_stats.get("historico_obstaculos_destruidos_partida", []))
            
            if soma_gerados > 0:
                global_stats["taxa_destruicao_media"] = round((float(soma_destruidos) / soma_gerados) * 100, 2)
            else:
                global_stats["taxa_destruicao_media"] = 0.0

        # 3. Balanceamento Automático (Requisito 3)
        # Modificar Densidade de Obstáculos baseado na sobrevivência
        ultima_sobrevivencia = sessao["turno_atual"]
        media_historica = global_stats["media_turnos"]
        densidade_atual = global_stats.get("densidade_obstaculos", 0.48)
        
        # Lógica: Se sobreviveu muito acima da média -> Aumenta densidade (dificulta movimentação/fuga)
        # Se morreu rápido -> Diminui densidade (facilita fuga)
        # Limites: Min 30% (0.3), Max 70% (0.7)
        if ultima_sobrevivencia > (media_historica * 1.2) and total_partidas > 1:
            densidade_atual = min(0.7, densidade_atual + 0.05)
        elif ultima_sobrevivencia < (media_historica * 0.8) and total_partidas > 1:
            densidade_atual = max(0.3, densidade_atual - 0.05)
            
        global_stats["densidade_obstaculos"] = round(densidade_atual, 2)

        # Salva tudo
        cls.__salvar_arquivo(cls.ARQUIVO_GLOBAL, global_stats)
        
        # Limpa sessão
        cls.__salvar_arquivo(cls.ARQUIVO_SESSAO, cls.PADRAO_SESSAO)
