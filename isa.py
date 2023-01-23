# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

import json
from enum import Enum


class Opcode(str, Enum):
    LOAD = 'load'
    STORE = 'store'
    ADD = 'add'
    SUB = 'sub'
    MOD = 'mod'
    REM = 'rem'
    PRINT = 'print'
    SCAN = 'scan'
    READ = 'read'
    JMP = 'jmp'
    CMP = 'cmp'
    JE = 'je'
    JNE = 'jne'
    JL = 'jl'
    JLE = 'jle'
    HLT = 'hlt'
    MEM = 'mem'


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(code, indent=4))


def read_code(filename):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())
    return code
