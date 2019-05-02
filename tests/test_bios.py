import unittest
from emulator import utils
from emulator.cpu import Z80


class TestBIOS(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.cpu = Z80(headless=True)
        self.cpu.load_rom("roms/bgbtest.gb")

    def test_bios(self):
        ops = []
        i=0
        while i < len(self.cpu.MMU.bios):
            if self.cpu.MMU.bios[i] == 0xCB:
                op = hex((self.cpu.MMU.bios[i]<<8)+self.cpu.MMU.bios[i+1])
                ops.append(op)
                i+=1
            else:
                ops.append(hex(self.cpu.MMU.bios[i]))
            i+=1

        clock_m = 0
        ops = sorted(list(set(ops)))
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x31) # LD, SP 0xFFFE

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m*4)
        self.assertEqual(self.cpu.registers['PC'], 0x3)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xAF) # XORA

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['F'], 0x80)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m*4)
        self.assertEqual(self.cpu.registers['PC'], 0x4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x21) # LD HL,0x9FFFF

        self.cpu.dispatcher()
        self.assertEqual(self.cpu.registers['F'], 0x80)

        clock_m += 3
        addr = 0x9FFF
        while (self.cpu.registers['H'] << 8) + self.cpu.registers['L'] >= 0x8000:
            self.assertEqual(self.cpu.registers['H'], addr >> 8)
            self.assertEqual(self.cpu.registers['L'], addr & 255)
            self.assertEqual(self.cpu.registers['PC'], 0x7)
            self.assertEqual(self.cpu.clock['M'], clock_m)
            self.assertEqual(self.cpu.clock['T'], clock_m*4)
            self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x32) # LD (HL-),A

            self.cpu.dispatcher()

            self.assertEqual(self.cpu.MMU.rb(addr), 0x0)
            addr -= 1
            clock_m += 2
            self.assertEqual(self.cpu.registers['H'], addr >> 8)
            self.assertEqual(self.cpu.registers['L'], addr & 255)
            self.assertEqual(self.cpu.registers['PC'], 0x8)
            self.assertEqual(self.cpu.clock['M'], clock_m)
            self.assertEqual(self.cpu.clock['T'], clock_m*4)
            self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCB) # BIT 7,H
            self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']+1), 0x7C) # BIT 7,H

            self.cpu.dispatcher()

            clock_m += 2
            if addr == 0x7FFF:
                self.assertEqual(self.cpu.registers['F'], 0xA0)
            else:
                self.assertEqual(self.cpu.registers['F'], 0x20)
            self.assertEqual(self.cpu.registers['PC'], 0xA)
            self.assertEqual(self.cpu.clock['M'], clock_m)
            self.assertEqual(self.cpu.clock['T'], clock_m * 4)
            self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ, Addr_0007

            self.cpu.dispatcher()

            if addr != 0x7FFF:
                clock_m += 3
            else:
                clock_m += 2

        self.assertEqual(self.cpu.registers['H'], 0x7F)
        self.assertEqual(self.cpu.registers['L'], 0xFF)
        self.assertEqual(self.cpu.registers['PC'], 0xC)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m*4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x21) # LD HL,0xff26

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['F'], 0xA0)
        self.assertEqual(self.cpu.registers['PC'], 0xF)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m*4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xE) # LD C,0x11

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['F'], 0xA0)
        self.assertEqual(self.cpu.registers['PC'], 0x11)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m*4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x3E) # LD A,0x80

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['F'], 0xA0)
        self.assertEqual(self.cpu.registers['PC'], 0x13)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m*4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x32) # LD (HL-),A

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['F'], 0xA0)
        self.assertEqual(self.cpu.registers['PC'], 0x14)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m*4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xE2) # LD (0xFF00+C),A

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['F'], 0xA0)
        self.assertEqual(self.cpu.registers['PC'], 0x15)
        self.assertEqual(self.cpu.registers['C'], 0x11)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x0C) # INC C

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['C'], 0x12)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['PC'], 0x16)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x3E) # LD A,0xf3

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['PC'], 0x18)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xE2) # LD (0xFF00+C),A

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['PC'], 0x19)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x32) # LD (HL-),A

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['PC'], 0x1A)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x3E) # LD A,0x77

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['PC'], 0x1C)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x77) # LD (HL),A

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['PC'], 0x1D)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x3E) # LD A,0xfc

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0xFC)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x12)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0x00)
        self.assertEqual(self.cpu.registers['H'], 0xFF)
        self.assertEqual(self.cpu.registers['L'], 0x24)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x1F)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xE0) # LD ($FF00+$47),A

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0xFC)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x12)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0x00)
        self.assertEqual(self.cpu.registers['H'], 0xFF)
        self.assertEqual(self.cpu.registers['L'], 0x24)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x21)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x11) # LD DE,$0104

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0xFC)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x12)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0xFF)
        self.assertEqual(self.cpu.registers['L'], 0x24)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x24)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x21) # LD HL,$8010

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0xFC)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x12)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x27)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x1A) # LD A,(DE)

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0xCE)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x12)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x28)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCD) # CALL 0x0095

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0xCE)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x12)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0x95)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x4F) # LD C,A

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0xCE)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xCE)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0x96)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x06) # LD B,$04

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0xCE)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0xCE)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0x98)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xC5) # PUSH BC

        self.cpu.dispatcher()

        clock_m += 4
        self.assertEqual(self.cpu.registers['A'], 0xCE)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0xCE)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFA)
        self.assertEqual(self.cpu.registers['PC'], 0x99)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCB) # RL C
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']+1), 0x11) # RL C

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0xCE)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x9C)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x10)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFA)
        self.assertEqual(self.cpu.registers['PC'], 0x9B)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x17) # RLA

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x9D)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x9C)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x10)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFA)
        self.assertEqual(self.cpu.registers['PC'], 0x9C)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xC1) # POP BC

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0x9D)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0xCE)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x10)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0x9D)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCB) # RL C
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']+1), 0x11)

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x9D)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x9D)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x10)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0x9F)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x17) # RLA

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x3B)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x9D)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x10)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0xA0)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x05) # DEC B

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x3B)
        self.assertEqual(self.cpu.registers['B'], 0x03)
        self.assertEqual(self.cpu.registers['C'], 0x9D)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0xA1)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ

        while self.cpu.registers['PC'] != 0xA3:
            self.cpu.dispatcher()

        clock_m += 53
        self.assertEqual(self.cpu.registers['A'], 0xF0)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xEB)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x10)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0xA3)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x22) # LDI (HL), A

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0xF0)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xEB)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x11)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0xA4)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x23) # INC HL

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0xF0)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xEB)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x12)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0xA5)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x22) # LDI (HL), A

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0xF0)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xEB)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x13)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0xA6)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x23) # INC HL

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0xF0)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xEB)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x14)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0xA7)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xC9) # RET

        self.cpu.dispatcher()

        clock_m += 4
        self.assertEqual(self.cpu.registers['A'], 0xF0)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xEB)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x14)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x2B)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCD) # CALL 0096

        while self.cpu.registers['PC'] != 0x2E:
            self.cpu.dispatcher()

        clock_m += 84
        self.assertEqual(self.cpu.registers['A'], 0xFC)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xBC)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x04)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x18)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x2E)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x13) # INC DE

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0xFC)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xBC)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x05)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x18)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x2F)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x7B) # LD A,E

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x05)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xBC)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x05)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x18)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x30)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xFE) # CP A, 0x34

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x05)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xBC)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x05)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x18)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0x05)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xBC)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x05)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x18)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x27)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x1A) # LD A, (DE)

        while self.cpu.registers['PC'] != 0x32:
            self.cpu.dispatcher()

        clock_m += 176
        self.assertEqual(self.cpu.registers['A'], 0x06)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xEE)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x06)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x20)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()

        while self.cpu.registers['PC'] != 0x32:
            self.cpu.dispatcher()

        clock_m += 179
        self.assertEqual(self.cpu.registers['A'], 0x07)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x56)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x07)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x28)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()

        while self.cpu.registers['PC'] != 0x32:
            self.cpu.dispatcher()

        clock_m += 179
        self.assertEqual(self.cpu.registers['A'], 0x08)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x56)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x08)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x30)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()

        while self.cpu.registers['PC'] != 0x32:
            self.cpu.dispatcher()

        clock_m += 179
        self.assertEqual(self.cpu.registers['A'], 0x09)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0xAC)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x09)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x38)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x32:
            self.cpu.dispatcher()

        clock_m += 179
        self.assertEqual(self.cpu.registers['A'], 0x0A)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x20)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0x0A)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x20)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x27)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x1A) # LD A, (DE)

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x20)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x28)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCD) # CALL 0095

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x20)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0x95)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x4F) # LD C,A

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0x96)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x06) # LD B,4

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0x98)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xC5) # PUSH BC

        self.cpu.dispatcher()

        clock_m += 4
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFA)
        self.assertEqual(self.cpu.registers['PC'], 0x99)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCB) # RL, C
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']+1), 0x11) # RL, C

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x01)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFA)
        self.assertEqual(self.cpu.registers['PC'], 0x9B)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x17) # RLA

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x01)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFA)
        self.assertEqual(self.cpu.registers['PC'], 0x9C)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xC1) # POP BC

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0x9D)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCB) # RL, C
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']+1), 0x11) # RL, C

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x80)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0x9F)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x17) # RLA

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x40)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFC)
        self.assertEqual(self.cpu.registers['PC'], 0xA0)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x05) # DEC, B

        while self.cpu.registers['PC'] != 0x2B:
             self.cpu.dispatcher()

        clock_m += 66
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x44)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x2B)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCD) # CALL 0096

        while self.cpu.registers['PC'] != 0x2E:
             self.cpu.dispatcher()

        clock_m += 84
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0A)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x48)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x2E)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x13) # INC DE

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0B)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x48)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x2F)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x7B) # LD A, E

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x0B)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0B)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x48)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x30)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xFE) # CP A,34

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x0B)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0B)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x48)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x32:
            self.cpu.dispatcher()

        clock_m += 179
        self.assertEqual(self.cpu.registers['A'], 0x0C)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x30)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0C)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x50)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x32:
            self.cpu.dispatcher()

        clock_m += 179
        self.assertEqual(self.cpu.registers['A'], 0x0D)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x10)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0D)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x58)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x32:
            self.cpu.dispatcher()

        clock_m += 179
        self.assertEqual(self.cpu.registers['A'], 0x0E)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x57)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0E)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x60)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x32:
            self.cpu.dispatcher()

        clock_m += 179
        self.assertEqual(self.cpu.registers['A'], 0x0F)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x0F)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x68)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x32 or self.cpu.registers['A'] != 0x10:
            self.cpu.dispatcher()

        clock_m += 179
        self.assertEqual(self.cpu.registers['A'], 0x10)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x98)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x10)
        self.assertEqual(self.cpu.registers['H'], 0x80)
        self.assertEqual(self.cpu.registers['L'], 0x70)
        self.assertEqual(self.cpu.registers['F'], 0x70)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # LD A, 19

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x32 or self.cpu.registers['A'] != 0x33:
            self.cpu.dispatcher()

        clock_m += 6265
        self.assertEqual(self.cpu.registers['A'], 0x33)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x53)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x33)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x88)
        self.assertEqual(self.cpu.registers['F'], 0x70)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x32 or self.cpu.registers['A'] != 0x34:
            self.cpu.dispatcher()

        clock_m += 179
        self.assertEqual(self.cpu.registers['A'], 0x34)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x34)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x90)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x32)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x34)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x01)
        self.assertEqual(self.cpu.registers['E'], 0x34)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x90)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x34)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x11) # LD DE,00D8

        while self.cpu.registers['PC'] != 0x3D:
            self.cpu.dispatcher()

        clock_m += 13
        self.assertEqual(self.cpu.registers['A'], 0x3C)
        self.assertEqual(self.cpu.registers['B'], 0x08)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xD9)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x92)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3D)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x05) # DEC B

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x3C)
        self.assertEqual(self.cpu.registers['B'], 0x07)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xD9)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x92)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3E)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0039

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0x3C)
        self.assertEqual(self.cpu.registers['B'], 0x07)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xD9)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x92)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x39)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x1A) # LD A, (DE)

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x42)
        self.assertEqual(self.cpu.registers['B'], 0x07)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xD9)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x92)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3A)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x13) # INC DE

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x42)
        self.assertEqual(self.cpu.registers['B'], 0x07)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xDA)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x92)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3B)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x22) # LDI (HL), A

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x42)
        self.assertEqual(self.cpu.registers['B'], 0x07)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xDA)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x93)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3C)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x23) # INC HL

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x42)
        self.assertEqual(self.cpu.registers['B'], 0x07)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xDA)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x94)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3D)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x05) # DEC B

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x42)
        self.assertEqual(self.cpu.registers['B'], 0x06)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xDA)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x94)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3E)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0039

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x3E:
            self.cpu.dispatcher()

        clock_m += 12
        self.assertEqual(self.cpu.registers['A'], 0xB9)
        self.assertEqual(self.cpu.registers['B'], 0x05)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xDB)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x96)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3E)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0039

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x3E:
            self.cpu.dispatcher()

        clock_m += 12
        self.assertEqual(self.cpu.registers['A'], 0xA5)
        self.assertEqual(self.cpu.registers['B'], 0x04)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xDC)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x98)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3E)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0039

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x3E:
            self.cpu.dispatcher()

        clock_m += 12
        self.assertEqual(self.cpu.registers['A'], 0xB9)
        self.assertEqual(self.cpu.registers['B'], 0x03)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xDD)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x9A)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3E)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0039

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x3E:
            self.cpu.dispatcher()

        clock_m += 12
        self.assertEqual(self.cpu.registers['A'], 0xA5)
        self.assertEqual(self.cpu.registers['B'], 0x02)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xDE)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x9C)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3E)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0039

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x3E:
            self.cpu.dispatcher()

        clock_m += 12
        self.assertEqual(self.cpu.registers['A'], 0x42)
        self.assertEqual(self.cpu.registers['B'], 0x01)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xDF)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x9E)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3E)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0039

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0x42)
        self.assertEqual(self.cpu.registers['B'], 0x01)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xDF)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x9E)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x39)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x1A) # LD A,(DE)

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x3C)
        self.assertEqual(self.cpu.registers['B'], 0x01)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xDF)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x9E)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3A)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x13) # INC DE

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x3C)
        self.assertEqual(self.cpu.registers['B'], 0x01)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x9E)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3B)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x22) # LDI (HL), A


        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x3C)
        self.assertEqual(self.cpu.registers['B'], 0x01)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0x9F)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3C)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x23) # INC HL

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x3C)
        self.assertEqual(self.cpu.registers['B'], 0x01)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0xA0)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3D)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x05) # DEC B

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['A'], 0x3C)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0xA0)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x3E)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0027

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['A'], 0x3C)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0xA0)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x40)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x3E) # LD A,19

        self.cpu.dispatcher()

        self.assertEqual(self.cpu.registers['A'], 0x19)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0xA0)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x42)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xEA) # LD (0x9910), A

        self.cpu.dispatcher()

        self.assertEqual(self.cpu.MMU.vram[0x9910 & 0x1FFF], 0x19)
        self.assertEqual(self.cpu.registers['A'], 0x19)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x73)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x81)
        self.assertEqual(self.cpu.registers['L'], 0xA0)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x45)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x21) # HL,0x992F

        while self.cpu.registers['PC'] != 0x4D:
            self.cpu.dispatcher()

        self.assertEqual(self.cpu.registers['A'], 0x18)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x0C)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x99)
        self.assertEqual(self.cpu.registers['L'], 0x2F)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x4D)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x32) # LDD (HL), A

        self.cpu.dispatcher()

        self.assertEqual(self.cpu.MMU.rb(0x992F), 0x18)
        self.assertEqual(self.cpu.registers['A'], 0x18)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x0C)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x99)
        self.assertEqual(self.cpu.registers['L'], 0x2E)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x4E)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x0D) # DEC C

        while self.cpu.registers['PC'] != 0x4D:
            self.cpu.dispatcher()

        self.assertEqual(self.cpu.registers['A'], 0x17)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x0B)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x99)
        self.assertEqual(self.cpu.registers['L'], 0x2E)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x4D)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x32) # LDD (HL), A

        self.cpu.dispatcher()

        self.assertEqual(self.cpu.MMU.rb(0x992E), 0x17)
        self.assertEqual(self.cpu.registers['A'], 0x17)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x0B)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x99)
        self.assertEqual(self.cpu.registers['L'], 0x2D)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x4E)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x0D) # DEC C

        while self.cpu.registers['PC'] != 0x4D:
            self.cpu.dispatcher()

        self.assertEqual(self.cpu.registers['A'], 0x16)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x0A)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x99)
        self.assertEqual(self.cpu.registers['L'], 0x2D)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x4D)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x32) # LDD (HL), A

        self.cpu.dispatcher()

        self.assertEqual(self.cpu.MMU.rb(0x992D), 0x16)
        self.assertEqual(self.cpu.registers['A'], 0x16)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x0A)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x99)
        self.assertEqual(self.cpu.registers['L'], 0x2C)
        self.assertEqual(self.cpu.registers['F'], 0x40)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x4E)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x0D) # DEC C

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x51:
            self.cpu.dispatcher()

        clock_m += 118
        self.assertEqual(self.cpu.registers['A'], 0x0D)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x00)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x99)
        self.assertEqual(self.cpu.registers['L'], 0x23)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x51)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x2E) # LD 1,0F

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x55:
            self.cpu.dispatcher()

        clock_m += 125
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x00)
        self.assertEqual(self.cpu.registers['C'], 0x0C)
        self.assertEqual(self.cpu.registers['D'], 0x00)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x99)
        self.assertEqual(self.cpu.registers['L'], 0x0F)
        self.assertEqual(self.cpu.registers['F'], 0xC0)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x55)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x67) # LD H,A

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x60:
            self.cpu.dispatcher()

        clock_m += 11
        self.assertEqual(self.cpu.registers['A'], 0x91)
        self.assertEqual(self.cpu.registers['B'], 0x01)
        self.assertEqual(self.cpu.registers['C'], 0x0C)
        self.assertEqual(self.cpu.registers['D'], 0x64)
        self.assertEqual(self.cpu.registers['E'], 0xE0)
        self.assertEqual(self.cpu.registers['H'], 0x00)
        self.assertEqual(self.cpu.registers['L'], 0x0F)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x60)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x1E) # LD E,2

        self.cpu.dispatcher()
        while self.cpu.registers['PC'] != 0x68:
            self.cpu.dispatcher()

        clock_m += 8
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x01)
        self.assertEqual(self.cpu.registers['C'], 0x0C)
        self.assertEqual(self.cpu.registers['D'], 0x64)
        self.assertEqual(self.cpu.registers['E'], 0x02)
        self.assertEqual(self.cpu.registers['H'], 0x00)
        self.assertEqual(self.cpu.registers['L'], 0x0F)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x68)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x20) # JR NZ,0064

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0x00)
        self.assertEqual(self.cpu.registers['B'], 0x01)
        self.assertEqual(self.cpu.registers['C'], 0x0C)
        self.assertEqual(self.cpu.registers['D'], 0x64)
        self.assertEqual(self.cpu.registers['E'], 0x02)
        self.assertEqual(self.cpu.registers['H'], 0x00)
        self.assertEqual(self.cpu.registers['L'], 0x0F)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x64)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xF0) # LD A,(0xFF00+0x44)

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['A'], 0x08)
        self.assertEqual(self.cpu.registers['B'], 0x01)
        self.assertEqual(self.cpu.registers['C'], 0x0C)
        self.assertEqual(self.cpu.registers['D'], 0x64)
        self.assertEqual(self.cpu.registers['E'], 0x02)
        self.assertEqual(self.cpu.registers['H'], 0x00)
        self.assertEqual(self.cpu.registers['L'], 0x0F)
        self.assertEqual(self.cpu.registers['F'], 0x50)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['PC'], 0x66)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xFE) # CP 0x90
