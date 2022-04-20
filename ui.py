#!/usr/bin/python3

import gi
import cairo
import time
gi.require_version("Gtk", "3.0")
gi.require_version('PangoCairo', '1.0')
gi.require_version('Pango', '1.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, GLib, Pango, PangoCairo, Gst
import math
import datetime
#from gpiozero import PWMLED
#from gpiozero.pins.rpio import RPIOFactory
import shutil
import os
import fcntl
from pathlib import Path


pf = open('budka.pid','w')
pf.write(str(os.getpid()))
fcntl.lockf(pf, fcntl.LOCK_EX)

settings = {}

win = Gtk.Window()
win.connect("destroy", Gtk.main_quit)

start = 0
maxtime = 120
stop_timer = 0
timegap = 3








Gst.init(None)

audiosrc = "alsasrc device=hw:1"
videosrc = "v4l2src device=/dev/video0 ! video/x-h264,framerate=30/1,width=1920,height=1080 "

parser = "h264parse"
decoder = "h264dec"

pipeline = f"""
{videosrc} ! queue ! {parser} ! mux.
{audiosrc} ! audioresample ! audioconvert ! opusenc ! queue ! tee name=taudio 
matroskamux name=mux writing-app="Eri Kiosk" streamable=true ! filesink name=filesink
taudio. ! queue ! opusparse ! oggmux ! filesink name=audiofilesink
taudio. ! queue ! opusparse ! mux.
"""

#"""

#taudio. ! oggmux ! filesink name=audiofilesink
#taudio. ! mux.

#tvideo. ! {decoder} ! tee name=t2 
#t2. ! queue ! videoconvert ! gtksink name=preview
#t2. ! queue ! videoconvert ! videorate ! appsink name=facesink
#"""



pipeline = Gst.parse_launch(pipeline)
filesink = pipeline.get_child_by_name('filesink')
audiofilesink = pipeline.get_child_by_name('audiofilesink')


def checkfree(prefix):
    while True:
        total, used, free = shutil.disk_usage(prefix)
        if free > 1024*1024*1024:
            break
        paths = sorted(Path(prefix).iterdir(), key=os.path.getmtime)
        os.unlink(paths[0])


def video_rotate():
    prefix = settings['video']['prefix']
    checkfree(prefix)
    datedname = prefix + datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d-%H-%M-%S")
    filesink.set_property("location", datedname+'.mkv')
    audiofilesink.set_property("location", datedname+'.ogg')

def video_start():
    print('video_start')
    pipeline.set_state(Gst.State.PLAYING)

def video_stop():
    print('video_stop')
    pipeline.set_state(Gst.State.NULL)


def round8(x):
    return int(x)>>3<<3

def on_counter():
    global maxtime, start
    da.queue_draw()
    if start + maxtime + timegap > time.time():
        return True
    else:
        start = 0

def on_start():
    video_rotate()
    video_start()


def on_stop():
    video_stop()



def on_click(w=None,e=None):
    global start, stop_timer
    x = (time.time() - start)
    if x < 0:
        pass
    elif x < maxtime:
        GLib.source_remove(stop_timer)
        GLib.timeout_add(timegap * 1000, on_stop)
        start = time.time()-maxtime
    elif x < maxtime + timegap:
        pass
    else:
        GLib.timeout_add(100, on_counter)
        start = time.time() + timegap
        GLib.idle_add(on_start)
        stop_timer = GLib.timeout_add( (maxtime + timegap*2) * 1000, on_stop)



def draw_clock(w, c, x):
    s = w.get_allocation()
    font = Pango.FontDescription()
    font.set_family('Noto Sans Mono')
    font.set_size( 200 * Pango.SCALE )
    mn = int(x // 60)
    sc = int(x % 60 // 1)
    
    blink = int(x*2 % 2)
    sep = ":" if blink else " "
    layout = w.create_pango_layout(f"{mn:02d}{sep}{sc:02d}")
    layout.set_font_description(font)
    clock_width, clock_height = layout.get_pixel_size()
    
    clock_x = s.width/2 - clock_width/2
    
    c.move_to(clock_x, s.height/2 - clock_height/2)
    PangoCairo.show_layout(c,layout)
    c.stroke()

    font = Pango.FontDescription()
    font.set_family('Noto Sans Mono')
    font.set_size(64 * Pango.SCALE)
    layout = w.create_pango_layout("Идёт  запись".upper())
    layout.set_font_description(font)
    width, height = layout.get_pixel_size()
    c.move_to(clock_x + clock_width - width - 20 , 20)
    PangoCairo.show_layout(c, layout)
    c.stroke()

    font = Pango.FontDescription()
    font.set_family("Noto Sans")
    font.set_size(32 * Pango.SCALE)
    layout = w.create_pango_layout("Для окончания записи нажмите кнопку")
    layout.set_font_description(font)
    width, height = layout.get_pixel_size()
    c.move_to( s.width/2 - width/2, s.height - height - 35)
    PangoCairo.show_layout(c, layout)
    c.stroke()

    if blink:
        c.set_source_rgb(1, 0, 0)
        c.arc(clock_x+60,75,38,0,7)
        c.move_to(clock_x+50,50)
        c.fill()
        c.stroke()


def draw_countdown(w, c, x):
    s = w.get_allocation()        
    font = Pango.FontDescription()
    font.set_family('Noto Sans Mono')
    font.set_size(300 *Pango.SCALE)
    layout = w.create_pango_layout(str(round(-x)));
    layout.set_font_description(font)
    width,height = layout.get_pixel_size()
    c.move_to(s.width/2 - width/2, s.height/2 - height/2)
    PangoCairo.show_layout(c,layout)
    c.stroke()
    
    n = round(((-x)%1)*4)
    gap = 0.07
    c.set_line_width(20)
    
    if n < 4:
        c.arc(s.width/2, s.height/2, 250, -math.pi/2 +gap, -gap)
        c.stroke()
    if n <= 3:
        c.arc(s.width/2, s.height/2, 250, +gap, -gap + math.pi/2)
        c.stroke()
    if n <= 2:
        c.arc(s.width/2, s.height/2, 250, +gap + math.pi/2, -gap + math.pi)
        c.stroke()
    if n <= 1:
        c.arc(s.width/2, s.height/2, 250, +gap + math.pi, -gap + math.pi*1.5)
        c.stroke()
      
def draw_text(w,c,x, text):
    s = w.get_allocation()      
    font = Pango.FontDescription()
    font.set_family("Noto Sans")
    font.set_size(100*Pango.SCALE)
    
    layout = w.create_pango_layout();
    layout.set_markup(text)
    layout.set_alignment(Pango.Alignment.CENTER)
    layout.set_font_description(font)
    width,height = layout.get_pixel_size()
    c.move_to(s.width/2 - width/2, s.height/2 - height/2)
    PangoCairo.show_layout(c, layout)
    c.stroke()

def draw_hello(w,c,x):
    return draw_text(w,c,x, "Для записи\nнажмите\nкнопку снизу")

def draw_bye(w,c,x):
    return draw_text(w,c,x, "До свидания!")

def on_draw(w,c,data=None):
    global start
    c.set_source_rgb(1, 1, 1)
    c.paint()
    c.set_source_rgb(0, 0, 0)
    x= ( time.time() - start )
    if x < 0:
        sofit.set(settings['sofit']['action'])
        draw_countdown(w,c,x)
    elif x < maxtime:
        draw_clock(w,c, maxtime - x)
        sofit.set(settings['sofit']['action'])
    elif x < maxtime + timegap:
        sofit.set(settings['sofit']['wait'])
        draw_bye(w,c,x)
    else:
        sofit.set(settings['sofit']['wait'])
        draw_hello(w,c,x)


#sofit = PWMLED(pin=18, frequency=1000, pin_factory=RPIOFactory())

class SYSPWM():
    def __init__(self, chip=0, out=0, freq=400, value=0):
        self.chip = chip
        self.out = out
        self.freq = freq
        self.value = value
        self.period = period = 10**9/freq
        open(f'/sys/class/pwm/pwmchip{chip}/export', 'w').write(f'{out}')
        time.sleep(1)
        open(f'/sys/class/pwm/pwmchip{chip}/pwm{out}/period', 'w').write(f'{period:.0f}')
        open(f'/sys/class/pwm/pwmchip{chip}/pwm{out}/enable', 'w').write(f'1')
        self.set(value)

    def set(self, value):
        print('sofit', repr(value))
        if self.value == value:
            return
        self.value = value
        duty_cycle = value * self.period
        print(f'{duty_cycle:.0f}')
        open(f'/sys/class/pwm/pwmchip{self.chip}/pwm{self.out}/duty_cycle', 'w').write(f'{duty_cycle:.0f}')



import threading
import fcntl
from select import poll
import select
import os

class Button(threading.Thread):
    def __init__(self, pin=4):
        super().__init__()
        self.pin = pin
        open(f'/sys/class/gpio/export', 'w').write(f'{pin}')
        time.sleep(1)
        open(f'/sys/class/gpio/gpio{pin}/direction', 'w').write(f'in')
        open(f'/sys/class/gpio/gpio{pin}/edge','w').write(f'rising') # both, falling , rising
        time.sleep(1)
        self.value = int(open(f'/sys/class/gpio/gpio{self.pin}/value','r').read())


    def up(self):
        print('UP')
        on_click()


    def run(self):
        with open(f'/sys/class/gpio/gpio{self.pin}/value','r') as pinf:
            fd = pinf.fileno()
            flag = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
            poller = poll()
            poller.register(fd, select.POLLPRI)
            pinf.seek(0)
            while True:
                ev = poller.poll()
                print(ev)
                if ev:
                    pinf.seek(0)
                    data = int(pinf.read())
                    if data > self.value:
                        self.up()
                    if data != self.value:
                        self.value = data
                    print(data, self.value, time.time())





def load_settings():
    global settings
    import toml
    settings = toml.load('settings.ini')
    maxtime = settings['timer']['max']
    timegap = settings['timer']['gap']



load_settings()

sofit = SYSPWM()
sofit.set(settings['sofit']['wait'])


start_button = Button(4)
start_button.start()

da = Gtk.DrawingArea()
da.connect('draw', on_draw)

eventbox = Gtk.EventBox()
eventbox.connect('button-press-event', on_click)
eventbox.add(da)
win.add(eventbox)
win.set_default_size(1024,600)
win.fullscreen()
win.show_all()
try:
    Gtk.main()
finally:
    fcntl.lockf(pf, fcntl.LOCK_UN)

sofit.set(0)
