def generate_payment_link(user_id, amount, subscription=False):
    # Тут нужно интегрировать CloudPayments или Telegram Payments
    # Пока просто заглушка
    if subscription:
        return f"https://payment.example.com/subscribe?user={user_id}&price={amount}"
    else:
        return f"https://payment.example.com/topup?user={user_id}&stars={amount}"
