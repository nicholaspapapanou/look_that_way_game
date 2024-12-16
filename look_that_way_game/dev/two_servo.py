import pigpio
from time import sleep

# Need to run "sudo pigpiod" to start daemon before running
# Need to run "sudo killall pigpiod" to stop daemon when done

# Use GPIOs 4 and 5 for point gimbal
POINT_BASE_GIMBAL_PIN = 4
POINT_HEAD_GIMBAL_PIN = 5

# Use GPIOs 12 and 19 for looker gimbal
LOOK_BASE_GIMBAL_PIN = 12
LOOK_HEAD_GIMBAL_PIN = 19

# Set up hardware PWM values - duty cycle values multiplied by 10,000 because of 0-1M scale
FREQ = 50               # 50 Hz = 20 ms period

### Pointer Gimbal Duty Cycles ###

# Base gimbal (Left-Right)
LEFT_POINT_DC = 805         # 50 Hz @ 8.05% duty cycle =  1.61 ms pulse width
CENTER_BASE_POINT_DC = 1055 # 50 Hz @ 10.55% duty cycle = 2.11 ms pulse width
RIGHT_POINT_DC = 1305       # 50 Hz @ 13.05% duty cycle = 2.61 ms pulse width

# Head gimbal (Up-Down)
UP_POINT_DC = 700           # 50 Hz @ 7% duty cycle = 1.4 ms pulse width
CENTER_HEAD_POINT_DC = 1000 # 50 Hz @ 10 duty cycle = 2 ms pulse width
DOWN_POINT_DC = 1300        # 50 Hz @ 13% duty cycle = 2.6 ms pulse width

### Looker Gimbal Duty Cycles ###

# Base gimbal (Left-Right)
LEFT_LOOK_DC = 60000         # 50 Hz @ 6% duty cycle = 1.2 ms pulse width
CENTER_BASE_LOOK_DC = 90000  # 50 Hz @ 9% duty cycle = 1.8 ms pulse width
RIGHT_LOOK_DC = 120000       # 50 Hz @ 12% duty cycle = 2.4 ms pulse width

# Head gimbal (Up-Down)
UP_LOOK_DC = 40000           # 50 Hz @ 4% duty cycle = 0.8 ms pulse width
CENTER_HEAD_LOOK_DC = 65000  # 50 Hz @ 6.5% duty cycle = 1.3 ms pulse width
DOWN_LOOK_DC = 90000         # 50 Hz @ 9% duty cycle = 1.8 ms pulse width

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

# Practice routine

cpu_point_center()
cpu_look_center()
print("Center")
sleep(3)

cpu_point_up()
cpu_look_up()
print("Up")
sleep(3)
cpu_point_center()
cpu_look_center()
print("Center")
sleep(1)

cpu_point_down()
cpu_look_down()
print("Down")
sleep(3)
cpu_point_center()
cpu_look_center()
sleep(1)

cpu_point_left()
cpu_look_left()
print("Left")
sleep(3)
cpu_point_center()
cpu_look_center()
print("Center")
sleep(1)

cpu_point_right()
cpu_look_right()
print("Right")
sleep(3)

cpu_point_center()
cpu_look_center()
print("Center")
sleep(3)

stop_PWM()