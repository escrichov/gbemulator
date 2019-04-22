import unittest
from emulator.cpu import Z80

class TestLD(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.cpu = Z80()
        self.cpu.registers['PC'] = 0x100 # PC is initialized to 0x100 on power up.

    def test_dispatcher_ldspnn(self):
        self.cpu.MMU.rom[0x100] = 0x31
        self.cpu.MMU.rom[0x101] = 253
        self.cpu.MMU.rom[0x102] = 254

        self.cpu.dispatcher()

        self.assertEqual(self.cpu.registers['PC'], 0x103)
        self.assertEqual(self.cpu.registers['SP'], (254 << 8) + 253)
        self.assertEqual(self.cpu.clock['M'], 3)
        self.assertEqual(self.cpu.clock['T'], 12)
