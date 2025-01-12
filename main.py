import telebot
from db import Database # Из файлы db.py
from datetime import datetime
import json
import sqlite3
from typing import Optional, Tuple
import os

# Конфигурация
TOKEN = "YOUR_BOT_TOKEN"
SUPPORT_TOKEN = "super_secret_token_123"
DATABASE = "support_bot.db"

# Импортируем ф-ции и класс бд из db.py
db = Database(DATABASE)

bot = telebot.TeleBot(TOKEN)

# Обработчик команд
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "Добро пожаловать! Пожалуйста, представьтесь.")
    bot.register_next_step_handler(message, process_name)

def process_name(message):
    user_id = message.from_user.id
    name = message.text
    db.register_client(user_id, name)
    
    # Ищем свободного агента
    agent = db.find_available_agent()
    if agent:
        agent_id, agent_username = agent
        db.assign_chat(user_id, agent_id)
        bot.send_message(agent_id, f"Новый клиент: {name}")
        bot.reply_to(message, "Вас подключили к специалисту поддержки. Опишите вашу проблему.")
    else:
        bot.reply_to(message, "К сожалению, все специалисты сейчас заняты. Попробуйте позже.")

@bot.message_handler(commands=['register_support'])
def register_support_command(message):
    token = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if token == SUPPORT_TOKEN:
        db.register_support(message.from_user.id, message.from_user.username)
        bot.reply_to(message, "Вы успешно зарегистрированы как специалист поддержки.")
    else:
        bot.reply_to(message, "Неверный токен.")

@bot.message_handler(commands=['available'])
def available_command(message):
    agent_id = message.from_user.id
    is_available = not db.find_available_agent()
    db.update_agent_status(agent_id, is_available)
    status = "доступны" if is_available else "недоступны"
    bot.reply_to(message, f"Теперь вы {status} для новых запросов.")

@bot.message_handler(commands=['end_chat'])
def end_chat_command(message):
    agent_id = message.from_user.id
    client_id = db.end_chat(agent_id)
    if client_id:
        bot.send_message(client_id, "Диалог завершен. Спасибо за обращение!")
        bot.reply_to(message, "Диалог завершен.")
    else:
        bot.reply_to(message, "У вас нет активного диалога.")
        

# stats

# history 


# Обработчик всех смсок от пользователей
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        
        # Проверяем, имеет ли клиент активный диалог
        c.execute('SELECT current_agent_id, name FROM clients WHERE user_id = ?', (user_id,))
        client_result = c.fetchone()
        
        if client_result:
            agent_id, client_name = client_result
            if agent_id:
                bot.send_message(agent_id, f"{client_name}: {message.text}")
                db.add_message(user_id, agent_id, message.text, "client")
            else:
                bot.reply_to(message, "У вас нет активного диалога. Используйте /start для начала нового диалога.")
        
        # Проверим, имеет ли агент чат с клиентом
        c.execute('SELECT current_chat_id FROM support_agents WHERE user_id = ?', (user_id,))
        agent_result = c.fetchone()
        
        if agent_result:
            client_id = agent_result[0]
            if client_id:
                bot.send_message(client_id, message.text)
                db.add_message(client_id, user_id, message.text, "agent")
            else:
                bot.reply_to(message, "У вас нет активного диалога.")

# Начало бота
if __name__ == "__main__":
    bot.infinity_polling()