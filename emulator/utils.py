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

def carry_half_carry_8_bit(a, b):
    if (((a & 0xf) + (b & 0xf)) & 0x10) == 0x10:
        return True
    else:
        return False

def carry_half_carry_16_bit(a, b):
    if (((a & 0xfff) + (b & 0xfff)) & 0x1000) == 0x1000:
        return True
    else:
        return False

def carry_carry_8_bit(a, b):
    val = a + b
    if (a + b) > 0xFF:
        return True
    else:
        return False

def carry_carry_16_bit(a, b):
    val = a + b
    if (a + b) > 0xFFFF:
        return True
    else:
        return False

def half_borrow_8_bit(a, b):
    if (((a & 0xf) + (b & 0xf)) & 0x10) == 0x10:
        return True
    else:
        return False

def half_borrow_16_bit(a, b):
    if (((a & 0xfff) + (b & 0xfff)) & 0x1000) == 0x1000:
        return True
    else:
        return False

def borrow_8_bit(a, b):
    val = a + b
    if (a + b) > 0xFF:
        return True
    else:
        return False

def borrow_16_bit(a, b):
    val = a + b
    if (a + b) > 0xFFFF:
        return True
    else:
        return False


def swap_nibbles(value):
    old_high_part = value >> 4
    old_low_part = value & 0xF

    return (old_low_part << 4) + old_high_part

def flip_bits_8b(value):
    return ~value & 0xFF

def flip_bits_16b(value):
    return ~value & 0xFFFF
