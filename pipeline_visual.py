from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk


class MasInfo:
    def __init__(self):
        self.id_rs1 = 0


def mas():
    return MasInfo()


class PipelineGraphics:
    def __init__(self, master):
        pipe_pane_x = 20
        pipe_pane_y = 400
        pipe_pane_width = 1200
        pipe_pane_height = 800
        self.pipe_pane = ttk.Panedwindow(master, orient=VERTICAL, width=pipe_pane_width, height=pipe_pane_height)
        self.pipe_pane.place(x=pipe_pane_x, y=pipe_pane_y)

        self.load1 = Image.open("images/pipe_all.png")
        self.render1 = ImageTk.PhotoImage(self.load1)
        self.load2 = Image.open("images/pipe_all2.png")
        self.render2 = ImageTk.PhotoImage(self.load2)

        self.pipe_image1 = Label(self.pipe_pane, image=self.render1)
        self.pipe_image1.image = self.render1
        self.pipe_image1.place(x=0, y=0)

        self.pipe_image2 = Label(self.pipe_pane, image=self.render2)
        self.pipe_image2.image = self.render2
        self.pipe_image2.place(x=0, y=0)
        self.pipe_image2.place_forget()

        self.if_pc_in = StringVar()
        self.if_pc_in.set("pc")
        self.if_pc_in_label = Label(self.pipe_pane, textvariable=self.if_pc_in, relief=FLAT, font=("courier", 10))
        self.if_pc_in_label.place(x=50, y=300)

    def toggle_forwarding(self, choice):
        if choice == 1:
            self.pipe_image1.place_forget()
            self.pipe_image2.place(x=0, y=0)
        else:
            self.pipe_image2.place_forget()
            self.pipe_image1.place(x=0, y=0)

    def setup_pipeline_box(self):
        pipe_distance_x = 220
        pipe_if_id_x = 200
        pipes_y = 0

        # _place_pipes(pipe_pane, x=pipe_if_id_x, y=pipes_y, distance=pipe_distance_x)
        [if_inst, if_id_inst, id_ex_inst, ex_mem_inst, mem_wb_inst] = _place_instruction_labels(self.pipe_pane, x=150, y=600, distance=pipe_distance_x)

        if_pc_out = StringVar()
        if_pc_out.set("")
        label = Label(self.pipe_pane, textvariable=if_pc_out, relief=FLAT, font=("courier", 10))
        label.place(x=110, y=300)

        prog_mem_out = StringVar()
        prog_mem_out.set("br_addr")
        label = Label(self.pipe_pane, textvariable=prog_mem_out, relief=FLAT, font=("courier", 10))
        label.place(x=250, y=300)

        id_branch_addr = StringVar()
        id_branch_addr.set("br_addr")
        label = Label(self.pipe_pane, textvariable=id_branch_addr, relief=FLAT, font=("courier", 10))
        label.place(x=500, y=60)

        id_rs1 = StringVar()
        id_rs1.set("rs1")
        label = Label(self.pipe_pane, textvariable=id_rs1, relief=FLAT, font=("courier", 10))
        label.place(x=360, y=210)

        id_rs2 = StringVar()
        id_rs2.set("rs2")
        label = Label(self.pipe_pane, textvariable=id_rs2, relief=FLAT, font=("courier", 10))
        label.place(x=360, y=270)

        ex_alu_left = StringVar()
        ex_alu_left.set("alu_l")
        label = Label(self.pipe_pane, textvariable=ex_alu_left, relief=FLAT, font=("courier", 10))
        label.place(x=600, y=220)

        ex_alu_right = StringVar()
        ex_alu_right.set("alu_r")
        label = Label(self.pipe_pane, textvariable=ex_alu_right, relief=FLAT, font=("courier", 10))
        label.place(x=600, y=330)

        return [if_inst, if_id_inst, id_ex_inst, ex_mem_inst, mem_wb_inst, self.if_pc_in, if_pc_out, prog_mem_out, id_branch_addr,
                id_rs1, id_rs2, ex_alu_left, ex_alu_right]


def _place_instruction_labels(pipe_pane, x, y, distance):
    font_size = 11
    font = "courier"
    if_inst = StringVar()
    if_inst.set("")
    label = Label(pipe_pane, textvariable=if_inst, relief=FLAT, font=(font, font_size))
    label.place(x=x, y=y)

    if_id_inst = StringVar()
    if_id_inst.set("")
    label = Label(pipe_pane, textvariable=if_id_inst, relief=FLAT, font=(font, font_size))
    label.place(x=x+distance, y=y)

    id_ex_inst = StringVar()
    id_ex_inst.set("")
    label = Label(pipe_pane, textvariable=id_ex_inst, relief=FLAT, font=(font, font_size))
    label.place(x=x+2*distance, y=y)

    ex_mem_inst = StringVar()
    ex_mem_inst.set("")
    label = Label(pipe_pane, textvariable=ex_mem_inst, relief=FLAT, font=(font, font_size))
    label.place(x=x+3*distance, y=y)

    mem_wb_inst = StringVar()
    mem_wb_inst.set("")
    label = Label(pipe_pane, textvariable=mem_wb_inst, relief=FLAT, font=(font, font_size))
    label.place(x=x+4*distance, y=y)

    return [if_inst, if_id_inst, id_ex_inst, ex_mem_inst, mem_wb_inst]