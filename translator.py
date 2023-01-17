"""
    Транслятор LISP в машинный код
"""

import sys
from lispClasses import *
from lispReader import *
from lispEvaluator import *


def main(args):
    f = open("lispCode", mode="r")
    text = f.read().strip()

    sExpressions = readerWork(text)
    forms = []

    for expr in sExpressions:
        try:
            form = makeLispForm(expr)
            forms.append(form)
        except SymbNotFoundException as e:
            print(e)

    for form in forms:
        evaluate(form)
        print()


if __name__ == '__main__':
    main(sys.argv[1:])
