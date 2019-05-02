
from emulator.mmu import MMU
from emulator.gpu import GPU
from emulator import utils
from emulator import graphics

class Z80():
    # Flags
    # 7 6 5 4 3 2 1 0
    # Z N H C 0 0 0 0
    FLAG_Z = 7
    FLAG_N = 6
    FLAG_H = 5
    FLAG_C = 4

    # Halt & stop mode
    stop_mode = 0 # Halt CPU & LCD display until button pressed.
    halt_mode = 0 # Power down CPU until an interrupt occurs

    # Interrupt enabled
    interrup_enabled = 1

    # Time clock: The Z80 holds two types of clock (m and t)
    clock = {'M': 0, 'T': 0}

    registers = {
        'A': 0, 'B':0, 'C': 0, 'D':0, 'E': 0, 'H':0, 'L':0, # 8-bit registers
        'F': 0, # Flags register
                # Zero (0x80): Set if the last operation produced a result of 0
                # Operation (0x40): Set if the last operation was a subtraction
                # Half-carry (0x20): Set if, in the result of the last operation, the lower half of the byte overflowed past 15
                # Carry (0x10): Set if the last operation produced a result over 255 (for additions) or under 0 (for subtractions).

        'PC': 0, 'SP': 0,                                          # 16-bit registers
        'M': 0, 'T': 0,                                            # Clock for last instr
    }

    # PC (Program Counter)
    # PC is initialized to 0x100 on power up.
    # The instruction found in this location is executed.
    # Then the program counter is controlled indirectly by the instructions.

    # SP (Stack pointer)
    # The stack is used for saving variables, saving return addresses,
    # passing arguments to subroutines, and various other uses
    # CALL, PUSH, and RST all put information onto the stack
    # POP, RET, and RETI all take information off of the stack
    # (Interrupts put a return address on the stack and remove it at their completion as well.)
    # As information is put onto the stack, the stack grows downward in RAM memory.
    # The Stack Pointer automatically decrements before it puts something onto the stack
    # Stack Pointer is initialized to $FFFE on power up
    # Set Stack pointer with instruction: LD SP,0xE000

    current_op = 0

    def __init__(self, headless=False):
        if not headless:
            self.window = graphics.Window('Gameboy')
        else:
            self.window = None
        self.GPU = GPU(self, self.window)
        self.MMU = MMU(self)

    def get_16b_register(self, register_high, register_low):
        return utils.bytes_to_16(self.registers[register_high], self.registers[register_low])

    def set_16b_register(self, register_high, register_low, value):
        self.registers[register_high] = value >> 8
        self.registers[register_low] = value & 0xFF

    def rb_16b_register(self, register_high, register_low):
        addr = utils.bytes_to_16(self.registers[register_high], self.registers[register_low])
        return self.MMU.rb(addr)

    def wb_16b_register(self, register_high, register_low, value):
        addr = utils.bytes_to_16(self.registers[register_high], self.registers[register_low])
        self.MMU.wb(addr, value)

    def rw_16b_register(self, register_high, register_low):
        addr = utils.bytes_to_16(self.registers[register_high], self.registers[register_low])
        return self.MMU.rw(addr)

    def ww_16b_register(self, register_high, register_low, value):
        addr = utils.bytes_to_16(self.registers[register_high], self.registers[register_low])
        self.MMU.ww(addr, value)

    def push_16b_on_stack(self, value):
        self.registers['SP'] -= 1 # Decrement Stack Pointer (SP)
        self.MMU.wb(self.registers['SP'], value >> 8)
        self.registers['SP'] -= 1 # Decrement Stack Pointer (SP)
        self.MMU.wb(self.registers['SP'], value & 0xFF)

    def pop_16b_from_stack(self):
        value = self.MMU.rw(self.registers['SP'])
        self.registers['SP'] += 2 # Increment Stack Pointer (SP)
        return value

    # Add n to A.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Set if carry from bit 3.
    #   C - Set if carry from bit 7.
    # Use with: n = A,B,C,D,E,H,L,(HL), #
    def op_add_an(self, value):
        if utils.half_carry_8_bit(self.registers['A'], value):
            half_carry = True
        else:
            half_carry = False
        if utils.carry_8_bit(self.registers['A'], value):
            carry = True
        else:
            carry = False
        self.registers['A'] += value
        self.registers['F'] = 0 # Clear flags
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        if half_carry: # H - Set if carry from bit 3.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H)
        if carry: # C - Set if carry from bit 7.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C)
        self.registers['A'] &= 255 # Mask to 8-bits
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # ADC A,n
    # Add n + Carry flag to A
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Set if carry from bit 3.
    #   C - Set if carry from bit 7.
    def op_adc_an(self, value):
        carry_flag_value = utils.get_bit(self.registers['F'], self.FLAG_C)  # Get carry flag value
        value += carry_flag_value
        self.op_add_an(value)

    # SUB n
    # Subtract n from A
    # Use with
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Set.
    #   H - Set if no borrow from bit 4.
    #   C - Set if no borrow.
    def op_sub_an(self, value):
        if utils.half_borrow_8_bit(self.registers['A'], value):
            half_borrow = True
        else:
            half_borrow = False
        if utils.half_borrow_8_bit(self.registers['A'], value):
            borrow = True
        else:
            borrow = False
        self.registers['A'] -= value
        self.registers['F'] = 0 # Clear flags
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_N) # Set
        if half_borrow: # H - Set if borrow from bit 3.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H)
        if borrow: # C - Set if borrow from bit 7.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C)
        self.registers['A'] &= 255 # Mask to 8-bits
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # SBC A,n
    # Subtract n + Carry flag from A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Set.
    #   H - Set if no borrow from bit 4.
    #   C - Set if no borrow.
    def op_sbc_an(self, value):
        carry_flag_value = utils.get_bit(self.registers['F'], self.FLAG_C)  # Get carry flag value
        value += carry_flag_value
        self.op_sub_an(value)

    # AND n
    # Logically AND n with A, result in A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Set.
    #   C - Reset.
    def op_and_n(self, value):
        self.registers['A'] = self.registers['A'] & value
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z) # Z - Set if bit b of register r is 0.
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H) # H - Set.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) # C - Reset.
        self.registers['M'] = 2 # 8 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    # OR n
    # Logical OR n with register A, result in A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Reset.
    def op_or_n(self, value):
        self.registers['A'] = self.registers['A'] | value
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z) # Z - Set if bit b of register r is 0.
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) # H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) # C - Reset.
        self.registers['M'] = 2 # 8 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    # XOR n
    # Logical exclusive OR n with register A, result in A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Reset.
    def op_xor_n(self, value):
        self.registers['A'] = utils.bitwise_xor(self.registers['A'], value)
        self.registers['F'] = 0x00 # Clear flags
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] |= 0x80
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # Test bit b in register r.
    # Use with:
    #   b = 0 - 7, r = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if bit b of register r is 0.
    #   N - Reset.
    #   H - Set.
    #   C - Not affected.
    def op_test_bit(self, value, bit):
        if not utils.test_bit(value, bit): # Z - Set if bit b of register r is 0.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z) # Z - Set if bit b of register r is 0.
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H) # H - Set.
        self.registers['M'] = 2 # 8 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    def op_test_bit_hl(self, bit):
        value = self.rb_16b_register('H', 'L')
        if not utils.test_bit(value, bit): # Z - Set if bit b of register r is 0.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z) # Z - Set if bit b of register r is 0.
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H) # H - Set.
        self.registers['M'] = 4 # 16 M-time taken
        self.registers['T'] = 16 # 16 M-time taken

    # SET b,r
    # Set bit b in register r.
    # Use with:
    #   b = 0 - 7, r = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   None
    def op_set_bit(self, register, bit):
        self.register[register] = utils.set_bit(self.register[register], bit)
        self.register['PC'] += 1
        self.registers['M'] = 2 # 8 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    def op_set_bit_hl(self, register, bit):
        value = self.rb_16b_register('H', 'L')
        value = utils.set_bit(value, bit)
        self.wb_16b_register('H', 'L')
        self.registers['M'] = 2 # 8 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    # RES b,r
    # Reset bit b in register r.
    # Use with:
    #   b = 0 - 7, r = A,B,C,D,E,H,L,(HL)
    # Flags affected: None
    def op_reset_bit(self, register, bit):
        self.register[register] = utils.reset_bit(self.register[register], bit)
        self.registers['M'] = 2 # 8 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    def op_reset_bit_hl(self, register, bit):
        value = self.rb_16b_register('H', 'L')
        value = utils.reset_bit(value, bit)
        self.wb_16b_register('H', 'L')
        self.registers['M'] = 2 # 8 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    def op_inc(self, register):
        if utils.half_carry_8_bit(self.registers[register], 1):
            half_carry = 1
        else:
            half_carry = 0
        self.registers[register] += 1
        self.registers[register] &= 255
        if self.registers[register] == 0: # Z - Set if bit b of register r is 0.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z) # Z -  Set if result is zero.
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z) # Z -  Set if result is zero.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        if half_carry:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H) # H - Set if half carry
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) # H - Set if half carry
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    def op_inc_hlm(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        value = self.MMU.rb(addr)
        if utils.half_carry_8_bit(value, 1):
            half_carry = 1
        else:
            half_carry = 0
        value += 1
        value &= 255
        self.MMU.wb(addr, value)
        if value == 0: # Z - Set if bit b of register r is 0.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z) # Z -  Set if result is zero.
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z) # Z -  Set if result is zero.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        if half_carry:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H) # H - Set if half carry
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) # H - Set if half carry
        self.registers['M'] = 3 # 3 M-time taken
        self.registers['T'] = 12 # 12 M-time taken

    def op_inc_16(self, register_high, register_low):
        value = self.get_16b_register(register_high, register_low)
        value += 1
        value &= 0xFFFF
        self.set_16b_register(register_high, register_low, value)
        self.registers['M'] = 2 # 1 M-time taken
        self.registers['T'] = 8 # 1 M-time taken

    def op_inc_16_one_register(self, register):
        self.registers[register] += 1
        self.registers[register] &= 0xFFFF
        self.registers['M'] = 2 # 1 M-time taken
        self.registers['T'] = 8 # 1 M-time taken

    def op_dec(self, register):
        borrow_bit_4 = utils.half_borrow_8_bit(self.registers[register], 1)
        self.registers[register] -= 1
        self.registers[register] &= 255
        if self.registers[register] == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        if not borrow_bit_4:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H)
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_N) #  N - Set.
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    def op_dec_hl(self):
        addr = self.registers['H'] << 8 + self.registers['L']
        value = self.MMU.rb(addr)
        value -= 1
        value &= 255
        self.MMU.wb(addr, value)
        if value == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_N) #  N - Set.
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    def op_dec_16(self, register_high, register_low):
        value = self.registers[register_high] << 8 + self.registers[register_low]
        value -= 1
        value &= 0xFFFF
        self.set_16b_register(register_high, register_low, value)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    def op_dec_sp(self):
        self.registers['SP'] -= 1
        self.registers['SP'] &= 0xFFFF
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

   # CP n
    # Compare A with n. This is basically an A - n
    # subtraction instruction but the results are thrown away.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero. (Set if A = n.)
    #   N - Set. Substraction flag
    #   H - Set if no borrow from bit 4.
    #   C - Set for no borrow. (Set if A < n.)
    def op_cp_an(self, n):
        result = self.registers['A'] - n
        self.registers['F'] = 0x00 # Clear flags
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_N) # N - Set. Substraction flag
        if result == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        if not utils.half_borrow_8_bit(self.registers['A'], n): # H - Set if no borrow from bit 4.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H)
        if not utils.borrow_8_bit(self.registers['A'], n): # C - Set for no borrow. (Set if A < n.)
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C)
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # ADD HL,n
    # Add n to HL.
    # Flags affected:
    #   Z - Not affected.
    #   N - Reset.
    #   H - Set if carry from bit 11.
    #   C - Set if carry from bit 15.
    # Use with: n = BC,DE,HL,SP
    def op_add_hln(self, value):
        hlm_value = self.rw_16b_register('H', 'L')
        if utils.half_carry_16_bit(hlm_value, value):
            half_carry = True
        else:
            half_carry = False
        if utils.carry_16_bit(hlm_value, value):
            carry = True
        else:
            carry = False
        hlm_value += value
        hlm_value &= 0xFFFF # Mask to 16-bits
        self.ww_16b_register('H', 'L', hlm_value)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        if half_carry: # H - Set if carry from bit 11.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H)
        if carry: # C - Set if carry from bit 15.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C)
        self.registers['M'] = 2 # 1 M-time taken
        self.registers['T'] = 8 # 1 M-time taken

    def op_ld_r1r2(self, r_dst, r_src):
        self.registers[r_dst] = self.registers[r_src]
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    def op_ld_r1hl(self, r_dst):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        self.registers[r_dst] = self.MMU.rb(addr) # Read from address
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def op_ld_r1bc(self, r_dst):
        addr = utils.bytes_to_16(self.registers['B'], self.registers['C'])
        self.registers[r_dst] = self.MMU.rb(addr) # Read from address
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def op_ld_r1de(self, r_dst):
        self.registers[r_dst] = self.rb_16b_register('D', 'E') # Read from address
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def op_ld_r1nn(self, r_dst):
        addr = self.MMU.rw(self.registers['PC']) # Get address from instr
        self.registers['PC'] += 2 # Advance PC
        self.registers[r_dst] = self.MMU.rb(addr) # Read from address
        self.registers['M'] = 4  # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    def op_ld_hlr2(self, r_src):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        self.MMU.wb(addr, self.registers[r_src])
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def op_pushnn(self, register1, register2):
        self.registers['SP'] -= 1 # Decrement Stack Pointer (SP)
        self.MMU.wb(self.registers['SP'], self.registers[register1])
        self.registers['SP'] -= 1 # Decrement Stack Pointer (SP)
        self.MMU.wb(self.registers['SP'], self.registers[register2])
        self.registers['M'] = 4  # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    def op_popnn(self, register1, register2):
        self.registers[register2] = self.MMU.rb(self.registers['SP'])
        self.registers['SP'] += 1 # Increment Stack Pointer (SP)
        self.registers[register1] = self.MMU.rb(self.registers['SP'])
        self.registers['SP'] += 1 # Increment Stack Pointer (SP)
        self.registers['M'] = 3  # 3 M-time taken
        self.registers['T'] = 12 # 12 M-time taken

    # SWAP n
    # Add n to HL.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Reset.
    def op_swapn(self, register):
        self.register[register] = utils.swap_nibbles(self.register[register])
        self.registers['F'] = 0x00
        if self.registers[register] == 0:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def op_swaphlm(self):
        value = self.rb_16b_register('H', 'L')
        value = utils.swap_nibbles(value)
        self.wb_16b_register('H', 'L', value)
        self.registers['F'] = 0x00
        if value == 0:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        self.registers['M'] = 4 # 4 M-time taken
        self.registers['T'] = 16 # 2 M-time taken

    # RLC n
    # Rotate n left. Old bit 7 to Carry flag.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 7 data.
    def op_rlc_common(self, value):
        old_bit_7_data = utils.get_bit(value, 7)
        value = (value << 8) + old_bit_7_data # Rotate A left
        value &= 255
        if value == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) #  H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) #  N - Reset.
        if old_bit_7_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

        return value

    def op_rlc_register(self, register):
        self.registers[register] = self.op_rlc_common(self.registers[register])

    # RL n
    # Rotate n left through Carry flag.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 7 data.
    def op_rl_common(self, value):
        old_carry_flag = utils.get_bit(self.registers['F'], self.FLAG_C)
        old_bit_7_data = utils.get_bit(value, 7)
        value = (value << 1) + old_carry_flag # Rotate A left through Carry flag.
        value &= 0xFF
        if value == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) #  H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) #  N - Reset.
        if old_bit_7_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 7 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 7 data
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

        return value

    def op_rla(self):
        value = self.registers['A']
        old_carry_flag = utils.get_bit(self.registers['F'], self.FLAG_C)
        old_bit_7_data = utils.get_bit(value, 7)
        value = (value << 1) + old_carry_flag # Rotate A left through Carry flag.
        value &= 0xFF
        self.registers['A'] = value
        self.registers['F'] = 0x00
        if old_bit_7_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 7 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 7 data
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

        return value

    def op_rl_register(self, register):
        self.registers[register] = self.op_rl_common(self.registers[register])

    # RRC n
    # Rotate n right. Old bit 0 to Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C -  Contains old bit 0 data
    def op_rrc_common(self):
        old_bit_0_data = utils.get_bit(value, 0)
        value = value >> 1 + (old_bit_0_data << 7) # Rotate A right
        value &= 255
        if value == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) #  H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) #  N - Reset.
        if old_bit_0_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        self.registers['M'] = 2 # 1 M-time taken
        self.registers['T'] = 8 # 1 M-time taken

    def op_rrc_register(self, register):
        self.registers[register] = self.op_rl_common(self.registers[register])

    # RRA
    # Rotate A right through Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 0 data.
    def op_rr_common(self):
        old_bit_0_data = utils.get_bit(value, 0)
        old_bit_4_data = utils.get_bit(value, 4)
        value = value >> 1 + (old_bit_4_data << 7) # Rotate A right through Carry flag.
        value &= 255
        if value == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) #  H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) #  N - Reset.
        if old_bit_7_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    def op_rrc_register(self, register):
        self.registers[register] = self.op_rr_common(self.registers[register])

    # SLA n
    # Shift n left into Carry. LSB of n set to 0.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 7 data.
    def op_sla_common(self):
        old_bit_7_data = utils.get_bit(value, 7)
        value = value << 1
        value &= 255
        if value == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) #  H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) #  N - Reset.
        if old_bit_7_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    def op_sla_register(self, register):
        self.registers[register] = self.op_sla_common(self.registers[register])

    # SRA n
    # Shift n right into Carry. MSB doesn't change.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 0 data.
    def op_sra_common(self):
        old_bit_7_data = utils.get_bit(value, 7)
        old_bit_0_data = utils.get_bit(value, 0)
        value = (old_bit_7_data << 7) + (value >> 1)
        value &= 255
        if value == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) #  H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) #  N - Reset.
        if old_bit_0_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    def op_sra_register(self, register):
        self.registers[register] = self.op_sra_common(self.registers[register])

    # SRL n
    # Shift n right into Carry. MSB set to 0.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 0 data.
    def op_srl_common(self):
        old_bit_0_data = utils.get_bit(value, 0)
        value = value >> 1
        value &= 255
        if value == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) #  H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) #  N - Reset.
        if old_bit_0_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    def op_srl_register(self, register):
        self.registers[register] = self.op_srl_common(self.registers[register])

    # RST n
    # Push present address onto stack.
    # Jump to address 0x0000 + n.
    # Use with:
    #   nn = 0x00,0x08,0x10,0x18,0x20,0x28,0x30,0x38
    def op_rst(self, value):
        self.push_16b_on_stack(self.registers['PC']) # Push address of next instruction onto stack
        self.registers['PC'] = value # Jump to address 0x0000 + n.
        self.registers['M'] = 8 # 8 M-time taken
        self.registers['T'] = 32 # 8 M-time taken

    def add_aa(self):
        self.op_add_an(self.registers['A'])

    def add_ab(self):
        self.op_add_an(self.registers['B'])

    def add_ac(self):
        self.op_add_an(self.registers['C'])

    def add_ad(self):
        self.op_add_an(self.registers['D'])

    def add_ae(self):
        self.op_add_an(self.registers['E'])

    def add_ah(self):
        self.op_add_an(self.registers['H'])

    def add_al(self):
        self.op_add_an(self.registers['L'])

    def add_ahl(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        value = self.MMU.rb(addr)
        self.op_add_an(value)
        self.registers['M'] = 8 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def add_an(self):
        value = self.registers['PC']
        self.registers['PC'] += 1
        self.op_add_an(value)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def adc_aa(self):
        self.op_adc_an(self.registers['A'])

    def adc_ab(self):
        self.op_adc_an(self.registers['B'])

    def adc_ac(self):
        self.op_adc_an(self.registers['C'])

    def adc_ad(self):
        self.op_adc_an(self.registers['D'])

    def adc_ae(self):
        self.op_adc_an(self.registers['E'])

    def adc_ah(self):
        self.op_adc_an(self.registers['H'])

    def adc_al(self):
        self.op_adc_an(self.registers['L'])

    def adc_ahl(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        value = self.MMU.rb(addr)
        self.op_adc_an(value)
        self.registers['M'] = 8 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def adc_an(self):
        value = self.registers['PC']
        self.registers['PC'] += 1
        self.op_adc_an(value)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def sub_aa(self):
        self.op_sub_an(self.registers['A'])

    def sub_ab(self):
        self.op_sub_an(self.registers['B'])

    def sub_ac(self):
        self.op_sub_an(self.registers['C'])

    def sub_ad(self):
        self.op_sub_an(self.registers['D'])

    def sub_ae(self):
        self.op_sub_an(self.registers['E'])

    def sub_ah(self):
        self.op_sub_an(self.registers['H'])

    def sub_al(self):
        self.op_sub_an(self.registers['L'])

    def sub_ahl(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        value = self.MMU.rb(addr)
        self.op_sub_an(value)
        self.registers['M'] = 8 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def sub_an(self):
        value = self.registers['PC']
        self.registers['PC'] += 1
        self.op_sub_an(value)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def sbc_aa(self):
        self.op_sbc_an(self.registers['A'])

    def sbc_ab(self):
        self.op_sbc_an(self.registers['B'])

    def sbc_ac(self):
        self.op_sbc_an(self.registers['C'])

    def sbc_ad(self):
        self.op_sbc_an(self.registers['D'])

    def sbc_ae(self):
        self.op_sbc_an(self.registers['E'])

    def sbc_ah(self):
        self.op_sbc_an(self.registers['H'])

    def sbc_al(self):
        self.op_sbc_an(self.registers['L'])

    def sbc_ahl(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        value = self.MMU.rb(addr)
        self.op_sbc_an(value)
        self.registers['M'] = 8 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def sbc_an(self):
        value = self.registers['PC']
        self.registers['PC'] += 1
        self.op_sbc_an(value)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def and_aa(self):
        self.op_and_n(self.registers['A'])

    def and_ab(self):
        self.op_and_n(self.registers['B'])

    def and_ac(self):
        self.op_and_n(self.registers['C'])

    def and_ad(self):
        self.op_and_n(self.registers['D'])

    def and_ae(self):
        self.op_and_n(self.registers['E'])

    def and_ah(self):
        self.op_and_n(self.registers['H'])

    def and_al(self):
        self.op_and_n(self.registers['L'])

    def and_ahl(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        value = self.MMU.rb(addr)
        self.op_and_n(value)
        self.registers['M'] = 8 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def and_an(self):
        value = self.registers['PC']
        self.registers['PC'] += 1
        self.op_and_n(value)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def or_aa(self):
        self.op_or_an(self.registers['A'])

    def or_ab(self):
        self.op_or_an(self.registers['B'])

    def or_ac(self):
        self.op_or_an(self.registers['C'])

    def or_ad(self):
        self.op_or_an(self.registers['D'])

    def or_ae(self):
        self.op_or_an(self.registers['E'])

    def or_ah(self):
        self.op_or_an(self.registers['H'])

    def or_al(self):
        self.op_or_an(self.registers['L'])

    def or_ahl(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        value = self.MMU.rb(addr)
        self.op_or_an(value)
        self.registers['M'] = 8 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def or_an(self):
        value = self.registers['PC']
        self.registers['PC'] += 1
        self.op_or_an(value)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def xor_aa(self):
        self.op_xor_n(self.registers['A'])

    def xor_ab(self):
        self.op_xor_n(self.registers['B'])

    def xor_ac(self):
        self.op_xor_n(self.registers['C'])

    def xor_ad(self):
        self.op_xor_n(self.registers['D'])

    def xor_ae(self):
        self.op_xor_n(self.registers['E'])

    def xor_ah(self):
        self.op_xor_n(self.registers['H'])

    def xor_al(self):
        self.op_xor_n(self.registers['L'])

    def xor_ahl(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        value = self.MMU.rb(addr)
        self.op_xor_a(value)
        self.registers['M'] = 8 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def xor_an(self):
        value = self.registers['PC']
        self.registers['PC'] += 1
        self.op_xor_a(value)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def addhlbc(self):
        n = self.get_16b_register('B', 'C')
        self.op_add_hln(n)

    def addhlde(self):
        n = self.get_16b_register('D', 'E')
        self.op_add_hln(n)

    def addhlhl(self):
        n = self.get_16b_register('H', 'L')
        self.op_add_hln(n)

    def addhlsp(self):
        n = self.registers['SP']
        self.op_add_hln(n)

    # ADD SP,n
    # Use with: one byte signed immediate value (#).
    # Use with: n = one byte signed immediate value (#).
    # Flags affected:
    #   Z - Reset.
    #   N - Reset.
    #   H - Set or reset according to operation.
    #   C - Set or reset according to operation.
    def addspn():
        n = utils.signed_8b(self.MMU.rb(self.registers['PC']))
        self.registers['PC'] += 1
        sp_value = self.registers['SP']
        if utils.half_carry_16_bit(sp_value, n):
            half_carry = True
        else:
            half_carry = False
        if utils.carry_16_bit(sp_value, n):
            carry = True
        else:
            carry = False
        sp_value += n
        sp_value &= 0xFFFF # Mask to 16-bits
        self.registers['SP'] = sp_value
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z) # N - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        if half_carry: # H - Set if carry from bit 11.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H)
        if carry: # C - Set if carry from bit 15.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C)
        self.registers['M'] = 4 # 4 M-time taken
        self.registers['T'] = 16 # 16 M-time taken

    def bit0a(self):
        self.op_test_bit(self.registers['A'], 0)

    def bit0b(self):
        self.op_test_bit(self.registers['B'], 0)

    def bit0c(self):
        self.op_test_bit(self.registers['C'], 0)

    def bit0d(self):
        self.op_test_bit(self.registers['D'], 0)

    def bit0e(self):
        self.op_test_bit(self.registers['E'], 0)

    def bit0h(self):
        self.op_test_bit(self.registers['H'], 0)

    def bit0l(self):
        self.op_test_bit(self.registers['L'], 0)

    def bit0hl(self):
        self.op_test_bit_hl(0)

    def bit1a(self):
        self.op_test_bit(self.registers['A'], 1)

    def bit1b(self):
        self.op_test_bit(self.registers['B'], 1)

    def bit1c(self):
        self.op_test_bit(self.registers['C'], 1)

    def bit1d(self):
        self.op_test_bit(self.registers['D'], 1)

    def bit1e(self):
        self.op_test_bit(self.registers['E'], 1)

    def bit1h(self):
        self.op_test_bit(self.registers['H'], 1)

    def bit1l(self):
        self.op_test_bit(self.registers['L'], 1)

    def bit1hl(self):
        self.op_test_bit_hl(1)

    def bit2a(self):
        self.op_test_bit(self.registers['A'], 2)

    def bit2b(self):
        self.op_test_bit(self.registers['B'], 2)

    def bit2c(self):
        self.op_test_bit(self.registers['C'], 2)

    def bit2d(self):
        self.op_test_bit(self.registers['D'], 2)

    def bit2e(self):
        self.op_test_bit(self.registers['E'], 2)

    def bit2h(self):
        self.op_test_bit(self.registers['H'], 2)

    def bit2l(self):
        self.op_test_bit(self.registers['L'], 2)

    def bit2hl(self):
        self.op_test_bit_hl(2)

    def bit3a(self):
        self.op_test_bit(self.registers['A'], 3)

    def bit3b(self):
        self.op_test_bit(self.registers['B'], 3)

    def bit3c(self):
        self.op_test_bit(self.registers['C'], 3)

    def bit3d(self):
        self.op_test_bit(self.registers['D'], 3)

    def bit3e(self):
        self.op_test_bit(self.registers['E'], 3)

    def bit3h(self):
        self.op_test_bit(self.registers['H'], 3)

    def bit3l(self):
        self.op_test_bit(self.registers['L'], 3)

    def bit3hl(self):
        self.op_test_bit_hl(3)

    def bit4a(self):
        self.op_test_bit(self.registers['A'], 4)

    def bit4b(self):
        self.op_test_bit(self.registers['B'], 4)

    def bit4c(self):
        self.op_test_bit(self.registers['C'], 4)

    def bit4d(self):
        self.op_test_bit(self.registers['D'], 4)

    def bit4e(self):
        self.op_test_bit(self.registers['E'], 4)

    def bit4h(self):
        self.op_test_bit(self.registers['H'], 4)

    def bit4l(self):
        self.op_test_bit(self.registers['L'], 4)

    def bit4hl(self):
        self.op_test_bit_hl(4)

    def bit5a(self):
        self.op_test_bit(self.registers['A'], 5)

    def bit5b(self):
        self.op_test_bit(self.registers['B'], 5)

    def bit5c(self):
        self.op_test_bit(self.registers['C'], 5)

    def bit5d(self):
        self.op_test_bit(self.registers['D'], 5)

    def bit5e(self):
        self.op_test_bit(self.registers['E'], 5)

    def bit5h(self):
        self.op_test_bit(self.registers['H'], 5)

    def bit5l(self):
        self.op_test_bit(self.registers['L'], 5)

    def bit5hl(self):
        self.op_test_bit_hl(5)

    def bit6a(self):
        self.op_test_bit(self.registers['A'], 6)

    def bit6b(self):
        self.op_test_bit(self.registers['B'], 6)

    def bit6c(self):
        self.op_test_bit(self.registers['C'], 6)

    def bit6d(self):
        self.op_test_bit(self.registers['D'], 6)

    def bit6e(self):
        self.op_test_bit(self.registers['E'], 6)

    def bit6h(self):
        self.op_test_bit(self.registers['H'], 6)

    def bit6l(self):
        self.op_test_bit(self.registers['L'], 6)

    def bit6hl(self):
        self.op_test_bit_hl(6)

    def bit7a(self):
        self.op_test_bit(self.registers['A'], 7)

    def bit7b(self):
        self.op_test_bit(self.registers['B'], 7)

    def bit7c(self):
        self.op_test_bit(self.registers['C'], 7)

    def bit7d(self):
        self.op_test_bit(self.registers['D'], 7)

    def bit7e(self):
        self.op_test_bit(self.registers['E'], 7)

    def bit7h(self):
        self.op_test_bit(self.registers['H'], 7)

    def bit7l(self):
        self.op_test_bit(self.registers['L'], 7)

    def bit7hl(self):
        self.op_test_bit_hl(7)

    def setbit0a(self):
        self.op_set_bit(self.registers['A'], 0)

    def setbit0b(self):
        self.op_set_bit(self.registers['B'], 0)

    def setbit0c(self):
        self.op_set_bit(self.registers['C'], 0)

    def setbit0d(self):
        self.op_set_bit(self.registers['D'], 0)

    def setbit0e(self):
        self.op_set_bit(self.registers['E'], 0)

    def setbit0h(self):
        self.op_set_bit(self.registers['H'], 0)

    def setbit0l(self):
        self.op_set_bit(self.registers['L'], 0)

    def setbit0hl(self):
        self.op_set_bit_hl(0)

    def setbit1a(self):
        self.op_set_bit(self.registers['A'], 1)

    def setbit1b(self):
        self.op_set_bit(self.registers['B'], 1)

    def setbit1c(self):
        self.op_set_bit(self.registers['C'], 1)

    def setbit1d(self):
        self.op_set_bit(self.registers['D'], 1)

    def setbit1e(self):
        self.op_set_bit(self.registers['E'], 1)

    def setbit1h(self):
        self.op_set_bit(self.registers['H'], 1)

    def setbit1l(self):
        self.op_set_bit(self.registers['L'], 1)

    def setbit1hl(self):
        self.op_set_bit_hl(1)

    def setbit2a(self):
        self.op_set_bit(self.registers['A'], 2)

    def setbit2b(self):
        self.op_set_bit(self.registers['B'], 2)

    def setbit2c(self):
        self.op_set_bit(self.registers['C'], 2)

    def setbit2d(self):
        self.op_set_bit(self.registers['D'], 2)

    def setbit2e(self):
        self.op_set_bit(self.registers['E'], 2)

    def setbit2h(self):
        self.op_set_bit(self.registers['H'], 2)

    def setbit2l(self):
        self.op_set_bit(self.registers['L'], 2)

    def setbit2hl(self):
        self.op_set_bit_hl(2)

    def setbit3a(self):
        self.op_set_bit(self.registers['A'], 3)

    def setbit3b(self):
        self.op_set_bit(self.registers['B'], 3)

    def setbit3c(self):
        self.op_set_bit(self.registers['C'], 3)

    def setbit3d(self):
        self.op_set_bit(self.registers['D'], 3)

    def setbit3e(self):
        self.op_set_bit(self.registers['E'], 3)

    def setbit3h(self):
        self.op_set_bit(self.registers['H'], 3)

    def setbit3l(self):
        self.op_set_bit(self.registers['L'], 3)

    def setbit3hl(self):
        self.op_set_bit_hl(3)

    def setbit4a(self):
        self.op_set_bit(self.registers['A'], 4)

    def setbit4b(self):
        self.op_set_bit(self.registers['B'], 4)

    def setbit4c(self):
        self.op_set_bit(self.registers['C'], 4)

    def setbit4d(self):
        self.op_set_bit(self.registers['D'], 4)

    def setbit4e(self):
        self.op_set_bit(self.registers['E'], 4)

    def setbit4h(self):
        self.op_set_bit(self.registers['H'], 4)

    def setbit4l(self):
        self.op_set_bit(self.registers['L'], 4)

    def setbit4hl(self):
        self.op_set_bit_hl(4)

    def setbit5a(self):
        self.op_set_bit(self.registers['A'], 5)

    def setbit5b(self):
        self.op_set_bit(self.registers['B'], 5)

    def setbit5c(self):
        self.op_set_bit(self.registers['C'], 5)

    def setbit5d(self):
        self.op_set_bit(self.registers['D'], 5)

    def setbit5e(self):
        self.op_set_bit(self.registers['E'], 5)

    def setbit5h(self):
        self.op_set_bit(self.registers['H'], 5)

    def setbit5l(self):
        self.op_set_bit(self.registers['L'], 5)

    def setbit5hl(self):
        self.op_set_bit_hl(5)

    def setbit6a(self):
        self.op_set_bit(self.registers['A'], 6)

    def setbit6b(self):
        self.op_set_bit(self.registers['B'], 6)

    def setbit6c(self):
        self.op_set_bit(self.registers['C'], 6)

    def setbit6d(self):
        self.op_set_bit(self.registers['D'], 6)

    def setbit6e(self):
        self.op_set_bit(self.registers['E'], 6)

    def setbit6h(self):
        self.op_set_bit(self.registers['H'], 6)

    def setbit6l(self):
        self.op_set_bit(self.registers['L'], 6)

    def setbit6hl(self):
        self.op_set_bit_hl(6)

    def setbit7a(self):
        self.op_set_bit(self.registers['A'], 7)

    def setbit7b(self):
        self.op_set_bit(self.registers['B'], 7)

    def setbit7c(self):
        self.op_set_bit(self.registers['C'], 7)

    def setbit7d(self):
        self.op_set_bit(self.registers['D'], 7)

    def setbit7e(self):
        self.op_set_bit(self.registers['E'], 7)

    def setbit7h(self):
        self.op_set_bit(self.registers['H'], 7)

    def setbit7l(self):
        self.op_set_bit(self.registers['L'], 7)

    def setbit7hl(self):
        self.op_set_bit_hl(7)

    def resbit0a(self):
        self.op_reset_bit(self.registers['A'], 0)

    def resbit0b(self):
        self.op_reset_bit(self.registers['B'], 0)

    def resbit0c(self):
        self.op_reset_bit(self.registers['C'], 0)

    def resbit0d(self):
        self.op_reset_bit(self.registers['D'], 0)

    def resbit0e(self):
        self.op_reset_bit(self.registers['E'], 0)

    def resbit0h(self):
        self.op_reset_bit(self.registers['H'], 0)

    def resbit0l(self):
        self.op_reset_bit(self.registers['L'], 0)

    def resbit0hl(self):
        self.op_reset_bit_hl(0)

    def resbit1a(self):
        self.op_reset_bit(self.registers['A'], 1)

    def resbit1b(self):
        self.op_reset_bit(self.registers['B'], 1)

    def resbit1c(self):
        self.op_reset_bit(self.registers['C'], 1)

    def resbit1d(self):
        self.op_reset_bit(self.registers['D'], 1)

    def resbit1e(self):
        self.op_reset_bit(self.registers['E'], 1)

    def resbit1h(self):
        self.op_reset_bit(self.registers['H'], 1)

    def resbit1l(self):
        self.op_reset_bit(self.registers['L'], 1)

    def resbit1hl(self):
        self.op_reset_bit_hl(1)

    def resbit2a(self):
        self.op_reset_bit(self.registers['A'], 2)

    def resbit2b(self):
        self.op_reset_bit(self.registers['B'], 2)

    def resbit2c(self):
        self.op_reset_bit(self.registers['C'], 2)

    def resbit2d(self):
        self.op_reset_bit(self.registers['D'], 2)

    def resbit2e(self):
        self.op_reset_bit(self.registers['E'], 2)

    def resbit2h(self):
        self.op_reset_bit(self.registers['H'], 2)

    def resbit2l(self):
        self.op_reset_bit(self.registers['L'], 2)

    def resbit2hl(self):
        self.op_reset_bit_hl(2)

    def resbit3a(self):
        self.op_reset_bit(self.registers['A'], 3)

    def resbit3b(self):
        self.op_reset_bit(self.registers['B'], 3)

    def resbit3c(self):
        self.op_reset_bit(self.registers['C'], 3)

    def resbit3d(self):
        self.op_reset_bit(self.registers['D'], 3)

    def resbit3e(self):
        self.op_reset_bit(self.registers['E'], 3)

    def resbit3h(self):
        self.op_reset_bit(self.registers['H'], 3)

    def resbit3l(self):
        self.op_reset_bit(self.registers['L'], 3)

    def resbit3hl(self):
        self.op_reset_bit_hl(3)

    def resbit4a(self):
        self.op_reset_bit(self.registers['A'], 4)

    def resbit4b(self):
        self.op_reset_bit(self.registers['B'], 4)

    def resbit4c(self):
        self.op_reset_bit(self.registers['C'], 4)

    def resbit4d(self):
        self.op_reset_bit(self.registers['D'], 4)

    def resbit4e(self):
        self.op_reset_bit(self.registers['E'], 4)

    def resbit4h(self):
        self.op_reset_bit(self.registers['H'], 4)

    def resbit4l(self):
        self.op_reset_bit(self.registers['L'], 4)

    def resbit4hl(self):
        self.op_reset_bit_hl(4)

    def resbit5a(self):
        self.op_reset_bit(self.registers['A'], 5)

    def resbit5b(self):
        self.op_reset_bit(self.registers['B'], 5)

    def resbit5c(self):
        self.op_reset_bit(self.registers['C'], 5)

    def resbit5d(self):
        self.op_reset_bit(self.registers['D'], 5)

    def resbit5e(self):
        self.op_reset_bit(self.registers['E'], 5)

    def resbit5h(self):
        self.op_reset_bit(self.registers['H'], 5)

    def resbit5l(self):
        self.op_reset_bit(self.registers['L'], 5)

    def resbit5hl(self):
        self.op_reset_bit_hl(5)

    def resbit6a(self):
        self.op_reset_bit(self.registers['A'], 6)

    def resbit6b(self):
        self.op_reset_bit(self.registers['B'], 6)

    def resbit6c(self):
        self.op_reset_bit(self.registers['C'], 6)

    def resbit6d(self):
        self.op_reset_bit(self.registers['D'], 6)

    def resbit6e(self):
        self.op_reset_bit(self.registers['E'], 6)

    def resbit6h(self):
        self.op_reset_bit(self.registers['H'], 6)

    def resbit6l(self):
        self.op_reset_bit(self.registers['L'], 6)

    def resbit6hl(self):
        self.op_reset_bit_hl(6)

    def resbit7a(self):
        self.op_reset_bit(self.registers['A'], 7)

    def resbit7b(self):
        self.op_reset_bit(self.registers['B'], 7)

    def resbit7c(self):
        self.op_reset_bit(self.registers['C'], 7)

    def resbit7d(self):
        self.op_reset_bit(self.registers['D'], 7)

    def resbit7e(self):
        self.op_reset_bit(self.registers['E'], 7)

    def resbit7h(self):
        self.op_reset_bit(self.registers['H'], 7)

    def resbit7l(self):
        self.op_reset_bit(self.registers['L'], 7)

    def resbit7hl(self):
        self.op_reset_bit_hl(7)

    # No operation
    def nop(self):
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # PUSH nn
    # Push register pair nn onto stack. Decrement Stack Pointer (SP) twice.
    # Use with: nn = AF,BC,DE,HL
    def pushaf(self):
        self.op_pushnn('A', 'F')

    def pushbc(self):
        self.op_pushnn('B', 'C')

    def pushde(self):
        self.op_pushnn('D', 'E')

    def pushhl(self):
        self.op_pushnn('H', 'L')

    # POP nn
    # Pop two bytes off stack into register pair nn. Increment Stack Pointer (SP) twice.
    # Use with: nn = AF,BC,DE,HL
    def popaf(self):
        self.op_popnn('A', 'F')

    def popbc(self):
        self.op_popnn('B', 'C')

    def popde(self):
        self.op_popnn('D', 'E')

    def pophl(self):
        self.op_popnn('H', 'L')

    # LD n,nn
    # Put value nn into n
    # Use with:
    #   n = BC,DE,HL,SP
    #   nn = 16 bit immediate value
    def ldnnn(self):
        addr = self.MMU.rw(self.registers['PC']) # Get address from instr
        self.registers['PC'] += 2 # Advance PC
        self.registers['A'] = self.MMU.rb(addr) # Read from address
        self.registers['M'] = 3  # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken

    # LD n,nn
    # Put value nn into n
    # Use with:
    #   n = BC,DE,HL,SP
    #   nn = 16 bit immediate value
    def ldbcnn(self):
        self.registers['C'] = self.MMU.rb(self.registers['PC']) # Read from address
        self.registers['B'] = self.MMU.rb(self.registers['PC']+1) # Read from address
        self.registers['PC'] += 2 # Advance PC
        self.registers['M'] = 3  # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken

    # LD n,nn
    # Put value nn into n
    # Use with:
    #   n = BC,DE,HL,SP
    #   nn = 16 bit immediate value
    def lddenn(self):
        self.registers['E'] = self.MMU.rb(self.registers['PC']) # Read from address
        self.registers['D'] = self.MMU.rb(self.registers['PC']+1) # Read from address
        self.registers['PC'] += 2 # Advance PC
        self.registers['M'] = 3  # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken

    # LD n,nn
    # Put value nn into n
    # Use with:
    #   n = BC,DE,HL,SP
    #   nn = 16 bit immediate value
    def ldhlnn(self):
        self.registers['L'] = self.MMU.rb(self.registers['PC']) # Read from address
        self.registers['H'] = self.MMU.rb(self.registers['PC']+1) # Read from address
        self.registers['PC'] += 2 # Advance PC
        self.registers['M'] = 3  # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken

    # LD n,nn
    # Put value nn into n
    # Use with:
    #   n = BC,DE,HL,SP
    #   nn = 16 bit immediate value
    def ldspnn(self):
        self.registers['SP'] = self.MMU.rw(self.registers['PC']) # Read from address
        self.registers['PC'] += 2 # Advance PC
        self.registers['M'] = 3  # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken

    # LD A,(HL-)
    # Put value at address HL into A
    # Decrement HL
    def ldahlminus(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        self.registers['A']= self.MMU.rb(addr) # Put value at address HL into A
        addr -= 1 # Decrement HL.
        self.registers['H'] = addr >> 8
        self.registers['L'] = addr & 0x00FF
        self.registers['M'] = 2  # 8 M-time taken
        self.registers['T'] = 8  # 8 M-time taken

    # LD (HL-),A
    # Put A into memory address HL
    # Decrement HL
    def ldhlminusa(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        self.MMU.wb(addr, self.registers['A']) # Put A into memory address HL
        addr -= 1 # Decrement HL.
        self.registers['H'] = addr >> 8
        self.registers['L'] = addr & 0x00FF
        self.registers['M'] = 2  # 8 M-time taken
        self.registers['T'] = 8  # 8 M-time taken

    # LD A,(HL+)
    # Put value at address HL into A
    # Increment HL
    def ldahlplus(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        self.registers['A']= self.MMU.rb(addr) # Put value at address HL into A
        addr += 1 # Increment HL.
        self.registers['H'] = addr >> 8
        self.registers['L'] = addr & 0x00FF
        self.registers['M'] = 2  # 8 M-time taken
        self.registers['T'] = 8  # 8 M-time taken

    # LD (HL+),A
    # Put A into memory address HL
    # Increment HL
    def ldhlplusa(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        self.MMU.wb(addr, self.registers['A']) # Put A into memory address HL
        addr += 1 # Increment HL.
        self.registers['H'] = addr >> 8
        self.registers['L'] = addr & 0x00FF
        self.registers['M'] = 2  # 8 M-time taken
        self.registers['T'] = 8  # 8 M-time taken

    # LD A,n
    # Put value n into A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(BC),(DE),(HL),(nn),#
    #   nn = two byte immediate value. (LS byte first.)
    def ldad8(self):
        self.registers['A'] = self.MMU.rb(self.registers['PC']) # Get address from instr
        self.registers['PC'] += 1 # Advance PC
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD nn,n
    # Put value nn into n.
    # Use with:
    #   n = B,C,D,E,H,L,BC,DE,HL,SP
    #   nn = 8 bit immediate value
    def ldbd8(self):
        self.registers['B'] = self.MMU.rb(self.registers['PC']) # Get address from instr
        self.registers['PC'] += 1 # Advance PC
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD nn,n
    # Put value nn into n.
    # Use with:
    #   n = B,C,D,E,H,L,BC,DE,HL,SP
    #   nn = 8 bit immediate value
    def ldcd8(self):
        self.registers['C'] = self.MMU.rb(self.registers['PC']) # Get address from instr
        self.registers['PC'] += 1 # Advance PC
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD nn,n
    # Put value nn into n.
    # Use with:
    #   n = B,C,D,E,H,L,BC,DE,HL,SP
    #   nn = 8 bit immediate value
    def lddd8(self):
        self.registers['D'] = self.MMU.rb(self.registers['PC']) # Get address from instr
        self.registers['PC'] += 1 # Advance PC
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD nn,n
    # Put value nn into n.
    # Use with:
    #   n = B,C,D,E,H,L,BC,DE,HL,SP
    #   nn = 8 bit immediate value
    def lded8(self):
        self.registers['E'] = self.MMU.rb(self.registers['PC']) # Get address from instr
        self.registers['PC'] += 1 # Advance PC
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD nn,n
    # Put value nn into n.
    # Use with:
    #   n = B,C,D,E,H,L,BC,DE,HL,SP
    #   nn = 8 bit immediate value
    def ldhd8(self):
        self.registers['H'] = self.MMU.rb(self.registers['PC']) # Get address from instr
        self.registers['PC'] += 1 # Advance PC
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD nn,n
    # Put value nn into n.
    # Use with:
    #   n = B,C,D,E,H,L,BC,DE,HL,SP
    #   nn = 8 bit immediate value
    def ldld8(self):
        self.registers['L'] = self.MMU.rb(self.registers['PC']) # Get address from instr
        self.registers['PC'] += 1 # Advance PC
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD (C),A
    # Put A into address $FF00 + register C
    def ldff00ca(self):
        addr = 0xFF00 + self.registers['C']
        self.MMU.wb(addr, self.registers['A'])
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD A,(C) = LD A,($FF00+C)
    # Put value at address $FF00 + register C into A
    def ldaff00c(self):
        addr = 0xFF00 + self.registers['C']
        self.registers['A'] = self.MMU.rb(addr)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD (FF00+n),A
    # Put A into address $FF00 + n
    def ldff00na(self):
        n = self.MMU.rb(self.registers['PC'])
        self.registers['PC'] += 1
        addr = 0xFF00 + n
        self.MMU.wb(addr, self.registers['A'])
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD A,(FF00+n)
    # Put value at address $FF00 + n into A
    def ldaff00n(self):
        n = self.MMU.rb(self.registers['PC'])
        self.registers['PC'] += 1
        addr = 0xFF00 + n
        self.registers['A'] = self.MMU.rb(addr)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD (nn),SP
    # Put Stack Pointer (SP) at address n.
    # Use with:
    #     nn = two byte immediate address.
    def ldnnsp(self):
        addr = self.MMU.rw(self.registers['PC'])
        self.MMU.ww(addr, self.registers['SP'])
        self.registers['PC'] += 2
        self.registers['M'] = 5 # 5 M-time taken
        self.registers['T'] = 20 # 5 M-time taken

    # LD SP,HL
    # Put HL into Stack Pointer (SP).
    def ldsphl(self):
        value = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        self.registers['SP'] = value
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    # LD HL,SP+n
    # Put SP + n effective address into HL.
    # Use with: n = one byte signed immediate value.
    # Flags affected:
    #   Z - Reset.
    #   N - Reset.
    #   H - Set or reset according to operation.
    #   C - Set or reset according to operation.
    def ldhlspplusn(self):
        n = self.MMU.rb(self.registers['PC'])
        self.registers['PC'] += 1
        addr = self.registers['SP'] + n
        carry = utils.half_carry_16_bit(self.registers['SP'], n)
        half_carry = utils.carry_16_bit(self.registers['SP'], n)
        self.ww_16b_register(self.registers['H'], self.registers['L'], addr)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N)
        if half_carry:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H)
        if carry:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C)
        self.registers['M'] = 4 # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    # LD n,A
    # Put value nn into n
    # Use with:
    #   n = A,B,C,D,E,H,L,(BC),(DE),(HL),(nn
    def ldbca(self):
        addr = utils.bytes_to_16(self.registers['B'], self.registers['C'])
        self.MMU.wb(addr, self.registers['A'])
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def lddea(self):
        addr = utils.bytes_to_16(self.registers['D'], self.registers['E'])
        self.MMU.wb(addr, self.registers['A'])
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def ldhla(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        self.MMU.wb(addr, self.registers['A'])
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    def ldnna(self):
        addr = self.MMU.rw(self.registers['PC'])
        self.registers['PC'] += 2
        self.MMU.wb(addr, self.registers['A'])
        self.registers['M'] = 4  # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    # LD r1,r2
    # Put value r2 into r1.
    # Use with:
    #   r1,r2 = A,B,C,D,E,H,L,(HL)
    def ldaa(self):
        self.op_ld_r1r2('A', 'A')

    def ldab(self):
        self.op_ld_r1r2('A', 'B')

    def ldac(self):
        self.op_ld_r1r2('A', 'C')

    def ldad(self):
        self.op_ld_r1r2('A', 'D')

    def ldae(self):
        self.op_ld_r1r2('A', 'E')

    def ldah(self):
        self.op_ld_r1r2('A', 'H')

    def ldal(self):
        self.op_ld_r1r2('A', 'L')

    def ldahl(self):
        self.op_ld_r1hl('A')

    def ldabc(self):
        self.op_ld_r1bc('A')

    def ldade(self):
        self.op_ld_r1de('A')

    def ldann(self):
        self.op_ld_r1nn('A')

    def ldba(self):
        self.op_ld_r1r2('B', 'A')

    def ldbb(self):
        self.op_ld_r1r2('B', 'B')

    def ldbc(self):
        self.op_ld_r1r2('B', 'C')

    def ldbd(self):
        self.op_ld_r1r2('B', 'D')

    def ldbe(self):
        self.op_ld_r1r2('B', 'E')

    def ldbh(self):
        self.op_ld_r1r2('B', 'H')

    def ldbl(self):
        self.op_ld_r1r2('B', 'L')

    def ldbhl(self):
        self.op_ld_r1hl('B')

    def ldca(self):
        self.op_ld_r1r2('C', 'A')

    def ldcb(self):
        self.op_ld_r1r2('C', 'B')

    def ldcc(self):
        self.op_ld_r1r2('C', 'C')

    def ldcd(self):
        self.op_ld_r1r2('C', 'D')

    def ldce(self):
        self.op_ld_r1r2('C', 'E')

    def ldch(self):
        self.op_ld_r1r2('C', 'H')

    def ldcl(self):
        self.op_ld_r1r2('C', 'L')

    def ldchl(self):
        self.op_ld_r1hl('C')

    def ldda(self):
        self.op_ld_r1r2('D', 'A')

    def lddb(self):
        self.op_ld_r1r2('D', 'B')

    def lddc(self):
        self.op_ld_r1r2('D', 'C')

    def lddd(self):
        self.op_ld_r1r2('D', 'D')

    def ldde(self):
        self.op_ld_r1r2('D', 'E')

    def lddh(self):
        self.op_ld_r1r2('D', 'H')

    def lddl(self):
        self.op_ld_r1r2('D', 'L')

    def lddhl(self):
        self.op_ld_r1hl('D')

    def ldea(self):
        self.op_ld_r1r2('E', 'A')

    def ldeb(self):
        self.op_ld_r1r2('E', 'B')

    def ldec(self):
        self.op_ld_r1r2('E', 'C')

    def lded(self):
        self.op_ld_r1r2('E', 'D')

    def ldee(self):
        self.op_ld_r1r2('E', 'E')

    def ldeh(self):
        self.op_ld_r1r2('E', 'H')

    def ldel(self):
        self.op_ld_r1r2('E', 'L')

    def ldehl(self):
        self.op_ld_r1hl('E')

    def ldha(self):
        self.op_ld_r1r2('H', 'A')

    def ldhb(self):
        self.op_ld_r1r2('H', 'B')

    def ldhc(self):
        self.op_ld_r1r2('H', 'C')

    def ldhd(self):
        self.op_ld_r1r2('H', 'D')

    def ldhe(self):
        self.op_ld_r1r2('H', 'E')

    def ldhh(self):
        self.op_ld_r1r2('H', 'H')

    def ldhl(self):
        self.op_ld_r1r2('H', 'L')

    def ldhhl(self):
        self.op_ld_r1hl('H')

    def ldla(self):
        self.op_ld_r1r2('L', 'A')

    def ldlb(self):
        self.op_ld_r1r2('L', 'B')

    def ldlc(self):
        self.op_ld_r1r2('L', 'C')

    def ldld(self):
        self.op_ld_r1r2('L', 'D')

    def ldle(self):
        self.op_ld_r1r2('L', 'E')

    def ldlh(self):
        self.op_ld_r1r2('L', 'H')

    def ldll(self):
        self.op_ld_r1r2('L', 'L')

    def ldlhl(self):
        self.op_ld_r1hl('L')

    def ldhla(self):
        self.op_ld_hlr2('A')

    def ldhlb(self):
        self.op_ld_hlr2('B')

    def ldhlc(self):
        self.op_ld_hlr2('C')

    def ldhld(self):
        self.op_ld_hlr2('D')

    def ldhle(self):
        self.op_ld_hlr2('E')

    def ldhlh(self):
        self.op_ld_hlr2('H')

    def ldhll(self):
        self.op_ld_hlr2('L')

    def ldhln(self):
        addr = utils.bytes_to_16(self.registers['H'], self.registers['L'])
        n = self.MMU.rb(self.registers['PC'])
        self.registers['PC'] += 1
        self.MMU.wb(addr, n)
        self.registers['M'] = 3 # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken

    # Increment register n.
    # Put value nn into n.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero
    #   N - Reset.
    #   H - Set if carry from bit 3.
    #   C - Not affected.
    def inca(self):
        self.op_inc('A')

    def incb(self):
        self.op_inc('B')

    def incc(self):
        self.op_inc('C')

    def incd(self):
        self.op_inc('D')

    def ince(self):
        self.op_inc('E')

    def inch(self):
        self.op_inc('H')

    def incl(self):
        self.op_inc('L')

    def inchlm(self):
        self.op_inc_hl()

    # Increment register nn.
    # Put value nn into n.
    # Use with:
    #   nn = BC,DE,HL,SP
    # Flags affected:
    #   None
    def incbc(self):
        self.op_inc_16('B', 'C')

    def incde(self):
        self.op_inc_16('D', 'E')

    def inchl(self):
        self.op_inc_16('H', 'L')

    def incsp(self):
        self.op_inc_16_one_register('SP')

    # JR cc,n
    # If following condition is true then add n to current address and jump to it:
    # Use with:
    #   n = one byte signed immediate value
    #   cc = NZ, Jump if Z flag is reset.
    #   cc = Z, Jump if Z flag is set.
    #   cc = NC, Jump if C flag is reset.
    #   cc = C, Jump if C flag is set.
    def jrnz(self):
        param = utils.signed_8b(self.MMU.rb(self.registers['PC']))
        self.registers['PC'] += 1
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken
        if not utils.test_bit(self.registers['F'], self.FLAG_Z):
            self.registers['PC'] += param
            self.registers['PC'] &= 0xFFFF
            self.registers['M'] += 1 # 1 extra M-time taken
            self.registers['T'] += 4 # 1 extra M-time taken

    # JR cc,n
    # If following condition is true then add n to current address and jump to it:
    # Use with:
    #   n = one byte signed immediate value
    #   cc = NZ, Jump if Z flag is reset.
    #   cc = Z, Jump if Z flag is set.
    #   cc = NC, Jump if C flag is reset.
    #   cc = C, Jump if C flag is set.
    def jrz(self):
        param = utils.signed_8b(self.MMU.rb(self.registers['PC']))
        self.registers['PC'] += 1
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken
        if utils.test_bit(self.registers['F'], self.FLAG_Z):
            self.registers['PC'] += param
            self.registers['PC'] &= 0xFFFF
            self.registers['M'] += 1 # 1 extra M-time taken
            self.registers['T'] += 4 # 1 extra M-time taken

    # JR cc,n
    # If following condition is true then add n to current address and jump to it:
    # Use with:
    #   n = one byte signed immediate value
    #   cc = NZ, Jump if Z flag is reset.
    #   cc = Z, Jump if Z flag is set.
    #   cc = NC, Jump if C flag is reset.
    #   cc = C, Jump if C flag is set.
    def jrnc(self):
        param = self.MMU.rb(self.registers['PC'])
        self.registers['PC'] += 1
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken
        if not utils.test_bit(self.registers['F'], self.FLAG_C):
            self.registers['PC'] += param
            self.registers['M'] += 1 # 1 extra M-time taken
            self.registers['T'] += 4 # 1 extra M-time taken

    # JR cc,n
    # If following condition is true then add n to current address and jump to it:
    # Use with:
    #   n = one byte signed immediate value
    #   cc = NZ, Jump if Z flag is reset.
    #   cc = Z, Jump if Z flag is set.
    #   cc = NC, Jump if C flag is reset.
    #   cc = C, Jump if C flag is set.
    def jrc(self):
        param = utils.signed_8b(self.MMU.rb(self.registers['PC']))
        self.registers['PC'] += 1
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken
        if utils.test_bit(self.registers['F'], self.FLAG_C):
            self.registers['PC'] += param
            self.registers['M'] += 1 # 1 extra M-time taken
            self.registers['T'] += 4 # 1 extra M-time taken

    # JR n
    # Add n to current address and jump to it.
    # Use with:
    #   n = one byte signed immediate value
    def jrr8(self):
        param = utils.signed_8b(self.MMU.rb(self.registers['PC']))
        self.registers['PC'] += 1
        self.registers['PC'] += param
        self.registers['PC'] &= 0xFFFF
        self.registers['M'] = 3 # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken

    # JP nn
    # Jump to address nn
    # Use with:
    #   nn = two byte immediate value. (LS byte first.)
    def jpnn(self):
        param = self.MMU.rw(self.registers['PC'])
        self.registers['PC'] += 2
        self.registers['PC'] = param
        self.registers['PC'] &= 0xFFFF
        self.registers['M'] = 3 # 3 M-time taken
        self.registers['T'] = 12 # 12 M-time taken

    # JP cc,nn
    # Jump to address n if following condition is true:
    #   cc = NZ, Jump if Z flag is reset.
    #   cc = Z, Jump if Z flag is set.
    #   cc = NC, Jump if C flag is reset.
    #   cc = C, Jump if C flag is set.
    # Use with:
    #   nn = two byte immediate value. (LS byte first.)
    def jpnznn(self):
        param = self.MMU.rw(self.registers['PC'])
        self.registers['PC'] += 2
        self.registers['M'] = 3 # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken
        if not utils.get_bit(self.registers['F'], self.FLAG_Z):
            self.registers['PC'] = param
            self.registers['M'] = 1 # 1 M-time taken
            self.registers['T'] = 4 # 1 M-time taken

    def jpznn(self):
        param = self.MMU.rw(self.registers['PC'])
        self.registers['PC'] += 2
        self.registers['M'] = 3 # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken
        if utils.get_bit(self.registers['F'], self.FLAG_Z):
            self.registers['PC'] = param
            self.registers['M'] += 1 # 1 M-time taken
            self.registers['T'] += 4 # 1 M-time taken

    def jpncnn(self):
        param = self.MMU.rw(self.registers['PC'])
        self.registers['PC'] += 2
        self.registers['M'] = 3 # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken
        if not utils.get_bit(self.registers['F'], self.FLAG_C):
            self.registers['PC'] = param
            self.registers['M'] += 1 # 1 M-time taken
            self.registers['T'] += 4 # 1 M-time taken

    def jpcnn(self):
        param = self.MMU.rw(self.registers['PC'])
        self.registers['PC'] += 2
        self.registers['M'] = 3 # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken
        if utils.get_bit(self.registers['F'], self.FLAG_C):
            self.registers['PC'] = param
            self.registers['M'] += 1 # 1 M-time taken
            self.registers['T'] += 4 # 1 M-time taken

    # JP (HL)
    # Jump to address contained in HL.
    def jphlm(self):
        param = self.rw_16b_register('H', 'L')
        self.registers['PC'] = param
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # DEC n
    # Decrement register n.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Set.
    #   H - Set if no borrow from bit 4.
    #   C - Not affected.
    def deca(self):
        self.op_dec('A')

    def decb(self):
        self.op_dec('B')

    def decc(self):
        self.op_dec('C')

    def decd(self):
        self.op_dec('D')

    def dece(self):
        self.op_dec('E')

    def dech(self):
        self.op_dec('H')

    def decl(self):
        self.op_dec('L')

    def dechlm(self):
        self.op_dec_hl()

    # DEC nn
    # Decrement register nn.
    # Use with:
    #   nn = BC,DE,HL,SP
    # Flags affected:
    #   None.
    def decbc(self):
        self.op_dec_16('B', 'C')

    def decde(self):
        self.op_dec_16('D', 'E')

    def dechl(self):
        self.op_dec_16('H', 'L')

    def decsp(self):
        self.op_dec_sp()

    # CP n
    # Compare A with n. This is basically an A - n
    # subtraction instruction but the results are thrown away.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Set.
    #   H - Set if no borrow from bit 4.
    #   C - Not affected.
    def cpa(self):
        self.op_cp_an(self.registers['A'])

    def cpb(self):
        self.op_cp_an(self.registers['B'])

    def cpc(self):
        self.op_cp_an(self.registers['C'])

    def cpd(self):
        self.op_cp_an(self.registers['D'])

    def cpe(self):
        self.op_cp_an(self.registers['E'])

    def cph(self):
        self.op_cp_an(self.registers['H'])

    def cpl(self):
        self.op_cp_an(self.registers['L'])

    def cphl(self):
        value = self.MMU.rb(utils.bytes_to_16(self.registers['H'],
            self.registers['L']))
        self.op_cp_an(value)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    def cpn(self):
        value = self.MMU.rb(self.registers['PC'])
        self.registers['PC'] += 1
        self.op_cp_an(value)
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    # RLC A
    # Rotate A left. Old bit 7 to Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 7 data
    def rlca(self):
        self.op_rlc_register('A')
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # RLC n
    # Rotate n left. Old bit 7 to Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 7 data
    def rlca(self):
        self.op_rlc_register('A')

    def rlcb(self):
        self.op_rlc_register('B')

    def rlcc(self):
        self.op_rlc_register('C')

    def rlcd(self):
        self.op_rlc_register('D')

    def rlce(self):
        self.op_rlc_register('E')

    def rlch(self):
        self.op_rlc_register('H')

    def rlcl(self):
        self.op_rlc_register('L')

    def rlchl(self):
        value = self.rb_16b_register('H', 'L')
        value = self.op_rlc_common(value)
        self.wb_16b_register('H', 'L', value)
        self.registers['M'] = 4 # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    # RLA
    # Rotate A left through Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 7 data
    def rla(self):
        self.op_rla()
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # RL n
    # Rotate n left through Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 7 data
    def rlna(self):
        self.op_rl_register('A')

    def rlnb(self):
        self.op_rl_register('B')

    def rlnc(self):
        self.op_rl_register('C')

    def rlnd(self):
        self.op_rl_register('D')

    def rlne(self):
        self.op_rl_register('E')

    def rlnh(self):
        self.op_rl_register('H')

    def rlnl(self):
        self.op_rl_register('L')

    def rlnhl(self):
        value = self.rb_16b_register('H', 'L')
        value = self.op_rl_common(value)
        self.wb_16b_register('H', 'L', value)
        self.registers['M'] = 4 # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    # RRCA
    # Rotate A right. Old bit 0 to Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C -  Contains old bit 0 data
    def rrca(self):
        self.op_rrc_register['A']
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # RRC n
    # Rotate n right. Old bit 0 to Carry flag.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C -  Contains old bit 0 data
    def rrcna(self):
        self.op_rrc_register['A']

    def rrcnb(self):
        self.op_rrc_register['B']

    def rrcnc(self):
        self.op_rrc_register['C']

    def rrcnd(self):
        self.op_rrc_register['D']

    def rrcne(self):
        self.op_rrc_register['E']

    def rrcnh(self):
        self.op_rrc_register['H']

    def rrcnl(self):
        self.op_rrc_register['L']

    def rrcnhl(self):
        value = self.rb_16b_register('H', 'L')
        value = self.op_rl_common(value)
        self.wb_16b_register('H', 'L', value)
        self.registers['M'] = 4 # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    # RRA
    # Rotate A right through Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 0 data.
    def rra(self):
        self.op_rr_register['A']
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # RR n
    # Rotate n right through Carry flag.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 0 data.
    def rrna(self):
        self.op_rr_register['A']

    def rrnb(self):
        self.op_rr_register['B']

    def rrnc(self):
        self.op_rr_register['C']

    def rrnd(self):
        self.op_rr_register['D']

    def rrne(self):
        self.op_rr_register['E']

    def rrnh(self):
        self.op_rr_register['H']

    def rrnl(self):
        self.op_rr_register['L']

    def rrnhl(self):
        value = self.rb_16b_register('H', 'L')
        value = self.op_rr_common(value)
        self.wb_16b_register('H', 'L', value)
        self.registers['M'] = 4 # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    # SLA n
    # Shift n left into Carry. LSB of n set to 0.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   Contains old bit 7 data.
    def slaa(self):
        self.op_sla_register['A']

    def slab(self):
        self.op_sla_register['B']

    def slac(self):
        self.op_sla_register['C']

    def slad(self):
        self.op_sla_register['D']

    def slae(self):
        self.op_sla_register['E']

    def slah(self):
        self.op_sla_register['H']

    def slal(self):
        self.op_sla_register['L']

    def slahl(self):
        value = self.rb_16b_register('H', 'L')
        value = self.op_sla_common(value)
        self.wb_16b_register('H', 'L', value)
        self.registers['M'] = 4 # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    # SRA n
    # Shift n right into Carry. MSB doesn't change.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 0 data.
    def sraa(self):
        self.op_sra_register['A']

    def srab(self):
        self.op_sra_register['B']

    def srac(self):
        self.op_sra_register['C']

    def srad(self):
        self.op_sra_register['D']

    def srae(self):
        self.op_sra_register['E']

    def srah(self):
        self.op_sra_register['H']

    def sral(self):
        self.op_sra_register['L']

    def srahl(self):
        value = self.rb_16b_register('H', 'L')
        value = self.op_sra_common(value)
        self.wb_16b_register('H', 'L', value)
        self.registers['M'] = 4 # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    # SRL n
    # Shift n right into Carry. MSB set to 0.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 0 data.
    def srla(self):
        self.op_srl_register['A']

    def srlb(self):
        self.op_srl_register['B']

    def srlc(self):
        self.op_srl_register['C']

    def srld(self):
        self.op_srl_register['D']

    def srle(self):
        self.op_srl_register['E']

    def srlh(self):
        self.op_srl_register['H']

    def srll(self):
        self.op_srl_register['L']

    def srlhl(self):
        value = self.rb_16b_register('H', 'L')
        value = self.op_srl_common(value)
        self.wb_16b_register('H', 'L', value)
        self.registers['M'] = 4 # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    # CALL nn
    # Push address of next instruction onto stack and then jump to address nn.
    # Use with:
    #   nn = two byte immediate value. (LS byte first.)
    def callnn(self):
        addr = self.MMU.rw(self.registers['PC'])
        self.registers['PC'] += 2
        self.push_16b_on_stack(self.registers['PC']) # Push address of next instruction onto stack
        self.registers['PC'] = addr # jump to address nn
        self.registers['M'] = 3 # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken

    # CALL cc,nn
    # Call address n if following condition is true:
    #   cc = NZ, Call if Z flag is reset.
    #   cc = Z, Call if Z flag is set.
    #   cc = NC, Call if C flag is reset.
    #   cc = C, Call if C flag is set.
    # Use with:
    #   nn = two byte immediate value. (LS byte first.)
    def callnznn(self):
        if not utils.get_bit(self.registers['F'], self.FLAG_Z):
            self.callnn()
            self.registers['M'] = 6
            self.registers['M'] = 24
        else:
            self.registers['PC'] += 2
            self.registers['M'] = 3
            self.registers['T'] = 12

    def callznn(self):
        if utils.get_bit(self.registers['F'], self.FLAG_Z):
            self.callnn()
            self.registers['M'] = 6
            self.registers['T'] = 24
        else:
            self.registers['PC'] += 2
            self.registers['M'] = 3
            self.registers['T'] = 12

    def callncnn(self):
        if not utils.get_bit(self.registers['F'], self.FLAG_C):
            self.callnn()
            self.registers['M'] = 6
            self.registers['T'] = 24
        else:
            self.registers['PC'] += 2
            self.registers['M'] = 3
            self.registers['T'] = 12

    def callcnn(self):
        if utils.get_bit(self.registers['F'], self.FLAG_C):
            self.callnn()
            self.registers['M'] = 6
            self.registers['T'] = 24
        else:
            self.registers['PC'] += 2
            self.registers['M'] = 3
            self.registers['T'] = 12

    def rst00(self):
        self.op_rst(0x00)

    def rst08(self):
        self.op_rst(0x08)

    def rst10(self):
        self.op_rst(0x10)

    def rst18(self):
        self.op_rst(0x18)

    def rst20(self):
        self.op_rst(0x20)

    def rst28(self):
        self.op_rst(0x28)

    def rst30(self):
        self.op_rst(0x30)

    def rst38(self):
        self.op_rst(0x38)

    def ret(self):
        addr = self.pop_16b_from_stack()
        self.registers['PC'] = addr
        self.registers['M'] = 4 # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    def retnz(self):
        if not utils.get_bit(self.registers['F'], self.FLAG_Z):
            self.ret()
            self.registers['M'] = 5 # 5 M-time taken
            self.registers['T'] = 20 # 5 M-time taken
        else:
            self.registers['M'] = 2 # 2 M-time taken
            self.registers['T'] = 8 # 2 M-time taken

    def retz(self):
        if utils.get_bit(self.registers['F'], self.FLAG_Z):
            self.ret()
            self.registers['M'] = 5 # 5 M-time taken
            self.registers['T'] = 20 # 5 M-time taken
        else:
            self.registers['M'] = 2 # 2 M-time taken
            self.registers['T'] = 8 # 2 M-time taken

    def retnc(self):
        if not utils.get_bit(self.registers['F'], self.FLAG_C):
            self.ret()
            self.registers['M'] = 5 # 5 M-time taken
            self.registers['T'] = 20 # 5 M-time taken
        else:
            self.registers['M'] = 2 # 2 M-time taken
            self.registers['T'] = 8 # 2 M-time taken

    def retc(self):
        if utils.get_bit(self.registers['F'], self.FLAG_C):
            self.ret()
            self.registers['M'] = 5 # 5 M-time taken
            self.registers['T'] = 20 # 5 M-time taken
        else:
            self.registers['M'] = 2 # 2 M-time taken
            self.registers['T'] = 8 # 2 M-time taken

    # RETI
    # Pop two bytes from stack & jump to that address then enable interrupts.
    def reti(self):
        self.ret()
        self.interrup_enabled = True

    def swapa(self):
        self.op_swapn('A')

    def swapb(self):
        self.op_swapn('B')

    def swapc(self):
        self.op_swapn('C')

    def swapd(self):
        self.op_swapn('D')

    def swape(self):
        self.op_swapn('E')

    def swaph(self):
        self.op_swapn('H')

    def swapl(self):
        self.op_swapn('L')

    def swaphlm(self):
        self.op_swaphlm()

    # DAA
    # Decimal adjust register A
    # This instruction adjusts register A so that the
    # correct representation of Binary Coded Decimal (BCD) is obtained.
    # https://en.wikipedia.org/wiki/Binary-coded_decimal
    # Flags affected:
    #   Z - Set if register A is zero.
    #   N - Not affected
    #   H - Reset.
    #   C - Set or reset according to operation.
    def daa(self):
        if self.registers['A'] == 0: #  Z - Set if register A is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) # H - Reset.
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # CPL
    # Complement A register. (Flip all bits.)
    # Flags affected:
    #   Z - Not affected
    #   N - Set.
    #   H - Set.
    #   C - Not affected
    def cpl(self):
        self.registers['A'] = utils.flip_bits_8b(self.registers['A'])
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_N) # N - Set.
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H) # H - Set.
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # CCF
    # Complement carry flag.
    # If C flag is set, then reset it.
    # If C flag is reset, then set it.
    # Flags affected:
    #   Z - Not affected.
    #   N - Reset.
    #   H - Reset.
    #   C - Complemented.
    def ccf(self):
        if utils.get_bit(self.registers['F'], self.FLAG_C): # C - Complemented.
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C)
        else:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C)
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H) # H - Reset.
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # SCF
    # Set Carry flag.
    # Flags affected:
    #   Z - Not affected.
    #   N - Reset.
    #   H - Reset.
    #   C - Set.
    def scf(self):
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H) # H - Reset.
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # STOP
    # Halt CPU & LCD display until button pressed.
    def stop(self):
        self.stop_mode = 1
        self.registers['PC'] += 1
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # HALT
    # Power down CPU until an interrupt occurs. Use this
    # when ever possible to reduce energy consumption.
    def halt(self):
        self.halt_mode = 1
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # DI
    # This instruction disables interrupts but not
    # immediately. Interrupts are disabled after
    # instruction after DI is executed.
    def di(self):
        self.interrup_enabled = 0
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # EI
    # Enable interrupts. This intruction enables interrupts
    # immediately. Interrupts are enabled after
    # instruction after EI is executed.
    def ei(self):
        self.interrup_enabled = 1
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    MAP = {
        0x00: nop,
        0x01: ldbcnn,
        0x02: ldbca,
        0x03: incbc,
        0x04: incb,
        0x05: decb,
        0x06: ldbd8,
        0x07: rlca,
        0x08: ldnnsp,
        0x09: addhlbc,
        0x0A: ldabc,
        0x0B: decbc,
        0x0C: incc,
        0x0D: decc,
        0x0E: ldcd8,
        0x0F: rrca,
        0x10: stop,
        0x11: lddenn,
        0x12: lddea,
        0x13: incde,
        0x14: incd,
        0x15: decd,
        0x16: lddd8,
        0x17: rla,
        0x18: jrr8,
        0x19: addhlde,
        0x1A: ldade,
        0x1B: decde,
        0x1C: ince,
        0x1D: dece,
        0x1E: lded8,
        0x1F: rra,
        0x20: jrnz,
        0x21: ldhlnn,
        0x22: ldhlplusa,
        0x23: inchl,
        0x24: inch,
        0x25: dech,
        0x26: ldhd8,
        0x27: daa,
        0x28: jrz,
        0x29: addhlhl,
        0x2A: ldahlplus,
        0x2B: dechl,
        0x2C: incl,
        0x2D: decl,
        0x2E: ldld8,
        0x2F: cpl,
        0x30: jrnc,
        0x31: ldspnn,
        0x32: ldhlminusa,
        0x33: incsp,
        0x34: inchlm,
        0x35: dechlm,
        0x36: ldhln,
        0x37: scf,
        0x38: jrc,
        0x39: addhlsp,
        0x3A: ldahlminus,
        0x3B: decsp,
        0x3D: deca,
        0x3C: inca,
        0x3E: ldad8,
        0x3F: ccf,
        0x40: ldbb,
        0x41: ldbc,
        0x42: ldbd,
        0x43: ldbe,
        0x44: ldbh,
        0x45: ldbl,
        0x46: ldbhl,
        0x47: ldba,
        0x48: ldcb,
        0x49: ldcc,
        0x4A: ldcd,
        0x4B: ldce,
        0x4C: ldch,
        0x4D: ldcl,
        0x4E: ldchl,
        0x4F: ldca,
        0x50: lddb,
        0x51: lddc,
        0x52: lddd,
        0x53: ldde,
        0x54: lddh,
        0x55: lddl,
        0x56: lddhl,
        0x57: ldda,
        0x58: ldeb,
        0x59: ldec,
        0x5A: lded,
        0x5B: ldee,
        0x5C: ldeh,
        0x5D: ldel,
        0x5E: ldehl,
        0x5F: ldea,
        0x60: ldhb,
        0x61: ldhc,
        0x62: ldhd,
        0x63: ldhe,
        0x64: ldhh,
        0x65: ldhl,
        0x66: ldhhl,
        0x67: ldha,
        0x68: ldlb,
        0x69: ldlc,
        0x6A: ldld,
        0x6B: ldle,
        0x6C: ldlh,
        0x6D: ldll,
        0x6E: ldlhl,
        0x6F: ldla,
        0x70: ldhlb,
        0x71: ldhlc,
        0x72: ldhld,
        0x73: ldhle,
        0x74: ldhlh,
        0x75: ldhll,
        0x76: halt,
        0x77: ldhla,
        0x78: ldab,
        0x79: ldac,
        0x7A: ldad,
        0x7B: ldae,
        0x7C: ldah,
        0x7D: ldal,
        0x7E: ldahl,
        0x7F: ldaa,
        0x80: add_ab,
        0x81: add_ac,
        0x82: add_ad,
        0x83: add_ae,
        0x84: add_ah,
        0x85: add_al,
        0x86: add_ahl,
        0x87: add_aa,
        0x88: adc_ab,
        0x89: adc_ac,
        0x8A: adc_ad,
        0x8B: adc_ae,
        0x8C: adc_ah,
        0x8D: adc_al,
        0x8E: adc_ahl,
        0x8F: adc_aa,
        0x90: sub_ab,
        0x91: sub_ac,
        0x92: sub_ad,
        0x93: sub_ae,
        0x94: sub_ah,
        0x95: sub_al,
        0x96: sub_ahl,
        0x97: sub_aa,
        0x98: sbc_ab,
        0x99: sbc_ac,
        0x9A: sbc_ad,
        0x9B: sbc_ae,
        0x9C: sbc_ah,
        0x9D: sbc_al,
        0x9E: sbc_ahl,
        0x9F: sbc_aa,
        0xA0: and_ab,
        0xA1: and_ac,
        0xA2: and_ad,
        0xA3: and_ae,
        0xA4: and_ah,
        0xA5: and_al,
        0xA6: and_ahl,
        0xA7: and_aa,
        0xA8: xor_ab,
        0xA9: xor_ac,
        0xAA: xor_ad,
        0xAB: xor_ae,
        0xAC: xor_ah,
        0xAD: xor_al,
        0xAE: xor_ahl,
        0xAF: xor_aa,
        0xB0: or_ab,
        0xB1: or_ac,
        0xB2: or_ad,
        0xB3: or_ae,
        0xB4: or_ah,
        0xB5: or_al,
        0xB6: or_ahl,
        0xB7: or_aa,
        0xB8: cpb,
        0xB9: cpc,
        0xBA: cpd,
        0xBB: cpe,
        0xBC: cph,
        0xBD: cpl,
        0xBE: cphl,
        0xBF: cpa,
        0xC0: retnz,
        0xC1: popbc,
        0xC2: jpnznn,
        0xC3: jpnn,
        0xC4: callnznn,
        0xC5: pushbc,
        0xC6: add_an,
        0xC7: rst00,
        0xC8: retz,
        0xC9: ret,
        0xCE: adc_an,
        0xCC: callznn,
        0xCD: callnn,
        0xCA: jpznn,
        0xCF: rst08,
        0xD0: retnc,
        0xD1: popde,
        0xD2: jpncnn,
        0xD4: callncnn,
        0xD5: pushde,
        0xD6: sub_an,
        0xD7: rst10,
        0xD8: retc,
        0xDA: jpcnn,
        0xDC: callcnn,
        0xDE: sbc_an,
        0xDF: rst18,
        0xE0: ldff00na,
        0xE1: pophl,
        0xE2: ldff00ca,
        0xE5: pushhl,
        0xE6: and_an,
        0xE7: rst20,
        0xE8: addspn,
        0xE9: jphlm,
        0xEA: ldnna,
        0xEE: xor_an,
        0xEF: rst28,
        0xF0: ldaff00n,
        0xF1: popaf,
        0xF2: ldaff00c,
        0xF3: di,
        0xF5: pushaf,
        0xF6: or_an,
        0xF7: rst30,
        0xF8: ldhlspplusn,
        0xF9: ldsphl,
        0xFA: ldann,
        0xFB: ei,
        0xFE: cpn,
        0xFf: rst38,
    }

    CB_MAP = {
        0x00: rlcb,
        0x01: rlcc,
        0x02: rlcd,
        0x03: rlce,
        0x04: rlch,
        0x05: rlcl,
        0x06: rlchl,
        0x07: rlca,
        0x10: rlnb,
        0x11: rlnc,
        0x12: rlnd,
        0x13: rlne,
        0x14: rlnh,
        0x15: rlnl,
        0x16: rlnhl,
        0x17: rlna,
        0x18: rrnb,
        0x19: rrnc,
        0x1A: rrnd,
        0x1B: rrne,
        0x1C: rrnh,
        0x1D: rrnl,
        0x1E: rrnhl,
        0x1F: rrna,
        0x20: slab,
        0x21: slac,
        0x22: slad,
        0x23: slae,
        0x24: slah,
        0x25: slal,
        0x26: slahl,
        0x27: sraa,
        0x28: srab,
        0x29: srac,
        0x2A: srad,
        0x2B: srae,
        0x2C: srah,
        0x2D: sral,
        0x2E: srahl,
        0x2F: sraa,
        0x30: swapb,
        0x31: swapc,
        0x32: swapd,
        0x33: swape,
        0x34: swaph,
        0x35: swapl,
        0x36: swaphlm,
        0x37: swapa,
        0x38: srab,
        0x39: srac,
        0x3A: srad,
        0x3B: srae,
        0x3C: srah,
        0x3D: sral,
        0x3E: srahl,
        0x3F: sraa,
        0x40: bit0b,
        0x41: bit0c,
        0x42: bit0d,
        0x43: bit0e,
        0x44: bit0h,
        0x45: bit0l,
        0x46: bit0hl,
        0x47: bit0a,
        0x48: bit1b,
        0x49: bit1c,
        0x4A: bit1d,
        0x4B: bit1e,
        0x4C: bit1h,
        0x4D: bit1l,
        0x4E: bit1hl,
        0x4F: bit1a,
        0x50: bit2b,
        0x51: bit2c,
        0x52: bit2d,
        0x53: bit2e,
        0x54: bit2h,
        0x55: bit2l,
        0x56: bit2hl,
        0x57: bit2a,
        0x58: bit3b,
        0x59: bit3c,
        0x5A: bit3d,
        0x5B: bit3e,
        0x5C: bit3h,
        0x5D: bit3l,
        0x5E: bit3hl,
        0x5F: bit3a,
        0x60: bit4b,
        0x61: bit4c,
        0x62: bit4d,
        0x63: bit4e,
        0x64: bit4l,
        0x65: bit4h,
        0x66: bit4hl,
        0x67: bit4a,
        0x68: bit5b,
        0x69: bit5c,
        0x6A: bit5d,
        0x6B: bit5e,
        0x6C: bit5h,
        0x6D: bit5l,
        0x6E: bit5hl,
        0x6F: bit5a,
        0x70: bit6b,
        0x71: bit6c,
        0x72: bit6d,
        0x73: bit6e,
        0x74: bit6h,
        0x75: bit6l,
        0x76: bit6hl,
        0x77: bit6a,
        0x78: bit7b,
        0x79: bit7c,
        0x7A: bit7d,
        0x7B: bit7e,
        0x7C: bit7h,
        0x7D: bit7l,
        0x7E: bit7hl,
        0x7F: bit7a,
        0x80: resbit0b,
        0x81: resbit0c,
        0x82: resbit0d,
        0x83: resbit0e,
        0x84: resbit0h,
        0x85: resbit0l,
        0x86: resbit0hl,
        0x87: resbit0a,
        0x88: resbit1b,
        0x89: resbit1c,
        0x8A: resbit1d,
        0x8B: resbit1e,
        0x8C: resbit1h,
        0x8D: resbit1l,
        0x8E: resbit1hl,
        0x8F: resbit1a,
        0x90: resbit2b,
        0x91: resbit2c,
        0x92: resbit2d,
        0x93: resbit2e,
        0x94: resbit2h,
        0x95: resbit2l,
        0x96: resbit2hl,
        0x97: resbit2a,
        0x98: resbit3b,
        0x99: resbit3c,
        0x9A: resbit3d,
        0x9B: resbit3e,
        0x9C: resbit3h,
        0x9D: resbit3l,
        0x9E: resbit3hl,
        0x9F: resbit3a,
        0xA0: resbit4b,
        0xA1: resbit4c,
        0xA2: resbit4d,
        0xA3: resbit4e,
        0xA4: resbit4h,
        0xA5: resbit4l,
        0xA6: resbit4hl,
        0xA7: resbit4a,
        0xA8: resbit5b,
        0xA9: resbit5c,
        0xAA: resbit5d,
        0xAB: resbit5e,
        0xAC: resbit5h,
        0xAD: resbit5l,
        0xAE: resbit5hl,
        0xAF: resbit5a,
        0xB0: resbit6b,
        0xB1: resbit6c,
        0xB2: resbit6d,
        0xB3: resbit6e,
        0xB4: resbit6h,
        0xB5: resbit6l,
        0xB6: resbit6hl,
        0xB7: resbit6a,
        0xB8: resbit7b,
        0xB9: resbit7c,
        0xBA: resbit7d,
        0xBB: resbit7e,
        0xBC: resbit7h,
        0xBD: resbit7l,
        0xBE: resbit7hl,
        0xBF: resbit7a,
        0xC0: setbit0b,
        0xC1: setbit0c,
        0xC2: setbit0d,
        0xC3: setbit0e,
        0xC4: setbit0h,
        0xC5: setbit0l,
        0xC6: setbit0hl,
        0xC7: setbit0a,
        0xC8: setbit1b,
        0xC9: setbit1c,
        0xCA: setbit1d,
        0xCB: setbit1e,
        0xCC: setbit1h,
        0xCD: setbit1l,
        0xCE: setbit1hl,
        0xCF: setbit1a,
        0xD0: setbit2b,
        0xD1: setbit2c,
        0xD2: setbit2d,
        0xD3: setbit2e,
        0xD4: setbit2h,
        0xD5: setbit2l,
        0xD6: setbit2hl,
        0xD7: setbit2a,
        0xD8: setbit3b,
        0xD9: setbit3c,
        0xDA: setbit3d,
        0xDB: setbit3e,
        0xDC: setbit3h,
        0xDD: setbit3l,
        0xDE: setbit3hl,
        0xDF: setbit3a,
        0xE0: setbit4b,
        0xE1: setbit4c,
        0xE2: setbit4d,
        0xE3: setbit4e,
        0xE4: setbit4h,
        0xE5: setbit4l,
        0xE6: setbit4hl,
        0xE7: setbit4a,
        0xE8: setbit5b,
        0xE9: setbit5c,
        0xEA: setbit5d,
        0xEB: setbit5e,
        0xEC: setbit5h,
        0xED: setbit5l,
        0xEE: setbit5hl,
        0xEF: setbit5a,
        0xF0: setbit6b,
        0xF1: setbit6c,
        0xF2: setbit6d,
        0xF3: setbit6e,
        0xF4: setbit6h,
        0xF5: setbit6l,
        0xF6: setbit6hl,
        0xF7: setbit6a,
        0xF8: setbit7b,
        0xF9: setbit7c,
        0xFA: setbit7d,
        0xFB: setbit7e,
        0xFC: setbit7h,
        0xFD: setbit7l,
        0xFE: setbit7hl,
        0xFF: setbit7a,
    }

    def reset(self):
        self.registers['A'] = 0
        self.registers['B'] = 0
        self.registers['C'] = 0
        self.registers['D'] = 0
        self.registers['E'] = 0
        self.registers['H'] = 0
        self.registers['L'] = 0
        self.registers['F'] = 0

        self.registers['SP'] = 0
        self.registers['PC'] = 0 # Start execution at 0

        self.clock['M'] = 0
        self.clock['T'] = 0

    def dispatcher(self):
        op = self.MMU.rb(self.registers['PC'])      # Fetch instruction
        current_pc = self.registers['PC']
        self.registers['PC'] += 1                   # Increment Program counter
        if op == 0xCB:
            op = self.MMU.rb(self.registers['PC'])  # Fetch CB instruction
            self.registers['PC'] += 1               # Increment Program counter
            self.CB_MAP[op](self)                   # Dispatch
            self.current_op = (0xCB << 8) + op
            self.current_op_name = self.CB_MAP[op].__name__
        else:
            self.MAP[op](self)                      # Dispatch
            self.current_op = op
            self.current_op_name = self.MAP[op].__name__
        print(hex(current_pc), hex(op), self.current_op_name)
        self.registers['PC'] &= 0xFFFF              # Mask PC to 16 bits
        self.clock['T'] += self.registers['T']      # Add time to CPU clock
        self.clock['M'] += self.registers['M']

        frame_number = self.GPU.ppu_step()
        return current_pc, op, frame_number

    def load_rom(self, filename):
        self.MMU.load(filename)
