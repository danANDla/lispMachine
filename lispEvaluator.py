from lispClasses import *
from lispReader import funcs, symbols, symbMem
from exceptions import *
from isa import Opcode

buffer = 0
prevId = 0


def createInstr(op: Opcode, arg, ismem):
    return {
        "opcode": op,
        "arg": arg,
        "isAddr": ismem != 0
    }


def loadValue(value: LispAtom) -> list:
    loadingValue = 0
    machineCodes = []
    if value.type == AtomType.SYMB:
        '''
            load mem[symbol.addres]
        '''
        address = symbols[value.content][2]
        machineCodes.append(createInstr(Opcode.LOAD, address, 1))
        return machineCodes
    elif value.type == AtomType.CONST:
        if value.content == 'T':
            loadingValue = 1
        else:
            loadingValue = 0
    elif value.type == AtomType.PREV:
        address = 'prev' + str(value.content)
        machineCodes.append(createInstr(Opcode.LOAD, address, 1))
        return machineCodes
    else:
        loadingValue = value.content

    machineCodes.append(createInstr(Opcode.LOAD, loadingValue, 0))
    return machineCodes


def storeValue(value: LispAtom) -> list:
    machineCodes = []
    if value.type == AtomType.SYMB:
        address = symbols[value.content][2]
        machineCodes.append(createInstr(Opcode.STORE, address, 1))
        return machineCodes
    elif value.type == AtomType.NUM:
        machineCodes.append(createInstr(Opcode.STORE, value.content, 1))
    elif value.type == AtomType.PREV:
        machineCodes.append(createInstr(Opcode.STORE, value.content, 1))
    return machineCodes


def storePrev(prev):
    return storeValue(LispAtom('prev' + str(prev), AtomType.PREV))


def lispSetq(form):
    machineOp = []
    if len(form.args) != 2:
        raise InvalidFunctionSignatureException(f'wrong arguments number of function {form.content}')
    if form.args[0].type != AtomType.SYMB:
        raise InvalidFunctionSignatureException(
            f'first argument of function "{form.content}" was another type than a symbol')

    if form.args[0].content in symbols:
        memAddr = symbols[form.args[0].content][2]
        symbols[form.args[0].content] = (AtomType.CONST, constNIL, memAddr)
    else:
        symbols[form.args[0].content] = (AtomType.CONST, constNIL, len(symbMem))

    val = form.args[1]
    t = val.type

    if t == AtomType.SYMB:
        if val.content not in symbols:
            raise SymbNotFoundException(f'unknown symbol {val.content}')
    for i in loadValue(form.args[1]):
        machineOp.append(i)
    for i in storeValue(form.args[0]):
        machineOp.append(i)
    return machineOp


def lispSum(form: LispList):
    for i, a in enumerate(form.args):
        if a.type == AtomType.SYMB and symbols[a.content][0] == AtomType.UNDEF:
            raise SymbNotFoundException(f"Unknown symbol '{a.content}'")
        if type(a) != LispAtom:
            raise InvalidFunctionSignatureException(f'sum function only works with atoms')
        if not (a.type == AtomType.SYMB or a.type == AtomType.NUM or a.type == AtomType.PREV):
            raise InvalidFunctionSignatureException(f'sum function only works with numbers')
        if a.type == AtomType.SYMB and not (
                symbols[a.content] == 'NIL' or
                symbols[a.content] == constNIL or
                symbols[a.content][0] == AtomType.CONST or
                symbols[a.content][0] == AtomType.NUM):
            raise InvalidFunctionSignatureException(f'sum function only works with numbers')

    machineCodes = []

    for instr in loadValue(form.args[0]):
        machineCodes.append(instr)

    if form.args[1].type == AtomType.PREV:
        machineCodes.append(createInstr(Opcode.ADD, "prev" + str(form.args[1].content), 1))
    elif form.args[1].type == AtomType.SYMB:
        machineCodes.append(createInstr(Opcode.ADD, symbols[form.args[1].content][2], 1))
    else:
        machineCodes.append(createInstr(Opcode.ADD, form.args[1].content, 0))
    return machineCodes


def execFunc(form: LispList):
    print(form)
    machineCodes = []
    global prevId

    for i, arg in enumerate(form.args):
        if type(arg) == LispList:
            form.args[i] = LispAtom(prevId, AtomType.PREV)
            prevId += 1

    if form.content in funcs:
        match form.content:
            case '+':
                machineCodes = lispSum(form)
                machineCodes += storePrev(prevId)
                prevId += 1
            case 'setq':
                machineCodes = lispSetq(form)

    return machineCodes


# [evaluator]
def evaluate(form: LispObject, machineCodes: list, isFirst):
    global prevId
    if isFirst:
        prevId = 0
    if type(form) == LispAtom:
        return machineCodes
    else:
        if form.content == 'loop':
            print('is loop')
        else:
            for i, arg in enumerate(form.args):
                machineCodes = evaluate(arg, machineCodes, False)
            machineCodes += execFunc(form)
    return machineCodes
