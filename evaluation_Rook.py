from config import *

ROOK_ON_SEMI_OPEN_FILE_BONUS = 15
ROOK_ON_OPEN_FILE_BONUS = 30
ROOK_ON_SEVENTH_RANK_BONUS = 40
CONNECTED_ROOK_BONUS = 0

def get_file_status(board_, file_index):
    """
    Kiểm tra trạng thái của cột
    :param board_: bàn cờ
    :param file_index: chỉ số của cột
    :return: (has_friendly_pawn, has_enemy_pawn)
    """

    friendly_color = board_.turn
    enemy_color = not friendly_color

    has_friendly_pawn = False
    has_enemy_pawn = False

    for rank_index in range(8):
        square = chess.square(file_index, rank_index)
        piece = board_.piece_at(square)
        if piece and piece.piece_type == chess.PAWN:
            if piece.color == friendly_color:
                has_friendly_pawn = True
            else:
                has_enemy_pawn = True
            if has_friendly_pawn and has_enemy_pawn:
                break
    return has_friendly_pawn, has_enemy_pawn

def evaluate_rooks(board: chess.Board, color: chess.Color) -> int:
    """ Tính điểm vị trí cho tất cả các Xe của phe 'color'. """
    rook_score = 0
    rook_squares = board.pieces(chess.ROOK, color)
    enemy_color = not color

    for square in rook_squares:
        file_index = chess.square_file(square)
        rank_index = chess.square_rank(square)

        # 1 & 2. Kiểm tra Cột Mở / Nửa Mở
        has_friendly_pawn_on_file = False
        has_enemy_pawn_on_file = False
        for r in range(8):
            p = board.piece_at(chess.square(file_index, r))
            if p and p.piece_type == chess.PAWN:
                if p.color == color:
                    has_friendly_pawn_on_file = True
                else:
                    has_enemy_pawn_on_file = True
                if has_friendly_pawn_on_file: # Nếu có tốt phe mình là cột đóng, không cần xét tiếp
                    break

        if not has_friendly_pawn_on_file:
            # Ít nhất là cột nửa mở cho phe mình
            rook_score += ROOK_ON_SEMI_OPEN_FILE_BONUS
            if not has_enemy_pawn_on_file:
                # Không có tốt nào -> Cột mở hoàn toàn
                rook_score += ROOK_ON_OPEN_FILE_BONUS # Cộng thêm bonus cho cột mở

        # 3. Kiểm tra Hàng Ngang Thứ 7
        target_rank = 6 if color == chess.WHITE else 1
        if rank_index == target_rank:
            rook_score += ROOK_ON_SEVENTH_RANK_BONUS

        # (Tùy chọn) 4. Kiểm tra Xe Kết Nối (đơn giản)
        # Ví dụ: cộng điểm nếu có Xe khác cùng phe bảo vệ nó
        # attackers = board.attackers(color, square)
        # for attacker_sq in attackers:
        #     attacker_piece = board.piece_at(attacker_sq)
        #     if attacker_piece and attacker_piece.piece_type == chess.ROOK:
        #         rook_score += CONNECTED_ROOK_BONUS # Cần định nghĩa CONNECTED_ROOK_BONUS
        #         break # Chỉ cần 1 Xe khác bảo vệ là đủ

    return rook_score

# --- Hàm Test ---
def test_evaluate_rooks():
    """ Chạy các test case cho hàm evaluate_rooks. """
    print("--- Starting Rook Evaluation Tests ---")
    tests_passed = 0
    tests_failed = 0

    test_cases = [
        {
            "name": "Initial Position",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "color": chess.WHITE,
            "expected_score": 0, # Xe bị chặn bởi Tốt
        },
        {
            "name": "White Rook on Semi-Open File (e-file)",
            "fen": "rnbqk2r/pppp1ppp/5n2/4p3/1b2P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 0 1", # Giả sử Re1 đã chơi
            # Tạo bàn cờ thực tế hơn:
            "fen": "4k3/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQ - 0 1", # Sau khi Trắng nhập thành cánh Vua
            # Bây giờ đặt Xe Trắng lên cột nửa mở (ví dụ cột d, không có tốt Trắng)
            "fen": "r3k2r/pp1ppppp/8/2p5/8/8/PPP1PPPP/R2RK2R w KQkq - 0 1", # Rd1, cột d nửa mở
            "color": chess.WHITE,
            "expected_score": ROOK_ON_SEMI_OPEN_FILE_BONUS, # Xe ở d1 có bonus
        },
        {
            "name": "White Rook on Open File (d-file)",
            # Cột d không có Tốt nào
            "fen": "r3k2r/pp2pppp/8/8/8/8/PP3PPP/R2RK2R w KQkq - 0 1",
            "color": chess.WHITE,
            # Rd1 trên cột mở hoàn toàn
            "expected_score": ROOK_ON_SEMI_OPEN_FILE_BONUS + ROOK_ON_OPEN_FILE_BONUS,
        },
         {
            "name": "Black Rook on Semi-Open File (c-file)",
            # Cột c không có Tốt Đen, có Tốt Trắng
            "fen": "r3k2r/pp2pppp/8/8/2P5/8/P4PPP/R3K2R b KQkq - 0 1", # Đặt Xe Đen ở c8
            "fen": "2r1k2r/pp2pppp/8/8/2P5/8/P4PPP/R3K2R b KQk - 0 1",
            "color": chess.BLACK,
            "expected_score": ROOK_ON_SEMI_OPEN_FILE_BONUS,
        },
        {
            "name": "Black Rook on Open File (d-file)",
            # Cột d không có Tốt nào
            "fen": "r3k2r/pp2pppp/8/8/8/8/PP3PPP/R3K2R b KQkq - 0 1", # Đặt Xe Đen ở d8
            "fen": "r2rk2r/pp2pppp/8/8/8/8/PP3PPP/R3K2R b KQ - 0 1", # Đã di chuyển Xe
            "color": chess.BLACK,
            "expected_score": ROOK_ON_SEMI_OPEN_FILE_BONUS + ROOK_ON_OPEN_FILE_BONUS,
        },
        {
            "name": "White Rook on 7th Rank (Open File)",
            # Xe Trắng ở d7, cột d mở
            "fen": "r3k2r/pp1Rpppp/8/8/8/8/PP3PPP/4K2R w Kkq - 0 1",
            "color": chess.WHITE,
            "expected_score": ROOK_ON_SEMI_OPEN_FILE_BONUS + ROOK_ON_OPEN_FILE_BONUS + ROOK_ON_SEVENTH_RANK_BONUS,
        },
        {
            "name": "White Rook on 7th Rank (Semi-Open File)",
            # Xe Trắng ở d7, cột d nửa mở (có tốt đen)
             "fen": "r3k2r/pp1Rpppp/8/3p4/8/8/PP3PPP/4K2R w Kkq - 0 1",
            "color": chess.WHITE,
            "expected_score": ROOK_ON_SEMI_OPEN_FILE_BONUS + ROOK_ON_SEVENTH_RANK_BONUS,
        },
        {
            "name": "Black Rook on 2nd Rank (Open File)",
            # Xe Đen ở d2, cột d mở
            "fen": "4k2r/pp3ppp/8/8/8/8/PPPrPPPP/R3K2R b Kk - 0 1",
            "color": chess.BLACK,
            "expected_score": ROOK_ON_SEMI_OPEN_FILE_BONUS + ROOK_ON_OPEN_FILE_BONUS + ROOK_ON_SEVENTH_RANK_BONUS,
        },
         {
            "name": "Black Rook on 2nd Rank (Semi-Open File)",
            # Xe Đen ở d2, cột d nửa mở (có tốt trắng)
            "fen": "4k2r/pp3ppp/8/8/3P4/8/PPPrPPPP/R3K2R b Kk - 0 1",
            "color": chess.BLACK,
            "expected_score": ROOK_ON_SEMI_OPEN_FILE_BONUS + ROOK_ON_SEVENTH_RANK_BONUS,
        },
        {
            "name": "Two White Rooks (Open + 7th)",
            # Ra1 (cột a mở), Rd7 (cột d mở + hàng 7)
            "fen": "1r2k2r/p2R1ppp/8/8/8/8/P4PPP/R3K2R w KQk - 0 1",
            "color": chess.WHITE,
            "expected_score": (ROOK_ON_SEMI_OPEN_FILE_BONUS + ROOK_ON_OPEN_FILE_BONUS) # Ra1
                           + (ROOK_ON_SEMI_OPEN_FILE_BONUS + ROOK_ON_OPEN_FILE_BONUS + ROOK_ON_SEVENTH_RANK_BONUS), # Rd7
        },
        {
            "name": "Two Black Rooks (Semi + Closed + 2nd)",
            # Ra8 (cột a đóng), Rd2 (cột d nửa mở + hàng 2)
            "fen": "r3k2r/p7/8/8/3P4/8/pPprPPPP/4K2R b Kkq - 0 1",
            "color": chess.BLACK,
            "expected_score": 0 # Ra8 (đóng)
                           + (ROOK_ON_SEMI_OPEN_FILE_BONUS + ROOK_ON_SEVENTH_RANK_BONUS), # Rd2
        },
         {
            "name": "Rook on Closed File",
            "fen": "r3k2r/p7/8/8/8/8/P7/R3K2R w KQkq - 0 1", # Ra1 có Tốt Trắng ở a2
            "color": chess.WHITE,
            "expected_score": 0,
        },
        {
            "name": "Rook on 7th but Closed File",
             # Rd7 có Tốt Trắng ở d2
            "fen": "r3k2r/p2Rpppp/8/8/8/8/P2P1PPP/4K2R w Kkq - 0 1",
            "color": chess.WHITE,
            "expected_score": ROOK_ON_SEVENTH_RANK_BONUS, # Vẫn được bonus hàng 7 dù cột đóng
        },

    ]

    for test in test_cases:
        board = chess.Board(test["fen"])
        result = evaluate_rooks(board, test["color"])
        expected = test["expected_score"]
        color_str = "White" if test["color"] == chess.WHITE else "Black"

        print(f"Testing: {test['name']} ({color_str})")
        print(f"  FEN: {test['fen']}")

        if result == expected:
            print(f"  PASSED! Score: {result}")
            tests_passed += 1
        else:
            print(f"  FAILED! Expected: {expected}, Got: {result}")
            tests_failed += 1
        print("-" * 20)

    print("--- Rook Evaluation Test Summary ---")
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print("--- End of Tests ---")

    return tests_failed == 0 # Trả về True nếu tất cả test thành công

# --- Chạy test ---
if __name__ == "__main__":
    # Nếu bạn chạy file này trực tiếp, nó sẽ thực hiện các bài test
    all_passed = test_evaluate_rooks()
    if all_passed:
        print("\nAll Rook evaluation tests passed successfully!")
    else:
        print("\nSome Rook evaluation tests failed.")