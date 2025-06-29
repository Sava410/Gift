from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from peewee import *
import os

# --- Настройки ---
API_ID = 29809992
API_HASH = "81e8cc2932d652f2ca7c4576cc0bd500"
BOT_TOKEN = "7749886683:AAGlPYtsMOTUTulH496s5vO9vsLpovSUIBo"

ADMIN_ID = "@Pepe_abmin1"  # <-- замени на свой ID

# --- База данных ---
db = SqliteDatabase("stars.db")

class User(Model):
    user_id = IntegerField(unique=True)
    stars = IntegerField(default=0)

    class Meta:
        database = db

db.connect()
db.create_tables([User], safe=True)

# --- Помощники по БД ---
def add_user_if_not_exists(user_id):
    user, created = User.get_or_create(user_id=user_id)
    if created:
        user.stars = 0
        user.save()

def get_stars(user_id):
    user = User.get_or_none(User.user_id == user_id)
    return user.stars if user else 0

def add_stars(user_id, amount):
    user = User.get_or_none(User.user_id == user_id)
    if not user:
        user = User.create(user_id=user_id, stars=0)
    user.stars += amount
    user.save()

def spend_stars(user_id, amount):
    user = User.get_or_none(User.user_id == user_id)
    if user and user.stars >= amount:
        user.stars -= amount
        user.save()
        return True
    return False

# --- Инициализация бота ---
app = Client("gift_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Кнопки ---
stars_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("Пополнить 100 ⭐", callback_data="add_100"),
     InlineKeyboardButton("Списать 100 ⭐", callback_data="spend_100")],
    [InlineKeyboardButton("Пополнить 300 ⭐", callback_data="add_300"),
     InlineKeyboardButton("Списать 300 ⭐", callback_data="spend_300")],
    [InlineKeyboardButton("Пополнить 500 ⭐", callback_data="add_500"),
     InlineKeyboardButton("Списать 500 ⭐", callback_data="spend_500")],
    [InlineKeyboardButton("Пополнить 1000 ⭐", callback_data="add_1000"),
     InlineKeyboardButton("Списать 1000 ⭐", callback_data="spend_1000")],
])

# --- Словарь для pending списаний ---
pending_spends = {}

# --- Команда /stars показать баланс и меню ---
@app.on_message(filters.command("stars") & filters.private)
async def stars_menu(client, message):
    user_id = message.from_user.id
    add_user_if_not_exists(user_id)
    stars = get_stars(user_id)
    await message.reply_text(
        f"Ваш баланс: {stars} ⭐.\nВыберите действие:",
        reply_markup=stars_keyboard
    )

# --- Обработка кнопок пополнения и списания ---
@app.on_callback_query(filters.regex(r"add_\d+|spend_\d+"))
async def handle_stars_buttons(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    amount = int(data.split("_")[1])

    add_user_if_not_exists(user_id)
    stars = get_stars(user_id)

    if data.startswith("add_"):
        add_stars(user_id, amount)
        stars = get_stars(user_id)
        await callback_query.answer(f"Добавлено {amount} ⭐!")
        await callback_query.message.edit_text(f"Ваш баланс: {stars} ⭐", reply_markup=stars_keyboard)

    elif data.startswith("spend_"):
        if stars < amount:
            await callback_query.answer("Недостаточно звезд для списания!", show_alert=True)
            return
        # Запрашиваем подтверждение
        pending_spends[user_id] = amount
        await callback_query.answer()
        await callback_query.message.reply_text(
            f"Вы запросили списание {amount} ⭐.\n"
            "Пожалуйста, отправьте скриншот или сообщение с подтверждением списания звезд в Telegram.\n"
            "После проверки администратором звезды будут списаны."
        )

# --- Обработка подтверждения списания от пользователя ---
@app.on_message(filters.private & (filters.photo | filters.text))
async def handle_confirmation(client, message):
    user_id = message.from_user.id
    if user_id in pending_spends:
        amount = pending_spends[user_id]
        # Отправляем админу сообщение с подтверждением
        admin_msg = f"Пользователь @{message.from_user.username or user_id} запрашивает списание {amount} ⭐.\n"
        admin_msg += f"Подтверждение:\n"
        if message.photo:
            admin_msg += "(Фото отправлено)"
            await message.photo[-1].download(f"confirm_{user_id}.jpg")  # сохраним локально для админа
        else:
            admin_msg += message.text or "без текста"
        await client.send_message(ADMIN_ID, admin_msg + f"\nИспользуйте /approve_spend {user_id} или /deny_spend {user_id}")
        await message.reply("Ваш запрос отправлен администратору. Ожидайте подтверждения.")
        del pending_spends[user_id]

# --- Команда админа подтвердить списание ---
@app.on_message(filters.user(ADMIN_ID) & filters.command("approve_spend"))
async def approve_spend(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Использование: /approve_spend user_id")
        return
    try:
        user_id = int(args[1])
    except ValueError:
        await message.reply("Неверный user_id")
        return
    amount = None
    # Находим pending запрос (если был)
    # Для упрощения: просто списываем amount, который последний сохранили (лучше сделать БД для запросов)
    if user_id in pending_spends:
        amount = pending_spends[user_id]
        del pending_spends[user_id]
    else:
        await message.reply("Нет ожидающих запросов на списание у этого пользователя.")
        return

    if spend_stars(user_id, amount):
        await message.reply(f"Списано {amount} ⭐ у пользователя {user_id}.")
        await client.send_message(user_id, f"Ваше списание {amount} ⭐ подтверждено администратором.")
    else:
        await message.reply("У пользователя недостаточно звезд для списания.")

# --- Команда админа отклонить списание ---
@app.on_message(filters.user(ADMIN_ID) & filters.command("deny_spend"))
async def deny_spend(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Использование: /deny_spend user_id")
        return
    try:
        user_id = int(args[1])
    except ValueError:
        await message.reply("Неверный user_id")
        return
    if user_id in pending_spends:
        del pending_spends[user_id]
        await message.reply(f"Запрос на списание пользователя {user_id} отклонён.")
        await client.send_message(user_id, "Ваш запрос на списание звезд отклонён администратором.")
    else:
        await message.reply("У пользователя нет ожидающих запросов на списание.")

# --- Команда покупки подарка ---
@app.on_message(filters.command("buy") & filters.private)
async def buy_gift(client, message):
    user_id = message.from_user.id
    add_user_if_not_exists(user_id)

    args = message.text.split()
    if len(args) < 2:
        await message.reply("Использование: /buy <цена_в_звездах>")
        return
    try:
        price = int(args[1])
    except ValueError:
        await message.reply("Цена должна быть числом.")
        return

    stars = get_stars(user_id)
    if stars < price:
        await message.reply(f"Недостаточно звезд для покупки. У вас {stars} ⭐, нужно {price} ⭐.")
        return

    # Списываем звезды
    spend_stars(user_id, price)

    # Здесь логика "выкупа подарка"
    # Например, можно отправить пользователю сообщение с подтверждением
    await message.reply(f"Подарок за {price} ⭐ успешно куплен! Спасибо за покупку 🎁")

# --- Запуск бота ---
print("Бот запущен...")
app.run()
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

gift_price = 1000


@app.on_message(filters.command("start"))
async def start(client, message):
    buttons = [
        [InlineKeyboardButton("Пополнить звёзды", callback_data="show_recharge")],
        [InlineKeyboardButton(f"Выставить подарок ({gift_price}⭐)", callback_data="give_gift")]
    ]
    await message.reply("Выбирай действие:", reply_markup=InlineKeyboardMarkup(buttons))


