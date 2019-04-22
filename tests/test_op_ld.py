import unittest
from emulator.cpu import Z80

class TestLD(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.cpu = Z80()
        self.cpu.registers['PC'] = 0x100 # PC is initialized to 0x100 on power up.
        self.cpu.MMU.rom[0x100] = 253
        self.cpu.MMU.rom[0x101] = 254

    def test_ldbcnn(self):

        self.cpu.ldbcnn()

        self.assertEqual(self.cpu.registers['B'], 254)
        self.assertEqual(self.cpu.registers['C'], 253)
        self.assertEqual(self.cpu.registers['PC'], 0x102)
        self.assertEqual(self.cpu.registers['M'], 3)
        self.assertEqual(self.cpu.registers['T'], 12)

    def test_lddenn(self):

        self.cpu.lddenn()

        self.assertEqual(self.cpu.registers['D'], 254)
        self.assertEqual(self.cpu.registers['E'], 253)
        self.assertEqual(self.cpu.registers['PC'], 0x102)
        self.assertEqual(self.cpu.registers['M'], 3)
        self.assertEqual(self.cpu.registers['T'], 12)

    def test_ldhlnn(self):

        self.cpu.ldhlnn()

        self.assertEqual(self.cpu.registers['H'], 254)
        self.assertEqual(self.cpu.registers['L'], 253)
        self.assertEqual(self.cpu.registers['PC'], 0x102)
        self.assertEqual(self.cpu.registers['M'], 3)
        self.assertEqual(self.cpu.registers['T'], 12)

    def test_ldspnn(self):

        self.cpu.ldspnn()

        self.assertEqual(self.cpu.registers['SP'], (254 << 8) + 253)
        self.assertEqual(self.cpu.registers['PC'], 0x102)
        self.assertEqual(self.cpu.registers['M'], 3)
        self.assertEqual(self.cpu.registers['T'], 12)

    def test_ldhlminusa(self):
        self.cpu.registers['A'] = 78
        self.cpu.registers['H'] = 0xFF
        self.cpu.registers['L'] = 0xC0
        addr = 0xFF + (0xC0 << 8)

        self.cpu.ldhlminusa()

        self.assertEqual(self.cpu.registers['H'], 0xFF)
        self.assertEqual(self.cpu.registers['L'], 0xBF)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)
        self.assertEqual(self.cpu.registers['A'], 78)
        self.assertEqual(self.cpu.MMU.rb(addr), self.cpu.registers['A'])

    def test_ldbd8(self):

        self.cpu.ldbd8()

        self.assertEqual(self.cpu.registers['B'], 253)
        self.assertEqual(self.cpu.registers['PC'], 0x101)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)

    def test_ldcd8(self):

        self.cpu.ldcd8()

        self.assertEqual(self.cpu.registers['C'], 253)
        self.assertEqual(self.cpu.registers['PC'], 0x101)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)

    def test_lddd8(self):

        self.cpu.lddd8()

        self.assertEqual(self.cpu.registers['C'], 253)
        self.assertEqual(self.cpu.registers['PC'], 0x101)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)

    def test_lded8(self):

        self.cpu.lded8()

        self.assertEqual(self.cpu.registers['E'], 253)
        self.assertEqual(self.cpu.registers['PC'], 0x101)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)

    def test_ldhd8(self):

        self.cpu.ldhd8()

        self.assertEqual(self.cpu.registers['H'], 253)
        self.assertEqual(self.cpu.registers['PC'], 0x101)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)

    def test_ldld8(self):

        self.cpu.ldld8()

        self.assertEqual(self.cpu.registers['L'], 253)
        self.assertEqual(self.cpu.registers['PC'], 0x101)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)

    def test_ldca(self):
        self.cpu.registers['A'] = 101
        self.cpu.registers['C'] = 3

        self.cpu.ldca()

        self.assertEqual(self.cpu.MMU.zram[0x3], 101)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)

    def test_ldhla(self):
        self.cpu.registers['A'] = 101
        self.cpu.registers['H'] = 0xC0
        self.cpu.registers['L'] = 0x01

        self.cpu.ldhla()

        self.assertEqual(self.cpu.MMU.wram[0xC001 & 0x1FFF], 101)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)
