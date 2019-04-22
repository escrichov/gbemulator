import pyglet
from emulator.cpu import Z80

cpu = Z80()
cpu.load_rom("roms/tetris.gb")
cpu.reset()

window = pyglet.window.Window()
label = pyglet.text.Label('Gameboy',
                          font_name='Times New Roman',
                          font_size=36,
                          x=window.width//2, y=window.height//2,
                          anchor_x='center', anchor_y='center')

breakpoints = [0x0C, 0x0F]

@window.event
def on_draw():
    window.clear()
    label.draw()

@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.Z:
        try:
            cpu.dispatcher()
            while cpu.registers["PC"] not in breakpoints:
                cpu.dispatcher()
            label.text = f'Op: {str(hex(cpu.current_op))} {cpu.current_op_name} PC: {hex(cpu.registers["PC"])}'
        except:
            label.text = f'Error. Op: {str(hex(cpu.current_op))} {cpu.current_op_name} PC: {hex(cpu.registers["PC"])}'

pyglet.app.run()

