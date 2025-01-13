import sqlite3
from typing import Optional, Tuple
from datetime import datetime

# настройка бд
class Database:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.init_db()
    
    def init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            # Таблица для тех. поддержки 
            c.execute('''CREATE TABLE IF NOT EXISTS support_agents
                        (user_id INTEGER PRIMARY KEY,
                         username TEXT,
                         is_available BOOLEAN DEFAULT TRUE,
                         last_online TIMESTAMP,
                         current_chat_id INTEGER DEFAULT NULL)''')
            
            # Таблица для клиентов
            c.execute('''CREATE TABLE IF NOT EXISTS clients
                        (user_id INTEGER PRIMARY KEY,
                         name TEXT,
                         current_agent_id INTEGER DEFAULT NULL)''')
            
            # История чата 
            c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         client_id INTEGER,
                         agent_id INTEGER,
                         message TEXT,
                         sender TEXT,
                         timestamp TIMESTAMP,
                         FOREIGN KEY (client_id) REFERENCES clients(user_id),
                         FOREIGN KEY (agent_id) REFERENCES support_agents(user_id))''')
            conn.commit()

    def register_support(self, user_id: int, username: str):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO support_agents (user_id, username, last_online) VALUES (?, ?, ?)',
                     (user_id, username, datetime.now()))
            conn.commit()

    def find_available_agent(self) -> Optional[Tuple[int, str]]:
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''SELECT user_id, username FROM support_agents 
                        WHERE is_available = TRUE AND current_chat_id IS NULL
                        ORDER BY last_online DESC LIMIT 1''')
            result = c.fetchone()
            return result if result else None

    def update_agent_status(self, user_id: int, is_available: bool):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('UPDATE support_agents SET is_available = ?, last_online = ? WHERE user_id = ?',
                     (is_available, datetime.now(), user_id))
            conn.commit()

    def register_client(self, user_id: int, name: str):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO clients (user_id, name) VALUES (?, ?)',
                     (user_id, name))
            conn.commit()

    def assign_chat(self, client_id: int, agent_id: int):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('UPDATE clients SET current_agent_id = ? WHERE user_id = ?',
                     (agent_id, client_id))
            c.execute('UPDATE support_agents SET current_chat_id = ? WHERE user_id = ?',
                     (client_id, agent_id))
            conn.commit()

    def end_chat(self, agent_id: int):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('SELECT current_chat_id FROM support_agents WHERE user_id = ?', (agent_id,))
            client_id = c.fetchone()[0]
            if client_id:
                c.execute('UPDATE clients SET current_agent_id = NULL WHERE user_id = ?', (client_id,))
                c.execute('UPDATE support_agents SET current_chat_id = NULL WHERE user_id = ?', (agent_id,))
                conn.commit()
            return client_id

    def add_message(self, client_id: int, agent_id: int, message: str, sender: str):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO chat_history 
                        (client_id, agent_id, message, sender, timestamp)
                        VALUES (?, ?, ?, ?, ?)''',
                     (client_id, agent_id, message, sender, datetime.now()))
            conn.commit()

    def get_chat_history(self, client_id: int, agent_id: int) -> list:
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''SELECT message, sender, timestamp 
                        FROM chat_history 
                        WHERE client_id = ? AND agent_id = ?
                        ORDER BY timestamp''', (client_id, agent_id))
            return c.fetchall()

    def get_agent_stats(self, agent_id: int) -> dict:
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''SELECT COUNT(DISTINCT client_id) as total_clients,
                        COUNT(*) as total_messages
                        FROM chat_history 
                        WHERE agent_id = ?''', (agent_id,))
            clients, messages = c.fetchone()
            return {
                "total_clients": clients,
                "total_messages": messages
            }
