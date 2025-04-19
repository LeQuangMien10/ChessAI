import chess
from matplotlib.pyplot import connect
from time import perf_counter
import config
from config import *


def get_game_phase(board):
    """
    Determine the game phase based on the number of pieces on the board.
    This is a simplified approach. You might want to use more sophisticated methods.
    """
    piece_count = len(board.piece_map())
    if piece_count >= 28:  # Roughly more than half of starting pieces
        return 'opening'
    elif piece_count >= 12: # Roughly between 12 and 28 pieces
        return 'middlegame'
    else:
        return 'endgame'


# HAM TONG
def evaluate_position(board_, color):
    """
    Đánh giá bàn cờ theo góc nhìn AI
    :param board_: bàn cờ
    :param color: 1 cho trắng, -1 cho đen
    :return:
    """
    evaluation = 0

    if board_.is_checkmate():
        return -float('inf')
    if board_.is_stalemate() or board_.is_insufficient_material() or board_.is_seventyfive_moves() or board_.is_fivefold_repetition():
        return 0  # Hòa, trả về 0

    # Get the evaluation parameters based on the game phase
    game_phase = get_game_phase(board_)
    params = EVAL_PARAMS[game_phase]

    #Trọng số cho các đánh giá (có thể tùy chỉnh)
    material_weight = params['material']
    piece_square_tables_weight = params['piece_square_tables']
    pawn_structure_weight = params['pawn_structure']
    mobility_weight = params['mobility']
    king_safety_weight = params['king_safety']
    tempo_weight = params['tempo']
    trapped_pieces_weight = params['trapped_pieces']
    space_weight = params['space']
    center_control_weight = params['center_control']
    connectivity_weight = params['connectivity']


    #Tạm thời ae dùng hàm này nhé để xem từng hàm mất bao nhiêu thời gian sau ok rồi thì zoá
    timers = {}

    def time_call(label, func):
        start = perf_counter()
        result = func()
        end = perf_counter()
        timers[label] = end - start
        return result

    # Tính tổng từng phần
    evaluation += time_call("material", lambda: material(board_)) * material_weight
    evaluation += time_call("piece_square_tables", lambda: piece_square_tables(board_)) * piece_square_tables_weight
    evaluation += time_call("pawn_structure", lambda: pawn_structure(board_)) * pawn_structure_weight
    evaluation += time_call("mobility", lambda: mobility(board_)) * mobility_weight
    evaluation += time_call("king_safety", lambda: king_safety(board_)) * king_safety_weight
    evaluation += time_call("tempo", lambda: tempo(board_, color)) * tempo_weight
    evaluation += time_call("trapped_pieces", lambda: trapped_pieces(board_)) * trapped_pieces_weight
    evaluation += time_call("space", lambda: space(board_)) * space_weight
    evaluation += time_call("center_control", lambda: center_control(board_)) * center_control_weight
    evaluation += time_call("connectivity", lambda: connectivity(board_)) * connectivity_weight
    
    if game_phase == "endgame":
        evaluation += mop_up_evaluation(board_, color)
    # In thông tin benchmark
    print(f"⚡ Evaluation Benchmark - Phase: {game_phase}")
    for label, t in timers.items():
        print(f"  {label:18s}: {t:.6f} s")

    return evaluation * color


# material
def material(board_):
    """
    Đánh giá material theo quân trắng.
    :param board_: bàn cờ
    :return: điểm nguyên liệu theo quân trắng
    """
    value = 0
    for square in chess.SQUARES:
        piece = board_.piece_at(square)
        if piece:
            value += PIECE_VALUES[piece.piece_type] if piece.color == chess.WHITE else -PIECE_VALUES[piece.piece_type]

    return value


# piece_square_tables
def piece_square_tables(board_):
    """
    Đánh giá vị trí quân cờ theo quân trắng
    :param board_: bàn cờ
    :return: Điểm vị trí các quân cờ theo màu trắng
    """
    evaluation_ = 0
    # positional_bonus = 0
    for square in chess.SQUARES:
        piece = board_.piece_at(square)
        if piece:
            index = square if piece.color == chess.WHITE else chess.square_mirror(square)

            if piece.piece_type == chess.PAWN:
                positional_bonus = PAWN_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.KNIGHT:
                positional_bonus = KNIGHT_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.BISHOP:
                positional_bonus = BISHOP_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.ROOK:
                positional_bonus = ROOK_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.QUEEN:
                positional_bonus = QUEEN_POSITION_BONUS[7 - index // 8][index % 8]
            elif piece.piece_type == chess.KING:
                positional_bonus = KING_POSITION_BONUS[7 - index // 8][index % 8]

            evaluation_ += positional_bonus if piece.color == chess.WHITE else -positional_bonus

    return evaluation_


# Pawn Structure
def pawn_structure(board_):
    """
    Đánh giá cấu trúc tốt trên bàn cờ theo phía trắng
    """
    evaluation_ = 0
    white_pawns = board_.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board_.pieces(chess.PAWN, chess.BLACK)

    def get_files(pawn_squares):
        return sorted(set([chess.square_file(sq) for sq in pawn_squares]))

    def is_isolated(square, color):
        file = chess.square_file(square)
        neighbor_files = [f for f in [file - 1, file + 1] if 0 <= f <= 7]
        for neighbor_file in neighbor_files:
            for rank in range(8):
                neighbor_square = chess.square(neighbor_file, rank)
                if board_.piece_at(neighbor_square) == chess.Piece(chess.PAWN, color):
                    return False
        return True

    def is_doubled(square, color):
        file = chess.square_file(square)
        count = 0
        for rank in range(8):
            sq = chess.square(file, rank)
            if board_.piece_at(sq) == chess.Piece(chess.PAWN, color):
                count += 1
        return count > 1

    def is_passed(square, color):
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        direction = 1 if color == chess.WHITE else -1
        enemy_color = not color

        for f in [file - 1, file, file + 1]:
            if 0 <= f <= 7:
                r = rank + direction
                while 0 <= r <= 7:
                    sq = chess.square(f, r)
                    if board_.piece_at(sq) == chess.Piece(chess.PAWN, enemy_color):
                        return False
                    r += direction
        return True

    def is_backward(square, color):
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        direction = 1 if color == chess.WHITE else -1
        enemy_color = not color

        # Không có đồng minh phía sau để đẩy lên
        has_support = False
        for f in [file - 1, file + 1]:
            if 0 <= f <= 7:
                for r in range(rank - direction, rank - direction * 3, -direction):
                    if 0 <= r <= 7:
                        sq = chess.square(f, r)
                        if board_.piece_at(sq) == chess.Piece(chess.PAWN, color):
                            has_support = True
                            break

        if has_support:
            return False

        # Có quân địch kiểm soát ô trước mặt
        front_square = chess.square(file, rank + direction)
        attackers = board_.attackers(enemy_color, front_square)
        return bool(attackers)

    def count_islands(pawn_squares):
        files = sorted([chess.square_file(sq) for sq in pawn_squares])
        if not files:
            return 0
        islands = 1
        for i in range(1, len(files)):
            if files[i] != files[i - 1] + 1:
                islands += 1
        return islands

    for square in white_pawns:
        if is_isolated(square, chess.WHITE):
            evaluation_ -= ISOLATED_PAWN_PENALTY
        if is_doubled(square, chess.WHITE):
            evaluation_ -= DOUBLED_PAWN_PENALTY
        if is_passed(square, chess.WHITE):
            evaluation_ += PASSED_PAWN_BONUS
        if is_backward(square, chess.WHITE):
            evaluation_ -= BACKWARD_PAWN_PENALTY

    for square in black_pawns:
        if is_isolated(square, chess.BLACK):
            evaluation_ += ISOLATED_PAWN_PENALTY
        if is_doubled(square, chess.BLACK):
            evaluation_ += DOUBLED_PAWN_PENALTY
        if is_passed(square, chess.BLACK):
            evaluation_ -= PASSED_PAWN_BONUS
        if is_backward(square, chess.BLACK):
            evaluation_ += BACKWARD_PAWN_PENALTY

    # Đánh giá pawn island
    white_islands = count_islands(white_pawns)
    black_islands = count_islands(black_pawns)
    evaluation_ -= PAWN_ISLAND_PENALTY * (white_islands - 1)
    evaluation_ += PAWN_ISLAND_PENALTY * (black_islands - 1)

    return evaluation_


# Evaluation of Pieces


# Evaluation Patterns

# Mobility
def mobility(board_):
    """
    Mobility nâng cao: tính số nước đi từng quân (không tính tốt), phân theo loại quân,
    nhân trọng số, rồi tính chênh lệch trắng - đen.
    """
    white_score = 0
    black_score = 0

    for move in board_.legal_moves:
        piece = board_.piece_at(move.from_square)
        if piece and piece.piece_type in MOBILITY_WEIGHTS:
            weight = MOBILITY_WEIGHTS[piece.piece_type]
            if piece.color == chess.WHITE:
                white_score += weight
            else:
                black_score += weight

    return white_score - black_score


# Center Control
def center_control(board):
    """Hàm này tính điểm dựa trên số lượng quân mỗi bên tấn công và chiếm đóng các ô trung tâm."""
    "Trả về Giá trị dương nghiêng về Trắng, giá trị âm nghiêng về Đen, 0 là cân bằng."
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]  # Các ô trung tâm (sử dụng ký hiệu chess.SQUARES nếu cần)
    center_control_score = 0

    for square in center_squares:
        # Kiểm tra quân cờ đang chiếm giữ ô trung tâm
        piece = board.piece_at(square)
        if piece:
            if piece.color == chess.WHITE:
                center_control_score += PIECE_VALUES[piece.piece_type]
            else:
                center_control_score -= PIECE_VALUES[piece.piece_type]

        # Kiểm tra quân cờ tấn công ô trung tâm
        attackers = board.attackers(chess.WHITE, square)
        center_control_score += len(attackers)  # Mỗi quân Trắng tấn công ô trung tâm +1 điểm

        attackers = board.attackers(chess.BLACK, square)
        center_control_score -= len(attackers)  # Mỗi quân Đen tấn công ô trung tâm -1 điểm

    return center_control_score

# Connectivity
def connectivity(board):
    """
    Đánh giá tính kết nối giữa các quân cờ trên bàn cờ.

    Hàm này tập trung vào:
    1.  **Sự gần gũi:**  Đếm số lượng quân cờ đồng minh ở gần nhau (trong phạm vi 1-2 ô).
    2.  **Sự hỗ trợ:** Đếm số lượng quân cờ được bảo vệ bởi quân cờ đồng minh.

    Args:
        board: Đối tượng bàn cờ chess.Board.

    Returns:
        Một giá trị số nguyên thể hiện điểm kết nối.
        Giá trị dương nghiêng về Trắng, giá trị âm nghiêng về Đen, 0 là cân bằng.
    """

    connectivity_score = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            # 1. Đánh giá sự gần gũi (Proximity)
            for neighbor_square in get_neighbor_squares(square): # Hàm phụ trợ để lấy ô lân cận
                neighbor_piece = board.piece_at(neighbor_square)
                if neighbor_piece and neighbor_piece.color == piece.color:
                    if piece.color == chess.WHITE:
                        connectivity_score += PIECE_VALUES[piece.piece_type] * 0.1  # Hệ số nhỏ hơn vì chỉ là gần gũi
                    else:
                        connectivity_score -= PIECE_VALUES[piece.piece_type] * 0.1

            # 2. Đánh giá sự hỗ trợ (Support)
            defenders = board.attackers(piece.color, square) # Quân đồng minh bảo vệ ô này
            if piece.color == chess.WHITE:
                connectivity_score += len(list(defenders)) * PIECE_VALUES[piece.piece_type] * 0.05
            else:
                connectivity_score -= len(list(defenders)) * PIECE_VALUES[piece.piece_type] * 0.05 # Hệ số nhỏ hơn

    return connectivity_score

def get_neighbor_squares(square):
    """
    Trả về danh sách các ô lân cận (orthogonally và diagonally) của một ô cho trước,
    loại bỏ các ô nằm ngoài bàn cờ.
    """
    neighbors = []
    rank, file = chess.square_rank(square), chess.square_file(square)
    for dr in [-1, 0, 1]:
        for df in [-1, 0, 1]:
            if dr == 0 and df == 0:
                continue  # Bỏ qua chính ô hiện tại
            new_rank, new_file = rank + dr, file + df
            if 0 <= new_rank <= 7 and 0 <= new_file <= 7:
                neighbors.append(chess.square(new_file, new_rank))
    return neighbors


# Trapped Pieces
def trapped_pieces(board_):
    """
    Đánh giá các quân bị mắc kẹt (trapped pieces) theo góc nhìn trắng.
    Tập trung vào Knight, Bishop, Rook chưa phát triển hoặc bị chặn.
    """
    evaluation = 0

    def is_trapped(piece, square, legal_moves):
        """
        Kiểm tra xem quân có bị mắc kẹt không:
        - Ít nước đi hợp lệ
        - Đứng ở góc/rìa bàn cờ
        """
        if piece.piece_type not in [chess.KNIGHT, chess.BISHOP, chess.ROOK]:
            return False

        if len(legal_moves) <= 1:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            if file in [0, 7] or rank in [0, 7]:  # ở biên
                return True

        return False

    for square in chess.SQUARES:
        piece = board_.piece_at(square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK]:
            legal_moves = [
                move for move in board_.legal_moves
                if move.from_square == square
            ]
            if is_trapped(piece, square, legal_moves):
                penalty = TRAPPED_PIECE_PENALTY.get(piece.piece_type, 50)
                if piece.color == chess.WHITE:
                    evaluation -= penalty
                else:
                    evaluation += penalty

    return evaluation


# King Safety
def king_safety(board_):
    """
    Đánh giá độ an toàn của vua theo góc nhìn trắng.
    Các yếu tố:
    - Vị trí vua (gần biên hay ở giữa)
    - Số tốt bảo vệ vua
    - Các ô xung quanh bị tấn công
    - Đã nhập thành chưa
    """

    def evaluate_king(color):
        safety = 0
        king_square = board_.king(color)
        if king_square is None:
            return -float('inf')  # mất vua

        # 1. Vị trí vua
        rank = chess.square_rank(king_square)
        file = chess.square_file(king_square)
        center_distance = abs(file - 3.5) + abs(rank - 3.5)
        safety -= KING_CENTER_PENALTY * center_distance

        # 2. Các ô quanh vua
        surrounding_squares = [
            chess.square(f, r)
            for f in range(file - 1, file + 2)
            for r in range(rank - 1, rank + 2)
            if 0 <= f <= 7 and 0 <= r <= 7 and chess.square(f, r) != king_square
        ]

        # Bị tấn công bởi đối phương?
        opponent = not color
        for sq in surrounding_squares:
            attackers = board_.attackers(opponent, sq)
            if attackers:
                safety -= KING_ATTACKED_SQUARE_PENALTY * len(attackers)

        # 3. Có bao nhiêu tốt bảo vệ?
        pawn_protectors = 0
        for sq in surrounding_squares:
            piece = board_.piece_at(sq)
            if piece and piece.piece_type == chess.PAWN and piece.color == color:
                pawn_protectors += 1
        safety += PAWN_SHIELD_BONUS * pawn_protectors

        # 4. Đã nhập thành chưa?
        if color == chess.WHITE:
            if board_.has_kingside_castling_rights(color) or board_.has_queenside_castling_rights(color):
                safety += CASTLING_RIGHTS_BONUS
        else:
            if board_.has_kingside_castling_rights(color) or board_.has_queenside_castling_rights(color):
                safety += CASTLING_RIGHTS_BONUS

        return safety

    white_king_safety = evaluate_king(chess.WHITE)
    black_king_safety = evaluate_king(chess.BLACK)
    return white_king_safety - black_king_safety


# Space
def space(board_):
    """
    Đánh giá không gian kiểm soát theo góc nhìn trắng.
    Tính số ô trống được kiểm soát trên phần sân đối phương.
    """
    white_space = 0
    black_space = 0
    central_squares = [chess.D4, chess.E4, chess.D5, chess.E5]

    for square in chess.SQUARES:
        # Bỏ qua ô đang có quân
        if board_.piece_at(square):
            continue

        white_attackers = board_.attackers(chess.WHITE, square)
        black_attackers = board_.attackers(chess.BLACK, square)

        rank = chess.square_rank(square)

        # White kiểm soát ô trên nửa sân của đen
        if white_attackers and rank >= 4:
            white_space += 1
            if square in central_squares:
                white_space += 0.5

        # Black kiểm soát ô trên nửa sân của trắng
        if black_attackers and rank <= 3:
            black_space += 1
            if square in central_squares:
                black_space += 0.5

    return SPACE_WEIGHT * (white_space - black_space)


# Tempo
def tempo(board_, color):
    """
    Đánh giá tempo: nếu là lượt của AI, cộng thêm điểm.
    Đây là lợi thế tạm thời vì AI được đi trước.
    """
    if (board_.turn == chess.WHITE and color == 1) or (board_.turn == chess.BLACK and color == -1):
        return TEMPO_BONUS
    else:
        return 0


# manhattan_distance
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


# mop_up_evaluation
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
        center_manhattan_distance = CENTER_MANHATTAN_DISTANCE[7 - opponent_king_square // 8][
            opponent_king_square % 8]
        center_bonus = 4.7 * center_manhattan_distance
        evaluation += center_bonus

        # 2. Thưởng hai vua gần nhau
        kings_distance = manhattan_distance(king_square, opponent_king_square)
        king_proximity_bonus = 1.6 * (14 - kings_distance)
        evaluation += king_proximity_bonus

    return evaluation