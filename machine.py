import sys
import logging
from isa import Opcode, read_code
from enum import Enum
from exceptions import WrongSignalException, EmptyInputException


class Signal(str, Enum):
    CU = 'fromCU'
    ACC = 'fromAcc'
    MEM = 'fromMem'
    ALU = 'fromAlu'
    PC = 'fromPC'
    IO = 'fromIO'
    WR = 'writeMem'
    NEXT = 'next'
    ZERO = 'zero'
    NEG = 'neg'
    ADD = 'add'


class ArithmeticLogicUnit:
    def __init__(self):
        self.left = 0
        self.right = 0
        self.res = 0

        self.leftNeg = False
        self.rightNeg = False
        self.rightNul = False
        self.operation = Opcode.ADD

    def set(self, left: int, leftNeg: bool, rightNeg: bool, rightNul: bool, op: Opcode):
        self.left = left
        self.leftNeg = leftNeg
        self.rightNeg = rightNeg
        self.rightNul = rightNul
        self.operation = op

    def setNoArg(self, leftNeg: bool, rightNeg: bool, rightNul: bool, op: Opcode):
        self.leftNeg = leftNeg
        self.rightNeg = rightNeg
        self.rightNul = rightNul
        self.operation = op

    def execOperation(self):
        if self.leftNeg:
            self.left = -abs(self.left)
        if self.rightNeg:
            self.right = -abs(self.right)
        if self.rightNul:
            self.right = 0

        match self.operation:
            case Opcode.ADD:
                self.res = self.left + self.right


class DataPath:
    def __init__(self, memSize: int, inputTokens: list):
        self.inputTokens = inputTokens
        self.dataMemory = [0 for _ in range(memSize)]
        self.acc = 0
        self.addr = 0
        self.alu = ArithmeticLogicUnit()
        self.zf = False
        self.sf = False
        self.outBuff = []

    def latchAddr(self, sel: Signal):
        if sel == Signal.ACC:
            self.addr = self.acc
        elif sel == Signal.CU:
            pass
        else:
            raise WrongSignalException('invalid signal')

    def latchAcc(self, sel: Signal):
        if sel == Signal.MEM:
            self.acc = self.dataMemory[self.addr]
        elif sel == Signal.ALU:
            self.acc = self.alu.res
        elif sel == Signal.IO:
            if len(self.inputTokens) == 0:
                raise EmptyInputException('end of file reached')
            self.acc = ord(self.inputTokens.pop(0))
        else:
            raise WrongSignalException('invalid signal')

    def latchZF(self, sel: Signal):
        if sel == Signal.ACC:
            self.zf = self.acc == 0
        elif sel == Signal.ALU:
            self.zf = self.alu.res == 0
        else:
            raise WrongSignalException('invalid signal')

    def latchSF(self, sel: Signal):
        if sel == Signal.ACC:
            self.sf = self.acc < 0
        elif sel == Signal.ALU:
            self.sf = self.alu.res < 0

    def latchAlu(self, sel: Signal):
        self.alu.right = self.acc
        if sel == Signal.MEM:
            self.alu.left = self.dataMemory[self.addr]
        elif sel == Signal.CU:
            pass
        elif sel == Signal.PC:
            pass
        else:
            raise WrongSignalException('invalid signal')

    def writeMem(self):
        self.dataMemory[self.addr] = self.acc

    def output(self):
        symbol = chr(self.acc)
        self.outBuff.append(symbol)


class ControlUnit:
    def __init__(self, program: list, dataPath: DataPath):
        self.program = program
        self.pc = 0
        self.dataPath = dataPath
        self._tick = 0

    def tick(self):
        self._tick += 1

    def getTick(self):
        return self._tick

    def latchPC(self, sel: Signal):
        if sel == Signal.NEXT:
            self.pc += 1
        elif sel == Signal.ACC:
            self.pc = self.dataPath.acc
        else:
            raise WrongSignalException('invalid signal')

    def putToAcc(self, arg):
        self.dataPath.alu.set(arg, False, False, True, Opcode.ADD)
        self.dataPath.latchAlu(Signal.CU)
        self.dataPath.alu.execOperation()
        self.dataPath.latchAcc(Signal.ALU)

    def workInstruction(self):
        instr = self.program[self.pc]
        opcode = instr["opcode"]
        arg = instr["arg"]

        match opcode:
            case Opcode.HLT:
                return Opcode.HLT
            case Opcode.LOAD:
                if instr["mem"] == 1:
                    self.dataPath.addr = arg
                    self.dataPath.latchAddr(Signal.CU)
                    self.tick()
                    self.dataPath.latchAcc(Signal.MEM)
                elif instr["mem"] == 2:
                    self.dataPath.addr = arg
                    self.dataPath.latchAddr(Signal.CU)
                    self.tick()
                    self.dataPath.latchAcc(Signal.MEM)

                    self.dataPath.latchAddr(Signal.ACC)
                    self.dataPath.latchAcc(Signal.MEM)
                else:
                    self.putToAcc(arg)
                    self.tick()
                    self.dataPath.latchAcc(Signal.ALU)
                self.latchPC(Signal.NEXT)
                self.tick()

            case Opcode.STORE:
                self.dataPath.addr = arg
                self.dataPath.latchAddr(Signal.CU)
                self.tick()
                self.dataPath.writeMem()
                self.latchPC(Signal.NEXT)
                self.tick()

            case Opcode.ADD | Opcode.SUB | Opcode.REM | Opcode.MOD:
                if instr["mem"] == 1:
                    self.dataPath.addr = arg
                    self.dataPath.latchAddr(Signal.CU)
                    self.tick()
                    self.dataPath.latchAlu(Signal.MEM)
                else:
                    self.dataPath.alu.left = arg
                    self.dataPath.latchAlu(Signal.CU)
                self.tick()
                self.dataPath.alu.setNoArg(False, False, False, Opcode.ADD)
                self.dataPath.alu.execOperation()
                self.dataPath.latchAcc(Signal.ALU)
                self.latchPC(Signal.NEXT)
                self.tick()

            case Opcode.JMP:
                self.putToAcc(self.pc)
                self.tick()
                if instr["mem"] == 1:
                    pass
                elif instr["mem"] == 3:
                    self.dataPath.alu.set(arg, False, False, False, Opcode.ADD)
                    self.dataPath.latchAlu(Signal.CU)
                    self.dataPath.alu.execOperation()
                    self.dataPath.latchAcc(Signal.ALU)
                    self.tick()

                self.latchPC(Signal.ACC)
                self.tick()

            case Opcode.CMP:
                if instr["mem"] == 1:
                    self.dataPath.addr = arg
                    self.dataPath.latchAddr(Signal.CU)
                    self.tick()
                    self.dataPath.latchAlu(Signal.MEM)
                else:
                    self.dataPath.alu.left = arg
                    self.dataPath.latchAlu(Signal.CU)
                self.dataPath.alu.setNoArg(True, False, False, Opcode.ADD)
                self.dataPath.alu.execOperation()
                self.dataPath.latchZF(Signal.ALU)
                self.dataPath.latchSF(Signal.ALU)
                self.latchPC(Signal.NEXT)
                self.tick()

            case Opcode.JE | Opcode.JNE | Opcode.JL | Opcode.JLE:
                if opcode == Opcode.JE and not self.dataPath.zf or opcode == Opcode.JNE and self.dataPath.zf:
                    self.latchPC(Signal.NEXT)
                    self.tick()
                elif opcode == Opcode.JL and not self.dataPath.sf or \
                        (opcode == Opcode.JLE and not self.dataPath.sf and not self.dataPath.zf):
                    self.latchPC(Signal.NEXT)
                    self.tick()
                else:
                    self.putToAcc(self.pc)
                    self.tick()
                    if instr["mem"] == 1:
                        pass
                    elif instr["mem"] == 3:
                        self.dataPath.alu.set(arg, False, False, False, Opcode.ADD)
                        self.dataPath.latchAlu(Signal.CU)
                        self.dataPath.alu.execOperation()
                        self.dataPath.latchAcc(Signal.ALU)
                        self.tick()

                    self.latchPC(Signal.ACC)
                    self.tick()

            case Opcode.PRINT:
                self.dataPath.output()
                self.latchPC(Signal.NEXT)
                self.tick()

            case Opcode.SCAN:
                if instr["mem"] == 1:
                    self.dataPath.addr = arg
                    self.dataPath.latchAddr(Signal.CU)
                    self.dataPath.latchAcc(Signal.IO)
                    self.dataPath.writeMem()
                    self.tick()
                self.latchPC(Signal.NEXT)
                self.tick()

    def __repr__(self):
        zf = 0
        sf = 0
        if self.dataPath.zf:
            zf = 1
        if self.dataPath.sf:
            sf = 1
        state = "{{TICK: {}, PC: {}, ADDR: {}, OUT: {}, ACC: {}, ZF|SF: {}{}}}".format(
            self._tick,
            self.pc,
            self.dataPath.addr,
            self.dataPath.dataMemory[self.dataPath.addr],
            self.dataPath.acc,
            zf, sf
        )

        instr = self.program[self.pc]
        opcode = instr["opcode"]
        arg = instr.get("arg", "")
        isAddr = ''
        if instr["mem"] == 1:
            isAddr = 'addr'
        elif instr["mem"] == 2:
            isAddr = 'indirect addr'
        elif instr["mem"] == 3:
            isAddr = 'relative addr'

        action = "{} {} {}".format(opcode, arg, isAddr)

        return "{} {}".format(state, action)


def simulation(code, inputTokens, data_memory_size, limit):
    data_path = DataPath(data_memory_size, inputTokens)
    control_unit = ControlUnit(code, data_path)
    instr_counter = 0

    logging.debug('%s', control_unit)
    try:
        while True:
            if instr_counter > limit:
                print("too long execution")
                return
            res = control_unit.workInstruction()
            if res == Opcode.HLT:
                break
            instr_counter += 1
            logging.debug('%s', control_unit)
    except EOFError:
        logging.warning('Input buffer is empty!')
    except StopIteration:
        pass
    logging.info('output_buffer: %s', repr(''.join(data_path.outBuff)))
    return ''.join(data_path.outBuff), instr_counter, control_unit.getTick()


def main(args):
    if len(args) != 2:
        print("wrong args")
        return
    code_file, input_file = args

    code = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    input_token.append('\0')
    output, instr_counter, ticks = simulation(code,
                                              inputTokens=input_token,
                                              data_memory_size=1000,
                                              limit=1000)

    print(''.join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
