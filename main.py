import pygame.time
from menu import *
from game import *
from negamax import get_best_move
from fen_string_test import *
from transposition_table import TranspositionTable
from stockfish_test import StockfishEngine
import chess.polyglot

with open("elo.txt", "r") as file:
    ai_elo = float(file.readline().strip())

def handle_game_end(ai_color=None):
    global running, ai_elo
    update_screen()
    result = "Checkmate" if board.is_checkmate() else "Draw"
    font = pygame.font.Font(None, 32)
    text = font.render(result, True, (0, 0, 0))
    screen.blit(text, (BOARD_SIZE // 2 - 50, BOARD_SIZE // 2))
    pygame.display.flip()

    # Tính Elo nếu chơi với Stockfish
    if game_mode == TWO_AIS:
        game_result = board.result()
        ai_elo = stockfish_engine.calculate_elo(ai_elo, stockfish_elo, game_result, ai_color)
        print(f"Game result: {game_result}, New AI Elo: {ai_elo:.2f}")
        with open("elo.txt", "w") as file:
            file.write(f"{ai_elo:.2f}\n")

    pygame.time.wait(2000)
    running = False

def update_screen():
    screen.fill(WHITE)
    last_move = board.peek() if board.move_stack else None
    draw_board(screen, selected_square, legal_moves, last_move, board)
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
                    selected_square = None
                    legal_moves = []
                    update_screen()

                    if not board.is_game_over():
                        handle_ai_turn()
                else:
                    # Nếu click vào ô không hợp lệ, cho phép chọn quân cờ khác
                    piece_ = board.piece_at(square)
                    if piece_ and piece_.color == board.turn:
                        selected_square = square
                        legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]
                    else:
                        selected_square = None
                        legal_moves = []
        if board.is_game_over():
            handle_game_end()
            break


def ai_vs_player():
    global running, selected_square, legal_moves
    if board.turn == chess.WHITE and not board.is_game_over():
        handle_ai_turn()

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
                    selected_square = None
                    legal_moves = []
                    update_screen()
                else:
                    # Nếu click vào ô không hợp lệ, cho phép chọn quân cờ khác
                    piece_ = board.piece_at(square)
                    if piece_ and piece_.color == board.turn:
                        selected_square = square
                        legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]
                    else:
                        selected_square = None
                        legal_moves = []
        if board.is_game_over():
            handle_game_end()
            break


def get_book_move(board):
    try:
        with chess.polyglot.open_reader("polyglot-collection/sixth_merge.bin") as reader:
            return reader.weighted_choice(board).move
    except (IndexError, FileNotFoundError):
        return None

def handle_ai_turn(use_stockfish=False):
    # Ưu tiên book trong 12 nước đầu
    if board.fullmove_number <= 12:
        book_move = get_book_move(board)
        if book_move:
            print(f"📖 Opening book move: {book_move}")
            board.push(book_move)
            return

    # Chọn giữa Stockfish và AI của bạn
    if use_stockfish:
        best_move = stockfish_engine.get_best_move(board, time_limit=0.1)
        if best_move:
            print(f"🤖 Stockfish move: {board.san(best_move)}")
            board.push(best_move)
        else:
            print("⚠️ No valid move found by Stockfish.")
    else:
        # Nếu không có trong book → dùng AI hiện tại
        best_move = get_best_move(board, target_depth=MAX_DEPTH, tt=tt)
        if best_move:
            print(f"🧠 AI move: {board.san(best_move)}")
            board.push(best_move)
        else:
            print("⚠️ No valid move found by AI.")


def ai_vs_ai():
    # True: Stockfish (Trắng), AI (Đen)
    # False: Stockfish (Đen), AI (Trắng)
    use_stockfish = False
    global running
    for event_ in pygame.event.get():
        if event_.type == pygame.QUIT:
            running = False
            stockfish_engine.quit()

    handle_ai_turn(use_stockfish)

    if not board.is_game_over():
        update_screen()
        handle_ai_turn(not use_stockfish)
    if board.is_game_over():
        ai_color = chess.BLACK if use_stockfish else chess.WHITE
        handle_game_end(ai_color)  # Màu AI
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
                    selected_square = None
                    legal_moves = []
                    update_screen()
                else:
                    # Nếu click vào ô không hợp lệ, cho phép chọn quân cờ khác
                    piece_ = board.piece_at(square)
                    if piece_ and piece_.color == board.turn:
                        selected_square = square
                        legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]
                    else:
                        selected_square = None
                        legal_moves = []
        if board.is_game_over():
            handle_game_end()
            break

# Bọc hàm main
pygame.init()
screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
pygame.display.set_caption("Chess")

# Khởi tạo Stockfish engine
stockfish_path = "stockfish/stockfish-windows-x86-64-avx2.exe"  # Thay bằng đường dẫn thực tế
stockfish_engine = StockfishEngine(stockfish_path, skill_level=STOCKFISH_LEVEL)  # Mức độ trung bình


ELO_PER_SKILL_LEVEL = {
    0: 1100, 1: 1250, 2: 1400, 3: 1550, 4: 1700, 5: 1850, 6: 2000, 7: 2150, 8: 2300, 9: 2450,
    10: 2600, 11: 2725, 12: 2850, 13: 2975, 14: 3100, 15: 3200, 16: 3300, 17: 3400, 18: 2475, 19: 3550, 20: 3600
}

stockfish_elo = ELO_PER_SKILL_LEVEL[STOCKFISH_LEVEL]
game_history = []


game_mode = get_game_mode(screen)
board = chess.Board()  # Sửa thế ở đây
tt = TranspositionTable(size_mb=128)
selected_square = None
legal_moves = []
clock = pygame.time.Clock()
running = True

def main():
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
    stockfish_engine.quit()
    pygame.quit()


if __name__ == "__main__":
    print()
    main()
