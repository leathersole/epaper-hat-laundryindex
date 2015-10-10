# Copyright 2013 Pervasive Displays, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#   http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.


import sys
import os
import subprocess
import Image
import ImageDraw
import ImageFont
from EPD import EPD
import smbus
import lxml.html
import requests
from datetime import datetime
import re
from time import sleep
import RPi.GPIO as GPIO # Use the RPi.GPIO python module - need to run as root

GPIO.setmode(GPIO.BCM) # Use Broadcom GPIO pin designations
GPIO.setwarnings(False) # Disable warning messages, because they annoy me!
gpio_out = [6, 12, 5] # Led driven Red, Green, Blue on GPIO 6, 12, 5 respectively

bus = smbus.SMBus(1)

WHITE = 1
BLACK = 0

RED = 6
GREEN = 12
BLUE =5

LED_WHILE = {RED:True,GREEN:True,BLUE:True}
LED_BLACK = {RED:False,GREEN:False,BLUE:False}
LED_RED = {RED:True,GREEN:False,BLUE:False}
LED_GREEN = {RED:False,GREEN:True,BLUE:False}
LED_BLUE = {RED:False,GREEN:False,BLUE:True}

# fonts are in different places on Raspbian/Angstrom so search
possible_fonts = [
    '/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf',            # Debian B.B
#    '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf',   # Debian B.B
    '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSansMono-Bold.ttf',   # R.Pi
    '/usr/share/fonts/truetype/freefont/FreeMono.ttf',                # R.Pi
#    '/usr/share/fonts/truetype/LiberationMono-Bold.ttf',              # B.B
#    '/usr/share/fonts/truetype/DejaVuSansMono-Bold.ttf'               # B.B
]

FONT_FILE = ''
for f in possible_fonts:
    if os.path.exists(f):
        FONT_FILE = f
        break

if '' == FONT_FILE:
    raise 'no font file found'

TIMESTAMP_FONT_SIZE = 20
TODAY_FONT_SIZE = 110 
TOMORROW_FONT_SIZE = 70 
REST_FONT_SIZE = 35 

for x in gpio_out: # Set up three led RGB channels as outputs
    GPIO.setup(x, GPIO.OUT)

def main(argv):
    """main program - draw HH:MM clock on 2.70" size panel"""

    epd = EPD()

    print('panel = {p:s} {w:d} x {h:d}  version={v:s}  cog={g:d}'.format(p=epd.panel, w=epd.width, h=epd.height, v=epd.version, g=epd.cog))

    if 'EPD 2.7' != epd.panel:
        print('incorrect panel size')
        sys.exit(1)

    epd.clear()

    demo(epd)

def demo(epd):
    """simple partial update demo - draw draw a clock"""

    # initially set all white background
    image = Image.new('1', epd.size, WHITE)

    # prepare for drawing
    draw = ImageDraw.Draw(image)
    width, height = image.size

    timestamp_font = ImageFont.truetype(FONT_FILE, TIMESTAMP_FONT_SIZE)
    today_font = ImageFont.truetype(FONT_FILE, TODAY_FONT_SIZE)
    tomorrow_font = ImageFont.truetype(FONT_FILE, TOMORROW_FONT_SIZE)
    rest_font = ImageFont.truetype(FONT_FILE, REST_FONT_SIZE)

    (cloth_dried_today, cloth_dried_tomorrow,cloth_dried_r1,cloth_dried_r2,cloth_dried_r3,cloth_dried_r4,cloth_dried_r5) = get_cloth_dried()
    now = datetime.today()

    # clear the display buffer
    draw.rectangle((0, 0, width, height), fill=WHITE, outline=WHITE)

    draw.rectangle((3, 3, width - 3, height - 3), fill=WHITE, outline=BLACK)
    # print (width - X_OFFSET), "  ", (height - Y_OFFSET)	
    # draw.rectangle((0,86,264,176), fill=WHITE, outline=WHITE)
    draw.text((4, 4), now.strftime("%Y/%m/%d %H:%M:%S"), fill=BLACK, font=timestamp_font)
    draw.text((5, 15), cloth_dried_today, fill=BLACK, font=today_font)
    draw.text((5, 110), cloth_dried_tomorrow, fill=BLACK, font=tomorrow_font)
    draw.text((200, 20), cloth_dried_r1, fill=BLACK, font=rest_font)
    draw.text((200, 50), cloth_dried_r2, fill=BLACK, font=rest_font)
    draw.text((200, 80), cloth_dried_r3, fill=BLACK, font=rest_font)
    draw.text((200, 110), cloth_dried_r4, fill=BLACK, font=rest_font)
    draw.text((200, 140), cloth_dried_r5, fill=BLACK, font=rest_font)
    # display image on the panel
#	epd.clear()
    epd.display(image)
    epd.update()

    today_value = int(cloth_dried_today)
    if today_value > 80:
        turn_led(LED_RED)
    elif today_value > 50:
        turn_led(LED_GREEN)
    else:
        turn_led(LED_BLUE)

def get_cloth_dried():
    p = re.compile('[0-9]+$')

    target_url = 'http://www.tenki.jp/indexes/cloth_dried/3/16/4410.html'
    target_html = requests.get(target_url).text
    root = lxml.html.fromstring(target_html)
    cloth_dried_today = root.cssselect('#exponentLargeLeft > dd > dl > dd')[0].text_content()
    cloth_dried_tomorrow = root.cssselect('#exponentLargeRight > dd > dl > dd')[0].text_content()
    cloth_dried_r1 = root.cssselect('td.amedasIcon:nth-child(2) > p:nth-child(2)')[0].text_content()
    cloth_dried_r2 = root.cssselect('td.amedasIcon:nth-child(3) > p:nth-child(2)')[0].text_content()
    cloth_dried_r3 = root.cssselect('td.amedasIcon:nth-child(4) > p:nth-child(2)')[0].text_content()
    cloth_dried_r4 = root.cssselect('td.amedasIcon:nth-child(5) > p:nth-child(2)')[0].text_content()
    cloth_dried_r5 = root.cssselect('td.amedasIcon:nth-child(6) > p:nth-child(2)')[0].text_content()
    return (cloth_dried_today,
            cloth_dried_tomorrow,
            p.search(cloth_dried_r1).group(),
            p.search(cloth_dried_r2).group(),
            p.search(cloth_dried_r3).group(),
            p.search(cloth_dried_r4).group(),
            p.search(cloth_dried_r5).group()
    )

def turn_led(colorMap):
    for color_name in colorMap.keys():
        GPIO.output(color_name,colorMap[color_name])

# main
if "__main__" == __name__:
    if len(sys.argv) < 1:
        sys.exit('usage: {p:s}'.format(p=sys.argv[0]))

    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit('interrupted')
        pass
