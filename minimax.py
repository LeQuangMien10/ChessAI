import pickle
import time
import os

import chess

import config
from config import *
from transposition_table import compute_zorbist_hash

# Load transposition table nếu có
if os.path.exists(TRANSPOSITION_FILE):
    with open(TRANSPOSITION_FILE, 'rb') as f:
        transposition_table = pickle.load(f)
else:
    transposition_table = {}

def save_transposition_table(min_depth=3):
    # Đọc bảng cũ nếu có
    old_table = {}
    if os.path.exists(TRANSPOSITION_FILE):
        with open(TRANSPOSITION_FILE, "rb") as f:
            old_table = pickle.load(f)

    # Gộp bảng cũ và mới, ưu tiên entry có depth cao hơn
    merged_table = old_table.copy()
    for k, v in transposition_table.items():
        if (k not in merged_table) or (v["depth"] > merged_table[k]["depth"]):
            merged_table[k] = v

    # Lọc theo độ sâu
    filtered_table = {
        k: v for k, v in merged_table.items() if v["depth"] >= min_depth
    }

    # Ghi đè sau khi merge
    with open(TRANSPOSITION_FILE, "wb") as f:
        pickle.dump(filtered_table, f)


def evaluate_board(board_):
    if board_.is_checkmate():
        return -float('inf') if DEFAULT_DEPTH % 2 == 1 else float('inf')
    if board_.is_stalemate() or board_.is_insufficient_material():
        return 0

    evaluation = 0

    # 1. Trừ điểm nếu bị chiếu
    if board_.is_check():
        evaluation -= 20

    # 2. Trung tâm bàn cờ
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    for square in center_squares:
        piece = board_.piece_at(square)
        if piece:
            if piece.color == board_.turn:
                evaluation += 10
            else:
                evaluation -= 10

    # 3. Giá trị + bonus vị trí
    for square in chess.SQUARES:
        piece = board_.piece_at(square)
        if piece:
            value = config.PIECE_VALUES[piece.piece_type]

            index = square if piece.color == chess.WHITE else chess.square_mirror(square)

            if piece.piece_type == chess.PAWN:
                positional_bonus = config.PAWN_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.KNIGHT:
                positional_bonus = config.KNIGHT_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.BISHOP:
                positional_bonus = config.BISHOP_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.ROOK:
                positional_bonus = config.ROOK_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.QUEEN:
                positional_bonus = config.QUEEN_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.KING:
                positional_bonus = config.KING_POSITION_BONUS[7 - index // 8][index % 8]
            else:
                positional_bonus = 0

            total = value + positional_bonus
            evaluation += total if piece.color == board_.turn else -total

            # 4. Phạt quân treo
            attackers = board_.attackers(not piece.color, square)
            defenders = board_.attackers(piece.color, square)
            if attackers and not defenders:
                penalty = value // 2
                evaluation -= penalty if piece.color == board_.turn else -penalty

    # 5. Thưởng bảo vệ vua
    for color in [chess.WHITE, chess.BLACK]:
        king_square = board_.king(color)
        if king_square:
            defenders = len(board_.attackers(color, king_square))
            if color == board_.turn:
                evaluation += defenders * 5
            else:
                evaluation -= defenders * 5

    return evaluation


def minimax(board, depth, alpha, beta, is_maximizing):
    key = compute_zorbist_hash(board)
    if key in transposition_table and transposition_table[key]['depth'] >= depth:
        return transposition_table[key]['value']

    if depth == 0 or board.is_game_over():
        value = -evaluate_board(board) if DEFAULT_DEPTH % 2 == 1 else evaluate_board(board)
        transposition_table[key] = {'value': value, 'depth': depth}
        return value

    if is_maximizing:
        max_value = -float('inf')
        for move in order_moves(board):
            board.push(move)
            evaluation = minimax(board, depth - 1, alpha, beta, not is_maximizing)
            board.pop()

            max_value = max(max_value, evaluation)
            alpha = max(alpha, max_value)
            if alpha >= beta:
                break
        transposition_table[key] = {'value': max_value, 'depth': depth}
        return max_value
    else:
        min_value = float('inf')
        for move in order_moves(board):
            board.push(move)
            evaluation = minimax(board, depth - 1, alpha, beta, not is_maximizing)
            board.pop()

            min_value = min(min_value, evaluation)
            beta = min(beta, min_value)
            if beta <= alpha:
                break
        transposition_table[key] = {'value': min_value, 'depth': depth}
        return min_value


def get_best_move(board, depth=3):
    start_time = time.time()

    best_move = None
    # if board.turn == chess.WHITE:
    #     best_value = -float('inf')
    #     is_maximizing = True
    # else:
    #     best_value = float('inf')
    #     is_maximizing = False
    best_value = -float('inf')
    is_maximizing = True

    for move in order_moves(board):
        # Kiểm tra nếu đi nước này sẽ dẫn đến hòa 3 lần lặp
        if is_threefold_repetition_if_move(board, move):
            white_score, black_score = material_score(board)
            print("white: " + str(white_score))
            print("black: " + str(black_score))

            if board.turn == chess.BLACK:
                if black_score >= white_score + 100:
                    continue  # Đen đang lợi thế → tránh hòa
                elif black_score <= white_score - 200:
                    return move  # Đen thua nặng → chấp nhận hòa
            else:
                if white_score >= black_score + 100:
                    continue
                elif white_score <= black_score - 200:
                    return move

        # Đánh giá nước đi thông qua minimax
        board.push(move)
        evaluation = minimax(board, depth - 1, float('-inf'), float('inf'), not is_maximizing)
        board.pop()

        # if board.turn == chess.WHITE and evaluation > best_value:
        #     best_value = evaluation
        #     best_move = move
        # elif board.turn == chess.BLACK and evaluation < best_value:
        #     best_value = evaluation
        #     best_move = move
        if evaluation > best_value:
            best_value = evaluation
            best_move = move

    elapsed_time = time.time() - start_time
    print(f"Time: {elapsed_time: .2f} seconds")

    return best_move


def is_important_move(board, move):
    # Nước chiếu
    if board.gives_check(move):
        return True

    # Nước phong cấp
    if move.promotion is not None:
        return True

    # Nước ăn quân
    if board.is_capture(move):
        captured_piece = board.piece_at(move.to_square)
        moving_piece = board.piece_at(move.from_square)
        if captured_piece and moving_piece:
            captured_value = config.PIECE_VALUES[captured_piece.piece_type]
            moving_value = config.PIECE_VALUES[moving_piece.piece_type]
            if captured_value >= moving_value:
                return True

    # Nước đe dọa quân mạnh
    board.push(move)
    attacked_squares = board.attacks(move.to_square)
    for sq in attacked_squares:
        target_piece = board.piece_at(sq)
        if target_piece and target_piece.color != board.turn:
            value = config.PIECE_VALUES[target_piece.piece_type]
            if value >= config.PIECE_VALUES[chess.ROOK]:
                board.pop()
                return True
    board.pop()

    return False


def order_moves(board):
    moves = list(board.legal_moves)

    def move_score(move):
        score = 0

        # Ưu tiên cao nếu nước đi được đánh giá là quan trọng bởi is_important_move
        if is_important_move(board, move):
            score += 1000  # Giá trị lớn để đảm bảo nước quan trọng đứng đầu

        # Logic hiện có: ưu tiên nước ăn quân
        if board.is_capture(move):
            captured = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if captured and attacker:
                score += 10 * config.PIECE_VALUES[captured.piece_type] - config.PIECE_VALUES[attacker.piece_type]
            else:
                score += 50  # Ưu tiên nước bắt thường

        # Logic hiện có: ưu tiên nước phong cấp
        if move.promotion:
            score += 900

        return -score  # Đảo dấu để sort tăng → highest score trước

    moves.sort(key=move_score)
    return moves

# Hàm tránh bị hòa khi đang có lợi thế
def is_threefold_repetition_if_move(board, move):
    board_copy = board.copy()
    board_copy.push(move)
    return board_copy.is_repetition(3) #3 lần lặp => Có thể cầu hòa, 5 lần lặp => Bắt buộc hòa

#Hàm tính giá trị quân còn lại trên bàn
def material_score(board):
    white_score = 0
    black_score = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = config.PIECE_VALUES[piece.piece_type]
            if piece.color == chess.WHITE:
                white_score += value
            else:
                black_score += value

    return white_score, black_score
