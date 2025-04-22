import chess
import pygame

# Size
SQUARE_SIZE = 64
BOARD_SIZE = SQUARE_SIZE * 8
SCREEN_WIDTH = BOARD_SIZE + 200
SCREEN_HEIGHT = BOARD_SIZE
MOVE_HIGHLIGHT = (255, 255, 0, 128)
LAST_MOVE_HIGHLIGHT = (255, 255, 128, 128)
# (255, 182, 193, 128)

# Color
WHITE = (238, 238, 210)
BLACK = (48, 76, 128)
HIGHLIGHT = (100, 150, 200)

# Menu
TWO_PLAYERS = 0
TWO_AIS = 1
PLAYER_VS_AI = 2
AI_VS_PLAYER = 3

# Game
MAX_DEPTH = 1
TIME_LIMIT = 1
STOCKFISH_LEVEL = 5
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

# --- King Safety ---
# MG: Phạt nặng Vua ở giữa, thưởng Tốt che chắn
# EG: Thưởng Vua ở giữa, không cần Tốt che chắn
KING_ATTACKED_SQUARE_PENALTY_MG = 25 # Phạt cho mỗi đe dọa gần Vua (MG)
KING_ATTACKED_SQUARE_PENALTY_EG = 10 # Phạt nhẹ hơn ở EG
PAWN_SHIELD_BONUS_MG = 18           # Bonus cho mỗi Tốt che chắn (MG)
PAWN_SHIELD_BONUS_EG = 0            # Không cần Tốt che chắn ở EG
CASTLING_RIGHTS_BONUS = 25          # Giữ nguyên bonus quyền nhập thành (chỉ ảnh hưởng MG phase)


# --- Passed Pawns ---
# Bonus tăng mạnh theo rank ở EG
# Index 0 là rank 1, index 7 là rank 8 (theo perspective của Trắng)
# Nên bonus ở rank 1 và 8 thường là 0 vì Tốt không thể là passed pawn ở đó
PASSED_PAWN_BONUS_MG = [0, 10, 15, 20, 30, 45, 65, 0]
PASSED_PAWN_BONUS_EG = [0, 25, 40, 60, 90, 130, 180, 0]

# --- Rooks on Files ---
ROOK_OPEN_FILE_BONUS_MG = 20
ROOK_OPEN_FILE_BONUS_EG = 30
ROOK_SEMI_OPEN_FILE_BONUS_MG = 10 # Cột chỉ có Tốt đối phương
ROOK_SEMI_OPEN_FILE_BONUS_EG = 15
ROOK_ON_7TH_BONUS_MG = 25         # Xe ở hàng 7 (hoặc 2 cho Đen)
ROOK_ON_7TH_BONUS_EG = 40


EVAL_WEIGHTS = {
    'material': 1.00,             # cơ bản, nên là trọng số chuẩn
    'piece_square_tables': 0.20,  # PST chỉ là điều chỉnh vị trí
    'passed_pawn': 0.40,
    'rook_files': 0.25,
    'pawn_structure': 0.25,       # khá quan trọng (tốt cô lập, backward, island)
    'mobility': 0.20,             # ảnh hưởng chiến lược trung cuộc
    'king_safety': 0.50,          # rất quan trọng trung cuộc
    'trapped_pieces': 0.15,       # nhẹ, vì hiếm gặp
    'space': 0.25,                # quan trọng trung cuộc, nhất là với minor pieces
    'mop_up': 0.30                # dùng chủ yếu ở endgame
}

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

Q_HASH_MOVE_SCORE = 100_000 # Nếu bạn quyết định dùng TT trong QSearch
Q_PROMOTION_QUEEN_SCORE = 90_000
Q_PROMOTION_OTHER_BASE = 85_000
Q_CAPTURE_GOOD_SEE_BASE = 80_000 # Base cho capture có SEE >= 0
Q_CAPTURE_BAD_SEE_BASE = 30_000  # Base cho capture có SEE < 0 (nhưng > ngưỡng)
