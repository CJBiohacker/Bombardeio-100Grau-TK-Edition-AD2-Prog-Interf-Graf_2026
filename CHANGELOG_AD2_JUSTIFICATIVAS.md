# Justificativas de Alteração (AD2 GUI FIX)

A fundação fornecida e definida na AD1 foi mantida integralmente (MVC rigoroso). As mínimas modificações no arquivo `classes.py` foram feitas puramente para acomodar o padrão MVC com a View e Controller rodando via Tkinter, evitando ao máximo qualquer modificação nas engrenagens e nas implementações de regra do objeto em si.

## Modificação 01: Exposição de Atributos Privados
- **Arquivos Alterados:** `Code Python 3/classes.py`
- **Trecho Anterior:** O acesso à matriz de células do grid e objetos de ambiente e entidade estavam presos no método padrão `__str__` (feito originariamente para terminal print). Ex: Instância tinha `self.__linhas`, `self.__celulas`, `self.__bombas`.
- **Trecho Novo:** Adicionadas anotações em classe `@property` (Getters) para retorno de leitura pública das variáveis: 
  - `linhas` / `colunas` -> Necessário para cálculos matemáticos relativos ao resizer da GUI Tkinter baseada em `event.width / self.mapa.colunas`.
  - `celulas`, `jogadores`, `bombas` -> Para renderização vetorial no componente Tkinter Canvas, mantendo o Controller livre de gambiarras para interpretar matriz e objetos.
- **Motivação Arquitetural:** O Tkinter Controller e sua UI derivada de View necessitam ter autoridade de _Read Only_ no estado do Modelo do Game a todo tempo, para realizar _Re-Render_ do palco e também poder efetuar tracking da coordenada `x/y` ou instanciar frames visuais de transição, isso não pode ser feito interceptando Strings (stdout) de um método de Console (`__str__`). Para evitar a quebra dessa regra central e evitar o vazamento da View ou dependência de pacotes na camada de regras, expusemos essas propriedades.
