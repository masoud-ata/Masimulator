class Instruction:
    def __init__(self, inst):
        self.word = inst

    def _negative_fix(self, imm, length):
        return imm - (imm >> length-1) * (2 ** length)

    def opcode(self):
        return self.word & 0b111_1111

    def rd(self):
        return (self.word >> 7) & 0b1_1111

    def rs1(self):
        return (self.word >> 15) & 0b1_1111

    def rs2(self):
        return (self.word >> 20) & 0b1_1111

    def funct3(self):
        return (self.word >> 12) & 0b111

    def funct7(self):
        return (self.word >> 25) & 0b111_1111

    def imm_i(self):
        imm = (self.word >> 20) & 0b1111_1111_1111
        imm = self._negative_fix(imm, 12)
        return imm

    def imm_s(self):
        imm = (self.funct7() << 5) | self.rd()
        imm = self._negative_fix(imm, 12)
        return imm

    def imm_sb(self):
        imm = ((self.funct7() >> 6) << 11) | ((self.rd() & 0b1) << 10) | ((self.funct7() & 0b0111111) << 4) | (self.rd() >> 1)
        imm = self._negative_fix(imm, 12)
        return imm

    def nop(self):
        return 0x13

    def is_nop(self):
        return self.word == self.nop()


def disassemble(inst):
    instruction = Instruction(inst)

    R_FORMAT = 0b0110011
    ADDI = 0b0010011
    LOAD = 0b0000011
    STORE = 0b0100011
    BEQ = 0b1100011

    dic = {
        LOAD: "lw",
        STORE: "sw",
        BEQ: "beq",
        ADDI: "addi",
        R_FORMAT: ""
    }

    try:
        assembly_code = dic[instruction.opcode()]
    except KeyError:
        assembly_code = ""

    if instruction.is_nop():
        assembly_code = "nop"
    elif instruction.opcode() == LOAD:
        assembly_code = assembly_code + " $" + str(instruction.rd()) + ", $" + str(instruction.rs1()) + ", " + str(instruction.imm_i())
    elif instruction.opcode() == STORE:
        assembly_code = assembly_code + " $" + str(instruction.rs1()) + ", $" + str(instruction.rs2()) + ", " + str(instruction.imm_s())
    elif instruction.opcode() == ADDI:
        assembly_code = assembly_code + " $" + str(instruction.rd()) + ", $" + str(instruction.rs1()) + ", " + str(instruction.imm_i())
    elif instruction.opcode() == BEQ:
        assembly_code = assembly_code + " $" + str(instruction.rs1()) + ", $" + str(instruction.rs2()) + ", " + str(instruction.imm_sb())
    elif instruction.opcode() == R_FORMAT:
        alu_control = (instruction.funct7() & 0b100000) >> 2 | instruction.funct3()
        if alu_control == 0b0000:
            assembly_code = "add"
        elif alu_control == 0b1000:
            assembly_code = "sub"
        elif alu_control == 0b0111:
            assembly_code = "and"
        elif alu_control == 0b0110:
            assembly_code = "or"
        assembly_code = assembly_code + " $" + str(instruction.rd()) + ", $" + str(instruction.rs2()) + ", $" + str(instruction.rs1())

    return assembly_code
