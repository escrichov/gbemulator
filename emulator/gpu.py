from random import randint
from emulator.graphics import Pixel
from emulator import utils

# 160x144 LCD
# 4 shades of gray
# 8x8 pixel tile-based, 20x18 tiles
# 40 sprites (10 per line)
# 8 KB VRAM

# Total 256 tiles in the system for background
# 20x18 background tiles visible
# Each tile is 8x8 pixels = 2bit*8x8 = Total 16 bytes per tile
# Each pixel has 2 bit for color
# In video ram are 32x32 background tiles
# FF42 SCY Scroll Y (R/W)
# FF43 SCX Scroll X (R/W)

# Background palettes
# 0xFF47    BGP     BG Palette (R/W)
#    6-7            Color for 11
#    4-5            Color for 10
#    2-3            Color for 01
#    0-1            Color for 00

# Window
# FF40 LCDC LCD Control (R/W)
# 7         LCD Display Enable
# 5         Window Enable
# 1         OBJ Enable
# 0         Background Enable
# FF4A WY   Window Y Position (R/W)
# FF4B WX   Window X Position (R/W)

# VRAM Memory Map
# 6         Window Tile Map Address
# 4         BG & Window Tile Data Address
# 3         BG Tile Map Address
# FF4A WY   Window Y Position (R/W)
# FF4B WX   Window X Position (R/W)
# 1KB Window Map    32 x 32 indexes
# 1KB BG Map        32 x 32 indexes
# 4KB BG Tiles      256 tiles x 16 bytes
# 4KB Sprite Tiles  256 tiles x 16 bytes

# FF41  STAT    LCDC Status (R/W)
#    6          LYC=LY Interrupt
#    2          LYC=LY Flag
# FF44  LY      LCDC Y-Coordinate (R)
# FF45  LYC     LY Compare (R/W)

# Horizontal Timing
# 1 line = OAM Search (20 Clocks) + Pixel Transfer (43 Clocks) + HBlank (51 Clocks)
# 1 line = 20 + 43 + 51 = 114 Clocks
# Screen = 114 clocks * (144 lines + VBlank(10 lines)) = 17556 clocks
# 1Mhz / 17556 clocks = 59.7 Hz refres rate
# FF41  STAT    LCDC Status (R/W)
#    5          Mode 2 OAM Interrupt
#    4          Mode 1 V-Blank Interrupts
#    3          Mode 0 H-Blank Interrupt
#  1-0          Mode (00: HBlank, 01: VBlank, 10: OAM, 11: Pixel Transfer)
# FF0F  IF      Interrupt Flag (R/W)
#    0          V-Blank
# FFFF  IE      Interrupt Enable (R/W)
#    0          V-Blank
class GPU():

    PIXEL_FIFO = []
    TILE_SET = []
    BG_PALETTE = []
    SCRN = []

    lcd_display_enabled = 0
    window_enabled = 0
    obj_enabled = 0
    bg_enabled = 0
    bg_map = 0
    bg_tile = 0
    scy = 0
    scx = 0

    MODE_HBLANK = 0
    MODE_VBLANK = 1
    MODE_OAM = 2
    MODE_PIXEL_TRANSFER = 3
    mode = MODE_OAM

    modeclock = 0
    MODE_TIMES = {
        MODE_HBLANK: 20,
        MODE_VBLANK: 114,
        MODE_OAM: 80,
        MODE_PIXEL_TRANSFER: 43
    }

    line = 0
    frame_number = 0

    def __init__(self, cpu, window):
        self.cpu = cpu
        self.window = window
        self.reset()

    def reset(self):
        self.lcd_display_enabled = 0
        self.window_enabled = 0
        self.obj_enabled = 0
        self.bg_enabled = 0
        self.mode = self.MODE_OAM
        self.bg_map = 0
        self.bg_tile = 0
        self.scy = 0
        self.scx = 0
        self.line = 0
        self.TILE_SET = [[[0,0,0,0,0,0,0,0] for x in range(8)] for y in range(384)] # 384 x (8x8)
        self.BG_PALETTE = [Pixel(255, 255, 255, 0) for _ in range(0, 4)]
        self.PIXEL_FIFO = []
        self.SCRN = [255] * 4 * 160 * 144

    def get_tile_from_addr(self, addr):
        tile = (addr >> 4) & 0x1FF
        return tile

    def get_row_from_addr(self, addr):
        row = (addr >> 1) & 0x07
        return row

    def wb(self, addr, value):
        if addr == 0xFF40:  # LCD Control
            self.bg_enabled = utils.get_bit(value, 0)
            self.bg_map = utils.get_bit(value, 3)
            self.bg_tile = utils.get_bit(value, 4)
            self.lcd_display_enabled = utils.get_bit(value, 7)
            print("BG Enabled", self.bg_enabled)
        elif addr == 0xFF42: # Scroll Y
            self.scy = value
        elif addr == 0xFF43: # Scroll X
            self.scx = value
        elif addr == 0xFF47: # Background palette mapping
            for i in range(0, 4):
                # Background palettes
                # 0xFF47    BGP     BG Palette (R/W)
                #    6-7            Color for 11
                #    4-5            Color for 10
                #    2-3            Color for 01
                #    0-1            Color for 00
                colour = (value >> (i * 2)) & 0x3
                #print(colour)
                if colour == 0:
                    self.BG_PALETTE[i] = Pixel(255, 255, 255, 0)
                elif colour == 1:
                    self.BG_PALETTE[i] = Pixel(192, 192, 192, 0)
                elif colour == 2:
                    self.BG_PALETTE[i] = Pixel(96, 96, 96, 0)
                elif colour == 3:
                    self.BG_PALETTE[i] = Pixel(0, 0, 0, 0)

    def rb(self, addr):
        if addr == 0xFF40:  # LCD Control
            value = 0x00
            value = utils.set_bit(value, 0, self.bg_enabled)
            value = utils.set_bit(value, 3, self.bg_map)
            value = utils.set_bit(value, 4, self.bg_tile)
            value = utils.set_bit(value, 7, self.lcd_display_enabled)
            return value
        elif addr == 0xFF42: # Scroll Y
            return self.scy
        elif addr == 0xFF43: # Scroll X
            return self.scx
        elif addr == 0xFF44: # Current line
            return self.line

    # addr is base address of VRAM
    def update_tile(self, addr, value):
        if addr > 0x97FF:
            return
        # Work out which tile and row was updated
        base_addr = addr & 0x1FFE
        tile = self.get_tile_from_addr(base_addr)
        row = self.get_row_from_addr(base_addr)

        for x in range(0, 8):
            # Find bit index for this pixel
            sx = 7-x

            if utils.get_bit(self.cpu.MMU.vram[base_addr], sx):
                value_a = 1
            else:
                value_a = 0

            if utils.get_bit(self.cpu.MMU.vram[base_addr+1], sx):
                value_b = 2
            else:
                value_b = 0

            # Update tile set
            self.TILE_SET[tile][row][x] = value_a + value_b

    # Fetch
    # 3 clocks to fetch 8 pixels
    # Pauses in 4th clock unless space in FIFO
    def fetcher(self):
        pass

    # FIFO
    # pushes one pixel per clock at 4MHz
    # pauses unless it contains more than 8 pixels
    # FIFO  FETCHER
    # push
    # push  Read Tile #
    # push
    # push  Read Data 0
    # push
    # push  Read Data 1
    # push
    # push  Idle
    # 4MHz  2Mhz
    # Horizonal Scrolling = Discard pixels FF43 SCX
    # Pixel information is 2 bits for combination and Palette
    def pixel_fifo(self):
        pass

    # From all sprites put sprites visible in that lines
    # Logic:
    # oam.x != 0
    # LY + 16 >= oam.y
    # LY + 16 < oam.y + h
    # 20 cycles
    # Bug here:
    # It you do any 16 bit calculation with number in OAM RAM
    # in the range FE00 <= r16 <= FEFF it will destroy RAM during OAM search
    # VRAM Access is OK
    # OAM Access is BAD
    def oam_search(self):
        pass

    # VRAM Access is BAD
    # OAM Access is BAD
    # 43 cycles
    def pixel_transfer(self):
	    # VRAM offset for the tile map
        # Tile map 0 or 1
        if self.bg_map:
            mapoffs = 0x9C00
        else:
            mapoffs = 0x9800

	    # Which line of tiles to use in the map
        #mapoffs += ((self.line + self.scy) & 0xFF) >> 3
        mapoffs += (self.line // 8) * 0x20

        # Which tile to start with in the map line
        #lineoffs = (self.scx >> 3)
        lineoffs = 0x00

        # Which line of pixels to use in the tiles
        #y = (self.line + self.scy) & 7
        y = self.line % 8

        # Where in the tileline to start
        #x = self.scx & 7
        x = 0

        # Read tile index from the background map
        base_addr = (mapoffs + lineoffs)
        addr = (mapoffs + lineoffs) & 0x1FFE
        tile = self.cpu.MMU.vram[addr]

        # If the tile data set in use is #1, the
        # indices are signed; calculate a real tile offset
        #if self.bg_tile == 1 and tile < 128:
        #    tile += 256

        for i in range(0, 160):
            # Re-map the tile pixel through the palette
            colour = self.BG_PALETTE[self.TILE_SET[tile][y][x]]

            # Plot the pixel to canvas
            #print(tile, y, x, colour)
            #print("Canvas", hex(base_addr), tile, i, self.line, x, y)
            self.window.frame.set_pixel(i, self.line, colour)

            # When this tile ends, read another
            x += 1
            if x == 8:
                x = 0
                lineoffs = (lineoffs + 1) & 0x1F
                base_addr = (mapoffs + lineoffs)
                addr = (mapoffs + lineoffs) & 0x1FFE
                tile = self.cpu.MMU.vram[addr]
                #if self.bg_tile == 1 and tile < 128:
                #    tile += 256

    # VRAM Access is OK
    # OAM Access is OK
    # 51 cycles
    def hblank(self):
        pass

    # VRAM Access is OK
    # OAM Access is OK
    # 10 lines * 114 cycles each line = 1140 cycles
    # Normally here you should move new columns into the background map
    def vblank(self):
        pass

    def is_in_mode(self, mode):
        if self.mode == mode and self.modeclock >= self.MODE_TIMES[mode]:
            return True
        else:
            return False

    def write_canvas(self):
        #self.write_background_tiles(26)
        #self.write_tile_map()
        self.window.frame.sync()

    def write_tile_map(self):
        init_address = 0x9800
        addr = 0x9800
        for x in range(8, 10):
            for y in range(0, 20):
                x_frame_begin = y * 8
                y_frame_begin = x * 8
                base_addr = init_address + (0x20 * x) + y
                addr = base_addr & 0x1FFE
                tile_number = self.cpu.MMU.vram[addr]
                self.write_tile(tile_number, x_frame_begin, y_frame_begin)

    def write_tile(self, tile_number, x_screen, y_screen):
        tile = self.TILE_SET[tile_number]
        for x in range(0, 8):
            for y in range(0, 8):
                colour = self.BG_PALETTE[tile[y][x]]
                self.window.frame.set_pixel(x+x_screen, y+y_screen, colour)

    def write_background_tiles(self, max_number):
        for i in range(0, max_number):
            x_frame_begin = (i * 8) % 160
            y_frame_begin = ((i * 8) // 160) * 8
            self.write_tile(i, x_frame_begin, y_frame_begin)

    def ppu_step(self):
        self.modeclock += self.cpu.clock['M']

        if self.is_in_mode(self.MODE_OAM):
            self.modeclock = 0
            self.mode = self.MODE_PIXEL_TRANSFER
            self.oam_search()
        elif self.is_in_mode(self.MODE_PIXEL_TRANSFER):
            self.modeclock = 0
            self.mode = self.MODE_HBLANK
            # Write a scanline to the framebuffer
            self.pixel_transfer()
        elif self.is_in_mode(self.MODE_HBLANK):
            self.modeclock = 0
            self.line += 1
            if self.line == 143: # Enter VBlank
                self.mode = self.MODE_VBLANK
                # Push the screen data to canvas
                self.write_canvas()
            else: # Go to next line
                self.mode = self.MODE_OAM
        elif self.is_in_mode(self.MODE_VBLANK): # 10 lines
            self.modeclock = 0
            self.line += 1
            self.vblank()

            # Restart scanning modes
            if self.line == 153:
                self.mode = self.MODE_OAM
                self.line = 0
                self.frame_number += 1

        return self.frame_number
