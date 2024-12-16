import pigpio
from time import sleep

# Need to run "sudo pigpiod" to start daemon before running
# Need to run "sudo killall pigpiod" to stop daemon when done

# Only GPIOs 12, 13, 18, and 19 have hardware PWM capabilities 
# --> issue because PiTFT uses 18, so if we want 2 camera gimbals
# we need 4 hardware PWMs.

# Use GPIOs 12 and 19 for looker gimbal
LOOK_BASE_GIMBAL_PIN = 12
LOOK_HEAD_GIMBAL_PIN = 19

# Set up hardware PWM values - duty cycle values multiplied by 10,000 because of 0-1M scale
FREQ = 50               # 50 Hz = 20 ms period

# Base gimbal (Left-Right)
LEFT_LOOK_DC = 60000         # 50 Hz @ 6% duty cycle = 1.2 ms pulse width
CENTER_BASE_LOOK_DC = 90000  # 50 Hz @ 9% duty cycle = 1.8 ms pulse width
RIGHT_LOOK_DC = 120000       # 50 Hz @ 12% duty cycle = 2.4 ms pulse width

# Head gimbal (Up-Down)
UP_LOOK_DC = 40000           # 50 Hz @ 4% duty cycle = 0.8 ms pulse width
CENTER_HEAD_LOOK_DC = 65000  # 50 Hz @ 6.5% duty cycle = 1.3 ms pulse width
DOWN_LOOK_DC = 90000         # 50 Hz @ 9% duty cycle = 1.8 ms pulse width

pi = pigpio.pi()

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

def stop_PWM():
    pi.hardware_PWM(LOOK_BASE_GIMBAL_PIN, FREQ, 0)
    pi.hardware_PWM(LOOK_HEAD_GIMBAL_PIN, FREQ, 0)

# Practice routine

cpu_look_center()
print("Center")
sleep(3)

cpu_look_up()
print("Up")
sleep(3)
cpu_look_center()
print("Center")
sleep(1)

cpu_look_down()
print("Down")
sleep(3)
cpu_look_center()
print("Center")
sleep(1)

cpu_look_left()
print("Left")
sleep(3)
cpu_look_center()
print("Center")
sleep(1)

cpu_look_right()
print("Right")
sleep(3)

cpu_look_center()
print("Center")
sleep(3)

stop_PWM()