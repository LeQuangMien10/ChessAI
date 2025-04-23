import pygame.mixer
import chess

class SoundManager:
    def __init__(self):
        # Khởi tạo mixer nếu chưa được khởi tạo
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        # Load các âm thanh
        try:
            self.move_sound = pygame.mixer.Sound("sounds/move.mp3")
            self.capture_sound = pygame.mixer.Sound("sounds/capture.mp3")
            self.check_sound = pygame.mixer.Sound("sounds/check.mp3")
            self.castle_sound = pygame.mixer.Sound("sounds/castle.mp3")
            
            # Điều chỉnh âm lượng cho từng loại âm thanh
            self.move_sound.set_volume(0.5)
            self.capture_sound.set_volume(0.5)
            self.check_sound.set_volume(0.5)
            self.castle_sound.set_volume(0.5)
            
        except:
            print("Warning: Could not load some sound files")
            # Tạo dummy sound để tránh lỗi
            dummy = pygame.mixer.Sound(buffer=bytes([0]*44))
            self.move_sound = self.capture_sound = self.check_sound = self.castle_sound = dummy

    def play_move_sound(self, board, move):
        """Phát âm thanh tương ứng với loại nước đi"""
        # Kiểm tra nước nhập thành
        if board.is_castling(move):
            self.castle_sound.play()
            return
        
        # Kiểm tra nước bắt quân
        if board.is_capture(move):
            self.capture_sound.play()
            return
        
        # Thực hiện nước đi để kiểm tra chiếu
        board.push(move)
        if board.is_check():
            self.check_sound.play()
        else:
            self.move_sound.play()
        board.pop()

    def play_lobby_music(self):
        """Phát nhạc lobby"""
        try:
            pygame.mixer.music.load("sounds/lobby.mp3")
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
        except:
            print("Warning: Could not play lobby music")

    def stop_lobby_music(self):
        """Dừng nhạc lobby"""
        try:
            pygame.mixer.music.stop()
        except:
            print("Warning: Could not stop lobby music")

# Tạo instance toàn cục để sử dụng trong toàn bộ game
sound_manager = SoundManager() 