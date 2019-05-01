def zerolistmaker(n):
    listofzeros = [0] * n
    return listofzeros

def bitwise_xor(val1, val2):
    return val1 ^ val2

def test_bit(value, bit):
    mask = 1 << bit
    if (mask & value) == 0:
        return False
    else:
        return True

def get_bit(value, bit):
    return (value >> bit) & 0x01

def set_bit(value, bit):
    return value | 1 << bit

def reset_bit(value, bit):
    return value & ~(1 << bit)

def bytes_to_16(high, low):
    return (high << 8) + low

def half_carry_8_bit(a, b):
    if (((a & 0xF) + (b & 0xF)) & 0x10) == 0x10:
        return True
    else:
        return False

def half_carry_16_bit(a, b):
    if (((a & 0xFFF) + (b & 0xFFF)) & 0x1000) == 0x1000:
        return True
    else:
        return False

def carry_8_bit(a, b):
    val = a + b
    if val > 0xFF:
        return True
    else:
        return False

def carry_16_bit(a, b):
    val = a + b
    if val > 0xFFFF:
        return True
    else:
        return False

def half_borrow_8_bit(a, b):
    if ((a & 0xF) - (b & 0xF)) < 0:
        return False
    else:
        return True

def half_borrow_16_bit(a, b):
    if ((a & 0xFFF) - (b & 0xFFF)) < 0:
        return False
    else:
        return True

def borrow_8_bit(a, b):
    val = a - b
    if val < 0:
        return False
    else:
        return True

def borrow_16_bit(a, b):
    val = a - b
    if val < 0:
        return False
    else:
        return True

def swap_nibbles(value):
    old_high_part = value >> 4
    old_low_part = value & 0xF

    return (old_low_part << 4) + old_high_part

def flip_bits_8b(value):
    return ~value & 0xFF

def flip_bits_16b(value):
    return ~value & 0xFFFF

def signed_8b(value):
    if value > 0x7F:
        return -((~value+1)&0xFF)
    else:
        return value

def signed_16b(value):
    if value > 0x7FFF:
        return -((~value+1)&0xFFFF)
    else:
        return value
