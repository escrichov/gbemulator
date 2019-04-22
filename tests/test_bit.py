import unittest
from emulator.cpu import Z80

class TestABit(unittest.TestCase):

    register_param = 'a'

    def setUp(self):
        super().setUp()

        self.cpu = Z80()
        self.cpu.registers['PC'] = 0x100 # PC is initialized to 0x100 on power up.
        self.cpu.MMU.rom[0x100] = 7
        self.cpu.registers['F'] = 0b01010000
        self.register = self.register_param.upper()

    def assert_bit_not_set(self):
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)
        self.assertEqual(self.cpu.registers['F'], 0b10110000)

    def assert_bit_set(self):
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['M'], 2)
        self.assertEqual(self.cpu.registers['T'], 8)
        self.assertEqual(self.cpu.registers['F'], 0b00110000)

    def test_bit0_bit_not_set(self):
        self.cpu.registers[self.register] = 0b11111110

        method_to_call = getattr(self.cpu, f'bit0{self.register_param}')
        method_to_call()

        self.assert_bit_not_set()

    def test_bit0_bit_set(self):
        self.cpu.registers[self.register] = 0b00000001

        method_to_call = getattr(self.cpu, f'bit0{self.register_param}')
        method_to_call()

        self.assert_bit_set()

    def test_bit1_bit_not_set(self):
        self.cpu.registers[self.register] = 0b11111101

        method_to_call = getattr(self.cpu, f'bit1{self.register_param}')
        method_to_call()

        self.assert_bit_not_set()

    def test_bit1_bit_set(self):
        self.cpu.registers[self.register] = 0b00000010

        method_to_call = getattr(self.cpu, f'bit1{self.register_param}')
        method_to_call()

        self.assert_bit_set()

    def test_bit2_bit_not_set(self):
        self.cpu.registers[self.register] = 0b11111011

        method_to_call = getattr(self.cpu, f'bit2{self.register_param}')
        method_to_call()

        self.assert_bit_not_set()

    def test_bit2_bit_set(self):
        self.cpu.registers[self.register] = 0b00000100

        method_to_call = getattr(self.cpu, f'bit2{self.register_param}')
        method_to_call()

        self.assert_bit_set()

    def test_bit3_bit_not_set(self):
        self.cpu.registers[self.register] = 0b11110111

        method_to_call = getattr(self.cpu, f'bit3{self.register_param}')
        method_to_call()

        self.assert_bit_not_set()

    def test_bit3_bit_set(self):
        self.cpu.registers[self.register] = 0b00001000

        method_to_call = getattr(self.cpu, f'bit3{self.register_param}')
        method_to_call()

        self.assert_bit_set()

    def test_bit4_bit_not_set(self):
        self.cpu.registers[self.register] = 0b11101111

        method_to_call = getattr(self.cpu, f'bit4{self.register_param}')
        method_to_call()

        self.assert_bit_not_set()

    def test_bit4_bit_set(self):
        self.cpu.registers[self.register] = 0b00010000

        method_to_call = getattr(self.cpu, f'bit4{self.register_param}')
        method_to_call()

        self.assert_bit_set()

    def test_bit5_bit_not_set(self):
        self.cpu.registers[self.register] = 0b11011111

        method_to_call = getattr(self.cpu, f'bit5{self.register_param}')
        method_to_call()

        self.assert_bit_not_set()

    def test_bit5_bit_set(self):
        self.cpu.registers[self.register] = 0b00100000

        method_to_call = getattr(self.cpu, f'bit5{self.register_param}')
        method_to_call()

        self.assert_bit_set()

    def test_bit6_bit_not_set(self):
        self.cpu.registers[self.register] = 0b10111111

        method_to_call = getattr(self.cpu, f'bit6{self.register_param}')
        method_to_call()

        self.assert_bit_not_set()

    def test_bit6_bit_set(self):
        self.cpu.registers[self.register] = 0b01000000

        method_to_call = getattr(self.cpu, f'bit6{self.register_param}')
        method_to_call()

        self.assert_bit_set()

    def test_bit7_bit_not_set(self):
        self.cpu.registers[self.register] = 0b01111111

        method_to_call = getattr(self.cpu, f'bit7{self.register_param}')
        method_to_call()

        self.assert_bit_not_set()

    def test_bit7_bit_set(self):
        self.cpu.registers[self.register] = 0b10000000

        method_to_call = getattr(self.cpu, f'bit7{self.register_param}')
        method_to_call()

        self.assert_bit_set()


class TestBBit(TestABit):
    register_param = 'b'


class TestCBit(TestABit):
    register_param = 'c'


class TestDBit(TestABit):
    register_param = 'd'


class TestEBit(TestABit):
    register_param = 'e'


class TestHBit(TestABit):
    register_param = 'h'


class TestLBit(TestABit):
    register_param = 'l'
