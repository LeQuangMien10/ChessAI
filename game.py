from config import *
from sounds import sound_manager

# Load ảnh quân cờ
pieces = {}
for piece in chess.PIECE_SYMBOLS[1:]:  # 'p', 'n', 'b', 'r', 'q', 'k'
    pieces[piece] = pygame.image.load(f"images/{piece}.png")
    pieces[piece.upper()] = pygame.image.load(f"images/{piece.upper()}_.png")


# Hàm vẽ bàn cờ
def draw_board(screen, selected_square=None, legal_moves=None, last_move=None, board=None):
    if legal_moves is None:
        legal_moves = []

    font = pygame.font.SysFont(None, 24)  # Có thể đổi font, size tuỳ ý

    for row in range(8):
        for col in range(8):
            color = WHITE if (row + col) % 2 == 0 else BLACK
            if selected_square == chess.square(col, 7 - row):
                color = HIGHLIGHT
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

            # Vẽ ký hiệu cột (a–h) ở hàng cuối cùng
            if row == 7:
                label = font.render(chr(ord('a') + col), True, (0, 0, 0) if color == WHITE else (255, 255, 255))
                screen.blit(label, (col * SQUARE_SIZE + 4, 8 * SQUARE_SIZE - 20))

            # Vẽ ký hiệu hàng (1–8) ở cột đầu tiên
            if col == 0:
                label = font.render(str(8 - row), True, (0, 0, 0) if color == WHITE else (255, 255, 255))
                screen.blit(label, (4, row * SQUARE_SIZE + 4))

    # Highlight các nước đi hợp lệ
    for move in legal_moves:
        col, row = chess.square_file(move), chess.square_rank(move)
        pygame.draw.circle(screen, MOVE_HIGHLIGHT[:3],
                           (col * SQUARE_SIZE + SQUARE_SIZE // 2, (7 - row) * SQUARE_SIZE + SQUARE_SIZE // 2), 10)

    # Highlight nước đi cuối cùng
    if last_move and board:
        # Xác định màu của quân cờ vừa đi
        piece = board.piece_at(last_move.to_square)
        if piece and piece.color == chess.WHITE:
            highlight_color = LAST_MOVE_HIGHLIGHT
        else:
            highlight_color = LAST_MOVE_HIGHLIGHT

        # Vẽ ô bắt đầu
        start_col, start_row = chess.square_file(last_move.from_square), chess.square_rank(last_move.from_square)
        start_rect = pygame.Rect(start_col * SQUARE_SIZE, (7 - start_row) * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        highlight_surface.fill(highlight_color)
        screen.blit(highlight_surface, start_rect)

        # Vẽ ô kết thúc
        end_col, end_row = chess.square_file(last_move.to_square), chess.square_rank(last_move.to_square)
        end_rect = pygame.Rect(end_col * SQUARE_SIZE, (7 - end_row) * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        highlight_surface.fill(highlight_color)
        screen.blit(highlight_surface, end_rect)


# Hàm vẽ quân cờ
def draw_pieces(screen, board):
    for square in chess.SQUARES:
        piece_ = board.piece_at(square)
        if piece_:
            row, col = divmod(square, 8)
            screen.blit(pieces[piece_.symbol()], (col * SQUARE_SIZE, (7 - row) * SQUARE_SIZE))


def get_square_from_mouse(pos):
    col, row = pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE
    return chess.square(col, 7 - row)


def promote_pawn(board, move, screen):
    """Kiểm tra nếu quân tốt đi đến hàng cuối và yêu cầu phong cấp bằng Pygame."""
    piece_ = board.piece_at(move.from_square)

    if piece_ and piece_.piece_type == chess.PAWN:
        last_rank = 7 if piece_.color == chess.WHITE else 0  # Lấy hàng cuối cùng cho từng màu
        if chess.square_rank(move.to_square) == last_rank:  # Kiểm tra tốt đã đến hàng cuối chưa
            color = "white" if piece_.color == chess.WHITE else "black"
            promotion_choice = choose_promotion_pygame(screen, color)
            move.promotion = promotion_choice


def choose_promotion_pygame(screen, colorTurn):
    """Hiển thị menu chọn quân phong cấp bằng hình ảnh trong Pygame."""
    choices_for_white = {
        "Q": (chess.QUEEN, "images/Q_.png"),
        "R": (chess.ROOK, "images/R_.png"),
        "B": (chess.BISHOP, "images/B_.png"),
        "N": (chess.KNIGHT, "images/N_.png")
    }
    choices_for_black = {
        "Q": (chess.QUEEN, "images/q.png"),
        "R": (chess.ROOK, "images/r.png"),
        "B": (chess.BISHOP, "images/b.png"),
        "N": (chess.KNIGHT, "images/n.png")
    }
    if colorTurn == "black":
        choices = choices_for_black
    else:
        choices = choices_for_white

        # Tạo vùng hiển thị menu
    menu_rect = pygame.Rect(90, 140, 280, 80)
    pygame.draw.rect(screen, (220, 220, 220), menu_rect, border_radius=10)  # Bo góc nhẹ

    # Load ảnh và hiển thị lên màn hình
    button_rects = []
    x_offset = 105
    y_offset = 155
    for key, (piece_, img_path) in choices.items():
        img = pygame.image.load(img_path)
        img = pygame.transform.scale(img, (50, 50))  # Điều chỉnh kích thước ảnh

        btn_rect = screen.blit(img, (x_offset, y_offset))
        button_rects.append((btn_rect, piece_))

        x_offset += 65  # Dịch chuyển ảnh tiếp theo

    pygame.display.flip()

    # Chờ người chơi chọn quân phong cấp
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for btn_rect, piece_ in button_rects:
                    if btn_rect.collidepoint(event.pos):
                        return piece_


def draw_info_panel(screen, move_history, game_mode, stockfish_level):
    # Vẽ background cho panel bên phải
    info_panel = pygame.Rect(BOARD_SIZE, 0, 201, BOARD_SIZE)
    pygame.draw.rect(screen, (105, 117, 101), info_panel)

    # Font cho bảng
    font_size = 24
    font = pygame.font.Font(None, font_size)

    # Vẽ bảng nước đi
    header_y = 60
    headers = ["#", "White", "Black"]
    col_widths = [30, 80, 80]
    x_start = BOARD_SIZE + 10


    #Xác định màu người chơi, AI, Stockfish
    elo_stockfish = ELO_PER_SKILL_LEVEL[stockfish_level]
    with open("elo.txt", "r") as file:
        ai_elo = float(file.readline().strip())
    ai_elo_round_number = round(ai_elo)
    if game_mode == AI_VS_PLAYER:
        player_white = "My AI"
        player_black = "Human"
        elo_white = ai_elo_round_number
        elo_black = "?"
    elif game_mode  == PLAYER_VS_AI:
        player_white = "Human"
        player_black = "My AI"
        elo_white = "?"
        elo_black = ai_elo_round_number
    elif game_mode== TWO_PLAYERS:
        player_white = "Human 1"
        player_black = "Human 2"
        elo_white = "?"
        elo_black = "?"
    else:
        if not STOCKFISH_WHITE:
            player_white = "My AI"
            player_black = "Stockfish " + str(stockfish_level)
            elo_white = ai_elo_round_number
            elo_black = elo_stockfish
        else:
            player_white = "Stockfish " + str(stockfish_level)
            player_black = "My AI"
            elo_white = elo_stockfish
            elo_black = ai_elo_round_number

    # Vẽ tên người chơi
    white_player_text = font.render(f"{player_white}", True, (255, 255, 255))
    black_player_text = font.render(f"{player_black}", True, (255, 255, 255))
    screen.blit(white_player_text, (x_start + 30, 10))  # Tên người chơi trắng
    screen.blit(black_player_text, (x_start + 30, 30))  # Tên người chơi đen

    # Vẽ elo
    white_elo_text = font.render(f"({elo_white})", True, (255, 255, 255))
    black_elo_text = font.render(f"({elo_black})", True, (255, 255, 255))
    elo_x_position = x_start + 100 + 20
    screen.blit(white_elo_text, (elo_x_position, 10))
    screen.blit(black_elo_text, (elo_x_position, 30))

    # Vẽ hình vuông trắng cho người chơi trắng
    pygame.draw.rect(screen, (255, 255, 255), (x_start - font_size + 25, 10, font_size - 10, font_size - 10))
    # Vẽ hình vuông đen cho người chơi đen
    pygame.draw.rect(screen, (0, 0, 0), (x_start - font_size + 25, 30, font_size - 10, font_size - 10))

    # Vẽ header
    for i, header in enumerate(headers):
        x = x_start + sum(col_widths[:i])
        text = font.render(header, True, (255, 255, 255))
        screen.blit(text, (x, header_y))

    # Vẽ đường kẻ ngang dưới header
    pygame.draw.line(screen, (255, 255, 255),
                     (x_start, header_y + 25),
                     (x_start + sum(col_widths), header_y + 25))

    # Vẽ các nước đi
    moves = move_history.get_visible_moves()
    start_move_number = move_history.get_move_number_start()
    row_height = 22

    # Vẽ vùng hiển thị nước đi với viền
    moves_area = pygame.Rect(x_start - 5, header_y + 30,
                             sum(col_widths) + 10, row_height * 10 + 5)
    pygame.draw.rect(screen, (30, 30, 30), moves_area, 1)  # Vẽ viền

    for row, (white, black) in enumerate(moves):
        y = header_y + 35 + row * row_height
        move_num = start_move_number + row

        # Highlight nước mới nhất khi đang ở cuối
        is_latest_move = (row == len(moves) - 1 and move_history.scroll_position == 0)
        if is_latest_move:
            highlight_rect = pygame.Rect(x_start - 5, y - 2,
                                         sum(col_widths) + 10, row_height)
            pygame.draw.rect(screen, (50, 50, 50), highlight_rect)

        # Số thứ tự
        num_text = font.render(str(move_num), True, (255, 255, 255))
        screen.blit(num_text, (x_start, y))

        # Nước trắng
        if white:
            white_text = font.render(white, True, (255, 255, 255))
            screen.blit(white_text, (x_start + col_widths[0], y))

        # Nước đen
        if black:
            black_text = font.render(black, True, (255, 255, 255))
            screen.blit(black_text, (x_start + col_widths[0] + col_widths[1], y))

    # Vẽ thanh cuộn
    if len(move_history.moves) > 10:
        scrollbar_x = x_start + sum(col_widths) + 15
        scrollbar_height = row_height * 10
        scrollbar_rect = pygame.Rect(scrollbar_x, header_y + 35, 5, scrollbar_height)
        pygame.draw.rect(screen, (100, 100, 100), scrollbar_rect)

        # Vẽ nút cuộn
        total_moves = len(move_history.moves)
        visible_ratio = 10 / total_moves
        thumb_height = max(20, int(scrollbar_height * visible_ratio))
        thumb_pos = (scrollbar_height - thumb_height) * (move_history.scroll_position / (total_moves - 10))
        thumb_rect = pygame.Rect(scrollbar_x, header_y + 35 + thumb_pos, 5, thumb_height)
        pygame.draw.rect(screen, (200, 200, 200), thumb_rect)

    # Vẽ thông tin depth và time
    info_y = header_y + 300
    pygame.draw.line(screen, (255, 255, 255),
                     (x_start, info_y - 10),
                     (x_start + sum(col_widths), info_y - 10))

    depth_text = font.render(f"Depth: {move_history.last_depth}", True, (255, 255, 255))
    time_text = font.render(f"Time: {move_history.last_time:.2f}s", True, (255, 255, 255))

    screen.blit(depth_text, (x_start, info_y))
    screen.blit(time_text, (x_start, info_y + 30))


def play_move_sound(board, move):
    """
    Phát âm thanh tương ứng với loại nước đi
    """
    sound_manager.play_move_sound(board, move)


import pygame
import sys


def choose_stockfish_level_gui(screen):
    pygame.init()

    # Load background image
    background = pygame.image.load("images/menu/background.jpg")

    font = pygame.font.Font(None, 48)
    input_text = ""
    clock = pygame.time.Clock()

    input_box = pygame.Rect(50, 160, 200, 50)  # Ô nhập level

    while True:
        screen.blit(background, (0, 0))  # Hiển thị ảnh nền

        # Hiển thị hướng dẫn
        instruction = font.render("Enter Stockfish Level (0-20):", True, (255, 255, 255))
        screen.blit(instruction, (50, 100))

        # Vẽ ô nhập với viền
        pygame.draw.rect(screen, (200, 200, 200), input_box, 2)

        # Hiển thị text đã nhập
        input_surface = font.render(input_text, True, (255, 255, 255))
        screen.blit(input_surface, (input_box.x + 10, input_box.y + 10))

        # Thêm dòng "Click Enter"
        enter_hint = font.render("Click Enter", True, (255, 255, 255))
        screen.blit(enter_hint, (input_box.x, input_box.y + 80))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    try:
                        level = int(input_text)
                        if 0 <= level <= 20:
                            return level
                        else:
                            input_text = ""  # reset nếu không hợp lệ
                    except ValueError:
                        input_text = ""  # reset nếu không hợp lệ
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.unicode.isdigit():
                    input_text += event.unicode

        pygame.display.flip()
        clock.tick(30)

