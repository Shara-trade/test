from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard():
 keyboard = [
 [
 KeyboardButton(text='⛏ Шахта'),
 KeyboardButton(text='🚀 Ангар'),
 KeyboardButton(text='📦 Инвентарь')
 ],
 [
 KeyboardButton(text='⚙️ Модули'),
 KeyboardButton(text='🏪 Рынок'),
 KeyboardButton(text='🔨 Крафт')
 ],
 [
 KeyboardButton(text='👥 Клан'),
 KeyboardButton(text='🌌 Галактика'),
 KeyboardButton(text='👤 Профиль')
 ],
 [
 KeyboardButton(text='📊 Топ'),
 KeyboardButton(text='❓ Помощь')
 ]
 ]
 return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, persistent=True)


def get_start_welcome_keyboard():
 keyboard = [
 [
 InlineKeyboardButton(text='👤 Профиль', callback_data='profile'),
 InlineKeyboardButton(text='📊 Топ', callback_data='top'),
 InlineKeyboardButton(text='📖 Гайд', callback_data='guide')
 ],
 [
 InlineKeyboardButton(text='⚡ Начать игру', callback_data='start_game')
 ]
 ]
 return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_start_return_keyboard():
 keyboard = [
 [
 InlineKeyboardButton(text='⛏ Шахта', callback_data='mine'),
 InlineKeyboardButton(text='🚀 Ангар', callback_data='drones'),
 InlineKeyboardButton(text='📦 Инвент', callback_data='inventory')
 ],
 [
 InlineKeyboardButton(text='🏪 Рынок', callback_data='market'),
 InlineKeyboardButton(text='🔨 Крафт', callback_data='craft'),
 InlineKeyboardButton(text='👥 Клан', callback_data='clan')
 ]
 ]
 return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_mine_keyboard():
 keyboard = [
 [
 InlineKeyboardButton(text='⛏ ДОБЫТЬ АСТЕРОИД', callback_data='mine_click')
 ],
 [
 InlineKeyboardButton(text='📦 Контейнеры', callback_data='containers'),
 InlineKeyboardButton(text='⚡ Купить энергию', callback_data='buy_energy')
 ],
 [
 InlineKeyboardButton(text='🤖 Дроны', callback_data='drones'),
 InlineKeyboardButton(text='⚙️ Модули', callback_data='modules'),
 InlineKeyboardButton(text='💰 Крафт', callback_data='craft_mine')
 ],
 [
 InlineKeyboardButton(text='🔄 Обновить', callback_data='refresh_mine'),
 InlineKeyboardButton(text='📊 Статистика', callback_data='stats'),
 InlineKeyboardButton(text='◀️ В меню', callback_data='main_menu')
 ]
 ]
 return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_buy_energy_keyboard():
 keyboard = [
 [
 InlineKeyboardButton(text='100 [50 металла]', callback_data='buy_energy_100'),
 InlineKeyboardButton(text='500 [200 металла]', callback_data='buy_energy_500'),
 InlineKeyboardButton(text='1000 [350 металла]', callback_data='buy_energy_1000')
 ],
 [
 InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_mine')
 ]
 ]
 return InlineKeyboardMarkup(inline_keyboard=keyboard)
