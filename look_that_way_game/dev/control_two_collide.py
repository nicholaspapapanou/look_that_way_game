# Nicholas Papapanou (ngp37) & Nathan Rakhlin (npr29)
# Lab 2 10/3/24

import pygame,pigame
from pygame.locals import *
import os
from time import sleep,time
import RPi.GPIO as GPIO
import sys

# Colors
WHITE = (255,255,255)
BLACK = (0, 0, 0)
GREEN = (39, 119, 20)

# Uncomment to run on PiTFT
os.putenv('SDL_VIDEODRV','fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV','dummy')
os.putenv('SDL_MOUSEDEV','/dev/null')
os.putenv('DISPLAY','')

# Initialize pygame and pigame
pygame.init()
pitft = pigame.PiTft()

# Setup screen and size parameters
size = width, height = 320, 240
screen = pygame.display.set_mode(size)

# pygame.mouse.set_visible(False) # Comment when debugging on monitor

# Setup GPIO numbering and button 27 as active low
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(27, GPIO.IN, pull_up_down = GPIO.PUD_UP)

# Setup bailout button functionality with threaded callback 
def GPIO27_callback(channel):
    global code_run
    global total_runtime
    global init_time
    print("Bailout button pressed!")
    code_run = False
GPIO.add_event_detect(27, GPIO.FALLING, callback=GPIO27_callback, bouncetime=300)      

# Font size
font_big = pygame.font.Font(None, 50)
font_small = pygame.font.Font(None, 25)
      
# Define buttons for each menu level in dictionary
level_1_buttons = {'Start': (80, 200), 'Quit':(240,200)}
level_2_buttons = {'Pause': (40, 200), 'Fast': (120, 200), 'Slow': (200, 200), 'Back': (280, 200)}

# Draw level 1 buttons
for k,v in level_1_buttons.items():
    text_surface = font_big.render('%s'%k, True, WHITE)
    rect = text_surface.get_rect(center=v)
    screen.blit(text_surface, rect)        

# Initialize level functionality parameters
level = 1 
touch_bool = False

# Ball speed parameters
speed_1 = [2,2]
speed_2 = [4,4]

# Initialize balls: load and scale images, get rects
ball_1 = pygame.image.load("/home/pi/lab2/8ball.png")
ball_1 = pygame.transform.scale(ball_1, (50,50))
ball_1_rect = ball_1.get_rect(center=(150,150))
ball_2 = pygame.image.load("/home/pi/lab2/cueball.png")
ball_2 = pygame.transform.scale(ball_2, (45,45))
ball_2_rect = ball_2.get_rect(center=(75,75))

# Deflate rects for more realistic corner collisions
ball_1_rect = ball_1_rect.inflate(-5, -5) 
ball_2_rect = ball_2_rect.inflate(-5, -5) 

# Set FPS and initialize clock
FPS = 96
my_clock = pygame.time.Clock()

# Initialize global time variables
code_run = True
total_runtime = 30 # Auto-timeout duration
init_time = time()

### MAIN CODE ### 

try:
    while code_run:

        # Runtime auto timeout logic
        if (time() - init_time) >= total_runtime:
            code_run = False
        pitft.update()
        screen.fill(BLACK)

        # Reset speed increase/decrease flags 
        fast = False
        slow = False

        # Scan touchscreen events to determine what should be displayed on screen
        for event in pygame.event.get():
            if(event.type is MOUSEBUTTONUP):
                x,y = pygame.mouse.get_pos()
                # Service where touch
                if level == 1:    # Level 1 menu
                  if y > 160:
                      if x > 160: # Quit button pressed
                          print(f"Quit button pressed at ({x}, {y})!")
                          pygame.quit()
                          sys.exit(0)
                      else:       # Start button pressed
                          print(f"Start button pressed at ({x}, {y})!")
                          move = True                                 # Set start animation flag high
                          #  Re-initialize 2 balls: load and scale image, get and deflate rects
                          ball_1 = pygame.image.load("/home/pi/lab2/8ball.png")
                          ball_1 = pygame.transform.scale(ball_1, (50,50))
                          ball_1_rect = ball_1.get_rect(center=(150,150))
                          ball_1_rect = ball_1_rect.inflate(-5, -5) 
                          ball_2 = pygame.image.load("/home/pi/lab2/cueball.png")
                          ball_2 = pygame.transform.scale(ball_2, (45,45))
                          ball_2_rect = ball_2.get_rect(center=(75,75))
                          ball_2_rect = ball_2_rect.inflate(-5, -5) 
                          level = 2                                   # Increment menu level
                          touch_bool = False                          # Turn off screen coord functionality
                  else:           # Area above buttons pressed --> screen coordinate functionality
                      touch_bool = True
                      touch_string = f"Touch at ({x}, {y})"
                      print(touch_string) 

                elif level == 2:    # Level 2 menu
                    if y > 160:
                        if x < 80:  # Pause button pressed
                            print(f"Pause button pressed at ({x}, {y})!")
                            if move:
                                move = False
                            else:   # Restart button pressed
                                move = True                                 # Set start animation flag high
                                #  Re-initialize 2 balls: load and scale image, get and deflate rects
                                ball_1 = pygame.image.load("/home/pi/lab2/8ball.png")
                                ball_1 = pygame.transform.scale(ball_1, (50,50))
                                ball_1_rect = ball_1.get_rect(center=(150,150))
                                ball_1_rect = ball_1_rect.inflate(-5, -5) 
                                ball_2 = pygame.image.load("/home/pi/lab2/cueball.png")
                                ball_2 = pygame.transform.scale(ball_2, (45,45))
                                ball_2_rect = ball_2.get_rect(center=(75,75))
                                ball_2_rect = ball_2_rect.inflate(-5, -5) 
                            
                        elif x < 160: # Fast button pressed
                            print(f"Fast button pressed at ({x}, {y})!")
                            fast = True                                     # Prepare speed increase
                        elif x < 240: # Slow button pressed
                            print(f"Slow button pressed at ({x}, {y})!")
                            slow = True                                     # Prepare speed decrease
                        else:         # Back button pressed
                            print(f"Back button pressed at ({x}, {y})!")
                            level = 1                                       # Reset to menu level 1
                            move = False                                    # Set animation flag low
                            touch_bool = False                              # Safeguard, should alread be false

        # Now that events have been handled to determine what to display, do the actual displaying
        
        if level == 1:          # Menu level 1  
            font = font_big
            touch_buttons = level_1_buttons
            if touch_bool:      # Area above level 1 buttons was clicked, print coords
              text_surface = font_big.render(touch_string, True, WHITE)
              rect = text_surface.get_rect(center=(160, 120))
              screen.blit(text_surface, rect) 
            sleep(0.1)
              
        elif level == 2:        # Menu level 2
            font = font_small
            touch_buttons = level_2_buttons
            if fast:            # Fast button was clicked, increase speed by 10%
                FPS = FPS * 1.1
            if slow:            # Slow button was clicked, decrease speed by 10%
                FPS = FPS * 0.9

            # Draw animation 
            my_clock.tick(FPS) 
            screen.fill(GREEN)
            if move:
                # Logic for each ball colliding with screen borders
                ball_1_rect = ball_1_rect.move(speed_1)
                if ball_1_rect.left < 0 or ball_1_rect.right > width:
                    speed_1[0] = -speed_1[0]
                if ball_1_rect.top < 0 or ball_1_rect.bottom > height:
                    speed_1[1] = -speed_1[1]
                ball_2_rect = ball_2_rect.move(speed_2)
                if ball_2_rect.left < 0 or ball_2_rect.right > width:
                    speed_2[0] = -speed_2[0]
                if ball_2_rect.top < 0 or ball_2_rect.bottom > height:
                    speed_2[1] = -speed_2[1]
                # Logic for balls colliding with each other
                if ball_1_rect.colliderect(ball_2_rect):
                    x1 = ball_1_rect.centerx
                    x2 = ball_2_rect.centerx
                    y1 = ball_1_rect.centery
                    y2 = ball_2_rect.centery
                    if x1 < x2:
                        speed_1[0] = -abs(speed_1[0])
                        speed_2[0] = abs(speed_2[0])
                    else:
                        speed_1[0] = abs(speed_1[0])
                        speed_2[0] = -abs(speed_2[0])
                    if y1 < y2:
                        speed_1[1] = -abs(speed_1[1])
                        speed_2[1] = abs(speed_2[1])
                    else:
                        speed_1[1] = abs(speed_1[1])
                        speed_2[1] = -abs(speed_2[1])

            screen.blit(ball_1, ball_1_rect) # Combine ball1 surface with workspace surface
            screen.blit(ball_2, ball_2_rect) # Combine ball2 surface with workspace surface

        # Draw current level's buttons from respective dictionary
        for k,v in touch_buttons.items():
            text_surface = font.render('%s'%k, True, WHITE)
            rect = text_surface.get_rect(center=v)
            screen.blit(text_surface, rect)   

        pygame.display.update()     # Display workspace on screen   
        
except KeyboardInterrupt:
    pass

finally:
    del(pitft)
    GPIO.cleanup()
