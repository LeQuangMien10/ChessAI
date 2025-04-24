# AI CHESS ENGINE
Dự án của sinh viên khoa _Công nghệ thông tin_ của _trường Đại học Công Nghệ - Đại học Quốc gia Hà Nội (UET)_ thực hiện trong môn học _Trí tuệ nhân tạo AI_ nhằm mục đích lấy điểm thành phần.
## Tác giả
 **_Group 5_**
| Tên                            | MSV       |
|--------------------------------|-----------|
| Lê Quang Miền                  | 23021621  |
| Mạch Trần Quang Nhật           | 23021653  |
| Nguyễn Thành Phước             | 23021665  |

## Cài Đặt
- Download zip và giải nén dự án tại link ...
- Dùng IDE thích hợp và thêm các thư viện cần thiết: python-chess, pygame, ...
- Mở file, tìm đến thư mục _main.py_ và **_RUN_**
- Hoặc ...
## Giới thiệu
- Dự án **_AI CHESS ENGINE_** là một hệ thống AI chơi cờ vua được phát triển bằng **_ngôn ngữ Python_** và sử dụng **_pygame_** và **_chess_** để hỗ trợ tạo giao diện.
- Mục tiêu của dự án là xây dựng một đối thủ có khả năng phân tích sâu, chơi thông minh và phản ứng nhanh trong mọi tình huống trên bàn cờ.
- Dự án phù hợp để học tập về thuật toán AI trong trò chơi, nghiên cứu chiến thuật cờ vua, hoặc đơn giản là một thử thách thú vị cho người chơi muốn đối đầu với một AI chiến lược.

  ![mainScreen](https://github.com/LeQuangMien10/ChessAI/blob/MinimaxAI/images/Readme_demo/mainScreen.png)
  ![gameScreen](https://github.com/LeQuangMien10/ChessAI/blob/MinimaxAI/images/Readme_demo/gameScreen.png)
## Tính năng
- AI có thể tính được độ sâu tối đa là 10 và ra quyết định thực hiện nước đi với thời gian < 10s
- Người dùng có thể chọn 1 trong 4 chế độ chơi:
  + **_PLAYER vs PLAYER_**: 2 người chơi có thể so tài với nhau.
  + **_PLAYER vs AI_**: Người chơi sẽ so tài với bot **"_My AI_"** và cầm quân **_Trắng_**.
  + **_AI vs PLAYER_**: Người chơi sẽ so tài với bot **_"My AI"_** và cầm quân **_Đen_**.
  + **_AI vs AI_**: bot **_My AI_** sẽ so tài với engine **_Stockfish_** với các cấp độ khác nhau. Chức năng này còn giúp nhà phát triển đánh giá được Elo của bot **"_My AI_"**
## Kỹ thuật áp dụng
- Negamax Algorithm
- Alpha-Beta Pruning
- Iterative Deepening
- Quiescence Search
- Evaluate Position
- ...
