import pygame.time
from menu import *
from game import *
from negamax import get_best_move
from fen_string_test import *
from pgn import save_pgn
from transposition_table import TranspositionTable
from stockfish_test import StockfishEngine
import chess.polyglot
import time
import pygame.mixer
from sounds import sound_manager

with open("elo.txt", "r") as file:
    ai_elo = float(file.readline().strip())

# Bọc hàm main
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Chess")

# Khởi tạo mixer cho âm thanh
pygame.mixer.init()

def handle_game_end(ai_color=None):
    global running, ai_elo
    update_screen()
    result = "Checkmate" if board.is_checkmate() else "Draw"
    font = pygame.font.Font(None, 32)
    text = font.render(result, True, (0, 0, 0))
    screen.blit(text, (BOARD_SIZE // 2 - 50, BOARD_SIZE // 2))
    pygame.display.flip()

    # Tính Elo nếu chơi với Stockfish
    game_result = board.result()
    if game_mode == TWO_AIS:
        ai_elo = stockfish_engine.calculate_elo(ai_elo, stockfish_elo, game_result, ai_color)
        print(f"Game result: {game_result}, New AI Elo: {ai_elo:.2f}")
        with open("elo.txt", "w") as file:
            file.write(f"{ai_elo:.2f}\n")
        save_pgn("TWO_AIS", ai_color, "Stockfish", game_result, move_history.history_move_list())

    elif game_mode == PLAYER_VS_AI:
        save_pgn("PLAYER_VS_AI", ai_color, "Human", game_result, move_history.history_move_list())

    elif game_mode == AI_VS_PLAYER:
        print (ai_color)
        save_pgn("AI_VS_PLAYER", ai_color, "Human", game_result, move_history.history_move_list())

    pygame.time.wait(2000)
    # Có thể thêm âm thanh kết thúc game ở đây nếu muốn
    running = False
def update_screen():
    screen.fill(WHITE)
    last_move = board.peek() if board.move_stack else None
    draw_board(screen, selected_square, legal_moves, last_move, board)
    draw_pieces(screen, board)
    draw_info_panel(screen, move_history)
    pygame.display.flip()


def player_vs_ai():
    global running, selected_square, legal_moves
    for event_ in pygame.event.get():
        if event_.type == pygame.QUIT:
            running = False
            
        elif event_.type == pygame.MOUSEBUTTONDOWN:
            # Xử lý sự kiện cuộn chuột
            if event_.button == 4:  # Cuộn lên
                move_history.handle_scroll(True)
                update_screen()
            elif event_.button == 5:  # Cuộn xuống
                move_history.handle_scroll(False)
                update_screen()
            
            # Xử lý click chuột bình thường
            square = get_square_from_mouse(event_.pos)

            # Nếu click vào ô trống hoặc quân địch khi đã chọn một quân
            if selected_square is not None:
                piece_ = board.piece_at(square)
                move = chess.Move(selected_square, square)
                
                # Nếu click vào quân của mình -> chọn quân mới
                if piece_ and piece_.color == board.turn:
                    selected_square = square
                    legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]
                # Nếu là nước đi hợp lệ -> thực hiện nước đi
                elif move in board.legal_moves:
                    sound_manager.play_move_sound(board, move)
                    promote_pawn(board, move, screen)
                    try:
                        move_san = board.san(move)
                        move_history.add_move(move_san, board.turn == chess.WHITE)
                    except:
                        move_san = move.uci()
                    
                    board.push(move)
                    selected_square = None
                    legal_moves = []
                    update_screen()

                    if not board.is_game_over():
                        start_time = time.time()
                        handle_ai_turn()
                        end_time = time.time()
                        
                        if board.move_stack:
                            last_move = board.peek()
                            try:
                                ai_move_san = board.san(last_move)
                                move_history.add_move(ai_move_san, board.turn != chess.WHITE)
                            except:
                                ai_move_san = last_move.uci()
                            
                            move_history.update_stats(
                                final_depth_completed,
                                end_time - start_time
                            )
                else:
                    # Nếu click vào ô không hợp lệ và không phải quân của mình -> bỏ chọn
                    selected_square = None
                    legal_moves = []
            # Chưa chọn quân nào
            else:
                piece_ = board.piece_at(square)
                if piece_ and piece_.color == board.turn:
                    selected_square = square
                    legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]

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

            # Nếu chưa chọn quân nào
            if selected_square is None:
                piece_ = board.piece_at(square)
                if piece_ and piece_.color == board.turn:
                    selected_square = square
                    legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]

            # Nếu đã chọn quân
            else:
                move = chess.Move(selected_square, square)
                promote_pawn(board, move, screen)

                # Nếu nước đi hợp lệ
                if move in board.legal_moves:
                    # Phát âm thanh trước khi thực hiện nước đi
                    play_move_sound(board, move)
                    try:
                        move_san = board.san(move)
                        move_history.add_move(move_san, board.turn == chess.WHITE)
                    except:
                        move_san = move.uci()

                    board.push(move)
                    selected_square = None
                    legal_moves = []
                    update_screen()

                    # Nếu không phải là lượt cuối, chuyển sang lượt AI
                    if not board.is_game_over():
                        start_time = time.time()
                        handle_ai_turn()
                        end_time = time.time()

                        if board.move_stack:
                            last_move = board.peek()
                            try:
                                ai_move_san = board.san(last_move)
                                move_history.add_move(ai_move_san, board.turn != chess.WHITE)
                            except:
                                ai_move_san = last_move.uci()

                            move_history.update_stats(
                                final_depth_completed,
                                end_time - start_time
                            )
                else:
                    # Nếu click vào ô không hợp lệ -> bỏ chọn
                    selected_square = None
                    legal_moves = []
                    piece_ = board.piece_at(square)
                    if piece_ and piece_.color == board.turn:
                        selected_square = square
                        legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]

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
    global final_depth_completed
    
    # Ưu tiên book trong 12 nước đầu
    if board.fullmove_number <= 12:
        book_move = get_book_move(board)
        if book_move:
            print(f"📖 Opening book move: {book_move}")
            # Phát âm thanh cho book move
            sound_manager.play_move_sound(board, book_move)
            try:
                move_san = board.san(book_move)
                move_history.add_move(move_san, board.turn == chess.WHITE)
            except:
                move_san = book_move.uci()
            board.push(book_move)
            final_depth_completed = 0
            return

    # Chọn giữa Stockfish và AI của bạn
    if use_stockfish:
        best_move = stockfish_engine.get_best_move(board, time_limit=0.1)
        if best_move:
            print(f"🤖 Stockfish move: {board.san(best_move)}")
            # Phát âm thanh cho Stockfish move
            sound_manager.play_move_sound(board, best_move)
            try:
                move_san = board.san(best_move)
                move_history.add_move(move_san, board.turn == chess.WHITE)
            except:
                move_san = best_move.uci()
            board.push(best_move)
            final_depth_completed = 0
        else:
            print("⚠️ No valid move found by Stockfish.")
    else:
        # Nếu không có trong book → dùng AI hiện tại
        start_time = time.time()
        result = get_best_move(board, target_depth=MAX_DEPTH, tt=tt)
        end_time = time.time()
        
        if isinstance(result, tuple):
            best_move, depth = result
            final_depth_completed = depth
        else:
            best_move = result
            final_depth_completed = 0
        
        if best_move:
            print(f"🧠 AI move: {board.san(best_move)}")
            # Phát âm thanh cho AI move
            sound_manager.play_move_sound(board, best_move)
            try:
                move_san = board.san(best_move)
                move_history.add_move(move_san, board.turn == chess.WHITE)
            except:
                move_san = best_move.uci()
            board.push(best_move)
            move_history.update_stats(final_depth_completed, end_time - start_time)
        else:
            print("⚠️ No valid move found by AI.")


def ai_vs_ai():
    # True: Stockfish (Trắng), AI (Đen)
    # False: Stockfish (Đen), AI (Trắng)
    use_stockfish = True
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
                    # Thêm âm thanh trước khi thực hiện nước đi
                    sound_manager.play_move_sound(board, move)
                    try:
                        move_san = board.san(move)
                        move_history.add_move(move_san, board.turn == chess.WHITE)
                    except:
                        move_san = move.uci()
                        
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


# Khởi tạo Stockfish engine
stockfish_path = "stockfish/stockfish-windows-x86-64-avx2.exe"  # cái này là đường dẫn của anh em
# stockfish_path = "/Users/phuocthanh/Documents/ChessAI/stockfish copy/stockfish-macos-m1-apple-silicon"  # cái này của Phước ae comment thôi đừng xoá !!!!!!!!!!!!!!!!!!!!!!!!!.
stockfish_engine = StockfishEngine(stockfish_path, skill_level=STOCKFISH_LEVEL)  # Mức độ trung bình


ELO_PER_SKILL_LEVEL = {
    0: 1100, 1: 1250, 2: 1400, 3: 1550, 4: 1700, 5: 1850, 6: 2000, 7: 2150, 8: 2300, 9: 2450,
    10: 2600, 11: 2725, 12: 2850, 13: 2975, 14: 3100, 15: 3200, 16: 3300, 17: 3400, 18: 2475, 19: 3550, 20: 3600
}

stockfish_elo = ELO_PER_SKILL_LEVEL[STOCKFISH_LEVEL]
game_history = []


game_mode = get_game_mode(screen)
board = chess.Board()
tt = TranspositionTable(size_mb=128)
selected_square = None
legal_moves = []
clock = pygame.time.Clock()
running = True
final_depth_completed = 0

class MoveHistory:
    def __init__(self):
        self.moves = []  # List of tuples (white_move, black_move)
        self.current_move = {'white': None, 'black': None}
        self.last_depth = 0
        self.last_time = 0
        self.scroll_position = 0  # Vị trí cuộn, 0 là ở cuối (nước mới nhất)
    
    def add_move(self, move_san, is_white):
        if is_white:
            self.moves.append((move_san, None))
        else:
            if self.moves:
                last_white, _ = self.moves[-1]
                self.moves[-1] = (last_white, move_san)
        self.scroll_position = 0  # Reset về cuối khi có nước đi mới
    
    def get_visible_moves(self):
        start_idx = max(0, len(self.moves) - 10 - self.scroll_position)
        end_idx = len(self.moves) - self.scroll_position
        return self.moves[start_idx:end_idx]
    
    def get_move_number_start(self):
        total_moves = len(self.moves)
        visible_start = max(0, total_moves - 10 - self.scroll_position)
        return visible_start + 1
    
    def handle_scroll(self, scroll_up):
        if scroll_up:
            # Cuộn lên (xem nước cũ hơn)
            if self.scroll_position < len(self.moves) - 10:
                self.scroll_position += 1
        else:
            # Cuộn xuống (xem nước mới hơn)
            if self.scroll_position > 0:
                self.scroll_position -= 1

    def update_stats(self, depth, time):
        self.last_depth = depth
        self.last_time = time

    def history_move_list(self):
        history_lines = []
        for i, (white_move, black_move) in enumerate(self.moves, start=1):
            move_str = f"{i}. {white_move or ''} {black_move or ''}"
            history_lines.append(move_str)
        return " ".join(history_lines)

move_history = MoveHistory()

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
    
    # Dọn dẹp âm thanh khi thoát game
    pygame.mixer.quit()
    stockfish_engine.quit()
    pygame.quit()


if __name__ == "__main__":
    print()
    main()
