import chess
import chess.engine

class StockfishEngine:
    def __init__(self, stockfish_path, skill_level=10, threads=4, hash_size=128):
        """Khởi tạo Stockfish engine."""
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.engine.configure({"Skill Level": skill_level})
        self.engine.configure({"Threads": threads})
        self.engine.configure({"Hash": hash_size})

    def get_best_move(self, board, time_limit=0.5):
        """Tìm nước đi tốt nhất từ Stockfish."""
        try:
            result = self.engine.play(board, chess.engine.Limit(time=time_limit))
            return result.move
        except Exception as e:
            print(f"Error getting Stockfish move: {e}")
            return None

    def quit(self):
        """Đóng engine để giải phóng tài nguyên."""
        self.engine.quit()

    def calculate_elo(self, ai_elo, stockfish_elo, result, ai_color, k=32):
        """Tính toán Elo mới cho AI dựa trên kết quả trận đấu và màu cờ."""
        expected_score = 1 / (1 + 10 ** ((stockfish_elo - ai_elo) / 400))
        # Xác định điểm thực tế dựa trên màu cờ của AI
        if ai_color == chess.WHITE:
            actual_score = 1 if result == "1-0" else 0 if result == "0-1" else 0.5
        else:  # ai_color == chess.BLACK
            actual_score = 1 if result == "0-1" else 0 if result == "1-0" else 0.5
        new_elo = ai_elo + k * (actual_score - expected_score)
        return new_elo

