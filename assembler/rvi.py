#!/usr/bin/python
# @author:Don Dennis
# rvi.py
#
# The RISC-V assembler for subset of instructions.

from assembler.lib.parser import parse_input
import argparse
from argparse import Namespace


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


def assemble():
    args = get_arguments()
    assembly_file = args.INFILE
    temp_assembly_file = replace_nop_with_addi(assembly_file)
    return parse_input(temp_assembly_file, **vars(args))


def assemble_again(assembly_file):
    args = get_arguments()
    assembly_file = assembly_file
    temp_assembly_file = replace_nop_with_addi(assembly_file)
    return parse_input(temp_assembly_file, **vars(args))


def replace_nop_with_addi(assembly_file):
    with open(assembly_file) as f:
        newText = f.read().replace('nop', 'addi $0, $0, 0')

    temp_assembly_file = "examples/tmp.rvi"
    with open(temp_assembly_file, "w") as f:
        f.write(newText)

    return temp_assembly_file
