#!/usr/bin/python
# @author:Don Dennis
# rvi.py
#
# The RISC-V assembler for subset of instructions.

from assembler.lib.parser import parse_input
import argparse
import re
import io

VERSION = 0.1


def get_arguments():
    descr = '''
    RVI v''' + str(VERSION) + '''
    - A simple RV32I assembler developed for testing
    RV32I targeted hardware designs.
    '''
    ap = argparse.ArgumentParser(description=descr)
    ap.add_argument("INFILE", help="Input file containing assembly code.")
    ap.add_argument('-o', "--outfile",
                    help="Output file name.", default='a.b')
    ap.add_argument('-e', "--echo", help="Echo converted code to console",
                    action="store_true")
    ap.add_argument('-nc', "--no-color", help="Turn off color output.",
                    action="store_true")
    ap.add_argument('-n32', "--no-32", help="Turn of 32 bit core warnings.",
                    action="store_true")
    ap.add_argument('-x', "--hex", action="store_true",
                    help="Output generated code in hexadecimal format" +
                         " instead of binary.")
    ap.add_argument('-t', '--tokenize', action="store_true",
                    help="Echo tokenized instructions to console" +
                         " for debugging.")
    ap.add_argument("-es", "--echo-symbols", action="store_true",
                    help="Echo the symbols table.")
    args = ap.parse_args()
    return args


def preset_args(assembly_file):
    args = argparse.Namespace()
    args.INFILE = assembly_file
    args.echo = False
    args.echo_symbols = False
    args.hex = False
    args.no_32 = False
    args.no_color = False
    args.outfile = 'mem.txt'
    args.tokenize = False
    return args


def assemble(assembly_file):
    args = preset_args(assembly_file)
    assembly_file_text = read_assembly_file(assembly_file)

    assembly_file_text = replace_hex_with_decimal(assembly_file_text)
    assembly_file_text = replace_nop_with_addi(assembly_file_text)
    assembly_file_text = replace_ret_with_jalr(assembly_file_text)
    assembly_file_text = replace_nice_looking_stores(assembly_file_text)
    assembly_file_text = replace_nice_looking_loads(assembly_file_text)
    assembly_file_text = replace_nice_looking_registers(assembly_file_text)
    assembly_file_text = ensure_newline_at_end(assembly_file_text)

    temp_assembly_file = "examples/tmp.rvi"
    write_assembly_file(temp_assembly_file, assembly_file_text)
    return parse_input(temp_assembly_file, **vars(args))


def read_assembly_file(assembly_file):
    with open(assembly_file) as f:
        return f.read()


def write_assembly_file(assembly_file, assembly_file_text):
    with open(assembly_file, "w") as f:
        f.write(assembly_file_text)


def replace_nop_with_addi(assembly_file_text):
    assembly_file_text = assembly_file_text.replace('nop', 'addi x0, x0, 0')
    return assembly_file_text


def replace_ret_with_jalr(assembly_file_text):
    assembly_file_text = assembly_file_text.replace('ret', 'jalr x0, x1, 0')
    return assembly_file_text


def replace_nice_looking_stores(assembly_file_text):
    lines = io.StringIO(assembly_file_text).readlines()
    lines_updated = []
    for l in lines:
        tokens = re.findall(r"[\w']+", l)
        if tokens and tokens[0] == "sw":
            inst = "sw"
            rs1 = tokens[1]
            rs2 = tokens[3]
            imm = tokens[2]
            l = inst + " " + rs2 + ", " + rs1 + ", " + imm + "\n"
        lines_updated.append(l)
    return ''.join(lines_updated)


def replace_nice_looking_loads(assembly_file_text):
    lines = io.StringIO(assembly_file_text).readlines()
    lines_updated = []
    load_types = ['lb', 'lh', 'lw']
    for l in lines:
        tokens = re.findall(r"[\w']+", l)
        if tokens and tokens[0] in load_types:
            inst = tokens[0]
            rs1 = tokens[1]
            rs2 = tokens[3]
            imm = tokens[2]
            l = inst + " " + rs1 + ", " + rs2 + ", " + imm + "\n"
        lines_updated.append(l)
    return ''.join(lines_updated)


def replace_nice_looking_registers(assembly_file_text):
    nice_regs = re.findall(r'\bx\d+', assembly_file_text)
    ugly_regs = [w.replace('x', '$') for w in nice_regs]
    for index, nice_reg in enumerate(nice_regs):
        assembly_file_text = assembly_file_text.replace(nice_reg, ugly_regs[index])
    return assembly_file_text


def replace_hex_with_decimal(assembly_file_text):
    hex_numbers = re.findall(r'\b0x\w+', assembly_file_text)
    for hex_num in hex_numbers:
        assembly_file_text = assembly_file_text.replace(hex_num, str(int(hex_num, 16)))
    return assembly_file_text


def ensure_newline_at_end(assembly_file_text):
    return assembly_file_text + "\n"
