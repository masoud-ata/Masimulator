def read_program_mem(filename, mem):
    mem_list = []
    f = open(filename, "r")

    for line in f:
        mem_list.append(line)

    f.close()

    for element in mem_list:
        mem.append(int(element, 2))


def to_unsigned(val, bits):
    if 0 > val >= -2 ** (bits - 1):
        val = 2**bits + val
    return val