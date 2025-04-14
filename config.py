import chess
import pygame

# Size
SQUARE_SIZE = 64
BOARD_SIZE = SQUARE_SIZE * 8
MOVE_HIGHLIGHT = (255, 255, 0, 128)

# Color
WHITE = (238, 238, 210)
BLACK = (118, 150, 86)
HIGHLIGHT = (186, 202, 68)

# Menu
TWO_PLAYERS = 0
TWO_AIS = 1
PLAYER_VS_AI = 2
AI_VS_PLAYER = 3

# Game
DEFAULT_DEPTH = 4
TRANSPOSITION_FILE = 'transposition_table.pkl'

# Board

# Test tránh hòa do LẶP NƯỚC 1 (2 xe vs vua)
FEN_STRING_THREEFOLD_REPEAT_1 = "8/8/8/8/1k6/8/r1r5/K7 w - - 0 1"

# Test tránh hòa do LẮP NƯỚC 2 (vua vs Mã+Xe)
FEN_STRING_THREEFOLD_REPEAT_2 = "1K6/8/8/8/8/kn6/8/2r5 w - - 0 1"

# Test endgame 1 (Vua + Hậu vs Vua)
FEN_STRING_ENDGAME_1 = '8/8/5k2/8/8/3Q4/4K3/8 w - - 0 1'

# Test endgame 2 (Vua + Tốt vs Vua)
FEN_STRING_ENDGAME_2 = '8/8/5k2/8/8/5P2/4K3/8 w - - 0 1'

# Test endgame 3 (Vua + 2 Tượng vs Vua)
FEN_STRING_ENDGAME_3 = '1k6/8/8/8/8/8/6B1/1K2B3 w HAha - 0 1'

#Test endgame 4 (Vua + Xe vs Vua)
FEN_STRING_ENDGAME_4 = "6k1/8/8/8/R7/8/8/4K3 w - - 0 1"

#Test endgame 5 (Vua + Xe + Tốt vs Vua)
FEN_STRING_ENDGAME_5 = "6k1/4p3/8/8/r7/8/8/4K3 w - - 0 1"

#Test endgame 6 (Vua + Mã + Tượng vs Vua + Tượng) (Thế hòa)
FEN_STRING_ENDGAME_6 = "8/8/4kb2/8/8/8/3B4/3K1N2 w - - 0 1"

#Test endgame 7 (Vua + Tượng + Tốt vs Vua)
FEN_STRING_ENDGAME_7 = "1k6/1p4b1/8/8/8/8/8/4K3 w - - 0 1"

#Test endgame 8 (Vua + Mã + Tốt vs Vua)
FEN_STRING_ENDGAME_8 = "1k3n2/1p6/8/8/8/8/8/4K3 w - - 0 1"

# Test blockage
FEN_STRING_BLOCKAGE = '5k2/p3p1p1/8/8/3R4/8/1K6/8 w - - 0 1'

# Test mate in 5
FEN_STRING_MATE_IN_FIVE = '4rb1k/2pqn2p/6pn/ppp3N1/P1QP2b1/1P2p3/2B3PP/B3RRK1 w - - 0 1'

FEN_STRING_MATE_IN_ONE = 'r1bqkb1r/pppnp1pp/2n2p2/4P3/2BP4/2N5/PP3PPP/R1BQK1NR w KQkq - 0 1'

PAWN_POSITION_BONUS = [
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [ 5,  5, 10, 25, 25, 10,  5,  5],
    [ 0,  0,  0, 20, 20,  0,  0,  0],
    [ 5, -5,-10,  0,  0,-10, -5,  5],
    [ 5, 10, 10,-20,-20, 10, 10,  5],
    [ 0,  0,  0,  0,  0,  0,  0,  0]
]

KNIGHT_POSITION_BONUS = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   0,   0,   0, -20, -40],
    [-30,   0,  10,  15,  15,  10,   0, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-30,   0,  15,  20,  20,  15,   0, -30],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50]
]

BISHOP_POSITION_BONUS = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,  10,  10,   5,   0, -10],
    [-10,   5,   5,  10,  10,   5,   5, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,  10,  10,  10,  10,  10,  10, -10],
    [-10,   5,   0,   0,   0,   0,   5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20]
]

ROOK_POSITION_BONUS = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [  5,  10,  10,  10,  10,  10,  10,   5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [  0,   0,   0,   5,   5,   0,   0,   0]
]

QUEEN_POSITION_BONUS = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [ -5,   0,   5,   5,   5,   5,   0,  -5],
    [  0,   0,   5,   5,   5,   5,   0,  -5],
    [-10,   5,   5,   5,   5,   5,   0, -10],
    [-10,   0,   5,   0,   0,   0,   0, -10],
    [-20, -10, -10,  -5,  -5, -10, -10, -20]
]

KING_POSITION_BONUS = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [ 20,  20,   0,   0,   0,   0,  20,  20],
    [ 20,  30,  10,   0,   0,   10, 30,  20]
]

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

CENTER_MANHATTAN_DISTANCE = [
    [6, 5, 4, 3, 3, 4, 5, 6],
    [5, 4, 3, 2, 2, 3, 4, 5],
    [4, 3, 2, 1, 1, 2, 3, 4],
    [3, 2, 1, 0, 0, 1, 2, 3],
    [3, 2, 1, 0, 0, 1, 2, 3],
    [4, 3, 2, 1, 1, 2, 3, 4],
    [5, 4, 3, 2, 2, 3, 4, 5],
    [6, 5, 4, 3, 3, 4, 5, 6]
]