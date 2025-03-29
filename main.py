import pygame
from pygame_chess_api.api import Board, Bishop, Piece
from pygame_chess_api.render import Gui
from random import choice

def function_for_ai(board:Board):
    #finding the best move to do... Here we will execute a random move for a random piece as an example
    allowed_moves = None
    while not allowed_moves: #loop until we find some allowed move
        random_piece = choice(board.pieces_by_color[board.cur_color_turn]) #getting a random piece
        allowed_moves = random_piece.get_moves_allowed() #fetching allowed moves for this piece

    random_move = choice(random_piece.get_moves_allowed()) #getting one random move from the allowed moves

    if random_move.special_type == random_move.TO_PROMOTE_TYPE:
        '''if we have to specify a pawn promotion we promote it to a Bishop'''
        random_piece.promote_class_wanted = Bishop

    random_piece.move(random_move) #executing this move

pygame.init()

board = Board()

# Add Piece.WHITE để thêm người chơi trắng, Piece.BLACK để thêm người chơi đen
gui = Gui(board, (Piece.WHITE, ))

gui.run_pygame_loop(function_for_ai)
'''function_for_ai handles AI turns'''