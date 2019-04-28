import unittest
from emulator import utils
from emulator.cpu import Z80


class TestBIOS(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.cpu = Z80()

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
        print(ops, len(ops))
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
        self.assertEqual(self.cpu.registers['H'], 0xFF)
        self.assertEqual(self.cpu.registers['L'], 0x24)
        self.assertEqual(self.cpu.registers['SP'], 0xFFFE)
        self.assertEqual(self.cpu.registers['F'], 0x00)
        self.assertEqual(self.cpu.registers['PC'], 0x1F)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xE0) # LD ($FF00+$47),A

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['PC'], 0x21)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x11) # LD DE,$0104

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['PC'], 0x24)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x21) # LD HL,$8010

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['PC'], 0x27)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x1A) # LD A,(DE)

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['PC'], 0x28)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCD) # CALL 0x0095

        self.cpu.dispatcher()

        clock_m += 3
        self.assertEqual(self.cpu.registers['PC'], 0x95)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x4F) # LD C,A

        self.cpu.dispatcher()

        clock_m += 1
        self.assertEqual(self.cpu.registers['PC'], 0x96)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0x06) # LD B,$04

        self.cpu.dispatcher()

        clock_m += 2
        self.assertEqual(self.cpu.registers['PC'], 0x98)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xC5) # PUSH BC

        self.cpu.dispatcher()

        clock_m += 4
        self.assertEqual(self.cpu.registers['PC'], 0x99)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCB) # RL C
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']+1), 0x11) # RL C

        self.cpu.dispatcher()

        clock_m += 4
        self.assertEqual(self.cpu.registers['PC'], 0x9B)
        self.assertEqual(self.cpu.clock['M'], clock_m)
        self.assertEqual(self.cpu.clock['T'], clock_m * 4)
        self.assertEqual(self.cpu.MMU.rb(self.cpu.registers['PC']), 0xCB) # RLA
