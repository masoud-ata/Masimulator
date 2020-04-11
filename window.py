from tkinter import *
from tkinter import ttk, messagebox
from disassembler import *
from PIL import Image, ImageTk
from cpu import *
from pipeline_visual import PipelineGraphics
from pipeline_visual import mas
from tkinter import filedialog
from rvi import assemble_again


def _setup_buttons(master, cpu_step, cpu_back, cpu_reset):
    buttons_pane = ttk.Panedwindow(master, width=100, height=50)
    buttons_pane.place(x=0, y=0)
    step_button = Button(buttons_pane, text="Step (F1)", command=cpu_step)
    step_button.grid(row=0, column=0, sticky=W)
    back_button = Button(buttons_pane, text="Back (F2)", command=cpu_back)
    back_button.grid(row=0, column=1, sticky=W)
    reset_button = Button(buttons_pane, text="Reset (F3)", command=cpu_reset)
    reset_button.grid(row=0, column=2, sticky=W)


def _setup_check_buttons(master, forwarding_en, toggle_forwarding):
    check_buttons_pane = ttk.Panedwindow(master, width=100, height=50)
    check_buttons_pane.place(x=0, y=80)
    c = Checkbutton(check_buttons_pane, text="Enable forwarding", variable=forwarding_en, command=toggle_forwarding)
    c.grid(row=1, column=0, sticky=W)


def _setup_register_file_entries(master):
    rf_pane = ttk.Panedwindow(master, orient=VERTICAL, width=200, height=100)
    rf_pane.place(x=200, y=0)

    l = Label(rf_pane, text="Register file")
    l.grid(row=0, column=1, sticky=W)

    entries = []
    for i in range(0, 32):
        entries.append(Entry(rf_pane, width=10))
        entries[i].grid(row=int(1 + i % 16), column=1 + 2 * int(i / 16), sticky=W)
        l = Label(rf_pane, text="x" + str(i))
        l.grid(row=int(1 + i % 16), column=2 * int(i / 16), sticky=W)

    return entries


def _setup_data_mem_box(master, data_memory, data_mem_yview, data_mem_yview_tie):
    mem_pane = ttk.Panedwindow(master, orient=VERTICAL, width=200, height=100)
    mem_pane.place(x=500, y=0)

    l = Label(mem_pane, text="Address")
    l.grid(row=0, column=0, sticky=W)
    l = Label(mem_pane, text="Data Memory")
    l.grid(row=0, column=1, sticky=W)

    mem_text = Text(mem_pane, height=20, width=12)
    mem_text.grid(row=1, column=1, sticky=W)
    scrollbar = Scrollbar(mem_pane, orient=VERTICAL, command=data_mem_yview)
    scrollbar.grid(row=1, column=2, rowspan=15, columnspan=1, sticky=NS)
    mem_text.config(yscrollcommand=data_mem_yview_tie)

    mem_addr_text = Text(mem_pane, height=20, width=5)
    mem_addr_text.grid(row=1, column=0, sticky=W)
    mem_addr_text.config(yscrollcommand=data_mem_yview_tie)

    text = ""
    addr_text = ""
    address = 0
    for value in data_memory:
        text = text + '{0:08x}'.format(int(value)) + "\n"
        addr_text = addr_text + str(address) + "\n"
        address = address + 4

    text = text[:-len("\n")]
    addr_text = addr_text[:-len("\n")]
    mem_text.insert(END, text)
    mem_addr_text.insert(END, addr_text)
    mem_addr_text.config(state=DISABLED)

    return [mem_text, mem_addr_text, scrollbar]


def _setup_program_mem_box(master, program_memory, program_mem_yview, program_mem_yview_tie):
    prog_mem_pane = ttk.Panedwindow(master, orient=VERTICAL, width=200, height=100)
    prog_mem_pane.place(x=700, y=0)

    l = Label(prog_mem_pane, text="Address")
    l.grid(row=0, column=0, sticky=W)
    l = Label(prog_mem_pane, text="Program Memory")
    l.grid(row=0, column=1, sticky=W)

    mem_text = Text(prog_mem_pane, height=20, width=20)
    mem_text.grid(row=1, column=1, sticky=W)
    scrollbar = Scrollbar(prog_mem_pane, orient=VERTICAL, command=program_mem_yview)
    scrollbar.grid(row=1, column=2, rowspan=15, columnspan=1, sticky=NS)
    mem_text.config(yscrollcommand=program_mem_yview_tie)

    mem_addr_text = Text(prog_mem_pane, height=20, width=5)
    mem_addr_text.grid(row=1, column=0, sticky=W)
    mem_addr_text.config(yscrollcommand=program_mem_yview_tie)

    text = ""
    address_text = ""
    addr = 0
    for value in program_memory:
        text = text + disassemble(value) + "\n"
        address_text = address_text + str(addr) + "\n"
        addr = addr + 4

    text = text[:-len("\n")]
    address_text = address_text[:-len("\n")]
    mem_text.insert(END, text)
    mem_addr_text.insert(END, address_text)
    mem_addr_text.config(state=DISABLED)

    return [mem_text, mem_addr_text, scrollbar]


def _about_window():
    messagebox.showinfo("About", "Created by MJ!")


# def _open_window():
#     master.filename = filedialog.askopenfilename(initialdir="/", title="Select file", filetypes=(("jpeg files", "*.jpg"), ("all files", "*.*")))


class Screen:
    def __init__(self, width, height):
        self.risc_v = CPU()
        self.register_file_entries = []

        self.master = Tk()
        self.master.wm_title("RISC-V Masimulator")
        self.master.geometry(width + "x" + height)

        self._setup_menus(self.master)
        _setup_buttons(self.master, self.step_callback, self.backstep_callback, self.reset_callback)

        self.forwarding_enabled = IntVar()
        _setup_check_buttons(self.master, self.forwarding_enabled, self.toggle_forwarding_callback)

        self.register_file_entries = _setup_register_file_entries(self.master)
        [self.data_memory_box, self.data_memory_address_box, self.data_mem_scrollbar] = \
            _setup_data_mem_box(self.master, self.risc_v.state.data_memory, self.data_mem_yview,
                                self.data_mem_yview_tie)
        [self.program_memory_box, self.program_memory_address_box, self.program_mem_scrollbar] = \
            _setup_program_mem_box(self.master, self.risc_v.memory, self.program_mem_yview, self.program_mem_yview_tie)

        self.pipe_graphics = PipelineGraphics(self.master)
        [self.if_inst, self.if_id_inst, self.id_ex_inst, self.ex_mem_inst,
         self.mem_wb_inst, self.if_pc_in, self.if_pc_out, self.prog_mem_out, self.id_branch_addr,
         self.id_rs1, self.id_rs2, self.alu_left, self.alu_right] = self.pipe_graphics.setup_pipeline_box()

        self.reset_callback()

        self.master.bind('<Key>', lambda a: self._key_press_callback(a))

        mainloop()

    def _setup_menus(self, master):
        menu = Menu(master)
        master.config(menu=menu)

        file_menu = Menu(menu)
        menu.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Open & Assemble ...', command=self._open_and_assemble)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=master.quit)

        help_menu = Menu(menu)
        menu.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='About', command=_about_window)

    def _open_and_assemble(self):
        filename = filedialog.askopenfilename(initialdir=".", title="Select file", filetypes=(("Assembly files", "*.rvi"), ("all files", "*.*")))
        if filename != "":
            assemble_again(filename)
            self.risc_v.read_program_memory()
            [self.program_memory_box, self.program_memory_address_box, self.program_mem_scrollbar] = \
                _setup_program_mem_box(self.master, self.risc_v.memory, self.program_mem_yview, self.program_mem_yview_tie)
            self.reset_callback()

    def _key_press_callback(self, event):
        key = event.keysym
        if key == "F1":
            self.step_callback()
        elif key == "F2":
            self.backstep_callback()
        elif key == "F3":
            self.reset_callback()

    def refresh_pipeline_box(self):
        self.if_inst.set(disassemble(self.risc_v.state.signals.if_signals.instruction) + "\n" + "0x{:08x}".format(
            self.risc_v.state.signals.if_signals.instruction))
        self.if_id_inst.set(disassemble(self.risc_v.state.pipe.if_id.instruction) + "\n" + "0x{:08x}".format(
            self.risc_v.state.pipe.if_id.instruction))
        self.id_ex_inst.set(disassemble(self.risc_v.state.pipe.id_ex.instruction) + "\n" + "0x{:08x}".format(
            self.risc_v.state.pipe.id_ex.instruction))
        self.ex_mem_inst.set(disassemble(self.risc_v.state.pipe.ex_mem.instruction) + "\n" + "0x{:08x}".format(
            self.risc_v.state.pipe.ex_mem.instruction))
        self.mem_wb_inst.set(disassemble(self.risc_v.state.pipe.mem_wb.instruction) + "\n" + "0x{:08x}".format(
            self.risc_v.state.pipe.mem_wb.instruction))

        self.id_branch_addr.set(str(self.risc_v.state.signals.id_signals.branch_address))
        self.if_pc_in.set("" + str(self.risc_v.state.signals.if_signals.next_pc))
        self.if_pc_out.set("" + str(self.risc_v.state.signals.if_signals.pc))
        self.prog_mem_out.set("0x{:08x}".format(self.risc_v.state.signals.if_signals.instruction))
        self.id_rs1.set(self.risc_v.state.signals.id_signals.rs1)
        self.id_rs2.set(self.risc_v.state.signals.id_signals.rs2)
        self.alu_left.set(self.risc_v.state.signals.ex_signals.alu_left_op)
        self.alu_right.set(self.risc_v.state.signals.ex_signals.alu_right_op)
        m = mas()

    def program_mem_yview_tie(self, *args):
        self.program_memory_box.yview_moveto(args[0])
        self.program_memory_address_box.yview_moveto(args[0])
        self.program_mem_scrollbar.set(args[0], args[1])

    def program_mem_yview(self, *args):
        self.program_memory_box.yview(*args)
        self.program_memory_address_box.yview(*args)

    def data_mem_yview_tie(self, *args):
        self.data_memory_box.yview_moveto(args[0])
        self.data_memory_address_box.yview_moveto(args[0])
        self.data_mem_scrollbar.set(args[0], args[1])

    def data_mem_yview(self, *args):
        self.data_memory_box.yview(*args)
        self.data_memory_address_box.yview(*args)

    def modify_register_file(self):
        for i in range(32):
            try:
                reg1 = int(self.register_file_entries[i].get())
                self.risc_v.state.register_file[i] = reg1
            except ValueError:
                self.register_file_entries[i].delete(0, 'end')
                self.register_file_entries[i].insert(0, self.risc_v.state.register_file[i])

    def refresh_register_file_box(self):
        for i in range(32):
            value_before = self.register_file_entries[i].get()
            value_now = str(self.risc_v.state.register_file[i])
            self.register_file_entries[i].delete(0, 'end')
            self.register_file_entries[i].insert(0, self.risc_v.state.register_file[i])
            if value_before != value_now:
                self.register_file_entries[i].config({"background": "Yellow"})
            else:
                self.register_file_entries[i].config({"background": "White"})

    def modify_data_memory(self):
        text = self.data_memory_box.get("1.0", END)
        text = text.replace("\t", "        ")
        text = text.split("\n")

        address = 0
        max_width = 8
        for elem in text:
            if len(elem) >= max_width:
                for i in range(0, len(elem), max_width):
                    try:
                        mem_data = int(elem[i:i + max_width], 16)
                        self.risc_v.state.data_memory[address] = mem_data
                    except (ValueError, IndexError) as error:
                        pass
                    address = address + 1
            else:
                try:
                    mem_data = int(elem, 16)
                    self.risc_v.state.data_memory[address] = mem_data
                except (ValueError, IndexError) as error:
                    pass
                address = address + 1

    def refresh_program_memory_box(self, p_mem_yview_old):
        self.program_memory_box.config(state=NORMAL)
        for tag in self.program_memory_box.tag_names():
            self.program_memory_box.tag_delete(tag)

        pc = int(self.risc_v.state.signals.if_signals.pc / 4)
        value = disassemble(self.risc_v.memory[pc])
        row = pc + 1
        self.program_memory_box.tag_add("here", str(row) + ".0", str(row) + "." + str(len(value)))
        self.program_memory_box.tag_config("here", background="green", foreground="yellow")
        self.program_memory_box.yview_moveto(p_mem_yview_old)
        self.program_memory_box.config(state=DISABLED)

    def refresh_colored_data_memory_box(self, data_mem_old, d_mem_yview_old):
        self.refresh_data_memory_box()

        address = 0
        for value in self.risc_v.state.data_memory:
            value = '{0:08x}'.format(value) + "\n"
            if data_mem_old[address] != self.risc_v.state.data_memory[address]:
                self.data_memory_box.tag_add("here", str(address + 1) + ".0", str(address + 1) + "." + str(len(value)))
                self.data_memory_box.tag_config("here", background="blue", foreground="yellow")
                break
            address = address + 1

        self.data_memory_box.yview_moveto(d_mem_yview_old)

    def refresh_data_memory_box(self):
        for tag in self.data_memory_box.tag_names():
            self.data_memory_box.tag_delete(tag)

        text = ""
        self.data_memory_box.delete('1.0', END)
        self.data_memory_box.edit_reset()
        for value in self.risc_v.state.data_memory:
            text = text + '{0:08x}'.format(int(value)) + "\n"
        text = text[:-len("\n")]
        self.data_memory_box.insert(END, text)

    def step_callback(self):
        self.modify_register_file()
        self.modify_data_memory()

        data_mem_old = self.risc_v.state.data_memory.copy()
        d_mem_yview_old = self.data_memory_box.yview()[0]
        p_mem_yview_old = self.program_memory_box.yview()[0]

        self.risc_v.tick()
        self.risc_v.calculate_signals()

        self.refresh_program_memory_box(p_mem_yview_old)
        self.refresh_register_file_box()
        self.refresh_colored_data_memory_box(data_mem_old, d_mem_yview_old)
        self.refresh_pipeline_box()

    def backstep_callback(self):
        data_mem_old = self.risc_v.state.data_memory.copy()
        d_mem_yview_old = self.data_memory_box.yview()[0]
        p_mem_yview_old = self.program_memory_box.yview()[0]

        self.risc_v.back_tick()

        self.refresh_program_memory_box(p_mem_yview_old)
        self.refresh_register_file_box()
        self.refresh_colored_data_memory_box(data_mem_old, d_mem_yview_old)
        self.refresh_pipeline_box()

    def reset_callback(self):
        self.risc_v.reset()
        self.risc_v.calculate_signals()

        self.refresh_register_file_box()
        self.refresh_data_memory_box()
        self.refresh_program_memory_box(0)
        self.refresh_pipeline_box()

    def toggle_forwarding_callback(self):
        self.pipe_graphics.toggle_forwarding(self.forwarding_enabled.get())
        self.reset_callback()
        self.risc_v.forwarding_enabled = self.forwarding_enabled.get()
