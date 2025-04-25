import pygame
import sys
from config import *  # Import tất cả từ config, bao gồm WINDOW_WIDTH và BOARD_SIZE
from sounds import sound_manager

pygame.mixer.init()

# Load nhạc lobby
try:
    LOBBY_MUSIC = pygame.mixer.music.load("sounds/lobby.mp3")
    pygame.mixer.music.set_volume(0.3)
except:
    print("Warning: Could not load lobby music")

# Load hình ảnh menu
try:
    BACKGROUND = pygame.image.load("images/menu/background.jpg")
    BACKGROUND = pygame.transform.scale(BACKGROUND, (SCREEN_WIDTH, BOARD_SIZE))
    
    TITLE = pygame.image.load("images/menu/title.webp")
    # Thu nhỏ logo
    original_width = TITLE.get_width()
    original_height = TITLE.get_height()
    target_width = 250  # Giảm kích thước logo
    target_height = int(original_height * (target_width / original_width))  # Giữ tỷ lệ
    TITLE = pygame.transform.scale(TITLE, (target_width, target_height))
except:
    print("Warning: Could not load some menu images")

# Định nghĩa các màu
BUTTON_NORMAL = (50, 50, 50)      # Xám đậm
BUTTON_HOVER = (100, 100, 100)    # Xám sáng
BUTTON_BORDER = (200, 200, 200)   # Viền trắng
TEXT_COLOR = (255, 255, 255)      # Chữ trắng

class Button:
    def __init__(self, x, y, width, height, text, font_size=32):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.is_hovered = False
        
        # Màu sắc cho button
        self.normal_color = BUTTON_NORMAL
        self.hover_color = BUTTON_HOVER
        self.border_color = BUTTON_BORDER
        self.text_color = TEXT_COLOR
        
        # Render text
        self.text_surface = self.font.render(text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def draw(self, screen):
        # Vẽ button với viền
        color = self.hover_color if self.is_hovered else self.normal_color
        pygame.draw.rect(screen, self.border_color, self.rect, border_radius=10)  # Vẽ viền
        pygame.draw.rect(screen, color, self.rect.inflate(-4, -4), border_radius=8)  # Vẽ nền
        
        # Vẽ text
        screen.blit(self.text_surface, self.text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

def draw_animated_background(screen, time):
    # Vẽ background
    screen.blit(BACKGROUND, (0, 0))
    
    # Thêm lớp overlay để làm tối background một chút
    overlay = pygame.Surface((SCREEN_WIDTH, BOARD_SIZE))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(100)  # Độ trong suốt cố định
    screen.blit(overlay, (0, 0))

def get_game_mode(screen):
    sound_manager.play_lobby_music()
    clock = pygame.time.Clock()
    
    # Thu nhỏ kích thước button và điều chỉnh khoảng cách
    button_width = 250  # Chiều rộng button
    button_height = 40  # Giảm chiều cao button xuống
    spacing = 15       # Giảm khoảng cách giữa các button
    top_margin = 50    # Tăng khoảng cách từ trên xuống
    bottom_margin = 30 # Khoảng cách từ dưới lên
    
    # Tính toán layout tổng thể
    title_height = TITLE.get_height()
    total_button_height = (button_height * 3) + (spacing * 2)  # Tổng chiều cao phần buttons (giảm xuống 3 buttons)
    
    # Tính khoảng cách từ trên xuống để căn đều
    total_content_height = title_height + 25 + total_button_height  # Giảm khoảng cách giữa title và buttons xuống 25
    available_height = BOARD_SIZE - (top_margin + bottom_margin)  # Chiều cao khả dụng sau khi trừ margins
    
    # Điểm bắt đầu từ trên xuống, thêm top_margin
    start_y = top_margin + (available_height - total_content_height) // 2
    
    # Vị trí title
    title_x = (SCREEN_WIDTH - TITLE.get_width()) // 2
    title_y = start_y
    
    # Vị trí buttons (bắt đầu sau title)
    button_x = (SCREEN_WIDTH - button_width) // 2
    first_button_y = title_y + title_height + 25  # Giảm khoảng cách giữa title và button đầu tiên

    buttons = [
        Button(button_x, first_button_y + (button_height + spacing) * 0, button_width, button_height, "Player vs Player"),
        Button(button_x, first_button_y + (button_height + spacing) * 1, button_width, button_height, "Player vs AI"),
        Button(button_x, first_button_y + (button_height + spacing) * 2, button_width, button_height, "AI vs Player")
    ]

    while True:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            for i, button in enumerate(buttons):
                if button.handle_event(event):
                    sound_manager.stop_lobby_music()
                    return [TWO_PLAYERS, PLAYER_VS_AI, AI_VS_PLAYER][i]

        # Vẽ background
        draw_animated_background(screen, current_time)
        
        # Vẽ tiêu đề
        screen.blit(TITLE, (title_x, title_y))
        
        # Vẽ các button
        for button in buttons:
            button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)