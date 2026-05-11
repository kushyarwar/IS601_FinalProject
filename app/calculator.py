"""
Calculator module implementing the Factory design pattern.

Each operation is its own class so adding a new operation never
requires modifying existing classes — only registering a new one
in CalculationFactory._registry (Open/Closed Principle).
"""
from enum import Enum


class OperationType(str, Enum):
    """Supported arithmetic operation types. Inherits str so values
    serialize directly to/from JSON without extra conversion."""
    Add = "Add"
    Sub = "Sub"
    Multiply = "Multiply"
    Divide = "Divide"
    Power = "Power"
    Modulus = "Modulus"


class AddOperation:
    def compute(self, a: float, b: float) -> float:
        """Return a + b."""
        return a + b


class SubOperation:
    def compute(self, a: float, b: float) -> float:
        """Return a - b."""
        return a - b


class MultiplyOperation:
    def compute(self, a: float, b: float) -> float:
        """Return a * b."""
        return a * b


class DivideOperation:
    def compute(self, a: float, b: float) -> float:
        """Return a / b. Raises ValueError when b is zero."""
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        return a / b


class PowerOperation:
    def compute(self, a: float, b: float) -> float:
        """Return a raised to the power of b (a ** b)."""
        return a ** b


class ModulusOperation:
    def compute(self, a: float, b: float) -> float:
        """Return a % b. Raises ValueError when b is zero."""
        if b == 0:
            raise ValueError("Modulus by zero is not allowed")
        return a % b


class CalculationFactory:
    """Factory that maps OperationType values to their operation classes.

    To add a new operation: create a class with a compute(a, b) method
    and add it to _registry — no other code needs to change.
    """

    _registry = {
        OperationType.Add: AddOperation,
        OperationType.Sub: SubOperation,
        OperationType.Multiply: MultiplyOperation,
        OperationType.Divide: DivideOperation,
        OperationType.Power: PowerOperation,
        OperationType.Modulus: ModulusOperation,
    }

    @classmethod
    def get_operation(cls, op_type: OperationType):
        """Return an instantiated operation object for the given type."""
        operation_class = cls._registry.get(op_type)
        if operation_class is None:
            raise ValueError(f"Unknown operation type: {op_type}")
        return operation_class()

    @classmethod
    def compute(cls, op_type: OperationType, a: float, b: float) -> float:
        """Resolve the operation class and compute the result in one call."""
        return cls.get_operation(op_type).compute(a, b)
