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

from multiprocessing import Process, Manager, Lock, Value
from ctypes import c_char_p as s

### CONSTANTS ###

# GPIO pins
UP_PIN = 26
RIGHT_PIN = 13
DOWN_PIN = 16
LEFT_PIN = 6
LOOK_BASE_GIMBAL_PIN = 12
LOOK_HEAD_GIMBAL_PIN = 19
POINT_BASE_GIMBAL_PIN = 4
POINT_HEAD_GIMBAL_PIN = 5
RESTART_PIN = 22  # Restart button (active low)
QUIT_PIN = 17     # Quit button (active low)

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
GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RESTART_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(QUIT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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

GPIO.add_event_detect(UP_PIN, GPIO.FALLING, callback=lambda channel: dpad_callback("up"), bouncetime=300)
GPIO.add_event_detect(RIGHT_PIN, GPIO.FALLING, callback=lambda channel: dpad_callback("right"), bouncetime=300)
GPIO.add_event_detect(DOWN_PIN, GPIO.FALLING, callback=lambda channel: dpad_callback("down"), bouncetime=300)
GPIO.add_event_detect(LEFT_PIN, GPIO.FALLING, callback=lambda channel: dpad_callback("left"), bouncetime=300)

def restart_game_callback(channel):
    global restart_flag
    print("Restart button pressed!")
    restart_flag = True
GPIO.add_event_detect(RESTART_PIN, GPIO.FALLING, callback=restart_game_callback, bouncetime=300)

def quit_game_callback(channel):
    global quit_flag
    print("Quit button pressed!")
    quit_flag = True
GPIO.add_event_detect(QUIT_PIN, GPIO.FALLING, callback=quit_game_callback, bouncetime=300)

### GAME SOUNDS ###

# pygame.init()
# pygame.mixer.init()
path = "/home/pi/look_that_way_game/sounds/"

# # Load and play background music in the INIT stage
# def start_background_music():
#     pygame.mixer.music.load(f"{path}game_music.mp3")
#     pygame.mixer.music.play(loops=-1, start=0.0)  # loops=-1 for infinite loop
#     pygame.mixer.music.set_volume(0.5)

# # Stop background music in the GAMEOVER stage
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

# cap = cv2.VideoCapture(-1)
def head_computer_vision(shared_dict, get_cv, lock):
    print(get_cv.value)
    sleep(5)
    cap = cv2.VideoCapture(-1)
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        min_detection_confidence=0.5, min_tracking_confidence=0.5
    )
    # mp_drawing = mp.solutions.drawing_utils
    # drawing_spec = mp_drawing.DrawingSpec(color=(128, 0, 128), thickness=2, circle_radius=1)

    # init_time = time()
    # max_dir, max_count = "down", 0
    # dir_dict = {
    #     "oop": 0,
    #     "down": 0,
    #     "up": 0,
    #     "right": 0,
    #     "left": 0,
    # }

    # sleep(3)
    #Tips for performance: which function takes most time. Is it face_mesh.process?
    while True:
        while get_cv:
            # print("CV IS RUNNING")
            ret, frame = cap.read()
            # facemesh
            results = face_mesh.process(frame)
            frame.flags.writeable = True

            img_h, img_w, img_c = frame.shape
            face_2d = []
            face_3d = []
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    for idx, lm in enumerate(face_landmarks.landmark):
                        if (
                            idx == 33
                            or idx == 263
                            or idx == 1
                            or idx == 61
                            or idx == 291
                            or idx == 199
                        ):
                            if idx == 1:
                                nose_2d = (lm.x * img_w, lm.y * img_h)
                                nose_3d = (lm.x * img_w, lm.y * img_h, lm.z * 3000)
                            x, y = int(lm.x * img_w), int(lm.y * img_h)

                            face_2d.append([x, y])
                            face_3d.append(([x, y, lm.z]))

                    # Get 2d Coord
                    face_2d = np.array(face_2d, dtype=np.float64)

                    face_3d = np.array(face_3d, dtype=np.float64)

                    focal_length = 1 * img_w

                    cam_matrix = np.array(
                        [
                            [focal_length, 0, img_h / 2],
                            [0, focal_length, img_w / 2],
                            [0, 0, 1],
                        ]
                    )
                    distortion_matrix = np.zeros((4, 1), dtype=np.float64)

                    success, rotation_vec, translation_vec = cv2.solvePnP(
                        face_3d, face_2d, cam_matrix, distortion_matrix
                    )

                    # getting rotational of face
                    rmat, jac = cv2.Rodrigues(rotation_vec)

                    angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

                    x = angles[0] * 360
                    y = angles[1] * 360
                    z = angles[2] * 360

                    # here based on axis rot angle is calculated
                    with lock:
                        if y < -5:
                            text = "right"
                        elif y > 5:
                            text = "left"
                        elif x < -2.5:
                            text = "down"
                        elif x > 5:
                            text = "up"
                        else:
                            text = "Forward"
                        if text != "Forward":
                            shared_dict[text] += 1
# cap = cv2.VideoCapture(0)

### GAME LOGIC ###

class States(Enum):
    INIT = 1
    USER_POINTER = 2
    USER_LOOKER = 3
    GAMEOVER = 4
    LEADERBOARD = 5
    SETTINGS = 6

class Directions:
    left = "left"
    right = "right"
    up = "up"
    down = "down"
    dirs = [left, right, up, down]
    def select_random_direction():
        rand_dir = random.randint(0, 3)
        # return "up" # Uncomment to debug (CPU always picks up)
        return Directions.dirs[rand_dir]

# Countdown printing function
def countdown_timer(round_number):
    global user_choice
    # Calculate sleep time based on the round number (faster countdown as the rounds progress)
    sleep_time = max(1 - (round_number - 1) * 0.1, 0.1)  # Minimum sleep time of 0.1 seconds
    
    # Print countdown
    for i in range(3, 0, -1):
        print(i)
        # short_beep.play()
        sleep(sleep_time)
        if user_choice != "":  # User acted too early
            print("You acted too early!")
            # timing_buzzer.play()
            return False
    print("GO!")
    # long_beep.play()
    return True

def actuate_CPU_look(dir):
    if dir == "up":
        cpu_look_up()
    elif dir == "down":
        cpu_look_down()
    elif dir == "left":
        cpu_look_left()
    elif dir == "right":
        cpu_look_right()

def actuate_CPU_point(dir):
    if dir == "up":
        cpu_point_up()
    elif dir == "down":
        cpu_point_down()
    elif dir == "left":
        cpu_point_left()
    elif dir == "right":
        cpu_point_right()

def game_logic(shared_dict, get_cv, lock, user_choice):
    # global user_choice
    state = States.INIT
    next_state = None
    input_window = 2  # Allowable time after countdown for user input
    score_multiplier = 1
    level = 1
    score = 0
    points_per_score = 1

    ### MAIN CODE LOOP ###

    try:
        while True:
            cpu_look_center()
            cpu_point_center()
            user_choice = ""
            cpu_choice = ""

            if state != States.GAMEOVER:
                print(f"Level: {level}")
                print(f"Score: {score}")

            if state == States.INIT:
                # start_background_music()
                score_multiplier = 1
                level = 1
                score = 0
                points_per_score = 1
                print("Welcome to Look That Way!")
                sleep(2)
                next_state = States.USER_POINTER

            elif state == States.USER_POINTER:
                print("Your turn to point! Try to guess which way the CPU will look.")

                # Countdown timer (speed up as rounds progress)
                if not countdown_timer(level):
                    next_state = States.GAMEOVER  # If time runs out, set next state to GAMEOVER
                    # game_over_sound.play()
                    state = next_state            # Transition to GAMEOVER immediately
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
                    # timing_buzzer.play()
                    # sleep(timing_buzzer.get_length())
                    next_state = States.GAMEOVER  # Transition to GAMEOVER state
                    # game_over_sound.play()
                    state = next_state            # Update state to GAMEOVER immediately
                    continue

                # CPU action and result evaluation
                sleep(1)
                cpu_choice = Directions.select_random_direction()
                actuate_CPU_look(cpu_choice)
                print(f"CPU looked {cpu_choice}.")

                if user_choice == cpu_choice:
                    # score_sound.play()
                    gained_points = score_multiplier * points_per_score
                    score += gained_points
                    print(f"Great job, you pointed correctly! You gained {gained_points} points!") 
                    print("Try to catch the CPU again!")
                    score_multiplier += 1
                    next_state = States.USER_POINTER
                else:
                    print("Nice try, but you pointed incorrectly.")
                    print("Time to switch roles!")
                    next_state = States.USER_LOOKER

            elif state == States.USER_LOOKER:
                # get_cv = True
                print("Your turn to look! Try to evade the CPU's point.")

                # Countdown timer (speed up as rounds progress)
                if not countdown_timer(level):
                    next_state = States.GAMEOVER  # If time runs out, set next state to GAMEOVER
                    # game_over_sound.play()
                    state = next_state            # Transition to GAMEOVER immediately
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
                    # timing_buzzer.play()
                    # sleep(timing_buzzer.get_length())
                    next_state = States.GAMEOVER  # Transition to GAMEOVER state
                    # game_over_sound.play()
                    state = next_state            # Update state to GAMEOVER immediately
                    continue

                # CPU action and result evaluation
                sleep(1)
                cpu_choice = Directions.select_random_direction()
                actuate_CPU_point(cpu_choice)
                print(f"CPU pointed {cpu_choice}.")

                if user_choice == cpu_choice:
                    print("Oh no, the CPU pointed correctly!")
                    print("Sorry, you lose!")
                    next_state = States.GAMEOVER  # Transition to GAMEOVER state
                    # game_over_sound.play()
                    state = next_state            # Update state to GAMEOVER immediately
                else:
                    level += 1
                    print("Nice job, you evaded the CPU!")
                    # success_sound.play()
                    # sleep(success_sound.get_length())
                    print("Level up!")
                    # next_level_sound.play()
                    next_state = States.USER_POINTER

            elif state == States.GAMEOVER:
                # stop_background_music()
                print("\nGAME OVER!")
                # game_over_speech.play()
                print(f"Final Score: {score}")
                print(f"Level Reached: {level}")
                print(f"Press restart button ({RESTART_PIN}) to restart or quit button ({QUIT_PIN}) to exit.")

                # Wait for the button press to handle the restart or quit
                restart_flag = False
                quit_flag = False
                while not restart_flag and not quit_flag:
                    sleep(0.1)  # Allow the callbacks to be processed

                if quit_flag:
                    print("Exiting game!")
                    exit()  # Quit the game

                if restart_flag:
                    # Reset game state
                    next_state = States.INIT
                    level = 1
                    score = 0
                    print("Game restarted!")

            print("\n")
            sleep(3)  # Buffer before the next round
            state = next_state  # Make sure to update the state here before the next iteration

    except KeyboardInterrupt:
        pass

    finally:
        # pygame.mixer.music.stop()
        # pygame.mixer.quit()
        # pygame.quit()
        cpu_look_center()
        cpu_point_center()
        sleep(1)
        stop_PWM()
        GPIO.cleanup()

### MULTIPROCESSING ###

lock = Lock()

get_cv = Value('b', False) #Value only used for basic primitives
# user_choice = Value('s', "")
with Manager() as manager:
    # Use Manager for shared dictionary
    user_choice = manager.Value(s, '')
    shared_dict = manager.dict({
        "oop": 0,
        "down": 0,
        "up": 0,
        "right": 0,
        "left": 0,
    })
    game_logic_proc = Process(target = game_logic, args=(shared_dict, get_cv, lock, user_choice))
    head_cv_proc = Process(target = head_computer_vision, args=(shared_dict, get_cv, lock))

    # Start processes
    game_logic_proc.start()
    head_cv_proc.start()

    # Wait for processes to complete
    game_logic_proc.join()
    head_cv_proc.join()
