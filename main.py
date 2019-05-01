from emulator.cpu import Z80
import pyglet
import sys

FPS = 60

if __name__ == '__main__':
    cpu = Z80()
    cpu.load_rom("roms/tetris.gb")
    cpu.reset()

    def worker(dt):
        i = 0
        initial_frame_number = cpu.GPU.frame_number
        if initial_frame_number <= 120000:
            frame_number = initial_frame_number
            while frame_number == initial_frame_number:
                current_pc, op, frame_number = cpu.dispatcher()
                #print('Frame {}, i={}. PC={}, OP={}'.format(initial_frame_number, i, hex(current_pc), hex(op)))
                i += 1

    pyglet.clock.schedule_interval(worker, 1.0/FPS)
    pyglet.app.run()
