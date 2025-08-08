import pygame as pg
import datetime
import time
import socket
import json
import threading
import collections

WIDTH, HEIGHT = 600, 720

COLOR_DICT = {
    "White": (255, 255, 255),
    "Black": (0, 0, 0),
    "DarkGray": (36, 36, 36),
    "LightGray": (150, 150, 150),
    "Green": (0, 255, 0),
    "Yellow": (255, 255, 0),
    "Orange": (255, 165, 0)
}

GAME_SERVER_IP = input("Enter IP Address ")
GAME_SERVER_PORT = 12345
pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("High Scores")
font_large = pg.font.Font(None, int(HEIGHT * 0.12))
font_medium = pg.font.Font(None, int(HEIGHT * 0.06))
font_small = pg.font.Font(None, int(HEIGHT * 0.045))

received_scores_data = []
scores_lock = threading.Lock()

client_running = False
client_socket = None

def format_timestamp_to_hms(timestamp_str):
    try:
        dt_object = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return dt_object.strftime("%H:%M:%S")
    except ValueError:
        return "N/A"

def get_highest_scores(scores_list):
    scores_list.sort(key=lambda x: x[0], reverse=True)
    return scores_list

def draw_high_scores(surface, high_scores_data):
    surface.fill(COLOR_DICT["DarkGray"])

    title_text = font_large.render("HIGH SCORES", True, COLOR_DICT["White"])
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT * 0.15))
    surface.blit(title_text, title_rect)

    panel_width = WIDTH * 0.85
    panel_height = HEIGHT * 0.7
    panel_x = (WIDTH - panel_width) // 2
    panel_y = HEIGHT * 0.25
    pg.draw.rect(surface, COLOR_DICT["Black"], (panel_x, panel_y, panel_width, panel_height), border_radius=int(HEIGHT * 0.015))
    pg.draw.rect(surface, COLOR_DICT["LightGray"], (panel_x, panel_y, panel_width, panel_height), int(WIDTH * 0.005), border_radius=int(HEIGHT * 0.015))

    header_font = font_medium
    
    header_text_rank = header_font.render("Rank", True, COLOR_DICT["White"])
    header_text_score = header_font.render("Highest Score", True, COLOR_DICT["Yellow"])
    header_text_time = header_font.render("Time", True, COLOR_DICT["Orange"])

    header_rank_rect = header_text_rank.get_rect(center=(panel_x + panel_width * 0.15, panel_y + panel_height * 0.1))
    header_score_rect = header_text_score.get_rect(center=(panel_x + panel_width * 0.45, panel_y + panel_height * 0.1))
    header_time_rect = header_text_time.get_rect(center=(panel_x + panel_width * 0.80, panel_y + panel_height * 0.1))

    surface.blit(header_text_rank, header_rank_rect)
    surface.blit(header_text_score, header_score_rect)
    surface.blit(header_text_time, header_time_rect)

    pg.draw.line(surface, COLOR_DICT["LightGray"], (panel_x + panel_width * 0.03, panel_y + panel_height * 0.18),
                 (panel_x + panel_width * 0.97, panel_y + panel_height * 0.18), int(WIDTH * 0.004))

    start_y_content = panel_y + panel_height * 0.25
    row_padding_y = int(HEIGHT * 0.015)

    current_rank = 1

    for i, (total_score, timestamp_str) in enumerate(high_scores_data[:5]):
        if i > 0 and total_score < high_scores_data[i-1][0]:
            current_rank = i + 1

        rank_text = font_medium.render(str(current_rank), True, COLOR_DICT["White"])
        score_text = font_medium.render(str(total_score), True, COLOR_DICT["Green"])
        time_text_formatted = format_timestamp_to_hms(timestamp_str)
        time_text = font_small.render(time_text_formatted, True, COLOR_DICT["LightGray"])

        max_height = max(rank_text.get_height(), score_text.get_height(), time_text.get_height())
        row_height = max_height + 2 * row_padding_y

        current_row_y = start_y_content + i * row_height
        
        rank_text_width = rank_text.get_width()
        rank_cell_center_x = panel_x + panel_width * 0.15
        rank_rect_outer = pg.Rect(rank_cell_center_x - (rank_text_width / 2) - row_padding_y, current_row_y - row_padding_y,
                                  rank_text_width + 2 * row_padding_y, row_height)
        pg.draw.rect(surface, COLOR_DICT["DarkGray"], rank_rect_outer, border_radius=int(HEIGHT * 0.008))
        pg.draw.rect(surface, COLOR_DICT["LightGray"], rank_rect_outer, 1, border_radius=int(HEIGHT * 0.008))
        rank_text_rect = rank_text.get_rect(center=rank_rect_outer.center)
        surface.blit(rank_text, rank_text_rect)

        score_text_width = score_text.get_width()
        score_cell_center_x = panel_x + panel_width * 0.45
        score_rect_outer = pg.Rect(score_cell_center_x - (score_text_width / 2) - row_padding_y, current_row_y - row_padding_y,
                                   score_text_width + 2 * row_padding_y, row_height)
        pg.draw.rect(surface, COLOR_DICT["DarkGray"], score_rect_outer, border_radius=int(HEIGHT * 0.008))
        pg.draw.rect(surface, COLOR_DICT["LightGray"], score_rect_outer, 1, border_radius=int(HEIGHT * 0.008))
        score_text_rect = score_text.get_rect(center=score_rect_outer.center)
        surface.blit(score_text, score_text_rect)

        time_text_width = time_text.get_width()
        time_cell_center_x = panel_x + panel_width * 0.80
        time_rect_outer = pg.Rect(time_cell_center_x - (time_text_width / 2) - row_padding_y, current_row_y - row_padding_y,
                                  time_text_width + 2 * row_padding_y, row_height)
        pg.draw.rect(surface, COLOR_DICT["DarkGray"], time_rect_outer, border_radius=int(HEIGHT * 0.008))
        pg.draw.rect(surface, COLOR_DICT["LightGray"], time_rect_outer, 1, border_radius=int(HEIGHT * 0.008))
        time_text_rect = time_text.get_rect(center=time_rect_outer.center)
        surface.blit(time_text, time_text_rect)

def connect_to_game_server():
    global client_socket, client_running
    client_running = True
    buffer = ""
    while client_running:
        if not client_socket:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(1)
                client_socket.connect((GAME_SERVER_IP, GAME_SERVER_PORT))
                print(f"Connected to game server at {GAME_SERVER_IP}:{GAME_SERVER_PORT}")
            except socket.error as e:
                print(f"Could not connect to game server: {e}. Retrying in 2 seconds...")
                client_socket = None
                time.sleep(2)
                continue

        try:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                print("Game server disconnected. Attempting to reconnect...")
                client_socket.close()
                client_socket = None
                continue
            
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                try:
                    received_data = json.loads(line)
                    score = received_data.get('score')
                    timestamp = received_data.get('timestamp')
                    if score is not None and timestamp is not None:
                        with scores_lock:
                            received_scores_data.append((score, timestamp))
                            global current_display_scores
                            current_display_scores = get_highest_scores(list(received_scores_data))[:5]
                            print(f"Received score: {score}, Timestamp: {timestamp}")
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {line}")
        except socket.timeout:
            pass
        except socket.error as e:
            print(f"Socket error with game server: {e}. Reconnecting...")
            if client_socket:
                client_socket.close()
            client_socket = None
            time.sleep(1)
    
    if client_socket:
        client_socket.close()
    print("Scoreboard client stopped.")

client_thread = threading.Thread(target=connect_to_game_server, daemon=True)
client_thread.start()

current_display_scores = []

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
            client_running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                running = False
                client_running = False

    with scores_lock:
        draw_high_scores(screen, current_display_scores)

    pg.display.flip()

pg.quit()