import pygame as pg
import time
import random
import math
import os
import socket
import json
import threading
import serial
from serial.tools import list_ports

pg.init()

WIDTH, HEIGHT = 1280, 720
FPS = 60
ITEM_SPAWN_INTERVAL = 2000
GAME_OVER_RESET_DELAY = 5000
PLAYER_MOVE_SPEED = 5
PLAYER_ROTATE_SPEED = 5
COUNTDOWN_TIME = 4

COLOR_DICT = {
    "LightGray": (150, 150, 150),
    "DarkGray": (36, 36, 36),
    "Gray": (180, 180, 180),
    "White": (255, 255, 255),
    "Black": (0, 0, 0),
    "Red": (150, 0, 0),
    "Blue": (0, 0, 150),
    "Green": (0, 255, 0),
    "Orange": (255, 165, 0)
}

screen = pg.display.set_mode((WIDTH, HEIGHT), pg.FULLSCREEN)
pg.display.set_caption("Grabbing Game")
clock = pg.time.Clock()

font_large = pg.font.Font(None, 100)
font_medium = pg.font.Font(None, 50)
font_small = pg.font.Font(None, 36)
font_countdown = pg.font.Font(None, 200)

GAME_SERVER_IP = '0.0.0.0'
GAME_SERVER_PORT = 12345

scoreboard_client_socket = None
scoreboard_client_address = None
server_running = False

def start_game_server():
    global scoreboard_client_socket, scoreboard_client_address, server_running
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((GAME_SERVER_IP, GAME_SERVER_PORT))
        server_socket.listen(1)
        server_socket.settimeout(0.5)
        print(f"Game server listening on {GAME_SERVER_IP}:{GAME_SERVER_PORT}")
        server_running = True
    except socket.error as e:
        print(f"Failed to start game server: {e}")
        server_running = False
        return

    while server_running:
        try:
            conn, addr = server_socket.accept()
            print(f"Scoreboard connected from {addr}")
            scoreboard_client_socket = conn
            scoreboard_client_address = addr
        except socket.timeout:
            pass
        except socket.error as e:
            print(f"Server accept error: {e}")
            break
    server_socket.close()
    print("Game server stopped.")

def send_scores_to_scoreboard(score_data):
    global scoreboard_client_socket
    if scoreboard_client_socket:
        try:
            scoreboard_client_socket.sendall(json.dumps(score_data).encode('utf-8') + b'\n')
            print(f"Sent scores to scoreboard: {score_data}")
        except socket.error as e:
            print(f"Error sending data to scoreboard: {e}. Closing connection.")
            scoreboard_client_socket.close()
            scoreboard_client_socket = None

server_thread = threading.Thread(target=start_game_server, daemon=True)
server_thread.start()

ARDUINO_SERIAL_PORT = 'COM3'
ARDUINO_BAUD_RATE = 115200

ser = None

def setup_serial():
    global ser
    print("Searching for Arduino COM ports...")
    ports = list_ports.comports()
    if not ports:
        print("No COM ports found. Please ensure Arduino is connected.")
    else:
        print("Available COM ports:")
        for p in ports:
            print(f"- {p.device} ({p.description})")

    try:
        ser = serial.Serial(ARDUINO_SERIAL_PORT, ARDUINO_BAUD_RATE, timeout=0.1)
        print(f"Connected to Arduino on {ARDUINO_SERIAL_PORT}")
    except serial.SerialException as e:
        print(f"Could not open serial port {ARDUINO_SERIAL_PORT}: {e}")
        print("Please check if Arduino is connected and the port is correct. Game will proceed without Arduino control.")
        ser = None

def read_arduino_data():
    if ser and ser.isOpen():
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                data = [int(x) for x in line.split(',')]
                if len(data) == 10:
                    return data
                else:
                    return None
        except ValueError as ve:
            return None
        except Exception as e:
            return None
    return None

def get_time_ms():
    return pg.time.get_ticks()

class TimerManager:
    def __init__(self):
        self.timers = {}

    def set_timer(self, timer_id, interval):
        self.timers[timer_id] = get_time_ms() + interval

    def check_timer(self, timer_id):
        if timer_id not in self.timers:
            self.set_timer(timer_id, 0)
            return False
        
        if get_time_ms() >= self.timers[timer_id]:
            self.set_timer(timer_id, 0)
            return True
        return False

    def check_and_reset_timer(self, timer_id, interval):
        if timer_id not in self.timers:
            self.set_timer(timer_id, interval)
            return False
        
        if get_time_ms() >= self.timers[timer_id]:
            self.set_timer(timer_id, interval)
            return True
        return False

timer_manager = TimerManager()

class Item(pg.sprite.Sprite):
    def __init__(self, x=-1, y=-1, scale=1.5):
        super().__init__()
        self.size = int(20 * scale)
        self.image = pg.Surface((self.size, self.size), pg.SRCALPHA)
        pg.draw.circle(self.image, COLOR_DICT["Gray"], (self.size // 2, self.size // 2), self.size // 2)
        
        pool_x_min = WIDTH // 2 - 200 + 35
        pool_x_max = WIDTH // 2 + 200 - 35
        pool_y_min = HEIGHT // 2 - 200 + 35
        pool_y_max = HEIGHT // 2 + 200 - 35

        if x == -1:
            x = random.randint(pool_x_min, pool_x_max)
        if y == -1:
            y = random.randint(pool_y_min, pool_y_max)
        
        self.rect = self.image.get_rect(center=(x, y))

    def pick(self):
        self.kill()

class Gripper(pg.sprite.Sprite):
    def __init__(self, player, player_id):
        super().__init__()
        self.original_image = pg.Surface((8, 20), pg.SRCALPHA)
        pg.draw.rect(self.original_image, COLOR_DICT["Black"], (0, 0, 8, 20))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=player.rect.center)
        self.player_id = player_id
        self.has_item = False
        self.is_key_pressed = False

    def update(self, player):
        player.has_item = self.has_item
        self.angle = player.angle
        rad = math.radians(self.angle)

        offset = 40
        nose_x = player.rect.centerx + math.cos(rad) * offset
        nose_y = player.rect.centery + math.sin(rad) * offset
        new_center = (nose_x, nose_y)

        self.image = pg.transform.rotate(self.original_image, -self.angle)
        self.rect = self.image.get_rect(center=new_center)

    def handle_grip_action(self, item_list):
        if self.is_key_pressed:
            if not self.has_item:
                collided_items = pg.sprite.spritecollide(self, item_list, False)
                if collided_items:
                    item = collided_items[0]
                    item.pick()
                    self.has_item = True
            else:
                item_list.add(Item(self.rect.centerx, self.rect.centery))
                self.has_item = False
            self.is_key_pressed = False

    def set_key_pressed(self):
        self.is_key_pressed = True

def map_joystick_to_speed(joystick_value, max_speed):
    dead_zone = 50
    
    normalized_value = joystick_value - 511.5 

    abs_value = abs(normalized_value)

    if abs_value < dead_zone:
        return 0

    threshold_low = 150
    threshold_mid = 300

    speed_level_1 = max_speed * 0.3
    speed_level_2 = max_speed * 0.6
    speed_level_3 = max_speed * 1.0
    
    if abs_value < threshold_low:
        speed = speed_level_1
    elif abs_value < threshold_mid:
        speed = speed_level_2
    else:
        speed = speed_level_3
    
    return speed if normalized_value > 0 else -speed

class Player(pg.sprite.Sprite):
    def __init__(self, x, y, image_path, gripped_image_path, player_id, scale=1.0):
        super().__init__()
        self.base_image_path = image_path
        self.gripped_image_path = gripped_image_path
        self.scale = scale
        
        self.original_images = {
            "normal": self._load_and_scale_image(self.base_image_path),
            "gripped": self._load_and_scale_image(self.gripped_image_path)
        }
        self.image = self.original_images["normal"]
        self.rect = self.image.get_rect(center=(x, y))
        
        self.angle = 0
        if player_id == 1:
            self.angle = 0
        elif player_id == 2:
            self.angle = 180

        self.move_speed = PLAYER_MOVE_SPEED
        self.rotate_speed = PLAYER_ROTATE_SPEED
        self.player_id = player_id
        self.has_item = False
        
        self.image = pg.transform.rotate(self.image, -self.angle)
        
    def _load_and_scale_image(self, path):
        original = pg.image.load(path).convert_alpha()
        width = int(original.get_width() * self.scale)
        height = int(original.get_height() * self.scale)
        return pg.transform.scale(original, (width, height))

    def update(self, move_forward_backward_speed, move_left_right_speed, rotate_speed_val):
        self.image = self.original_images["gripped"] if self.has_item else self.original_images["normal"]
        
        self.angle += rotate_speed_val 
        self.angle %= 360

        rad = math.radians(self.angle)

        dx_forward = math.cos(rad) * move_forward_backward_speed
        dy_forward = math.sin(rad) * move_forward_backward_speed

        dx_strafe = math.cos(rad + math.pi / 2) * move_left_right_speed
        dy_strafe = math.sin(rad + math.pi / 2) * move_left_right_speed

        self.rect.x += dx_forward + dx_strafe
        self.rect.y += dy_forward + dy_strafe

        old_center = self.rect.center
        self.image = pg.transform.rotate(self.image, -self.angle)
        self.rect = self.image.get_rect(center=old_center)
        
        self.rect.x = max(0, min(self.rect.x, WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, HEIGHT - self.rect.height))
        
class Pool(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        original_image = pg.image.load("assets/pool.png").convert_alpha()
        self.image = pg.transform.scale(original_image, (400, 400))
        self.rect = self.image.get_rect(center=(WIDTH / 2, HEIGHT / 2))

class Basket(pg.sprite.Sprite):
    def __init__(self, x, y, image_path, player_id):
        super().__init__()
        self.score = 0
        self.width = 70
        self.height = 100
        original_image = pg.image.load(image_path).convert_alpha()
        self.image = pg.transform.scale(original_image, (self.width, self.height))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.player_id = player_id

    def update(self, item_list):
        collided_items = pg.sprite.spritecollide(self, item_list, True)
        for _item in collided_items:
            self.score += 1

    def draw_score(self, surface):
        text = font_medium.render(str(self.score), False, COLOR_DICT["Black"])
        text_rect = text.get_rect(center=(self.rect.x + self.width // 2, self.rect.y + self.height // 2))
        surface.blit(text, text_rect)

class EndGame:
    def __init__(self, basket1, basket2):
        self.w = 600
        self.h = 400
        self.x = WIDTH // 2 - self.w // 2
        self.y = HEIGHT // 2 - self.h // 2
        
        self.msg1 = font_large.render("Game Over!", True, COLOR_DICT["Black"])
        self.msg2 = font_small.render(f"Player Blue Score: {basket1.score}", True, COLOR_DICT["Blue"])
        self.msg3 = font_small.render(f"Player Red Score: {basket2.score}", True, COLOR_DICT["Red"])
        
        self.msg1_rect = self.msg1.get_rect(center=(WIDTH // 2, self.y + self.h // 4))
        self.msg2_rect = self.msg2.get_rect(center=(WIDTH // 2, self.y + self.h // 2))
        self.msg3_rect = self.msg3.get_rect(center=(WIDTH // 2, self.y + self.h * 3 // 4))

    def draw(self, surface):
        pg.draw.rect(surface, COLOR_DICT["White"], (self.x, self.y, self.w, self.h))
        surface.blit(self.msg1, self.msg1_rect)
        surface.blit(self.msg2, self.msg2_rect)
        surface.blit(self.msg3, self.msg3_rect)
    
    def trigger_score_send(self, player1_score, player2_score):
        total_score = player1_score + player2_score
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        data = {"score": total_score, "timestamp": timestamp}
        send_scores_to_scoreboard(data)

class TMinus:
    def __init__(self, total_time_seconds=60):
        self.total_time = total_time_seconds
        self.time_left = total_time_seconds
        self.is_playing = True

    def update(self, delta_time_ms):
        if self.is_playing:
            self.time_left -= delta_time_ms / 1000
            if self.time_left <= 0:
                self.time_left = 0
                self.is_playing = False

    def draw(self, surface):
        minutes = int(self.time_left // 60)
        seconds = int(self.time_left % 60)
        time_str = f"{minutes:02}:{seconds:02}"
        
        text = font_medium.render(time_str, True, COLOR_DICT["Black"])
        text_rect = text.get_rect(center=(WIDTH // 2, 50))
        
        padding = 20
        bg_rect = pg.Rect(text_rect.x - padding, text_rect.y - padding,
                            text_rect.width + 2 * padding, text_rect.height + 2 * padding)
        pg.draw.rect(surface, COLOR_DICT["Gray"], bg_rect, border_radius=5)
        
        surface.blit(text, text_rect)

class MenuButton:
    def __init__(self, x, y, width, height, player_id):
        self.rect = pg.Rect(x, y, width, height)
        self.player_id = player_id
        self.is_ready = False
        self.initial_text = "Press to Ready!"
        self.ready_text = "Ready"
        self._update_text_surface()

    def _update_text_surface(self):
        current_text = self.ready_text if self.is_ready else self.initial_text
        self.text_surface = font_medium.render(current_text, True, COLOR_DICT["White"])
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def draw(self, surface):
        color = COLOR_DICT["Green"] if self.is_ready else COLOR_DICT["Orange"]
        pg.draw.rect(surface, color, self.rect, border_radius=10)
        surface.blit(self.text_surface, self.text_rect)

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.is_ready = not self.is_ready
            self._update_text_surface()
            return True
        return False

    def reset(self):
        self.is_ready = False
        self._update_text_surface()

class MainMenu:
    def __init__(self):
        self.player1_img = pg.transform.scale(pg.image.load("assets/player2.png").convert_alpha(), (350, 150))
        self.player2_img = pg.transform.scale(pg.image.load("assets/player1.png").convert_alpha(), (350, 150))

        self.player1_rect = self.player1_img.get_rect(center=(WIDTH // 4 + 30, HEIGHT // 2 - 100))
        self.player2_rect = self.player2_img.get_rect(center=(WIDTH * 3 // 4 + 30, HEIGHT // 2 - 100))

        button_width = 280
        button_height = 80
        self.button1 = MenuButton(WIDTH // 4 - button_width // 2, HEIGHT // 2 + 50, button_width, button_height, 1)
        self.button2 = MenuButton(WIDTH * 3 // 4 - button_width // 2, HEIGHT // 2 + 50, button_width, button_height, 2)

    def draw(self, surface):
        surface.fill(COLOR_DICT["DarkGray"])
        surface.blit(self.player1_img, self.player1_rect)
        surface.blit(self.player2_img, self.player2_rect)
        self.button1.draw(surface)
        self.button2.draw(surface)

    def handle_mouse_click(self, pos):
        self.button1.handle_click(pos)
        self.button2.handle_click(pos)

    def both_players_ready(self):
        return self.button1.is_ready and self.button2.is_ready
    
    def reset_buttons(self):
        self.button1.reset()
        self.button2.reset()

class GameState:
    MAIN_MENU = 0
    COUNTDOWN = 1
    PLAYING = 2
    GAME_OVER = 3

    def __init__(self):
        self.state = self.MAIN_MENU
        self.countdown_start_time = 0
        self.current_countdown_value = COUNTDOWN_TIME

    def set_state(self, new_state):
        self.state = new_state
        if new_state == self.COUNTDOWN:
            self.countdown_start_time = get_time_ms()
            self.current_countdown_value = COUNTDOWN_TIME

    def get_state(self):
        return self.state
    
    def update_countdown(self):
        if self.state == self.COUNTDOWN:
            elapsed_time = (get_time_ms() - self.countdown_start_time) / 1000
            self.current_countdown_value = COUNTDOWN_TIME - math.ceil(elapsed_time)
            if self.current_countdown_value <= 0:
                self.set_state(self.PLAYING)

    def draw_countdown(self, surface):
        if self.state == self.COUNTDOWN:
            countdown_text = str(max(1, self.current_countdown_value))
            text_surface = font_countdown.render(countdown_text, True, COLOR_DICT["Red"])
            text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            surface.blit(text_surface, text_rect)

game_state_manager = GameState()

def reset_game():
    global player1, player2, gripper1, gripper2, pool, basket1, basket2, play_time, end_game_screen
    
    background_sprites.empty()
    item_list.empty()
    player_sprites.empty()
    
    basket_width = 70
    player_display_width = 150
    
    basket1_x = 50
    basket1_y = HEIGHT / 2 - 50
    basket2_x = WIDTH - 50 - basket_width
    basket2_y = HEIGHT / 2 - 50

    pool_center_x = WIDTH // 2
    pool_center_y = HEIGHT // 2
    pool_radius = 200

    distance_from_pool_edge = 100
    
    player1_x = pool_center_x - pool_radius - distance_from_pool_edge
    player1_y = HEIGHT / 2

    player2_x = pool_center_x + pool_radius + distance_from_pool_edge
    player2_y = HEIGHT / 2

    player1 = Player(player1_x, player1_y, "assets/player2.png", "assets/player2_griped.png", 1, 1.5)
    player2 = Player(player2_x, player2_y, "assets/player1.png", "assets/player1_griped.png", 2, 1.5)
    gripper1 = Gripper(player1, 1)
    gripper2 = Gripper(player2, 2)

    pool = Pool()
    basket1 = Basket(basket1_x, basket1_y, "assets/player2_basket.png", 1)
    basket2 = Basket(basket2_x, basket2_y, "assets/player1_basket.png", 2)

    background_sprites.add(pool, basket1, basket2)
    player_sprites.add(player1, gripper1, player2, gripper2)
    
    play_time = TMinus(total_time_seconds=60)
    end_game_screen = None
    timer_manager.timers.clear()

background_sprites = pg.sprite.Group()
item_list = pg.sprite.Group()
player_sprites = pg.sprite.Group()

main_menu = MainMenu()

player1 = None
player2 = None
gripper1 = None
gripper2 = None
pool = None
basket1 = None
basket2 = None
play_time = None
end_game_screen = None

setup_serial()

running = True
last_tick = get_time_ms()

while running:
    current_tick = get_time_ms()
    delta_time = current_tick - last_tick
    last_tick = current_tick

    arduino_data = read_arduino_data()
    
    p1_move_forward_backward = 0
    p1_move_left_right = 0
    p1_rotate_speed = 0
    p1_grab_action = False
    p1_ready_action = False

    p2_move_forward_backward = 0
    p2_move_left_right = 0
    p2_rotate_speed = 0
    p2_grab_action = False
    p2_ready_action = False

    if arduino_data and len(arduino_data) >= 10:
        p1_move_x_arduino = arduino_data[0]
        p1_move_y_arduino = arduino_data[1]
        p1_rotate_x_arduino = arduino_data[2]
        
        p2_move_x_arduino = arduino_data[3]
        p2_move_y_arduino = arduino_data[4]
        p2_rotate_x_arduino = arduino_data[5]

        p1_ready_action = (arduino_data[6] == 1)
        p1_grab_action = (arduino_data[7] == 1)
        p2_ready_action = (arduino_data[8] == 1)
        p2_grab_action = (arduino_data[9] == 1)

        p1_move_forward_backward = map_joystick_to_speed(p1_move_y_arduino, player1.move_speed)
        p1_move_left_right = map_joystick_to_speed(p1_move_x_arduino, player1.move_speed)
        p1_rotate_speed = map_joystick_to_speed(p1_rotate_x_arduino, player1.rotate_speed)
        
        p2_move_forward_backward = map_joystick_to_speed(p2_move_y_arduino, player2.move_speed)
        p2_move_left_right = map_joystick_to_speed(p2_move_x_arduino, player2.move_speed)
        p2_rotate_speed = map_joystick_to_speed(p2_rotate_x_arduino, player2.rotate_speed)

    else:
        keys = pg.key.get_pressed()
        
        if keys[pg.K_w]:
            p1_move_forward_backward = player1.move_speed
        elif keys[pg.K_s]:
            p1_move_forward_backward = -player1.move_speed
        
        if keys[pg.K_a]:
            p1_move_left_right = -player1.move_speed
        elif keys[pg.K_d]:
            p1_move_left_right = player1.move_speed

        if keys[pg.K_q]:
            p1_rotate_speed = -player1.rotate_speed
        elif keys[pg.K_e]:
            p1_rotate_speed = player1.rotate_speed

        if keys[pg.K_UP]:
            p2_move_forward_backward = player2.move_speed
        elif keys[pg.K_DOWN]:
            p2_move_forward_backward = -player2.move_speed

        if keys[pg.K_LEFT]:
            p2_move_left_right = -player2.move_speed
        elif keys[pg.K_RIGHT]:
            p2_move_left_right = player2.move_speed

        if keys[pg.K_KP4]:
            p2_rotate_speed = -player2.rotate_speed
        elif keys[pg.K_KP6]:
            p2_rotate_speed = player2.rotate_speed
        
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
            server_running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                running = False
                server_running = False
            
            if game_state_manager.get_state() == GameState.MAIN_MENU:
                if event.key == pg.K_LSHIFT and not main_menu.button1.is_ready:
                    p1_ready_action = True 
                if event.key == pg.K_RSHIFT and not main_menu.button2.is_ready:
                    p2_ready_action = True
            
            elif game_state_manager.get_state() == GameState.PLAYING:
                if event.key == pg.K_f:
                    p1_grab_action = True
                if event.key == pg.K_m:
                    p2_grab_action = True

    if game_state_manager.get_state() == GameState.MAIN_MENU:
        if p1_ready_action:
            main_menu.button1.is_ready = True
            main_menu.button1._update_text_surface()
        if p2_ready_action:
            main_menu.button2.is_ready = True
            main_menu.button2._update_text_surface()

        if main_menu.both_players_ready():
            game_state_manager.set_state(GameState.COUNTDOWN)
            reset_game()

    elif game_state_manager.get_state() == GameState.COUNTDOWN:
        game_state_manager.update_countdown()
        
    elif game_state_manager.get_state() == GameState.PLAYING:
        play_time.update(delta_time)

        if play_time.is_playing:
            player1.update(p1_move_forward_backward, p1_move_left_right, p1_rotate_speed)
            player2.update(p2_move_forward_backward, p2_move_left_right, p2_rotate_speed)
            
            gripper1.update(player1)
            gripper2.update(player2)

            if p1_grab_action:
                gripper1.set_key_pressed()
            if p2_grab_action:
                gripper2.set_key_pressed()
            
            gripper1.handle_grip_action(item_list)
            gripper2.handle_grip_action(item_list)
            
            basket1.update(item_list)
            basket2.update(item_list)

            if timer_manager.check_and_reset_timer("item_spawn", ITEM_SPAWN_INTERVAL):
                item_list.add(Item())
        else:
            game_state_manager.set_state(GameState.GAME_OVER)
            end_game_screen = EndGame(basket1, basket2)
            end_game_screen.trigger_score_send(basket1.score, basket2.score)
            timer_manager.set_timer("game_over_reset", GAME_OVER_RESET_DELAY)

    elif game_state_manager.get_state() == GameState.GAME_OVER:
        if timer_manager.check_timer("game_over_reset"):
            game_state_manager.set_state(GameState.MAIN_MENU)
            main_menu.reset_buttons()

    screen.fill(COLOR_DICT["LightGray"])

    if game_state_manager.get_state() == GameState.MAIN_MENU:
        main_menu.draw(screen)
    
    elif game_state_manager.get_state() == GameState.COUNTDOWN:
        background_sprites.draw(screen)
        item_list.draw(screen)
        player_sprites.draw(screen)
        basket1.draw_score(screen)
        basket2.draw_score(screen)
        play_time.draw(screen)
        game_state_manager.draw_countdown(screen)
        
    elif game_state_manager.get_state() == GameState.PLAYING:
        background_sprites.draw(screen)
        item_list.draw(screen)
        player_sprites.draw(screen)

        basket1.draw_score(screen)
        basket2.draw_score(screen)
        play_time.draw(screen)

    elif game_state_manager.get_state() == GameState.GAME_OVER:
        background_sprites.draw(screen)
        item_list.draw(screen)
        player_sprites.draw(screen)
        basket1.draw_score(screen)
        basket2.draw_score(screen)
        play_time.draw(screen)
        
        if end_game_screen:
            end_game_screen.draw(screen)

    pg.display.flip()

    clock.tick(FPS)

if ser:
    ser.close()
    print("Serial port closed.")

pg.quit()