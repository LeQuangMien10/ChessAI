from config import *

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


def choose_promotion_onlyQ():
    """Hiển thị lựa chọn quân phong cấp, trả về mã quân cờ (hậu, xe, mã, tượng)."""
    # Ở đây ta mặc định phong cấp thành Hậu (Queen)
    return chess.QUEEN


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


def draw_info_panel(screen, move_history):
    # Vẽ background đen cho panel bên phải
    info_panel = pygame.Rect(BOARD_SIZE, 0, 200, BOARD_SIZE)
    pygame.draw.rect(screen, (0, 0, 0), info_panel)
    
    # Font cho bảng
    font = pygame.font.Font(None, 24)
    
    # Vẽ bảng nước đi
    header_y = 20
    headers = ["#", "White", "Black"]
    col_widths = [30, 80, 80]
    x_start = BOARD_SIZE + 10
    
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
        thumb_height = max(20, scrollbar_height * visible_ratio)
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
