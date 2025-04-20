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
MAX_DEPTH = 10
TIME_LIMIT = 8

CHECKMATE_SCORE = 3000000
CHECKMATE_THRESHOLD = 2900000

TRANSPOSITION_FILE = 'transposition_table.pkl'
HISTORY_TABLE_FILE = 'history_table.pkl'

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

# config.py
KING_POSITION_BONUS_MG = KING_POSITION_BONUS

KING_POSITION_BONUS_EG = [ # Khuyến khích Vua ra trung tâm
    [-50, -30, -10,  0,  0, -10, -30, -50],
    [-30, -10,  20, 30, 30, 20, -10, -30],
    [-10,  20,  40, 50, 50, 40,  20, -10],
    [  0,  30,  50, 55, 55, 50,  30,   0],
    [  0,  30,  50, 55, 55, 50,  30,   0],
    [-10,  20,  40, 50, 50, 40,  20, -10],
    [-30, -10,  20, 30, 30, 20, -10, -30],
    [-50, -30, -10,  0,  0, -10, -30, -50]
]
# Tương tự, có thể tạo PAWN_POSITION_BONUS_MG/EG nếu muốn nhấn mạnh Tốt tiến ở EG
PAWN_POSITION_BONUS_MG = PAWN_POSITION_BONUS # Giữ nguyên cho MG
PAWN_POSITION_BONUS_EG = [ # Ví dụ: tăng mạnh giá trị Tốt ở hàng 6, 7
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [100, 100, 100, 100, 100, 100, 100, 100], # Hàng 7 (index 1)
    [ 80,  80,  80,  80,  80,  80,  80,  80], # Hàng 6
    [ 50,  50,  50,  50,  50,  50,  50,  50],
    [ 20,  20,  20,  30,  30,  20,  20,  20],
    [ 10,  10,  10,  10,  10,  10,  10,  10],
    [  5,   5,   5,   5,   5,   5,   5,   5],
    [  0,   0,   0,   0,   0,   0,   0,   0]
]
# PST cho các quân khác có thể giữ nguyên MG/EG ban đầu
KNIGHT_POSITION_BONUS_MG = KNIGHT_POSITION_BONUS
KNIGHT_POSITION_BONUS_EG = KNIGHT_POSITION_BONUS # Hoặc giảm nhẹ giá trị ở trung tâm
BISHOP_POSITION_BONUS_MG = BISHOP_POSITION_BONUS
BISHOP_POSITION_BONUS_EG = BISHOP_POSITION_BONUS
ROOK_POSITION_BONUS_MG = ROOK_POSITION_BONUS
ROOK_POSITION_BONUS_EG = ROOK_POSITION_BONUS
QUEEN_POSITION_BONUS_MG = QUEEN_POSITION_BONUS
QUEEN_POSITION_BONUS_EG = QUEEN_POSITION_BONUS # Hậu thường yếu đi ở EG

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

PIECE_VALUES_MG = {
    chess.PAWN: 100,
    chess.KNIGHT: 305,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 975,
    chess.KING: 0
}
PIECE_VALUES_EG = {
    chess.PAWN: 120,
    chess.KNIGHT: 300,
    chess.BISHOP: 315, # Giá trị tương đối có thể giảm nhẹ
    chess.ROOK: 530,
    chess.QUEEN: 950,
    chess.KING: 0 # Vua sẽ có giá trị vị trí ở EG
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

# Pawn Structure Weights
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

# Phase value cho từng loại quân
PIECE_PHASE = {
    chess.PAWN: 0,
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4,
    chess.KING: 0  # bỏ qua vì luôn có
}

TOTAL_PHASE = 24  # tổng phase khi full quân
