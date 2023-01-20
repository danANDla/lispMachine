"""
    Транслятор LISP в машинный код
"""

import sys
from lispTranslator.lispReader import *
from lispTranslator.lispEvaluator import *
from isa import write_code

prevId = 0


def main(args):
    if len(args) != 2:
        print("wrong args")
        return
    global prevId
    f = open(args[0], mode="r")
    text = f.read().strip()

    sExpressions = readerWork(text)
    forms = []

    for expr in sExpressions:
        try:
            form = makeLispForm(expr)
            forms.append(form)
        except SymbNotFoundException as e:
            print(e)

    code = []
    for form in forms:
        machineCodes = []
        prevId = 0
        machineCodes = evaluate(form, machineCodes, 0)[0]
        code += machineCodes

    code.append(createInstr(Opcode.HLT, '', 0))
    write_code(args[1], code)


if __name__ == '__main__':
    main(sys.argv[1:])
