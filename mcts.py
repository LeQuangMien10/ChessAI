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
    # Điểm vị trí cho tốt (khuyến khích tốt tiến lên)
    pawn_position_bonus = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5, 5, 10, 25, 25, 10, 5, 5],
        [0, 0, 0, 20, 20, 0, 0, 0],
        [5, -5, -10, 0, 0, -10, -5, 5],
        [5, 10, 10, -20, -20, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ]

    score = 0

    # Tính điểm dựa trên quân cờ và vị trí
    for color in [0, 1]:  # 0: Trắng, 1: Đen
        multiplier = 1 if color == perspective_color else -1
        for piece in state.pieces_by_color[color]:
            # Điểm cơ bản của quân cờ
            piece_value = piece.SCORE_VALUE
            score += piece_value * multiplier

            # Điểm bonus cho vị trí của tốt
            if isinstance(piece, Pawn):
                row, col = piece.pos[1], piece.pos[0]
                if color == 1:  # Đen
                    row = 7 - row  # Lật bảng cho quân đen
                position_bonus = pawn_position_bonus[row][col]
                score += position_bonus * multiplier

    # Thêm điểm cho các yếu tố chiến thuật
    if state.cur_color_turn_in_check:
        score -= 50 * multiplier  # Trừ điểm nếu bị chiếu

    return score


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
                result = evaluation / 20000.0

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
