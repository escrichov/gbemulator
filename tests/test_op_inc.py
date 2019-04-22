import unittest
from emulator.cpu import Z80

class TestINC(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.cpu = Z80()
        self.cpu.registers['PC'] = 0x100 # PC is initialized to 0x100 on power up.
        self.cpu.registers['F'] = 0b01010000

    def inc(self, method, register):
        self.cpu.registers[register] = 0xFE

        method()

        self.assertEqual(self.cpu.registers[register], 0xFF)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['F'], 0b00110000)
        self.assertEqual(self.cpu.registers['M'], 1)
        self.assertEqual(self.cpu.registers['T'], 4)

    def inc_result_zero(self, method, register):
        self.cpu.registers[register] = 0xFF

        method()

        self.assertEqual(self.cpu.registers[register], 0x00)
        self.assertEqual(self.cpu.registers['PC'], 0x100)
        self.assertEqual(self.cpu.registers['F'], 0b10110000)
        self.assertEqual(self.cpu.registers['M'], 1)
        self.assertEqual(self.cpu.registers['T'], 4)

    def test_incb(self):
        self.inc(self.cpu.incb, 'B')

    def test_incb_result_zero(self):
        self.inc_result_zero(self.cpu.incb, 'B')

    def test_incc(self):
        self.inc(self.cpu.incc, 'C')

    def test_incc_result_zero(self):
        self.inc_result_zero(self.cpu.incc, 'C')

    def test_incd(self):
        self.inc(self.cpu.incd, 'D')

    def test_incd_result_zero(self):
        self.inc_result_zero(self.cpu.incd, 'D')

    def test_ince(self):
        self.inc(self.cpu.ince, 'E')

    def test_ince_result_zero(self):
        self.inc_result_zero(self.cpu.ince, 'E')

    def test_inch(self):
        self.inc(self.cpu.inch, 'H')

    def test_inch_result_zero(self):
        self.inc_result_zero(self.cpu.inch, 'H')

    def test_incl(self):
        self.inc(self.cpu.incl, 'L')

    def test_incl_result_zero(self):
        self.inc_result_zero(self.cpu.incl, 'L')
