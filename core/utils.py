"""
Утилиты для бота
"""
from typing import Union


def format_number(value: Union[int, float]) -> str:
    """
    Форматирование чисел согласно Update.txt.
    
    От 0 до 999,999: обычные цифры с запятой (1,234)
    От 1M: сокращения (1.2M, 845.5M, 2.5B, 3.7T, ...)
    
    Args:
        value: Число для форматирования
    
    Returns:
        Отформатированная строка
    """
    if value is None:
        return "0"
    
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "0"
    
    if value < 0:
        return f"-{format_number(abs(value))}"
    
    if value < 1_000_000:
        # До миллиона - обычные цифры с запятой
        return f"{int(value):,}".replace(",", " ")
    
    # Суффиксы согласно Update.txt
    suffixes = [
        (10**63, "Ce"),   # Centillion
        (10**60, "Nod"),  # Novemdecillion
        (10**57, "Ocd"),  # Octodecillion
        (10**54, "Spd"),  # Septendecillion
        (10**51, "Sxd"),  # Sexdecillion
        (10**48, "Qid"),  # Quindecillion
        (10**45, "Qad"),  # Quattuordecillion
        (10**42, "Td"),   # Tredecillion
        (10**39, "Dd"),   # Duodecillion
        (10**36, "Ud"),   # Undecillion
        (10**33, "Dc"),   # Decillion
        (10**30, "No"),   # Nonillion
        (10**27, "Oc"),   # Octillion
        (10**24, "Sp"),   # Septillion
        (10**21, "Sx"),   # Sextillion
        (10**18, "Qi"),   # Quintillion
        (10**15, "Qa"),   # Quadrillion
        (10**12, "T"),    # Trillion
        (10**9, "B"),     # Billion
        (10**6, "M"),     # Million
    ]
    
    for threshold, suffix in suffixes:
        if value >= threshold:
            formatted = value / threshold
            # Если целое число - без десятичной части
            if formatted == int(formatted):
                return f"{int(formatted)}{suffix}"
            return f"{formatted:.1f}{suffix}"
    
    return f"{int(value):,}".replace(",", " ")


def format_resources(metal: int = 0, crystals: int = 0, dark_matter: int = 0) -> str:
    """
    Форматировать ресурсы для отображения.
    
    Returns:
        Строка с ресурсами
    """
    parts = []
    if metal > 0:
        parts.append(f"⚙️ Металл +{format_number(metal)}")
    if crystals > 0:
        parts.append(f"💎 Кристаллы +{format_number(crystals)}")
    if dark_matter > 0:
        parts.append(f"🕳️ Тёмная материя +{format_number(dark_matter)}")
    return "\n".join(parts)


def plural_form(n: int, form1: str, form2: str, form5: str) -> str:
    """
    Склонение слов по числу.
    
    Пример: plural_form(5, "контейнер", "контейнера", "контейнеров")
    
    Args:
        n: Число
        form1: Форма для 1 (контейнер)
        form2: Форма для 2-4 (контейнера)
        form5: Форма для 5+ (контейнеров)
    
    Returns:
        Правильная форма слова
    """
    n = abs(n) % 100
    n1 = n % 10
    
    if n > 10 and n < 20:
        return form5
    if n1 > 1 and n1 < 5:
        return form2
    if n1 == 1:
        return form1
    
    return form5
