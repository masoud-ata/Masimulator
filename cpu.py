from disassembler import Instruction
from utils import read_program_mem
import copy


class IfSignals:
    def __init__(self):
        self.pc = 0
        self.pc_plus_4 = 0
        self.next_pc = 0
        self.instruction = 0

class IdSignals:
    def __init__(self):
        self.instruction = Instruction(0)
        self.rs1 = 0
        self.rs2 = 0
        self.rf_data1 = 0
        self.rf_data2 = 0
        self.zero_flag = 0
        self.control_alu_op = 0
        self.control_alu_src = 0
        self.control_mem_read = 0
        self.control_mem_write = 0
        self.control_reg_write = 0
        self.control_mem_to_reg = 0
        self.control_is_branch = 0
        self.sign_extended_immediate = 0
        self.branch_address = 0
        self.control_branch_taken = 0


class ExSignals:
    def __init__(self):
        self.alu_left_op = 0
        self.alu_right_op = 0
        self.alu_result = 0
        self.right_forward_out = 0


class MemSignals:
    def __init__(self):
        self.address = 0
        self.mem_data = 0


class WbSignals:
    def __init__(self):
        self.rf_write_data = 0


class Signals:
    def __init__(self):
        self.if_signals = IfSignals()
        self.id_signals = IdSignals()
        self.ex_signals = ExSignals()
        self.mem_signals = MemSignals()
        self.wb_signals = WbSignals()


class IfIdReg:
    def __init__(self):
        self.pc = 0
        self.instruction = 0


class IdExReg:
    def __init__(self):
        self.control_alu_op = 0
        self.control_alu_src = 0
        self.control_mem_read = 0
        self.control_mem_write = 0
        self.control_reg_write = 0
        self.control_mem_to_reg = 0
        self.register_file_data1 = 0
        self.register_file_data2 = 0
        self.register_file_rs1 = 0
        self.register_file_rs2 = 0
        self.sign_extended_immediate = 0
        self.alu_control = 0
        self.register_file_rd = 0
        self.instruction = 0


class ExMemReg:
    def __init__(self):
        self.control_mem_read = 0
        self.control_mem_write = 0
        self.control_reg_write = 0
        self.control_mem_to_reg = 0
        self.alu_result = 0
        self.register_file_data2 = 0
        self.register_file_rd = 0
        self.instruction = 0


class MemWbReg:
    def __init__(self):
        self.control_reg_write = 0
        self.control_mem_to_reg = 0
        self.memory_data = 0
        self.alu_result = 0
        self.register_file_rd = 0
        self.instruction = 0


class Pipeline:
    def __init__(self):
        self.if_id = IfIdReg()
        self.id_ex = IdExReg()
        self.ex_mem = ExMemReg()
        self.mem_wb = MemWbReg()


class CpuState:
    def __init__(self):
        self.pipe = Pipeline()
        self.signals = Signals()
        self.register_file = [0] * 32
        self.pc = 0
        self.data_memory = [0] * 1024

    def reset(self):
        self.pipe = Pipeline()
        self.signals = Signals()
        self.register_file = [0] * 32
        self.pc = 0
        self.data_memory = [0] * 1024


class CPU:
    def __init__(self):
        self.memory = []
        read_program_mem("mem.txt", self.memory)
        self.state = CpuState()
        self.trace = []
        self.forwarding_enabled = 0

    def read_program_memory(self):
        self.memory = []
        read_program_mem("mem.txt", self.memory)

    def reset(self):
        self.trace = []
        self.state.reset()

    def back_tick(self):
        if len(self.trace) != 0:
            del self.state
            self.state = copy.deepcopy(self.trace.pop())

    def tick(self):
        if int(self.state.pc / 4) == len(self.memory) - 1:
            return
        self.trace.append(copy.deepcopy(self.state))
        self._register_mem_wb()
        self._register_ex_mem()
        self._register_id_ex()
        self._register_if_id()

    def calculate_signals(self):
        self._calc_wb_signals()
        self._calc_mem_signals()
        self._calc_ex_signals()
        self._calc_id_signals()
        self._calc_if_signals()

    def _calc_if_signals(self):
        self.state.signals.if_signals.instruction = self.memory[self.state.pc >> 2]
        self.state.signals.if_signals.pc = self.state.pc
        self.state.signals.if_signals.pc_plus_4 = self.state.pc + 4
        if self.state.signals.id_signals.control_branch_taken == 0:
            self.state.signals.if_signals.next_pc = self.state.signals.if_signals.pc_plus_4
        else:
            self.state.signals.if_signals.next_pc = self.state.signals.id_signals.branch_address

    def _calc_id_signals(self):
        def imm_generation(inst):
            op_6_5 = inst.opcode() >> 5

            if op_6_5 == 0b00:
                self.state.signals.id_signals.sign_extended_immediate = inst.imm_i()
            elif op_6_5 == 0b01:
                self.state.signals.id_signals.sign_extended_immediate = inst.imm_s()
            else:
                self.state.signals.id_signals.sign_extended_immediate = inst.imm_sb()

        def control(opcode):
            R_FORMAT = 0b0110011
            ADDI = 0b0010011
            LOAD = 0b0000011
            STORE = 0b0100011
            BEQ = 0b1100011

            self.state.signals.id_signals.zero_flag = 0
            self.state.signals.id_signals.control_alu_op = 0
            self.state.signals.id_signals.control_alu_src = 0
            self.state.signals.id_signals.control_mem_read = 0
            self.state.signals.id_signals.control_mem_write = 0
            self.state.signals.id_signals.control_reg_write = 0
            self.state.signals.id_signals.control_mem_to_reg = 0
            self.state.signals.id_signals.control_is_branch = 0

            if opcode == R_FORMAT:
                self.state.signals.id_signals.control_alu_op = 0b10
                self.state.signals.id_signals.control_reg_write = 1
            elif opcode == ADDI:
                self.state.signals.id_signals.control_alu_op = 0b00
                self.state.signals.id_signals.control_reg_write = 1
                self.state.signals.id_signals.control_alu_src = 1
            elif opcode == LOAD:
                self.state.signals.id_signals.control_alu_src = 1
                self.state.signals.id_signals.control_mem_read = 1
                self.state.signals.id_signals.control_reg_write = 1
                self.state.signals.id_signals.control_mem_to_reg = 1
            elif opcode == STORE:
                self.state.signals.id_signals.control_alu_src = 1
                self.state.signals.id_signals.control_mem_write = 1
            elif opcode == BEQ:
                self.state.signals.id_signals.control_alu_op = 0b01
                self.state.signals.id_signals.control_is_branch = 1

        self.state.signals.id_signals.instruction = Instruction(self.state.pipe.if_id.instruction)
        self.state.signals.id_signals.rs1 = self.state.signals.id_signals.instruction.rs1()
        self.state.signals.id_signals.rs2 = self.state.signals.id_signals.instruction.rs2()
        self.state.signals.id_signals.rf_data1 = self.state.register_file[self.state.signals.id_signals.rs1]
        self.state.signals.id_signals.rf_data2 = self.state.register_file[self.state.signals.id_signals.rs2]
        imm_generation(self.state.signals.id_signals.instruction)
        control(self.state.signals.id_signals.instruction.opcode())
        self.state.signals.id_signals.zero_flag = (self.state.signals.id_signals.rf_data1 == self.state.signals.id_signals.rf_data2)
        self.state.signals.id_signals.branch_address = self.state.pipe.if_id.pc + (self.state.signals.id_signals.sign_extended_immediate << 1)
        self.state.signals.id_signals.control_branch_taken = self.state.signals.id_signals.control_is_branch and self.state.signals.id_signals.zero_flag

    def _calc_ex_signals(self):
        def alu_control():
            ALU_AND = 0b000
            ALU_OR = 0b001
            ALU_ADD = 0b010
            ALU_SUB = 0b110
            ex_alu_control = ALU_AND

            if self.state.pipe.id_ex.control_alu_op == 0b00:
                ex_alu_control = ALU_ADD
            elif self.state.pipe.id_ex.control_alu_op == 0b01:
                ex_alu_control = ALU_SUB
            elif self.state.pipe.id_ex.alu_control == 0b0000:
                ex_alu_control = ALU_ADD
            elif self.state.pipe.id_ex.alu_control == 0b1000:
                ex_alu_control = ALU_SUB
            elif self.state.pipe.id_ex.alu_control == 0b0111:
                ex_alu_control = ALU_AND
            elif self.state.pipe.id_ex.alu_control == 0b0110:
                ex_alu_control = ALU_OR

            return ex_alu_control

        def alu(control, left, right):
            if control == 0b000:
                ex_alu_result = left & right
            elif control == 0b001:
                ex_alu_result = left | right
            elif control == 0b010:
                ex_alu_result = left + right
            elif control == 0b110:
                ex_alu_result = left - right
            else:
                ex_alu_result = left & right

            return ex_alu_result

        def forward_stuff():
            self.state.signals.ex_signals.alu_left_op = self.state.pipe.id_ex.register_file_data1
            if self.forwarding_enabled == 1:
                if self.state.pipe.ex_mem.control_reg_write == 1 and self.state.pipe.ex_mem.register_file_rd != 0 and self.state.pipe.ex_mem.register_file_rd == self.state.pipe.id_ex.register_file_rs1:
                    self.state.signals.ex_signals.alu_left_op = self.state.pipe.ex_mem.alu_result
                elif self.state.pipe.mem_wb.control_reg_write == 1 and self.state.pipe.mem_wb.register_file_rd != 0 and self.state.pipe.mem_wb.register_file_rd == self.state.pipe.id_ex.register_file_rs1:
                    self.state.signals.ex_signals.alu_left_op = self.state.signals.wb_signals.rf_write_data

            self.state.signals.ex_signals.right_forward_out = self.state.pipe.id_ex.register_file_data2
            if self.forwarding_enabled == 1:
                if self.state.pipe.ex_mem.control_reg_write == 1 and self.state.pipe.ex_mem.register_file_rd != 0 and self.state.pipe.ex_mem.register_file_rd == self.state.pipe.id_ex.register_file_rs2:
                    self.state.signals.ex_signals.right_forward_out = self.state.pipe.ex_mem.alu_result
                elif self.state.pipe.mem_wb.control_reg_write == 1 and self.state.pipe.mem_wb.register_file_rd != 0 and self.state.pipe.mem_wb.register_file_rd == self.state.pipe.id_ex.register_file_rs2:
                    self.state.signals.ex_signals.right_forward_out = self.state.signals.wb_signals.rf_write_data

            if self.state.pipe.id_ex.control_alu_src == 0:
                self.state.signals.ex_signals.alu_right_op = self.state.signals.ex_signals.right_forward_out
            else:
                self.state.signals.ex_signals.alu_right_op = self.state.pipe.id_ex.sign_extended_immediate

        forward_stuff()
        self.state.signals.ex_signals.alu_result = alu(alu_control(), self.state.signals.ex_signals.alu_left_op, self.state.signals.ex_signals.alu_right_op)

    def _calc_mem_signals(self):
        self.state.signals.mem_signals.address = self.state.pipe.ex_mem.alu_result
        self.state.signals.mem_signals.mem_data = self.state.data_memory[self.state.signals.mem_signals.address] if self.state.pipe.ex_mem.control_mem_read == 1 else 0
        if self.state.pipe.ex_mem.control_mem_write == 1:
            self.state.data_memory[self.state.signals.mem_signals.address] = self.state.pipe.ex_mem.register_file_data2

    def _calc_wb_signals(self):
        self.state.signals.wb_signals.rf_write_data = self.state.pipe.mem_wb.alu_result if self.state.pipe.mem_wb.control_mem_to_reg == 0 else self.state.pipe.mem_wb.memory_data
        if self.state.pipe.mem_wb.control_reg_write:
            self.state.register_file[self.state.pipe.mem_wb.register_file_rd] = self.state.signals.wb_signals.rf_write_data

    def _register_if_id(self):
        self.state.pipe.if_id.pc = self.state.signals.if_signals.pc
        self.state.pipe.if_id.instruction = self.state.signals.if_signals.instruction
        self.state.pc = self.state.signals.if_signals.next_pc

    def _register_id_ex(self):
        self.state.pipe.id_ex.register_file_data1 = self.state.signals.id_signals.rf_data1
        self.state.pipe.id_ex.register_file_data2 = self.state.signals.id_signals.rf_data2
        self.state.pipe.id_ex.register_file_rs1 = self.state.signals.id_signals.rs1
        self.state.pipe.id_ex.register_file_rs2 = self.state.signals.id_signals.rs2
        self.state.pipe.id_ex.register_file_rd = self.state.signals.id_signals.instruction.rd()
        self.state.pipe.id_ex.control_alu_op = self.state.signals.id_signals.control_alu_op
        self.state.pipe.id_ex.control_alu_src = self.state.signals.id_signals.control_alu_src
        self.state.pipe.id_ex.control_mem_read = self.state.signals.id_signals.control_mem_read
        self.state.pipe.id_ex.control_mem_write = self.state.signals.id_signals.control_mem_write
        self.state.pipe.id_ex.control_reg_write = self.state.signals.id_signals.control_reg_write
        self.state.pipe.id_ex.control_mem_to_reg = self.state.signals.id_signals.control_mem_to_reg
        self.state.pipe.id_ex.sign_extended_immediate = self.state.signals.id_signals.sign_extended_immediate
        self.state.pipe.id_ex.alu_control = (self.state.signals.id_signals.instruction.funct7() & 0b100000) >> 2 | self.state.signals.id_signals.instruction.funct3()
        self.state.pipe.id_ex.instruction = self.state.pipe.if_id.instruction

    def _register_ex_mem(self):
        self.state.pipe.ex_mem.control_mem_read = self.state.pipe.id_ex.control_mem_read
        self.state.pipe.ex_mem.control_mem_write = self.state.pipe.id_ex.control_mem_write
        self.state.pipe.ex_mem.control_reg_write = self.state.pipe.id_ex.control_reg_write
        self.state.pipe.ex_mem.control_mem_to_reg = self.state.pipe.id_ex.control_mem_to_reg
        self.state.pipe.ex_mem.alu_result = self.state.signals.ex_signals.alu_result
        self.state.pipe.ex_mem.register_file_data2 =self.state.signals.ex_signals.right_forward_out
        self.state.pipe.ex_mem.register_file_rd = self.state.pipe.id_ex.register_file_rd
        self.state.pipe.ex_mem.instruction = self.state.pipe.id_ex.instruction

    def _register_mem_wb(self):
        self.state.pipe.mem_wb.control_reg_write = self.state.pipe.ex_mem.control_reg_write
        self.state.pipe.mem_wb.control_mem_to_reg = self.state.pipe.ex_mem.control_mem_to_reg
        self.state.pipe.mem_wb.memory_data = self.state.signals.mem_signals.mem_data
        self.state.pipe.mem_wb.alu_result = self.state.pipe.ex_mem.alu_result
        self.state.pipe.mem_wb.register_file_rd = self.state.pipe.ex_mem.register_file_rd
        self.state.pipe.mem_wb.instruction = self.state.pipe.ex_mem.instruction
