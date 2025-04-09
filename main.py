import pygame
from pygame_chess_api.api import Board, Piece, Queen, King, Bishop, Rook, Pawn, Knight
from pygame_chess_api.render import Gui
from minimax import get_best_move

"""Tạo bàn cờ từ danh sách các quân cờ"""
def create_board_from_pieces(pieces_data):
    # Tạo bàn cờ trống trước
    custom_board = Board(pieces_by_pos={})

    for pos, piece_type, color in pieces_data:
        custom_board.pieces_by_pos[pos] = piece_type(color, pos, custom_board)

    # Khởi tạo các biến cần thiết cho bàn cờ
    custom_board._init_vars()
    return custom_board

def function_for_ai(board: Board) -> None:
    """Function to be called by the GUI for AI moves"""
    piece, move = get_best_move(board, depth=3)  # You can adjust the depth here
    print(f"AI move: {piece} to {move.target}")
    piece.move(move)

if __name__ == "__main__":
    pygame.init()

    board = Board()

    # board = create_board_from_pieces(
    #     [
    #         ((6, 7), King, Piece.BLACK),  # Vua đen ở g1
    #         ((0, 0), Rook, Piece.WHITE),  # Xe trắng ở a8
    #         ((6, 5), King, Piece.WHITE),  # Vua trắng ở e1
    #     ]
    # )

    # board = create_board_from_pieces(
    #     [
    #         ((3, 0), King, Piece.BLACK),  # Vua đen ở d8
    #         ((2, 0), Rook, Piece.BLACK),  # Xe đen ở c8
    #         ((4, 1), Bishop, Piece.BLACK), # Tượng đen ở e7
    #         ((3, 3), Pawn, Piece.BLACK), # Tốt đen ở d5
    #         ((5, 2), Pawn, Piece.BLACK),  # Tốt đen ở f6
    #         ((6, 3), Pawn, Piece.BLACK),  # Tốt đen ở g5
    #         ((7, 6), Pawn, Piece.BLACK),  # Tốt đen ở h2
    #         ((5, 1), King, Piece.WHITE),  # Vua trắng ở f7
    #         ((0, 1), Rook, Piece.WHITE),  # Xe trắng ở a7
    #         ((4, 2), Pawn, Piece.WHITE),  # Tốt trắng ở e6
    #         ((6, 4), Pawn, Piece.WHITE),  # Tốt trắng ở g4
    #     ]
    # )

    # Add Piece.WHITE để thêm người chơi trắng, Piece.BLACK để thêm người chơi đen
    gui = Gui(board, (Piece.BLACK, ))

    gui.run_pygame_loop(function_for_ai)
'''function_for_ai handles AI turns'''
