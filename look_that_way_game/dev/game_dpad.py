from enum import Enum
import random
import time
import RPi.GPIO as GPIO


'''
GPIOs

Top: 26
Right: 13
Bottom: 16
Left: 6
'''

GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN, pull_up_down = GPIO.PUD_UP) # Top
GPIO.setup(13, GPIO.IN, pull_up_down = GPIO.PUD_UP) # Right
GPIO.setup(16, GPIO.IN, pull_up_down = GPIO.PUD_UP) # Bottom
GPIO.setup(6, GPIO.IN, pull_up_down = GPIO.PUD_UP)  # Left

def GPIO26_callback(channel):
    global usr_point
    usr_point = "up"
    print(f"button {usr_point} pushed")
GPIO.add_event_detect(26, GPIO.FALLING, callback=GPIO26_callback, bouncetime=300)  

def GPIO13_callback(channel):
    global usr_point
    usr_point = "right"
    print(f"button {usr_point} pushed")
GPIO.add_event_detect(13, GPIO.FALLING, callback=GPIO13_callback, bouncetime=300)  

def GPIO16_callback(channel):
    global usr_point
    usr_point = "down"
    print(f"button {usr_point} pushed")
GPIO.add_event_detect(16, GPIO.FALLING, callback=GPIO16_callback, bouncetime=300)  

def GPIO6_callback(channel):
    global usr_point
    usr_point = "left"
    print(f"button {usr_point} pushed")
GPIO.add_event_detect(6, GPIO.FALLING, callback=GPIO6_callback, bouncetime=300)  


class States(Enum):
    INIT = 1
    USR_POINTER = 2
    USR_LOOK = 3
    GAMEOVER = 4
    LEADERBOARD = 5
    SETTINGS = 6

class Directions():
  left  = "left"
  right = "right"
  up    = "up"
  down  = "down"

  dirs = [left, right, up, down]

  def select_random_direction():
    return Directions.dirs[random.randint(0, 3)]


look = ""

point = ""

state = States.INIT
next_state = None


countdown = 3
score_multiplier = 1
level = 1
score = 0
points_per_score = 1


def get_user_input():
  usr_point = ""
  while(usr_point not in Directions.dirs):
      usr_point = input("Please input your direction for pointing (left, right, up, down): \n")
  time.sleep(0.5)
  ai_point = Directions.select_random_direction()
  print(f"ai point direction: {ai_point}")
  return usr_point, ai_point


ready = False

try:
  while(1):
    print(f"Score: {score}")
    print(f"Level: {level}")
    usr_point = ""
    ai_point = ""
    #currently in state x
    if state == States.INIT:
      print("Welcome to Game")
      pass

    elif state == States.USR_POINTER:
      print("User_pointer")
      ready = True
      while(usr_point == ""):
        pass
      time.sleep(1)
      ai_point = Directions.select_random_direction()
      print(f"ai point direction: {ai_point}")
      # usr_point, ai_point = get_user_input()
    
    elif state == States.USR_LOOK:
      print("user_looker")
      while(usr_point == ""):
        pass
      time.sleep(1)
      ai_point = Directions.select_random_direction()
      print(f"ai point direction: {ai_point}")
      # usr_point, ai_point = get_user_input()

    elif state == States.GAMEOVER:
      print("Sorry, you loose")
      print(f"Final Score: {score}")
      print(f"Final level: {level}")
      break

    time.sleep(1)

    #handle state transition from 
    if state == States.INIT:
      next_state = States.USR_POINTER
    if state == States.USR_POINTER:
      if usr_point == ai_point:
        score += score_multiplier * points_per_score
        next_state = state
        print("Great job, you gottem! Try to catch this individual once more!!")
      else:
        next_state = States.USR_LOOK
        print("Nice try but you missed, Mr.")
        print("Switch sides!")
    
    if state == States.USR_LOOK:

      if usr_point == ai_point:
        next_state = States.GAMEOVER
        print("The AI got you why would you let it do that!!")
      else:
        countdown = countdown - countdown * 0.2
        score_multiplier = score_multiplier * 1.1
        level += 1
        next_state = States.USR_POINTER
        print("Nice job, you evaded the AI!!")

    time.sleep(1)
    print("\n")
    
    state = next_state

except KeyboardInterrupt:
   pass
finally:
   GPIO.cleanup
