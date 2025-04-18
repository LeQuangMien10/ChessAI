import chess

from config import *
from evaluation import evaluate_position


def negamax(board_, depth_, alpha, beta, color):
    """
    Negamax.
    :param board_: bàn cờ
    :param depth_: độ sâu
    :param alpha: alpha
    :param beta: beta
    :param color: 1 cho trắng, -1 cho đen
    :return: điểm số cao nhất theo góc nhìn AI
    """
    if depth_ == 0 or board_.is_game_over():
        return evaluate_position(board_, color=color)

    max_score = float('-inf')
    for move in board_.legal_moves:
        board_.push(move)
        score = -negamax(board_, depth_ - 1, -beta, -alpha, -color)
        board_.pop()

        max_score = max(max_score, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break

    return max_score


def get_best_move(board_, depth_):
    """
    Tìm nước đi tốt nhất theo negamax.
    :param board_: bàn cờ
    :param depth_: độ sâu
    :return: nước đi tốt nhất theo góc nhìn AI
    """
    best_move = None
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    color = 1 if board_.turn == chess.WHITE else -1

    for move in board_.legal_moves:
        board_.push(move)
        score = -negamax(board_, depth_ - 1, -beta, -alpha, -color)
        board_.pop()

        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)

    san = board_.san(best_move)
    print(f"Best move: {san}, Score: {best_score}")

    return best_move