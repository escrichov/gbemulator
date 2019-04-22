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
