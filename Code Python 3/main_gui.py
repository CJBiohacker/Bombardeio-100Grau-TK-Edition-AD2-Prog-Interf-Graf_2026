import tkinter as tk
from view import GameView
from controller import GameController

def main():
    root = tk.Tk()
    
    # Inicializa o Controller passando a classe de View pura por injeção
    app = GameController(root, GameView)
    
    # Start no Event Loop do SO / Tkinter (Substituindo o sys.stdin e while true)
    root.mainloop()

if __name__ == "__main__":
    main()
