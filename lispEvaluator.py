from lispClasses import *
from lispReader import funcs, symbols
from exceptions import *

def setq(form):
    machineOp = []

    print("\nSETQ START")
    if len(form.args) != 2:
        raise InvalidFunctionSignatureException(f'wrong arguments number of function {form.content}')
    if form.args[0].type != AtomType.SYMB:
        raise InvalidFunctionSignatureException(
            f'first argument of function "{form.content}" was another type than a symbol')
    val = evaluate(form.args[1])
    t = val.type
    if t == AtomType.NUM or t == AtomType.STR or t == AtomType.CONST:
        symbols[form.args[0].content] = val.content
        print("{")
        for k in symbols.keys():
            print(f'{k}: {symbols.get(k)}')
        print("}")
        print()
    else:



def execFunc(form: LispList):
    print(f'|{form.type}| {form.content} ', end="")
    if form.content in funcs:
        match form.content:
            case 'setq':





# [evaluator]
def evaluate(form: LispObject):
    if type(form) == LispAtom:
        return form
    else:
        execFunc(form)
    return
