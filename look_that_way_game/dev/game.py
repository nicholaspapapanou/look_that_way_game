from enum import Enum
import random
import time
import sys
import select
import threading

class States(Enum):
    STARTUP = 1
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

state = States.STARTUP
next_state = None


countdown = 5
score_multiplier = 1
level = 1
score = 0
points_per_score = 1

def print_remaining_time(timeout, stop_event):
    """ Function to print remaining time every second """
    for remaining in range(timeout, 0, -1):
        if stop_event.is_set():  # Check if the countdown should be stopped
            print("\nCountdown stopped.")
            return
        print(f"\nTime remaining: {remaining} seconds", end='\r')
        time.sleep(1)
    print("Time's up! No input received within the given time.")


def get_decisions():
  usr_point = ""
  while(usr_point not in Directions.dirs):
      usr_point = input("Please input your direction for pointing (left, right, up, down): \n")
  time.sleep(0.5)
  # ai_point = Directions.select_random_direction()
  ai_point = "right"
  print(f"ai point direction: {ai_point}")
  return usr_point, ai_point

def get_user_input_with_timeout(timeout=3):
    """ Function to get user input with a timeout and display remaining time every second """
    
    print(f"You have {timeout} seconds to enter your input:")
    
    # Create an event to signal when to stop the countdown
    stop_event = threading.Event()

    # Start a background thread to print the countdown
    countdown_thread = threading.Thread(target=print_remaining_time, args=(timeout, stop_event))
    countdown_thread.start()

    # Wait for input for 'timeout' seconds
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)

    if rlist:
        user_input = sys.stdin.readline().strip()  # Read the input
        stop_event.set()  # Stop the countdown thread once input is received
        print(f"\nUser input: {user_input}")
        return user_input
    else:
        stop_event.set()  # Stop the countdown thread if no input is received
        print(f"\nTime's up! No input received within {timeout} seconds.")
        return None

while(1):
  print(f"Score: {round(score, 3)}")
  print(f"Level: {level}")
  usr_point = ""
  ai_point = ""
  #currently in state x
  if state == States.STARTUP:
    print("Welcome to Game")
    pass

  elif state == States.USR_POINTER:
    print("User_pointer")
    # usr_point, ai_point = get_decisions()
    usr_point = get_user_input_with_timeout(countdown)
    time.sleep(0.5)
    ai_point = Directions.select_random_direction()
    print(f"ai look direction: {ai_point}")
  
  elif state == States.USR_LOOK:
    print("user_looker")
    # usr_point, ai_point = get_decisions()
    usr_point = get_user_input_with_timeout(countdown)
    time.sleep(0.5)
    ai_point = Directions.select_random_direction()
    print(f"ai point direction: {ai_point}")

  elif state == States.GAMEOVER:
    print("Sorry, you lose")
    print(f"Final Score: {score}")
    print(f"Final level: {level}")
    break

  time.sleep(1)

  #handle state transition
  if state == States.STARTUP:
    next_state = States.USR_POINTER

  if state == States.USR_POINTER:
    if usr_point == None:
       next_state = States.GAMEOVER
       print("YOU RAN OUTTA TIME WHY WOULD YOU DO THAT YOU SHOULD BE FASTER WHAT THE HECK")
    elif usr_point == ai_point:
      score += score_multiplier * points_per_score
      next_state = state
      print("Great job, you gottem! Try to catch this individual once more!!")
    else:
      next_state = States.USR_LOOK
      print("Nice try but you missed, Mr.")
      print("Switch sides!")
  
  if state == States.USR_LOOK:
    if usr_point == None:
       next_state = States.GAMEOVER
       print("YOU RAN OUTTA TIME WHY WOULD YOU DO THAT YOU SHOULD BE FASTER WHAT THE HECK")
    elif usr_point == ai_point:
      next_state = States.GAMEOVER
      print("The AI got you why would you let it do that!!")
    else:
      countdown = countdown - countdown * 0.2
      score_multiplier = score * 1.1
      level += 1
      next_state = States.USR_POINTER
      print("Nice job, you evaded the AI!!")

  time.sleep(1)
  print("\n")
  
  state = next_state