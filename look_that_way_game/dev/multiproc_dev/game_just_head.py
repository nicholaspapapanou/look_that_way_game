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
# 0c45:6367
cap = cv2.VideoCapture(0)

def head_computer_vision(shared_dict, code_run, lock, cap):
    # access webcam
    cap = cv2.VideoCapture(0)

    # vars for face mesh
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        min_detection_confidence=0.5, min_tracking_confidence=0.5
    )
    mp_drawing = mp.solutions.drawing_utils

    sleep(3)
    #Tips for performance: which function takes most time. Is it face_mesh.process?
    while code_run:

        # print("READING RARARARA")
        # print(type(cap))
        # print(type(face_mesh))
        ret, frame = cap.read()
        # cv2.imshow('frame',frame)
        # facemesh
        results = face_mesh.process(frame)
        frame.flags.writeable = True

        # frame = cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)

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
        # print(shared_dict)


# access webcam
cap = cv2.VideoCapture(0)


def get_head_camera(time_length):
    init_time = time()
    max_dir, max_count = "down", 0
    dir_dict = {
        "oop": 0,
        "down": 0,
        "up": 0,
        "right": 0,
        "left": 0,
    }

    print("Reading your movements now")
    #Tips for performance: which function takes most time. Is it face_mesh.process?
    while time_length > time() - init_time and code_run:
        # print("READING RARARARA")
        ret, frame = cap.read()
        # cv2.imshow('frame',frame)
        # facemesh
        results = face_mesh.process(frame)
        frame.flags.writeable = True

        # frame = cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)

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
                dir_dict[text] += 1

    # cap.release()
    # cv2.destroyAllWindows()

    print(f"\n\nDIR\n{dir_dict}")
    for key, value in dir_dict.items():
        if value > max_count:
            print(f"Changed from {max_dir}, {max_count} to {key}, {value}")
            max_dir, max_count = key, value

    return max_dir



### GAME LOGIC ###



dir_dict = {
        "oop": 0,
        "down": 0,
        "up": 0,
        "right": 0,
        "left": 0,
    }



# GPIO pins
BAILOUT_PIN = 27
UP_PIN = 26
RIGHT_PIN = 13
DOWN_PIN = 16
LEFT_PIN = 6
BASE_GIMBAL_PIN = 12
HEAD_GIMBAL_PIN = 19

# Need to run "sudo pigpiod" to start daemon before running
# Need to run "sudo killall pigpiod" to stop daemon when done

# Set up hardware PWM values - duty cycle values multiplied by 10,000 because of 0-1M scale
FREQ = 50  # 50 Hz = 20 ms period
LEFT_DC = 60000  # 50 Hz @ 6% duty cycle = 1.2 ms pulse width
CENTER_BASE_DC = 90000  # 50 Hz @ 9% duty cycle = 1.8 ms pulse width
RIGHT_DC = 120000  # 50 Hz @ 12% duty cycle = 2.4 ms pulse width
UP_DC = 40000  # 50 Hz @ 4% duty cycle = 0.8 ms pulse width
CENTER_HEAD_DC = 65000  # 50 Hz @ 6.5% duty cycle = 1.3 ms pulse width
DOWN_DC = 90000  # 50 Hz @ 9% duty cycle = 1.8 ms pulse width

# Set up GPIOs
GPIO.setmode(GPIO.BCM)
GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BAILOUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

### PWM FUNCTIONS ###

pi = pigpio.pi()


def cpu_left():
    pi.hardware_PWM(BASE_GIMBAL_PIN, FREQ, LEFT_DC)


def cpu_right():
    pi.hardware_PWM(BASE_GIMBAL_PIN, FREQ, RIGHT_DC)


def cpu_up():
    pi.hardware_PWM(HEAD_GIMBAL_PIN, FREQ, UP_DC)


def cpu_down():
    pi.hardware_PWM(HEAD_GIMBAL_PIN, FREQ, DOWN_DC)


def cpu_center():
    pi.hardware_PWM(BASE_GIMBAL_PIN, FREQ, CENTER_BASE_DC)
    pi.hardware_PWM(HEAD_GIMBAL_PIN, FREQ, CENTER_HEAD_DC)


def stop_PWM():
    pi.hardware_PWM(BASE_GIMBAL_PIN, FREQ, 0)
    pi.hardware_PWM(HEAD_GIMBAL_PIN, FREQ, 0)


### DPAD CALLBACKS ###


def dpad_up_callback(channel):
    global user_choice
    user_choice = "up"
    print(f"User chose {user_choice}.")


GPIO.add_event_detect(UP_PIN, GPIO.FALLING, callback=dpad_up_callback, bouncetime=300)


def dpad_right_callback(channel):
    global user_choice
    user_choice = "right"
    print(f"User chose {user_choice}.")


GPIO.add_event_detect(13, GPIO.FALLING, callback=dpad_right_callback, bouncetime=300)


def dpad_down_callback(channel):
    global user_choice
    user_choice = "down"
    print(f"User chose {user_choice}.")


GPIO.add_event_detect(16, GPIO.FALLING, callback=dpad_down_callback, bouncetime=300)


def dpad_left_callback(channel):
    global user_choice
    user_choice = "left"
    print(f"User chose {user_choice}.")


GPIO.add_event_detect(6, GPIO.FALLING, callback=dpad_left_callback, bouncetime=300)


# Setup bailout button functionality with threaded callback
def GPIO27_callback(channel):
    global code_run
    print("Bailout button pressed!")
    code_run = False


GPIO.add_event_detect(27, GPIO.FALLING, callback=GPIO27_callback, bouncetime=300)
#def head_computer_vision(shared_dict, code_run, lock):
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
        return "up"  # Uncomment to cheat (CPU always picks up)
        # return Directions.dirs[rand_dir]


def actuate_CPU_motion(dir):
    print("should be toggling")
    if dir == "up":
        cpu_up()
    elif dir == "down":
        cpu_down()
    elif dir == "left":
        cpu_left()
    else:
        cpu_right()

def game_logic(shared_dict, code_run, lock):
    ### CONSTANTS ###

    look = ""
    point = ""

    state = States.INIT
    next_state = None

    countdown = 3
    score_multiplier = 1
    level = 1
    score = 0
    points_per_score = 1

    ready = False
    ### MAIN CODE LOOP ###
    code_run = True
    try:
        while code_run:
            if state != States.GAMEOVER:
                print(f"Level: {level}")
                print(f"Score: {score}")
            user_choice = ""
            cpu_choice = ""
            cpu_center()

            if state == States.INIT:
                print("Welcome to Look That Way!")
                pass

            elif state == States.USER_POINTER:
                print("Your turn to point!")
                ready = True
                while user_choice == "" and code_run:
                    print(f"Spinning: {user_choice}__")
                    sleep(1.5)
                    pass
                    user_choice = 'left'
                print("exiting")
                # user_choice = get_pointer_camera(5)
                sleep(1)
                cpu_choice = Directions.select_random_direction()
                actuate_CPU_motion(cpu_choice)
                print(f"CPU looked {cpu_choice}.")

            elif state == States.USER_LOOKER:
                print("Your turn to look!")
                # while user_choice == "":
                #     pass

                with lock:
                    for key in shared_dict.keys():
                        shared_dict[key] = 0
                # user_choice = get_head_camera(5)
                sleep(5)#amount of time head movements are registered
                with lock:
                    max_count = -1
                    for key, value in shared_dict.items():
                        if value > max_count:
                            print(f"Changed from {user_choice}, {max_count} to {key}, {value}")
                            user_choice, max_count = key, value

                print(f"You looked here: {user_choice}")
                sleep(1)
                cpu_choice = Directions.select_random_direction()
                actuate_CPU_motion(cpu_choice)
                print(f"CPU pointed {cpu_choice}.")

            elif state == States.GAMEOVER:
                print("GAME OVER!")
                print(f"Final Score: {score}")
                print(f"Level Reached: {level}")
                break

            sleep(1)

            if state == States.INIT:
                next_state = States.USER_POINTER

            if state == States.USER_POINTER:
                gained_points = score_multiplier * points_per_score
                if user_choice == cpu_choice:
                    score += gained_points
                    next_state = state
                    print(
                        f"Great job, you pointed correctly! You gained {gained_points} points!"
                    )
                    print("Try to catch the CPU again!")
                    score_multiplier = score_multiplier * 2
                else:
                    next_state = States.USER_LOOKER
                    print("Nice try, but you pointed incorrectly.")
                    print("Time to switch roles!")

            if state == States.USER_LOOKER:
                if user_choice == cpu_choice:
                    next_state = States.GAMEOVER
                    print("Oh no, the CPU pointed correctly!")
                    print("Sorry, you lose!")
                else:
                    countdown = countdown - countdown * 0.2
                    score_multiplier = score_multiplier * 2
                    level += 1
                    next_state = States.USER_POINTER
                    print("Nice job, you evaded the CPU!")
                    print("Level up!")

            sleep(1)
            print("\n")

            state = next_state

    except KeyboardInterrupt:
        cap.release()
        cv2.destroyAllWindows()

    finally:
        cpu_center()
        stop_PWM()
        GPIO.cleanup



lock = Lock()

code_run = Value('b', True) #Value only used for basic primitives
with Manager() as manager:
    # Use Manager for shared dictionary
    shared_dict = manager.dict({
        "oop": 0,
        "down": 0,
        "up": 0,
        "right": 0,
        "left": 0,
    })
    # print("hey there//////////`//////////////////////////////")
    # # cap = cv2.VideoCapture(0)
    # print("hey there///////////////`/////////////////////////")
    game_logic_proc = Process(target = game_logic, args=(shared_dict, code_run, lock))
    head_cv_proc = Process(target = head_computer_vision, args=(shared_dict, code_run, lock, cap))

    # Start processes
    game_logic_proc.start()
    head_cv_proc.start()

    # Wait for processes to complete
    game_logic_proc.join()
    head_cv_proc.join()
