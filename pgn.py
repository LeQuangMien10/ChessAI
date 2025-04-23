import datetime
import os
import chess


def save_pgn(event, ai_color, opponent ,result, move_list):
    directory = "pgn_match"
    if not os.path.exists(directory):
        os.makedirs(directory)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%Hh%Mm%Ss")
    filename = os.path.join(directory, f"game_{timestamp}.txt")

    if ai_color is not None:
        if ai_color == chess.WHITE:
            white = "My AI"
            black = opponent
        else:
            white = opponent
            black = "My AI"
    else:
        if event == "PLAYER_VS_AI":
            white = "Human"
            black = "My AI"
        else:
            white = "My AI"
            black = "Human"


    pgn = f"[Event \"{event}\"]\n"
    pgn += f"[Date \"{timestamp}\"]\n"
    pgn += f"[White \"{white}\"]\n"
    pgn += f"[Black \"{black}\"]\n"
    pgn += f"[Result \"{result}\"]\n\n"
    pgn += move_list

    with open(filename, "w") as file:
        file.write(pgn)

