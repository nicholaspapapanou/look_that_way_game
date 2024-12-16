import pygame
from time import sleep

try:
    pygame.init()
    pygame.mixer.init()

    path = "/home/pi/look_that_way_game/sounds/"

    pygame.mixer.music.load(f"{path}game_music.mp3")

    # Load and play background music in the INIT stage
    def start_background_music():
        pygame.mixer.music.play(loops=-1, start=0.0)  # loops=-1 for infinite loop
        # pygame.mixer.music.set_volume(1)

    # Stop background music in the GAMEOVER stage
    def stop_background_music():
        pygame.mixer.music.stop()

    # Initialize sounds

    short_beep = pygame.mixer.Sound(f"{path}short_beep.wav")
    short_beep.set_volume(0.5)

    long_beep = pygame.mixer.Sound(f"{path}long_beep.wav")
    long_beep.set_volume(0.5)   

    game_over_sound = pygame.mixer.Sound(f"{path}game_over_sound.wav")
    game_over_sound.set_volume(0.75)   

    game_over_speech = pygame.mixer.Sound(f"{path}game_over_speech.wav")
    game_over_speech.set_volume(0.25)   

    timing_buzzer = pygame.mixer.Sound(f"{path}timing_buzzer.wav")
    timing_buzzer.set_volume(0.25)

    next_level_sound = pygame.mixer.Sound(f"{path}next_level.wav")
    next_level_sound.set_volume(0.5)

    score_sound = pygame.mixer.Sound(f"{path}score.wav")
    score_sound.set_volume(0.5)

    success_sound = pygame.mixer.Sound(f"{path}success.wav")
    success_sound.set_volume(1)

    sounds = [short_beep, long_beep, game_over_sound, game_over_speech, timing_buzzer, next_level_sound, score_sound, success_sound]

    # Play sounds
    print("Play sounds")
    for sound in sounds:
        sound.play()
        sleep(sound.get_length())

    print("Done with sounds")
    sleep(2)

    # Play music for 5 seconds

    print("start background music")
    start_background_music()
    sleep(5)
    print("stop background music")
    stop_background_music()

    pygame.mixer.quit()
    pygame.quit()

finally:
    print("finally")
    pygame.mixer.quit()
    print("mixer quit")
    pygame.quit()
    print("pygame quit")