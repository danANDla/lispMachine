import sys
import logging
from isa import Opcode, read_code
from enum import Enum
from exceptions import WrongSignalException


class Signal(str, Enum):
    CU = 'fromCU'
    ACC = 'fromAcc'
    MEM = 'fromMem'
    ALU = 'fromAlu'
    PC = 'fromPC'
    WR = 'writeMem'
    NEXT = 'next'
    ZERO = 'zero'
    NEG = 'neg'
    ADD = 'add'


class ALOperation(str, Enum):
    ADD = 'add'


class ArithmeticLogicUnit:
    def __init__(self):
        self.left = 0
        self.right = 0
        self.res = 0

        self.leftNeg = False
        self.rightNeg = False
        self.rightNul = False
        self.operation = ALOperation.ADD

    def execOperation(self):
        if self.leftNeg:
            self.left = -abs(self.left)
        if self.rightNeg:
            self.right = -abs(self.right)
        if self.rightNul:
            self.right = 0

        match self.operation:
            case ALOperation.ADD:
                self.res = self.left + self.right


class DataPath:
    def __init__(self, memSize: int, inputTokens: list):
        self.inputTokens = inputTokens
        self.dataMemory = [0 for _ in range(memSize)]
        self.acc = 0
        self.addr = 0
        self.alu = ArithmeticLogicUnit()
        self.zf = False
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
        else:
            raise WrongSignalException('invalid signal')

    def latchZF(self, sel: Signal):
        if sel == Signal.ACC:
            self.zf = self.acc == 0
        elif sel == Signal.ALU:
            self.zf = self.alu.res == 0
        else:
            raise WrongSignalException('invalid signal')

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
        self.dataPath.alu.left = arg
        self.dataPath.alu.leftNeg = False
        self.dataPath.alu.rightNul = True
        self.dataPath.alu.operation = ALOperation.ADD
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

            case Opcode.ADD:
                if instr["mem"] == 1:
                    self.dataPath.addr = arg
                    self.dataPath.latchAddr(Signal.CU)
                    self.tick()
                    self.dataPath.latchAlu(Signal.MEM)
                else:
                    self.dataPath.alu.left = arg
                    self.dataPath.latchAlu(Signal.CU)
                self.tick()
                self.dataPath.alu.leftNeg = False
                self.dataPath.alu.rightNeg = False
                self.dataPath.alu.rightNul = False
                self.dataPath.alu.operation = ALOperation.ADD
                self.dataPath.alu.execOperation()
                self.dataPath.latchAcc(Signal.ALU)
                self.latchPC(Signal.NEXT)
                self.tick()

            case Opcode.PRINT:
                self.dataPath.output()
                self.latchPC(Signal.NEXT)
                self.tick()

            case Opcode.JMP:
                self.putToAcc(self.pc)
                self.tick()
                if instr["mem"] == 1:
                    pass
                elif instr["mem"] == 3:
                    self.dataPath.alu.left = arg
                    self.dataPath.alu.leftNeg = False
                    self.dataPath.alu.rightNeg = False
                    self.dataPath.alu.rightNul = False
                    self.dataPath.alu.operation = ALOperation.ADD
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
                self.dataPath.alu.leftNeg = False
                self.dataPath.alu.rightNeg = True
                self.dataPath.alu.rightNul = False
                self.dataPath.alu.operation = ALOperation.ADD
                self.dataPath.alu.execOperation()
                self.dataPath.latchZF(Signal.ALU)
                self.latchPC(Signal.NEXT)
                self.tick()

            case Opcode.JE:
                if not self.dataPath.zf:
                    self.latchPC(Signal.NEXT)
                    self.tick()
                else:
                    self.putToAcc(self.pc)
                    self.tick()
                    if instr["mem"] == 1:
                        pass
                    elif instr["mem"] == 3:
                        self.dataPath.alu.left = arg
                        self.dataPath.alu.leftNeg = False
                        self.dataPath.alu.rightNeg = False
                        self.dataPath.alu.rightNul = False
                        self.dataPath.alu.operation = ALOperation.ADD
                        self.dataPath.latchAlu(Signal.CU)
                        self.dataPath.alu.execOperation()
                        self.dataPath.latchAcc(Signal.ALU)
                        self.tick()

                    self.latchPC(Signal.ACC)
                    self.tick()

    def __repr__(self):
        state = "{{TICK: {}, PC: {}, ADDR: {}, OUT: {}, ACC: {}, ZF: {}}}".format(
            self._tick,
            self.pc,
            self.dataPath.addr,
            self.dataPath.dataMemory[self.dataPath.addr],
            self.dataPath.acc,
            self.dataPath.zf
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


def simulation(code, input_tokens, data_memory_size, limit):
    data_path = DataPath(data_memory_size, input_tokens)
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

    output, instr_counter, ticks = simulation(code,
                                              input_tokens=input_token,
                                              data_memory_size=1000,
                                              limit=1000)

    print(''.join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
