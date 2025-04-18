from config import *
from evaluation import evaluate_position


def negamax(board_, depth_, alpha, beta, color):
    if depth_ == 0 or board_.is_game_over():
        return color * evaluate_position(board_, ai_color_=board_.turn if color == 1 else not board_.turn)

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

    return best_move