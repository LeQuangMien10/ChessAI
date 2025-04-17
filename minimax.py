import pickle
import time
import os
import chess.syzygy
from concurrent.futures import ProcessPoolExecutor, as_completed
import config
from config import *
from transposition_table import compute_zorbist_hash
import multiprocessing

KILLER_MOVES = [{} for _ in range(DEFAULT_DEPTH + 1)]

# List to store move times
MOVE_TIMES = []

HISTORY_TABLE = {}
if os.path.exists(HISTORY_TABLE_FILE):
    with open(HISTORY_TABLE_FILE, 'rb') as f:
        HISTORY_TABLE = pickle.load(f)

# Load transposition table nếu có
if os.path.exists(TRANSPOSITION_FILE):
    with open(TRANSPOSITION_FILE, 'rb') as f:
        transposition_table = pickle.load(f)
else:
    transposition_table = {}


def save_history_table(min_score=100):
    filtered_table = {k: v for k, v in HISTORY_TABLE.items() if v >= min_score}
    with open(HISTORY_TABLE_FILE, "wb") as file:
        pickle.dump(filtered_table, file)


def decay_history_table(factor=0.5):
    global HISTORY_TABLE
    HISTORY_TABLE = {k: int(v * factor) for k, v in HISTORY_TABLE.items()}


def save_transposition_table(min_depth=3):
    if multiprocessing.current_process().name != "MainProcess":
        return
    try:
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
    except Exception as e:
        print(f"Lỗi khi lưu Transposition Table: {e}")


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


def mop_up_evaluation(board, ai_color_):
    """
    Tính mop-up evaluation cho giai đoạn end game (https://www.chessprogramming.org/Mop-up_Evaluation)
    :param ai_color_: màu cờ AI điều khiển
    :param board: bàn cờ
    :return: giá trị mop-up
    """
    evaluation = 0
    # Vị trí vua
    king_square = board.king(ai_color_)
    opponent_king_square = board.king(not ai_color_)
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


def evaluate_board(board_, ai_color_):
    """
    Đánh giá bàn cờ
    :param ai_color_: màu cờ AI điều khiển
    :param board_: bàn cờ
    :return: Giá trị bàn cờ
    """

    if board_.is_checkmate():
        return -float('inf') if board_.turn == ai_color_ else float('inf')
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
            if piece.color == ai_color_:
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
            evaluation += total if piece.color == ai_color_ else -total

            # 4. Phạt quân treo
            attackers = board_.attackers(not piece.color, square)
            defenders = board_.attackers(piece.color, square)
            if attackers and not defenders:
                penalty = value // 2
                evaluation -= penalty if piece.color == ai_color_ else -penalty

    # 5. Thưởng bảo vệ vua
    for color in [chess.WHITE, chess.BLACK]:
        king_square = board_.king(color)
        if king_square:
            defenders = len(board_.attackers(color, king_square))
            bonus = defenders * 5 if not is_endgame_phase else defenders * 2
            if color == ai_color_:
                evaluation += bonus
            else:
                evaluation -= bonus

    # 6. Mop-up evaluation
    if is_endgame_phase:
        evaluation += mop_up_evaluation(board_, ai_color_)

    return evaluation


def negamax(board, depth, alpha, beta, color):
    key = compute_zorbist_hash(board)
    if key in transposition_table and transposition_table[key]['depth'] >= depth:
        return transposition_table[key]['value']

    if depth == 0 or board.is_game_over():
        value = evaluate_board(board, ai_color_=board.turn if color == 1 else not board.turn) * color
        transposition_table[key] = {'value': value, 'depth': depth}
        return value

    max_value = -float('inf')
    for move in order_moves(board, depth):
        # Phát hiện chiếu hết sau 50
        if len(board.move_stack) >= 50:
            board.push(move)
            if board.is_checkmate():
                board.pop()
                return float('inf') * -color
            board.pop()

        board.push(move)
        value = -negamax(board, depth - 1, -beta, -alpha, -color)
        board.pop()

        if value > max_value:
            max_value = value
            move_key = (move.from_square, move.to_square)
            HISTORY_TABLE[move_key] = HISTORY_TABLE.get(move_key, 0) + (depth * depth)
        alpha = max(value, alpha)
        if alpha >= beta:
            if depth <= DEFAULT_DEPTH:
                if move not in KILLER_MOVES[depth]:
                    if len(KILLER_MOVES[depth]) >= 2:
                        KILLER_MOVES[depth].pop(list(KILLER_MOVES[depth].keys())[0])
                    KILLER_MOVES[depth][move] = True
                move_key = (move.from_square, move.to_square)
                HISTORY_TABLE[move_key] = HISTORY_TABLE.get(move_key, 0) + (depth * depth)
            break

    transposition_table[key] = {'value': max_value, 'depth': depth}
    return max_value


def count_pieces(board):
    """Đếm số quân cờ trên bàn (bao gồm cả vua)."""
    return sum(len(board.pieces(piece_type, color))
               for piece_type in chess.PIECE_TYPES
               for color in [chess.WHITE, chess.BLACK])


def evaluate_with_tablebase(board, ai_color_=chess.WHITE):
    import chess.syzygy
    with chess.syzygy.open_tablebase("3-4-5") as tablebase:
        try:
            piece_count = len(board.piece_map())
            print(f"Số quân: {piece_count}")

            wdl_raw = tablebase.probe_wdl(board)
            dtz = tablebase.probe_dtz(board)

            # Chuyển về góc nhìn AI
            if board.turn == ai_color_:
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
            return mop_up_evaluation(board, ai_color_)
        except Exception as e:
            print("❌ Lỗi khác:", e)
            return mop_up_evaluation(board, ai_color_)


def has_pawn(board, color):
    return any(piece.piece_type == chess.PAWN and piece.color == color for piece in board.piece_map().values())


# Sử dụng Manager để chia sẻ HISTORY_TABLE giữa các tiến trình
import pickle


def get_best_move(board, depth, ai_color_):
    start_time = time.time()

    global KILLER_MOVES
    KILLER_MOVES = [{} for _ in range(depth + 1)]

    piece_count = count_pieces(board)
    best_move = None
    best_value = -float('inf')
    color = 1 if board.turn == ai_color_ else -1

    board_bytes = pickle.dumps(board)  # serialize nguyên bàn cờ

    possible_moves = list(order_moves(board, depth))
    max_workers = max(1, int(os.cpu_count() * 0.75))

    with ProcessPoolExecutor(max_workers) as executor:
        futures = [
            executor.submit(
                evaluate_move_in_process,
                board_bytes,
                move.uci(),
                depth,
                ai_color_,
                piece_count,
                color
            )
            for move in possible_moves
        ]

        history_delta_total = {}
        for future in as_completed(futures):
            move_uci, evaluation, history_delta = future.result()

            if evaluation >= best_value:
                best_value = evaluation
                best_move = chess.Move.from_uci(move_uci)

            for key, value in history_delta.items():
                history_delta_total[key] = history_delta_total.get(key, 0) + value

        for key, value in history_delta_total.items():
            HISTORY_TABLE[key] = HISTORY_TABLE.get(key, 0) + value

    move_time = time.time() - start_time
    MOVE_TIMES.append(move_time)

    print(f"Time: {move_time:.2f}s")
    san = board.san(best_move) if best_move else 'None'
    print(f"Best move: {san} | Value: {best_value:.2f}")
    return best_move


# Cập nhật hàm evaluate_move_in_process để nhận shared_history_table
def evaluate_move_in_process(board_bytes, move_uci, depth, ai_color_, piece_count, color):
    board = pickle.loads(board_bytes)  # khôi phục lại chess.Board
    move = chess.Move.from_uci(move_uci)
    history_delta = {}

    if is_threefold_repetition_if_move(board, move):
        white_score, black_score = material_score(board)
        if ai_color_ == chess.BLACK:
            if black_score >= white_score + 100:
                return move_uci, -float('inf'), {}
            elif black_score <= white_score - 200:
                return move_uci, float('inf'), {}
        else:
            if white_score >= black_score + 100:
                return move_uci, -float('inf'), {}
            elif white_score <= black_score - 200:
                return move_uci, float('inf'), {}

    board.push(move)

    if piece_count <= 5 and not has_pawn(board, ai_color_):
        evaluation = evaluate_with_tablebase(board, ai_color_)
    else:
        evaluation = -negamax(board, depth - 1, -float('inf'), float('inf'), -color)

    move_key = (move.from_square, move.to_square)
    history_delta[move_key] = depth * depth

    return move_uci, evaluation, history_delta


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


def promote_pawn_aggressively(board, ai_color_):
    promotion_moves = []

    for move in board.legal_moves:
        # Kiểm tra xem có phải nước đi của tốt không
        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.PAWN and piece.color == ai_color_:
            promotion_moves.append((move, move_score(board, move)))

    # Sắp xếp các nước theo điểm số để chọn nước tốt nhất
    promotion_moves.sort(key=lambda x: x[1], reverse=True)

    return [move for move, _ in promotion_moves]


def order_moves(board, depth):
    if is_wining_change(board, ai_color_=chess.BLACK):
        print("Winning change...")
        aggressive_promotions = promote_pawn_aggressively(board, ai_color_=chess.BLACK)
        if aggressive_promotions:
            return aggressive_promotions  # Ưu tiên đẩy tốt lên nếu có nước hợp lệ

    moves = list(board.legal_moves)
    # Tính điểm cho từng nước đi
    # scored_moves = [(move, move_score(board, move)) for move in moves]
    scored_moves = []

    for move in moves:
        score = move_score(board, move)

        if depth <= DEFAULT_DEPTH and move in KILLER_MOVES[depth]:
            score += 2000
        move_key = (move.from_square, move.to_square)
        history_score = HISTORY_TABLE.get(move_key, 0)
        score += history_score // 100

        scored_moves.append((move, score))

    # Sắp xếp theo điểm số, điểm cao nhất đứng đầu
    scored_moves.sort(key=lambda x: x[1], reverse=True)
    return [move for move, _ in scored_moves]


# Hàm tránh bị hòa khi đang có lợi thế
def is_threefold_repetition_if_move(board, move):
    board_copy = board.copy(stack=True)
    if move in board_copy.legal_moves:
        board_copy.push(move)
        return board_copy.is_repetition(3)
    return False


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


# Thế sắp thắng
def is_wining_change(board, ai_color_=chess.BLACK):
    white_material, black_material = material_score(board)

    white_pawn_count = len(board.pieces(chess.PAWN, chess.WHITE))
    black_pawn_count = len(board.pieces(chess.PAWN, chess.BLACK))

    white_score_without_pawns = white_material - 100 * white_pawn_count
    black_score_without_pawns = black_material - 100 * black_pawn_count

    if ai_color_ == chess.WHITE and black_material == 0 and white_score_without_pawns >= 500:
        return True
    if ai_color_ == chess.BLACK and white_material == 0 and black_score_without_pawns >= 500:
        return True

    return False


def is_endgame(board):
    """
    Kiểm tra xem bàn cờ có tổng giá trị các quân cờ nhỏ hơn 1200
    hoặc cả hai bên không còn quân hậu hay xe nào
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
    return total_material < 1200 or not has_major_piece


def print_move_times():
    """Print move times statistics when program exits"""
    if MOVE_TIMES:
        print("\nMove Times Statistics:")
        print(f"Total moves: {len(MOVE_TIMES)}")
        print(f"Average time: {sum(MOVE_TIMES) / len(MOVE_TIMES):.2f}s")
        print(f"Min time: {min(MOVE_TIMES):.2f}s")
        print(f"Max time: {max(MOVE_TIMES):.2f}s")
        print("\nIndividual move times:")
        for i, t in enumerate(MOVE_TIMES, 1):
            print(f"Move {i}: {t:.2f}s")
