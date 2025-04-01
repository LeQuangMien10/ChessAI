import pygame
from pygame_chess_api.api import Board, Bishop, Piece
from pygame_chess_api.render import Gui
from mcts import mcts

def function_for_ai(board:Board):
    piece, move = mcts(board)
    print(piece, move)
    piece.move(move)

pygame.init()

board = Board()

# Add Piece.WHITE để thêm người chơi trắng, Piece.BLACK để thêm người chơi đen
gui = Gui(board, (Piece.BLACK, ))

gui.run_pygame_loop(function_for_ai)
'''function_for_ai handles AI turns'''

# ToDo: Parallel MCTS, Transposition Table