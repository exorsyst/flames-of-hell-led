# starts a flame effect once the correct time is reached, staying on until the off time.
# while the strip is on during waking hours the sensor will not record a value or sent it to the mqtt service.
# it was far too problematic

import WIFI_CONFIG
from network_manager import NetworkManager
import ntp
import uasyncio
import urequests
import time
import utime
import plasma
from random import uniform
from plasma import plasma_stick
from machine import Pin
from machine import RTC
from pimoroni_i2c import PimoroniI2C

# Set how many LEDs you have
NUM_LEDS = 144

# How much snow? [bigger number = more flames]
FLAME_INTENSITY = 0.0035

# Change RGB colours here (RGB colour picker: https://g.co/kgs/k2Egjk )
BACKGROUND_COLOUR = [0, 40, 0]  # dim blue
FLAME_COLOUR = [80, 255, 0]  # bluish white

# how quickly current colour changes to target colour [1 - 255]
FADE_UP_SPEED = 10  # abrupt change for a snowflake
FADE_DOWN_SPEED = 5

# time to wake up and to turn the light off
flame_hour = 15
flame_minute = 10
off_hour = 17
off_minute = 00

def status_handler(mode, status, ip):
    # reports wifi connection status
#     print(mode, status, ip)
#     print('Connecting to wifi...')
    # flash while connecting
    for i in range(NUM_LEDS):
        led_strip.set_rgb(i, 50, 50, 150)
        time.sleep(0.02)
    for i in range(NUM_LEDS):
        led_strip.set_rgb(i, 0, 0, 0)
    if status is not None:
        if status:
            print('Wifi connection successful!')
        else:
            print('Wifi connection failed!')

# strip config
            
def display_current():
    # paint our current LED colours to the strip
    for i in range(NUM_LEDS):
        led_strip.set_rgb(i, current_leds[i][0], current_leds[i][1], current_leds[i][2])


def move_to_target():
    # nudge our current colours closer to the target colours
    for i in range(NUM_LEDS):
        for c in range(3):  # 3 times, for R, G & B channels
            if current_leds[i][c] < target_leds[i][c]:
                current_leds[i][c] = min(current_leds[i][c] + FADE_UP_SPEED, target_leds[i][c])  # increase current, up to a maximum of target
            elif current_leds[i][c] > target_leds[i][c]:
                current_leds[i][c] = max(current_leds[i][c] - FADE_DOWN_SPEED, target_leds[i][c])  # reduce current, down to a minimum of target

# Create a list of [r, g, b] values that will hold current LED colours, for display
current_leds = [[0] * 3 for i in range(NUM_LEDS)]
# Create a list of [r, g, b] values that will hold target LED colours, to move towards
target_leds = [[0] * 3 for i in range(NUM_LEDS)]

# set up the Pico W's onboard LED
pico_led = Pin('LED', Pin.OUT)

# set up the WS2812 / NeoPixel™ LEDs
led_strip = plasma.WS2812(NUM_LEDS, 0, 0, plasma_stick.DAT, color_order=plasma.COLOR_ORDER_RGB)

# start updating the LED strip
led_strip.start()

# set up wifi
try:
    network_manager = NetworkManager(WIFI_CONFIG.COUNTRY, status_handler=status_handler)
    uasyncio.get_event_loop().run_until_complete(network_manager.client(WIFI_CONFIG.SSID, WIFI_CONFIG.PSK))
except Exception as e:
    print(f'Wifi connection failed! {e}')
    
# CAN WE ADD set_time() here from the ntp script? Does it do anything?

while True:
    # get the time from Pico RTC
    year, month, day, hour, minute, second, _, _ = time.localtime()

# when it's time to start the flames this runs first
    if hour >= flame_hour and hour < off_hour and minute >= flame_minute:
        print('flame on')

        for i in range(NUM_LEDS):
            # randomly add snow
            if FLAME_INTENSITY > uniform(0, 1):
                # set a target to start a snowflake
                target_leds[i] = FLAME_COLOUR
            # slowly reset snowflake to background
            if current_leds[i] == target_leds[i]:
                target_leds[i] = BACKGROUND_COLOUR
        move_to_target()   # nudge our current colours closer to the target colours
        display_current()  # display current colours to strip

# after the start time this keeps the flames on
    elif hour > flame_hour and hour < off_hour and minute >= 0:
        print('flames of hell are licking')

        for i in range(NUM_LEDS):
            # randomly add snow
            if FLAME_INTENSITY > uniform(0, 1):
                # set a target to start a snowflake
                target_leds[i] = FLAME_COLOUR
            # slowly reset snowflake to background
            if current_leds[i] == target_leds[i]:
                target_leds[i] = BACKGROUND_COLOUR
        move_to_target()   # nudge our current colours closer to the target colours
        display_current()  # display current colours to strip

# once the end time is reached the LED will go off
    elif hour == off_hour and minute == off_minute:        
        print('all flames are now extinguished')
        led_strip.clear()
        print('led off')
        time.sleep(600)

# if it isn't time then the LEDs will go off checking in every 10 mins so make
# sure your on and off times are in 10 minute intervals
    else:        
        print("we're inbetween off time and flame time")
        led_strip.clear()
        print("turning the strip off and waiting for flame hour")
        time.sleep(60)



