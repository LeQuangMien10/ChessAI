import pickle
import time
import os
import chess.syzygy

import config
from config import *
from config import ai_color
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
        with open(TRANSPOSITION_FILE, "rb") as file:
            old_table = pickle.load(file)

    # Gộp bảng cũ và mới, ưu tiên entry có value cao hơn
    merged_table = old_table.copy()
    for k, v in transposition_table.items():
        if (k not in merged_table) or (v["value"] > merged_table[k]["value"]):
            merged_table[k] = v

    # Lọc theo độ sâu
    filtered_table = {
        k: v for k, v in merged_table.items() if v["depth"] >= min_depth
    }

    # Ghi đè sau khi merge
    with open(TRANSPOSITION_FILE, "wb") as file:
        pickle.dump(filtered_table, file)


def manhattan_distance(square1, square2):
    """
    Tính khoảng cách manhattan giữa hai ô
    :param square1: ô thứ nhất
    :param square2: ô thứ hai
    :return: khoảng cách manhattan
    """
    file1, rank1 = chess.square_file(square1), chess.square_rank(square1)
    file2, rank2 = chess.square_file(square2), chess.square_rank(square2)
    return abs(file1 - file2) + abs(rank1 - rank2)


def mop_up_evaluation(board, ai_color):
    """
    Tính mop-up evaluation cho giai đoạn end game (https://www.chessprogramming.org/Mop-up_Evaluation)
    :param ai_color: màu cờ AI điều khiển
    :param board: bàn cờ
    :return: giá trị mop-up
    """
    evaluation = 0
    # Vị trí vua
    king_square = board.king(ai_color)
    opponent_king_square = board.king(not ai_color)
    if king_square and opponent_king_square:
        # 1. Thưởng vua đối phương xa trung tâm
        center_manhattan_distance = config.CENTER_MANHATTAN_DISTANCE[7 - opponent_king_square // 8][
            opponent_king_square % 8]
        center_bonus = 4.7 * center_manhattan_distance
        evaluation += center_bonus

        # 2. Thưởng hai vua gần nhau
        kings_distance = manhattan_distance(king_square, opponent_king_square)
        king_proximity_bonus = 1.6 * (14 - kings_distance)
        evaluation += king_proximity_bonus

    return evaluation


def evaluate_board(board_, ai_color):
    """
    Đánh giá bàn cờ
    :param ai_color: màu cờ AI điều khiển
    :param board_: bàn cờ
    :return: Giá trị bàn cờ
    """

    if board_.is_checkmate():
        return -float('inf') if board_.turn == ai_color else float('inf')
    if board_.is_stalemate() or board_.is_insufficient_material():
        return 0

    evaluation = 0
    is_endgame_phase = is_endgame(board_)

    # 1. Trừ điểm nếu bị chiếu
    if board_.is_check():
        evaluation -= 20 if not is_endgame_phase else 10

    # 2. Trung tâm bàn cờ
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    for square in center_squares:
        piece = board_.piece_at(square)
        if piece:
            if piece.color == ai_color:
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
                # Được tính bình thường khi không phải endgame, nếu là endgame thì sẽ được tính sau.
                positional_bonus = config.KING_POSITION_BONUS[7 - index // 8][index % 8] if not is_endgame_phase else 0
            else:
                positional_bonus = 0

            total = value + positional_bonus
            evaluation += total if piece.color == ai_color else -total

            # 4. Phạt quân treo
            attackers = board_.attackers(not piece.color, square)
            defenders = board_.attackers(piece.color, square)
            if attackers and not defenders:
                penalty = value // 2
                evaluation -= penalty if piece.color == ai_color else -penalty

    # 5. Thưởng bảo vệ vua
    for color in [chess.WHITE, chess.BLACK]:
        king_square = board_.king(color)
        if king_square:
            defenders = len(board_.attackers(color, king_square))
            bonus = defenders * 5 if not is_endgame_phase else defenders * 2
            if color == ai_color:
                evaluation += bonus
            else:
                evaluation -= bonus

    # 6. Mop-up evaluation
    if is_endgame_phase:
        evaluation += mop_up_evaluation(board_, ai_color)

    return evaluation


def negamax(board, depth, alpha, beta, color):
    key = compute_zorbist_hash(board)
    if key in transposition_table and transposition_table[key]['depth'] >= depth:
        return transposition_table[key]['value']

    if depth == 0 or board.is_game_over():
        value = evaluate_board(board, ai_color=board.turn if color == 1 else not board.turn) * color
        transposition_table[key] = {'value': value, 'depth': depth}
        return value

    max_value = -float('inf')
    for move in order_moves(board):
        board.push(move)
        value = -negamax(board, depth - 1, -beta, -alpha, -color)
        board.pop()

        max_value = max(max_value, value)
        alpha = max(value, alpha)
        if alpha >= beta:
            break

    transposition_table[key] = {'value': max_value, 'depth': depth}
    return max_value


def count_pieces(board):
    """Đếm số quân cờ trên bàn (bao gồm cả vua)."""
    return sum(len(board.pieces(piece_type, color))
               for piece_type in chess.PIECE_TYPES
               for color in [chess.WHITE, chess.BLACK])


def evaluate_with_tablebase(board, ai_color=chess.WHITE):
    import chess.syzygy
    with chess.syzygy.open_tablebase("3-4-5") as tablebase:
        try:
            piece_count = len(board.piece_map())
            print(f"Số quân: {piece_count}")

            wdl_raw = tablebase.probe_wdl(board)
            dtz = tablebase.probe_dtz(board)

            # Chuyển về góc nhìn AI
            if board.turn == ai_color:
                wdl = wdl_raw
            else:
                wdl = -wdl_raw

            print(f"✅ File hợp lệ. WDL (raw): {wdl_raw} | WDL (AI): {wdl} | DTZ: {dtz}")

            evaluation = {
                2: 10000,  # AI thắng
                1: 5000,
                0: 0,
                -1: -5000,
                -2: -10000  # AI thua
            }.get(wdl, 0)

            if dtz is not None:
                evaluation += max(0, 100 - abs(dtz)) * 0.5
                print("syzygy eval:", evaluation)

            return evaluation

        except chess.syzygy.MissingTableError:
            print("❌ Thiếu file tablebase.")
            return mop_up_evaluation(board, ai_color)
        except Exception as e:
            print("❌ Lỗi khác:", e)
            return mop_up_evaluation(board, ai_color)


def has_pawn(board, color):
    return any(piece.piece_type == chess.PAWN and piece.color == color for piece in board.piece_map().values())


def get_best_move(board, depth=3, ai_color_=chess.WHITE):
    start_time = time.time()

    # Đếm số quân cờ
    piece_count = count_pieces(board)

    best_move = None
    best_value = -float('inf')
    color = 1 if board.turn == ai_color_ else -1

    for move in order_moves(board):
        # Kiểm tra nếu đi nước này sẽ dẫn đến hòa 3 lần lặp
        if is_threefold_repetition_if_move(board, move):
            white_score, black_score = material_score(board)
            print("white: " + str(white_score))
            print("black: " + str(black_score))

            if ai_color_ == chess.BLACK:
                if black_score >= white_score + 100:
                    continue  # Đen đang lợi thế → tránh hòa
                elif black_score <= white_score - 200:
                    return move  # Đen thua nặng → chấp nhận hòa
            else:
                if white_score >= black_score + 100:
                    continue
                elif white_score <= black_score - 200:
                    return move

        # Đánh giá nước đi
        board.push(move)
        # Dùng Tablebase cho ≤ 5 quân, nếu không thì Minimax
        if piece_count <= 5 and not has_pawn(board, ai_color_):
            evaluation = evaluate_with_tablebase(board, ai_color_)
        else:
            evaluation = -negamax(board, depth - 1, -float('inf'), float('inf'), -color)

        board.pop()

        if evaluation >= best_value:
            best_value = evaluation
            best_move = move

    print(f"Time: {time.time() - start_time:.2f}s")
    san = board.san(best_move)
    print(f"Best move: {san} | Value: {best_value:.2f}")
    return best_move


# Hàm move_score (tách ra từ order_moves để tái sử dụng)
def move_score(board, move):
    score = 0
    if is_important_move(board, move):
        score += 1000

    if board.is_capture(move):
        captured = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if captured and attacker:
            score += 10 * config.PIECE_VALUES[captured.piece_type] - config.PIECE_VALUES[attacker.piece_type]
        else:
            score += 50

    if move.promotion:
        score += 900

    if board.gives_check(move):
        score += 100

    return score


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

    # Tính điểm cho từng nước đi
    scored_moves = [(move, move_score(board, move)) for move in moves]

    # Sắp xếp theo điểm số, điểm cao nhất đứng đầu
    moves.sort(key=lambda move: next(s for m, s in scored_moves if m == move), reverse=True)

    return moves


# Hàm tránh bị hòa khi đang có lợi thế
def is_threefold_repetition_if_move(board, move):
    board_copy = board.copy()
    board_copy.push(move)
    return board_copy.is_repetition(2)  # 3 lần lặp => Có thể cầu hòa, 5 lần lặp => Bắt buộc hòa


# Hàm tính giá trị quân còn lại trên bàn
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


def is_endgame(board):
    """
    Kiểm tra xem bàn cờ có tổng giá trị các quân cờ nhỏ hơn 1300
    hoặc cả hai bên không còn quân hậu hay xe nào
    hoặc là bên AI có đủ quân để thắng
    :param board: bàn cờ
    :return: True nếu là end game, False nếu ngược lại
    """
    white_material = black_material = 0
    has_major_piece = False

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = config.PIECE_VALUES[piece.piece_type]
            if piece.color == chess.WHITE:
                white_material += value
            else:
                black_material += value
            if piece.piece_type in [chess.QUEEN, chess.ROOK]:
                has_major_piece = True
    total_material = white_material + black_material
    if ai_color == chess.WHITE and black_material <= 100 and white_material >= 300:
        return True
    if ai_color == chess.BLACK and white_material <= 100 and black_material >= 300:
        return True
    return total_material < 1200 or not has_major_piece
