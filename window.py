from tkinter import *
from tkinter import ttk
from cpu import *
from pipeline_visual import PipelineGraphics
import tkinter as tk
from tkinter import filedialog, font
from assembler.rvi import assemble
from assembler.lib.cprint import cprint as cp
from disassembler import *
import webbrowser
import io
from functools import partial
from scrolled_lined_text import ScrolledLinedText


class Screen:
    def __init__(self, width, height):
        self.risc_v = CPU()
        self.register_file_entries = []

        self.main_window = Tk()

        vertical_tabs = False
        if vertical_tabs:
            style = ttk.Style(self.main_window)
            style.configure('lefttab.TNotebook', tabposition='wn')

        nb = ttk.Notebook(self.main_window, style='lefttab.TNotebook')
        self.pipeline_window = ttk.Frame(nb)
        self.editor_window = ttk.Frame(nb)

        self.assembly_file_name = 'examples/default.rvi'
        self._editor_setup()

        self.recent_file_list_menu = Menu()
        self.recent_file_list = list()
        self.setup_recent_file_list()

        nb.add(self.pipeline_window, text='Pipeline')
        nb.add(self.editor_window, text='Editor')

        nb.pack(expand=1, fill="both")

        self.main_window.wm_title("RISC-V Masimulator")
        self.main_window.geometry(width + "x" + height)

        self._setup_menus(self.main_window)
        self._setup_buttons(self.step_callback, self.backstep_callback, self.reset_callback, self.execute_all_callback)

        self.forwarding_enabled = IntVar()
        self.hazard_detection_enabled = IntVar()
        self.delayed_branches_enabled = IntVar()
        self._setup_check_buttons()
        self._setup_statistics_pane()

        self._memory_window_init()

        self.show_rf_in_hex = BooleanVar()
        self.register_file_entries = self._setup_register_file_entries()
        self.show_data_mem_in_hex = BooleanVar()
        [self.data_memory_box, self.data_memory_address_box, self.data_mem_scrollbar] = \
            self._setup_data_mem_box(g_memory, self.data_mem_yview, self.data_mem_yview_tie)
        [self.program_memory_box, self.program_memory_address_box, self.program_mem_scrollbar] = \
            self._setup_program_mem_box(self.risc_v.memory, self.program_mem_yview, self.program_mem_yview_tie)

        self.pipe_graphics = PipelineGraphics(self.pipeline_window)
        self.reset_callback()
        self.main_window.bind('<Key>', lambda a: self._key_press_callback(a))
        nb.bind("<<NotebookTabChanged>>", self.on_tab_selected)

        self._assemble_editor_contetnts()

        mainloop()

    def _editor_setup(self):
        self.assembly_file_name_title = StringVar()
        self.assembly_file_name_title.set(self.assembly_file_name)
        title_pane = ttk.Panedwindow(self.editor_window, width=500, height=30)
        l = Label(title_pane, textvariable=self.assembly_file_name_title)
        l.grid(row=0, column=0, sticky=W)
        self.assembly_status_icon = Label(title_pane, text="    ", background="green")
        self.assembly_status_icon.grid(row=0, column=1, sticky=W, padx=10)
        title_pane.pack()
        buttons_pane = ttk.Panedwindow(self.editor_window, width=500, height=30)
        b = Button(buttons_pane, text="Save", command=self._save_assembly_file)
        b.grid(row=0, column=0, sticky=W)
        b = Button(buttons_pane, text="Save As", command=self._save_as_file_dialog)
        b.grid(row=0, column=1, sticky=W)
        b = Button(buttons_pane, text="Open", command=self._open_and_assemble_dialog)
        b.grid(row=0, column=2, sticky=W)
        b = Button(buttons_pane, text="Assemble", command=self._assemble_editor_contetnts)
        b.grid(row=0, column=3, sticky=W)
        buttons_pane.pack()

        e = ScrolledLinedText(self.editor_window)
        e.pack(side="top", fill="both", expand=True)
        self.editor_text = e.text
        self.editor_text.configure(font=("Consolas", 17))
        self.editor_text.bind("<Tab>", self._editor_tab_key_pressed)
        self.editor_text.bind("<Control-s>", self._save_assembly_file)
        self.editor_text.bind("<KeyRelease>", self._editor_any_key_pressed)
        self.editor_text.insert('end', open(self.assembly_file_name, 'r').read())
        self._highlight_syntax()

        self.assembly_status_bar_text = StringVar()
        status_bar_pane = ttk.Panedwindow(self.editor_window, width=500, height=200)
        self.assembly_status_bar_label = Label(status_bar_pane, textvariable=self.assembly_status_bar_text, font=("Consolas", 15))
        self.assembly_status_bar_label.grid(row=0, column=0, sticky=W)
        status_bar_pane.pack()

    def _editor_any_key_pressed(self, arg):
        self._highlight_syntax()
        if arg.char != "" or arg.keysym == "BackSpace":
            self.assembly_status_icon.config(bg="black")

    def _editor_tab_key_pressed(self, arg):
        self.editor_text.insert(INSERT, " " * 4)
        return 'break'

    def setup_recent_file_list(self):
        try:
            with open("recent.txt", "r") as f:
                self.recent_file_list = list(f.read().splitlines())
        except:
            pass

    def update_recent_file_list(self):
        for recent in self.recent_file_list:
            self.recent_file_list_menu.delete(0)
        for recent in self.recent_file_list:
            self.recent_file_list_menu.add_command(label=recent, command=partial(self._open_and_assemble_file, recent))

    def add_to_recent_file_list(self, filename):
        if filename in self.recent_file_list:
            self.recent_file_list.remove(filename)
        self.recent_file_list.insert(0, filename)
        if len(self.recent_file_list) >= 10:
            self.recent_file_list.pop()
        with open("recent.txt", "w") as f:
            f.writelines("%s\n" % recent_file for recent_file in self.recent_file_list)
        self.update_recent_file_list()

    def on_tab_selected(self, event):
        pass

    def _memory_window_init(self):
        self._cache_visual_init()
        self.memory_window = None
        self.memory_window_open = False
        self.cache_visual_pane = None
        self.cache_num_sets_entry = None
        self.cache_num_blocks_entry = None
        self.cache_num_words_entry = None
        self.cache_is_active = BooleanVar()
        self.memory_wait_cycles_entry = None
        self.memory_word_transfer_cycles_entry = None
        self.cache_hit_rate = StringVar()
        self.cache_hit_rate.set("0.00")
        self.cache_replacement_selector = ttk.Combobox()

    def _about_window(self):
        about_window = Toplevel(self.pipeline_window)
        about_window.wm_title("About")
        about_window.geometry("300" + "x" + "100")

        def callback(url):
            webbrowser.open_new(url)

        link1 = Label(about_window, text="Masimulator by Mohammad Attari")
        link1.pack()

        link1 = Label(about_window, text="Masimulator on GitHub", fg="blue", cursor="hand2")
        link1.pack()
        link1.bind("<Button-1>", lambda e: callback("https://github.com/masoud-ata/Masimulator"))
        f = tk.font.Font(link1, link1.cget("font"))
        f.configure(underline=True)
        link1.configure(font=f)

        link1 = Label(about_window, text="RISCV-RV32I-Assembler by Don Dennis")
        link1.pack()
        link2 = Label(about_window, text="RISCV-RV32I-Assembler on GitHub", fg="blue", cursor="hand2")
        link2.pack()
        link2.bind("<Button-1>", lambda e: callback("https://github.com/metastableB/RISCV-RV32I-Assembler"))
        f = tk.font.Font(link2, link2.cget("font"))
        f.configure(underline=True)
        link2.configure(font=f)

    # Creates 3D arrays for cache visualization
    def _cache_visual_init(self):
        self.cache_requested_address = StringVar()
        self.cache_requested_address_tag = StringVar()
        self.cache_requested_address_index = StringVar()
        self.cache_requested_address_block_offset = StringVar()
        self.cache_values = []
        self.cache_tags = []
        self.cache_valid_bits = []
        self.cache_dirty_bits = []
        self.cache_replace_bits = []
        self.cache_word_lables = []
        for set in range(MemorySettings.num_sets):
            s = []
            s_t = []
            s_v = []
            s_d = []
            s_r = []
            s_l = []
            for block in range(MemorySettings.num_blocks_per_set):
                b = []
                s.append(b)
                s_t.append(StringVar())
                s_v.append(StringVar())
                s_d.append(StringVar())
                s_r.append(StringVar())
                b_l = []
                s_l.append(b_l)
                for word in range(MemorySettings.num_words_per_block):
                    b.append(StringVar())
                    b_l.append(Label())
            self.cache_values.append(s)
            self.cache_tags.append(s_t)
            self.cache_valid_bits.append(s_v)
            self.cache_dirty_bits.append(s_d)
            self.cache_replace_bits.append(s_r)
            self.cache_word_lables.append(s_l)

    def apply_memory_setings_callback(self):
        MemorySettings.cache_active = self.cache_is_active.get()
        MemorySettings.cache_replacement_policy = self.cache_replacement_selector.get()
        num_sets = 1
        num_blocks_per_set = 1
        num_words_per_block = 1
        memory_wait_cycles = 0
        word_transfer_cycles = 0
        try:
            num_sets = int(self.cache_num_sets_entry.get())
            num_blocks_per_set = int(self.cache_num_blocks_entry.get())
            num_words_per_block = int(self.cache_num_words_entry.get())
            memory_wait_cycles = int(self.memory_wait_cycles_entry.get())
            word_transfer_cycles = int(self.memory_word_transfer_cycles_entry.get())
        except ValueError:
            return
        else:
            if num_sets > 0 and num_blocks_per_set > 0 and num_words_per_block > 0:
                self.risc_v.state.data_memory_system.cache.resize(num_sets, num_blocks_per_set, num_words_per_block)
                self._cache_visual_init()
                self.cache_visual_pane.destroy()
                self._memory_window_visual_setup()
            if memory_wait_cycles >= 0 and word_transfer_cycles >= 0:
                MemorySettings.memory_wait_cycles = memory_wait_cycles
                MemorySettings.word_transfer_cycles = word_transfer_cycles
                self.risc_v.state.data_memory_system.update_penalty()
            self.reset_callback()

    def _memory_window_config_setup(self):
        cache_config_pane = ttk.Panedwindow(self.memory_window, orient=VERTICAL, width=100, height=100)
        cache_config_pane.place(x=10, y=10)

        c = Checkbutton(cache_config_pane, text="activate cache", variable=self.cache_is_active)
        c.grid(row=0, column=0, sticky=W)

        l = Label(cache_config_pane, text="number of sets")
        l.grid(row=1, column=0, sticky=W)
        self.cache_num_sets_entry = Entry(cache_config_pane, font=("Courier 10"), width=5)
        self.cache_num_sets_entry.grid(row=1, column=1, sticky=W)
        self.cache_num_sets_entry.insert(0, MemorySettings.num_sets)
        l = Label(cache_config_pane, text="number of blocks/set")
        l.grid(row=2, column=0, sticky=W)
        self.cache_num_blocks_entry = Entry(cache_config_pane, font=("Courier 10"), width=5)
        self.cache_num_blocks_entry.grid(row=2, column=1, sticky=W)
        self.cache_num_blocks_entry.insert(0, MemorySettings.num_blocks_per_set)
        l = Label(cache_config_pane, text="number of words/block")
        l.grid(row=3, column=0, sticky=W)
        self.cache_num_words_entry = Entry(cache_config_pane, font=("Courier 10"), width=5)
        self.cache_num_words_entry.grid(row=3, column=1, sticky=W)
        self.cache_num_words_entry.insert(0, MemorySettings.num_words_per_block)

        l = Label(cache_config_pane, text="memory wait cycles")
        l.grid(row=1, column=2, sticky=W)
        self.memory_wait_cycles_entry = Entry(cache_config_pane, font=("Courier 10"), width=9)
        self.memory_wait_cycles_entry.grid(row=1, column=3, sticky=W)
        self.memory_wait_cycles_entry.insert(0, MemorySettings.memory_wait_cycles)

        l = Label(cache_config_pane, text="word transfer cycles")
        l.grid(row=2, column=2, sticky=W)
        self.memory_word_transfer_cycles_entry = Entry(cache_config_pane, font=("Courier 10"), width=9)
        self.memory_word_transfer_cycles_entry.grid(row=2, column=3, sticky=W)
        self.memory_word_transfer_cycles_entry.insert(0, MemorySettings.word_transfer_cycles)

        l = Label(cache_config_pane, text="hit rate")
        l.grid(row=1, column=4, sticky=W)
        l = Label(cache_config_pane, textvariable=self.cache_hit_rate, width=5, relief=GROOVE)
        l.grid(row=1, column=5, sticky=W)

        l = Label(cache_config_pane, text="replacement policy")
        l.grid(row=3, column=2, sticky=W)
        self.cache_replacement_selector = ttk.Combobox(cache_config_pane, values=MemorySettings.cache_replacement_policy_choices, width=9, state="readonly")
        self.cache_replacement_selector.grid(row=3, column=3)
        self.cache_replacement_selector.current(MemorySettings.cache_replacement_policy_choices.index(MemorySettings.cache_replacement_policy))

        b = Button(cache_config_pane, text="Apply Settings", command=self.apply_memory_setings_callback)
        b.grid(row=3, column=4, sticky=W)

    def _memory_window_visual_setup(self):
        self.cache_visual_pane = ttk.Panedwindow(self.memory_window, orient=VERTICAL, width=400, height=300)
        self.cache_visual_pane.place(x=50, y=120)

        if MemorySettings.cache_active:
            layout = ttk.Notebook(self.cache_visual_pane)
            table = Frame(layout)
            table.pack(fill="both")
            self._address_breakup_visual_setup(table)
            self._cache_contetnts_visual_setup(table)
            layout.add(table, text="data cache")
            layout.pack(fill="both")

    def _address_breakup_visual_setup(self, table):
        tag_bits, index_bits, block_offset_bits = self.risc_v.state.data_memory_system.get_address_breakup_num_bits()

        address_breakup_pane = ttk.Panedwindow(table, orient=VERTICAL, width=800, height=50)
        address_breakup_pane.grid(row=0, column=0, columnspan=10, sticky=W)

        bits = Label(address_breakup_pane, text="bits: ", fg="black", anchor='w')
        bits.grid(row=0, column=0, sticky=W)
        self.cache_requested_address.set("address: ")
        incoimg_address = Label(address_breakup_pane, textvariable=self.cache_requested_address, width=12, fg="black", anchor='w')
        incoimg_address.grid(row=1, column=0, sticky=E)
        num_tag_bits = Label(address_breakup_pane, text=tag_bits, width=10)
        num_tag_bits.grid(row=0, column=1, sticky=W)
        tag_field = Label(address_breakup_pane, textvariable=self.cache_requested_address_tag, width=10, bg="white", fg="black")
        tag_field.grid(row=1, column=1, sticky="nsew", padx=2, pady=3)
        if index_bits:
            num_index_bits = Label(address_breakup_pane, text=index_bits, width=index_bits)
            num_index_bits.grid(row=0, column=2, sticky=W)
            index_field = Label(address_breakup_pane, textvariable=self.cache_requested_address_index, width=index_bits, bg="white", fg="black")
            index_field.grid(row=1, column=2, sticky="nsew", padx=2, pady=3)
        if block_offset_bits:
            num_block_offset_bits = Label(address_breakup_pane, text=block_offset_bits, width=block_offset_bits)
            num_block_offset_bits.grid(row=0, column=3, sticky=W)
            block_offset_field = Label(address_breakup_pane, textvariable=self.cache_requested_address_block_offset, width=block_offset_bits, bg="white", fg="black")
            block_offset_field.grid(row=1, column=3, sticky="nsew", padx=2, pady=3)
        byte_bits = Label(address_breakup_pane, text="2", width=1)
        byte_bits.grid(row=0, column=4, sticky=W)
        byte_field = Label(address_breakup_pane, text=0, width=1, bg="white", fg="black")
        byte_field.grid(row=1, column=4, sticky="nsew", padx=2, pady=3)
        empty_space = Label(address_breakup_pane)
        empty_space.grid(row=2, column=0, sticky="nsew", padx=2, pady=3)

    def _cache_contetnts_visual_setup(self, table):
        set_width = 3
        valid_width = 2
        replace_width = 2
        dirty_width = 2
        tag_width = 7
        word_width = 13

        set_title = Label(table, text="Set", width=set_width, fg="black")
        set_title.grid(row=1, column=0, sticky=E, padx=3, pady=3)

        for set in range(MemorySettings.num_sets):
            col = 0
            set_num = Label(table, text=set, width=set_width, fg="blue")
            set_num.grid(row=set + 2, column=col, sticky=E, padx=3, pady=3)
            for block in range(MemorySettings.num_blocks_per_set):
                col = col + 1
                if set == 0:
                    dirt_title = Label(table, text="D", width=dirty_width, fg="black")
                    dirt_title.grid(row=1, column=col, sticky=E, padx=3, pady=3)
                cache_dirty = Label(table, textvariable=self.cache_dirty_bits[set][block], width=dirty_width,
                                    bg="white", fg="black")
                cache_dirty.grid(row=set + 2, column=col, sticky="nsew", padx=3, pady=3)
                col = col + 1
                if set == 0:
                    valid_title = Label(table, text="V", width=valid_width, fg="black")
                    valid_title.grid(row=1, column=col, sticky=E, padx=3, pady=3)
                cache_valid = Label(table, textvariable=self.cache_valid_bits[set][block], width=valid_width,
                                    bg="white", fg="black")
                cache_valid.grid(row=set + 2, column=col, sticky="nsew", padx=3, pady=3)
                if MemorySettings.cache_replacement_policy != "Random":
                    col = col + 1
                    if set == 0:
                        replace_title = Label(table, text="R", width=replace_width, fg="black")
                        replace_title.grid(row=1, column=col, sticky=E, padx=3, pady=3)
                    cache_replace = Label(table, textvariable=self.cache_replace_bits[set][block], width=replace_width,
                                          bg="white", fg="black")
                    cache_replace.grid(row=set + 2, column=col, sticky="nsew", padx=3, pady=3)
                col = col + 1
                if set == 0:
                    tag_title = Label(table, text="Tag", width=tag_width, fg="black")
                    tag_title.grid(row=1, column=col, sticky=E, padx=3, pady=3)
                cache_tag = Label(table, textvariable=self.cache_tags[set][block], width=tag_width, bg="white",
                                  fg="black")
                cache_tag.grid(row=set + 2, column=col, sticky="nsew", padx=3, pady=3)
                for word in range(MemorySettings.num_words_per_block):
                    col = col + 1
                    if set == 0:
                        word_title = Label(table, text="Word " + str(word), width=word_width, fg="black")
                        word_title.grid(row=1, column=col, sticky=E, padx=1, pady=3)
                    self.cache_word_lables[set][block][word] = Label(table,
                                                                     textvariable=self.cache_values[set][block][word],
                                                                     relief=SOLID, width=word_width, bg="white",
                                                                     fg="black")
                    self.cache_word_lables[set][block][word].grid(row=set + 2, column=col, sticky="nsew", padx=1,
                                                                  pady=3)
                col = col + 1
                empty_space = Label(table, width=3)
                empty_space.grid(row=set + 2, column=col, sticky=E, padx=3, pady=3)

    def on_memory_window_closing(self):
        self.memory_window_open = False
        self.memory_window.destroy()

    def _setup_memory_window(self):
        if self.memory_window_open:
            self.memory_window.lift()
            self.memory_window.focus_force()
            return
        self.memory_window_open = True
        self.memory_window = Toplevel(self.pipeline_window)
        self.memory_window.wm_title("Memory")
        self.memory_window.geometry("700" + "x" + "400")
        self.memory_window.bind('<Key>', lambda a: self._key_press_callback(a))
        self.memory_window.protocol("WM_DELETE_WINDOW", self.on_memory_window_closing)
        self._memory_window_config_setup()
        self._memory_window_visual_setup()

    def _setup_menus(self, master):
        menu = Menu(master)
        master.config(menu=menu)

        file_menu = Menu(menu, tearoff=False)
        menu.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Open & Assemble ...', command=self._open_and_assemble_dialog)
        self.recent_file_list_menu = Menu(file_menu, tearoff=False)
        for recent in self.recent_file_list:
            self.recent_file_list_menu.add_command(label=recent, command=partial(self._open_and_assemble_file, recent))
        file_menu.add_cascade(label="Open Recent", menu=self.recent_file_list_menu)
        file_menu.add_command(label='Save       Ctrl+S', command=self._save_assembly_file)
        file_menu.add_command(label='Save As ...', command=self._save_as_file_dialog)
        file_menu.add_command(label='Assemble', command=self._assemble_editor_contetnts)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=master.quit)

        edit_menu = Menu(menu, tearoff=False)
        menu.add_cascade(label='Edit', menu=edit_menu)
        edit_menu.add_command(label='Memory', command=self._setup_memory_window)

        help_menu = Menu(menu, tearoff=False)
        menu.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='About', command=self._about_window)

    def _setup_buttons(self, cpu_step, cpu_back, cpu_reset, cpu_execute_all):
        buttons_pane = ttk.Panedwindow(self.pipeline_window, width=100, height=50)
        buttons_pane.place(x=0, y=0)

        self.icon_step = PhotoImage(file=r"images/icon_step.png")
        self.icon_backstep = PhotoImage(file=r"images/icon_backstep.png")
        self.icon_finish = PhotoImage(file=r"images/icon_finish.png")
        self.icon_reset = PhotoImage(file=r"images/icon_reset.png")

        step_button = Button(buttons_pane, text="(F1)", command=cpu_step, image=self.icon_step, compound=LEFT)
        step_button.grid(row=0, column=0, sticky=W)
        from tooltip import ToolTip
        ToolTip(step_button, text="Step")
        back_button = Button(buttons_pane, text="(F2)", command=cpu_back, image=self.icon_backstep, compound=LEFT)
        back_button.grid(row=0, column=1, sticky=W)
        ToolTip(back_button, text="Backstep")
        execute_all_button = Button(buttons_pane, text="(F3)", command=cpu_execute_all, image=self.icon_finish, compound=LEFT)
        execute_all_button.grid(row=0, column=2, sticky=W)
        ToolTip(execute_all_button, text="Execute all")
        reset_button = Button(buttons_pane, text="(F4)", command=cpu_reset, image=self.icon_reset, compound=LEFT)
        reset_button.grid(row=0, column=3, sticky=W)
        ToolTip(reset_button, text="Reset")

    def _highlight_syntax(self):
        for tag in self.editor_text.tag_names():
            self.editor_text.tag_delete(tag)
        editor_lines = io.StringIO(self.editor_text.get("1.0", END)).readlines()
        for line_number, line_string in enumerate(editor_lines):
            line_tokens = line_string.replace("\n", " ").split(" ")
            comment_start_pos = line_string.find("#")
            line_has_comment = comment_start_pos >= 0
            for instruction in g_instruction_set:
                if instruction in line_tokens:
                    pos = line_string.find(instruction)
                    appears_in_comment = line_has_comment and comment_start_pos < pos
                    if pos >= 0 and not (appears_in_comment):
                        self.editor_text.tag_add("here", str(line_number + 1) + "." + str(pos), str(line_number + 1) + "." + str(pos + len(instruction)))
                        self.editor_text.tag_config("here", foreground="blue")
                    break
            end_pos = line_string.find("\n")
            if line_has_comment:
                self.editor_text.tag_add("comment", str(line_number + 1) + "." + str(comment_start_pos), str(line_number + 1) + "." + str(end_pos))
                self.editor_text.tag_config("comment", foreground="green")

    def _save_assembly_file(self, arg=0):
        with open(self.assembly_file_name, "w") as f:
            f.write(self.editor_text.get("1.0", END)[:-1])

    def _save_as_file_dialog(self):
        filename = filedialog.asksaveasfilename(title="Select file",filetypes=[("Assembly files ", "*.rvi"), ("Assembly files", "*.s"), ("all files", "*.*")])
        if filename != "":
            self.assembly_file_name = filename
            self.assembly_file_name_title.set(filename)
            with open(self.assembly_file_name, "w") as f:
                f.write(self.editor_text.get("1.0", END)[:-1])

    def _open_and_assemble_file(self, filename):
        self.assembly_file_name = filename
        self.assembly_file_name_title.set(filename)
        self._assemble_file(filename)
        self.editor_text.delete('1.0', END)
        self.editor_text.edit_reset()
        self.editor_text.insert('end', open(filename, 'r').read())
        self._highlight_syntax()
        self.add_to_recent_file_list(filename)

    def _open_and_assemble_dialog(self):
        filename = filedialog.askopenfilename(title="Select file", filetypes=(("Assembly files", "*.rvi *.s"), ("all files", "*.*")))
        if filename != "":
            self._open_and_assemble_file(filename)

    def _assemble_editor_contetnts(self):
        temp_filename = "examples/tmp2.rvi"
        with open(temp_filename, "w") as f:
            f.write(self.editor_text.get("1.0", END)[:-1])
        self._assemble_file(temp_filename)

    def _assemble_file(self, filename):
        try:
            assemble(filename)
            self.risc_v.read_program_memory()
            [self.program_memory_box, self.program_memory_address_box, self.program_mem_scrollbar] = \
                self._setup_program_mem_box(self.risc_v.memory, self.program_mem_yview, self.program_mem_yview_tie)
            self.reset_callback()
            self.assembly_status_icon.config(bg="red") if cp.failed else self.assembly_status_icon.config(bg="green")
        except Exception:
            self.assembly_status_icon.config(bg="red")
        color, text = cp.consume_message()
        self.assembly_status_bar_label.config(fg=color)
        self.assembly_status_bar_text.set(text)

    def _setup_check_buttons(self):
        check_buttons_pane = ttk.Panedwindow(self.pipeline_window, width=100, height=50)
        check_buttons_pane.place(x=0, y=40)
        c = Checkbutton(check_buttons_pane, text="Enable forwarding", variable=self.forwarding_enabled, command=self.toggle_forwarding_callback)
        c.grid(row=1, column=0, sticky=W)
        c = Checkbutton(check_buttons_pane, text="Enable hazard detection", variable=self.hazard_detection_enabled, command=self.toggle_hazard_detection_callback)
        c.grid(row=2, column=0, sticky=W)
        c = Checkbutton(check_buttons_pane, text="Enable delayed branches", variable=self.delayed_branches_enabled, command=self.toggle_delayed_branches_callback)
        c.grid(row=3, column=0, sticky=W)

    def _setup_statistics_pane(self):
        statistics_pane = ttk.Panedwindow(self.pipeline_window, width=100, height=50)
        statistics_pane.place(x=0, y=130)
        self.num_cycles = StringVar()
        self.num_cycles.set("1")
        cycle_count = Label(statistics_pane, text="Cycle count: ")
        cycle_count.grid(row=0, column=0, sticky=W)
        cycle_count_label = Label(statistics_pane, textvariable=self.num_cycles, width=10, relief=GROOVE)
        cycle_count_label.grid(row=0, column=1, sticky=W)

    def _setup_register_file_entries(self):
        rf_pane = ttk.Panedwindow(self.pipeline_window, orient=VERTICAL, width=200, height=100)
        rf_pane.place(x=230, y=0)

        l = Label(rf_pane, text="Register file")
        l.grid(row=0, column=0, sticky=W)

        c = Checkbutton(rf_pane, text="in hex", variable=self.show_rf_in_hex, command=self.toggle_show_rf_in_hex_callback)
        c.grid(row=1, column=0, sticky=W)

        entries = []
        for i in range(0, 32):
            entries.append(Entry(rf_pane, font=("Courier 10"), width=12))
            entries[i].grid(row=int(i % 8), column=2 + 2 * (i // 8), sticky=W)
            entries[i].insert(0, 0)
            l = Label(rf_pane, text="x" + str(i))
            l.grid(row=int(i % 8), column=1 + 2 * (i // 8), sticky=W)
        return entries

    def _setup_data_mem_box(self, data_memory, data_mem_yview, data_mem_yview_tie):
        mem_pane = ttk.Panedwindow(self.pipeline_window, orient=VERTICAL, width=200, height=100)
        mem_pane.place(x=790, y=0)

        c = Checkbutton(mem_pane, text="in hex", variable=self.show_data_mem_in_hex, command=self.toggle_show_data_mem_in_hex_callback)
        c.grid(row=0, column=0, sticky=W)

        l = Label(mem_pane, text="Address")
        l.grid(row=0, column=1, sticky=W)
        l = Label(mem_pane, text="Data Memory")
        l.grid(row=0, column=2, sticky=W)

        mem_text = Text(mem_pane, height=9, width=12)
        mem_text.grid(row=1, column=2, sticky=W)
        scrollbar = Scrollbar(mem_pane, orient=VERTICAL, command=data_mem_yview)
        scrollbar.grid(row=1, column=3, rowspan=15, columnspan=1, sticky=NS)
        mem_text.config(yscrollcommand=data_mem_yview_tie)

        mem_addr_text = Text(mem_pane, height=9, width=6)
        mem_addr_text.grid(row=1, column=1, sticky=W)
        mem_addr_text.config(yscrollcommand=data_mem_yview_tie)

        text = ""
        addr_text = ""
        address = 0
        for value in data_memory:
            # text = text + '{0:08x}'.format(int(value)) + "\n"
            text = text + str(value) + "\n"
            addr_text = addr_text + str(address) + "\n"
            address = address + 4

        text = text[:-len("\n")]
        addr_text = addr_text[:-len("\n")]
        mem_text.insert(END, text)
        mem_addr_text.insert(END, addr_text)
        mem_addr_text.config(state=DISABLED)

        return [mem_text, mem_addr_text, scrollbar]

    def _setup_program_mem_box(self, program_memory, program_mem_yview, program_mem_yview_tie):
        prog_mem_pane = ttk.Panedwindow(self.pipeline_window, orient=VERTICAL, width=200, height=100)
        prog_mem_pane.place(x=1030, y=0)

        l = Label(prog_mem_pane, text="Address")
        l.grid(row=0, column=0, sticky=W)
        l = Label(prog_mem_pane, text="Program Memory")
        l.grid(row=0, column=1, sticky=W)

        mem_text = Text(prog_mem_pane, height=9, width=20)
        mem_text.grid(row=1, column=1, sticky=W)
        scrollbar = Scrollbar(prog_mem_pane, orient=VERTICAL, command=program_mem_yview)
        scrollbar.grid(row=1, column=2, rowspan=15, columnspan=1, sticky=NS)
        mem_text.config(yscrollcommand=program_mem_yview_tie)

        mem_addr_text = Text(prog_mem_pane, height=9, width=5)
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

    def _key_press_callback(self, event):
        key = event.keysym
        if key == "F1":
            self.step_callback()
        elif key == "F2":
            self.backstep_callback()
        elif key == "F3":
            self.execute_all_callback()
        elif key == "F4":
            self.reset_callback()
        elif key == "F6":
            self.populate_data_memory()
        elif key == "F9":
            self.execute_all_no_trace_callback()

    def populate_data_memory(self):
        g_memory.clear()
        g_memory.extend(range(1, MEMORY_SIZE))
        self.refresh_data_memory_box()

    def refresh_pipeline_box(self):
        self.pipe_graphics.refresh_pipeline(self.risc_v)

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
        is_in_hex = self.show_rf_in_hex.get()
        self.modify_register_file_with_check(is_in_hex)

    def modify_register_file_with_check(self, is_in_hex):
        if is_in_hex:
            for i, rf_entry in enumerate(self.register_file_entries):
                try:
                    reg_value = rf_entry.get()
                    rf_entry.delete(0, 'end')
                    reg_value = to_uint32(int(reg_value, 16))
                    if i == 0:
                        reg_value = 0
                    rf_entry.insert(0, '{0:08x}'.format(reg_value))
                    self.risc_v.state.register_file[i] = to_int32(reg_value)
                except ValueError:
                    rf_entry.insert(0, '{0:08x}'.format(self.risc_v.state.register_file[i]))
        else:
            for i in range(32):
                try:
                    reg_value = int(self.register_file_entries[i].get())
                    if i == 0:
                        reg_value = 0
                    self.risc_v.state.register_file[i] = to_int32(reg_value)
                except ValueError:
                    self.register_file_entries[i].delete(0, 'end')
                    self.register_file_entries[i].insert(0, self.risc_v.state.register_file[i])

    def refresh_register_file_box(self):
        show_in_hex = self.show_rf_in_hex.get()
        for i, rf_entry in enumerate(self.register_file_entries):
            value_before = to_int32(int(rf_entry.get(), 16)) if show_in_hex else to_int32(int(rf_entry.get()))
            value_now = to_int32(self.risc_v.state.register_file[i])
            rf_entry.delete(0, 'end')
            if show_in_hex:
                rf_entry.insert(0, '{0:08x}'.format(to_uint32(self.risc_v.state.register_file[i])))
            else:
                rf_entry.insert(0, to_int32(self.risc_v.state.register_file[i]))
            if value_before != value_now:
                self.register_file_entries[i].config({"background": "Yellow"})
            else:
                self.register_file_entries[i].config({"background": "White"})

    def modify_data_memory(self, is_in_hex):
        text = self.data_memory_box.get("1.0", END)
        text = text.replace("\t", "        ")
        text = text.split("\n")
        address = 0
        max_width = 8
        if not is_in_hex:
            max_width = 11
        for elem in text:
            if len(elem) >= max_width:
                for i in range(0, len(elem), max_width):
                    try:
                        if is_in_hex:
                            mem_data = int(elem[i:i + max_width], 16)
                        else:
                            mem_data = to_int32(int(elem[i:i + max_width]))
                        g_memory[address] = mem_data
                    except (ValueError, IndexError) as error:
                        pass
                    address = address + 1
            else:
                try:
                    if is_in_hex:
                        mem_data = int(elem, 16)
                    else:
                        mem_data = to_int32(int(elem))
                    g_memory[address] = mem_data
                except (ValueError, IndexError) as error:
                    pass
                address = address + 1

    def refresh_program_memory_box(self, p_mem_yview_old):
        self.program_memory_box.config(state=NORMAL)
        for tag in self.program_memory_box.tag_names():
            self.program_memory_box.tag_delete(tag)

        pc = self.risc_v.state.signals.if_signals.pc // 4
        value = disassemble(self.risc_v.memory[pc])
        row = pc + 1
        self.program_memory_box.tag_add("here", str(row) + ".0", str(row) + "." + str(len(value)))
        self.program_memory_box.tag_config("here", background="green", foreground="yellow")
        self.program_memory_box.yview_moveto(p_mem_yview_old)
        self.program_memory_box.config(state=DISABLED)

    def refresh_colored_data_memory_box(self, data_mem_old, d_mem_yview_old):
        self.refresh_data_memory_box()
        self.data_memory_box.yview_moveto(d_mem_yview_old)
        address = self.risc_v.state.data_memory_system.history.block_address
        for word in range(len(self.risc_v.state.data_memory_system.history.new_block)):
            value = self.risc_v.state.data_memory_system.history.new_block[word]
            value = '{0:08x}'.format(value) + "\n" if self.show_data_mem_in_hex.get() else str(value)
            self.data_memory_box.tag_add("here", str(address + word + 1) + ".0", str(address + + word + 1) + "." + str(len(value)))
            self.data_memory_box.tag_config("here", background="blue", foreground="yellow")

    def refresh_data_memory_box(self):
        for tag in self.data_memory_box.tag_names():
            self.data_memory_box.tag_delete(tag)

        text = ""
        self.data_memory_box.delete('1.0', END)
        self.data_memory_box.edit_reset()
        for value in g_memory:
            if self.show_data_mem_in_hex.get():
                text = text + '{0:08x}'.format(int(to_uint32(value))) + "\n"
            else:
                text = text + str(to_int32(value)) + "\n"
        text = text[:-len("\n")]
        self.data_memory_box.insert(END, text)

    def step_callback(self):
        self.modify_register_file()
        self.modify_data_memory(self.show_data_mem_in_hex.get())

        data_mem_old = g_memory.copy()
        d_mem_yview_old = self.data_memory_box.yview()[0]
        p_mem_yview_old = self.program_memory_box.yview()[0]

        self.risc_v.tick()

        self.refresh_program_memory_box(p_mem_yview_old)
        self.refresh_register_file_box()
        self.refresh_colored_data_memory_box(data_mem_old, d_mem_yview_old)
        self.refresh_pipeline_box()
        self.refresh_statistics()
        self.refresh_cache_window()

    def step_non_visual_callback(self):
        self.risc_v.tick()

    def backstep_callback(self):
        data_mem_old = g_memory.copy()
        d_mem_yview_old = self.data_memory_box.yview()[0]
        p_mem_yview_old = self.program_memory_box.yview()[0]

        self.risc_v.back_tick()

        self.refresh_program_memory_box(p_mem_yview_old)
        self.refresh_register_file_box()
        self.refresh_colored_data_memory_box(data_mem_old, d_mem_yview_old)
        self.refresh_pipeline_box()
        self.refresh_statistics()
        self.refresh_cache_window()

    def reset_callback(self):
        self.risc_v.reset()
        self.risc_v.calculate_signals()
        self.refresh_register_file_box()
        self.refresh_data_memory_box()
        self.refresh_program_memory_box(0)
        self.refresh_pipeline_box()
        self.refresh_statistics()
        self.refresh_cache_window(1)

    def execute_all_callback(self):
        self.step_callback()
        for i in range(500000):
            if not self.risc_v.is_finished():
                self.step_non_visual_callback()
            else:
                self.backstep_callback()
                self.step_callback()
                return

    def execute_all_no_trace_callback(self):
        self.risc_v.clear_trace()
        for i in range(500000):
            if not self.risc_v.is_finished():
                self.risc_v.tick(trace=False)
        data_mem_old = g_memory.copy()
        d_mem_yview_old = self.data_memory_box.yview()[0]
        p_mem_yview_old = self.program_memory_box.yview()[0]
        self.refresh_program_memory_box(p_mem_yview_old)
        self.refresh_register_file_box()
        self.refresh_colored_data_memory_box(data_mem_old, d_mem_yview_old)
        self.refresh_pipeline_box()
        self.refresh_statistics()
        self.refresh_cache_window()

    def toggle_forwarding_callback(self):
        self.pipe_graphics.toggle_forwarding(self.forwarding_enabled.get())
        self.risc_v.forwarding_enabled = self.forwarding_enabled.get()

    def toggle_hazard_detection_callback(self):
        self.pipe_graphics.toggle_hazard_detection(self.hazard_detection_enabled.get())
        self.risc_v.hazard_detection_enabled = self.hazard_detection_enabled.get()

    def toggle_delayed_branches_callback(self):
        self.risc_v.delayed_branches_enabled = self.delayed_branches_enabled.get()

    def toggle_show_rf_in_hex_callback(self):
        show_in_hex = self.show_rf_in_hex.get()
        was_showing_in_hex = not show_in_hex
        self.modify_register_file_with_check(was_showing_in_hex)
        for rf_entry in self.register_file_entries:
            entry_content = rf_entry.get()
            rf_entry.delete(0, 'end')
            rf_entry.config({"background": "White"})
            if show_in_hex:
                entry_value_uint = to_uint32(int(entry_content))
                entry_value_hex = '{0:08x}'.format(entry_value_uint)
                rf_entry.insert(0, entry_value_hex)
            else:
                entry_value_int = to_int32(int(entry_content, 16))
                rf_entry.insert(0, entry_value_int)

    def toggle_show_data_mem_in_hex_callback(self):
        d_mem_yview_old = self.data_memory_box.yview()[0]
        was_showing_in_hex = not self.show_data_mem_in_hex.get()
        self.modify_data_memory(was_showing_in_hex)
        self.refresh_data_memory_box()
        self.data_memory_box.yview_moveto(d_mem_yview_old)

    def refresh_statistics(self):
        self.num_cycles.set(str(self.risc_v.state.cycles_executed))

    def refresh_cache_window(self, reset=0):
        if MemorySettings.cache_active:
            if reset:
                self.cache_requested_address_tag.set("")
                self.cache_requested_address_index.set("")
                self.cache_requested_address_block_offset.set("")
                self.cache_requested_address.set("address: ")
            cache = self.risc_v.state.data_memory_system.cache
            hits_plus_misses = cache.book_keeping_hits + cache.book_keeping_misses
            hit_rate = (cache.book_keeping_hits / hits_plus_misses) if hits_plus_misses != 0 else cache.book_keeping_hits / 1.0
            self.cache_hit_rate.set("{:.2f}".format(hit_rate))
            if self.risc_v.state.pipe.ex_mem.control_mem_read or self.risc_v.state.pipe.ex_mem.control_mem_write:
                st = "address: " + str(self.risc_v.state.signals.mem_signals.address) + " "
                tag, index, block_offset = self.risc_v.state.data_memory_system.get_address_breakup_fields(self.risc_v.state.signals.mem_signals.address)
                self.cache_requested_address_tag.set(tag)
                self.cache_requested_address_index.set(index)
                self.cache_requested_address_block_offset.set(block_offset)
                self.cache_requested_address.set(st)
            for set in range(MemorySettings.num_sets):
                for block in range(MemorySettings.num_blocks_per_set):
                    self.cache_tags[set][block].set(cache.tags[set, block])
                    self.cache_valid_bits[set][block].set(cache.valid_bits[set, block])
                    self.cache_dirty_bits[set][block].set(cache.dirty_bits[set, block])
                    self.cache_replace_bits[set][block].set(cache.replace_bits[set, block])
                    for word in range(MemorySettings.num_words_per_block):
                        self.cache_values[set][block][word].set(cache.contents[set, block, word])
                        color = "white"
                        if cache.book_keeping_read_set == set and cache.book_keeping_read_block == block and cache.book_keeping_read_word == word:
                            color = "green"
                        elif cache.book_keeping_was_modified and cache.book_keeping_modified_set == set and \
                            cache.book_keeping_modified_block == block and word in cache.book_keeping_modified_words:
                                if cache.book_keeping_modified_just_one and word == cache.book_keeping_modified_word:
                                    color = "orange"
                                else:
                                    color = "yellow"
                        if self.memory_window_open:
                            self.cache_word_lables[set][block][word].config(bg=color, fg="black")
