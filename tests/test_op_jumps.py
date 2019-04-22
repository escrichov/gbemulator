import unittest
from emulator import utils
from emulator.cpu import Z80

class TestJumps(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.cpu = Z80()
        self.cpu.registers['PC'] = 0x100 # PC is initialized to 0x100 on power up.
        self.cpu.registers['F'] = 0x00
        self.cpu.MMU.rom[0x100] = 253


    def test_jrnzr8_flag_not_zero(self):
        self.cpu.registers['F'] = utils.set_bit(self.cpu.registers['F'], self.cpu.FLAG_Z)

        self.cpu.jrnz()

        self.assertEqual(self.cpu.registers['PC'], 0x101)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)

    def test_jrnzr8_flag_zero(self):
        self.cpu.registers['F'] = utils.reset_bit(self.cpu.registers['F'], self.cpu.FLAG_Z)

        self.cpu.jrnz()

        self.assertEqual(self.cpu.registers['PC'], 0x101 + 253)
        self.assertEqual(self.cpu.registers['M'], 3)
        self.assertEqual(self.cpu.registers['T'], 12)

    def test_jrzr8_flag_not_zero(self):
        self.cpu.registers['F'] = utils.set_bit(self.cpu.registers['F'], self.cpu.FLAG_Z)

        self.cpu.jrz()

        self.assertEqual(self.cpu.registers['PC'], 0x101 + 253)
        self.assertEqual(self.cpu.registers['M'], 3)
        self.assertEqual(self.cpu.registers['T'], 12)

    def test_jrzr8_flag_zero(self):
        self.cpu.registers['F'] = utils.reset_bit(self.cpu.registers['F'], self.cpu.FLAG_Z)

        self.cpu.jrz()

        self.assertEqual(self.cpu.registers['PC'], 0x101)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)

    def test_jrncr8_flag_not_zero(self):
        self.cpu.registers['F'] = utils.set_bit(self.cpu.registers['F'], self.cpu.FLAG_C)

        self.cpu.jrnc()

        self.assertEqual(self.cpu.registers['PC'], 0x101)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)

    def test_jrncr8_flag_zero(self):
        self.cpu.registers['F'] = utils.reset_bit(self.cpu.registers['F'], self.cpu.FLAG_C)

        self.cpu.jrnc()

        self.assertEqual(self.cpu.registers['PC'], 0x101 + 253)
        self.assertEqual(self.cpu.registers['M'], 3)
        self.assertEqual(self.cpu.registers['T'], 12)

    def test_jrcr8_flag_not_zero(self):
        self.cpu.registers['F'] = utils.set_bit(self.cpu.registers['F'], self.cpu.FLAG_C)

        self.cpu.jrc()

        self.assertEqual(self.cpu.registers['PC'], 0x101 + 253)
        self.assertEqual(self.cpu.registers['M'], 3)
        self.assertEqual(self.cpu.registers['T'], 12)

    def test_jrcr8_flag_zero(self):
        self.cpu.registers['F'] = utils.reset_bit(self.cpu.registers['F'], self.cpu.FLAG_C)

        self.cpu.jrc()

        self.assertEqual(self.cpu.registers['PC'], 0x101)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)
