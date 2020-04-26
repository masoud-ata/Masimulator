#!/usr/bin/python
# @author:Don Dennis
# rvi.py
#
# The RISC-V assembler for subset of instructions.

from assembler.lib.parser import parse_input
import argparse
import re


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
                    help="Output file name.", default = 'a.b')
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
    temp_assembly_file = replace_nop_with_addi(assembly_file)
    temp_assembly_file = replace_nice_looking_stores(temp_assembly_file)
    temp_assembly_file = replace_nice_looking_loads(temp_assembly_file)
    return parse_input(temp_assembly_file, **vars(args))


def replace_nop_with_addi(assembly_file):
    with open(assembly_file) as f:
        newText = f.read().replace('nop', 'addi $0, $0, 0')
    temp_assembly_file = "examples/tmp.rvi"
    with open(temp_assembly_file, "w") as f:
        f.write(newText)
    return temp_assembly_file


def replace_nice_looking_stores(assembly_file):
    in_file = open(assembly_file, 'r')
    lines = in_file.readlines()
    lines_2_write = []

    for l in lines:
        sw_pos = l.find('sw')
        if sw_pos > 0:
            rs1 = 0
            rs2 = 1
            imm = 2
            numbers = re.findall("[-\d]+", l)
            l = " " * sw_pos + "sw " + "$" + str(numbers[rs2]) + ", " + "$" + str(numbers[rs1]) + ", " + str(numbers[imm]) + "\n"
        lines_2_write.append(l)
    in_file.close()

    out_file = open(assembly_file, "w")
    for line in lines_2_write:
        out_file.write(line)
    out_file.close()

    return assembly_file


def replace_nice_looking_loads(assembly_file):
    in_file = open(assembly_file, 'r')
    lines = in_file.readlines()
    lines_2_write = []

    for l in lines:
        lw_pos = l.find('lw')
        if lw_pos > 0:
            rd = 0
            rs1 = 1
            imm = 2
            numbers = re.findall("[-\d]+", l)
            l = " " * lw_pos + "lw " + "$" + str(numbers[rd]) + ", " + "$" + str(numbers[rs1]) + ", " + str(numbers[imm]) + "\n"
        lines_2_write.append(l)
    in_file.close()

    out_file = open(assembly_file, "w")
    for line in lines_2_write:
        out_file.write(line)
    out_file.close()

    return assembly_file
