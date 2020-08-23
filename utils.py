import math

from disassembler import Instruction


def read_program_mem(filename, mem):
    mem_list = []
    f = open(filename, "r")
    for line in f:
        mem_list.append(line)
    f.close()
    for element in mem_list:
        mem.append(int(element, 2))
    for i in range(4):
        mem.append(Instruction(0).nop())


def to_unsigned(val, bits):
    if 0 > val >= -2 ** (bits - 1):
        val = 2**bits + val
    return val


def __correct(value, bits, signed):
    base = 1 << bits
    value %= base
    return value - base if signed and value.bit_length() == bits else value


to_uint8, to_int8, to_uint16, to_int16, to_uint32, to_int32, to_uint64, to_int64 = (
    lambda v: __correct(v, 8, False),
    lambda v: __correct(v, 8, True),
    lambda v: __correct(v, 16, False),
    lambda v: __correct(v, 16, True),
    lambda v: __correct(v, 32, False),
    lambda v: __correct(v, 32, True),
    lambda v: __correct(v, 64, False),
    lambda v: __correct(v, 64, True)
)


def round_down_to_power_of_two(n):
    return pow(2, int(math.floor(math.log2(n))))
