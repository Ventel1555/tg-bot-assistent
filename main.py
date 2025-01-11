import telebot
import sqlite3
from datetime import datetime
import json
from typing import Optional, Tuple
import os

# Конфигурация
TOKEN = "YOUR_BOT_TOKEN"
SUPPORT_TOKEN = "super_secret_token_123"
DATABASE = "support_bot.db"

bot = telebot.TeleBot(TOKEN)

# Начало бота
if __name__ == "__main__":
    bot.infinity_polling()