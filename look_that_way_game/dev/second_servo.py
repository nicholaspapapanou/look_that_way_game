import pigpio
from time import sleep

# Need to run "sudo pigpiod" to start daemon before running
# Need to run "sudo killall pigpiod" to stop daemon when done

# Use GPIOs 4 and 5 for point gimbal
POINT_BASE_GIMBAL_PIN = 4
POINT_HEAD_GIMBAL_PIN = 5

# Set up hardware PWM values - duty cycle values multiplied by 10,000 because of 0-1M scale
FREQ = 50               # 50 Hz = 20 ms period

# Base gimbal (Left-Right)
LEFT_POINT_DC = 80500         # 50 Hz @ 6% duty cycle = 1.2 ms pulse width
CENTER_BASE_POINT_DC = 105500  # 50 Hz @ 9% duty cycle = 1.8 ms pulse width
RIGHT_POINT_DC = 130500       # 50 Hz @ 12% duty cycle = 2.4 ms pulse width

# Head gimbal (Up-Down)
UP_POINT_DC = 70000           # 50 Hz @ 7.5% duty cycle = 1.5 ms pulse width
CENTER_HEAD_POINT_DC = 100000 # 50 Hz @ 10 duty cycle = 2 ms pulse width
DOWN_POINT_DC = 130000        # 50 Hz @ 12.5% duty cycle = 2.5 ms pulse width
pi = pigpio.pi()

# Configure hardware-timed PWM GPIOs used for pointer gimbal to mimic 
# hardware PWM GPIOs used for looker gimbal (made range 10000 instead of 1M
# --> must divide duty cycle values by 100 when doing pointer functions)
pi.set_PWM_range(POINT_BASE_GIMBAL_PIN, 10000)
pi.set_PWM_range(POINT_HEAD_GIMBAL_PIN, 10000)
pi.set_PWM_frequency(POINT_BASE_GIMBAL_PIN, FREQ)
pi.set_PWM_frequency(POINT_HEAD_GIMBAL_PIN, FREQ)

def stop_PWM():
    pi.set_PWM_dutycycle(POINT_BASE_GIMBAL_PIN, 0)
    pi.set_PWM_dutycycle(POINT_HEAD_GIMBAL_PIN, 0)

# CPU pointer gimbal

def cpu_point_left():
    pi.set_PWM_dutycycle(POINT_BASE_GIMBAL_PIN, LEFT_POINT_DC/100)   

def cpu_point_right():
    pi.set_PWM_dutycycle(POINT_BASE_GIMBAL_PIN, RIGHT_POINT_DC/100)   

def cpu_point_up():
    pi.set_PWM_dutycycle(POINT_HEAD_GIMBAL_PIN, UP_POINT_DC/100)

def cpu_point_down():
    pi.set_PWM_dutycycle(POINT_HEAD_GIMBAL_PIN, DOWN_POINT_DC/100)   

def cpu_point_center():
    pi.set_PWM_dutycycle(POINT_BASE_GIMBAL_PIN, CENTER_BASE_POINT_DC/100)
    pi.set_PWM_dutycycle(POINT_HEAD_GIMBAL_PIN, CENTER_HEAD_POINT_DC/100)

# Practice routine

cpu_point_center()
print("Center")
sleep(3)

cpu_point_up()
print("Up")
sleep(3)
cpu_point_center()
print("Center")
sleep(1)

cpu_point_down()
print("Down")
sleep(3)
cpu_point_center()
print("Center")
sleep(1)

cpu_point_left()
print("Left")
sleep(3)
cpu_point_center()
print("Center")
sleep(1)

cpu_point_right()
print("Right")
sleep(3)

cpu_point_center()
print("Center")
sleep(3)

stop_PWM()