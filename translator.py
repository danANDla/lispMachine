"""
    Транслятор LISP в машинный код
"""

import sys
from lispClasses import *
from lispReader import *
from lispEvaluator import *
from isa import write_code

prevId = 0


def main(args):
    global prevId
    f = open("lispPrograms/lispCode", mode="r")
    text = f.read().strip()

    text = "(setq a 5) (setq b 2) (+ b (+ b (+ 1 (+ a b))))"
    text = "(setq a 5) (setq b 2) (+ b (+ b (+ (+ a 1) (+ a b)))) (+ b (+ 1 2))"

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
        machineCodes = evaluate(form, machineCodes, True)
        code += machineCodes

    write_code("lispPrograms/out", code)


if __name__ == '__main__':
    main(sys.argv[1:])
