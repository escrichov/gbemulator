import pyglet
from pyglet.window import key
from pyglet.gl import *
from random import randint


class Mapping():
    data = []

    def __init__(self, img):
        self.image = img
        self.width = self.image.width
        self.height = self.image.height
        self.data = self.image.get_data('RGBA', self.width * 4)
        self.data = bytearray(self.data)

    def get_position(self, x, y):
        y = self.height - 1 - y # Convert to top
        return (x * 4 + self.width * 4 * y)

    def get_pixel(self, x, y):
        position = self.get_position(x, y)
        pixel = (self.data[position], self.data[position+1],
                 self.data[position+2], self.data[position+3])
        return pixel

    def set_pixel(self, x, y, pixel):
        position = self.get_position(x, y)
        self.data[position] = pixel[0]
        self.data[position+1] = pixel[1]
        self.data[position+2] = pixel[2]
        self.data[position+3] = pixel[3]

    def fill(self, pixel):
        self.data = pixel * self.width * self.height

    def fill_column(self, x, pixel):
        for j in range(self.height):
            self.set_pixel(x, j, pixel)

    def fill_row(self, y, pixel):
        for i in range(self.width):
            self.set_pixel(i, y, pixel)

    def draw(self):
        self.image.set_data('RGBA', self.width * 4, bytes(self.data))


WIDTH = 160
HEIGHT = 144
FPS = 60
window = pyglet.window.Window(width=WIDTH, height=HEIGHT, style=pyglet.window.Window.WINDOW_STYLE_DIALOG)
window.set_visible()
window.set_caption("Gameboy")
image = pyglet.image.SolidColorImagePattern((255,255,255,255)).create_image(WIDTH, HEIGHT)
mapping = Mapping(image)


@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.Z:
        print('The "A" key was pressed.')
    if symbol == key.X:
        print('The "B" key was pressed.')
    elif symbol == key.LEFT:
        print('The left arrow key was pressed.')
    elif symbol == key.RIGHT:
        print('The right arrow key was pressed.')
    elif symbol == key.UP:
        print('The up arrow key was pressed.')
    elif symbol == key.DOWN:
        print('The down arrow key was pressed.')
    elif symbol == key.ENTER:
        print('The enter key was pressed.')
    elif symbol == key.BACKSPACE:
        print('The select key was pressed.')


@window.event
def on_draw():
    window.clear()
    image.blit(0, 0)


def callback(dt):
    pixel = (randint(0, 255), randint(0, 255), randint(0, 255), 0)
    mapping.fill(pixel)
    mapping.draw()
    print('%f seconds since last callback' % dt)


pyglet.clock.schedule_interval(callback, 1.0/FPS)
pyglet.app.run()
