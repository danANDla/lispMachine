from lispTranslator.lispClasses import *
from exceptions import *

funcs = {
    'print': ListType.FUNC,
    'defmacro': ListType.FUNC,
    '+': ListType.FUNC,
    '-': ListType.FUNC,
    'mod': ListType.FUNC,
    'rem': ListType.FUNC,
    '=': ListType.FUNC,
    '>': ListType.FUNC,
    '>=': ListType.FUNC,
    '<': ListType.FUNC,
    '<=': ListType.FUNC,
    'setq': ListType.SPEC,
    'progn': ListType.SPEC,
    'loop': ListType.SPEC,
    'return': ListType.SPEC,
    'if': ListType.SPEC,
}
symbols = {}
symbMem = [0 for i in range(100)] # symbols Addresses, prealloc mem for 100 prevs


# Function to check balanced parentheses
def checkParentheses(myStr):
    stack = []
    open_list = ["("]
    close_list = [")"]
    for i in myStr:
        if i in open_list:
            stack.append(i)
        elif i in close_list:
            pos = close_list.index(i)
            if ((len(stack) > 0) and
                    (open_list[pos] == stack[len(stack) - 1])):
                stack.pop()
            else:
                return "Unbalanced"
    if len(stack) == 0:
        return "Balanced"
    else:
        return "Unbalanced"


def isSelfEvaluated(pred: str) -> bool:
    if pred[0] == '"' or str.isnumeric(pred) or pred == 'NIL' or pred == 'T':
        return True
    else:
        return False


def substituteRecursively(dic: dict, expr):
    for i, content in enumerate(expr):
        if type(content) == str:
            s = str(content)
            if s.startswith(',') and s[1:] in dic:
                lispObj = dic.get(s[1:])
                if type(lispObj) == list:
                    expr[i] = lispObj[0]
                    for o in lispObj[1:]:
                        expr.append(o)
                    break
                else:
                    expr[i] = lispObj

        else:
            expr[i] = substituteRecursively(dic, expr[i])
    return expr


def makeFuncFromMacro(macro: LispList):
    rule = symbols.get(macro.content)
    macroArgs = {}
    for i, arg in enumerate(rule[1].args[1]):
        if arg.startswith('&'):
            s = []
            for j in range(i, len(macro.args)):
                s.append(macro.args[i])
            macroArgs[arg[1:]] = s

        else:
            macroArgs[arg] = macro.args[i]

    body = rule[1].args[2]
    subBody = substituteRecursively(macroArgs, body)

    newForm = makeLispForm(subBody)

    return newForm


def makeLispForm(expr):
    if type(expr) == LispAtom or type(expr) == LispList:
        return expr
    if type(expr) != list:
        s = str(expr)
        form = []
        if s.isnumeric():
            form = LispAtom(int(expr), AtomType.NUM)
        elif s.startswith('"'):
            form = LispAtom(expr, AtomType.STR)
        elif s == 'NIL' or s == 'T':
            form = LispAtom(expr, AtomType.CONST)
        elif s in symbols:
            form = LispAtom(expr, AtomType.SYMB)
        else:
            symbols[s] = (AtomType.UNDEF, LispAtom('n', AtomType.UNDEF), len(symbMem))
            symbMem.append('NIL')
            form = LispAtom(expr, AtomType.SYMB)

        return form

    pred = expr[0]
    if isSelfEvaluated(pred):
        raise SymbNotFoundException("Bad Lisp Form\nForm starts with self-evaluating object")
    if pred not in symbols and pred not in funcs:
        # symbols[pred] = (AtomType.CONST, constNIL)
        raise SymbNotFoundException(f"Unknown symbol '{pred}'")

    if pred == 'defmacro':
        form = LispList(pred, ListType.MACRO, expr[1:])
    else:
        args = []
        for arg in expr[1:]:
            args.append(makeLispForm(arg))
        form = LispList(pred, funcs.get(pred), args)

    if pred == 'defmacro':
        if expr[1] in symbols:
            raise MacrosNameTakenException(f"Macos with name '{pred}' is already defined")
        symbols[expr[1]] = (ListType.MACRO, form)
    elif pred in symbols and type(symbols.get(pred)) != LispAtom:
        form = makeFuncFromMacro(form)

    return form


def readExpressions(text, pos, prevCh):
    sExpressions = []
    sExpr = ''
    stringReading = False
    while pos < len(text):
        ch = text[pos]
        if ch == '"':
            if stringReading:
                stringReading = False
                sExpr += ch
                sExpressions.append(sExpr)
                sExpr = ''
            else:
                stringReading = True
                sExpr += ch
        elif ch == ' ' or ch == '\n':
            if sExpr == '' and (prevCh == ' ' or prevCh == '\n'):
                sExpr = 'NIL'
            if sExpr != '' and sExpr != '\n':
                sExpressions.append(sExpr)
            sExpr = ''
        elif ch == '(':
            sExpr, pos = readExpressions(text, pos + 1, ch)
            prevCh = text[pos]
            sExpressions.append(sExpr)
            sExpr = ''
            pos += 1
            continue
        elif ch == ')':
            if sExpr == '' and (prevCh == ' ' or prevCh == '\n'):
                sExpr = 'NIL'
            if sExpr != '' and sExpr != '\n':
                sExpressions.append(sExpr)
            return sExpressions, pos
        else:
            sExpr += ch
        pos += 1
        prevCh = ch

    return sExpressions, pos, text[pos - 1]


def showSymbols():
    print("{")
    for k in symbols.keys():
        print(f'{k}: <{symbols.get(k)[0]}> {symbols.get(k)[1].content}')
    print("}")
    print()


# [reader]
def readerWork(text):
    sExpressions = []
    forms = []
    if checkParentheses(text) == 'Balanced':
        sExpressions = readExpressions(text, 0, 'a')
        for expr in sExpressions[0]:
            form = makeLispForm(expr)
            if form.type != ListType.MACRO:
                forms.append(form)
    else:
        print('Bad parenthesis')
    return forms
