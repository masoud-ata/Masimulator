from disassembler import Instruction
from utils import read_program_mem
import copy



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
        self.register_file = [0] * 32
        self.if_pc = 0
        self.if_instruction = 0
        self.data_memory = [0] * 1024
        self.id_zero_flag = 0
        self.id_control_alu_op = 0
        self.id_control_alu_src = 0
        self.id_control_mem_read = 0
        self.id_control_mem_write = 0
        self.id_control_reg_write = 0
        self.id_control_mem_to_reg = 0
        self.id_control_is_branch = 0
        self.id_sign_extended_immediate = 0
        self.id_branch_address = 0
        self.id_control_branch_taken = 0

    def reset(self):
        self.pipe = Pipeline()
        self.register_file = [0] * 32
        self.if_pc = 0
        self.data_memory = [0] * 1024
        self.id_zero_flag = 0
        self.id_control_alu_op = 0
        self.id_control_alu_src = 0
        self.id_control_mem_read = 0
        self.id_control_mem_write = 0
        self.id_control_reg_write = 0
        self.id_control_mem_to_reg = 0
        self.id_control_is_branch = 0
        self.id_sign_extended_immediate = 0
        self.id_branch_address = 0
        self.id_control_branch_taken = 0


class CPU:
    def __init__(self):
        self.memory = []
        read_program_mem("mem.txt", self.memory)
        self.state = CpuState()
        self.trace = []

    def reset(self):
        self.trace = []
        self.state.reset()

    def back_tick(self):
        if len(self.trace) != 0:
            del self.state
            self.state = copy.deepcopy(self.trace.pop())

    def tick(self):
        def if_operations():
            self.state.if_instruction = self.memory[self.state.if_pc >> 2]
            self.state.pipe.if_id.pc = self.state.if_pc
            self.state.pipe.if_id.instruction = self.memory[self.state.if_pc >> 2]
            if self.state.id_control_branch_taken == 0:
                self.state.if_pc = self.state.if_pc + 4
            else:
                self.state.if_pc = self.state.id_branch_address

        def id_operations():
            def imm_generation(inst):
                op_6_5 = inst.opcode() >> 5

                if op_6_5 == 0b00:
                    self.state.id_sign_extended_immediate = instruction.imm_i()
                elif op_6_5 == 0b01:
                    self.state.id_sign_extended_immediate = instruction.imm_s()
                else:
                    self.state.id_sign_extended_immediate = instruction.imm_sb()

            def control(opcode):
                R_FORMAT = 0b0110011
                ADDI = 0b0010011
                LOAD = 0b0000011
                STORE = 0b0100011
                BEQ = 0b1100011

                self.state.id_zero_flag = 0
                self.state.id_control_alu_op = 0
                self.state.id_control_alu_src = 0
                self.state.id_control_mem_read = 0
                self.state.id_control_mem_write = 0
                self.state.id_control_reg_write = 0
                self.state.id_control_mem_to_reg = 0
                self.state.id_control_is_branch = 0

                if opcode == R_FORMAT:
                    self.state.id_control_alu_op = 0b10
                    self.state.id_control_reg_write = 1
                elif opcode == ADDI:
                    self.state.id_control_alu_op = 0b10
                    self.state.id_control_reg_write = 1
                    self.state.id_control_alu_src = 1
                elif opcode == LOAD:
                    self.state.id_control_alu_src = 1
                    self.state.id_control_mem_read = 1
                    self.state.id_control_reg_write = 1
                    self.state.id_control_mem_to_reg = 1
                elif opcode == STORE:
                    self.state.id_control_alu_src = 1
                    self.state.id_control_mem_write = 1
                elif opcode == BEQ:
                    self.state.id_control_alu_op = 0b01
                    self.state.id_control_is_branch = 1

            instruction = Instruction(self.state.pipe.if_id.instruction)
            rf_data1 = self.state.register_file[instruction.rs1()]
            rf_data2 = self.state.register_file[instruction.rs2()]
            imm_generation(instruction)
            control(instruction.opcode())
            self.state.id_zero_flag = (rf_data1 == rf_data2)
            self.state.id_branch_address = self.state.pipe.if_id.pc + (
                    self.state.id_sign_extended_immediate << 1)
            self.state.id_control_branch_taken = self.state.id_control_is_branch and self.state.id_zero_flag

            self.state.pipe.id_ex.register_file_data1 = rf_data1
            self.state.pipe.id_ex.register_file_data2 = rf_data2
            self.state.pipe.id_ex.register_file_rd = instruction.rd()
            self.state.pipe.id_ex.control_alu_op = self.state.id_control_alu_op
            self.state.pipe.id_ex.control_alu_src = self.state.id_control_alu_src
            self.state.pipe.id_ex.control_mem_read = self.state.id_control_mem_read
            self.state.pipe.id_ex.control_mem_write = self.state.id_control_mem_write
            self.state.pipe.id_ex.control_reg_write = self.state.id_control_reg_write
            self.state.pipe.id_ex.control_mem_to_reg = self.state.id_control_mem_to_reg
            self.state.pipe.id_ex.sign_extended_immediate = self.state.id_sign_extended_immediate
            self.state.pipe.id_ex.alu_control = (instruction.funct7() & 0b100000) >> 2 | instruction.funct3()
            self.state.pipe.id_ex.instruction = self.state.pipe.if_id.instruction

        def ex_operations():
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

            alu_left_op = self.state.pipe.id_ex.register_file_data1
            alu_right_op = self.state.pipe.id_ex.register_file_data2 if self.state.pipe.id_ex.control_alu_src == 0 else self.state.pipe.id_ex.sign_extended_immediate
            alu_result = alu(alu_control(), alu_left_op, alu_right_op)

            self.state.pipe.ex_mem.control_mem_read = self.state.pipe.id_ex.control_mem_read
            self.state.pipe.ex_mem.control_mem_write = self.state.pipe.id_ex.control_mem_write
            self.state.pipe.ex_mem.control_reg_write = self.state.pipe.id_ex.control_reg_write
            self.state.pipe.ex_mem.control_mem_to_reg = self.state.pipe.id_ex.control_mem_to_reg
            self.state.pipe.ex_mem.alu_result = alu_result
            self.state.pipe.ex_mem.register_file_data2 = self.state.pipe.id_ex.register_file_data2
            self.state.pipe.ex_mem.register_file_rd = self.state.pipe.id_ex.register_file_rd
            self.state.pipe.ex_mem.instruction = self.state.pipe.id_ex.instruction

        def mem_operations():
            address = self.state.pipe.ex_mem.alu_result
            mem_data = self.state.data_memory[address] if self.state.pipe.ex_mem.control_mem_read == 1 else 0
            if self.state.pipe.ex_mem.control_mem_write == 1:
                self.state.data_memory[address] = self.state.pipe.ex_mem.register_file_data2

            self.state.pipe.mem_wb.control_reg_write = self.state.pipe.ex_mem.control_reg_write
            self.state.pipe.mem_wb.control_mem_to_reg = self.state.pipe.ex_mem.control_mem_to_reg
            self.state.pipe.mem_wb.memory_data = mem_data
            self.state.pipe.mem_wb.alu_result = self.state.pipe.ex_mem.alu_result
            self.state.pipe.mem_wb.register_file_rd = self.state.pipe.ex_mem.register_file_rd
            self.state.pipe.mem_wb.instruction = self.state.pipe.ex_mem.instruction

        def wb_operations():
            wb_register_file_write_data = self.state.pipe.mem_wb.alu_result if self.state.pipe.mem_wb.control_mem_to_reg == 0 else self.state.pipe.mem_wb.memory_data

            if self.state.pipe.mem_wb.control_reg_write:
                self.state.register_file[self.state.pipe.mem_wb.register_file_rd] = wb_register_file_write_data

        if int(self.state.if_pc / 4) == len(self.memory):
            return

        self.trace.append(copy.deepcopy(self.state))
        wb_operations()
        mem_operations()
        ex_operations()
        id_operations()
        if_operations()
