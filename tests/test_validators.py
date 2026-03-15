"""
Тесты валидаторов.
"""
import pytest
from handlers.utils import InputValidator, format_number, format_time_delta, truncate_text


class TestInputValidator:
    """Тесты валидатора ввода"""
    
    def test_validate_int_valid(self):
        """Тест валидации целого числа"""
        is_valid, value, error = InputValidator.validate_int("42")
        
        assert is_valid is True
        assert value == 42
        assert error == ""
    
    def test_validate_int_invalid(self):
        """Тест валидации нецелого числа"""
        is_valid, value, error = InputValidator.validate_int("not a number")
        
        assert is_valid is False
        assert value is None
        assert "целое число" in error.lower()
    
    def test_validate_int_with_min(self):
        """Тест валидации с минимумом"""
        is_valid, value, error = InputValidator.validate_int("5", min_val=1)
        
        assert is_valid is True
        
        is_valid, value, error = InputValidator.validate_int("0", min_val=1)
        
        assert is_valid is False
    
    def test_validate_int_with_max(self):
        """Тест валидации с максимумом"""
        is_valid, value, error = InputValidator.validate_int("50", max_val=100)
        
        assert is_valid is True
        
        is_valid, value, error = InputValidator.validate_int("150", max_val=100)
        
        assert is_valid is False
    
    def test_validate_int_with_range(self):
        """Тест валидации с диапазоном"""
        is_valid, value, error = InputValidator.validate_int("50", min_val=1, max_val=100)
        
        assert is_valid is True
        assert value == 50
    
    def test_validate_int_negative(self):
        """Тест валидации отрицательного числа"""
        is_valid, value, error = InputValidator.validate_int("-10", allow_negative=True)
        
        assert is_valid is True
        assert value == -10
        
        is_valid, value, error = InputValidator.validate_int("-10", allow_negative=False)
        
        assert is_valid is False
    
    def test_validate_float_valid(self):
        """Тест валидации дробного числа"""
        is_valid, value, error = InputValidator.validate_float("3.14")
        
        assert is_valid is True
        assert abs(value - 3.14) < 0.01
    
    def test_validate_float_negative(self):
        """Тест валидации отрицательного числа"""
        is_valid, value, error = InputValidator.validate_float("-10.5", allow_negative=True)
        
        assert is_valid is True
        assert value == -10.5
        
        is_valid, value, error = InputValidator.validate_float("-10.5", allow_negative=False)
        
        assert is_valid is False
    
    def test_validate_username_valid(self):
        """Тест валидации имени пользователя"""
        is_valid, value, error = InputValidator.validate_username("player123")
        
        assert is_valid is True
        assert value == "player123"
    
    def test_validate_username_with_at(self):
        """Тест валидации имени с @"""
        is_valid, value, error = InputValidator.validate_username("@player123")
        
        assert is_valid is True
        assert value == "player123"
    
    def test_validate_username_empty(self):
        """Тест валидации пустого имени"""
        is_valid, value, error = InputValidator.validate_username("")
        
        assert is_valid is False
    
    def test_validate_username_too_short(self):
        """Тест валидации слишком короткого имени"""
        is_valid, value, error = InputValidator.validate_username("ab")
        
        assert is_valid is False
    
    def test_validate_username_too_long(self):
        """Тест валидации слишком длинного имени"""
        long_name = "a" * 50
        is_valid, value, error = InputValidator.validate_username(long_name)
        
        assert is_valid is False
    
    def test_validate_text_length_valid(self):
        """Тест валидации длины текста"""
        is_valid, value, error = InputValidator.validate_text_length("Hello", max_len=100)
        
        assert is_valid is True
    
    def test_validate_text_length_too_long(self):
        """Тест валидации слишком длинного текста"""
        long_text = "a" * 200
        is_valid, value, error = InputValidator.validate_text_length(long_text, max_len=100)
        
        assert is_valid is False
    
    def test_validate_text_length_empty(self):
        """Тест валидации пустого текста"""
        is_valid, value, error = InputValidator.validate_text_length("", min_len=1)
        
        assert is_valid is False


class TestFormatNumber:
    """Тесты форматирования чисел"""
    
    def test_format_small_number(self):
        """Тест форматирования малого числа"""
        assert format_number(100) == "100"
        assert format_number(999) == "999"
    
    def test_format_thousands(self):
        """Тест форматирования тысяч"""
        assert format_number(1000) == "1 000"
        assert format_number(10000) == "10 000"
    
    def test_format_millions(self):
        """Тест форматирования миллионов"""
        assert "1 000 000" in format_number(1000000)


class TestFormatTimeDelta:
    """Тесты форматирования времени"""
    
    def test_format_seconds(self):
        """Тест форматирования секунд"""
        result = format_time_delta(30)
        assert "30" in result
        assert "сек" in result
    
    def test_format_minutes(self):
        """Тест форматирования минут"""
        result = format_time_delta(300)  # 5 минут
        assert "5" in result
        assert "мин" in result
    
    def test_format_hours(self):
        """Тест форматирования часов"""
        result = format_time_delta(7200)  # 2 часа
        assert "2" in result
        assert "ч" in result
    
    def test_format_days(self):
        """Тест форматирования дней"""
        result = format_time_delta(172800)  # 2 дня
        assert "2" in result
        assert "д" in result
    

class TestTruncateText:
    """Тесты обрезки текста"""
    
    def test_truncate_short_text(self):
        """Тест обрезки короткого текста"""
        text = "Hello"
        result = truncate_text(text, max_len=100)
        
        assert result == text
    
    def test_truncate_long_text(self):
        """Тест обрезки длинного текста"""
        text = "a" * 200
        result = truncate_text(text, max_len=100)
        
        assert len(result) <= 103  # 100 + "..."
        assert result.endswith("...")
    
    def test_truncate_exact_length(self):
        """Тест обрезки точной длины"""
        text = "a" * 100
        result = truncate_text(text, max_len=100)
        
        assert result == text

