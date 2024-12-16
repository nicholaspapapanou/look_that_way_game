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
LOOK_BASE_GIMBAL_PIN = 12
LOOK_HEAD_GIMBAL_PIN = 19
POINT_BASE_GIMBAL_PIN = 4
POINT_HEAD_GIMBAL_PIN = 5

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
GPIO.add_event_detect(RIGHT_PIN, GPIO.FALLING, callback=dpad_right_callback, bouncetime=300)

def dpad_down_callback(channel):
    global user_choice
    user_choice = "down"
    print(f"User chose {user_choice}.")
GPIO.add_event_detect(DOWN_PIN, GPIO.FALLING, callback=dpad_down_callback, bouncetime=300)

def dpad_left_callback(channel):
    global user_choice
    user_choice = "left"
    print(f"User chose {user_choice}.")
GPIO.add_event_detect(LEFT_PIN, GPIO.FALLING, callback=dpad_left_callback, bouncetime=300)

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
    
state = States.INIT
next_state = None

countdown = 3
score_multiplier = 1
level = 1
score = 0
points_per_score = 1

### MAIN CODE LOOP ###

try:
    while True:

        cpu_look_center()
        cpu_point_center()
        if state != States.GAMEOVER:
            print(f"Level: {level}")
            print(f"Score: {score}")
        user_choice = ""
        cpu_choice = ""

        if state == States.INIT:
            print("Welcome to Look That Way!")
            pass

        elif state == States.USER_POINTER:
            print("Your turn to point! Try to guess which way the CPU will look.")
            while user_choice == "":
                pass
            sleep(1)
            cpu_choice = Directions.select_random_direction()
            actuate_CPU_look(cpu_choice)
            print(f"CPU looked {cpu_choice}.")

        elif state == States.USER_LOOKER:
            print("Your turn to look! Try to evade the CPU's point.")
            while user_choice == "":
                pass
            sleep(1)
            cpu_choice = Directions.select_random_direction()
            actuate_CPU_point(cpu_choice)
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
                score_multiplier = score_multiplier + 1
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
                score_multiplier = score_multiplier + 1
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
    cpu_look_center()
    cpu_point_center()
    sleep(1)
    stop_PWM()
    GPIO.cleanup
