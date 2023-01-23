# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

"""
    Транслятор LISP в машинный код
"""

import sys
from lispTranslator.lispReader import readerWork
from lispTranslator.lispEvaluator import evaluate, createInstr
from isa import write_code, Opcode

prevId = 0


def main(args):
    if len(args) != 2:
        print("wrong args")
        return
    global prevId
    with open(args[0], mode="r", encoding="UTF-8") as f:
        text = f.read().strip()

    sExpressions, symbols, _ = readerWork(text)

    code = []
    for form in sExpressions:
        machineCodes = []
        prevId = 0
        machineCodes, _, symbols = evaluate(form, machineCodes, 0, symbols)
        code += machineCodes

    code.append(createInstr(Opcode.HLT, '', 0))
    write_code(args[1], code)


if __name__ == '__main__':
    main(sys.argv[1:])
