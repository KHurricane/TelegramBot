import telebot
from telebot import types
import json
import schedule
import time
from datetime import datetime, timedelta

token = "YOUR TOKEN"
bot = telebot.TeleBot(token)

# Файл для хранения расписания отправки
schedule_file = "channel_schedule.json"

# Список ID каналов
channels = []

# Функция для загрузки расписания из файла
def load_schedule():
    try:
        with open(schedule_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Функция для сохранения расписания в файл
def save_schedule(data):
    with open(schedule_file, "w") as file:
        json.dump(data, file)

# Загружаем расписание при запуске
channel_schedule = load_schedule()

# Создаем меню для создания поста и экспорта участников
@bot.message_handler(commands=['start'])
def start_menu(message):
    global post_text, image_file_id, selected_channel, post_day, post_time
    post_text = None
    image_file_id = None
    selected_channel = None
    post_day = None
    post_time = None

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    create_post_btn = types.KeyboardButton("Создать пост")
    export_members_btn = types.KeyboardButton("Экспортировать участников")
    reset_btn = types.KeyboardButton("Сбросить все команды")
    markup.add(create_post_btn, export_members_btn, reset_btn)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Сбросить все команды")
def reset_bot(message):
    start_menu(message)  # Возвращаемся к начальному меню

@bot.message_handler(func=lambda message: message.text == "Экспортировать участников")
def export_members(message):
    bot.send_message(message.chat.id, "Выберите канал для экспорта участников.")
    show_channel_selection_for_export(message)

def show_channel_selection_for_export(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for channel_id in channels:
        try:
            chat = bot.get_chat(channel_id)
            channel_name = chat.title  # Получаем название канала
            markup.add(types.KeyboardButton(channel_name))
        except Exception as e:
            bot.send_message(message.chat.id, f"Не удалось получить название для канала {channel_id}: {e}")
    markup.add(types.KeyboardButton("Назад"))  # Добавляем кнопку назад
    markup.add(types.KeyboardButton("Сбросить все команды"))  # Добавляем кнопку сброса
    bot.send_message(message.chat.id, "Выберите канал для экспорта участников:", reply_markup=markup)
    bot.register_next_step_handler(message, process_channel_selection_for_export)

def process_channel_selection_for_export(message):
    if message.text == "Сбросить все команды":
        start_menu(message)
        return

    selected_channel_name = message.text
    selected_channel = next((id for id in channels if bot.get_chat(id).title == selected_channel_name), None)

    if selected_channel:
        try:
            members = bot.get_chat_members_count(selected_channel)
            bot.send_message(message.chat.id, f"Количество участников в канале {selected_channel_name}: {members}")
            export_channel_members(selected_channel, message.chat.id)
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка при получении участников канала: {e}")
    else:
        bot.send_message(message.chat.id, "Неверный выбор канала. Попробуйте еще раз.")
        export_members(message)

def export_channel_members(channel_id, chat_id):
    try:
        # Получаем список администраторов канала
        administrators = bot.get_chat_administrators(channel_id)
        member_ids = []

        # Извлекаем информацию о пользователях
        for admin in administrators:
            user = admin.user
            member_ids.append((user.id, user.username or "Не указано", user.first_name or "Не указано"))

        bot.send_message(chat_id, "ID участников канала:\n" + "\n".join([f"{user_id}: {username} ({display_name})" for user_id, username, display_name in member_ids]))

    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при экспорте участников: {e}")

# Остальная часть кода остается без изменений...
# Создание поста и другие функции...

@bot.message_handler(func=lambda message: message.text == "Создать пост")
def create_post(message):
    bot.send_message(message.chat.id, "Отправьте текст поста и/или изображение.")
    bot.register_next_step_handler(message, process_post_content)

def process_post_content(message):
    global post_text, image_file_id
    # Если сообщение содержит изображение
    if message.content_type == 'photo':
        image_file_id = message.photo[-1].file_id  # Получаем ID изображения
        post_text = message.caption if message.caption else ""  # Получаем текст, если он есть
        bot.send_message(message.chat.id, "Выберите канал для поста.")
        show_channel_selection(message)
    # Если сообщение содержит только текст
    elif message.content_type == 'text':
        post_text = message.text
        image_file_id = None  # Не нужно изображение
        bot.send_message(message.chat.id, "Выберите канал для поста.")
        show_channel_selection(message)
    else:
        bot.send_message(message.chat.id, "Неверный ввод. Пожалуйста, введите текст или отправьте изображение.")
        create_post(message)

def show_channel_selection(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for channel_id in channels:
        try:
            chat = bot.get_chat(channel_id)
            channel_name = chat.title  # Получаем название канала
            markup.add(types.KeyboardButton(channel_name))
        except Exception as e:
            bot.send_message(message.chat.id, f"Не удалось получить название для канала {channel_id}: {e}")
    markup.add(types.KeyboardButton("Назад"))  # Добавляем кнопку назад
    markup.add(types.KeyboardButton("Сбросить все команды"))  # Добавляем кнопку сброса
    bot.send_message(message.chat.id, "Выберите канал для поста:", reply_markup=markup)
    bot.register_next_step_handler(message, process_channel_selection)

def process_channel_selection(message):
    global selected_channel
    if message.text == "Сбросить все команды":
        start_menu(message)
        return

    selected_channel = next((id for id in channels if bot.get_chat(id).title == message.text), None)

    if selected_channel:
        bot.send_message(message.chat.id, "Выберите время отправки.", reply_markup=get_time_markup())
    else:
        bot.send_message(message.chat.id, "Неверный выбор канала. Попробуйте еще раз.")
        create_post(message)

def get_time_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    now_btn = types.KeyboardButton("СЕЙЧАС")
    custom_time_btn = types.KeyboardButton("Выбрать свое время (Сегодня, Завтра или введите день)")
    markup.add(now_btn, custom_time_btn)
    markup.add(types.KeyboardButton("Сбросить все команды"))  # Добавляем кнопку сброса
    return markup

@bot.message_handler(func=lambda message: message.text in ["СЕЙЧАС", "Выбрать свое время (Сегодня, Завтра или введите день)"])
def process_time_selection(message):
    if message.text == "Сбросить все команды":
        start_menu(message)
        return

    if message.text == "СЕЙЧАС":
        schedule_post(post_text, selected_channel, image_file_id, "now")
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        today_btn = types.KeyboardButton("Сегодня")
        tomorrow_btn = types.KeyboardButton("Завтра")
        custom_day_btn = types.KeyboardButton("Введите свой день (dd.mm.yyyy)")
        markup.add(today_btn, tomorrow_btn, custom_day_btn)
        markup.add(types.KeyboardButton("Сбросить все команды"))  # Добавляем кнопку сброса
        bot.send_message(message.chat.id, "Выберите день отправки:", reply_markup=markup)
        bot.register_next_step_handler(message, process_day_selection)

def process_day_selection(message):
    global post_day
    if message.text == "Сбросить все команды":
        start_menu(message)
        return

    if message.text == "Сегодня":
        post_day = datetime.now().strftime("%d.%m.%Y")
    elif message.text == "Завтра":
        post_day = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
    elif message.text.startswith("Введите свой день"):
        bot.send_message(message.chat.id, "Введите дату в формате dd.mm.yyyy.")
        bot.register_next_step_handler(message, process_custom_day)
        return
    else:
        bot.send_message(message.chat.id, "Неверный выбор дня. Попробуйте еще раз.")
        process_time_selection(message)

    bot.send_message(message.chat.id, "Введите время в формате HH:MM.")
    bot.register_next_step_handler(message, process_custom_time)

def process_custom_day(message):
    global post_day
    if message.text == "Сбросить все команды":
        start_menu(message)
        return

    try:
        post_day = datetime.strptime(message.text, "%d.%m.%Y").strftime("%d.%m.%Y")
        bot.send_message(message.chat.id, "Введите время в формате HH:MM.")
        bot.register_next_step_handler(message, process_custom_time)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты. Попробуйте еще раз.")
        bot.register_next_step_handler(message, process_custom_day)

def process_custom_time(message):
    global post_time
    if message.text == "Сбросить все команды":
        start_menu(message)
        return

    try:
        post_time = message.text.strip()
        hour, minute = map(int, post_time.split(":"))
        if 0 <= hour < 24 and 0 <= minute < 60:
            full_schedule_time = f"{post_day} {post_time}"
            schedule_post(post_text, selected_channel, image_file_id, full_schedule_time)
        else:
            raise ValueError
    except Exception:
        bot.send_message(message.chat.id, "Неверный формат времени. Попробуйте еще раз.")
        bot.register_next_step_handler(message, process_custom_time)

def schedule_post(message_text, channel_id, image_id, send_time):
    if send_time == "now":
        if image_id:
            bot.send_photo(channel_id, image_id, caption=message_text)
        else:
            bot.send_message(channel_id, message_text)
    else:
        # Сохраняем расписание
        channel_schedule[channel_id] = {"time": send_time, "text": message_text, "image_id": image_id}
        save_schedule(channel_schedule)

        # Настраиваем расписание
        schedule.every().day.at(send_time.split()[1]).do(send_message_to_channel, channel_id=channel_id, message_text=message_text, image_id=image_id)

def send_message_to_channel(channel_id, message_text, image_id):
    try:
        if image_id:
            bot.send_photo(channel_id, image_id, caption=message_text)
        else:
            bot.send_message(channel_id, message_text)
        print(f"Сообщение отправлено в канал {channel_id}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения в канал {channel_id}: {e}")

# Основной цикл для проверки расписания
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

import threading
threading.Thread(target=run_schedule, daemon=True).start()

bot.polling()