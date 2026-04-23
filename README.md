# 💣 Bombardeio 1000Grau - AD2 (Tkinter Edition)

> **Versão:** 2.0.0 (Otimização Gráfica) | **Compatibilidade:** Python 3.6+ |
> **Contexto:** Avaliação a Distância 2 (AD2) - Programação com Interfaces Gráficas
> **Licença:** MIT | **Autor:** Carlos de Lima Junior

---

## 📖 Sobre a Evolução do Projeto (Da AD1 para a AD2)

Na **Versão 1.0 (AD1)**, o jogo operava de maneira puramente imperativa via terminal. Utilizando caracteres ASCII para a representação visual, a aplicação mantinha a *thread* principal bloqueada em um laço infinito (`while True`) e recebia as entradas do usuário por meio de bibliotecas de baixo nível do Sistema Operacional (`termios`, `msvcrt`).

Para esta **Versão 2.0 (AD2)**, o projeto passou por uma substancial reestruturação arquitetural. Adotamos o **padrão MVC (Model-View-Controller) Estrito**, desenvolvendo um motor gráfico baseado na biblioteca **Tkinter**. Dessa forma, o núcleo lógico do jogo opera de modo passivo e orientado a eventos através da interface gráfica nativa. Essa transição substitui definitivamente o terminal, garantindo que a pureza e as regras de negócio da Camada *Model* (avaliadas na AD1) permaneçam integralmente preservadas.

### ✨ Principais Implementações e Evoluções

1. **Camada Gráfica e Lógica Relativa (View - `view.py`)**:
   - A exibição do mapa bidimensional foi migrada da saída de console (stdout) para um componente **Canvas do Tkinter**.
   - **Dimensionamento Responsivo:** A interface escuta reajustes no tamanho da janela (por meio do evento `<Configure>`) e os recalcula proporcionalmente (`largura da tela / colunas`). Isso permite que a malha do jogo seja renderizada de forma responsiva em diversas resoluções, como 800x600 ou 1920x1080, sem qualquer distorção visual.
   - Foram estabelecidos perfis vetoriais de coloração clara e funcional: Inimigos em tons de vermelho, o Jogador em Ciano e obstáculos variados identificados por cores terrosas e neutras.

2. **Laço de Jogo Orientado a Eventos (Controller - `controller.py`)**:
   - O fluxo contínuo de processamento do antigo `main.py` foi isolado e delegado inteiramente à camada Controladora.
   - A captura de movimentação ocorre por meio de gatilhos assíncronos de teclado (`root.bind("<w>", ...)`), mantendo a execução sob controle do evento principal do Tkinter (`root.mainloop()`).
   - Implementação de um **HUD interativo em tempo real** e telas sobrepostas para o Menu Principal e para os cenários de fim de partida (Vitória ou Derrota).

3. **Efeitos Visuais e Raycast (Animação de Bombas)**:
   - Para maximizar a imersão na transição gráfica, projetamos uma rotina visual algorítmica para as explosões. O script escaneia a matriz de posições instantes antes da destruição das celas inflamáveis e rastreia vetorialmente os limites de uma detonação. A animação (fogo) atinge alvos destruíveis e cessa imediatamente ao colidir com obstáculos indestrutíveis, sendo limpa da tela após uma fração de segundos via gatilho temporal (`root.after`).

4. **Isolamento e Segurança (Model - `classes.py`)**:
   - Baseando-nos na exigência da atividade, as regras nativas não foram refatoradas. Foram implementados unicamente decoradores nativos (`@property`) para conceder permissões isoladas de leitura à interface. As justificativas técnicas completas destas definições encontram-se documentadas no `CHANGELOG_AD2_JUSTIFICATIVAS.md`.

---

## 🛠️ Guia de Instalação e Configuração

Para executar este projeto, você precisa ter um interpretador Python instalado. Abaixo segue o guia formal para configurar seu ambiente (compatível com a versão original).

### 1. Verificando a Instalação Atual

Abra seu terminal e digite:

```bash
python --version
# ou
python3 --version
```

### 2. Instalação Manual (Por Sistema Operacional)

#### 🪟 Windows

1. Acesse [python.org/downloads](https://www.python.org/downloads/).
2. Baixe a versão mais recente (Python 3.x) ou a 2.7.18 (se necessário legado).
3. **Importante:** Durante a instalação, certifique-se de marcar a caixa **"Add Python to PATH"**.

#### 🐧 Linux

**Debian/Ubuntu/Mint (`apt`):**

```bash
sudo apt update
sudo apt install python3      # Para instalar Python 3
# Para testar a versão legada (Python 2) instale o base e a interface gráfica:
sudo apt install python2 python-tk
```

**Fedora/RHEL/CentOS (`dnf`):**

```bash
sudo dnf install python3      # Para instalar Python 3
```

> [!WARNING]
> **Sobre o Python 2 e Bibliotecas Gráficas em Distros Modernas:**
> O Python 2 atingiu seu **End of Life (EOL)** oficial. Distribuições *cutting-edge* modernas, como o **Fedora**, Arch Linux e algumas versões recentes do Ubuntu, **removeram por completo** o pacote `python2` e o pacote de interface gráfica `python2-tkinter` (ou `python-tk`) de seus repositórios principais.
> 
> A pasta `Code Python 2` existe neste projeto **estritamente para cumprir o requisito acadêmico de compatibilidade retroativa**. Caso não consiga rodar o código do Python 2 em sua máquina Linux moderna devido à falta da biblioteca `_tkinter` compilada, utilize o diretório `Code Python 3`, ou valide a versão legada em um ambiente Windows (cujo instalador oficial traz o Tkinter embutido) ou em sistemas Unix legados.

**Arch Linux/Manjaro (`pacman`):**

```bash
sudo pacman -S python         # Instala a última ramificação estável (3.x)
sudo pacman -S python2        # Instala Python 2.7 secundário
```

**OpenSUSE (`zypper`):**

```bash
sudo zypper install python3
```

#### 🍎 macOS

Recomendamos utilizar o instalador interativo **Homebrew**:

```bash
brew install python           # Instala Python 3 nativo
brew install python@2         # Instala Python 2 legado (se disponível no pacote)
```

---

## 🎮 Novo Manual de Controles (Interface GUI)

### Inicialização Rápida
Abra seu emulador de terminal no diretório da nova versão:
```bash
cd "Code Python 3"
python3 main_gui.py
```

### Navegação (Mouse):
- Clique diretamente nos botões gráficos para **Iniciar a Partida** ou **Encerrar**.
- O jogo exibirá no início suas estatísticas baseadas na persistência de sessões salvas anteriores.
- Uma caixa de diálogo (modal) questionará, antes de renderizar o campo, a proporção do Mapa em que se deseja jogar (Pequeno, Médio, Grande).

### Controles Ativos (Teclado):
Os controles fluem instintivamente conforme o pressionamento, sem obrigatoriedade de acionar `Enter`.

- `W` : Move o personagem para cima.
- `S` : Move o personagem para baixo.
- `A` : Move o personagem para a esquerda.
- `D` : Move o personagem para a direita.
- `B` : Planta uma bomba na posição atual (a detonação ocorre impreterivelmente após **3 turnos**).
- `Q` : Abandona a partida em curso abruptamente.

### Legenda Visual (Camada Tkinter):

| Componente | Representação Gráfica | Padrão Cromático | Descrição de Uso |
| --- | --- | --- | --- |
| **Jogador** | Círculo Preenchido c/ Borda | Ciano | Sua entidade navegável. Sobreviva. |
| **Inimigo** | Círculo Sem Borda | Vermelho Vivo | Perseguição sistêmica. Encostar resulta em morte instantânea. |
| **Obstáculo Fixo** | Quadrado Sólido Amplo | Cinza Neutro | Elemento maciço da arquitetura. Indestrutível contra explosões de qualquer raio. |
| **Caixote Simples** | Quadrado Sólido Menor | Laranja Tênue | Destrutível. Cobre sua fuga ou esconde caminhos e armadilhas. |
| **Carga Explosiva** | Círculo Destaque e Número | Amarelo | Contém contador de turnos sobreposto. Fuja antes de ele zerar. |
| **Detonação Geométrica** | Rastro e Lampejo | Ouro e Vermelho | Dispersão cruzada do dano que limpa inimigos e obstáculos suscetíveis do mapa. |

---

## 🧠 Persistência e Ajuste Dinâmico (Relembrando)

Assim como garantido na versão base, a técnica de *Dificuldade Dinâmica Adaptativa* permanece contínua. Sem perdas funcionais, transações acontecem em segundo plano comunicando-se unicamente com o `estatisticas_globais.json`.

- A IA do controlador penaliza jogadores cujo registro provar níveis altos de desempenho, gerando gradualmente campos mais encurraladores no próximo reinício do código.
- Para invalidar forçadamente a progressão das partidas jogadas, os usuários logados podem deletar de maneira segura o arquivo `.json`. A recriação do *score* iniciará novamente na execução seguinte.