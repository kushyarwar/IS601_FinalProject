"""
Unit tests for calculator operations, auth utilities, and report logic.
"""
import pytest
from app.calculator import CalculationFactory, OperationType, DivideOperation, ModulusOperation
from app.auth import hash_password, verify_password
from app.jwt_utils import create_token, decode_token
from app.schemas import PasswordChange, CalculationCreate


# ── Calculator unit tests ──────────────────────────────────────────────────

class TestCalculatorOperations:
    def test_add(self):
        assert CalculationFactory.compute(OperationType.Add, 10, 5) == 15

    def test_subtract(self):
        assert CalculationFactory.compute(OperationType.Sub, 10, 5) == 5

    def test_multiply(self):
        assert CalculationFactory.compute(OperationType.Multiply, 6, 7) == 42

    def test_divide(self):
        assert CalculationFactory.compute(OperationType.Divide, 15, 3) == 5

    def test_power(self):
        assert CalculationFactory.compute(OperationType.Power, 2, 10) == 1024

    def test_power_zero_exponent(self):
        assert CalculationFactory.compute(OperationType.Power, 5, 0) == 1

    def test_power_negative_exponent(self):
        result = CalculationFactory.compute(OperationType.Power, 2, -1)
        assert result == pytest.approx(0.5)

    def test_modulus(self):
        assert CalculationFactory.compute(OperationType.Modulus, 10, 3) == 1

    def test_modulus_exact_division(self):
        assert CalculationFactory.compute(OperationType.Modulus, 9, 3) == 0

    def test_divide_by_zero_raises(self):
        with pytest.raises(ValueError, match="Division by zero"):
            DivideOperation().compute(5, 0)

    def test_modulus_by_zero_raises(self):
        with pytest.raises(ValueError, match="Modulus by zero"):
            ModulusOperation().compute(10, 0)

    def test_unknown_operation_raises(self):
        with pytest.raises(ValueError, match="Unknown operation"):
            CalculationFactory.get_operation("Unknown")

    def test_add_floats(self):
        result = CalculationFactory.compute(OperationType.Add, 1.5, 2.5)
        assert result == pytest.approx(4.0)

    def test_subtract_negative_result(self):
        assert CalculationFactory.compute(OperationType.Sub, 3, 10) == -7

    def test_multiply_by_zero(self):
        assert CalculationFactory.compute(OperationType.Multiply, 999, 0) == 0


# ── Auth unit tests ────────────────────────────────────────────────────────

class TestAuthUtils:
    def test_hash_password_returns_string(self):
        hashed = hash_password("mypassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"

    def test_verify_correct_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("correct_password", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("password123")
        h2 = hash_password("password123")
        assert h1 != h2


# ── JWT unit tests ─────────────────────────────────────────────────────────

class TestJwtUtils:
    def test_token_has_three_parts(self):
        token = create_token(1, "user@example.com")
        assert len(token.split(".")) == 3

    def test_decode_returns_correct_sub(self):
        token = create_token(42, "user@example.com")
        payload = decode_token(token)
        assert payload["sub"] == "42"

    def test_decode_returns_correct_email(self):
        token = create_token(1, "test@example.com")
        payload = decode_token(token)
        assert payload["email"] == "test@example.com"

    def test_invalid_token_raises(self):
        with pytest.raises(ValueError):
            decode_token("not.a.valid.token")

    def test_tampered_token_raises(self):
        token = create_token(1, "user@example.com")
        tampered = token[:-4] + "XXXX"
        with pytest.raises(ValueError):
            decode_token(tampered)


# ── Schema validation unit tests ───────────────────────────────────────────

class TestSchemaValidation:
    def test_password_change_same_password_raises(self):
        with pytest.raises(ValueError):
            PasswordChange(current_password="same123", new_password="same123")

    def test_password_change_different_passwords_ok(self):
        pc = PasswordChange(current_password="old_pass123", new_password="new_pass123")
        assert pc.new_password == "new_pass123"

    def test_calculation_create_divide_by_zero_raises(self):
        with pytest.raises(ValueError):
            CalculationCreate(a=5, b=0, type=OperationType.Divide)

    def test_calculation_create_modulus_by_zero_raises(self):
        with pytest.raises(ValueError):
            CalculationCreate(a=5, b=0, type=OperationType.Modulus)

    def test_calculation_create_valid(self):
        c = CalculationCreate(a=10, b=3, type=OperationType.Power)
        assert c.a == 10
        assert c.b == 3
