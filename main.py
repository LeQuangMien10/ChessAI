import pygame
from pygame_chess_api.api import Board, Piece
from pygame_chess_api.render import Gui
from mcts import parallel_mcts

def function_for_ai(board:Board):
    piece, move = parallel_mcts(board, num_workers=6)
    print(piece, move)
    piece.move(move)

if __name__ == "__main__":  # Đảm bảo mã khởi tạo game nằm trong khối này
    pygame.init()

    board = Board()

    # Add Piece.WHITE để thêm người chơi trắng, Piece.BLACK để thêm người chơi đen
    gui = Gui(board, (Piece.WHITE, ))

    gui.run_pygame_loop(function_for_ai)
'''function_for_ai handles AI turns'''
