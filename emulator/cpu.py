
from emulator.mmu import MMU
from emulator import utils

class Z80():
    # Flags
    # 7 6 5 4 3 2 1 0
    # Z N H C 0 0 0 0
    FLAG_Z = 7
    FLAG_N = 6
    FLAG_H = 5
    FLAG_C = 4

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

    def __init__(self):
        self.MMU = MMU(self)

    # Add n to A.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Set if carry from bit 3.
    #   C - Set if carry from bit 7.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    def add_an(self, register):
        self.registers['A'] += self.registers[register]
        self.registers['F'] = 0 # Clear flags
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        if self.registers['A'] > 255: # C - Set if carry from bit 7.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C)
        self.registers['A'] &= 255 # Mask to 8-bits
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    def add_ab(self):
        add_an('B')

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

    def op_inc(self, register):
        self.registers[register] += 1
        self.registers[register] &= 255
        if self.registers[register] == 0: # Z - Set if bit b of register r is 0.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z) # Z -  Set if result is zero.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H) # H - Set.
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    def op_inc_16(self, register_high, register_low):
        self.registers[register] += 1
        self.registers[register] &= 255
        if self.registers[register] == 0: # Z - Set if bit b of register r is 0.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z) # Z -  Set if result is zero.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) # N - Reset.
        self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_H) # H - Set.
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    def op_dec(self, register):
        self.registers[register] -= 1
        self.registers[register] &= 255
        if self.registers[register] == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
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
        self.registers[register_high] = value >> 8
        self.registers[register_low] = value & 0xFF
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 8 M-time taken

    def op_dec_sp(self):
        self.registers['SP'] -= 1
        self.registers['SP'] &= 0xFFFF
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

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

    # Use with: n = A,B,C,D,E,H,L,(HL)

    # Compare A with n. This is basically an A - n
    # subtraction instruction but the results are thrown away.
    # Use with: n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero. (Set if A = n.)
    #   N - Set. Substraction flag
    #   H - Set if no borrow from bit 4.
    #   C - Set for no borrow. (Set if A < n.)
    def cp_an(self, register):
        result = self.registers['A'] - self.registers[register]
        self.registers['F'] = 0 # Clear flags
        self.registers['F'] |= 0x40 # N - Set. Substraction flag
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] |= 0x80
        if self.registers['A'] < self.registers[register]: # C - Set for no borrow. (Set if A < n.)
            self.registers['F'] |= 0x10
        if self.registers['A'] < 0: # C - Set for no borrow. (Set if A < n.)
            self.registers['F'] |= 0x10
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # No operation
    def nop(self):
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # PUSH nn
    # Push register pair nn onto stack. Decrement Stack Pointer (SP) twice.
    # Use with: nn = AF,BC,DE,HL
    def pushnn(self, register1, register2):
        self.registers['SP'] -= 1 # Decrement Stack Pointer (SP)
        self.MMU.wb(self.registers['SP'], self.registers[register1])
        self.registers['SP'] -= 1 # Decrement Stack Pointer (SP)
        self.MMU.wb(self.registers['SP'], self.registers[register2])
        self.registers['M'] = 4  # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

    # POP nn
    # Pop two bytes off stack into register pair nn. Increment Stack Pointer (SP) twice.
    # Use with: nn = AF,BC,DE,HL
    def popnn(self, register1, register2):
        self.registers[register2] = self.MMU.rb(self.registers['SP'])
        self.registers['SP'] += 1 # Increment Stack Pointer (SP)
        self.registers[register1] = self.MMU.rb(self.registers['SP'])
        self.registers['SP'] += 1 # Increment Stack Pointer (SP)
        self.registers['M'] = 3  # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken

    # LD A,n
    # Put value n into A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(BC),(DE),(HL),(nn)
    #   nn = two byte immediate value. (LS byte first.)
    def LDAnn(self):
        addr = self.MMU.rw(self.registers['PC']) # Get address from instr
        self.registers['PC'] += 2 # Advance PC
        self.registers['A'] = self.MMU.rb(addr) # Read from address
        self.registers['M'] = 4  # 4 M-time taken
        self.registers['T'] = 16 # 4 M-time taken

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

    # LD (HL-),A
    # Put A into memory address HL
    # Decrement HL
    def ldhlminusa(self):
        addr = (self.registers['H'] << 8) + self.registers['L']
        self.MMU.wb(addr, self.registers['A']) # Put A into memory address HL
        addr -= 1
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
    def ldca(self):
        addr = 0xFF00 + self.registers['C']
        self.MMU.wb(addr, self.registers['A'])
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD (HL),A
    # Put value A into n.
    def ldhla(self):
        addr = (self.registers['H'] << 8) + self.registers['L']
        self.MMU.wb(addr, self.registers['A'])
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken

    # LD (nn),SP
    # Put Stack Pointer (SP) at address n.
    # Use with:
    #     nn = two byte immediate address.
    def lda16sp(self):
        addr = self.MMU.rw(self.registers['PC'])
        self.MMU.ww(addr, self.registers['SP'])
        self.registers['PC'] += 2
        self.registers['M'] = 5 # 5 M-time taken
        self.registers['T'] = 20 # 5 M-time taken

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

    # Increment register n.
    # Put value nn into n.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL)
    # Flags affected:
    #   Z - Set if result is zero
    #   N - Reset.
    #   H - Set if carry from bit 3.
    #   C - Not affected.
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
        self.op_inc_16('S', 'P')

    # JR cc,n
    # If following condition is true then add n to current address and jump to it:
    # Use with:
    #   n = one byte signed immediate value
    #   cc = NZ, Jump if Z flag is reset.
    #   cc = Z, Jump if Z flag is set.
    #   cc = NC, Jump if C flag is reset.
    #   cc = C, Jump if C flag is set.
    def jrnz(self):
        param = self.MMU.rb(self.registers['PC'])
        self.registers['PC'] += 1
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken
        if not utils.test_bit(self.registers['F'], self.FLAG_Z):
            self.registers['PC'] += param
            self.registers['PC'] &= 255
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
        param = self.MMU.rb(self.registers['PC'])
        self.registers['PC'] += 1
        self.registers['M'] = 2 # 2 M-time taken
        self.registers['T'] = 8 # 2 M-time taken
        if utils.test_bit(self.registers['F'], self.FLAG_Z):
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
        param = self.MMU.rb(self.registers['PC'])
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
        param = self.MMU.rb(self.registers['PC'])
        self.registers['PC'] += 1
        self.registers['PC'] += param
        self.registers['M'] = 3 # 3 M-time taken
        self.registers['T'] = 12 # 3 M-time taken

    # XOR n
    # Logical exclusive OR n with register A, result in A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Reset.
    def xora(self):
        self.registers['A'] = utils.bitwise_xor(self.registers['A'], self.registers['A'])
        self.registers['F'] =0 # Clear flags
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] |= 0x80
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # XOR n
    # Logical exclusive OR n with register A, result in A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Reset.
    def xorb(self):
        self.registers['A'] = utils.bitwise_xor(self.registers['A'], self.registers['B'])
        self.registers['F'] =0 # Clear flags
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] |= 0x80
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # XOR n
    # Logical exclusive OR n with register A, result in A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Reset.
    def xorc(self):
        self.registers['A'] = utils.bitwise_xor(self.registers['A'], self.registers['C'])
        self.registers['F'] =0 # Clear flags
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] |= 0x80
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # XOR n
    # Logical exclusive OR n with register A, result in A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Reset.
    def xord(self):
        self.registers['A'] = utils.bitwise_xor(self.registers['A'], self.registers['D'])
        self.registers['F'] =0 # Clear flags
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] |= 0x80
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # XOR n
    # Logical exclusive OR n with register A, result in A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Reset.
    def xore(self):
        self.registers['A'] = utils.bitwise_xor(self.registers['A'], self.registers['E'])
        self.registers['F'] =0 # Clear flags
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] |= 0x80
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # XOR n
    # Logical exclusive OR n with register A, result in A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Reset.
    def xorh(self):
        self.registers['A'] = utils.bitwise_xor(self.registers['A'], self.registers['H'])
        self.registers['F'] =0 # Clear flags
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] |= 0x80
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # XOR n
    # Logical exclusive OR n with register A, result in A.
    # Use with:
    #   n = A,B,C,D,E,H,L,(HL),#
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Reset.
    def xorl(self):
        self.registers['A'] = utils.bitwise_xor(self.registers['A'], self.registers['L'])
        self.registers['F'] =0 # Clear flags
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] |= 0x80
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

    # RLCA
    # Rotate A left. Old bit 7 to Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 7 data
    def rlca(self):
        old_bit_7_data = utils.get_bit(self.registers['A'], 7)
        self.registers['A'] = self.registers['A'] << 8 + old_bit_7_data # Rotate A left
        self.registers['A'] &= 255
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) #  H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) #  N - Reset.
        if old_bit_7_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 7 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 7 data
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # RLA
    # Rotate A left through Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 7 data
    def rla(self):
        old_bit_7_data = utils.get_bit(self.registers['A'], 7)
        old_bit_4_data = utils.get_bit(self.registers['A'], 4)
        self.registers['A'] = self.registers['A'] << 8 + old_bit_4_data # Rotate A left through Carry flag.
        self.registers['A'] &= 255
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) #  H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) #  N - Reset.
        if old_bit_7_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 7 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 7 data
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # RRCA
    # Rotate A right. Old bit 0 to Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C -  Contains old bit 0 data
    def rrca(self):
        old_bit_0_data = utils.get_bit(self.registers['A'], 0)
        self.registers['A'] = self.registers['A'] >> 1 + (old_bit_0_data << 7) # Rotate A right
        self.registers['A'] &= 255
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) #  H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) #  N - Reset.
        if old_bit_0_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # RRA
    # Rotate A right through Carry flag.
    # Flags affected:
    #   Z - Set if result is zero.
    #   N - Reset.
    #   H - Reset.
    #   C - Contains old bit 0 data.
    def rra(self):
        old_bit_0_data = utils.get_bit(self.registers['A'], 0)
        old_bit_4_data = utils.get_bit(self.registers['A'], 4)
        self.registers['A'] = self.registers['A'] >> 1 + (old_bit_4_data << 7) # Rotate A right through Carry flag.
        self.registers['A'] &= 255
        if self.registers['A'] == 0: # Z - Set if result is zero.
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_Z)
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_Z)
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_H) #  H - Reset.
        self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_N) #  N - Reset.
        if old_bit_7_data == 1:
            self.registers['F'] = utils.set_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        else:
            self.registers['F'] = utils.reset_bit(self.registers['F'], self.FLAG_C) #  C - Contains old bit 0 data
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken


    # STOP
    # Halt CPU & LCD display until button pressed.
    def stop(self):
        self.halt = 1
        self.registers['PC'] += 1
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    # HALT
    # Power down CPU until an interrupt occurs. Use this
    # when ever possible to reduce energy consumption.
    def halt(self):
        self.halt = 1
        self.registers['M'] = 1 # 1 M-time taken
        self.registers['T'] = 4 # 1 M-time taken

    def todo(self):
        pass

    MAP = {
        0x00: nop,
        #0x02: ldbca,
        0x03: incbc,
        0x04: incb,
        0x05: decb,
        0x06: ldbd8,
        0x07: rlca,
        0x08: lda16sp,
        0x0B: decbc,
        0x0C: incc,
        0x0D: decc,
        0x0E: ldcd8,
        0x0F: rrca,
        0x10: stop,
        0x11: lddenn,
        0x12: todo,
        0x13: incde,
        0x14: incd,
        0x15: decd,
        0x16: lddd8,
        0x17: rla,
        0x18: jrr8,
        0x19: todo,
        0x1A: todo,
        0x1B: decde,
        0x1C: ince,
        0x1D: dece,
        0x1E: lded8,
        0x1F: rra,
        0x20: jrnz,
        0x21: ldhlnn,
        0x22: todo,
        0x23: todo,
        0x24: todo,
        0x25: dech,
        0x26: todo,
        0x28: todo,
        0x2E: todo,
        0x2F: todo,
        0x28: jrz,
        0x2B: dechl,
        0x2C: incl,
        0x2D: decl,
        0x2E: ldld8,
        0x30: jrnc,
        0x31: ldspnn,
        0x32: ldhlminusa,
        0x35: dechlm,
        0x38: jrc,
        0x3B: decsp,
        0x3D: deca,
        0x3E: ldad8,
        0x76: halt,
        0x77: ldhla,
        0xA8: xorb,
        0xA9: xorc,
        0xAA: xord,
        0xAB: xore,
        0xAC: xorh,
        0xAD: xorl,
        0xAF: xora,
        0xE2: ldca,
    }

    CB_MAP = {
        0x40: bit0b,
        0x41: bit0c,
        0x42: bit0d,
        0x43: bit0e,
        0x44: bit0h,
        0x45: bit0h,
        0x47: bit0a,
        0x48: bit1b,
        0x49: bit1c,
        0x4A: bit1d,
        0x4B: bit1e,
        0x4C: bit1h,
        0x4D: bit1l,
        0x4F: bit1a,
        0x50: bit2b,
        0x51: bit2c,
        0x52: bit2d,
        0x53: bit2e,
        0x54: bit2h,
        0x55: bit2h,
        0x57: bit2a,
        0x58: bit3b,
        0x59: bit3c,
        0x5A: bit3d,
        0x5B: bit3e,
        0x5C: bit3h,
        0x5D: bit3l,
        0x5F: bit3a,
        0x60: bit4b,
        0x61: bit4c,
        0x62: bit4d,
        0x63: bit4e,
        0x64: bit4h,
        0x65: bit4h,
        0x67: bit4a,
        0x68: bit5b,
        0x69: bit5c,
        0x6A: bit5d,
        0x6B: bit5e,
        0x6C: bit5h,
        0x6D: bit5l,
        0x6F: bit5a,
        0x70: bit6b,
        0x71: bit6c,
        0x72: bit6d,
        0x73: bit6e,
        0x74: bit6h,
        0x75: bit6h,
        0x77: bit6a,
        0x78: bit7b,
        0x79: bit7c,
        0x7A: bit7d,
        0x7B: bit7e,
        0x7C: bit7h,
        0x7D: bit7l,
        0x7F: bit7a,
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
        self.registers['PC'] &= 0xFFFF              # Mask PC to 16 bits
        self.clock['T'] += self.registers['T']      # Add time to CPU clock
        self.clock['M'] += self.registers['M']

    def load_rom(self, filename):
        self.MMU.load(filename)
