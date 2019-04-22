import unittest
from emulator.cpu import Z80

class TestXOR(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.cpu = Z80()
        self.cpu.registers['PC'] = 0x100 # PC is initialized to 0x100 on power up.

    def test_xora(self):
        self.cpu.registers['A'] = 0xFF

        self.cpu.xora()

        self.assertEqual(self.cpu.registers['A'], 0)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['F'], 0x80)
        self.assertEqual(self.cpu.registers['M'], 1)
        self.assertEqual(self.cpu.registers['T'], 4)

    def test_xorb(self):
        self.cpu.registers['A'] = 0xFF
        self.cpu.registers['B'] = 0x00

        self.cpu.xorb()

        self.assertEqual(self.cpu.registers['A'], 0xFF)
        self.assertEqual(self.cpu.registers['B'], 0)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['F'], 0x0)
        self.assertEqual(self.cpu.registers['M'], 1)
        self.assertEqual(self.cpu.registers['T'], 4)

    def test_xorc(self):
        self.cpu.registers['A'] = 0xFF
        self.cpu.registers['C'] = 0x00

        self.cpu.xorc()

        self.assertEqual(self.cpu.registers['A'], 0xFF)
        self.assertEqual(self.cpu.registers['C'], 0)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['F'], 0x0)
        self.assertEqual(self.cpu.registers['M'], 1)
        self.assertEqual(self.cpu.registers['T'], 4)

    def test_xord(self):
        self.cpu.registers['A'] = 0xFF
        self.cpu.registers['D'] = 0x00

        self.cpu.xord()

        self.assertEqual(self.cpu.registers['A'], 0xFF)
        self.assertEqual(self.cpu.registers['D'], 0)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['F'], 0x0)
        self.assertEqual(self.cpu.registers['M'], 1)
        self.assertEqual(self.cpu.registers['T'], 4)

    def test_xore(self):
        self.cpu.registers['A'] = 0xFF
        self.cpu.registers['E'] = 0x00

        self.cpu.xore()

        self.assertEqual(self.cpu.registers['A'], 0xFF)
        self.assertEqual(self.cpu.registers['E'], 0)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['F'], 0x0)
        self.assertEqual(self.cpu.registers['M'], 1)
        self.assertEqual(self.cpu.registers['T'], 4)

    def test_xorh(self):
        self.cpu.registers['A'] = 0xFF
        self.cpu.registers['H'] = 0x00

        self.cpu.xorh()

        self.assertEqual(self.cpu.registers['A'], 0xFF)
        self.assertEqual(self.cpu.registers['H'], 0)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['F'], 0x0)
        self.assertEqual(self.cpu.registers['M'], 1)
        self.assertEqual(self.cpu.registers['T'], 4)

    def test_xorl(self):
        self.cpu.registers['A'] = 0xFF
        self.cpu.registers['L'] = 0x00

        self.cpu.xorl()

        self.assertEqual(self.cpu.registers['A'], 0xFF)
        self.assertEqual(self.cpu.registers['L'], 0)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['F'], 0x0)
        self.assertEqual(self.cpu.registers['M'], 1)
        self.assertEqual(self.cpu.registers['T'], 4)
