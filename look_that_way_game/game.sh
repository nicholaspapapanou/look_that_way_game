#!/bin/bash
cd /home/pi/look_that_way_game
sudo pigpiod
sudo -E python /home/pi/look_that_way_game/game_final.py
sudo killall pigpiod
