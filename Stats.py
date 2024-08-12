from microbit import *
import radio
import struct

ADDR = 0x3C
screen = bytearray(513)  # send byte plus pixels
screen[0] = 0x40
zoom = 1

def set_px(x, y, color, draw=1):
    page, shift_page = divmod(y, 8)
    ind = x * 2 + page * 128 + 1
    b = screen[ind] | (1 << shift_page) if color else screen[ind] & ~(1 << shift_page)
    struct.pack_into(">BB", screen, ind, b, b)
    if draw:
        set_pos(x, page)
        i2c.write(0x3C, bytearray([0x40, b, b]))

def set_zoom(v):
    global zoom
    if zoom != v:
        command([0xD6, v])  # zoom on/off
        command([0xA7 - v])  # inverted display
        zoom = v

def get_px(x, y):
    page, shift_page = divmod(y, 8)
    ind = x * 2 + page * 128 + 1
    b = (screen[ind] & (1 << shift_page)) >> shift_page
    return b

def draw_screen():
    set_pos()
    i2c.write(ADDR, screen)

def set_pos(col=0, page=0):
    command([0xB0 | page])  # page number
    # take upper and lower value of col * 2
    c1, c2 = col * 2 & 0x0F, col >> 3
    command([0x00 | c1])  # lower start column address
    command([0x10 | c2])  # upper start column address

def clear_oled(c=0):
    global screen
    set_pos()
    for i in range(1, 513):
        screen[i] = 0
    draw_screen()

def command(c):
    i2c.write(ADDR, b'\x00' + bytearray(c))

def add_text(x, y, text, draw=1):
    for i in range(0, min(len(text), 12 - x)):
        for c in range(0, 5):
            col = 0
            for r in range(1, 6):
                p = Image(text[i]).get_pixel(c, r - 1)
                col = col | (1 << r) if (p != 0) else col
            ind = x * 10 + y * 128 + i * 10 + c * 2 + 1
            screen[ind], screen[ind + 1] = col, col
    if draw == 1:
        set_zoom(1)
        set_pos(x * 5, y)
        ind0 = x * 10 + y * 128 + 1
        i2c.write(ADDR, b'\x40' + screen[ind0:ind + 1])

def initialize():
    cmd = [
        [0xAE],                     # SSD1306_DISPLAYOFF
        [0xA4],                     # SSD1306_DISPLAYALLON_RESUME
        [0xD5, 0xF0],               # SSD1306_SETDISPLAYCLOCKDIV
        [0xA8, 0x3F],               # SSD1306_SETMULTIPLEX
        [0xD3, 0x00],               # SSD1306_SETDISPLAYOFFSET
        [0 | 0x0],                  # line #SSD1306_SETSTARTLINE
        [0x8D, 0x14],               # SSD1306_CHARGEPUMP
        # 0x20 0x00 horizontal addressing
        [0x20, 0x00],               # SSD1306_MEMORYMODE
        [0x21, 0, 127],             # SSD1306_COLUMNADDR
        [0x22, 0, 63],              # SSD1306_PAGEADDR
        [0xA0 | 0x1],               # SSD1306_SEGREMAP
        [0xC8],                     # SSD1306_COMSCANDEC
        [0xDA, 0x12],               # SSD1306_SETCOMPINS
        [0x81, 0xCF],               # SSD1306_SETCONTRAST
        [0xD9, 0xF1],               # SSD1306_SETPRECHARGE
        [0xDB, 0x40],               # SSD1306_SETVCOMDETECT
        [0xA6],                     # SSD1306_NORMALDISPLAY
        [0xD6, 1],                  # zoom on
        [0xAF]                      # SSD1306_DISPLAYON
    ]
    for c in cmd:
        command(c)


def update_display(message_type, message_data):
    if message_type == "lvl":
        add_text(0, 0, "Level: " + message_data)
    elif message_type == "lvlt":
        add_text(0, 1, "Time: " + message_data)
    elif message_type == "rst":
        add_text(0, 2, "Restart: " + message_data)
    elif message_type == "dth":
        add_text(0, 3, "Deaths: " + message_data)
    elif message_type == "clr":
        clear_oled()
        draw_screen()


def process_message(message):
    parts = message.split(";")
    message_type = parts[0]
    message_data = parts[1] if len(parts) > 1 else None

    # Update display and send data to PC
    update_display(message_type, message_data)
    uart.write(message + "\n")


initialize()
clear_oled()
radio.config(group=23)
radio.on()

while True:
    incoming_message = radio.receive()
    if incoming_message:
        process_message(incoming_message)
    sleep(10)
