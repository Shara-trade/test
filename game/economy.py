"""
3.16. Экономика и валюты
Система валют и экономического баланса
"""
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


class Currency(Enum):
    """Типы валют"""
    METAL = "metal"
    CRYSTALS = "crystals"
    DARK_MATTER = "dark_matter"
    CREDITS = "credits"
    QUANTUM_TOKENS = "quantum_tokens"
    TECH_TOKENS = "tech_tokens"


@dataclass
class CurrencyInfo:
    """Информация о валюте"""
    key: str
    name: str
    emoji: str
    description: str
    is_premium: bool = False
    max_value: int = 2_147_483_647  # INT max


class EconomySystem:
    """Система экономики"""
    
    # Информация о валютах
    CURRENCIES = {
        Currency.METAL: CurrencyInfo(
            key="metal",
            name="Металл",
            emoji="⚙️",
            description="Основной ресурс для крафта и улучшений"
        ),
        Currency.CRYSTALS: CurrencyInfo(
            key="crystals",
            name="Кристаллы",
            emoji="💎",
            description="Редкий ресурс для продвинутых улучшений"
        ),
        Currency.DARK_MATTER: CurrencyInfo(
            key="dark_matter",
            name="Тёмная материя",
            emoji="⚫",
            description="Легендарный ресурс для топовых предметов"
        ),
        Currency.CREDITS: CurrencyInfo(
            key="credits",
            name="Кредиты",
            emoji="💰",
            description="Валюта для торговли между игроками"
        ),
        Currency.QUANTUM_TOKENS: CurrencyInfo(
            key="quantum_tokens",
            name="Квант-токены",
            emoji="💠",
            description="Премиум валюта, покупается за донат",
            is_premium=True
        ),
        Currency.TECH_TOKENS: CurrencyInfo(
            key="tech_tokens",
            name="Tech-токены",
            emoji="🔬",
            description="Получаются при престиже, не сбрасываются"
        )
    }
    
    # Курсы конвертации (в кредиты)
    EXCHANGE_RATES = {
        Currency.METAL: 0.1,           # 10 металла = 1 кредит
        Currency.CRYSTALS: 5.0,        # 1 кристалл = 5 кредитов
        Currency.DARK_MATTER: 100.0,   # 1 тёмная материя = 100 кредитов
    }
    
    # Комиссия рынка
    MARKET_COMMISSION = 0.05  # 5%
    
    # Стартовые ресурсы
    STARTER_RESOURCES = {
        "metal": 0,
        "crystals": 0,
        "dark_matter": 0,
        "energy": 1000,
        "max_energy": 1000,
        "credits": 1000,
        "quantum_tokens": 0
    }
    
    @staticmethod
    def get_currency_info(currency: Currency) -> CurrencyInfo:
        """Получить информацию о валюте"""
        return EconomySystem.CURRENCIES.get(currency)
    
    @staticmethod
    def convert_to_credits(currency: Currency, amount: int) -> int:
        """Конвертировать валюту в кредиты"""
        rate = EconomySystem.EXCHANGE_RATES.get(currency, 0)
        return int(amount * rate)
    
    @staticmethod
    def calculate_market_fee(price: int) -> int:
        """Рассчитать комиссию рынка"""
        return int(price * EconomySystem.MARKET_COMMISSION)
    
    @staticmethod
    def calculate_market_revenue(price: int) -> int:
        """Рассчитать доход продавца"""
        fee = EconomySystem.calculate_market_fee(price)
        return price - fee
    
    @staticmethod
    def can_afford(user_resources: Dict, cost: Dict) -> bool:
        """Проверить, может ли игрок позволить себе покупку"""
        for key, required in cost.items():
            current = user_resources.get(key, 0)
            if current < required:
                return False
        return True
    
    @staticmethod
    def calculate_purchase_result(user_resources: Dict, cost: Dict) -> Dict:
        """Рассчитать результат покупки"""
        result = {}
        for key in set(user_resources.keys()) | set(cost.keys()):
            current = user_resources.get(key, 0)
            spent = cost.get(key, 0)
            result[key] = current - spent
        return result
    
    @staticmethod
    def format_amount(amount: int) -> str:
        """Форматировать число для отображения"""
        if amount >= 1_000_000_000:
            return f"{amount / 1_000_000_000:.1f}B"
        elif amount >= 1_000_000:
            return f"{amount / 1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"{amount / 1_000:.1f}K"
        else:
            return str(amount)
    
    @staticmethod
    def format_resources(resources: Dict) -> str:
        """Форматировать ресурсы для отображения"""
        lines = []
        
        currency_order = [
            (Currency.METAL, "metal"),
            (Currency.CRYSTALS, "crystals"),
            (Currency.DARK_MATTER, "dark_matter"),
            (Currency.CREDITS, "credits"),
            (Currency.QUANTUM_TOKENS, "quantum_tokens"),
        ]
        
        for currency, key in currency_order:
            if key in resources:
                info = EconomySystem.get_currency_info(currency)
                amount = resources[key]
                formatted = EconomySystem.format_amount(amount)
                lines.append(f"{info.emoji} {info.name}: {formatted}")
        
        return "\n".join(lines)


@dataclass
class Price:
    """Цена предмета/улучшения"""
    metal: int = 0
    crystals: int = 0
    dark_matter: int = 0
    credits: int = 0
    quantum_tokens: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "metal": self.metal,
            "crystals": self.crystals,
            "dark_matter": self.dark_matter,
            "credits": self.credits,
            "quantum_tokens": self.quantum_tokens
        }
    
    def total_in_credits(self) -> int:
        """Общая стоимость в кредитах"""
        total = EconomySystem.convert_to_credits(Currency.METAL, self.metal)
        total += EconomySystem.convert_to_credits(Currency.CRYSTALS, self.crystals)
        total += EconomySystem.convert_to_credits(Currency.DARK_MATTER, self.dark_matter)
        total += self.credits
        total += self.quantum_tokens * 100  # Условный курс
        return total
    
    def __mul__(self, multiplier: int) -> "Price":
        return Price(
            metal=self.metal * multiplier,
            crystals=self.crystals * multiplier,
            dark_matter=self.dark_matter * multiplier,
            credits=self.credits * multiplier,
            quantum_tokens=self.quantum_tokens * multiplier
        )
    
    def __add__(self, other: "Price") -> "Price":
        return Price(
            metal=self.metal + other.metal,
            crystals=self.crystals + other.crystals,
            dark_matter=self.dark_matter + other.dark_matter,
            credits=self.credits + other.credits,
            quantum_tokens=self.quantum_tokens + other.quantum_tokens
        )


@dataclass
class Transaction:
    """Транзакция"""
    transaction_id: int
    from_user: Optional[int]  # None = система
    to_user: Optional[int]    # None = система
    transaction_type: str     # purchase, sale, gift, reward
    items: Dict[str, int]     # item_key: quantity
    currencies: Dict[str, int]  # валюта: количество
    timestamp: str
    
    TRANSACTION_TYPES = [
        "purchase",      # Покупка на рынке
        "sale",          # Продажа на рынке
        "craft",         # Крафт предмета
        "reward",        # Награда от системы
        "gift",          # Передача между игроками
        "admin_grant",   # Выдача админом
        "prestige"       # Сброс при престиже
    ]
