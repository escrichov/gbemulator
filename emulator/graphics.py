import pyglet
from pyglet.window import key
from pyglet.gl import *


class Pixel():
    def __init__(self, r, g, b, a):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __str__(self):
        return "{}, {}, {}, {}".format(self.r, self.g, self.b, self.a)

    def __repr__(self):
        return self.__str__()

    def to_list(self):
        return [self.r, self.g, self.b, self.a]

class Frame():
    data = []

    def __init__(self, width, height):
        self.image = pyglet.image.SolidColorImagePattern((255,255,255,255)).create_image(width, height)
        self.width = self.image.width
        self.height = self.image.height
        self.data = self.image.get_data('RGBA', self.width * 4)
        self.data = bytearray(self.data)

    def get_position(self, x, y):
        y = self.height - 1 - y # Convert to top
        return (x * 4 + self.width * 4 * y)

    def get_pixel(self, x, y):
        position = self.get_position(x, y)
        pixel = Pixel(self.data[position], self.data[position+1], self.data[position]+2, self.data[position+3])
        return pixel

    def set_pixel(self, x, y, pixel):
        position = self.get_position(x, y)
        self.data[position] = pixel.r
        self.data[position+1] = pixel.g
        self.data[position+2] = pixel.b
        self.data[position+3] = pixel.a

    def fill(self, pixel):
        self.data = pixel.to_list() * self.width * self.height

    def fill_column(self, x, pixel):
        for j in range(self.height):
            self.set_pixel(x, j, pixel)

    def fill_row(self, y, pixel):
        for i in range(self.width):
            self.set_pixel(i, y, pixel)

    def sync(self):
        self.image.set_data('RGBA', self.width * 4, bytes(self.data))

    def draw(self):
        self.image.blit(0, 0)


class Window(pyglet.window.Window):
    def __init__(self, caption_text):
        width = 160
        height = 140
        super(Window, self).__init__(width=width, height=height, style=pyglet.window.Window.WINDOW_STYLE_DIALOG, vsync=False)
        self.set_visible()
        self.set_caption(caption_text)
        self.fps_display = pyglet.clock.ClockDisplay()
        self.label = pyglet.text.Label('Hello, world!')
        self.frame = Frame(width, height)

    def on_draw(self):
        self.clear()
        self.label.draw()
        self.frame.draw()
        self.fps_display.draw()

    def on_key_press(self, symbol, modifiers):
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
