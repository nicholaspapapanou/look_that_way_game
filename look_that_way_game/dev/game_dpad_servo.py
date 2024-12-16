from enum import Enum
import random
import RPi.GPIO as GPIO
import pigpio
from time import sleep

### CONSTANTS ###

# GPIO pins
UP_PIN = 26
RIGHT_PIN = 13
DOWN_PIN = 16
LEFT_PIN = 6
BASE_GIMBAL_PIN = 12
HEAD_GIMBAL_PIN = 19

# Need to run "sudo pigpiod" to start daemon before running
# Need to run "sudo killall pigpiod" to stop daemon when done

# Set up hardware PWM values - duty cycle values multiplied by 10,000 because of 0-1M scale
FREQ = 50               # 50 Hz = 20 ms period
LEFT_DC = 60000         # 50 Hz @ 6% duty cycle = 1.2 ms pulse width
CENTER_BASE_DC = 90000  # 50 Hz @ 9% duty cycle = 1.8 ms pulse width
RIGHT_DC = 120000       # 50 Hz @ 12% duty cycle = 2.4 ms pulse width
UP_DC = 40000           # 50 Hz @ 4% duty cycle = 0.8 ms pulse width
CENTER_HEAD_DC = 65000  # 50 Hz @ 6.5% duty cycle = 1.3 ms pulse width
DOWN_DC = 90000         # 50 Hz @ 9% duty cycle = 1.8 ms pulse width

# Set up GPIOs
GPIO.setmode(GPIO.BCM)
GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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
        # return "up" # Uncomment to cheat (CPU always picks up)
        return Directions.dirs[rand_dir]

def actuate_CPU_motion(dir):
    if dir == "up":
        cpu_up()
    elif dir == "down":
        cpu_down()
    elif dir == "left":
        cpu_left()
    else:
        cpu_right()
        
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

try:
    while True:

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
            while user_choice == "":
                pass
            sleep(1)
            cpu_choice = Directions.select_random_direction()
            actuate_CPU_motion(cpu_choice)
            print(f"CPU looked {cpu_choice}.")

        elif state == States.USER_LOOKER:
            print("Your turn to look!")
            while user_choice == "":
                pass
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
                print(f"Great job, you pointed correctly! You gained {gained_points} points!") 
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
    pass
finally:
    cpu_center()
    stop_PWM()
    GPIO.cleanup
