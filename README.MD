# Лабораторная работа №3 по Архитектуре компьютера.
- Алексеев Даниил, Р33302
- ```lisp | acc | harv | hw | instr | struct | stream | port | prob2```



# Язык программирования Lisp
S-expression - символьноe выражение - способ представления вложенных списков данныx.
``` ebnf
program ::= s-expression
s_expression ::= atomic_symbol \
               / list 
list ::= "(" s_expression < s_expression > ")"
atomic_symbol ::= letter atom_part
atom_part ::= empty / letter atom_part / number atom_part
letter ::= "a" / "b" / " ..." / "z"
number ::= "1" / "2" / " ..." / "9"
empty ::= " "
```

# Орагнизация памяти

Модель памяти процессора:

1. Память команд. Машинное слово -- не определено. Реализуется списком словарей, описывающих инструкции (одно слово -- одна ячейка).
2. Память данных. Машинное слово -- 8 бит, знаковое. Линейное адресное пространство. [Реализуется](https://github.com/danANDla/lispMachine/blob/master/schemes/lispMemory.jpg) списком чисел.
- Первые 100 ячеек выделены под prevs - промежуточные значения Lisp-forms в случае вычисления вложенных форм (на [рисунке](https://github.com/danANDla/lispMachine/blob/master/schemes/lispPrev.jpg) указан пример и как транслятор распределяет память для промежуточных значений).
- Затем в памяти хранятся значения переменных.
- В конце помяти лежат строки.

В процессе работы ***reader*** создается [таблица символов](https://github.com/danANDla/lispMachine/blob/master/schemes/lispString.jpg), которая связывает обозначение переменной с типом данных и ячейкой памяти, в которой будет хранится значение. После таблица передается ***evaluator***, где вместо переменных будет подставлены адреса.

# Система команд

Особенности процессора:

- Память данных:
    - адресуется через регистр `addr`
    - может быть записана:
        - из аккумулятора `acc`;
        - напрямую из декодера команд.
- Память команды:
    - адресуется через регистр `pc`
- Аккумулятор `acc`:
    - может быть записана:
        - из `ALU`;
        - из памяти;
    - может быть загружен в ячейку памяти;
- Счётчик команд: `pc`:
    - может быть записана:
        - через икрементирующую схему `+1`;
        - из аккумулятора `acc`.
- Арифметико-логическое устройство `ALU`:
    - левый операнд может быть записанн:
        - напрямую из декодера команд;
        - из счётчика команд `pc`;
        - из памяти;
    - правый операнд может быть записанн:
        - из аккумулятора `acc`;
    - на левый и правый операнд можно подать сигнал инвертирования;
    - на правый операнд можно подать сигнал обнуления;
    - возможно выполнить операции: сложения, целочисленного деления, взятие остатка.
- регистры `SF` (1 в случае отрицательного значения), `ZF` (1 в случае нулевого значения):
    - могут быть записаны:
        - из `ALU`;
        - из аккумулятора `acc`.
- Ввод-вывод -- порты ввода/вывода, токенизирован, символьный.

## ISA (instruction set architechture)

аккумуляторная архитектура - значит **все операции - однооперандные -** всегда применяются к значению в аккумуляторе и еще какому-то значению (хард код или память)


| OPCODE | ARG | DESCRIPTION | ADDRESSING |
| --- | --- | --- | --- |
| load | imm / mem | загрузить данные в аккумулятор | 1/2 |
| store | imm | загрузить данные из аккумулятора в память по адресу из аргумента | |
| add | imm / mem  | сложить аккумулятор с числом или числом из памяти | 1 |
| sub | imm / mem  | вычесть из аккумулятора с число или число из памяти | 1 |
| mod | |  | 1 |
| rem | |  | 1 |
| print | | загрузить данные из аккумулятора в порт io |  |
| read | mem | считать из io в аккумулятор | 1 | 
| jmp | imm | безусловный переход, изменить PC на значение из аккумулятора | 1/3 |
| cmp | imm / mem | сравнить аккумулятор с чсилом или значением из памяти | 1 |
| je | imm | елси ZF == 1, произвести переход по значению из аккумулятора | 1/3 |
| jne | imm | елси ZF == 0, произвести переход по значению из аккумулятора | 1/3 |
| jl | imm | елси SF == 1 && ZF == 0, произвести переход по значению из аккумулятора | 1/3 |
| jle | imm | елси SF == 1 \|\| ZF == 1, произвести переход по значению из аккумулятора | 1/3 |
| hlt | | остановка | |

ADDRESSING - режимы адресации: 1 - прямая, 2 - косвенная, 3 - относительная прямая

### Кодирование инструкций

- Машинный код сериализуется в список JSON.
- Один элемент списка, одна инструкция.
- Индекс списка -- адрес инструкции. Используется для команд перехода.

Пример:

```json
[
    {
        "opcode": "jz",
        "arg": 5,
        "mem": 1,
    }
]
```

где:

- `opcode` -- строка с кодом операции;
- `arg` -- аргумент;
- `mem` -- режимы адресации/

Типы данные в модуле [isa](./isa.py), где:

- `Opcode` -- перечисление кодов операций;


# Транслятор Lisp
Эапы трансляции:
text → [reader] → [evaluator] → opcodes

## [reader]

На вход принимает принимает текст и возвращает s-expressions.

**базовые элементы s-expression**

1. **lists** - помещаются в скобки, могут содержать любое количество элементов разделенных пробельными символами. Элементы являются s-expression’ами, т.е. lists содержут atoms или lists.
2. **atoms -** все остальное.
    - numbers
    - strings
    - names: функции, переменные, операторы.

## [evaluator]

На вход принимаются lisp forms и формируется машинный код. Не все s-expression являются lisp-forms. Lisp form - всё, что должно быть вычислено (evalueted). Можно сказать, что ***Вычислитель (evaluator)*** это функция (в общем значении), которая на вход получает правильную Lisp form и возвращает некоторое значение.d

**Lisp forms могут быть:**

- atoms
    - symbols: переменные
    - self-evaluating objects: numbers, strings. константы **`T`**, **`NIL`** - канонические значения true и false. **`NIL`** также обозначает пустой список: если ***reader*** видит `()` то интерпретирует это как **`NIL`**. **`NIL`** в - единственный объект одновременно являющийся атом и списком.
- lists
    - functions. Вычисляет все элементы списка и подает их на вход именованной функции (первому элементу списка).
    - special forms/special operators. Не все операции могут быть определены как функции. В эту категорюю попадают конструкии, контролирующие выполнение программы (control structs)
    - macros. Конструкции расширяющие основной синтаксис Lisp. Макросы это функции которые получают s-expression в качестве аргументы и возвращают Lisp form, которая затем вычисляется вместо макроса. определяется при помощи конструкции **`(defmacro macrosName (parametersL))`**
        1. элементы макроса пробрасываются в функцию без вычисления
        2. Lisp form, возвращаемая макросом вычисляется согласно обычным правилам

**функции**

**`print`** - вывести значение переменной
**`scan`** - считать значение переменной

**функции-операторы (в общем значении) тоже являются функциями**

- арифметические
    - **`+`**
    - **`-`**
    - **`mod`**, **`rem`**
- сравнения (только числа? можно только числа, пожалуйста)
    - **`> ≥`**
    - **`=`**

**special operators (standard control structs)**

**`progn`** позволяет вычислить несколько форм, возвращает значение последней формы

**`setq`** выражение присвоения. присваевет значение формы именованной переменной

**`if`**  в качестве условия принимается форма, если он вычисляема и ее значение не **`NIL`** , то вычисляется then-form, в противном случае else-form. с использованием макросов можно создать оператор **`when`**, который позволяет использовать вычислять несколько форм в случае true или false.

**`loop`** - цикл, работает пока не достигнут **`return`** (в реальности loop является макросом и реализован довольно [сложно](https://sourceforge.net/p/clisp/clisp/ci/default/tree/src/loop.lisp))

# Модель процессора
![Схема](https://github.com/danANDla/lispMachine/blob/master/schemes/lispMachine.jpg?raw=true)

Красным цевтом обозначаются управляющие сигналы

# Апробация

- Работу программ hello, cat, prob2 можно посмотреть в [файлах](https://github.com/danANDla/lispMachine/tree/master/golden), сформированных pytest golden tests.
- В [lispProgram](https://github.com/danANDla/lispMachine/tree/master/lispPrograms) содержатся все программы, которые использовались для отдельной проверки функций и конструкций. В этих программах указано небольшое описание, использованных языковых коонструкций, и конечное состояние буффера вывода.

Пример работы транслятора:
```
❯ cat lispPrograms/hello
(setq a "hello")
(print a)

❯ python3 translator.py lispPrograms/hello out

❯ cat out
[
    {
        "opcode": "load",
        "arg": 0,
        "mem": 0
    },
    {
        "opcode": "store",
        "arg": 999,
        "mem": 1
    },
    {
        "opcode": "load",
        "arg": 111,
        "mem": 0
    },
    {
        "opcode": "store",
        "arg": 998,
        "mem": 1
    },
    {
        "opcode": "load",
        "arg": 108,
        "mem": 0
    },
    {
        "opcode": "store",
        "arg": 997,
        "mem": 1
    },
    {
        "opcode": "load",
        "arg": 108,
        "mem": 0
    },
    {
        "opcode": "store",
        "arg": 996,
        "mem": 1
    },
    {
        "opcode": "load",
        "arg": 101,
        "mem": 0
    },
    {
        "opcode": "store",
        "arg": 995,
        "mem": 1
    },
    {
        "opcode": "load",
        "arg": 104,
        "mem": 0
    },
    {
        "opcode": "store",
        "arg": 994,
        "mem": 1
    },
    {
        "opcode": "load",
        "arg": 994,
        "mem": 0
    },
    {
        "opcode": "store",
        "arg": 100,
        "mem": 1
    },
    {
        "opcode": "load",
        "arg": 100,
        "mem": 2
    },
    {
        "opcode": "print",
        "arg": "",
        "mem": 0
    },
    {
        "opcode": "load",
        "arg": 100,
        "mem": 1
    },
    {
        "opcode": "add",
        "arg": 1,
        "mem": 0
    },
    {
        "opcode": "store",
        "arg": 100,
        "mem": 1
    },
    {
        "opcode": "load",
        "arg": 100,
        "mem": 2
    },
    {
        "opcode": "cmp",
        "arg": 0,
        "mem": 0
    },
    {
        "opcode": "je",
        "arg": 2,
        "mem": 3
    },
    {
        "opcode": "jmp",
        "arg": -8,
        "mem": 3
    },
    {
        "opcode": "hlt",
        "arg": "",
        "mem": 0
    }
]

```

Пример работы модели:
```
❯ python3 machine.py out input
DEBUG:root:{TICK: 0, PC: 0, ADDR: 0, OUT: 0, ACC: 0, ZF|SF: 00} load 0
DEBUG:root:{TICK: 2, PC: 1, ADDR: 0, OUT: 0, ACC: 0, ZF|SF: 00} store 999 addr
DEBUG:root:{TICK: 4, PC: 2, ADDR: 999, OUT: 0, ACC: 0, ZF|SF: 00} load 111
DEBUG:root:{TICK: 6, PC: 3, ADDR: 999, OUT: 0, ACC: 111, ZF|SF: 00} store 998 addr
DEBUG:root:{TICK: 8, PC: 4, ADDR: 998, OUT: 111, ACC: 111, ZF|SF: 00} load 108
DEBUG:root:{TICK: 10, PC: 5, ADDR: 998, OUT: 111, ACC: 108, ZF|SF: 00} store 997 addr
DEBUG:root:{TICK: 12, PC: 6, ADDR: 997, OUT: 108, ACC: 108, ZF|SF: 00} load 108
DEBUG:root:{TICK: 14, PC: 7, ADDR: 997, OUT: 108, ACC: 108, ZF|SF: 00} store 996 addr
DEBUG:root:{TICK: 16, PC: 8, ADDR: 996, OUT: 108, ACC: 108, ZF|SF: 00} load 101
DEBUG:root:{TICK: 18, PC: 9, ADDR: 996, OUT: 108, ACC: 101, ZF|SF: 00} store 995 addr
DEBUG:root:{TICK: 20, PC: 10, ADDR: 995, OUT: 101, ACC: 101, ZF|SF: 00} load 104
DEBUG:root:{TICK: 22, PC: 11, ADDR: 995, OUT: 101, ACC: 104, ZF|SF: 00} store 994 addr
DEBUG:root:{TICK: 24, PC: 12, ADDR: 994, OUT: 104, ACC: 104, ZF|SF: 00} load 994
DEBUG:root:{TICK: 26, PC: 13, ADDR: 994, OUT: 104, ACC: 994, ZF|SF: 00} store 100 addr
DEBUG:root:{TICK: 28, PC: 14, ADDR: 100, OUT: 994, ACC: 994, ZF|SF: 00} load 100 indirect addr
DEBUG:root:{TICK: 30, PC: 15, ADDR: 994, OUT: 104, ACC: 104, ZF|SF: 00} print
DEBUG:root:{TICK: 31, PC: 16, ADDR: 994, OUT: 104, ACC: 104, ZF|SF: 00} load 100 addr
DEBUG:root:{TICK: 33, PC: 17, ADDR: 100, OUT: 994, ACC: 994, ZF|SF: 00} add 1
DEBUG:root:{TICK: 35, PC: 18, ADDR: 100, OUT: 994, ACC: 995, ZF|SF: 00} store 100 addr
DEBUG:root:{TICK: 37, PC: 19, ADDR: 100, OUT: 995, ACC: 995, ZF|SF: 00} load 100 indirect addr
DEBUG:root:{TICK: 39, PC: 20, ADDR: 995, OUT: 101, ACC: 101, ZF|SF: 00} cmp 0
DEBUG:root:{TICK: 40, PC: 21, ADDR: 995, OUT: 101, ACC: 101, ZF|SF: 00} je 2 relative addr
DEBUG:root:{TICK: 41, PC: 22, ADDR: 995, OUT: 101, ACC: 101, ZF|SF: 00} jmp -8 relative addr
DEBUG:root:{TICK: 44, PC: 14, ADDR: 995, OUT: 101, ACC: 14, ZF|SF: 00} load 100 indirect addr
DEBUG:root:{TICK: 46, PC: 15, ADDR: 995, OUT: 101, ACC: 101, ZF|SF: 00} print
DEBUG:root:{TICK: 47, PC: 16, ADDR: 995, OUT: 101, ACC: 101, ZF|SF: 00} load 100 addr
DEBUG:root:{TICK: 49, PC: 17, ADDR: 100, OUT: 995, ACC: 995, ZF|SF: 00} add 1
DEBUG:root:{TICK: 51, PC: 18, ADDR: 100, OUT: 995, ACC: 996, ZF|SF: 00} store 100 addr
DEBUG:root:{TICK: 53, PC: 19, ADDR: 100, OUT: 996, ACC: 996, ZF|SF: 00} load 100 indirect addr
DEBUG:root:{TICK: 55, PC: 20, ADDR: 996, OUT: 108, ACC: 108, ZF|SF: 00} cmp 0
DEBUG:root:{TICK: 56, PC: 21, ADDR: 996, OUT: 108, ACC: 108, ZF|SF: 00} je 2 relative addr
DEBUG:root:{TICK: 57, PC: 22, ADDR: 996, OUT: 108, ACC: 108, ZF|SF: 00} jmp -8 relative addr
DEBUG:root:{TICK: 60, PC: 14, ADDR: 996, OUT: 108, ACC: 14, ZF|SF: 00} load 100 indirect addr
DEBUG:root:{TICK: 62, PC: 15, ADDR: 996, OUT: 108, ACC: 108, ZF|SF: 00} print
DEBUG:root:{TICK: 63, PC: 16, ADDR: 996, OUT: 108, ACC: 108, ZF|SF: 00} load 100 addr
DEBUG:root:{TICK: 65, PC: 17, ADDR: 100, OUT: 996, ACC: 996, ZF|SF: 00} add 1
DEBUG:root:{TICK: 67, PC: 18, ADDR: 100, OUT: 996, ACC: 997, ZF|SF: 00} store 100 addr
DEBUG:root:{TICK: 69, PC: 19, ADDR: 100, OUT: 997, ACC: 997, ZF|SF: 00} load 100 indirect addr
DEBUG:root:{TICK: 71, PC: 20, ADDR: 997, OUT: 108, ACC: 108, ZF|SF: 00} cmp 0
DEBUG:root:{TICK: 72, PC: 21, ADDR: 997, OUT: 108, ACC: 108, ZF|SF: 00} je 2 relative addr
DEBUG:root:{TICK: 73, PC: 22, ADDR: 997, OUT: 108, ACC: 108, ZF|SF: 00} jmp -8 relative addr
DEBUG:root:{TICK: 76, PC: 14, ADDR: 997, OUT: 108, ACC: 14, ZF|SF: 00} load 100 indirect addr
DEBUG:root:{TICK: 78, PC: 15, ADDR: 997, OUT: 108, ACC: 108, ZF|SF: 00} print
DEBUG:root:{TICK: 79, PC: 16, ADDR: 997, OUT: 108, ACC: 108, ZF|SF: 00} load 100 addr
DEBUG:root:{TICK: 81, PC: 17, ADDR: 100, OUT: 997, ACC: 997, ZF|SF: 00} add 1
DEBUG:root:{TICK: 83, PC: 18, ADDR: 100, OUT: 997, ACC: 998, ZF|SF: 00} store 100 addr
DEBUG:root:{TICK: 85, PC: 19, ADDR: 100, OUT: 998, ACC: 998, ZF|SF: 00} load 100 indirect addr
DEBUG:root:{TICK: 87, PC: 20, ADDR: 998, OUT: 111, ACC: 111, ZF|SF: 00} cmp 0
DEBUG:root:{TICK: 88, PC: 21, ADDR: 998, OUT: 111, ACC: 111, ZF|SF: 00} je 2 relative addr
DEBUG:root:{TICK: 89, PC: 22, ADDR: 998, OUT: 111, ACC: 111, ZF|SF: 00} jmp -8 relative addr
DEBUG:root:{TICK: 92, PC: 14, ADDR: 998, OUT: 111, ACC: 14, ZF|SF: 00} load 100 indirect addr
DEBUG:root:{TICK: 94, PC: 15, ADDR: 998, OUT: 111, ACC: 111, ZF|SF: 00} print
DEBUG:root:{TICK: 95, PC: 16, ADDR: 998, OUT: 111, ACC: 111, ZF|SF: 00} load 100 addr
DEBUG:root:{TICK: 97, PC: 17, ADDR: 100, OUT: 998, ACC: 998, ZF|SF: 00} add 1
DEBUG:root:{TICK: 99, PC: 18, ADDR: 100, OUT: 998, ACC: 999, ZF|SF: 00} store 100 addr
DEBUG:root:{TICK: 101, PC: 19, ADDR: 100, OUT: 999, ACC: 999, ZF|SF: 00} load 100 indirect addr
DEBUG:root:{TICK: 103, PC: 20, ADDR: 999, OUT: 0, ACC: 0, ZF|SF: 00} cmp 0
DEBUG:root:{TICK: 104, PC: 21, ADDR: 999, OUT: 0, ACC: 0, ZF|SF: 10} je 2 relative addr
DEBUG:root:{TICK: 107, PC: 23, ADDR: 999, OUT: 0, ACC: 23, ZF|SF: 10} hlt
INFO:root:output_buffer: 'hello'
hello
instr_counter:  58 ticks: 107
```

CI:
Взят из примера.

| ФИО | алг. | LoC (в строках) | code байт | code инстр | инстр. | такт. | вариант |
| :---| :---| :---| :---| :---| :---| :---| :---| 
| Алексеев Д.И.| hello| 0| -| 0| 0| 0| lisp | 
| Алексеев Д.И.| cat| 0| -| 0| 0| 0| lisp | 
| Алексеев Д.И.| prob2| 0| -| 0| 0 | 0| lisp | 
