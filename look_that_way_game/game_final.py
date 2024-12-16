from enum import Enum
import random
import RPi.GPIO as GPIO
import pigpio
from time import sleep, time

import cv2  # OpenCV
import mediapipe as mp
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import numpy as np

import os
import pygame, pigame
from pygame.locals import *
import csv
from datetime import datetime

### COMMAND TO RUN FINAL GAME: ###

# sudo -E sh /home/pi/look_that_way_game/game.sh

### CONSTANTS ###

# ALLOWED PINS WITH NO SECOND USE/PITFT: 5, 6, 12, 13, 16, 19, and 26

# GPIO pins
UP_PIN = 26
RIGHT_PIN = 13
DOWN_PIN = 16
LEFT_PIN = 6
LOOK_BASE_GIMBAL_PIN = 12
LOOK_HEAD_GIMBAL_PIN = 19
POINT_BASE_GIMBAL_PIN = 4
POINT_HEAD_GIMBAL_PIN = 5
# RESTART_PIN = 22  # Restart button (active low)
# QUIT_PIN = 17     # Quit button (active low)
BAILOUT_BUTTON = 27

# Need to run "sudo pigpiod" to start daemon before running
# Need to run "sudo killall pigpiod" to stop daemon when done

FREQ = 50                       # 50 Hz = 20 ms period

# CPU looker gimbal duty cycles using hardware PWM - values multiplied by 10,000 because of 0-1M scale
LEFT_LOOK_DC = 60000            # 50 Hz @ 6% duty cycle = 1.2 ms pulse width
CENTER_BASE_LOOK_DC = 90000     # 50 Hz @ 9% duty cycle = 1.8 ms pulse width
RIGHT_LOOK_DC = 120000          # 50 Hz @ 12% duty cycle = 2.4 ms pulse width
UP_LOOK_DC = 40000              # 50 Hz @ 4% duty cycle = 0.8 ms pulse width
CENTER_HEAD_LOOK_DC = 65000     # 50 Hz @ 6.5% duty cycle = 1.3 ms pulse width
DOWN_LOOK_DC = 90000            # 50 Hz @ 9% duty cycle = 1.8 ms pulse width

# CPU pointer gimbal duty cycles using hardware timed PWM - values multiplied by 100
LEFT_POINT_DC = 805             # 50 Hz @ 8.05% duty cycle =  1.61 ms pulse width
CENTER_BASE_POINT_DC = 1055     # 50 Hz @ 10.55% duty cycle = 2.11 ms pulse width
RIGHT_POINT_DC = 1305           # 50 Hz @ 13.05% duty cycle = 2.61 ms pulse width
UP_POINT_DC = 700               # 50 Hz @ 7% duty cycle = 1.4 ms pulse width
CENTER_HEAD_POINT_DC = 1000     # 50 Hz @ 10 duty cycle = 2 ms pulse width
DOWN_POINT_DC = 1300            # 50 Hz @ 13% duty cycle = 2.6 ms pulse width

# Set up GPIOs
GPIO.setmode(GPIO.BCM)
# GPIO.setwarnings(False)
GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(RESTART_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(QUIT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BAILOUT_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

### CPU MOVEMENT FUNCTIONS ###

pi = pigpio.pi()

# Configure hardware-timed PWM GPIOs for pointer gimbal (range 10000 instead of 1M)
pi.set_PWM_range(POINT_BASE_GIMBAL_PIN, 10000)
pi.set_PWM_range(POINT_HEAD_GIMBAL_PIN, 10000)
pi.set_PWM_frequency(POINT_BASE_GIMBAL_PIN, FREQ)
pi.set_PWM_frequency(POINT_HEAD_GIMBAL_PIN, FREQ)

def stop_PWM():
    pi.hardware_PWM(LOOK_BASE_GIMBAL_PIN, FREQ, 0)
    pi.hardware_PWM(LOOK_HEAD_GIMBAL_PIN, FREQ, 0)
    pi.set_PWM_dutycycle(POINT_BASE_GIMBAL_PIN, 0)
    pi.set_PWM_dutycycle(POINT_HEAD_GIMBAL_PIN, 0)

# CPU pointer gimbal actuation functions

def cpu_point_left():
    pi.set_PWM_dutycycle(POINT_BASE_GIMBAL_PIN, LEFT_POINT_DC)   

def cpu_point_right():
    pi.set_PWM_dutycycle(POINT_BASE_GIMBAL_PIN, RIGHT_POINT_DC)   

def cpu_point_up():
    pi.set_PWM_dutycycle(POINT_HEAD_GIMBAL_PIN, UP_POINT_DC)

def cpu_point_down():
    pi.set_PWM_dutycycle(POINT_HEAD_GIMBAL_PIN, DOWN_POINT_DC)   

def cpu_point_center():
    pi.set_PWM_dutycycle(POINT_BASE_GIMBAL_PIN, CENTER_BASE_POINT_DC)
    pi.set_PWM_dutycycle(POINT_HEAD_GIMBAL_PIN, CENTER_HEAD_POINT_DC)

# CPU looker gimbal actuation functions

def cpu_look_left():
    pi.hardware_PWM(LOOK_BASE_GIMBAL_PIN, FREQ, LEFT_LOOK_DC)   

def cpu_look_right():
    pi.hardware_PWM(LOOK_BASE_GIMBAL_PIN, FREQ, RIGHT_LOOK_DC)   

def cpu_look_up():
    pi.hardware_PWM(LOOK_HEAD_GIMBAL_PIN, FREQ, UP_LOOK_DC)

def cpu_look_down():
    pi.hardware_PWM(LOOK_HEAD_GIMBAL_PIN, FREQ, DOWN_LOOK_DC)   

def cpu_look_center():
    pi.hardware_PWM(LOOK_BASE_GIMBAL_PIN, FREQ, CENTER_BASE_LOOK_DC)
    pi.hardware_PWM(LOOK_HEAD_GIMBAL_PIN, FREQ, CENTER_HEAD_LOOK_DC)

### GPIO CALLBACKS ###

def dpad_callback(direction):
    global user_choice
    if user_choice == "":
        user_choice = direction
        print(f"User chose {user_choice}.")

GPIO.add_event_detect(UP_PIN, GPIO.FALLING, callback=lambda channel: dpad_callback("UP"), bouncetime=300)
GPIO.add_event_detect(RIGHT_PIN, GPIO.FALLING, callback=lambda channel: dpad_callback("RIGHT"), bouncetime=300)
GPIO.add_event_detect(DOWN_PIN, GPIO.FALLING, callback=lambda channel: dpad_callback("DOWN"), bouncetime=300)
GPIO.add_event_detect(LEFT_PIN, GPIO.FALLING, callback=lambda channel: dpad_callback("LEFT"), bouncetime=300)

# def restart_game_callback(channel):
#     global restart_flag
#     print("Restart button pressed!")
#     restart_flag = True
# GPIO.add_event_detect(RESTART_PIN, GPIO.FALLING, callback=restart_game_callback, bouncetime=300)

# def quit_game_callback(channel):
#     global quit_flag
#     print("Quit button pressed!")
#     quit_flag = True
# GPIO.add_event_detect(QUIT_PIN, GPIO.FALLING, callback=quit_game_callback, bouncetime=300)

def bailout_callback(channel):
    global code_run
    global total_runtime
    global init_time
    print("Bailout button pressed!")
    draw_quitting_screen()
    code_run = False
GPIO.add_event_detect(BAILOUT_BUTTON, GPIO.FALLING, callback=bailout_callback, bouncetime=300)

### GAME SOUNDS ###

# pygame.init()
# pygame.mixer.init()
# path = "/home/pi/look_that_way_game/sounds/"

# pygame.mixer.music.load(f"{path}game_music.mp3")

# # Load and play background music in the MAIN_MENU stage
# def start_background_music():
#     pygame.mixer.music.play(loops=-1, start=0.0)  # loops=-1 for infinite loop
#     pygame.mixer.music.set_volume(0.5)

# # Stop background music in the GAME_OVER stage
# def stop_background_music():
#     pygame.mixer.music.stop()

# short_beep = pygame.mixer.Sound(f"{path}short_beep.wav")
# short_beep.set_volume(0.5)

# long_beep = pygame.mixer.Sound(f"{path}long_beep.wav")
# long_beep.set_volume(0.5)   

# game_over_sound = pygame.mixer.Sound(f"{path}game_over_sound.wav")
# game_over_sound.set_volume(0.5)   

# game_over_speech = pygame.mixer.Sound(f"{path}game_over_speech.wav")
# game_over_speech.set_volume(0.5)   

# timing_buzzer = pygame.mixer.Sound(f"{path}timing_buzzer.wav")
# timing_buzzer.set_volume(0.5)

# next_level_sound = pygame.mixer.Sound(f"{path}next_level.wav")
# next_level_sound.set_volume(0.5)

# score_sound = pygame.mixer.Sound(f"{path}score.wav")
# score_sound.set_volume(0.5)

# success_sound = pygame.mixer.Sound(f"{path}success.wav")
# success_sound.set_volume(0.5)

### COMPUTER VISION ###

cap = cv2.VideoCapture(-1)

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5,min_tracking_confidence=0.5)

def get_head_camera(time_length):
    global cpu_choice 
    init_time = time()
    max_dir, max_count = "DOWN", 0
    dir_dict = {
        "oop": 0,
        "DOWN": 0,
        "UP": 0,
        "RIGHT": 0,
        "LEFT": 0,
    }
    actuated = False
    while time_length > time() - init_time:
        if (time() - init_time > 0.25 * time_length) and not actuated:
            # CPU action and result evaluation
            # sleep(1)
            cpu_choice = Directions.select_random_direction()
            actuate_CPU_point(cpu_choice)
            print(f"CPU pointed {cpu_choice}.")
            actuated = True
        ret, frame = cap.read()
        results = face_mesh.process(frame)
        frame.flags.writeable = True
        img_h , img_w, img_c = frame.shape
        face_2d = []
        face_3d = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                for idx, lm in enumerate(face_landmarks.landmark):
                    if idx == 33 or idx == 263 or idx ==1 or idx == 61 or idx == 291 or idx==199:
                        if idx ==1:
                            nose_2d = (lm.x * img_w,lm.y * img_h)
                            nose_3d = (lm.x * img_w,lm.y * img_h,lm.z * 3000)
                        x,y = int(lm.x * img_w),int(lm.y * img_h)

                        face_2d.append([x,y])
                        face_3d.append(([x,y,lm.z]))

                face_2d = np.array(face_2d,dtype=np.float64)
                face_3d = np.array(face_3d,dtype=np.float64)
                focal_length = 1 * img_w
                cam_matrix = np.array([[focal_length,0,img_h/2],
                                    [0,focal_length,img_w/2],
                                    [0,0,1]])
                distortion_matrix = np.zeros((4,1),dtype=np.float64)
                success,rotation_vec,translation_vec = cv2.solvePnP(face_3d,face_2d,cam_matrix,distortion_matrix)

                rmat,jac = cv2.Rodrigues(rotation_vec)
                angles,mtxR,mtxQ,Qx,Qy,Qz = cv2.RQDecomp3x3(rmat)

                x = angles[0] * 360
                y = angles[1] * 360
                z = angles[2] * 360

                # Calculate rotation angle based on axis
                if y < -5:
                    text="RIGHT"
                elif y > 5:
                    text="LEFT"
                elif x < -2.5:
                    text="DOWN"
                elif x > 15:
                    text="UP"
                else:
                    text="Forward"
            if text != "Forward":
                dir_dict[text] += 1
            # print(dir_dict)
    for key, value in dir_dict.items():
        if value > max_count:
            max_dir, max_count = key, value
    # print(max_dir)
    return max_dir

### GAME LOGIC ###

class States(Enum):
    MAIN_MENU = 1
    USER_POINTER = 2
    USER_LOOKER = 3
    GAME_OVER = 4
    LEADERBOARD = 5
    UPDATE = 6
    RULES = 7

class Directions:
    left = "LEFT"
    right = "RIGHT"
    up = "UP"
    down = "DOWN"
    dirs = [left, right, up, down]
    def select_random_direction():
        rand_dir = random.randint(0, 3)
        # return "UP" # Uncomment to debug/cheat (CPU always picks up)
        return Directions.dirs[rand_dir]

# Countdown printing function
def countdown_timer(round_number):
    global user_choice
    global score
    global msg1
    global msg2
    # Calculate sleep time based on the round number (faster countdown as the rounds progress)
    sleep_time = max(1 - (round_number - 1) * 0.1, 0.1)  # Minimum sleep time of 0.1 seconds
    
    # Print countdown
    for i in range(3, 0, -1):
        draw_gameplay_screen(level, score, msg1, msg2, i, "", "")
        print(i)
        # short_beep.play()
        sleep(sleep_time)
        if user_choice != "":  # User acted too early
            print("You acted too early!")
            msg1 = ("Too early!")
            msg2 = ("You lose.")
            # timing_buzzer.play()
            draw_gameplay_screen(level, score, msg1, msg2, "", "", "")
            sleep(4)
            return False
    print("GO!")
    draw_gameplay_screen(level, score, msg1, msg2, "GO!", "", "")
    # long_beep.play()
    return True

def actuate_CPU_look(dir):
    if dir == "UP":
        cpu_look_up()
    elif dir == "DOWN":
        cpu_look_down()
    elif dir == "LEFT":
        cpu_look_left()
    elif dir == "RIGHT":
        cpu_look_right()

def actuate_CPU_point(dir):
    if dir == "UP":
        cpu_point_up()
    elif dir == "DOWN":
        cpu_point_down()
    elif dir == "LEFT":
        cpu_point_left()
    elif dir == "RIGHT":
        cpu_point_right()

state = States.MAIN_MENU
next_state = None
input_window = 2  # Allowable time after countdown for user input
score_multiplier = 1
level = 1
score = 0
points_per_score = 1
high_score = False
msg1 = ""
msg2 = ""

### LEADERBOARD HANDLING ###

name = "AAA"
char_0 = 1
char_1 = 2
char_2 = 3
cursor = 0

def update_best_scores(file_path, new_name, new_score, new_date):
    # Read the current entries from the CSV file
    try:
        with open(file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            entries = [row for row in reader]
    except (FileNotFoundError, IOError):
        # If the file does not exist or is empty, initialize an empty list
        entries = []

    # Convert score to integer and sort existing entries by score (descending)
    for entry in entries:
        entry['score'] = int(entry['score'])

    # Create the new entry
    new_entry = {
        'name': new_name,
        'score': int(new_score),
        'date': new_date
    }

    # Insert the new entry and sort by score in descending order
    entries.append(new_entry)
    entries.sort(key=lambda x: x['score'])

    # Keep only the top 5 entries
    entries = entries[1:6]

    # Write back to the CSV file
    with open(file_path, mode='w', newline='') as file:
        fieldnames = ['name', 'score', 'date']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Write the header
        writer.writeheader()

        # Write the entries
        for entry in entries:
            writer.writerow(entry)

def high_score_check(file_path, new_score):
    global high_score
    high_score = False
    try:
        with open(file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            entries = [row for row in reader]
    except (FileNotFoundError, IOError):
        # If the file does not exist or is empty, initialize an empty list
        entries = []

    # Convert score to integer and sort existing entries by score (descending)
    for entry in entries:
        entry['score'] = int(entry['score'])

    # print(int(entries[0]["score"]))
    if new_score > int(entries[0]["score"]):
        high_score = True
    return high_score

## SCREEN SETUP ###

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (39, 119, 20)

# Uncomment to run on PiTFT
os.putenv("SDL_VIDEODRV", "fbcon")
os.putenv("SDL_FBDEV", "/dev/fb0")
os.putenv("SDL_MOUSEDRV", "dummy")
os.putenv("SDL_MOUSEDEV", "/dev/null")
os.putenv("DISPLAY", "")

# Initialize pygame and pigame
pygame.init()
pitft = pigame.PiTft()

pygame.mouse.set_visible(False) # Comment when debugging on monitor

# Setup screen and size parameters
size = width, height = 320, 240
screen = pygame.display.set_mode(size)

# Font size
font_extra_large = pygame.font.Font(None, 70)
font_large = pygame.font.Font(None, 50)
font_medium = pygame.font.Font(None, 38)
font_small = pygame.font.Font(None, 25)
font_extra_small = pygame.font.Font(None, 20)
font_tiny = pygame.font.Font(None, 15)

# state = "STARTUP"

### TOUCHSCREEN BUTTONS ###

main_menu_buttons = {
    "Rules": [font_small, (40, 215)],
    "Leaderboard": [font_small, (160, 215)],
    "Quit": [font_small, (280, 215)],
    "Start": [font_medium, (160, 160)],
}

game_over_buttons = {
    "Next": [font_small, (280, 215)]
}

rules_buttons = {
    "Main Menu": [font_small, (265, 20)]
}

leaderboard_buttons = {
    "Quit": [font_small, (60, 20)], 
    "Main Menu": [font_small, (260, 20)]
}

update_buttons = {
    "Clear": [font_small, (40, 215)],
    "Next": [font_small, (100, 215)],
    "Increment Letter": [font_extra_small, (260, 110)],
    "Decrement Letter": [font_extra_small, (260, 160)],
    "Move Cursor": [font_extra_small, (260, 210)],
}

def draw_buttons(buttons_dict):
    for k, v in buttons_dict.items():
        font = v[0]
        center = v[1]
        text_surface = font.render("%s" % k, True, WHITE)
        rect = text_surface.get_rect(center=center)
        screen.fill(GREEN,rect)
        screen.blit(text_surface, rect)

### DRAW SCREEN FUNCTIONS ###

def draw_main_menu_screen():
    screen.fill(BLACK)
    draw_buttons(main_menu_buttons)
    text_surface = font_large.render("Welcome to", True, WHITE)
    rect = text_surface.get_rect(center=(160, 60))
    screen.blit(text_surface, rect)
    text_surface = font_large.render("Look That Way!", True, WHITE)
    rect = text_surface.get_rect(center=(160, 100))
    screen.blit(text_surface, rect)
    pygame.display.update() 

def draw_gameplay_screen(level, score, dialogue1, dialogue2, count, cpu_move, user_move):
    screen.fill(BLACK)
    text_surface = font_small.render("Level: ", True, WHITE)
    rect = text_surface.get_rect(center=(106, 20))
    screen.blit(text_surface, rect)

    text_surface = font_small.render(str(level), True, WHITE)
    rect = text_surface.get_rect(center=(106, 40))
    screen.blit(text_surface, rect)

    text_surface = font_small.render("Score: ", True, WHITE)
    rect = text_surface.get_rect(center=(212, 20))
    screen.blit(text_surface, rect)

    text_surface = font_small.render(str(score), True, WHITE)
    rect = text_surface.get_rect(center=(212, 40))
    screen.blit(text_surface, rect)

    text_surface = font_medium.render(dialogue1, True, WHITE)
    rect = text_surface.get_rect(center=(160, 70))
    screen.blit(text_surface, rect)

    text_surface = font_small.render(dialogue2, True, WHITE)
    rect = text_surface.get_rect(center=(160, 100))
    screen.blit(text_surface, rect)

    if count == "GO!":
        color = GREEN
    else:
        color = WHITE
    text_surface = font_extra_large.render(str(count), True, color)
    rect = text_surface.get_rect(center=(160, 155))
    screen.blit(text_surface, rect)

    text_surface = font_small.render("CPU Action: ", True, WHITE)
    rect = text_surface.get_rect(center=(51, 220))
    screen.blit(text_surface, rect)

    text_surface = font_small.render(cpu_move, True, WHITE)
    rect = text_surface.get_rect(center=(125, 220))
    screen.blit(text_surface, rect)

    text_surface = font_small.render("Your Action: ", True, WHITE)
    rect = text_surface.get_rect(center=(210, 220))
    screen.blit(text_surface, rect)

    text_surface = font_small.render(user_move, True, WHITE)
    rect = text_surface.get_rect(center=(290, 220))
    screen.blit(text_surface, rect)
    pygame.display.update()

def draw_game_over_screen(level, score):
    screen.fill(BLACK)
    text_surface = font_large.render("GAME OVER", True, WHITE)
    rect = text_surface.get_rect(center=(160, 40))
    screen.blit(text_surface, rect)

    text_surface = font_medium.render("Final Level: ", True, WHITE)
    rect = text_surface.get_rect(center=(160, 90))
    screen.blit(text_surface, rect)

    text_surface = font_medium.render(str(level), True, WHITE)
    rect = text_surface.get_rect(center=(160, 120))
    screen.blit(text_surface, rect)

    text_surface = font_medium.render("Final Score: ", True, WHITE)
    rect = text_surface.get_rect(center=(160, 150))
    screen.blit(text_surface, rect)

    text_surface = font_medium.render(str(score), True, WHITE)
    rect = text_surface.get_rect(center=(160, 180))
    screen.blit(text_surface, rect)

    draw_buttons(game_over_buttons)
    pygame.display.update()

def draw_rules_screen():
    screen.fill(BLACK)
    rules = [
    "There are two primary objectives in this game.",
    "As the pointer, use the d-pad to input points.",
    "Try to point in the same direction the CPU is looking.",
    "But don't point too early or too late! You'll lose!",
    "As the looker, keep your head facing the camera.",
    "The looker must not look in the direction the CPU's points.",
    "Lose the game by looking in the CPU's pointed direction.",
    "Get points by pointing in the direction of the CPU's look.",
    "The point value is scaled by two factors:",
    "1. The current game level",
    "2. The number of consecutive correct points",
]

    text_surface = font_large.render("Rules ", True, WHITE)
    rect = text_surface.get_rect(center=(160, 35))
    screen.blit(text_surface, rect)
    start = 70
    for i in rules:
        text_surface = font_tiny.render(i, True, WHITE)
        rect = text_surface.get_rect(center=(160, start))
        # rect.topright = (x, y)
        screen.blit(text_surface, rect)
        start += 15
    draw_buttons(rules_buttons)
    pygame.display.update()

def draw_leaderboard_screen():
    screen.fill(BLACK)
    text_surface = font_medium.render("Leaderboard", True, WHITE)
    rect = text_surface.get_rect(center=(160, 45))
    screen.blit(text_surface, rect)
    with open("leaderboard.csv", mode='r', newline='') as file:
        reader = csv.DictReader(file)
        entries = [row for row in reader]

    start = 75
    text_surface = font_small.render("RANK", True, WHITE)
    rect = text_surface.get_rect(center=(35, start))
    screen.blit(text_surface, rect)

    text_surface = font_small.render("NAME", True, WHITE)
    rect = text_surface.get_rect(center=(105, start))
    screen.blit(text_surface, rect)

    text_surface = font_small.render("SCORE", True, WHITE)
    rect = text_surface.get_rect(center=(170, start))
    screen.blit(text_surface, rect)

    text_surface = font_small.render("DATE", True, WHITE)
    rect = text_surface.get_rect(center=(265, start))
    screen.blit(text_surface, rect)
    
    start = 105
    number = 1
    entries.reverse()

    for entry in entries:
        name = entry["name"]
        score = entry["score"]
        date = entry["date"]

        text_surface = font_small.render(str(number), True, WHITE)
        rect = text_surface.get_rect(center=(35, start))
        screen.blit(text_surface, rect)

        text_surface = font_small.render(str(name), True, WHITE)
        rect = text_surface.get_rect(center=(105, start))
        screen.blit(text_surface, rect)

        text_surface = font_small.render(str(score), True, WHITE)
        rect = text_surface.get_rect(center=(170, start))
        screen.blit(text_surface, rect)

        text_surface = font_small.render(str(date), True, WHITE)
        rect = text_surface.get_rect(center=(265, start))
        screen.blit(text_surface, rect)

        start += 30
        number += 1

    draw_buttons(leaderboard_buttons)
    pygame.display.update()

def draw_update_screen(name):
    global cursor
    screen.fill(BLACK)
    text_surface = font_medium.render("You Got A High Score!", True, WHITE)
    rect = text_surface.get_rect(center=(160, 35))
    screen.blit(text_surface, rect)

    text_surface = font_medium.render("Enter Your Initials:", True, WHITE)
    rect = text_surface.get_rect(center=(160, 75))
    screen.blit(text_surface, rect)

    text_surface = font_extra_large.render(name, True, WHITE)
    rect = text_surface.get_rect(center=(120, 140))
    screen.blit(text_surface, rect)

    if cursor == 0:
        # left, top, width, height
        underline_0 = pygame.Rect(70, 160, 32, 5)
        pygame.draw.rect(screen, GREEN, underline_0)
    elif cursor == 1:
        underline_1 = pygame.Rect(105, 160, 32, 5)
        pygame.draw.rect(screen, GREEN, underline_1)
    elif cursor == 2:
        underline_2 = pygame.Rect(140, 160, 32, 5)
        pygame.draw.rect(screen, GREEN, underline_2)

    draw_buttons(update_buttons)
    pygame.display.update()

def draw_quitting_screen():
    screen.fill(BLACK)
    text_surface = font_extra_large.render("QUITTING", True, WHITE)
    rect = text_surface.get_rect(center=(160, 100))
    screen.blit(text_surface, rect)
    text_surface = font_medium.render("Thank you for playing!", True, WHITE)
    rect = text_surface.get_rect(center=(160, 150))
    screen.blit(text_surface, rect)
    pygame.display.update()

### SERVICE TOUCH EVENT FUNCTIONS ###

def main_menu_service_touch(x, y):
    global code_run
    next_state = States.MAIN_MENU
    # print("here")
    if y > 200:
        if x < 80:  # Rules button pressed
            print("Rules button pressed!")
            next_state = States.RULES
        elif x < 220: # Leaderboard button pressed
            print("Leaderboard button pressed!")
            next_state = States.LEADERBOARD 
        elif x > 220:  # Quit button pressed
            print ("Quit button pressed!")
            draw_quitting_screen()
            code_run = False

    elif y > 120 and y < 180 and x > 140 and x < 180:
        print("Start button pressed!")
        next_state = States.USER_POINTER
    return next_state

def game_over_service_touch(x, y):
    if high_score:
        next_state = States.UPDATE
    else:
        next_state = States.LEADERBOARD
    if y > 200:
        if x > 220:  # Next button pressed
            print("Next button pressed!")
    return next_state

def rules_service_touch(x, y):
    next_state = States.RULES
    if y < 80:
        if x > 240:  # Return to main menu button pressed
            print("Return to main menu button pressed! ")
            next_state = States.MAIN_MENU
    return next_state

def leaderboard_service_touch(x, y):
    next_state = States.LEADERBOARD
    global code_run
    if y < 80:
        if x > 215:  # Main menu button pressed
            print("Main menu button pressed!")
            next_state = States.MAIN_MENU
        elif x < 90:
            print("Quit button pressed!")
            draw_quitting_screen()
            code_run = False
    return next_state

def update_service_touch(x, y):
    global cursor
    global char_0
    global char_1
    global char_2
    global score
    global name
    next_state = States.UPDATE
    if x > 200:
        if y > 100 and y < 125: # Increment letter
            if cursor == 0:
                char_0 += 1
                if char_0 == 27:
                    char_0 = 1
            if cursor == 1:
                char_1 += 1
                if char_1 == 27:
                    char_1 = 1
            if cursor == 2:
                char_2 += 1
                if char_2 == 27:
                    char_2 = 1
        elif y > 150 and y < 175: # Decrement letter
            if cursor == 0:
                char_0 = char_0 - 1
                if char_0 == 0:
                    char_0 = 26
            if cursor == 1:
                char_1 = char_1 - 1
                if char_1 == 0:
                    char_1 = 26
            if cursor == 2:
                char_2 = char_2 - 1
                if char_2 == 0:
                    char_2 = 26
        elif y > 200: # Move cursor
            cursor +=1
            if cursor == 3:
                cursor = 0
    elif y > 200:
        if x < 75:  # Clear button pressed
            print("Clear button pressed!")
            char_0, char_1, char_2 = 1, 1, 1
            cursor = 0
        elif x < 130: # Next button pressed
            print("Next button pressed!")
            update_best_scores("leaderboard.csv", new_name = name, new_score = score, new_date = str(datetime.now().date()))
            next_state = States.LEADERBOARD 
    return next_state

### MAIN CODE LOOP ###

pitft.update()
# total_runtime = 320
init_time = time()
code_run = True
print("Welcome to Look That Way!")

try:
    while code_run:
        # Runtime auto timeout logic
        # if (time() - init_time) >= total_runtime:
        #     code_run = False

        pitft.update()
        cpu_look_center()
        cpu_point_center()
        user_choice = ""
        cpu_choice = ""
        
        if state == States.MAIN_MENU:
            # start_background_music()
            draw_main_menu_screen()
            score_multiplier = 1
            level = 1
            score = 0
            points_per_score = 1
            high_score = False
            next_state = States.MAIN_MENU
            for event in pygame.event.get():
                if event.type is MOUSEBUTTONUP:
                    x, y = pygame.mouse.get_pos()
                    # print(f"x: {x}, y: {y}")                    
                    next_state = main_menu_service_touch(x, y)

        elif state == States.RULES:  
            draw_rules_screen()
            for event in pygame.event.get():
                if event.type is MOUSEBUTTONUP:
                    x, y = pygame.mouse.get_pos()
                    # print(f"x: {x}, y: {y}")                    
                    next_state = rules_service_touch(x, y)

        elif state == States.LEADERBOARD:  
            draw_leaderboard_screen()
            for event in pygame.event.get():
                if event.type is MOUSEBUTTONUP:
                    x, y = pygame.mouse.get_pos()
                    # print(f"x: {x}, y: {y}")                    
                    next_state = leaderboard_service_touch(x, y)

        elif state == States.USER_POINTER:
            # print(f"Level: {level}")
            # print(f"Score: {score}")
            msg1 = "Your turn to point!"
            msg2 = "Guess which way the CPU will look."
            draw_gameplay_screen(level, score, msg1 , msg2, "", "", "")
            print("Your turn to point! Guess which way the CPU will look.")

            # Countdown timer (speed up as rounds progress)
            if not countdown_timer(level):
                next_state = States.GAME_OVER  # If time runs out, set next state to GAME_OVER
                # game_over_sound.play()
                state = next_state            # Transition to GAME_OVER immediately
                continue

            # Allow a window for user input
            start_time = time()
            user_acted = False

            while time() - start_time < input_window:
                if user_choice != "":
                    user_acted = True
                    break

            if not user_acted:  # User failed to act in time
                print("You ran out of time!")
                msg1 = "Too slow!"
                msg2 = "You lose."
                # timing_buzzer.play()
                # sleep(timing_buzzer.get_length())
                next_state = States.GAME_OVER  # Transition to GAME_OVER state
                # game_over_sound.play()
                state = next_state            # Update state to GAME_OVER immediately
                user_choice = ""
                draw_gameplay_screen(level, score, msg1, msg2, "", cpu_choice, user_choice)
                sleep(4)
                continue

            # CPU action and result evaluation
            # sleep(1)
            cpu_choice = Directions.select_random_direction()
            actuate_CPU_look(cpu_choice)
            print(f"CPU looked {cpu_choice}.")
            

            if user_choice == cpu_choice:
                # score_sound.play()
                gained_points = score_multiplier * points_per_score
                score += gained_points
                msg1 = "Got 'em!"
                msg2 = f"You gained {gained_points} points!"
                print(f"Great job, you pointed correctly! You gained {gained_points} points!") 
                print("Try to catch the CPU again!")
                score_multiplier += 1
                next_state = States.USER_POINTER
            else:
                if user_choice != "":
                    print("Nice try, but you pointed incorrectly.")
                    print("Time to switch roles!")
                    msg1 = "Nice try. You missed!"
                    msg2 = f"Time to switch roles!"
                    next_state = States.USER_LOOKER
                else:
                    pass # User failed to point in time
            
            draw_gameplay_screen(level, score, msg1, msg2, "", cpu_choice, user_choice)
            sleep(4)

        elif state == States.USER_LOOKER:
            msg1 = "Your turn to look!"
            msg2 = "Try to evade the CPU's point."
            # print(f"Level: {level}")
            # print(f"Score: {score}")
            draw_gameplay_screen(level, score, "Your turn to look!", "Try to evade the CPU's point.", "", "", "")
            print("Your turn to look! Try to evade the CPU's point.")

            # Countdown timer (speed up as rounds progress)
            if not countdown_timer(level):
                next_state = States.GAME_OVER  # If time runs out, set next state to GAME_OVER
                # game_over_sound.play()
                state = next_state            # Transition to GAME_OVER immediately
                continue

            # # CPU action and result evaluation
            # # sleep(1)
            # cpu_choice = Directions.select_random_direction()
            # actuate_CPU_point(cpu_choice)
            # print(f"CPU pointed {cpu_choice}.")

            # Allow a window for user input
            start_time = time()
            user_acted = False
            user_choice = get_head_camera(input_window)
            # user_choice = "UP"
            # sleep(input_window)
            print(f"User looked {user_choice}.")

            if user_choice == cpu_choice:
                print("Oh no, the CPU pointed correctly!")
                print("Sorry, you lose!")
                msg1 = "The CPU got you!"
                msg2 = "Sorry, you lose!"
                next_state = States.GAME_OVER  # Transition to GAME_OVER state
                # game_over_sound.play()
                state = next_state            # Update state to GAME_OVER immediately
            else:
                level += 1
                print("Nice job, you evaded the CPU!")
                # success_sound.play()
                # sleep(success_sound.get_length())
                print("Level up!")
                msg1 = "Evaded 'em!"
                msg2 = "Level up!"
                # next_level_sound.play()
                next_state = States.USER_POINTER
            draw_gameplay_screen(level, score, msg1, msg2, "", cpu_choice, user_choice)
            sleep(4)

        elif state == States.GAME_OVER:
            # print(f"Level: {level}, Score: {score}")
            draw_game_over_screen(level, score)
            high_score_check("/home/pi/look_that_way_game/leaderboard.csv", score)
            for event in pygame.event.get():
                if event.type is MOUSEBUTTONUP:
                    x, y = pygame.mouse.get_pos()
                    # print(f"x: {x}, y: {y}")                    
                    next_state = game_over_service_touch(x, y)
        
            # stop_background_music()
            # print("\nGAME OVER!")
            # game_over_speech.play()
            # print(f"Final Score: {score}")
            # print(f"Level Reached: {level}")

            # print(f"Press restart button ({RESTART_PIN}) to restart or quit button ({QUIT_PIN}) to exit.")

            # # Wait for the button press to handle the restart or quit
            # restart_flag = False
            # quit_flag = False
            # while not restart_flag and not quit_flag and code_run:
            #     sleep(0.1)  # Allow the callbacks to be processed

            # if quit_flag:
            #     print("Exiting game!")
            #     exit()  # Quit the game

            # if restart_flag:
            #     # Reset game state
            #     next_state = States.MAIN_MENU
            #     level = 1
            #     score = 0
            #     print("Game restarted!")

        elif state == States.UPDATE:
            alphabet = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 
                        8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L', 13: 'M', 14: 'N', 
                        15: 'O', 16: 'P', 17: 'Q', 18: 'R', 19: 'S', 20: 'T', 
                        21: 'U', 22: 'V', 23: 'W', 24: 'X', 25: 'Y', 26: 'Z'}
            name = alphabet[char_0] + alphabet[char_1] + alphabet[char_2]
            draw_update_screen(name)
            for event in pygame.event.get():
                if event.type is MOUSEBUTTONUP:
                    x, y = pygame.mouse.get_pos()
                    # print(f"x: {x}, y: {y}")                    
                    next_state = update_service_touch(x, y)

        # print("\n")
        if state != States.UPDATE:
            sleep(1)  # Buffer before the next round
        # print(f"Next state is {next_state}!")
        score_multiplier += 1
        state = next_state  # Make sure to update the state here before the next iteration

except KeyboardInterrupt:
    pass

finally:
    # pygame.mixer.music.stop()
    # pygame.mixer.quit()
    del pitft
    pygame.quit()
    cpu_look_center()
    cpu_point_center()
    sleep(1)
    stop_PWM()
    GPIO.cleanup()