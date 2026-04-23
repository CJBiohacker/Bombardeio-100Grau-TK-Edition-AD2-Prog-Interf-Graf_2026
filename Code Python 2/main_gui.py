#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import Tkinter as tk
from view import GameView
from controller import GameController

def main():
    root = tk.Tk()
    app = GameController(root, GameView)
    root.mainloop()

if __name__ == "__main__":
    main()
