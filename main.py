import chess
import pygame.time

from menu import *
from game import *
from minimax import get_best_move, save_history_table, decay_history_table
from minimax import save_transposition_table
from minimax import print_move_times

def handle_game_end():
    global running
    update_screen()
    result = "Checkmate" if board.is_checkmate() else "Draw"
    font = pygame.font.Font(None, 32)
    text = font.render(result, True, (0, 0, 0))
    screen.blit(text, (BOARD_SIZE // 2 - 50, BOARD_SIZE // 2))
    pygame.display.flip()
    pygame.time.wait(2000)
    running = False


def update_screen():
    screen.fill((0, 0, 0))
    draw_board(screen, selected_square, legal_moves)
    draw_pieces(screen, board)
    pygame.display.flip()


def player_vs_ai():
    global running, selected_square, legal_moves
    for event_ in pygame.event.get():
        if event_.type == pygame.QUIT:
            running = False

        elif event_.type == pygame.MOUSEBUTTONDOWN:
            square = get_square_from_mouse(event_.pos)

            if selected_square is None:
                piece_ = board.piece_at(square)
                if piece_ and piece_.color == board.turn:
                    selected_square = square
                    legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]
            else:
                move = chess.Move(selected_square, square)
                promote_pawn(board, move, screen)
                if move in board.legal_moves:
                    board.push(move)
                    update_screen()

                    if not board.is_game_over():
                        handle_ai_turn(chess.BLACK)

                selected_square = None
                legal_moves = []
        if board.is_game_over():
            handle_game_end()
            break


def ai_vs_player():
    global running, selected_square, legal_moves
    if board.turn == chess.WHITE and not board.is_game_over():
        handle_ai_turn(chess.WHITE)

    for event_ in pygame.event.get():
        if event_.type == pygame.QUIT:
            running = False

        elif event_.type == pygame.MOUSEBUTTONDOWN:
            square = get_square_from_mouse(event_.pos)

            if selected_square is None:
                piece_ = board.piece_at(square)
                if piece_ and piece_.color == board.turn:
                    selected_square = square
                    legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]
            else:
                move = chess.Move(selected_square, square)
                promote_pawn(board, move, screen)
                if move in board.legal_moves:
                    board.push(move)
                    update_screen()

                selected_square = None
                legal_moves = []
        if board.is_game_over():
            handle_game_end()
            break


def handle_ai_turn(ai_color):
    best_move = get_best_move(board, depth=DEFAULT_DEPTH, ai_color_=ai_color)
    if best_move:
        board.push(best_move)
    else:
        print("No move")


def ai_vs_ai():
    global running
    for event_ in pygame.event.get():
        if event_.type == pygame.QUIT:
            running = False

    handle_ai_turn(chess.WHITE)

    if not board.is_game_over():
        update_screen()
        handle_ai_turn(chess.BLACK)
    if board.is_game_over():
        handle_game_end()
        running = False


def player_vs_player():
    global running, selected_square, legal_moves
    for event_ in pygame.event.get():
        if event_.type == pygame.QUIT:
            running = False

        elif event_.type == pygame.MOUSEBUTTONDOWN:
            square = get_square_from_mouse(event_.pos)

            if selected_square is None:
                piece_ = board.piece_at(square)
                if piece_ and piece_.color == board.turn:
                    selected_square = square
                    legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]
            else:
                move = chess.Move(selected_square, square)
                promote_pawn(board, move, screen)
                if move in board.legal_moves:
                    board.push(move)
                    update_screen()

                selected_square = None
                legal_moves = []
        if board.is_game_over():
            handle_game_end()
            break

# Bọc hàm main


def main():
    global board, selected_square, legal_moves, clock, running, screen, game_mode
    pygame.init()
    screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
    pygame.display.set_caption("Chess")

    game_mode = get_game_mode(screen)
    board = chess.Board(FEN_STRING_ENDGAME_HAVE_PAWN_1)
    selected_square = None
    legal_moves = []
    clock = pygame.time.Clock()
    running = True

    while running:
        clock.tick(60)
        update_screen()
        if game_mode == TWO_PLAYERS:
            player_vs_player()
        elif game_mode == TWO_AIS:
            ai_vs_ai()
        elif game_mode == PLAYER_VS_AI:
            player_vs_ai()
        elif game_mode == AI_VS_PLAYER:
            ai_vs_player()
        save_history_table()
        decay_history_table()
        save_transposition_table()

    print_move_times()
    pygame.quit()


if __name__ == "__main__":
    main()