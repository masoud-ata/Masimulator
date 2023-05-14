import copy

from disassembler import BranchTypes, Instruction
from memory import *
from utils import *

ALU_AND = 0
ALU_OR = 1
ALU_XOR = 2
ALU_ADD = 3
ALU_SUB = 4
ALU_SLT = 5
ALU_SLTU = 6
ALU_RIGHT = 7
ALU_SLL = 8
ALU_SRL = 9
ALU_SRA = 10
ALU_MUL = 11

LUI = 0b0110111
R_FORMAT = 0b0110011
I_FORMAT = 0b0010011
LOAD = 0b0000011
STORE = 0b0100011
BRANCH = 0b1100011
JAL = 0b1101111
RET = 0b1100111


class MemoryReadMode:
    WORD = 0
    HALF_SIGNED = 1
    BYTE_SIGNED = 2


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
        self.less_than_flag = 0
        self.greater_than_equal_flag = 0
        self.less_than_unsigned_flag = 0
        self.greater_than_equal_unsigned_flag = 0
        self.control_alu_op = 0
        self.control_alu_src = 0
        self.control_mem_read = 0
        self.control_mem_read_mode = 0
        self.control_mem_write = 0
        self.control_reg_write = 0
        self.control_mem_to_reg = 0
        self.control_is_branch = 0
        self.control_is_jump = 0
        self.control_is_return = 0
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
        self.cache_data_ready = False


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
        self.pc_plus_4 = 0
        self.instruction = 0
        self.nop_inserted = False


class IdExReg:
    def __init__(self):
        self.pc_plus_4 = 0
        self.control_alu_op = 0
        self.control_alu_src = 0
        self.control_mem_read = 0
        self.control_mem_read_mode = 0
        self.control_mem_write = 0
        self.control_reg_write = 0
        self.control_mem_to_reg = 0
        self.control_is_jump = 0
        self.register_file_data1 = 0
        self.register_file_data2 = 0
        self.register_file_rs1 = 0
        self.register_file_rs2 = 0
        self.sign_extended_immediate = 0
        self.register_file_rd = 0
        self.instruction = 0
        self.nop_inserted = False


class ExMemReg:
    def __init__(self):
        self.pc_plus_4 = 0
        self.control_mem_read = 0
        self.control_mem_read_mode = 0
        self.control_mem_write = 0
        self.control_reg_write = 0
        self.control_mem_to_reg = 0
        self.control_is_jump = 0
        self.alu_result = 0
        self.register_file_data2 = 0
        self.register_file_rd = 0
        self.instruction = 0
        self.nop_inserted = False


class MemWbReg:
    def __init__(self):
        self.pc_plus_4 = 0
        self.control_reg_write = 0
        self.control_mem_to_reg = 0
        self.control_is_jump = 0
        self.memory_data = 0
        self.alu_result = 0
        self.register_file_rd = 0
        self.instruction = 0
        self.nop_inserted = False


class Pipeline:
    def __init__(self):
        self.if_id = IfIdReg()
        self.id_ex = IdExReg()
        self.ex_mem = ExMemReg()
        self.mem_wb = MemWbReg()


class CpuState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.pipe = Pipeline()
        self.signals = Signals()
        self.register_file = [0] * 32
        self.pc = 0
        self.data_memory_system = Memory()
        self.hazard_detected = 0
        self.cycles_executed = 1


class CPU:
    def __init__(self):
        self.memory = []
        read_program_mem("mem.txt", self.memory)
        self.state = CpuState()
        self.trace = []
        self.forwarding_enabled = 0
        self.hazard_detection_enabled = 0
        self.delayed_branches_enabled = 0

    def read_program_memory(self):
        self.memory = []
        read_program_mem("mem.txt", self.memory)

    def reset(self):
        self.trace = []
        self.state.reset()

    def clear_trace(self):
        self.trace = []

    def back_tick(self):
        if len(self.trace) != 0:
            self.state.data_memory_system.back_tick()
            del self.state
            self.state = copy.deepcopy(self.trace.pop())
            self.state.cycles_executed = self.state.cycles_executed - 1

    def is_finished(self):
        return self.state.pc // 4 == len(self.memory) - 1

    def tick(self, trace=True):
        if self.is_finished():
            return

        self.state.cycles_executed = self.state.cycles_executed + 1
        if trace:
            self.trace.append(copy.deepcopy(self.state))

        if not self.state.data_memory_system.is_processing():
            self._register_mem_wb()
            self._register_ex_mem()
            self._register_id_ex()
            self._register_if_id()
            self.calculate_signals()

        self._calc_mem_signals_wait_cycles()

    def calculate_signals(self):
            self._calc_wb_signals()
            self._calc_mem_signals_request_cycle()
            self._calc_ex_signals()
            self._calc_id_signals()
            self._calc_if_signals()

    def _calc_if_signals(self):
        self.state.signals.if_signals.instruction = self.memory[self.state.pc >> 2]
        self.state.signals.if_signals.pc = self.state.pc
        self.state.signals.if_signals.pc_plus_4 = self.state.pc + 4
        if self.state.signals.id_signals.control_is_return == 1:
            self.state.signals.if_signals.next_pc = self.state.signals.id_signals.rf_data1
        elif self.state.signals.id_signals.control_branch_taken == 0:
            self.state.signals.if_signals.next_pc = self.state.signals.if_signals.pc_plus_4
        else:
            self.state.signals.if_signals.next_pc = self.state.signals.id_signals.branch_address

    def _calc_id_signals(self):
        self.state.signals.id_signals.instruction = Instruction(self.state.pipe.if_id.instruction)
        self.state.signals.id_signals.rs1 = self.state.signals.id_signals.instruction.rs1()
        self.state.signals.id_signals.rs2 = self.state.signals.id_signals.instruction.rs2()
        self.state.signals.id_signals.rf_data1 = self.state.register_file[self.state.signals.id_signals.rs1]
        self.state.signals.id_signals.rf_data2 = self.state.register_file[self.state.signals.id_signals.rs2]
        self._id_imm_generation(self.state.signals.id_signals.instruction)
        self._id_control(self.state.signals.id_signals.instruction)
        self._id_handle_branch()

    def _calc_ex_signals(self):
        self._ex_forward_stuff()
        self.state.signals.ex_signals.alu_result = self._ex_alu(self.state.pipe.id_ex.control_alu_op, self.state.signals.ex_signals.alu_left_op, self.state.signals.ex_signals.alu_right_op)

    def _calc_mem_signals_request_cycle(self):
        self.state.signals.mem_signals.address = self.state.pipe.ex_mem.alu_result
        self.state.signals.mem_signals.mem_data = 0
        word_address = self.state.signals.mem_signals.address // 4
        data_word = self.state.pipe.ex_mem.register_file_data2
        if self.state.pipe.ex_mem.control_mem_read == 1:
            self.state.data_memory_system.read_request(word_address)
        elif self.state.pipe.ex_mem.control_mem_write == 1:
            self.state.data_memory_system.write_request(word_address, data_word)

    def _calc_mem_signals_wait_cycles(self):
        self.state.data_memory_system.tick()
        if self.state.data_memory_system.is_data_ready():
            mem_data = self.state.data_memory_system.read_data()
            if self.state.pipe.ex_mem.control_mem_read_mode == MemoryReadMode.WORD:
                self.state.signals.mem_signals.mem_data = mem_data
            elif self.state.pipe.ex_mem.control_mem_read_mode == MemoryReadMode.BYTE_SIGNED:
                byte_offset = self.state.signals.mem_signals.address & 0x3
                requested_byte = (mem_data >> (byte_offset * 8)) & 0xff
                sign = (requested_byte >> 7)
                requested_byte_sign_extended = requested_byte | (sign * 0xffffff00)
                self.state.signals.mem_signals.mem_data = to_int32(requested_byte_sign_extended)
            elif self.state.pipe.ex_mem.control_mem_read_mode == MemoryReadMode.HALF_SIGNED:
                sign = (mem_data >> 15 & 0x1)
                halfword_sign_extended = (mem_data & 0x0000ffff) | (sign * 0xffff0000)
                self.state.signals.mem_signals.mem_data = to_int32(halfword_sign_extended)

    def _calc_wb_signals(self):
        if self.state.pipe.mem_wb.control_mem_to_reg == 1:
            self.state.signals.wb_signals.rf_write_data = self.state.pipe.mem_wb.memory_data
        elif self.state.pipe.mem_wb.control_is_jump == 1:
            self.state.signals.wb_signals.rf_write_data = self.state.pipe.mem_wb.pc_plus_4
        else:
            self.state.signals.wb_signals.rf_write_data = self.state.pipe.mem_wb.alu_result
        if self.state.pipe.mem_wb.control_reg_write and self.state.pipe.mem_wb.register_file_rd != 0:
            self.state.register_file[self.state.pipe.mem_wb.register_file_rd] = self.state.signals.wb_signals.rf_write_data

    def _id_imm_generation(self, inst):
        op_6_5 = inst.opcode() >> 5
        if inst.opcode() == LUI:
            self.state.signals.id_signals.sign_extended_immediate = inst.imm_u()
        elif inst.opcode() == JAL:
            self.state.signals.id_signals.sign_extended_immediate = inst.imm_uj()
        elif op_6_5 == 0b00:
            self.state.signals.id_signals.sign_extended_immediate = inst.imm_i()
        elif op_6_5 == 0b01:
            self.state.signals.id_signals.sign_extended_immediate = inst.imm_s()
        else:
            self.state.signals.id_signals.sign_extended_immediate = inst.imm_sb()

    def _id_control(self, instruction):
        opcode = instruction.opcode()
        funct7 = instruction.funct7()
        funct3 = instruction.funct3()

        self.state.signals.id_signals.control_alu_op = ALU_ADD
        self.state.signals.id_signals.control_alu_src = 0
        self.state.signals.id_signals.control_mem_read = 0
        self.state.signals.id_signals.control_mem_write = 0
        self.state.signals.id_signals.control_reg_write = 0
        self.state.signals.id_signals.control_mem_read_mode = MemoryReadMode.WORD
        self.state.signals.id_signals.control_mem_to_reg = 0
        self.state.signals.id_signals.control_is_branch = 0
        self.state.signals.id_signals.control_is_jump = 0
        self.state.signals.id_signals.control_is_return = 0
        self.state.hazard_detected = 0

        if self.hazard_detection_enabled == 1 and self.state.pipe.id_ex.control_mem_read == 1 and \
            (self.state.pipe.id_ex.register_file_rd == Instruction(self.state.pipe.if_id.instruction).rs1() or
             self.state.pipe.id_ex.register_file_rd == Instruction(self.state.pipe.if_id.instruction).rs2()):
            self.state.hazard_detected = 1
        elif opcode == R_FORMAT:
            if funct3 == 0b000 and funct7 == 0b0000000:
                self.state.signals.id_signals.control_alu_op = ALU_ADD
            elif funct3 == 0b000 and funct7 == 0b0100000:
                self.state.signals.id_signals.control_alu_op = ALU_SUB
            elif funct3 == 0b111 and funct7 == 0b0000000:
                self.state.signals.id_signals.control_alu_op = ALU_AND
            elif funct3 == 0b110 and funct7 == 0b0000000:
                self.state.signals.id_signals.control_alu_op = ALU_OR
            elif funct3 == 0b100 and funct7 == 0b0000000:
                self.state.signals.id_signals.control_alu_op = ALU_XOR
            elif funct3 == 0b010 and funct7 == 0b0000000:
                self.state.signals.id_signals.control_alu_op = ALU_SLT
            elif funct3 == 0b011 and funct7 == 0b0000000:
                self.state.signals.id_signals.control_alu_op = ALU_SLTU
            elif funct3 == 0b001 and funct7 == 0b0000000:
                self.state.signals.id_signals.control_alu_op = ALU_SLL
            elif funct3 == 0b101 and funct7 == 0b0000000:
                self.state.signals.id_signals.control_alu_op = ALU_SRL
            elif funct3 == 0b101 and funct7 == 0b0100000:
                self.state.signals.id_signals.control_alu_op = ALU_SRA
            if funct3 == 0b000 and funct7 == 0b0000001:
                self.state.signals.id_signals.control_alu_op = ALU_MUL
            self.state.signals.id_signals.control_reg_write = 1
        elif opcode == I_FORMAT:
            if funct3 == 0b000:
                self.state.signals.id_signals.control_alu_op = ALU_ADD
            elif funct3 == 0b111:
                self.state.signals.id_signals.control_alu_op = ALU_AND
            elif funct3 == 0b110:
                self.state.signals.id_signals.control_alu_op = ALU_OR
            elif funct3 == 0b100:
                self.state.signals.id_signals.control_alu_op = ALU_XOR
            elif funct3 == 0b001:
                self.state.signals.id_signals.control_alu_op = ALU_SLL
            elif funct3 == 0b101 and (funct7 >> 1) == 0b000000:
                self.state.signals.id_signals.control_alu_op = ALU_SRL
            elif funct3 == 0b101 and (funct7 >> 1) == 0b010000:
                self.state.signals.id_signals.control_alu_op = ALU_SRA
            self.state.signals.id_signals.control_reg_write = 1
            self.state.signals.id_signals.control_alu_src = 1
        elif opcode == LOAD:
            self.state.signals.id_signals.control_alu_src = 1
            self.state.signals.id_signals.control_mem_read = 1
            self.state.signals.id_signals.control_reg_write = 1
            self.state.signals.id_signals.control_mem_to_reg = 1
            if funct3 == 0b000:
                self.state.signals.id_signals.control_mem_read_mode = MemoryReadMode.BYTE_SIGNED
            elif funct3 == 0b001:
                self.state.signals.id_signals.control_mem_read_mode = MemoryReadMode.HALF_SIGNED
            elif funct3 == 0b010:
                self.state.signals.id_signals.control_mem_read_mode = MemoryReadMode.WORD
        elif opcode == STORE:
            self.state.signals.id_signals.control_alu_src = 1
            self.state.signals.id_signals.control_mem_write = 1
        elif opcode == BRANCH:
            self.state.signals.id_signals.control_is_branch = 1
        elif opcode == JAL:
            self.state.signals.id_signals.control_is_jump = 1
            self.state.signals.id_signals.control_reg_write = 1
        elif opcode == RET:
            self.state.signals.id_signals.control_is_return = 1
        elif opcode == LUI:
            self.state.signals.id_signals.control_alu_op = ALU_RIGHT
            self.state.signals.id_signals.control_alu_src = 1
            self.state.signals.id_signals.control_reg_write = 1

    def _id_handle_branch(self):
        self.state.signals.id_signals.branch_address = self.state.pipe.if_id.pc + (self.state.signals.id_signals.sign_extended_immediate << 1)
        self.state.signals.id_signals.zero_flag = (self.state.signals.id_signals.rf_data1 == self.state.signals.id_signals.rf_data2)
        self.state.signals.id_signals.less_than_flag = (self.state.signals.id_signals.rf_data1 < self.state.signals.id_signals.rf_data2)
        self.state.signals.id_signals.greater_than_equal_flag = (self.state.signals.id_signals.rf_data1 >= self.state.signals.id_signals.rf_data2)
        self.state.signals.id_signals.less_than_unsigned_flag = (to_unsigned(self.state.signals.id_signals.rf_data1, 32) < to_unsigned(self.state.signals.id_signals.rf_data2, 32))
        self.state.signals.id_signals.greater_than_equal_unsigned_flag = (to_unsigned(self.state.signals.id_signals.rf_data1, 32) >= to_unsigned(self.state.signals.id_signals.rf_data2, 32))
        branch_type = Instruction(self.state.pipe.if_id.instruction).funct3()
        self.state.signals.id_signals.control_branch_taken = 0
        if self.state.signals.id_signals.control_is_jump or self.state.signals.id_signals.control_is_return == 1:
            self.state.signals.id_signals.control_branch_taken = 1
        elif self.state.signals.id_signals.control_is_branch:
            if branch_type == BranchTypes.BEQ and self.state.signals.id_signals.zero_flag:
                self.state.signals.id_signals.control_branch_taken = 1
            elif branch_type == BranchTypes.BNE and not self.state.signals.id_signals.zero_flag:
                self.state.signals.id_signals.control_branch_taken = 1
            elif branch_type == BranchTypes.BLT and self.state.signals.id_signals.less_than_flag:
                self.state.signals.id_signals.control_branch_taken = 1
            elif branch_type == BranchTypes.BGE and self.state.signals.id_signals.greater_than_equal_flag:
                self.state.signals.id_signals.control_branch_taken = 1
            elif branch_type == BranchTypes.BLTU and self.state.signals.id_signals.less_than_unsigned_flag:
                self.state.signals.id_signals.control_branch_taken = 1
            elif branch_type == BranchTypes.BGEU and self.state.signals.id_signals.greater_than_equal_unsigned_flag:
                self.state.signals.id_signals.control_branch_taken = 1

    def _ex_alu(self, control, left, right):
        ex_alu_result = to_int32(left & right)
        if control == ALU_AND:
            ex_alu_result = to_int32(left & right)
        elif control == ALU_OR:
            ex_alu_result = to_int32(left | right)
        elif control == ALU_XOR:
            ex_alu_result = to_int32(left ^ right)
        elif control == ALU_ADD:
            ex_alu_result = to_int32(left + right)
        elif control == ALU_SUB:
            ex_alu_result = to_int32(left - right)
        elif control == ALU_SLT:
            ex_alu_result = 1 if left < right else 0
        elif control == ALU_SLTU:
            ex_alu_result = 1 if to_uint32(left) < to_uint32(right) else 0
        elif control == ALU_RIGHT:
            ex_alu_result = to_int32(right)
        elif control == ALU_SLL:
            shift_amount = right & 0x1f
            ex_alu_result = to_int32(left << shift_amount)
        elif control == ALU_SRL:
            shift_amount = right & 0x1f
            ex_alu_result = to_int32((left & 0xffffffff) >> shift_amount)
        elif control == ALU_SRA:
            shift_amount = right & 0x1f
            ex_alu_result = to_int32(left >> shift_amount)
        if control == ALU_MUL:
            ex_alu_result = to_int32(left * right)
        return ex_alu_result

    def _ex_forward_stuff(self):
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

    def _register_if_id(self):
        if self.state.hazard_detected == 0:
            self.state.pipe.if_id.pc_plus_4 = self.state.signals.if_signals.pc_plus_4
            self.state.pipe.if_id.pc = self.state.signals.if_signals.pc
            flush_if_inst = self.delayed_branches_enabled == 0 and self.state.signals.id_signals.control_branch_taken == 1
            if flush_if_inst:
                self.state.pipe.if_id.instruction = Instruction(0).nop()
                self.state.pipe.if_id.nop_inserted = True
            else:
                self.state.pipe.if_id.instruction = self.state.signals.if_signals.instruction
                self.state.pipe.if_id.nop_inserted = False
            self.state.pc = self.state.signals.if_signals.next_pc

    def _register_id_ex(self):
        id_ex = self.state.pipe.id_ex
        id_ex.pc_plus_4 = self.state.pipe.if_id.pc_plus_4
        id_signals = self.state.signals.id_signals
        id_ex.register_file_data1 = id_signals.rf_data1
        id_ex.register_file_data2 = id_signals.rf_data2
        id_ex.register_file_rs1 = id_signals.rs1
        id_ex.register_file_rs2 = id_signals.rs2
        id_ex.register_file_rd = id_signals.instruction.rd()
        id_ex.control_alu_op = id_signals.control_alu_op
        id_ex.control_alu_src = id_signals.control_alu_src
        id_ex.control_mem_read = id_signals.control_mem_read
        id_ex.control_mem_write = id_signals.control_mem_write
        id_ex.control_reg_write = id_signals.control_reg_write
        id_ex.control_mem_read_mode = id_signals.control_mem_read_mode
        id_ex.control_mem_to_reg = id_signals.control_mem_to_reg
        id_ex.control_is_jump = id_signals.control_is_jump
        id_ex.sign_extended_immediate = id_signals.sign_extended_immediate
        if self.state.hazard_detected == 1:
            id_ex.instruction = Instruction(0).nop()
            id_ex.nop_inserted = True
        else:
            id_ex.instruction = self.state.pipe.if_id.instruction
            id_ex.nop_inserted = self.state.pipe.if_id.nop_inserted

    def _register_ex_mem(self):
        ex_mem = self.state.pipe.ex_mem
        id_ex = self.state.pipe.id_ex
        ex_mem.pc_plus_4 = id_ex.pc_plus_4
        ex_mem.control_mem_read = id_ex.control_mem_read
        ex_mem.control_mem_read_mode = id_ex.control_mem_read_mode
        ex_mem.control_mem_write = id_ex.control_mem_write
        ex_mem.control_reg_write = id_ex.control_reg_write
        ex_mem.control_mem_to_reg = id_ex.control_mem_to_reg
        ex_mem.control_is_jump = id_ex.control_is_jump
        ex_mem.alu_result = self.state.signals.ex_signals.alu_result
        ex_mem.register_file_data2 =self.state.signals.ex_signals.right_forward_out
        ex_mem.register_file_rd = id_ex.register_file_rd
        ex_mem.instruction = id_ex.instruction
        ex_mem.nop_inserted = id_ex.nop_inserted

    def _register_mem_wb(self):
        mem_wb = self.state.pipe.mem_wb
        ex_mem = self.state.pipe.ex_mem
        mem_wb.pc_plus_4 = ex_mem.pc_plus_4
        mem_wb.control_reg_write = ex_mem.control_reg_write
        mem_wb.control_mem_to_reg = ex_mem.control_mem_to_reg
        mem_wb.control_is_jump = ex_mem.control_is_jump
        mem_wb.memory_data = self.state.signals.mem_signals.mem_data
        mem_wb.alu_result = ex_mem.alu_result
        mem_wb.register_file_rd = ex_mem.register_file_rd
        mem_wb.instruction = ex_mem.instruction
        mem_wb.nop_inserted = ex_mem.nop_inserted
