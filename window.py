from tkinter import *
from tkinter import ttk, messagebox
from disassembler import *
from PIL import Image, ImageTk
from cpu import *

def _setup_menus(master):
    menu = Menu(master)
    master.config(menu=menu)

    file_menu = Menu(menu)
    menu.add_cascade(label='File', menu=file_menu)
    file_menu.add_command(label='Open...')
    file_menu.add_separator()
    file_menu.add_command(label='Exit', command=master.quit)

    help_menu = Menu(menu)
    menu.add_cascade(label='Help', menu=help_menu)
    help_menu.add_command(label='About', command=_about_window)


def _setup_buttons(master, cpu_step, cpu_back, cpu_reset):
    buttons_pane = ttk.Panedwindow(master, width=100, height=50)
    buttons_pane.place(x=0, y=0)
    step_button = Button(buttons_pane, text="Step", command=cpu_step)
    step_button.grid(row=0, column=0, sticky=W)
    back_button = Button(buttons_pane, text="Back", command=cpu_back)
    back_button.grid(row=0, column=1, sticky=W)
    reset_button = Button(buttons_pane, text="Reset", command=cpu_reset)
    reset_button.grid(row=0, column=2, sticky=W)


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


def _setup_pipeline_box(master):
    pipe_pane = ttk.Panedwindow(master, orient=VERTICAL, width=800, height=400)
    pipe_pane.place(x=100, y=400)

    load = Image.open("C:/Users/mo0887at/OneDrive - Lund University/pipe.png")
    render = ImageTk.PhotoImage(load)
    img = Label(pipe_pane, image=render)
    img.image = render
    img.place(x=100, y=0)

    img2 = Label(pipe_pane, image=render)
    img2.image = render
    img2.place(x=300, y=0)

    img3 = Label(pipe_pane, image=render)
    img3.image = render
    img3.place(x=500, y=0)

    img4 = Label(pipe_pane, image=render)
    img4.image = render
    img4.place(x=700, y=0)

    if_id_inst = StringVar()
    if_id_inst.set("")
    label = Label(pipe_pane, textvariable=if_id_inst, relief=FLAT, font=("courier", 12))
    label.place(x=100, y=200)

    id_ex_inst = StringVar()
    id_ex_inst.set("")
    label = Label(pipe_pane, textvariable=id_ex_inst, relief=FLAT, font=("courier", 12))
    label.place(x=300, y=200)

    ex_mem_inst = StringVar()
    ex_mem_inst.set("")
    label = Label(pipe_pane, textvariable=ex_mem_inst, relief=FLAT, font=("courier", 12))
    label.place(x=500, y=200)

    mem_wb_inst = StringVar()
    mem_wb_inst.set("")
    label = Label(pipe_pane, textvariable=mem_wb_inst, relief=FLAT, font=("courier", 12))
    label.place(x=700, y=200)

    load = Image.open("C:/Users/mo0887at/OneDrive - Lund University/pc.png")
    render = ImageTk.PhotoImage(load)
    img = Label(pipe_pane, image=render)
    img.image = render
    img.place(x=30, y=70)

    if_pc_in = StringVar()
    if_pc_in.set("pc")
    label = Label(pipe_pane, textvariable=if_pc_in, relief=FLAT, font=("courier", 10))
    label.place(x=-0, y=80)

    if_pc_out = StringVar()
    if_pc_out.set("")
    label = Label(pipe_pane, textvariable=if_pc_out, relief=FLAT, font=("courier", 10))
    label.place(x=60, y=80)

    return [if_id_inst, id_ex_inst, ex_mem_inst, mem_wb_inst, if_pc_in, if_pc_out]


def _about_window():
    messagebox.showinfo("About", "Created by MJ!")


class Screen:
    def __init__(self, width, height):
        self.risc_v = CPU()
        self.register_file_entries = []

        master = Tk()
        master.wm_title("RISC-V Masimulator")
        master.geometry(width + "x" + height)

        _setup_menus(master)
        _setup_buttons(master, self.step_callback, self.backstep_callback, self.reset_callback)
        self.register_file_entries = _setup_register_file_entries(master)
        [self.data_memory_box, self.data_memory_address_box, self.data_mem_scrollbar] = \
            _setup_data_mem_box(master, self.risc_v.state.data_memory, self.data_mem_yview, self.data_mem_yview_tie)
        [self.program_memory_box, self.program_memory_address_box, self.program_mem_scrollbar] = \
            _setup_program_mem_box(master, self.risc_v.memory, self.program_mem_yview, self.program_mem_yview_tie)
        [self.if_id_inst, self.id_ex_inst, self.ex_mem_inst, self.mem_wb_inst, self.if_pc_in, self.if_pc_out] = _setup_pipeline_box(master)

        self.reset_callback()

        mainloop()

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
            self.register_file_entries[i].delete(0, 'end')
            self.register_file_entries[i].insert(0, self.risc_v.state.register_file[i])

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

        pc = int(self.risc_v.state.if_pc / 4)
        value = disassemble(self.risc_v.memory[pc])
        self.program_memory_box.tag_add("here", str(pc) + ".0", str(pc) + "." + str(len(value)))
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

    def refresh_pipeline_box(self):
        self.if_id_inst.set(disassemble(self.risc_v.state.pipe.if_id.instruction))
        self.id_ex_inst.set(disassemble(self.risc_v.state.pipe.id_ex.instruction))
        self.ex_mem_inst.set(disassemble(self.risc_v.state.pipe.ex_mem.instruction))
        self.mem_wb_inst.set(disassemble(self.risc_v.state.pipe.mem_wb.instruction))

        self.if_pc_in.set("" + str(self.risc_v.state.if_pc))
        self.if_pc_out.set("" + str(self.risc_v.state.pipe.if_id.pc))

    def step_callback(self):
        self.modify_register_file()
        self.modify_data_memory()

        data_mem_old = self.risc_v.state.data_memory.copy()
        d_mem_yview_old = self.data_memory_box.yview()[0]
        p_mem_yview_old = self.program_memory_box.yview()[0]

        self.risc_v.tick()

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

        self.refresh_register_file_box()
        self.refresh_data_memory_box()
        self.refresh_program_memory_box(0)
        self.refresh_pipeline_box()
