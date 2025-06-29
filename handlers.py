from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import add_stars, activate_subscription, is_subscription_active
from payments import generate_payment_link

@Client.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(
        "Добро пожаловать в Gifts Buyer! "
        "Пополните звёзды и оформите подписку для приоритетного доступа к подаркам."
    )

@Client.on_message(filters.command("topup"))
async def topup(client, message):
    buttons = [
        [InlineKeyboardButton("100 ⭐", callback_data="topup_100"),
         InlineKeyboardButton("300 ⭐", callback_data="topup_300")],
        [InlineKeyboardButton("500 ⭐", callback_data="topup_500"),
         InlineKeyboardButton("1000 ⭐", callback_data="topup_1000")],
        [InlineKeyboardButton("1500 ⭐", callback_data="topup_1500"),
         InlineKeyboardButton("2000 ⭐", callback_data="topup_2000")],
        [InlineKeyboardButton("3500 ⭐", callback_data="topup_3500"),
         InlineKeyboardButton("5000 ⭐", callback_data="topup_5000")],
        [InlineKeyboardButton("10000 ⭐", callback_data="topup_10000"),
         InlineKeyboardButton("15000 ⭐", callback_data="topup_15000")],
        [InlineKeyboardButton("20000 ⭐", callback_data="topup_20000"),
         InlineKeyboardButton("30000 ⭐", callback_data="topup_30000")]
    ]
    await message.reply("Выберите количество звёзд для пополнения:", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"topup_\d+"))
async def process_topup(client, callback_query):
    amount = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id
    payment_link = generate_payment_link(user_id, amount)
    await callback_query.answer()
    await callback_query.message.edit(f"Перейдите по ссылке для оплаты {amount} звёзд:\n{payment_link}")

@Client.on_message(filters.command("subscribe"))
async def subscribe(client, message):
    user_id = message.from_user.id
    price = 59.0
    payment_link = generate_payment_link(user_id, price, subscription=True)
    await message.reply(f"Подписка стоит {price} рублей. Оплатите по ссылке:\n{payment_link}")
