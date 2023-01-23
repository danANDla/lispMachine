# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

"""
    Lisp objects that used in Lisp evaluator
"""
import dataclasses
from enum import Enum


class AtomType(str, Enum):
    SYMB = 'symbol'
    NUM = 'number'
    STR = 'string'
    CONST = 'constant symbol'
    UNDEF = 'undefined'
    PREV = 'prev'


class ListType(str, Enum):
    FUNC = 'function'
    SPEC = 'special operator'
    MACRO = 'macros'


@dataclasses.dataclass
class LispObject:
    def __init__(self, content):
        self.content = content


@dataclasses.dataclass
class LispAtom(LispObject):
    def __init__(self, content, atomType: AtomType):
        super().__init__(content)
        self.type = atomType

    def __str__(self):
        return f'|{self.type}| {self.content}'


@dataclasses.dataclass
class LispList(LispObject):
    def __init__(self, content, listType: ListType, args):
        super().__init__(content)
        self.type = listType
        self.args = args

    def __str__(self):
        return f'|{self.type}| {self.content}, args: {self.args}'


constNIL = LispAtom('NIL', AtomType.CONST)
constT = LispAtom('T', AtomType.CONST)
