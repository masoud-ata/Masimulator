from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from disassembler import *


g_font = "courier"
g_font_size = 10
g_pipe_no_forward_image_file = "images/pipe_simple.png"
g_pipe_with_forward_image_file = "images/pipe_forward.png"
g_hazard_detected_image_file = "images/hazard_detected.png"


class PipelineGraphics:
    def __init__(self, master):
        pipe_pane_x = 20
        pipe_pane_y = 400
        pipe_pane_width = 1300
        pipe_pane_height = 800
        self.pipe_pane = ttk.Panedwindow(master, orient=VERTICAL, width=pipe_pane_width, height=pipe_pane_height)
        self.pipe_pane.place(x=pipe_pane_x, y=pipe_pane_y)

        self._place_pipe_images()

        pipe_distance_x = 250
        self._place_pipe_instruction_labels(self.pipe_pane, x=150, y=630, distance=pipe_distance_x)

        self._setup_pipeline_if_stage_labels()
        self._setup_pipeline_id_stage_labels()
        self._setup_pipeline_ex_stage_labels()
        self._setup_pipeline_mem_stage_labels()
        self._setup_pipeline_wb_stage_labels()

        self.hazard_detection_on = False

    def toggle_forwarding(self, has_forwarding):
        if has_forwarding:
            self.simple_pipe_image.place_forget()
            self.forward_pipe_image.place(x=0, y=0)
            self.ex_forward_mem_to_mux1_label.place(x=self.ex_forward_mem_to_mux1_label_pos[0],
                                                    y=self.ex_forward_mem_to_mux1_label_pos[1])
            self.ex_forward_wb_to_mux1_label.place(x=self.ex_forward_wb_to_mux1_label_pos[0],
                                                    y=self.ex_forward_wb_to_mux1_label_pos[1])
            self.ex_forward_mem_to_mux2_label.place(x=self.ex_forward_mem_to_mux2_label_pos[0],
                                                    y=self.ex_forward_mem_to_mux2_label_pos[1])
            self.ex_forward_wb_to_mux2_label.place(x=self.ex_forward_wb_to_mux2_label_pos[0],
                                                    y=self.ex_forward_wb_to_mux2_label_pos[1])
            self.ex_imm_label.place(x=self.ex_imm_label_with_forward_pos[0], y=self.ex_imm_label_with_forward_pos[1])
            self.ex_right_forward_out_label.place(x=self.ex_right_forward_out_label_pos[0], y=self.ex_right_forward_out_label_pos[1])
        else:
            self.forward_pipe_image.place_forget()
            self.simple_pipe_image.place(x=0, y=0)
            self.ex_forward_mem_to_mux1_label.place_forget()
            self.ex_forward_wb_to_mux1_label.place_forget()
            self.ex_forward_mem_to_mux2_label.place_forget()
            self.ex_forward_wb_to_mux2_label.place_forget()
            self.ex_imm_label.place(x=self.ex_imm_label_no_forward_pos[0], y=self.ex_imm_label_no_forward_pos[1])
            self.ex_right_forward_out_label.place_forget()

    def toggle_hazard_detection(self, has_hazard_detection):
        self.hazard_detection_on = has_hazard_detection == 1

    def refresh_pipeline(self, processor):
        if processor.state.hazard_detected == 1:
            self.hazard_detected_image.place(x=self.hazard_detected_image_pos[0], y=self.hazard_detected_image_pos[1])
        else:
            self.hazard_detected_image.place_forget()

        self._refresh_instructions(processor)
        self._refresh_if_signals(processor)
        self._refresh_id_signals(processor)
        self._refresh_ex_signals(processor)
        self._refresh_mem_signals(processor)
        self._refresh_wb_signals(processor)

    def _refresh_instructions(self, processor):
        self._color_inserted_nops(processor)

        self.if_instruction.set(disassemble(processor.state.signals.if_signals.instruction) + "\n" + "0x{:08x}".format(
            processor.state.signals.if_signals.instruction))
        self.id_instruction.set(disassemble(processor.state.pipe.if_id.instruction) + "\n" + "0x{:08x}".format(
            processor.state.pipe.if_id.instruction))
        self.ex_instruction.set(disassemble(processor.state.pipe.id_ex.instruction) + "\n" + "0x{:08x}".format(
            processor.state.pipe.id_ex.instruction))
        self.mem_instruction.set(disassemble(processor.state.pipe.ex_mem.instruction) + "\n" + "0x{:08x}".format(
            processor.state.pipe.ex_mem.instruction))
        self.wb_instruction.set(disassemble(processor.state.pipe.mem_wb.instruction) + "\n" + "0x{:08x}".format(
            processor.state.pipe.mem_wb.instruction))

    def _color_inserted_nops(self, processor):
        self.id_instruction_label.config(fg="black")
        self.ex_instruction_label.config(fg="black")
        self.mem_instruction_label.config(fg="black")
        self.wb_instruction_label.config(fg="black")
        if processor.state.pipe.if_id.nop_inserted:
            self.id_instruction_label.config(fg="red")
        if processor.state.pipe.id_ex.nop_inserted:
            self.ex_instruction_label.config(fg="red")
        if processor.state.pipe.ex_mem.nop_inserted:
            self.mem_instruction_label.config(fg="red")
        if processor.state.pipe.mem_wb.nop_inserted:
            self.wb_instruction_label.config(fg="red")

    def _refresh_if_signals(self, processor):
        self.if_pc_mux_1.set("" + str(processor.state.signals.if_signals.pc + 4))
        self.if_pc_mux_2.set(str(processor.state.signals.id_signals.branch_address))
        self.if_pc_in.set("" + str(processor.state.signals.if_signals.next_pc))
        self.if_pc_out.set("" + str(processor.state.signals.if_signals.pc))
        self.if_pc_out_plus_4.set("" + str(processor.state.signals.if_signals.pc + 4))
        self.if_program_mem_out.set("0x{:08x}".format(processor.state.signals.if_signals.instruction))

    def _refresh_id_signals(self, processor):
        self.id_pc_plus_4.set(processor.state.pipe.if_id.pc_plus_4)
        self.id_pc.set(processor.state.pipe.if_id.pc)
        self.id_imm.set(processor.state.signals.id_signals.sign_extended_immediate)
        self.id_imm_to_ex.set(processor.state.signals.id_signals.sign_extended_immediate)
        self.id_imm_shifted.set(processor.state.signals.id_signals.sign_extended_immediate*2)
        self.id_rs1.set(processor.state.signals.id_signals.rs1)
        self.id_branch_addr.set(str(processor.state.signals.id_signals.branch_address))
        self.id_rs1.set(processor.state.signals.id_signals.rs1)
        self.id_rs2.set(processor.state.signals.id_signals.rs2)
        self.id_rf_read_1.set(processor.state.signals.id_signals.rf_data1)
        self.id_rf_read_2.set(processor.state.signals.id_signals.rf_data2)
        self.id_rd.set(processor.state.signals.id_signals.instruction.rd())

    def _refresh_ex_signals(self, processor):
        self.ex_pc_plus_4.set(processor.state.pipe.id_ex.pc_plus_4)
        self.ex_rf_data1.set(processor.state.pipe.id_ex.register_file_data1)
        self.ex_rf_data2.set(processor.state.pipe.id_ex.register_file_data2)
        self.ex_imm.set(processor.state.pipe.id_ex.sign_extended_immediate)
        self.ex_right_forward_out.set(processor.state.signals.ex_signals.right_forward_out)
        self.ex_forward_mem_to_mux1.set(processor.state.pipe.ex_mem.alu_result)
        self.ex_forward_mem_to_mux2.set(processor.state.pipe.ex_mem.alu_result)
        self.ex_forward_wb_to_mux1.set(processor.state.signals.wb_signals.rf_write_data)
        self.ex_forward_wb_to_mux2.set(processor.state.signals.wb_signals.rf_write_data)
        self.ex_alu_left.set(processor.state.signals.ex_signals.alu_left_op)
        self.ex_alu_right.set(processor.state.signals.ex_signals.alu_right_op)
        self.ex_alu_result.set(processor.state.signals.ex_signals.alu_result)
        self.ex_rf_data2_to_mem_stage.set(processor.state.signals.ex_signals.right_forward_out)
        self.ex_rd.set(processor.state.pipe.id_ex.register_file_rd)

    def _refresh_mem_signals(self, processor):
        self.mem_pc_plus_4.set(processor.state.pipe.ex_mem.pc_plus_4)
        self.mem_address.set(processor.state.pipe.ex_mem.alu_result)
        self.mem_alu_result_to_wb.set(processor.state.pipe.ex_mem.alu_result)
        self.mem_write_data.set(processor.state.pipe.ex_mem.register_file_data2)
        self.mem_read.set(processor.state.signals.mem_signals.mem_data)
        self.mem_rd.set(processor.state.pipe.ex_mem.register_file_rd)

    def _refresh_wb_signals(self, processor):
        self.wb_pc_plus_4.set(processor.state.pipe.mem_wb.pc_plus_4)
        self.wb_memory_data.set(processor.state.pipe.mem_wb.memory_data)
        self.wb_alu_result.set(processor.state.pipe.mem_wb.alu_result)
        self.wb_rf_write_data.set(processor.state.signals.wb_signals.rf_write_data)
        self.wb_rf_write_data_shown_at_id.set(processor.state.signals.wb_signals.rf_write_data)
        self.wb_rd.set(processor.state.pipe.mem_wb.register_file_rd)
        self.wb_rd_shown_at_id.set(processor.state.pipe.mem_wb.register_file_rd)

    def _place_pipe_images(self):
        self.load1 = Image.open(g_pipe_no_forward_image_file)
        self.render1 = ImageTk.PhotoImage(self.load1)
        self.load2 = Image.open(g_pipe_with_forward_image_file)
        self.render2 = ImageTk.PhotoImage(self.load2)

        self.simple_pipe_image = Label(self.pipe_pane, image=self.render1)
        self.simple_pipe_image.image = self.render1
        self.simple_pipe_image.place(x=0, y=0)

        self.forward_pipe_image = Label(self.pipe_pane, image=self.render2)
        self.forward_pipe_image.image = self.render2
        self.forward_pipe_image.place(x=0, y=0)
        self.forward_pipe_image.place_forget()

        load = Image.open(g_hazard_detected_image_file)
        render = ImageTk.PhotoImage(load)
        self.hazard_detected_image = Label(self.pipe_pane, image=render)
        self.hazard_detected_image.image = render
        self.hazard_detected_image_pos = 450, 120
        self.hazard_detected_image.place(x=self.hazard_detected_image_pos[0], y=self.hazard_detected_image_pos[1])
        self.hazard_detected_image.place_forget()

    def _place_pipe_instruction_labels(self, pipe_pane, x, y, distance):
        self.if_instruction = StringVar()
        self.if_instruction.set("")
        self.if_instruction_label = Label(pipe_pane, textvariable=self.if_instruction, relief=GROOVE, font=(g_font, g_font_size))
        self.if_instruction_label.place(x=x, y=y)

        self.id_instruction = StringVar()
        self.id_instruction.set("")
        self.id_instruction_label = Label(pipe_pane, textvariable=self.id_instruction, relief=GROOVE, font=(g_font, g_font_size))
        self.id_instruction_label.place(x=x+distance, y=y)

        self.ex_instruction = StringVar()
        self.ex_instruction.set("")
        self.ex_instruction_label = Label(pipe_pane, textvariable=self.ex_instruction, relief=GROOVE, font=(g_font, g_font_size))
        self.ex_instruction_label.place(x=x+2*distance+20, y=y)

        self.mem_instruction = StringVar()
        self.mem_instruction.set("")
        self.mem_instruction_label = Label(pipe_pane, textvariable=self.mem_instruction, relief=GROOVE, font=(g_font, g_font_size))
        self.mem_instruction_label.place(x=x+3*distance+30, y=y)

        self.wb_instruction = StringVar()
        self.wb_instruction.set("")
        self.wb_instruction_label = Label(pipe_pane, textvariable=self.wb_instruction, relief=GROOVE, font=(g_font, g_font_size))
        self.wb_instruction_label.place(x=x+4*distance, y=y)

    def _setup_pipeline_if_stage_labels(self):
        self.if_pc_mux_1 = StringVar()
        self.if_pc_mux_1.set("")
        self.if_pc_mux_1_label = Label(self.pipe_pane, textvariable=self.if_pc_mux_1, relief=FLAT, font=(g_font, g_font_size))
        self.if_pc_mux_1_label.place(x=20, y=280)

        self.if_pc_mux_2 = StringVar()
        self.if_pc_mux_2.set("")
        self.if_pc_mux_2_label = Label(self.pipe_pane, textvariable=self.if_pc_mux_2, relief=FLAT, font=(g_font, g_font_size))
        self.if_pc_mux_2_label.place(x=20, y=370)

        self.if_pc_in = StringVar()
        self.if_pc_in.set("")
        self.if_pc_in_label = Label(self.pipe_pane, textvariable=self.if_pc_in, relief=FLAT, font=(g_font, g_font_size))
        self.if_pc_in_label.place(x=60, y=300)

        self.if_pc_out = StringVar()
        self.if_pc_out.set("")
        label = Label(self.pipe_pane, textvariable=self.if_pc_out, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=130, y=300)

        self.if_pc_out_plus_4 = StringVar()
        self.if_pc_out_plus_4.set("")
        label = Label(self.pipe_pane, textvariable=self.if_pc_out_plus_4, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=260, y=124)

        self.if_program_mem_out = StringVar()
        self. if_program_mem_out.set("")
        label = Label(self.pipe_pane, textvariable=self.if_program_mem_out, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=250, y=300)

    def _setup_pipeline_id_stage_labels(self):
        self.id_pc_plus_4 = StringVar()
        label = Label(self.pipe_pane, textvariable=self.id_pc_plus_4, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=490, y=120)

        self.id_pc = StringVar()
        label = Label(self.pipe_pane, textvariable=self.id_pc, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=400, y=20)

        self.id_imm = StringVar()
        label = Label(self.pipe_pane, textvariable=self.id_imm, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=410, y=160)

        self.id_imm_to_ex = StringVar()
        label = Label(self.pipe_pane, textvariable=self.id_imm_to_ex, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=500, y=460)

        self.id_imm_shifted = StringVar()
        label = Label(self.pipe_pane, textvariable=self.id_imm_shifted, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=400, y=65)

        self.id_branch_addr = StringVar()
        label = Label(self.pipe_pane, textvariable=self.id_branch_addr, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=490, y=70)

        self.id_rs1 = StringVar()
        label = Label(self.pipe_pane, textvariable=self.id_rs1, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=430, y=190)

        self.id_rs2 = StringVar()
        label = Label(self.pipe_pane, textvariable=self.id_rs2, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=430, y=270)

        self.id_rf_read_1 = StringVar()
        label = Label(self.pipe_pane, textvariable=self.id_rf_read_1, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=530, y=190)

        self.id_rf_read_2 = StringVar()
        label = Label(self.pipe_pane, textvariable=self.id_rf_read_2, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=530, y=270)

        self.id_rd = StringVar()
        label = Label(self.pipe_pane, textvariable=self.id_rd, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=500, y=520)

    def _setup_pipeline_ex_stage_labels(self):
        self.ex_pc_plus_4 = StringVar()
        label = Label(self.pipe_pane, textvariable=self.ex_pc_plus_4, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=800, y=120)

        self.ex_rf_data1 = StringVar()
        label = Label(self.pipe_pane, textvariable=self.ex_rf_data1, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=640, y=185)

        self.ex_forward_mem_to_mux1 = StringVar()
        self.ex_forward_mem_to_mux1_label = Label(self.pipe_pane, textvariable=self.ex_forward_mem_to_mux1, relief=FLAT, font=(g_font, g_font_size))
        self.ex_forward_mem_to_mux1_label_pos = 640, 214
        self.ex_forward_mem_to_mux1_label.place(x=self.ex_forward_mem_to_mux1_label_pos[0], y=self.ex_forward_mem_to_mux1_label_pos[1])
        self.ex_forward_mem_to_mux1_label.place_forget()

        self.ex_forward_wb_to_mux1 = StringVar()
        self.ex_forward_wb_to_mux1_label = Label(self.pipe_pane, textvariable=self.ex_forward_wb_to_mux1, relief=FLAT, font=(g_font, g_font_size))
        self.ex_forward_wb_to_mux1_label_pos = 640, 238
        self.ex_forward_wb_to_mux1_label.place(x=self.ex_forward_wb_to_mux1_label_pos[0], y=self.ex_forward_wb_to_mux1_label_pos[1])
        self.ex_forward_wb_to_mux1_label.place_forget()

        self.ex_rf_data2 = StringVar()
        label = Label(self.pipe_pane, textvariable=self.ex_rf_data2, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=640, y=270)

        self.ex_imm = StringVar()
        self.ex_imm_label = Label(self.pipe_pane, textvariable=self.ex_imm, relief=FLAT, font=(g_font, g_font_size))
        self.ex_imm_label_no_forward_pos = 640, 300
        self.ex_imm_label_with_forward_pos = 710, 340
        self.ex_imm_label.place(x=self.ex_imm_label_no_forward_pos[0], y=self.ex_imm_label_no_forward_pos[1])

        self.ex_right_forward_out = StringVar()
        self.ex_right_forward_out_label = Label(self.pipe_pane, textvariable=self.ex_right_forward_out, relief=FLAT, font=(g_font, g_font_size))
        self.ex_right_forward_out_label_pos = 710, 295
        self.ex_right_forward_out_label.place(x=self.ex_right_forward_out_label_pos[0], y=self.ex_right_forward_out_label_pos[1])
        self.ex_right_forward_out_label.place_forget()

        self.ex_forward_mem_to_mux2 = StringVar()
        self.ex_forward_mem_to_mux2_label = Label(self.pipe_pane, textvariable=self.ex_forward_mem_to_mux2, relief=FLAT, font=(g_font, g_font_size))
        self.ex_forward_mem_to_mux2_label_pos = 640, 300
        self.ex_forward_mem_to_mux2_label.place(x=self.ex_forward_mem_to_mux2_label_pos[0], y=self.ex_forward_mem_to_mux2_label_pos[1])
        self.ex_forward_mem_to_mux2_label.place_forget()

        self.ex_forward_wb_to_mux2 = StringVar()
        self.ex_forward_wb_to_mux2_label = Label(self.pipe_pane, textvariable=self.ex_forward_wb_to_mux2, relief=FLAT, font=(g_font, g_font_size))
        self.ex_forward_wb_to_mux2_label_pos = 640, 330
        self.ex_forward_wb_to_mux2_label.place(x=self.ex_forward_wb_to_mux2_label_pos[0], y=self.ex_forward_wb_to_mux2_label_pos[1])
        self.ex_forward_wb_to_mux2_label.place_forget()

        self.ex_alu_left = StringVar()
        label = Label(self.pipe_pane, textvariable=self.ex_alu_left, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=770, y=214)

        self.ex_alu_right = StringVar()
        label = Label(self.pipe_pane, textvariable=self.ex_alu_right, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=770, y=278)

        self.ex_alu_result = StringVar()
        label = Label(self.pipe_pane, textvariable=self.ex_alu_result, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=845, y=245)

        self.ex_rf_data2_to_mem_stage = StringVar()
        label = Label(self.pipe_pane, textvariable=self.ex_rf_data2_to_mem_stage, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=820, y=375)

        self.ex_rd = StringVar()
        label = Label(self.pipe_pane, textvariable=self.ex_rd, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=820, y=520)

    def _setup_pipeline_mem_stage_labels(self):
        self.mem_pc_plus_4 = StringVar()
        label = Label(self.pipe_pane, textvariable=self.mem_pc_plus_4, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=1010, y=120)

        self.mem_address = StringVar()
        label = Label(self.pipe_pane, textvariable=self.mem_address, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=920, y=240)

        self.mem_write_data = StringVar()
        label = Label(self.pipe_pane, textvariable=self.mem_write_data, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=920, y=375)

        self.mem_rd = StringVar()
        label = Label(self.pipe_pane, textvariable=self.mem_rd, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=1030, y=520)

        self.mem_read = StringVar()
        label = Label(self.pipe_pane, textvariable=self.mem_read, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=1040, y=240)

        self.mem_alu_result_to_wb = StringVar()
        label = Label(self.pipe_pane, textvariable=self.mem_alu_result_to_wb, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=1040, y=285)

    def _setup_pipeline_wb_stage_labels(self):
        self.wb_pc_plus_4 = StringVar()
        label = Label(self.pipe_pane, textvariable=self.wb_pc_plus_4, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=1130, y=210)

        self.wb_memory_data = StringVar()
        label = Label(self.pipe_pane, textvariable=self.wb_memory_data, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=1115, y=245)

        self.wb_alu_result = StringVar()
        label = Label(self.pipe_pane, textvariable=self.wb_alu_result, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=1115, y=285)

        self.wb_rd = StringVar()
        label = Label(self.pipe_pane, textvariable=self.wb_rd, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=1115, y=520)

        self.wb_rf_write_data = StringVar()
        label = Label(self.pipe_pane, textvariable=self.wb_rf_write_data, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=1180, y=259)

        self.wb_rf_write_data_shown_at_id = StringVar()
        label = Label(self.pipe_pane, textvariable=self.wb_rf_write_data_shown_at_id, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=420, y=310)

        self.wb_rd_shown_at_id = StringVar()
        label = Label(self.pipe_pane, textvariable=self.wb_rd_shown_at_id, relief=FLAT, font=(g_font, g_font_size))
        label.place(x=430, y=340)
