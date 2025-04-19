import chess
import pygame

# Size
SQUARE_SIZE = 64
BOARD_SIZE = SQUARE_SIZE * 8
MOVE_HIGHLIGHT = (255, 255, 0, 128)
LAST_MOVE_HIGHLIGHT = (255, 255, 128, 128)
# (255, 182, 193, 128)

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
HISTORY_TABLE_FILE = 'history_table.pkl'

LMR_MIN_DEPTH = 3
LMR_MIN_MOVE_INDEX = 3
LMR_BASE_REDUCTION = 1

# Board

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

#Pawn Structure Weights
ISOLATED_PAWN_PENALTY = 0.5
DOUBLED_PAWN_PENALTY = 0.3
BACKWARD_PAWN_PENALTY = 0.4
PASSED_PAWN_BONUS = 0.5
PAWN_ISLAND_PENALTY = 0.2

MOBILITY_WEIGHTS = {
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 1.5,
    chess.QUEEN: 0.75,
    chess.KING: 0.75,
    chess.PAWN: 0.0,  # thường bỏ qua mobility của tốt
}

KING_CENTER_PENALTY = 10  # mỗi đơn vị lệch khỏi trung tâm
KING_ATTACKED_SQUARE_PENALTY = 20  # mỗi ô quanh vua bị tấn công
PAWN_SHIELD_BONUS = 15  # mỗi tốt quanh vua
CASTLING_RIGHTS_BONUS = 30  # có quyền nhập thành


TEMPO_BONUS = 10  # hoặc 10, tùy engine của bạn



TRAPPED_PIECE_PENALTY = {
    chess.KNIGHT: 80,
    chess.BISHOP: 60,
    chess.ROOK: 100,
}


SPACE_WEIGHT = 1.5

# Evaluation parameters for different game phases
EVAL_PARAMS = {
    'opening': {
        'center_control': 10,
        'king_safety': 5,
        'mobility': 2,
        'pawn_structure_isolated': 20,
        'pawn_structure_doubled': 10,
        'pawn_structure_passed': 10,
        'check_penalty': 20,
        'material': 9.0,
        'piece_square_tables': 1,
        'pawn_structure': 0.8,
        'mobility': 0.7,
        'king_safety': 1.5,
        'tempo': 0.3,
        'trapped_pieces': 0.6,
        'space': 0.5,
        'connectivity': 0.4,
    },
    'middlegame': {
        'center_control': 15,
        'king_safety': 8,
        'mobility': 3,
        'pawn_structure_isolated': 25,
        'pawn_structure_doubled': 15,
        'pawn_structure_passed': 30,
        'check_penalty': 15,
        'material': 9.0,
        'piece_square_tables': 1,
        'pawn_structure': 0.8,
        'mobility': 0.7,
        'king_safety': 1.5,
        'tempo': 0.3,
        'trapped_pieces': 0.6,
        'space': 0.5,
        'connectivity': 0.4,
    },
    'endgame': {
        'center_control': 5,
        'king_safety': 2,
        'mobility': 1,
        'pawn_structure_isolated': 30,
        'pawn_structure_doubled': 20,
        'pawn_structure_passed': 50,
        'check_penalty': 10,
        'material': 6.0, # Material importance decreases in endgame
        'piece_square_tables': 1.2, # Piece-square tables become more important
        'pawn_structure': 1.0, # Pawn structure even more critical in endgame
        'mobility': 0.5,
        'king_safety': 1.0, # King safety less of a concern when material is reduced
        'tempo': 0.2,
        'trapped_pieces': 0.4,
        'space': 0.3,
        'connectivity': 0.2,
    }
}