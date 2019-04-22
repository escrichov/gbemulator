import unittest
from emulator.cpu import Z80

class TestXOR(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.cpu = Z80()
        self.cpu.registers['PC'] = 0x100 # PC is initialized to 0x100 on power up.

    def test_nop(self):
        self.cpu.nop()

        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['M'], 1)
        self.assertEqual(self.cpu.registers['T'], 4)
