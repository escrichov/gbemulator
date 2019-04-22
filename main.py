from emulator.cpu import Z80

if __name__ == '__main__':
    cpu = Z80()
    cpu.load_rom("roms/DMG_ROM.bin")
    cpu.load_rom("roms/tetris.gb")
    cpu.reset()
    cpu.dispatcher()
