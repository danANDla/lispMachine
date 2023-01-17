class SymbNotFoundException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return (repr(self.value))


class MacrosNameTakenException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return (repr(self.value))


class InvalidFunctionSignatureException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return (repr(self.value))
