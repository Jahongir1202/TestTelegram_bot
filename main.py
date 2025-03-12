import json
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os



TOKEN = "7826152623:AAGPlVwcScLDOo7LxC_xAUK24M0KSDttODY"
bot = telebot.TeleBot(TOKEN)

TEST_FILE = "test_savollari.json"
USERS_FILE = "users.json"
CERTIFICATE_FILE = "/home/xtreme/PycharmProjects/Weking_tmebot/250697684196070-1.pdf"


def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


test_savollari = load_data(TEST_FILE)
users = load_data(USERS_FILE)


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user = next((u for u in users if u['id'] == chat_id), None)

    if user:
        send_main_menu(chat_id)
        return

    msg = bot.send_message(chat_id, "👋 Assalomu alaykum! Ismingizni va familiyangizni kiriting:")
    bot.register_next_step_handler(msg, get_address)


def get_address(message):
    chat_id = message.chat.id
    name = message.text.strip()
    msg = bot.send_message(chat_id, "🏠 Yashash manzilingizni kiriting:")
    bot.register_next_step_handler(msg, get_school, name)


def get_school(message, name):
    chat_id = message.chat.id
    address = message.text.strip()
    msg = bot.send_message(chat_id, "🏫 Qaysi maktabda o‘qiysiz?")
    bot.register_next_step_handler(msg, get_phone, name, address)


def get_phone(message, name, address):
    chat_id = message.chat.id
    school = message.text.strip()
    msg = bot.send_message(chat_id, "📞 Telefon raqamingizni kiriting:")
    bot.register_next_step_handler(msg, get_age, name, address, school)


def get_age(message, name, address, school):
    chat_id = message.chat.id
    phone = message.text.strip()
    msg = bot.send_message(chat_id, "🎂 Yoshingizni kiriting:")
    bot.register_next_step_handler(msg, check_age, name, address, school, phone)


def check_age(message, name, address, school, phone):
    chat_id = message.chat.id
    try:
        age = int(message.text.strip())
        if age < 5 or age > 16:
            bot.send_message(chat_id, "🚫 Kechirasiz, yoshingiz test uchun mos emas. Xayr!")
            return
    except ValueError:
        bot.send_message(chat_id, "❌ Iltimos, yoshingizni to'g'ri kiriting!")
        return

    user = {
        "id": chat_id, "name": name, "address": address, "school": school,
        "phone": phone, "age": age, "results": {}, "total_score": 0
    }
    users.append(user)
    save_data(USERS_FILE, users)

    bot.send_message(chat_id, "✅ Ma'lumotlaringiz saqlandi!")
    send_main_menu(chat_id)


def send_main_menu(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("📋 Testni boshlash", callback_data="start_test"),
        InlineKeyboardButton("📊 Mening natijam", callback_data="my_results"),
        InlineKeyboardButton("ℹ️ Men haqimda", callback_data="my_info"),
        InlineKeyboardButton("👥 Do‘stlarni taklif etish", switch_inline_query="Do‘stlarimni bu testga taklif qilaman!"),
        InlineKeyboardButton("🏆 Reyting", callback_data="ranking")
    )
    bot.send_message(chat_id, "👇 Quyidagilardan birini tanlang:", reply_markup=markup)

def show_my_results(chat_id):
    """Foydalanuvchining test natijalarini ko‘rsatish."""
    user = next((u for u in users if u['id'] == chat_id), None)
    if not user:
        bot.send_message(chat_id, "Siz ro'yxatdan o'tmagansiz. Iltimos, /start buyrug'ini bering.")
        return

    if not user['results']:
        bot.send_message(chat_id, "Siz hali testdan o'tmagansiz.")
        return

    results_text = "📊 *Sizning test natijalaringiz:*\n\n"
    for kasb, ball in user['results'].items():
        results_text += f"🔹 {kasb}: {ball} ball\n"

    bot.send_message(chat_id, results_text, parse_mode="Markdown")


def show_my_info(chat_id):
    """Foydalanuvchining shaxsiy ma'lumotlarini ko‘rsatish."""
    user = next((u for u in users if u['id'] == chat_id), None)
    if not user:
        bot.send_message(chat_id, "Iltimos, avval /start buyrug'ini bering va ro'yxatdan o'ting!")
        return

    info = (f"👤 *Ismingiz:* {user['name']}\n"
            f"🏠 *Manzilingiz:* {user['address']}\n"
            f"🏫 *Maktabingiz:* {user['school']}\n"
            f"📞 *Telefon:* {user['phone']}\n"
            f"🎂 *Yoshingiz:* {user['age']}")

    bot.send_message(chat_id, info, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data == "start_test":
        start_test(chat_id)
    elif call.data == "my_results":
        show_my_results(chat_id)
    elif call.data == "my_info":
        show_my_info(chat_id)
    elif call.data == "ranking":
        show_ranking(chat_id)


@bot.message_handler(commands=['test'])
def start_test(chat_id):
    user = next((u for u in users if u['id'] == chat_id), None)
    if not user:
        bot.send_message(chat_id, "Iltimos, avval /start buyrug'ini bering va ro'yxatdan o'ting!")
        return
    user['results'] = {}
    ask_question(chat_id, 0)


def ask_question(chat_id, index):
    if index >= len(test_savollari):
        calculate_results(chat_id)
        return

    question = test_savollari[index]
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for variant in question['variants']:
        markup.add(KeyboardButton(f"{variant['text']} ({variant['kasb']})"))

    msg = bot.send_message(chat_id, question['savol'], reply_markup=markup)
    bot.register_next_step_handler(msg, lambda msg: save_answer(msg, index))


def save_answer(message, index):
    chat_id = message.chat.id
    answer = message.text.strip()
    question = test_savollari[index]

    user = next((u for u in users if u['id'] == chat_id), None)
    if user:
        for variant in question['variants']:
            if answer.startswith(variant['text']):
                kasb = variant['kasb']
                ball = variant['ball']
                user['results'][kasb] = user['results'].get(kasb, 0) + ball
                save_data(USERS_FILE, users)
                break

    ask_question(chat_id, index + 1)


def calculate_results(chat_id):
    user = next((u for u in users if u['id'] == chat_id), None)
    if not user:
        return

    results = user['results']
    if not results:
        bot.send_message(chat_id, "Siz hech qanday savolga javob bermadingiz.")
        send_main_menu(chat_id)  # 🔥 Test natijasidan keyin menyuga qaytish
        return

    top_kasb = max(results, key=results.get)
    total_points = sum(results.values())
    user['total_score'] = total_points
    save_data(USERS_FILE, users)

    bot.send_message(chat_id, f"📋 Sizning kasbingiz: {top_kasb} ({results[top_kasb]} ball)\n🎯 Umumiy ball: {total_points}")

    show_ranking(chat_id)  # 🔥 Reyting ko‘rsatish
    send_main_menu(chat_id)  # 🔥 Test natijasidan keyin menyuga qaytish

    if is_in_top_10(user):
        send_certificate(chat_id, user)


def show_ranking(chat_id):
    sorted_users = sorted(users, key=lambda u: u.get("total_score", 0), reverse=True)
    ranking_text = "🏆 Eng kuchli TOP 10 foydalanuvchilar:\n\n"

    for i, user in enumerate(sorted_users[:10], start=1):
        ranking_text += f"{i}. {user['name']} - {user.get('total_score', 0)} ball\n"

    bot.send_message(chat_id, ranking_text)


def is_in_top_10(user):
    sorted_users = sorted(users, key=lambda u: u.get("total_score", 0), reverse=True)
    return user in sorted_users[:10]


def send_certificate(chat_id, user):
    if os.path.exists(CERTIFICATE_FILE):
        with open(CERTIFICATE_FILE, "rb") as cert:
            bot.send_document(chat_id, cert, caption=f"🎉 Tabriklaymiz, {user['name']}! Siz TOP 10 talikka kirdingiz!")
    else:
        bot.send_message(chat_id, "❌ Sertifikat fayli topilmadi!")


bot.polling(none_stop=True)
