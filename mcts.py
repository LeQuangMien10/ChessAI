import math
import random
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from pygame_chess_api.api import Pawn, Queen, Knight, Bishop, Rook
from trans_table import TTABLE


class Node:
    def __init__(self, state, parent=None, move=None):
        self.state = state  # Board object
        self.parent = parent
        self.move = move  # Move that led to this state
        self.children = []
        self.visits = 0
        self.value = 0
        self.untried_moves = []
        self.board_hash = TTABLE.compute_hash(state)
        self.get_untried_moves()

    def get_untried_moves(self):
        for pos, piece in self.state.pieces_by_pos.items():
            if piece.color == self.state.cur_color_turn:
                moves = piece.get_moves_allowed()
                for move in moves:
                    if isinstance(piece, Pawn) and move.special_type == move.TO_PROMOTE_TYPE:
                        for promote_class in [Queen, Knight, Bishop, Rook]:
                            move_copy = move.copy(piece)
                            # Lưu thông tin về lớp phong cấp vào move
                            move_copy.promote_class = promote_class
                            self.untried_moves.append((piece, move_copy))
                    else:
                        self.untried_moves.append((piece, move))

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0

    def best_child(self, exploration_weight=1.4):
        choices = [(child, child.value / (child.visits + 1e-6) +
                    exploration_weight * math.sqrt(math.log(self.visits + 1) / (child.visits + 1e-6)))
                   for child in self.children]
        return max(choices, key=lambda x: x[1])[0]

    def expand(self):
        # self.get_untried_moves()
        piece, move = self.untried_moves.pop()
        new_state = self.state.create_hypothesis_board()
        # Lấy quân cờ từ bản sao của bàn cờ
        new_piece = new_state.pieces_by_pos[piece.pos]

        # Thiết lập promote_class_wanted cho quân tốt mới nếu cần
        if isinstance(new_piece, Pawn) and move.special_type == move.TO_PROMOTE_TYPE:
            new_piece.promote_class_wanted = move.promote_class

        new_state.move_piece(new_piece, move)
        child_node = Node(new_state, parent=self, move=move)
        self.children.append(child_node)
        return child_node

    def update(self, result):
        self.visits += 1
        self.value += result

    def is_terminal(self):
        return self.state.game_ended

    def get_result(self):
        if self.state.winner == self.state.cur_color_turn:
            return 1
        elif self.state.winner is None:  # Hòa
            return 0
        return -1


def evaluate_board(state, perspective_color):
    score = 0

    # Tính điểm dựa trên quân cờ và vị trí
    for color in [0, 1]:  # 0: Trắng, 1: Đen
        multiplier = 1 if color == perspective_color else -1
        for piece in state.pieces_by_color[color]:
            # Điểm cơ bản của quân cờ
            piece_value = piece.SCORE_VALUE
            score += piece_value * multiplier
            
            # Điểm vị trí
            row, col = piece.pos[1], piece.pos[0]
            if color == 1:  # Đen
                row = 7 - row  # Lật bảng cho quân đen
            position_bonus = piece.POSITION_BONUS[row][col]
            score += position_bonus * multiplier

            # Đánh giá kiểm soát trung tâm
            if 2 <= col <= 5 and 2 <= row <= 5:
                score += 10 * multiplier

            # Đánh giá cặp Tượng
            if isinstance(piece, Bishop):
                for other_piece in state.pieces_by_color[color]:
                    if isinstance(other_piece, Bishop) and other_piece != piece:
                        score += 50 * multiplier  # Thưởng cho việc giữ được cặp Tượng

            # Đánh giá vị trí Xe
            if isinstance(piece, Rook):
                # Xe ở cột mở (không có Tốt cùng màu)
                pawns_in_col = sum(1 for p in state.pieces_by_color[color] 
                                 if isinstance(p, Pawn) and p.pos[0] == col)
                if pawns_in_col == 0:
                    score += 30 * multiplier  # Thưởng cho Xe ở cột mở

                # Xe ở hàng 7 (hàng 2 với quân đen)
                if (color == 0 and row == 6) or (color == 1 and row == 1):
                    score += 20 * multiplier

            # Đánh giá vị trí Tốt
            if isinstance(piece, Pawn):
                # Tốt đôi (cùng cột)
                doubled_pawns = sum(1 for p in state.pieces_by_color[color] 
                                  if isinstance(p, Pawn) and p.pos[0] == col)
                if doubled_pawns > 1:
                    score -= 20 * multiplier  # Phạt cho Tốt đôi

                # Tốt cô lập (không có Tốt ở cột bên cạnh)
                isolated = True
                for c in [col-1, col+1]:
                    if 0 <= c <= 7:
                        for p in state.pieces_by_color[color]:
                            if isinstance(p, Pawn) and p.pos[0] == c:
                                isolated = False
                                break
                if isolated:
                    score -= 15 * multiplier  # Phạt cho Tốt cô lập

                # Tốt thông qua (không bị chặn bởi Tốt đối phương)
                passed = True
                enemy_color = 1 - color
                for r in range(row-1 if color == 0 else row+1, -1 if color == 0 else 8, -1 if color == 0 else 1):
                    for c in [col-1, col, col+1]:
                        if 0 <= c <= 7:
                            for p in state.pieces_by_color[enemy_color]:
                                if isinstance(p, Pawn) and p.pos == (c, r):
                                    passed = False
                                    break
                if passed:
                    score += 30 * multiplier  # Thưởng cho Tốt thông qua

    # Đánh giá an toàn của Vua
    for color in [0, 1]:
        multiplier = 1 if color == perspective_color else -1
        king = state.check_pieces[color]
        king_row, king_col = king.pos[1], king.pos[0]
        
        # Phạt Vua ở trung tâm trong giai đoạn đầu/giữa
        if 2 <= king_col <= 5 and not is_endgame(state):
            score -= 50 * multiplier

        # Đánh giá che chắn cho Vua
        pawn_shield = 0
        if color == 0:  # Trắng
            shield_positions = [(king_col-1, 6), (king_col, 6), (king_col+1, 6)]
        else:  # Đen
            shield_positions = [(king_col-1, 1), (king_col, 1), (king_col+1, 1)]
        
        for pos in shield_positions:
            if 0 <= pos[0] <= 7:
                for piece in state.pieces_by_color[color]:
                    if isinstance(piece, Pawn) and piece.pos == pos:
                        pawn_shield += 1
        
        score += (pawn_shield * 10) * multiplier

    # Thêm điểm cho các yếu tố chiến thuật
    if state.cur_color_turn_in_check:
        score -= 50 * multiplier  # Trừ điểm nếu bị chiếu

    return score


def is_endgame(state):
    """Kiểm tra xem có phải là giai đoạn cuối game không"""
    # Định nghĩa endgame khi:
    # 1. Không còn Hậu hoặc
    # 2. Mỗi bên còn ít hơn 2 quân lớn (Xe, Tượng, Mã) hoặc
    # 3. Tổng giá trị quân còn lại < 23000
    total_value = {0: 0, 1: 0}
    major_pieces = {0: 0, 1: 0}
    queens = {0: 0, 1: 0}
    
    for color in [0, 1]:
        for piece in state.pieces_by_color[color]:
            total_value[color] += piece.SCORE_VALUE
            if isinstance(piece, Queen):
                queens[color] += 1
            elif isinstance(piece, (Rook, Bishop, Knight)):
                major_pieces[color] += 1
    
    return (sum(queens.values()) == 0 or
            all(mp < 2 for mp in major_pieces.values()) or
            sum(total_value.values()) < 23000)


# Hàm MCTS cho một worker
def mcts_worker(root_state, time_limit, seed):
    # Tạo một TranspositionTable riêng cho worker
    worker_table = {}
    random.seed(seed)
    root = Node(root_state)
    start_time = time.time()
    end_time = start_time + time_limit

    while time.time() < end_time:
        node = root

        # Selection
        while not node.is_terminal() and node.is_fully_expanded():
            if time.time() >= end_time:
                break
            node = node.best_child()

        if time.time() >= end_time:
            break

        # Expansion
        if not node.is_terminal():
            node = node.expand()

        # Simulation
        sim_state = node.state.create_hypothesis_board()
        simulation_depth = 0
        max_depth = 10

        while not sim_state.game_ended and simulation_depth < max_depth:
            if time.time() >= end_time:
                break

            valid_moves = []
            for piece in sim_state.pieces_by_pos.values():
                if piece.color == sim_state.cur_color_turn:
                    moves = piece.get_moves_allowed()
                    for move in moves:
                        if isinstance(piece, Pawn) and move.special_type == move.TO_PROMOTE_TYPE:
                            for promote_class in [Queen, Knight, Bishop, Rook]:
                                move_copy = move.copy(piece)
                                move_copy.promote_class = promote_class
                                valid_moves.append((piece, move_copy))
                        else:
                            valid_moves.append((piece, move))

            if not valid_moves:
                break

            piece, move = random.choice(valid_moves)
            if isinstance(piece, Pawn) and move.special_type == move.TO_PROMOTE_TYPE:
                piece.promote_class_wanted = move.promote_class
            sim_state.move_piece(sim_state.pieces_by_pos[piece.pos], move)
            simulation_depth += 1

        # Backpropagation
        while node is not None:
            if sim_state.game_ended:
                result = 1 if sim_state.winner == root_state.cur_color_turn else (
                    -1 if sim_state.winner is not None else 0)
            else:
                evaluation = evaluate_board(sim_state, root_state.cur_color_turn)
                result = max(-1, min(1, evaluation / 20000.0))

            node.visits += 1
            node.value += result
            # Lưu vào worker table
            worker_table[node.board_hash] = (node.value, node.visits, time.time())
            node = node.parent

    best_child = root.best_child(exploration_weight=0)
    # Trả về cả nước đi và worker table
    return best_child.move, worker_table


# Hàm MCTS song song
def parallel_mcts(root_state, time_limit=9.25, num_workers=4):
    start_time = time.time()

    if root_state.cur_color_turn_in_check:
        valid_moves = []
        for piece in root_state.pieces_by_color[root_state.cur_color_turn]:
            moves = piece.get_moves_allowed()
            for move in moves:
                valid_moves.append((piece, move))
        if len(valid_moves) == 1:
            return valid_moves[0]

    # Kiểm tra và làm sạch table cũ
    TTABLE.cleanup_old_entries()

    # Thực hiện MCTS song song
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(mcts_worker, root_state, time_limit, i)
                   for i in range(num_workers)]
        results = []
        worker_tables = []
        for future in as_completed(futures):
            move, worker_table = future.result()
            results.append(move)
            worker_tables.append(worker_table)

    # Merge kết quả từ tất cả các worker
    for worker_table in worker_tables:
        TTABLE.merge_from_worker(worker_table)

    # Tính toán nước đi tốt nhất
    move_counts = {}
    for move in results:
        move_counts[move] = move_counts.get(move, 0) + 1

    best_move = max(move_counts.items(), key=lambda x: x[1])[0]
    best_piece = root_state.pieces_by_pos[best_move.piece.pos]

    # Lưu transposition table
    TTABLE.save_table()

    elapsed_time = time.time() - start_time
    print(f"Thời gian tính toán: {elapsed_time:.2f} giây")
    print(f"Số lượng entries trong table: {len(TTABLE.table)}")

    return best_piece, best_move
