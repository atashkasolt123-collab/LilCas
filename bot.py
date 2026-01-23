import logging
import random
import sqlite3
import socket
import asyncio
import json
import time
from typing import Dict, List, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requests
from datetime import datetime, timedelta

BOT_TOKEN = "8222748757:AAEa0uAtC5JNr-IKlItpEy471VeM1ZJzsls"
CRYPTO_BOT_TOKEN = "520594:AAQbdXAC4R3zsQ7POKFb5p3w4gFc1V9LNcQ"
ADMIN_ID = 7313407194
CASINO_CHAT_ID = -1003310283988

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

RANKS = {
    0: {"name": "Novice", "min_games": 0, "progress": 0},
    1: {"name": "Player", "min_games": 10, "progress": 10},
    2: {"name": "Experienced", "min_games": 25, "progress": 25},
    3: {"name": "Expert", "min_games": 50, "progress": 50},
    4: {"name": "Master", "min_games": 100, "progress": 75},
    5: {"name": "Guru", "min_games": 200, "progress": 100}
}

DECK = [
    ('A', '♠'), ('2', '♠'), ('3', '♠'), ('4', '♠'), ('5', '♠'), ('6', '♠'), ('7', '♠'), ('8', '♠'), ('9', '♠'), ('10', '♠'), ('J', '♠'), ('Q', '♠'), ('K', '♠'),
    ('A', '♥'), ('2', '♥'), ('3', '♥'), ('4', '♥'), ('5', '♥'), ('6', '♥'), ('7', '♥'), ('8', '♥'), ('9', '♥'), ('10', '♥'), ('J', '♥'), ('Q', '♥'), ('K', '♥'),
    ('A', '♦'), ('2', '♦'), ('3', '♦'), ('4', '♦'), ('5', '♦'), ('6', '♦'), ('7', '♦'), ('8', '♦'), ('9', '♦'), ('10', '♦'), ('J', '♦'), ('Q', '♦'), ('K', '♦'),
    ('A', '♣'), ('2', '♣'), ('3', '♣'), ('4', '♣'), ('5', '♣'), ('6', '♣'), ('7', '♣'), ('8', '♣'), ('9', '♣'), ('10', '♣'), ('J', '♣'), ('Q', '♣'), ('K', '♣')
]

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('casino.db', check_same_thread=False)
        self.create_tables()
        self.update_database_structure()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0,
                total_bet REAL DEFAULT 0,
                total_won REAL DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                spins_count INTEGER DEFAULT 1,
                last_spin_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                crypto_amount REAL,
                currency TEXT,
                status TEXT,
                invoice_url TEXT,
                invoice_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                status TEXT,
                approved_by INTEGER,
                check_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                amount REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                result INTEGER,
                win_amount REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS duels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                joiner_id INTEGER,
                amount REAL,
                status TEXT,
                creator_dice INTEGER,
                joiner_dice INTEGER,
                winner_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                amount REAL,
                status TEXT,
                winner_id INTEGER,
                participants TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blackjack_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                joiner_id INTEGER,
                amount REAL,
                status TEXT,
                creator_cards TEXT,
                joiner_cards TEXT,
                creator_score INTEGER,
                joiner_score INTEGER,
                current_turn INTEGER,
                winner_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def update_database_structure(self):
        cursor = self.conn.cursor()

        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'spins_count' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN spins_count INTEGER DEFAULT 1')

        if 'last_spin_date' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN last_spin_date DATETIME')

        cursor.execute("PRAGMA table_info(deposits)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'invoice_id' not in columns:
            cursor.execute('ALTER TABLE deposits ADD COLUMN invoice_id TEXT')

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spins'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE spins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    result INTEGER,
                    win_amount REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='duels'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE duels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER,
                    joiner_id INTEGER,
                    amount REAL,
                    status TEXT,
                    creator_dice INTEGER,
                    joiner_dice INTEGER,
                    winner_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='giveaways'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE giveaways (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER,
                    amount REAL,
                    status TEXT,
                    winner_id INTEGER,
                    participants TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blackjack_games'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE blackjack_games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER,
                    joiner_id INTEGER,
                    amount REAL,
                    status TEXT,
                    creator_cards TEXT,
                    joiner_cards TEXT,
                    creator_score INTEGER,
                    joiner_score INTEGER,
                    current_turn INTEGER,
                    winner_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        self.conn.commit()

    def get_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

    def create_user(self, user_id: int, username: str):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username, spins_count) VALUES (?, ?, ?)', (user_id, username, 1))
        self.conn.commit()

    def update_balance(self, user_id: int, amount: float):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        self.conn.commit()

    def add_transaction(self, user_id: int, type: str, amount: float, description: str):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)',
            (user_id, type, amount, description)
        )
        self.conn.commit()

    def get_setting(self, key: str, default=None):
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result[0] if result else default

    def set_setting(self, key: str, value: str):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        self.conn.commit()

    def add_transfer(self, from_user_id: int, to_user_id: int, amount: float):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO transfers (from_user_id, to_user_id, amount) VALUES (?, ?, ?)',
            (from_user_id, to_user_id, amount)
        )
        self.conn.commit()

    def update_spins(self, user_id: int, spins_count: int, last_spin_date=None):
        cursor = self.conn.cursor()
        if last_spin_date:
            cursor.execute('UPDATE users SET spins_count = ?, last_spin_date = ? WHERE user_id = ?',
                          (spins_count, last_spin_date, user_id))
        else:
            cursor.execute('UPDATE users SET spins_count = ?, last_spin_date = CURRENT_TIMESTAMP WHERE user_id = ?',
                          (spins_count, user_id))
        self.conn.commit()

    def add_spin_result(self, user_id: int, result: int, win_amount: float):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO spins (user_id, result, win_amount) VALUES (?, ?, ?)',
            (user_id, result, win_amount)
        )
        self.conn.commit()

    def create_duel(self, creator_id: int, amount: float):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO duels (creator_id, amount, status) VALUES (?, ?, ?)',
            (creator_id, amount, 'waiting')
        )
        duel_id = cursor.lastrowid
        self.conn.commit()
        return duel_id

    def join_duel(self, duel_id: int, joiner_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE duels SET joiner_id = ?, status = ? WHERE id = ? AND status = ?',
            (joiner_id, 'active', duel_id, 'waiting')
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def update_duel_dice(self, duel_id: int, user_id: int, dice_value: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT creator_id, joiner_id FROM duels WHERE id = ?', (duel_id,))
        duel = cursor.fetchone()

        if duel[0] == user_id:
            cursor.execute('UPDATE duels SET creator_dice = ? WHERE id = ?', (dice_value, duel_id))
        else:
            cursor.execute('UPDATE duels SET joiner_dice = ? WHERE id = ?', (dice_value, duel_id))
        self.conn.commit()

    def complete_duel(self, duel_id: int, winner_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE duels SET status = ?, winner_id = ? WHERE id = ?',
            ('completed', winner_id, duel_id)
        )
        self.conn.commit()

    def get_duel(self, duel_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM duels WHERE id = ?', (duel_id,))
        return cursor.fetchone()

    def create_giveaway(self, creator_id: int, amount: float):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO giveaways (creator_id, amount, status, participants) VALUES (?, ?, ?, ?)',
            (creator_id, amount, 'active', '[]')
        )
        giveaway_id = cursor.lastrowid
        self.conn.commit()
        return giveaway_id

    def join_giveaway(self, giveaway_id: int, user_id: int, username: str):
        cursor = self.conn.cursor()
        cursor.execute('SELECT participants FROM giveaways WHERE id = ?', (giveaway_id,))
        result = cursor.fetchone()

        if result:
            participants = json.loads(result[0])
            for participant in participants:
                if participant['user_id'] == user_id:
                    return False

            participants.append({'user_id': user_id, 'username': username})
            cursor.execute(
                'UPDATE giveaways SET participants = ? WHERE id = ?',
                (json.dumps(participants), giveaway_id)
            )
            self.conn.commit()
            return True
        return False

    def get_giveaway(self, giveaway_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM giveaways WHERE id = ?', (giveaway_id,))
        return cursor.fetchone()

    def complete_giveaway(self, giveaway_id: int, winner_id: int):
        cursor = db.conn.cursor()
        cursor.execute(
            'UPDATE giveaways SET status = ?, winner_id = ? WHERE id = ?',
            ('completed', winner_id, giveaway_id)
        )
        self.conn.commit()

    def create_blackjack_game(self, creator_id: int, amount: float):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO blackjack_games (creator_id, amount, status) VALUES (?, ?, ?)',
            (creator_id, amount, 'waiting')
        )
        game_id = cursor.lastrowid
        self.conn.commit()
        return game_id

    def join_blackjack_game(self, game_id: int, joiner_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE blackjack_games SET joiner_id = ?, status = ? WHERE id = ? AND status = ?',
            (joiner_id, 'active', game_id, 'waiting')
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_blackjack_game(self, game_id: int):
        cursor = db.conn.cursor()
        cursor.execute('SELECT * FROM blackjack_games WHERE id = ?', (game_id,))
        return cursor.fetchone()

    def update_blackjack_game(self, game_id: int, creator_cards=None, joiner_cards=None,
                             creator_score=None, joiner_score=None, current_turn=None, status=None):
        cursor = self.conn.cursor()

        updates = []
        params = []

        if creator_cards is not None:
            updates.append('creator_cards = ?')
            params.append(creator_cards)

        if joiner_cards is not None:
            updates.append('joiner_cards = ?')
            params.append(joiner_cards)

        if creator_score is not None:
            updates.append('creator_score = ?')
            params.append(creator_score)

        if joiner_score is not None:
            updates.append('joiner_score = ?')
            params.append(joiner_score)

        if current_turn is not None:
            updates.append('current_turn = ?')
            params.append(current_turn)

        if status is not None:
            updates.append('status = ?')
            params.append(status)

        if updates:
            query = f'UPDATE blackjack_games SET {", ".join(updates)} WHERE id = ?'
            params.append(game_id)
            cursor.execute(query, params)
            self.conn.commit()

    def complete_blackjack_game(self, game_id: int, winner_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE blackjack_games SET status = ?, winner_id = ? WHERE id = ?',
            ('completed', winner_id, game_id)
        )
        self.conn.commit()

db = Database()

TOWER_COEFFICIENTS = {
    1: [1.2, 1.2, 1.5, 1.9, 2.3, 2.9, 3.65],
    2: [1.6, 1.6, 2.65, 4.3, 7.2, 12.2, 20],
    3: [2.4, 2.4, 5.9, 14.8, 37, 100, 230],
    4: [4.75, 4.75, 23, 100, 590, 3000, 15000]
}

MINES_COEFFICIENTS = {
    2: [1.0, 1.02, 1.11, 1.22, 1.34, 1.48, 1.65, 1.84, 2.07, 2.35, 2.69, 3.1, 3.62, 4.27, 5.13, 6.27, 7.83, 10.07, 13.43, 18.8, 28.2, 47, 94, 282],
    3: [1.0, 1.07, 1.22, 1.4, 1.63, 1.9, 2.23, 2.65, 3.18, 3.86, 4.75, 5.94, 7.56, 9.83, 13.1, 18.02, 25.74, 38.61, 61.77, 108.1, 216.2, 540.5, 2162],
    4: [1.0, 1.12, 1.34, 1.63, 1.99, 2.45, 3.07, 3.89, 5.0, 6.53, 8.71, 11.88, 16.63, 24.02, 36.03, 56.62, 94.37, 169.87, 339.74, 792.73, 2378.2, 11891],
    5: [1.0, 1.18, 1.48, 1.9, 2.45, 3.22, 4.29, 5.83, 8.07, 11.43, 16.63, 24.95, 38.81, 63.06, 108.1, 198.18, 396.37, 891.82, 2378.2, 8323.7, 49942.2],
    6: [1.0, 1.24, 1.65, 2.23, 3.07, 4.29, 6.14, 8.97, 13.45, 20.79, 33.26, 55.44, 97.01, 180.17, 360.33, 792.73, 1981.83, 5945.5, 23782, 166474],
    7: [1.0, 1.31, 1.84, 2.65, 3.89, 5.83, 8.97, 14.2, 23.23, 39.5, 70.22, 131.66, 263.32, 570.53, 1369.27, 3765.48, 12551.61, 56482.25, 451858],
    8: [1.0, 1.38, 2.07, 3.18, 5.0, 8.07, 13.45, 23.23, 41.82, 79.0, 157.99, 338.55, 789.96, 2053.9, 6161.7, 22592.9, 112964.5, 1016680.5],
    9: [1.0, 1.47, 2.35, 3.86, 6.53, 11.43, 20.79, 39.5, 79.0, 167.87, 383.7, 959.24, 2685.87, 8729.07, 34916.3, 192039.65, 1920396.5],
    10: [1.0, 1.57, 2.69, 4.75, 8.71, 16.63, 33.26, 70.22, 157.99, 383.7, 1023.19, 3069.56, 10743.48, 46555.07, 279330.4, 3072634.4],
    11: [1.0, 1.68, 3.1, 5.94, 11.88, 24.95, 55.44, 131.66, 338.55, 959.24, 3069.56, 11510.87, 53717.38, 349163, 4189956],
    12: [1.0, 1.81, 3.62, 7.56, 16.63, 38.81, 97.01, 263.32, 789.96, 2685.87, 10743.48, 53717.38, 376021.69, 4888282],
    13: [1.0, 1.96, 4.27, 9.83, 24.02, 63.06, 180.17, 570.53, 2053.9, 8729.08, 46555.07, 349163, 4888282],
    14: [1.0, 2.14, 5.13, 13.1, 36.03, 108.1, 360.33, 1369.27, 6161.7, 34916.3, 279330.4, 4189956],
    15: [1.0, 2.35, 6.27, 18.02, 56.62, 198.18, 792.73, 3765.48, 22592.9, 192039.65, 3072634.4],
    16: [1.0, 2.61, 7.83, 25.74, 94.37, 396.37, 1981.83, 12551.61, 112964.5, 1920396.5],
    17: [1.0, 2.94, 10.07, 38.61, 169.87, 891.83, 5945.5, 56482.25, 1016680.5],
    18: [1.0, 3.36, 13.43, 61.77, 339.74, 2378.2, 23782, 451858],
    19: [1.0, 3.92, 18.8, 108.1, 792.73, 8323.7, 166474],
    20: [1.0, 4.7, 28.2, 216.2, 2378.2, 49942.2],
    21: [1.0, 5.88, 47, 540.5, 11891],
    22: [1.0, 7.83, 94, 2162],
    23: [1.0, 11.75, 282],
    24: [1.0, 23.5]
}

def get_mines_coefficient(mines_count: int, opened_cells: int) -> float:
    if opened_cells == 0:
        return 1.0

    if mines_count in MINES_COEFFICIENTS and opened_cells < len(MINES_COEFFICIENTS[mines_count]):
        return MINES_COEFFICIENTS[mines_count][opened_cells]

    return 1.0

def get_next_mines_coefficient(mines_count: int, opened_cells: int) -> float:
    next_cell = opened_cells + 1
    if mines_count in MINES_COEFFICIENTS and next_cell < len(MINES_COEFFICIENTS[mines_count]):
        return MINES_COEFFICIENTS[mines_count][next_cell]
    return 1.0

DEFAULT_SETTINGS = {
    'welcome_message': '''<b>LIL ɢᴀᴍᴇs</b>
<blockquote>🍀 <b>LIL ɢᴀᴍᴇs</b> —— <b>игры прямо в Telegram, умножай свои $ и зарабатывай!</b></blockquote>
<b>Чат с играми <a href="https://t.me/LiLcasinochat">LIL ɢᴀᴍᴇs</a> вы сможете играть вместе с друзьями и другими игроками 🎰

📰 NEWS – <a href="http://t.me/LiLcasinoo">NEWS LIL</a></b>''',
    'deposit_amounts': '0.2,1,5,10,50,100'
}

class GameSession:
    def __init__(self):
        self.sessions: Dict[int, Dict] = {}
        self.last_click_time: Dict[int, float] = {}

    def create_session(self, user_id: int, game_type: str, **kwargs):
        self.sessions[user_id] = {
            'game_type': game_type,
            'state': 'playing',
            'moves_made': 0,
            **kwargs
        }

    def get_session(self, user_id: int):
        return self.sessions.get(user_id)

    def update_session(self, user_id: int, **kwargs):
        if user_id in self.sessions:
            self.sessions[user_id].update(kwargs)

    def end_session(self, user_id: int):
        if user_id in self.sessions:
            del self.sessions[user_id]

    def can_click(self, user_id: int) -> bool:
        current_time = time.time()
        last_time = self.last_click_time.get(user_id, 0)
        if current_time - last_time < 0.8:
            return False
        self.last_click_time[user_id] = current_time
        return True

game_sessions = GameSession()

def get_user_rank(games_played: int) -> Dict:
    current_rank = 0
    for rank_id, rank_info in RANKS.items():
        if games_played >= rank_info["min_games"]:
            current_rank = rank_id
        else:
            break

    current_rank_info = RANKS[current_rank]
    next_rank = current_rank + 1 if current_rank < len(RANKS) - 1 else current_rank

    if next_rank in RANKS:
        next_rank_games = RANKS[next_rank]["min_games"]
        progress = min(100, int((games_played - current_rank_info["min_games"]) / (next_rank_games - current_rank_info["min_games"]) * 100)) if next_rank_games > current_rank_info["min_games"] else 100
    else:
        progress = 100

    return {
        "current_rank": current_rank,
        "current_rank_name": current_rank_info["name"],
        "next_rank": next_rank,
        "next_rank_name": RANKS[next_rank]["name"] if next_rank in RANKS else current_rank_info["name"],
        "progress": progress,
        "games_played": games_played
    }

def get_progress_bar(progress: int) -> str:
    bars = 10
    filled_bars = int(progress / 100 * bars)
    empty_bars = bars - filled_bars
    return "▰" * filled_bars + "▱" * empty_bars

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🎲 Играть"), KeyboardButton("⚡️ Профиль")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_welcome_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎲 Играть!", callback_data="back_games"),
         InlineKeyboardButton("🎰 Крутить!", callback_data="daily_spin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_games_keyboard():
    keyboard = [
        [InlineKeyboardButton("• 🤖 Играть в боте", callback_data="play_in_bot"),
         InlineKeyboardButton("🎮 Играть в чате", callback_data="play_in_chat")],
        [InlineKeyboardButton("« Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_games_bot_keyboard():
    keyboard = [
        [InlineKeyboardButton("💣 Мины", callback_data="game_mines"), InlineKeyboardButton("🏰 Башня", callback_data="game_tower")],
        [InlineKeyboardButton("🎲 Дайс", callback_data="game_dice")],
        [InlineKeyboardButton("« Назад", callback_data="back_games_bot")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_chat_keyboard():
    keyboard = [
        [InlineKeyboardButton("💬 Вступить в чат", url="https://t.me/LiLcasinochat")],
        [InlineKeyboardButton("« Назад", callback_data="back_games")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_mines_bet_keyboard(user_id: int):
    keyboard = []
    balance = get_balance_rounded(user_id)
    keyboard.append([InlineKeyboardButton("⚡️ Мин. 0.2 USDT ($0.20)", callback_data="bet_0.2")])
    keyboard.append([InlineKeyboardButton("💵 Своя ставка", callback_data="custom_bet")])
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="back_games_bot")])
    return InlineKeyboardMarkup(keyboard)

def get_mines_count_keyboard():
    keyboard = []
    for i in range(2, 24, 4):
        row = []
        for j in range(i, min(i+4, 24)):
            row.append(InlineKeyboardButton(f"{j}", callback_data=f"mines_{j}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="back_mines_bet")])
    return InlineKeyboardMarkup(keyboard)

def get_mines_game_keyboard(opened_cells: List[int], mines_positions: List[int], can_cashout: bool = True, current_win: float = 0, game_ended: bool = False):
    keyboard = []
    for row in range(5):
        keyboard_row = []
        for col in range(5):
            cell_index = row * 5 + col
            if game_ended and cell_index in mines_positions:
                keyboard_row.append(InlineKeyboardButton("💣", callback_data="mines_disabled"))
            elif cell_index in opened_cells:
                keyboard_row.append(InlineKeyboardButton("💎", callback_data="mines_disabled"))
            else:
                if not game_ended:
                    keyboard_row.append(InlineKeyboardButton("⛶", callback_data=f"mine_{row}_{col}"))
                else:
                    keyboard_row.append(InlineKeyboardButton("⛶", callback_data="mines_disabled"))
        keyboard.append(keyboard_row)

    if can_cashout and not game_ended:
        cashout_button = [InlineKeyboardButton(f"⚡️ Забрать (${current_win:.2f})", callback_data="mines_cashout")]
        keyboard.append(cashout_button)

    return InlineKeyboardMarkup(keyboard)

def get_tower_bet_keyboard(user_id: int):
    keyboard = []
    balance = get_balance_rounded(user_id)
    keyboard.append([InlineKeyboardButton("⚡️ Мин. 0.2 USDT ($0.20)", callback_data="tower_bet_0.2")])
    keyboard.append([InlineKeyboardButton("💵 Своя ставка", callback_data="tower_custom_bet")])
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="back_games_bot")])
    return InlineKeyboardMarkup(keyboard)

def get_tower_mines_keyboard():
    keyboard = [
        [InlineKeyboardButton("1 мина", callback_data="tower_mines_1")],
        [InlineKeyboardButton("2 мины", callback_data="tower_mines_2")],
        [InlineKeyboardButton("3 мины", callback_data="tower_mines_3")],
        [InlineKeyboardButton("4 мины", callback_data="tower_mines_4")],
        [InlineKeyboardButton("« Назад", callback_data="back_tower_bet")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_tower_game_keyboard(current_level: int, opened_cells: List[int], mines_positions: List[int], can_cashout: bool, current_win: float, game_ended: bool = False):
    keyboard = []
    for row in range(5, -1, -1):
        keyboard_row = []
        for col in range(5):
            cell_index = row * 5 + col
            if game_ended and cell_index in mines_positions:
                keyboard_row.append(InlineKeyboardButton("💣", callback_data="tower_disabled"))
            elif cell_index in opened_cells:
                keyboard_row.append(InlineKeyboardButton("💎", callback_data="tower_disabled"))
            else:
                if row == current_level and not game_ended:
                    keyboard_row.append(InlineKeyboardButton("⛶", callback_data=f"tower_click_{row}_{col}"))
                else:
                    keyboard_row.append(InlineKeyboardButton("⛶", callback_data="tower_disabled"))
        keyboard.append(keyboard_row)

    if can_cashout and not game_ended:
        keyboard.append([InlineKeyboardButton(f"⚡️ Забрать (${current_win:.2f})", callback_data="tower_cashout")])

    return InlineKeyboardMarkup(keyboard)

def get_dice_bet_keyboard(user_id: int):
    keyboard = []
    balance = get_balance_rounded(user_id)
    keyboard.append([InlineKeyboardButton("⚡️ Мин. 0.2 USDT ($0.20)", callback_data="dice_bet_0.2")])
    keyboard.append([InlineKeyboardButton("💵 Своя ставка", callback_data="dice_custom_bet")])
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="back_games_bot")])
    return InlineKeyboardMarkup(keyboard)

def get_dice_mode_keyboard():
    keyboard = [
        [InlineKeyboardButton("Чёт/Нечёт", callback_data="dice_mode_evenodd")],
        [InlineKeyboardButton("Больше/Меньше", callback_data="dice_mode_highlow")],
        [InlineKeyboardButton("Больше/Меньше 7", callback_data="dice_mode_highlow7")],
        [InlineKeyboardButton("« Назад", callback_data="back_dice_mode")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_dice_choice_keyboard(mode: str):
    if mode == "evenodd":
        keyboard = [
            [InlineKeyboardButton("Чёт", callback_data="dice_choice_even"),
             InlineKeyboardButton("Нечёт", callback_data="dice_choice_odd")],
            [InlineKeyboardButton("« Назад", callback_data="back_dice_mode")]
        ]
    elif mode == "highlow":
        keyboard = [
            [InlineKeyboardButton("Больше", callback_data="dice_choice_high"),
             InlineKeyboardButton("Меньше", callback_data="dice_choice_low")],
            [InlineKeyboardButton("« Назад", callback_data="back_dice_mode")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("Больше 7", callback_data="dice_choice_high7"),
             InlineKeyboardButton("Меньше 7", callback_data="dice_choice_low7")],
            [InlineKeyboardButton("« Назад", callback_data="back_dice_mode")]
        ]
    return InlineKeyboardMarkup(keyboard)

def get_profile_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚡️ Пополнить", callback_data="deposit"),
         InlineKeyboardButton("💎 Вывести", callback_data="withdraw")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_deposit_keyboard():
    amounts = db.get_setting('deposit_amounts', DEFAULT_SETTINGS['deposit_amounts']).split(',')
    keyboard = []
    row = []
    for i, amount in enumerate(amounts):
        row.append(InlineKeyboardButton(f"{amount} $", callback_data=f"deposit_{amount}"))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("💵 Своя сумма", callback_data="deposit_custom")])
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="back_profile")])
    return InlineKeyboardMarkup(keyboard)

def get_deposit_invoice_keyboard(invoice_url: str):
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить счет", url=invoice_url)],
        [InlineKeyboardButton("« Назад", callback_data="back_profile")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_withdrawal_keyboard():
    amounts = db.get_setting('deposit_amounts', DEFAULT_SETTINGS['deposit_amounts']).split(',')
    keyboard = []
    row = []
    for i, amount in enumerate(amounts):
        row.append(InlineKeyboardButton(f"{amount} $", callback_data=f"withdraw_{amount}"))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("💵 Своя сумма", callback_data="withdraw_custom")])
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="back_profile")])
    return InlineKeyboardMarkup(keyboard)

def get_withdrawal_cancel_keyboard():
    keyboard = [
        [InlineKeyboardButton("🚫 Отменить", callback_data="cancel_withdrawal")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("💳 Выводы", callback_data="admin_withdrawals")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")],
        [InlineKeyboardButton("💰 Настройка пополнений", callback_data="admin_deposit_settings")],
        [InlineKeyboardButton("« Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    keyboard = [
        [InlineKeyboardButton("« Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_spin_keyboard(user_id: int, can_spin: bool = True):
    spins_count = get_spins_count(user_id)
    keyboard = []
    if can_spin:
        keyboard.append([InlineKeyboardButton("🎰 Крутить", callback_data="do_spin")])
    keyboard.append([InlineKeyboardButton("ВСТУПИТЬ В ЧАТ 💬", url="https://t.me/+p2bGwIhtLMNkMGVi")])
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)

def get_withdrawal_approve_keyboard(withdrawal_id: int):
    keyboard = [
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_withdrawal_{withdrawal_id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_withdrawal_{withdrawal_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_duel_join_keyboard(duel_id: int):
    keyboard = [
        [InlineKeyboardButton("Присоединится 🎲", callback_data=f"join_duel_{duel_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_giveaway_join_keyboard(giveaway_id: int):
    keyboard = [
        [InlineKeyboardButton("Присоединится 🎁", callback_data=f"join_giveaway_{giveaway_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_giveaway_completed_keyboard():
    keyboard = [
        [InlineKeyboardButton("« Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_blackjack_join_keyboard(game_id: int):
    keyboard = [
        [InlineKeyboardButton("🍀 Присоединится", callback_data=f"join_blackjack_{game_id}")],
        [InlineKeyboardButton("🚫 Отменить", callback_data=f"cancel_blackjack_{game_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_blackjack_game_keyboard(game_id: int, can_take_card: bool = True):
    keyboard = [
        [InlineKeyboardButton("🖐️ Взять", callback_data=f"blackjack_take_{game_id}"),
         InlineKeyboardButton("🤚 Остановится", callback_data=f"blackjack_stand_{game_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def generate_mines_positions(mines_count: int) -> List[int]:
    positions = list(range(25))
    random.shuffle(positions)
    return positions[:mines_count]

def generate_tower_level_mines(mines_count: int, level: int) -> List[int]:
    positions = list(range(5))
    random.shuffle(positions)
    return [level * 5 + pos for pos in positions[:mines_count]]

def check_dice_win(dice_value: int, mode: str, choice: str) -> bool:
    if mode == "evenodd":
        if choice == "even":
            return dice_value % 2 == 0
        else:
            return dice_value % 2 == 1
    elif mode == "highlow":
        if choice == "high":
            return dice_value > 3
        else:
            return dice_value < 4
    else:
        if choice == "high7":
            return dice_value > 7
        else:
            return dice_value < 7

def get_balance_rounded(user_id: int) -> float:
    user_data = db.get_user(user_id)
    if user_data:
        return round(user_data[2], 2)
    return 0.0

def get_spins_count(user_id: int) -> int:
    user_data = db.get_user(user_id)
    if user_data:
        return user_data[6]
    return 0

def get_card_value(card_value: str) -> int:
    if card_value in ['J', 'Q', 'K']:
        return 10
    elif card_value == 'A':
        return 11
    else:
        return int(card_value)

def calculate_hand_score(cards: List[Tuple[str, str]]) -> int:
    score = 0
    aces = 0

    for card_value, _ in cards:
        value = get_card_value(card_value)
        if card_value == 'A':
            aces += 1
            score += 11
        else:
            score += value

    while score > 21 and aces > 0:
        score -= 10
        aces -= 1

    return score

def format_cards(cards: List[Tuple[str, str]]) -> str:
    return " ".join([f"{suit}{value}" for value, suit in cards])

def format_cards_with_hidden(cards: List[Tuple[str, str]], hide_first: bool = False) -> str:
    if not cards:
        return ""

    if hide_first:
        return f"🃏 ? {' '.join([f'{suit}{value}' for value, suit in cards[1:]])}"
    else:
        return format_cards(cards)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.create_user(user.id, user.username or user.first_name)

    welcome_message = db.get_setting('welcome_message', DEFAULT_SETTINGS['welcome_message'])

    await update.message.reply_text(
        welcome_message,
        reply_markup=get_welcome_keyboard(),
        parse_mode='HTML'
    )

async def quick_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_profile(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text.startswith('/'):
        command_parts = text[1:].split()
        if not command_parts:
            return

        command = command_parts[0].lower()
        if command == 'п':
            context.args = command_parts[1:]
            await transfer_money(update, context)
            return
        elif command == 'б':
            await show_profile(update, context)
            return
        elif command == 'админ':
            await admin_command(update, context)
            return
        elif command == 'spin':
            await daily_spin_command(update, context)
            return
        elif command == 'cg':
            await create_duel_command(update, context)
            return
        elif command == 'fast':
            await create_giveaway_command(update, context)
            return
        elif command == '21':
            await create_blackjack_command(update, context)
            return
        elif command == 'o' and update.effective_user.id == ADMIN_ID:
            await reset_balance_command(update, context)

    # Обработка команд без слеша для чата казино
    if update.effective_chat.id == CASINO_CHAT_ID:
        text_lower = text.lower()
        command_parts = text.split()

        if not command_parts:
            return

        command = command_parts[0].lower()

        if command == 'б':
            await show_profile(update, context)
            return
        elif command == 'деп' and len(command_parts) >= 2:
            await handle_dep_command_chat(update, context, command_parts)
            return
        elif command == 'mines' and len(command_parts) >= 3:
            await quick_mines_command(update, context)
            return
        elif command == 'tower' and len(command_parts) >= 3:
            await quick_tower_command(update, context)
            return
        elif command == 'cube' and len(command_parts) >= 3:
            await quick_dice_command(update, context)
            return

    if text == "🎲 Играть":
        try:
            await update.message.reply_sticker("CAACAgIAAxkBAAIK4GkbUZyY_sk5ILY16Vx2G8GIUFPaAALgFQACHKIYSMXiQP8zW3fcNgQ")
        except:
            pass

        await asyncio.sleep(0.5)

        await update.message.reply_text(
            "🎮 <b>Выберите где хотите играть:</b>",
            reply_markup=get_games_keyboard(),
            parse_mode='HTML'
        )
    elif text == "⚡️ Профиль" or text.lower() == "б":
        await show_profile(update, context)
    elif context.user_data.get('waiting_for_bet'):
        await handle_custom_bet(update, context)
    elif context.user_data.get('waiting_for_deposit'):
        await handle_custom_deposit(update, context)
    elif context.user_data.get('waiting_for_withdrawal'):
        await handle_custom_withdrawal(update, context)
    elif context.user_data.get('waiting_for_deposit_settings'):
        await handle_deposit_settings(update, context)

async def handle_dep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ <b>Использование: /деп (сумма)</b>\n\n"
            "Пример: /деп 10",
            parse_mode='HTML'
        )
        return

    try:
        amount = float(context.args[0])
        if amount < 0.2:
            await update.message.reply_text("❌ <b>Минимальная сумма пополнения 0.2$!</b>", parse_mode='HTML')
            return

        await create_cryptobot_invoice(update, context, amount)

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат суммы!</b>", parse_mode='HTML')

async def handle_dep_command_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, command_parts: list):
    try:
        amount = float(command_parts[1])
        if amount < 0.2:
            await update.message.reply_text("❌ <b>Минимальная сумма пополнения 0.2$!</b>", parse_mode='HTML')
            return

        await create_cryptobot_invoice(update, context, amount)

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат суммы!</b>", parse_mode='HTML')

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = db.get_user(user.id)

    if user_data:
        cursor = db.conn.cursor()
        cursor.execute('SELECT SUM(amount) FROM deposits WHERE user_id = ? AND status = "completed"', (user.id,))
        total_deposits = cursor.fetchone()[0] or 0

        rank_info = get_user_rank(user_data[5])
        progress_bar = get_progress_bar(rank_info["progress"])

        profile_text = f"""<b>🪪 Твой профиль</b>

<b>💎 Ваш баланс:</b> <code>{get_balance_rounded(user.id)}$</code>
<blockquote>∟ <b>🔗 Ваш username</b>: <b>{user.username or user.first_name}</b>
∟ <b>⚡️Сумма депозитов:</b> <code>{total_deposits}$</code>

<b>🎮 Сыграно →</b> <b>{user_data[5]}</b></blockquote>

<b>✳️ Ваш прогресс —</b> <b>{rank_info["progress"]}%</b>
{progress_bar} → 🎁
🎖 <b>{rank_info["current_rank_name"]}</b> → <b>{rank_info["next_rank_name"]}</b> 🏅"""

        if update.message:
            await update.message.reply_text(
                profile_text,
                reply_markup=get_profile_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.callback_query.edit_message_text(
                profile_text,
                reply_markup=get_profile_keyboard(),
                parse_mode='HTML'
            )

async def show_profile_callback(query, context):
    user = query.from_user
    user_data = db.get_user(user.id)

    if user_data:
        cursor = db.conn.cursor()
        cursor.execute('SELECT SUM(amount) FROM deposits WHERE user_id = ? AND status = "completed"', (user.id,))
        total_deposits = cursor.fetchone()[0] or 0

        rank_info = get_user_rank(user_data[5])
        progress_bar = get_progress_bar(rank_info["progress"])

        profile_text = f"""<b>🪪 Твой профиль</b>

<b>💎 Ваш баланс:</b> <code>{get_balance_rounded(user.id)}$</code>
<blockquote>∟ <b>🔗 Ваш username</b>: <b>{user.username or user.first_name}</b>
∟ <b>⚡️Сумма депозитов:</b> <code>{total_deposits}$</code>

<b>🎮 Сыграно →</b> <b>{user_data[5]}</b></blockquote>

<b>✳️ Ваш прогресс —</b> <b>{rank_info["progress"]}%</b>
{progress_bar} → 🎁
🎖 <b>{rank_info["current_rank_name"]}</b> → <b>{rank_info["next_rank_name"]}</b> 🏅"""

        await query.edit_message_text(
            profile_text,
            reply_markup=get_profile_keyboard(),
            parse_mode='HTML'
        )

async def transfer_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ <b>Используйте команду в ответ на сообщение пользователя, которому хотите перевести средства!</b>\n\n"
            "Пример: /п 10",
            parse_mode='HTML'
        )
        return

    from_user = update.effective_user
    to_user = update.message.reply_to_message.from_user
    from_user_data = db.get_user(from_user.id)

    if from_user.id == to_user.id:
        await update.message.reply_text("❌ <b>Нельзя переводить самому себе!</b>", parse_mode='HTML')
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ <b>Укажите сумму перевода!</b>\n\n"
            "Пример: /п 10",
            parse_mode='HTML'
        )
        return

    try:
        amount = float(context.args[0])

        if amount < 0.2:
            await update.message.reply_text("❌ <b>Минимальная сумма перевода 0.2$!</b>", parse_mode='HTML')
            return

        if not from_user_data or from_user_data[2] < amount:
            await update.message.reply_text("❌ <b>Недостаточно средств для перевода!</b>", parse_mode='HTML')
            return

        db.create_user(to_user.id, to_user.username or to_user.first_name)

        db.update_balance(from_user.id, -amount)
        db.update_balance(to_user.id, amount)
        db.add_transaction(from_user.id, 'transfer_out', -amount, f'Перевод пользователю @{to_user.username or to_user.id}')
        db.add_transaction(to_user.id, 'transfer_in', amount, f'Перевод от пользователя @{from_user.username or from_user.id}')
        db.add_transfer(from_user.id, to_user.id, amount)

        await update.message.reply_text(
            f"🎁 <b>{from_user.first_name} подарил вам {amount}$</b>",
            parse_mode='HTML'
        )

        await update.message.reply_text(
            f"✅ <b>Перевод выполнен успешно!</b>\n\n"
            f"💸 Сумма: <b>{amount}$</b>\n"
            f"👤 Получатель: <b>{to_user.first_name}</b>",
            parse_mode='HTML'
        )

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат суммы!</b>", parse_mode='HTML')

async def daily_spin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user

    if update.effective_chat.id != CASINO_CHAT_ID:
        await update.message.reply_text("❌ <b>Эта команда доступна только в чате казино!</b>", parse_mode='HTML')
        return

    user_data = db.get_user(user_id)

    if not user_data:
        db.create_user(user_id, user.username or user.first_name)
        user_data = db.get_user(user_id)

    spins_count = user_data[6] if len(user_data) > 6 else 1
    last_spin_date = user_data[7] if len(user_data) > 7 else None

    can_claim = False
    time_remaining = None

    if last_spin_date is None:
        can_claim = True
    else:
        try:
            if isinstance(last_spin_date, str):
                last_date = datetime.strptime(last_spin_date, '%Y-%m-%d %H:%M:%S')
            else:
                last_date = datetime.fromisoformat(str(last_spin_date))

            time_diff = datetime.now() - last_date

            if time_diff >= timedelta(hours=24):
                can_claim = True
            else:
                remaining = timedelta(hours=24) - time_diff
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_remaining = f"{hours} ч. {minutes} м. {seconds} с."
        except (ValueError, TypeError) as e:
            can_claim = True

    if can_claim:
        new_spins_count = 1
        db.update_spins(user_id, new_spins_count, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        await update.message.reply_text(
            f"<b>[⚡] Вы забрали ежедневный спин!</b>\n\n<b>Доступно спинов - {new_spins_count} шт 🎰</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 Крутить", callback_data="do_spin")]]),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"<b>⏳ Осталось {time_remaining}</b>",
            parse_mode='HTML'
        )

async def daily_spin_callback(query, context):
    user_id = query.from_user.id
    user_data = db.get_user(user_id)

    if not user_data:
        db.create_user(user_id, query.from_user.username or query.from_user.first_name)
        user_data = db.get_user(user_id)

    spins_count = user_data[6] if len(user_data) > 6 else 1
    last_spin_date = user_data[7] if len(user_data) > 7 else None

    can_spin = True
    if last_spin_date:
        try:
            if isinstance(last_spin_date, str):
                last_date = datetime.strptime(last_spin_date, '%Y-%m-%d %H:%M:%S')
            else:
                last_date = datetime.fromisoformat(str(last_spin_date))

            time_diff = datetime.now() - last_date
            if time_diff < timedelta(hours=24):
                can_spin = False
        except:
            pass

    spin_text = f"""<b>Бесплатные СПИНЫ 🎰</b>

<b>Доступно спинов - {spins_count} шт 🎰</b>

<blockquote>Каждые 24 часа бот начисляет 1 БЕСПЛАТНЫЙ СПИН ✅</blockquote>"""

    await query.edit_message_text(
        spin_text,
        reply_markup=get_spin_keyboard(user_id, can_spin),
        parse_mode='HTML'
    )

async def quick_mines_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ <b>Использование: /mines (сумма ставки) (количество мин)</b>\n\n"
            "Пример: /mines 10 5",
            parse_mode='HTML'
        )
        return

    try:
        bet_amount = float(context.args[0])
        mines_count = int(context.args[1])

        if bet_amount < 0.2:
            await update.message.reply_text("❌ <b>Минимальная ставка 0.2$!</b>", parse_mode='HTML')
            return

        if mines_count < 2 or mines_count > 23:
            await update.message.reply_text("❌ <b>Количество мин должно быть от 2 до 23!</b>", parse_mode='HTML')
            return

        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < bet_amount:
            await update.message.reply_text("❌ <b>Недостаточно средств!</b>", parse_mode='HTML')
            return

        db.update_balance(user_id, -bet_amount)
        db.add_transaction(user_id, 'bet', -bet_amount, f'Ставка в игре Мины ({mines_count} мин)')

        coefficient = get_mines_coefficient(mines_count, 0)
        current_win = bet_amount * coefficient

        game_id = random.randint(1000, 9999)
        game_text = f"""<b>💣 Мины</b> <code>{bet_amount}$</code> • <b>{mines_count}</b>

<blockquote><i>🧨 Мин в поле</i> - <b>{mines_count}</b> / 5x5</blockquote>

<i>👇 Чтобы начать, нажимай на клетки</i>"""

        mines_positions = generate_mines_positions(mines_count)

        game_sessions.create_session(
            user_id=user_id,
            game_type='mines',
            bet=bet_amount,
            mines_count=mines_count,
            opened_cells=[],
            mines_positions=mines_positions
        )

        keyboard = get_mines_game_keyboard([], mines_positions, True, current_win, False)
        await update.message.reply_text(
            game_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат аргументов!</b>", parse_mode='HTML')

async def quick_tower_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ <b>Использование: /tower (сумма ставки) (количество мин)</b>\n\n"
            "Пример: /tower 10 2",
            parse_mode='HTML'
        )
        return

    try:
        bet_amount = float(context.args[0])
        mines_count = int(context.args[1])

        if bet_amount < 0.2:
            await update.message.reply_text("❌ <b>Минимальная ставка 0.2$!</b>", parse_mode='HTML')
            return

        if mines_count < 1 or mines_count > 4:
            await update.message.reply_text("❌ <b>Количество мин должно быть от 1 до 4!</b>", parse_mode='HTML')
            return

        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < bet_amount:
            await update.message.reply_text("❌ <b>Недостаточно средств!</b>", parse_mode='HTML')
            return

        db.update_balance(user_id, -bet_amount)
        db.add_transaction(user_id, 'bet', -bet_amount, f'Ставка в игре Башня ({mines_count} мин)')

        coefficients = TOWER_COEFFICIENTS.get(mines_count, [1.0] * 6)

        mines_positions = []
        for level in range(6):
            level_mines = generate_tower_level_mines(mines_count, level)
            mines_positions.extend(level_mines)

        game_sessions.create_session(
            user_id=user_id,
            game_type='tower',
            bet=bet_amount,
            mines_count=mines_count,
            coefficients=coefficients,
            current_level=0,
            opened_cells=[],
            mines_positions=mines_positions
        )

        current_coeff = coefficients[0]
        current_win = bet_amount * current_coeff

        game_text = f"""<b>[🗼] Башня · {mines_count} 💣</b>

<blockquote><b>💎 Ставка - {bet_amount}$</b>
<b>💣 Мин в ряду - {mines_count} / 6×5</b></blockquote>"""

        keyboard = get_tower_game_keyboard(0, [], mines_positions, False, current_win, False)
        await update.message.reply_text(
            game_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат аргументов!</b>", parse_mode='HTML')

async def quick_dice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ <b>Использование: /cube (сумма ставки) (исход)</b>\n\n"
            "Доступные исходы:\n"
            "- чет/нечет\n"
            "- больше/меньше\n"
            "- больше7/меньше7\n\n"
            "Пример: /cube 10 чет",
            parse_mode='HTML'
        )
        return

    try:
        bet_amount = float(context.args[0])
        choice_text = context.args[1].lower()

        if bet_amount < 0.2:
            await update.message.reply_text("❌ <b>Минимальная ставка 0.2$!</b>", parse_mode='HTML')
            return

        mode = None
        choice = None

        if choice_text in ['чет', 'нечет']:
            mode = 'evenodd'
            choice = 'even' if choice_text == 'чет' else 'odd'
        elif choice_text in ['больше', 'меньше']:
            mode = 'highlow'
            choice = 'high' if choice_text == 'больше' else 'low'
        elif choice_text in ['больше7', 'меньше7']:
            mode = 'highlow7'
            choice = 'high7' if choice_text == 'больше7' else 'low7'
        else:
            await update.message.reply_text(
                "❌ <b>Неверный исход!</b>\n\n"
                "Доступные исходы:\n"
                "- чет/нечет\n"
                "- больше/меньше\n"
                "- больше7/меньше7",
                parse_mode='HTML'
            )
            return

        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < bet_amount:
            await update.message.reply_text("❌ <b>Недостаточно средств!</b>", parse_mode='HTML')
            return

        db.update_balance(user_id, -bet_amount)
        db.add_transaction(user_id, 'bet', -bet_amount, f'Ставка в игре Дайс ({mode})')

        if mode == 'highlow7':
            dice1_message = await context.bot.send_dice(chat_id=update.message.chat_id, emoji="🎲")
            dice2_message = await context.bot.send_dice(chat_id=update.message.chat_id, emoji="🎲")
            dice1_value = dice1_message.dice.value
            dice2_value = dice2_message.dice.value
            dice_value = dice1_value + dice2_value
            dice_text = f"🎲 Результат: {dice1_value} + {dice2_value} = {dice_value}"
        else:
            dice_message = await context.bot.send_dice(chat_id=update.message.chat_id, emoji="🎲")
            dice_value = dice_message.dice.value
            dice_text = f"🎲 Результат: {dice_value}"

        await asyncio.sleep(2)

        won = check_dice_win(dice_value, mode, choice)

        db.conn.execute('UPDATE users SET total_bet = total_bet + ?, games_played = games_played + 1 WHERE user_id = ?',
                       (bet_amount, user_id))

        if won:
            win_amount = bet_amount * 1.8
            win_amount = round(win_amount, 2)
            db.update_balance(user_id, win_amount)
            db.conn.execute('UPDATE users SET total_won = total_won + ? WHERE user_id = ?',
                           (win_amount, user_id))
            db.add_transaction(user_id, 'game_win', win_amount, f'Выигрыш в игре Дайс')
            result_text = f"<b>🎲 Победа!</b>\n\n<b>{dice_text}</b>\n<b>💰 Выигрыш: {win_amount} $</b>"
        else:
            db.add_transaction(user_id, 'game_lose', 0, f'Проигрыш в игре Дайс')
            result_text = f"<b>🎲 Проигрыш</b>\n\n<b>{dice_text}</b>\n<b>💸 Потеряно: {bet_amount} $</b>"

        await update.message.reply_text(
            result_text,
            parse_mode='HTML'
        )

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат аргументов!</b>", parse_mode="HTML")

async def create_duel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user

    if update.effective_chat.id != CASINO_CHAT_ID:
        await update.message.reply_text("❌ <b>Эта команда доступна только в чате казино!</b>", parse_mode='HTML')
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ <b>Использование: /cg (сумма ставки)</b>", parse_mode='HTML')
        return

    try:
        amount = float(context.args[0])

        if amount < 0.1:
            await update.message.reply_text("❌ <b>Минимальная ставка 0.1$!</b>", parse_mode='HTML')
            return

        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < amount:
            await update.message.reply_text("❌ <b>Недостаточно средств!</b>", parse_mode='HTML')
            return

        db.update_balance(user_id, -amount)
        db.add_transaction(user_id, 'duel_bet', -amount, f'Ставка на дуэль')

        duel_id = db.create_duel(user_id, amount)

        await update.message.reply_text(
            f"<b>[🎲] Игра {duel_id} создана! ⚔️</b>\n\n"
            f"<b>[💎] Ставка - {amount}$</b>\n"
            f"<b>[🎲] Режим - кубик 🎲</b>\n\n"
            f"<b>✅ #1 Игрок - {user.username or user.first_name}</b>\n"
            f"<b>#2 Игрок -</b>",
            reply_markup=get_duel_join_keyboard(duel_id),
            parse_mode='HTML'
        )

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат суммы!</b>", parse_mode='HTML')

async def join_duel_callback(query, context, duel_id: int):
    user_id = query.from_user.id
    user = query.from_user

    duel = db.get_duel(duel_id)
    if not duel or duel[4] != 'waiting':
        await query.answer("❌ <b>Дуэль не найдена или уже начата!</b>", show_alert=True)
        return

    if duel[1] == user_id:
        await query.answer("❌ <b>Нельзя присоединиться к своей дуэли!</b>", show_alert=True)
        return

    user_data = db.get_user(user_id)
    if not user_data or user_data[2] < duel[3]:
        await query.answer("❌ <b>Недостаточно средств!</b>", show_alert=True)
        return

    db.update_balance(user_id, -duel[3])
    db.add_transaction(user_id, 'duel_bet', -duel[3], f'Ставка на дуэль #{duel_id}')

    if db.join_duel(duel_id, user_id):
        creator_data = db.get_user(duel[1])
        creator_name = creator_data[1] if creator_data else str(duel[1])

        await query.edit_message_text(
            f"<b>[🎲] Игра {duel_id} создана! ⚔️</b>\n\n"
            f"<b>[💎] Ставка - {duel[3]}$</b>\n"
            f"<b>[🎲] Режим - кубик 🎲</b>\n\n"
            f"<b>✅ #1 Игрок - {creator_name}</b>\n"
            f"<b>✅ #2 Игрок - {user.username or user.first_name}</b>\n\n"
            f"<b>✅ Дуэль начинается…</b>",
            parse_mode='HTML'
        )

        await start_duel(context, duel_id)
    else:
        await query.answer("❌ <b>Не удалось присоединиться к дуэли!</b>", show_alert=True)

async def start_duel(context: ContextTypes.DEFAULT_TYPE, duel_id: int):
    duel = db.get_duel(duel_id)
    if not duel or duel[4] != 'active':
        return

    creator_id = duel[1]
    joiner_id = duel[2]
    amount = duel[3]

    creator_dice_message = await context.bot.send_dice(chat_id=CASINO_CHAT_ID, emoji="🎲")
    creator_dice = creator_dice_message.dice.value

    await asyncio.sleep(2)

    joiner_dice_message = await context.bot.send_dice(chat_id=CASINO_CHAT_ID, emoji="🎲")
    joiner_dice = joiner_dice_message.dice.value

    db.update_duel_dice(duel_id, creator_id, creator_dice)
    db.update_duel_dice(duel_id, joiner_id, joiner_dice)

    if creator_dice > joiner_dice:
        winner_id = creator_id
    elif joiner_dice > creator_dice:
        winner_id = joiner_id
    else:
        db.update_balance(creator_id, amount)
        db.update_balance(joiner_id, amount)
        db.add_transaction(creator_id, 'duel_draw', amount, f'Ничья в дуэли #{duel_id}')
        db.add_transaction(joiner_id, 'duel_draw', amount, f'Ничья в дуэли #{duel_id}')
        db.complete_duel(duel_id, 0)

        await context.bot.send_message(
            chat_id=CASINO_CHAT_ID,
            text=f"<b>[🎲] Игра {duel_id} завершена [{creator_dice}:{joiner_dice}] ⚔️</b>\n\n"
                 f"<b>🗡 Дуэль - {duel[1]} ⚔️ {duel[2]}</b>\n"
                 f"<b>⚡️Ничья! Средства возвращены игрокам.</b>",
            parse_mode='HTML'
        )
        return

    win_amount = amount * 1.8
    db.update_balance(winner_id, win_amount)
    db.add_transaction(winner_id, 'duel_win', win_amount, f'Победа в дуэли #{duel_id}')
    db.complete_duel(duel_id, winner_id)

    winner_data = db.get_user(winner_id)
    winner_name = winner_data[1] if winner_data else str(winner_id)

    await context.bot.send_message(
        chat_id=CASINO_CHAT_ID,
        text=f"<b>[🎲] Игра {duel_id} завершена [{creator_dice}:{joiner_dice}] ⚔️</b>\n\n"
             f"<b>🗡 Дуэль - {duel[1]} ⚔️ {duel[2]}</b>\n"
             f"<b>⚡️Игрок {winner_name} выиграл {win_amount}$</b>",
        parse_mode='HTML'
    )

async def create_blackjack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user

    if update.effective_chat.id != CASINO_CHAT_ID:
        await update.message.reply_text("❌ <b>Эта команда доступна только в чате казино!</b>", parse_mode='HTML')
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ <b>Использование: /21 (сумма ставки)</b>", parse_mode='HTML')
        return

    try:
        amount = float(context.args[0])

        if amount < 0.2:
            await update.message.reply_text("❌ <b>Минимальная ставка 0.2$!</b>", parse_mode='HTML')
            return

        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < amount:
            await update.message.reply_text("❌ <b>Недостаточно средств!</b>", parse_mode='HTML')
            return

        db.update_balance(user_id, -amount)
        db.add_transaction(user_id, 'blackjack_bet', -amount, f'Ставка на блэкджек')

        game_id = db.create_blackjack_game(user_id, amount)

        await update.message.reply_text(
            f"<b>🃏 Игра 21 (Blackjack) [<code>#{game_id}</code>] создана!</b>\n\n"
            f"<b>💸 Ставка: {amount}$</b>\n\n"
            f"<b>👤 Игрок 1: {user.username or user.first_name}</b>\n"
            f"<b>⏳ Ждём второго игрока...</b>",
            reply_markup=get_blackjack_join_keyboard(game_id),
            parse_mode='HTML'
        )

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат суммы!</b>", parse_mode='HTML')

async def join_blackjack_callback(query, context, game_id: int):
    user_id = query.from_user.id
    user = query.from_user

    game = db.get_blackjack_game(game_id)
    if not game or game[4] != 'waiting':
        await query.answer("❌ <b>Игра не найдена или уже начата!</b>", show_alert=True)
        return

    if game[1] == user_id:
        await query.answer("❌ <b>Нельзя присоединиться к своей игре!</b>", show_alert=True)
        return

    user_data = db.get_user(user_id)
    if not user_data or user_data[2] < game[3]:
        await query.answer("❌ <b>Недостаточно средств!</b>", show_alert=True)
        return

    db.update_balance(user_id, -game[3])
    db.add_transaction(user_id, 'blackjack_bet', -game[3], f'Ставка на блэкджек #{game_id}')

    if db.join_blackjack_game(game_id, user_id):
        deck = DECK.copy()
        random.shuffle(deck)

        creator_cards = [deck.pop(), deck.pop()]
        joiner_cards = [deck.pop(), deck.pop()]

        creator_score = calculate_hand_score(creator_cards)
        joiner_score = calculate_hand_score(joiner_cards)

        current_turn = random.choice([game[1], user_id])

        db.update_blackjack_game(
            game_id=game_id,
            creator_cards=json.dumps(creator_cards),
            joiner_cards=json.dumps(joiner_cards),
            creator_score=creator_score,
            joiner_score=joiner_score,
            current_turn=current_turn,
            status='active'
        )

        creator_data = db.get_user(game[1])
        creator_name = creator_data[1] if creator_data else str(game[1])

        turn_name = creator_name if current_turn == game[1] else user.username or user.first_name

        creator_cards_formatted = format_cards_with_hidden(creator_cards, current_turn == user_id)
        joiner_cards_formatted = format_cards_with_hidden(joiner_cards, current_turn == game[1])

        await query.edit_message_text(
            f"<b>🃏 BlackJack</b>\n\n"
            f"<b>🎭 {creator_name} - {creator_cards_formatted}</b>\n"
            f"<b>🎭 {user.username or user.first_name} - {joiner_cards_formatted}</b>\n\n"
            f"<b>⚡️ Ход за: {turn_name}</b>",
            reply_markup=get_blackjack_game_keyboard(game_id),
            parse_mode='HTML'
        )
    else:
        await query.answer("❌ <b>Не удалось присоединиться к игре!</b>", show_alert=True)

async def cancel_blackjack_callback(query, context, game_id: int):
    user_id = query.from_user.id
    game = db.get_blackjack_game(game_id)

    if not game or game[4] != 'waiting':
        await query.answer("❌ <b>Игра не найдена или уже начата!</b>", show_alert=True)
        return

    if game[1] != user_id:
        await query.answer("❌ <b>Только создатель игры может отменить её!</b>", show_alert=True)
        return

    db.update_balance(user_id, game[3])
    db.add_transaction(user_id, 'blackjack_cancel', game[3], f'Отмена игры блэкджек #{game_id}')

    cursor = db.conn.cursor()
    cursor.execute('DELETE FROM blackjack_games WHERE id = ?', (game_id,))
    db.conn.commit()

    await query.edit_message_text(
        "❌ <b>Игра отменена создателем!</b>",
        parse_mode='HTML'
    )

async def blackjack_take_card_callback(query, context, game_id: int):
    user_id = query.from_user.id
    game = db.get_blackjack_game(game_id)

    if not game or game[4] != 'active':
        await query.answer("❌ <b>Игра не найдена или уже завершена!</b>", show_alert=True)
        return

    if game[9] != user_id:
        await query.answer("❌ <b>Сейчас не ваш ход!</b>", show_alert=True)
        return

    creator_cards = json.loads(game[5]) if game[5] else []
    joiner_cards = json.loads(game[6]) if game[6] else []

    all_cards = DECK.copy()
    used_cards = creator_cards + joiner_cards
    deck = [card for card in all_cards if card not in used_cards]
    random.shuffle(deck)

    new_card = deck.pop()

    if user_id == game[1]:
        creator_cards.append(new_card)
        new_cards_json = json.dumps(creator_cards)

        new_score = calculate_hand_score(creator_cards)
        db.update_blackjack_game(
            game_id=game_id,
            creator_cards=new_cards_json,
            creator_score=new_score
        )

        if new_score > 21:
            await finish_blackjack_game(context, game_id, game[2])
            return

        db.update_blackjack_game(
            game_id=game_id,
            current_turn=game[2]
        )

        turn_name = "Создатель" if game[2] == game[1] else "Игрок 2"

    else:
        joiner_cards.append(new_card)
        new_cards_json = json.dumps(joiner_cards)

        new_score = calculate_hand_score(joiner_cards)
        db.update_blackjack_game(
            game_id=game_id,
            joiner_cards=new_cards_json,
            joiner_score=new_score
        )

        if new_score > 21:
            await finish_blackjack_game(context, game_id, game[1])
            return

        db.update_blackjack_game(
            game_id=game_id,
            current_turn=game[1]
        )

        turn_name = "Создатель" if game[1] == game[1] else "Игрок 2"

    game = db.get_blackjack_game(game_id)
    creator_data = db.get_user(game[1])
    joiner_data = db.get_user(game[2])

    creator_name = creator_data[1] if creator_data else str(game[1])
    joiner_name = joiner_data[1] if joiner_data else str(game[2])

    current_turn_name = creator_name if game[9] == game[1] else joiner_name

    await query.edit_message_text(
        f"<b>🃏 BlackJack</b>\n\n"
        f"<b>🎭 {creator_name} - {format_cards_with_hidden(creator_cards, game[9] == game[2])}</b>\n"
        f"<b>🎭 {joiner_name} - {format_cards_with_hidden(joiner_cards, game[9] == game[1])}</b>\n\n"
        f"<b>⚡️ Ход за: {current_turn_name}</b>",
        reply_markup=get_blackjack_game_keyboard(game_id),
        parse_mode='HTML'
    )

async def blackjack_stand_callback(query, context, game_id: int):
    user_id = query.from_user.id
    game = db.get_blackjack_game(game_id)

    if not game or game[4] != 'active':
        await query.answer("❌ <b>Игра не найдена или уже завершена!</b>", show_alert=True)
        return

    if game[9] != user_id:
        await query.answer("❌ <b>Сейчас не ваш ход!</b>", show_alert=True)
        return

    next_turn = game[2] if user_id == game[1] else game[1]
    db.update_blackjack_game(
        game_id=game_id,
        current_turn=next_turn
    )

    if (user_id == game[1] and game[9] == game[2]) or (user_id == game[2] and game[9] == game[1]):
        creator_score = game[7] or 0
        joiner_score = game[8] or 0

        if creator_score > 21:
            winner_id = game[2]
        elif joiner_score > 21:
            winner_id = game[1]
        elif creator_score > joiner_score:
            winner_id = game[1]
        elif joiner_score > creator_score:
            winner_id = game[2]
        else:
            winner_id = 0

        await finish_blackjack_game(context, game_id, winner_id)
        return

    game = db.get_blackjack_game(game_id)
    creator_data = db.get_user(game[1])
    joiner_data = db.get_user(game[2])

    creator_name = creator_data[1] if creator_data else str(game[1])
    joiner_name = joiner_data[1] if joiner_data else str(game[2])

    current_turn_name = creator_name if game[9] == game[1] else joiner_name

    await query.edit_message_text(
        f"<b>🃏 BlackJack</b>\n\n"
        f"<b>🎭 {creator_name} - {format_cards_with_hidden(json.loads(game[5]) if game[5] else [], game[9] == game[2])}</b>\n"
        f"<b>🎭 {joiner_name} - {format_cards_with_hidden(json.loads(game[6]) if game[6] else [], game[9] == game[1])}</b>\n\n"
        f"<b>⚡️ Ход за: {current_turn_name}</b>",
        reply_markup=get_blackjack_game_keyboard(game_id),
        parse_mode='HTML'
    )

async def finish_blackjack_game(context: ContextTypes.DEFAULT_TYPE, game_id: int, winner_id: int):
    game = db.get_blackjack_game(game_id)
    if not game:
        return

    amount = game[3]
    creator_id = game[1]
    joiner_id = game[2]

    creator_data = db.get_user(creator_id)
    joiner_data = db.get_user(joiner_id)

    creator_name = creator_data[1] if creator_data else str(creator_id)
    joiner_name = joiner_data[1] if joiner_data else str(joiner_id)

    if winner_id == 0:
        db.update_balance(creator_id, amount)
        db.update_balance(joiner_id, amount)
        db.add_transaction(creator_id, 'blackjack_draw', amount, f'Ничья в блэкджеке #{game_id}')
        db.add_transaction(joiner_id, 'blackjack_draw', amount, f'Ничья в блэкджеке #{game_id}')

        result_text = f"<b>🤝 Ничья!</b>\n\n<b>💰 Средства возвращены обоим игрокам.</b>"
    else:
        win_amount = amount * 1.8
        db.update_balance(winner_id, win_amount)
        db.add_transaction(winner_id, 'blackjack_win', win_amount, f'Победа в блэкджеке #{game_id}')

        loser_id = joiner_id if winner_id == creator_id else creator_id
        loser_name = joiner_name if winner_id == creator_id else creator_name
        winner_name = creator_name if winner_id == creator_id else joiner_name

        result_text = f"<b>😔 {loser_name} проиграл!</b>\n\n<b>🏆 Победитель: {winner_name} (выигрыш: {win_amount}$)</b>"

    db.complete_blackjack_game(game_id, winner_id)

    await context.bot.send_message(
        chat_id=CASINO_CHAT_ID,
        text=result_text,
        parse_mode='HTML'
    )

async def create_giveaway_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user

    if update.effective_chat.id != CASINO_CHAT_ID:
        await update.message.reply_text("❌ <b>Эта команда доступна только в чате казино!</b>", parse_mode='HTML')
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ <b>Использование: /fast (сумма раздачи)</b>", parse_mode='HTML')
        return

    try:
        amount = float(context.args[0])

        if amount < 1:
            await update.message.reply_text("❌ <b>Минимальная сумма раздачи 1$!</b>", parse_mode='HTML')
            return

        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < amount:
            await update.message.reply_text("❌ <b>Недостаточно средств!</b>", parse_mode='HTML')
            return

        db.update_balance(user_id, -amount)
        db.add_transaction(user_id, 'giveaway', -amount, f'Создание раздачи')

        giveaway_id = db.create_giveaway(user_id, amount)

        await update.message.reply_text(
            f"<b>[🎁] Быстрая раздача от {user.username or user.first_name}</b>\n\n"
            f"<b>👥 Участники:</b>\n"
            f"<b>-</b>\n\n"
            f"<b>🎉 Приз раздачи → {amount}$</b>",
            reply_markup=get_giveaway_join_keyboard(giveaway_id),
            parse_mode='HTML'
        )

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат суммы!</b>", parse_mode='HTML')

async def join_giveaway_callback(query, context, giveaway_id: int):
    user_id = query.from_user.id
    user = query.from_user

    giveaway = db.get_giveaway(giveaway_id)
    if not giveaway or giveaway[3] != 'active':
        await query.answer("❌ <b>Раздача не найдена или завершена!</b>", show_alert=True)
        return

    if giveaway[1] == user_id:
        await query.answer("❌ <b>Нельзя присоединиться к своей раздаче!</b>", show_alert=True)
        return

    if db.join_giveaway(giveaway_id, user_id, user.username or user.first_name):
        giveaway = db.get_giveaway(giveaway_id)
        participants = json.loads(giveaway[5])

        participants_text = ""
        for i, participant in enumerate(participants, 1):
            participants_text += f"<b>- {participant['username']}</b>\n"

        for i in range(len(participants), 6):
            participants_text += f"<b>-</b>\n"

        if len(participants) >= 6:
            await query.edit_message_text(
                f"<b>[🎁] Быстрая раздача от {giveaway[1]}</b>\n\n"
                f"<b>👥 Участники:</b>\n"
                f"{participants_text}\n"
                f"<b>🎉 Приз раздачи → {giveaway[2]}$</b>\n\n"
                f"<b>✅ Набор участников завершен!</b>",
                reply_markup=get_giveaway_completed_keyboard(),
                parse_mode='HTML'
            )
            await start_giveaway(context, giveaway_id)
        else:
            await query.edit_message_text(
                f"<b>[🎁] Быстрая раздача от {giveaway[1]}</b>\n\n"
                f"<b>👥 Участники:</b>\n"
                f"{participants_text}\n"
                f"<b>🎉 Приз раздачи → {giveaway[2]}$</b>",
                reply_markup=get_giveaway_join_keyboard(giveaway_id),
                parse_mode='HTML'
            )
    else:
        await query.answer("❌ <b>Вы уже участвуете в этой раздаче!</b>", show_alert=True)

async def start_giveaway(context: ContextTypes.DEFAULT_TYPE, giveaway_id: int):
    giveaway = db.get_giveaway(giveaway_id)
    if not giveaway or giveaway[3] != 'active':
        return

    participants = json.loads(giveaway[5])

    dice_message = await context.bot.send_dice(chat_id=CASINO_CHAT_ID, emoji="🎲")
    dice_value = dice_message.dice.value

    winner_index = (dice_value - 1) % len(participants)
    winner = participants[winner_index]

    db.update_balance(winner['user_id'], giveaway[2])
    db.add_transaction(winner['user_id'], 'giveaway_win', giveaway[2], f'Победа в раздаче #{giveaway_id}')
    db.complete_giveaway(giveaway_id, winner['user_id'])

    await context.bot.send_message(
        chat_id=CASINO_CHAT_ID,
        text=f"<b>[🎉] розыгрыш {giveaway_id} завершен!</b>\n\n"
             f"<b>[🏆] победитель:</b>\n"
             f"<b>- {winner['username']}</b>\n\n"
             f"<b>[⚡] {winner['username']} выиграл {giveaway[2]}$</b>",
        parse_mode='HTML'
    )

async def reset_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ <b>Доступ запрещён!</b>", parse_mode='HTML')
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ <b>Использование: /o <user_id></b>\n"
            "Пример: /o 123456789",
            parse_mode='HTML'
        )
        return

    try:
        user_id = int(context.args[0])

        user_data = db.get_user(user_id)
        if not user_data:
            await update.message.reply_text("❌ <b>Пользователь не найден!</b>", parse_mode='HTML')
            return

        old_balance = user_data[2]

        db.update_balance(user_id, -old_balance)
        db.add_transaction(user_id, 'admin_reset', -old_balance, f'Обнуление баланса администратором {update.effective_user.id}')

        cursor = db.conn.cursor()
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        username_data = cursor.fetchone()
        username = username_data[0] if username_data else str(user_id)

        await update.message.reply_text(
            f"✅ <b>Баланс обнулен!</b>\n\n"
            f"👤 Пользователь: @{username}\n"
            f"💰 Старый баланс: {old_balance} $\n"
            f"🆔 ID: {user_id}",
            parse_mode='HTML'
        )

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат user_id!</b>", parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Ошибка: {str(e)}</b>", parse_mode='HTML')

async def handle_custom_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        bet_amount = float(update.message.text)
        if bet_amount < 0.2:
            await update.message.reply_text("❌ <b>Минимальная ставка 0.2$!</b>", parse_mode='HTML')
            return

        user_data = db.get_user(update.effective_user.id)
        if not user_data or user_data[2] < bet_amount:
            await update.message.reply_text("❌ <b>Недостаточно средств!</b>", parse_mode='HTML')
            return

        game_type = context.user_data.get('custom_bet_game')
        context.user_data['current_bet'] = bet_amount
        context.user_data['waiting_for_bet'] = False

        if game_type == 'mines':
            await update.message.reply_text(
                f"💣 <b>Мины 5x5</b>\n\n🎯 Ставка: <b>{bet_amount} $</b>\n💣 Выбери количество мин (2-23):",
                reply_markup=get_mines_count_keyboard(),
                parse_mode='HTML'
            )
        elif game_type == 'tower':
            await update.message.reply_text(
                f"🏰 <b>Башня 6x5</b>\n\n🎯 Ставка: <b>{bet_amount} $</b>\n💣 Выбери количество мин:",
                reply_markup=get_tower_mines_keyboard(),
                parse_mode='HTML'
            )
        elif game_type == 'dice':
            await update.message.reply_text(
                f"🎲 <b>Дайс</b>\n\n🎯 Ставка: <b>{bet_amount} $</b>\n🎮 Выбери режим игры:",
                reply_markup=get_dice_mode_keyboard(),
                parse_mode='HTML'
            )

    except ValueError:
        await update.message.reply_text("❌ <b>Введите корректную сумму!</b>", parse_mode="HTML")

async def handle_custom_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        if amount < 0.2:
            await update.message.reply_text("❌ <b>Минимальная сумма пополнения 0.2$!</b>", parse_mode='HTML')
            return

        context.user_data['waiting_for_deposit'] = False
        context.user_data['deposit_amount'] = amount

        await create_cryptobot_invoice(update, context, amount)

    except ValueError:
        await update.message.reply_text("❌ <b>Введите корректную сумму!</b>", parse_mode='HTML')

async def handle_custom_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        if amount < 0.2:
            await update.message.reply_text("❌ <b>Минимальная сумма вывода 0.2$!</b>", parse_mode='HTML')
            return

        user_data = db.get_user(update.effective_user.id)
        if not user_data or user_data[2] < amount:
            await update.message.reply_text("❌ <b>Недостаточно средств!</b>", parse_mode='HTML')
            return

        if user_data[3] <= 0:
            await update.message.reply_text("❌ <b>Для вывода необходимо сделать хотя бы одну ставку!</b>", parse_mode='HTML')
            return

        context.user_data['waiting_for_withdrawal'] = False
        await create_withdrawal_request(update, context, amount)

    except ValueError:
        await update.message.reply_text("❌ <b>Введите корректную сумму!</b>", parse_mode='HTML')

async def handle_deposit_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amounts_text = update.message.text
        amounts = [amount.strip() for amount in amounts_text.split(',')]
        for amount in amounts:
            float(amount)

        db.set_setting('deposit_amounts', amounts_text)
        context.user_data['waiting_for_deposit_settings'] = False

        await update.message.reply_text(
            f"✅ <b>Настройки пополнений обновлены!</b>\n\nТеперь доступны суммы: {amounts_text}",
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат! Введите суммы через запятую (например: 0.2,1,5,10,50,100)</b>", parse_mode="HTML")

async def create_cryptobot_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: float):
    user_id = update.effective_user.id
    user = update.effective_user

    try:
        headers = {
            'Crypto-Pay-API-Token': CRYPTO_BOT_TOKEN,
            'Content-Type': 'application/json'
        }

        data = {
            'asset': 'USDT',
            'amount': str(amount),
            'description': f'Пополнение баланса на {amount}$',
            'hidden_message': f'ID пользователя: {user_id}',
            'paid_btn_name': 'callback',
            'paid_btn_url': f'https://t.me/darkedcasino_bot',
            'payload': str(user_id)
        }

        response = requests.post(
            'https://pay.crypt.bot/api/createInvoice',
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                invoice_url = result['result']['pay_url']
                invoice_id = result['result']['invoice_id']

                cursor = db.conn.cursor()
                cursor.execute(
                    'INSERT INTO deposits (user_id, amount, status, invoice_url, invoice_id, currency) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, amount, 'pending', invoice_url, str(invoice_id), 'USDT')
                )
                db.conn.commit()

                db.add_transaction(user_id, 'deposit', amount, f'Создан счет CryptoBot для пополнения #{invoice_id}')

                if update.message:
                    await update.message.reply_text(
                        f"<b>✅ Счет создан на сумму {amount} USDT (CryptoBot)</b>",
                        reply_markup=get_deposit_invoice_keyboard(invoice_url),
                        parse_mode='HTML'
                    )
                else:
                    await update.callback_query.edit_message_text(
                        f"<b>✅ Счет создан на сумму {amount} USDT (CryptoBot)</b>",
                        reply_markup=get_deposit_invoice_keyboard(invoice_url),
                        parse_mode='HTML'
                    )
            else:
                error_msg = result.get('error', {}).get('name', 'Неизвестная ошибка')
                error_text = f"❌ <b>Ошибка при создании счета: {error_msg}</b>"
                if update.message:
                    await update.message.reply_text(error_text, parse_mode='HTML')
                else:
                    await update.callback_query.edit_message_text(error_text, parse_mode='HTML')
        else:
            error_text = f"❌ <b>Ошибка подключения к платежной системе! Статус: {response.status_code}</b>"
            if update.message:
                await update.message.reply_text(error_text, parse_mode='HTML')
            else:
                await update.callback_query.edit_message_text(error_text, parse_mode='HTML')

    except requests.exceptions.RequestException as e:
        error_text = f"❌ <b>Ошибка сети при создании счета: {str(e)}</b>"
        if update.message:
            await update.message.reply_text(error_text, parse_mode='HTML')
        else:
            await update.callback_query.edit_message_text(error_text, parse_mode='HTML')
    except Exception as e:
        error_text = f"❌ <b>Неожиданная ошибка при создании счета: {str(e)}</b>"
        if update.message:
            await update.message.reply_text(error_text, parse_mode='HTML')
        else:
            await update.callback_query.edit_message_text(error_text, parse_mode='HTML')

async def create_withdrawal_request(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: float):
    user_id = update.effective_user.id
    user = update.effective_user

    cursor = db.conn.cursor()
    cursor.execute(
        'INSERT INTO withdrawals (user_id, amount, status) VALUES (?, ?, ?)',
        (user_id, amount, 'pending')
    )
    withdrawal_id = cursor.lastrowid
    db.conn.commit()

    db.update_balance(user_id, -amount)
    db.add_transaction(user_id, 'withdrawal_request', -amount, f'Заявка на вывод #{withdrawal_id}')

    admin_message = f'📋 <b>Заявка на вывод #{withdrawal_id}</b>\n\n👤 <b>Пользователь:</b> @{user.username or user.first_name}\n💰 <b>Сумма:</b> {amount} $\n🆔 <b>ID:</b> {user_id}'

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message,
            reply_markup=get_withdrawal_approve_keyboard(withdrawal_id),
            parse_mode='HTML'
        )

        if update.message:
            await update.message.reply_text(
                f"<b>Заявка на вывод успешно создана ✅</b>\n\n"
                f"<b>⚙️ Ожидайте до 48 часов</b>\n"
                f"<b>💰 Сумма: {amount} $</b>",
                reply_markup=get_back_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.callback_query.edit_message_text(
                f"<b>Заявка на вывод успешно создана ✅</b>\n\n"
                f"<b>⚙️ Ожидайте до 48 часов</b>\n"
                f"<b>💰 Сумма: {amount} $</b>",
                reply_markup=get_back_keyboard(),
                parse_mode='HTML'
            )
    except Exception as e:
        error_text = "❌ <b>Ошибка при создании заявки!</b>"
        if update.message:
            await update.message.reply_text(error_text, parse_mode='HTML')
        else:
            await update.callback_query.edit_message_text(error_text, parse_mode='HTML')

async def create_withdrawal_request_callback(query, context, amount: float):
    user_id = query.from_user.id
    user = query.from_user

    cursor = db.conn.cursor()
    cursor.execute(
        'INSERT INTO withdrawals (user_id, amount, status) VALUES (?, ?, ?)',
        (user_id, amount, 'pending')
    )
    withdrawal_id = cursor.lastrowid
    db.conn.commit()

    db.update_balance(user_id, -amount)
    db.add_transaction(user_id, 'withdrawal_request', -amount, f'Заявка на вывод #{withdrawal_id}')

    admin_message = f'📋 <b>Заявка на вывод #{withdrawal_id}</b>\n\n👤 <b>Пользователь:</b> @{user.username or user.first_name}\n💰 <b>Сумма:</b> {amount} $\n🆔 <b>ID:</b> {user_id}'

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message,
            reply_markup=get_withdrawal_approve_keyboard(withdrawal_id),
            parse_mode='HTML'
        )

        await query.edit_message_text(
            f"<b>Заявка на вывод успешно создана ✅</b>\n\n"
            f"<b>⚙️ Ожидайте до 48 часов</b>\n"
            f"<b>💰 Сумма: {amount} $</b>",
            reply_markup=get_back_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        await query.edit_message_text("❌ <b>Ошибка при создании заявки!</b>", parse_mode='HTML')

async def approve_withdrawal(query, context, withdrawal_id: int):
    cursor = db.conn.cursor()
    cursor.execute('SELECT * FROM withdrawals WHERE id = ?', (withdrawal_id,))
    withdrawal = cursor.fetchone()

    if not withdrawal:
        await query.answer("❌ <b>Заявка не найдена!</b>", show_alert=True)
        return

    user_id = withdrawal[1]
    amount = withdrawal[2]

    cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()
    username = user_data[0] if user_data else str(user_id)

    try:
        headers = {
            'Crypto-Pay-API-Token': CRYPTO_BOT_TOKEN,
            'Content-Type': 'application/json'
        }

        data = {
            'asset': 'USDT',
            'amount': str(amount),
            'pin_to_user_id': user_id,
        }

        response = requests.post(
            'https://pay.crypt.bot/api/createCheck',
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                check_data = result['result']
                check_url = check_data.get('bot_check_url')
                check_id = check_data.get('id')

                cursor.execute(
                    'UPDATE withdrawals SET status = ?, approved_by = ?, check_url = ? WHERE id = ?',
                    ('approved', query.from_user.id, check_url, withdrawal_id)
                )
                db.conn.commit()

                db.add_transaction(user_id, 'withdrawal_approved', -amount, f'Вывод одобрен #{withdrawal_id}, чек #{check_id}')

                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"<b>✅ Ваш запрос на вывод одобрен!</b>\n\n"
                             f"<b>💳 Сумма: {amount} USDT</b>\n"
                             f"<b>🧾 Чек: {check_url}</b>",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"Ошибка отправки пользователю: {e}")

                await query.edit_message_text(
                    f"✅ <b>Заявка на вывод одобрена</b>\n\n"
                    f"💰 Сумма: <b>{amount} $</b>\n"
                    f"📋 Номер: <b>#{withdrawal_id}</b>\n"
                    f"👤 Пользователь: <b>@{username}</b>\n"
                    f"🔗 Чек создан: <b>{check_url}</b>\n\n"
                    f"Чек отправлен пользователю.",
                    parse_mode='HTML'
                )

            else:
                error_msg = result.get('error', {}).get('name', 'Неизвестная ошибка')
                db.update_balance(user_id, amount)
                db.add_transaction(user_id, 'withdrawal_error', amount, f'Ошибка создания чека: {error_msg}')

                cursor.execute(
                    'UPDATE withdrawals SET status = ? WHERE id = ?',
                    ('failed', withdrawal_id)
                )
                db.conn.commit()

                await query.answer(f"❌ <b>Ошибка при создании чека: {error_msg}</b>", show_alert=True)

        else:
            db.update_balance(user_id, amount)
            db.add_transaction(user_id, 'withdrawal_error', amount, 'Ошибка подключения к CryptoBot')

            cursor.execute(
                'UPDATE withdrawals SET status = ? WHERE id = ?',
                ('failed', withdrawal_id)
            )
            db.conn.commit()

            await query.answer("❌ <b>Ошибка подключения к платежной системе!</b>", show_alert=True)

    except Exception as e:
        db.update_balance(user_id, amount)
        db.add_transaction(user_id, 'withdrawal_error', amount, f'Ошибка обработки: {str(e)}')

        cursor.execute(
            'UPDATE withdrawals SET status = ? WHERE id = ?',
            ('failed', withdrawal_id)
        )
        db.conn.commit()

        await query.answer(f"❌ <b>Ошибка при обработке заявки: {str(e)}</b>", show_alert=True)

async def reject_withdrawal(query, context, withdrawal_id: int):
    cursor = db.conn.cursor()
    cursor.execute('SELECT * FROM withdrawals WHERE id = ?', (withdrawal_id,))
    withdrawal = cursor.fetchone()

    if not withdrawal:
        await query.answer("❌ <b>Заявка не найдена!</b>", show_alert=True)
        return

    user_id = withdrawal[1]
    amount = withdrawal[2]

    db.update_balance(user_id, amount)
    db.add_transaction(user_id, 'withdrawal_rejected', amount, f'Вывод отклонен #{withdrawal_id}')

    cursor.execute(
        'UPDATE withdrawals SET status = ? WHERE id = ?',
        ('rejected', withdrawal_id)
    )
    db.conn.commit()

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ <b>Заявка на вывод отклонена</b>\n\n💰 Сумма: <b>{amount} $</b> возвращена на баланс.",
            parse_mode='HTML'
        )
    except:
        pass

    await query.edit_message_text(
        f"❌ <b>Заявка на вывод отклонена</b>\n\n"
        f"💰 Сумма: <b>{amount} $</b>\n"
        f"📋 Номер: <b>#{withdrawal_id}</b>\n"
        f"👤 Пользователь: <b>{user_id}</b>",
        parse_mode='HTML'
    )

async def check_payments(context: ContextTypes.DEFAULT_TYPE):
    try:
        cursor = db.conn.cursor()
        cursor.execute('SELECT id, user_id, amount, invoice_id FROM deposits WHERE status = "pending" AND invoice_id IS NOT NULL')
        pending_deposits = cursor.fetchall()

        for dep_id, user_id, amount, invoice_id in pending_deposits:
            try:
                headers = {
                    'Crypto-Pay-API-Token': CRYPTO_BOT_TOKEN,
                    'Content-Type': 'application/json'
                }

                response = requests.get(
                    f'https://pay.crypt.bot/api/getInvoices',
                    headers=headers,
                    params={'invoice_ids': invoice_id},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok') and data['result']['items']:
                        invoice = data['result']['items'][0]
                        if invoice['status'] == 'paid':
                            db.update_balance(user_id, amount)
                            cursor.execute('UPDATE deposits SET status = "completed" WHERE id = ?', (dep_id,))
                            db.conn.commit()

                            db.add_transaction(user_id, 'deposit_success', amount, f'Пополнение #{dep_id}')

                            try:
                                await context.bot.send_message(
                                    chat_id=user_id,
                                    text=f"<b>✅ пополнение одобрено!😋</b>\n\n<blockquote><b>💸 На ваш баланс было начислено {amount}$!</b></blockquote>\n\n<b>Спасибо огромное за то что выбирайте нас! ❤️</b>",
                                    parse_mode='HTML'
                                )
                            except Exception as e:
                                print(f"❌ Ошибка отправки уведомления пользователю {user_id}: {e}")
            except Exception as e:
                print(f"❌ Ошибка проверки платежа {dep_id}: {e}")
    except Exception as e:
        print(f"❌ Общая ошибка в check_payments: {e}")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ <b>Доступ запрещён!</b>", parse_mode='HTML')
        return

    await update.message.reply_text(
        "<b>Админ-панель</b>",
        reply_markup=get_admin_keyboard(),
        parse_mode='HTML'
    )

async def give_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ <b>Доступ запрещён!</b>", parse_mode='HTML')
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ <b>Использование: /givebalance <user_id> <amount></b>\n"
            "Пример: /givebalance 123456789 100",
            parse_mode='HTML'
        )
        return

    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])

        if amount <= 0:
            await update.message.reply_text("❌ <b>Сумма должна быть больше 0!</b>", parse_mode='HTML')
            return

        user_data = db.get_user(user_id)
        if not user_data:
            await update.message.reply_text("❌ <b>Пользователь не найден!</b>", parse_mode='HTML')
            return

        db.update_balance(user_id, amount)
        db.add_transaction(user_id, 'admin_add', amount, f'Начисление администратором {update.effective_user.id}')

        cursor = db.conn.cursor()
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        username_data = cursor.fetchone()
        username = username_data[0] if username_data else str(user_id)

        await update.message.reply_text(
            f"✅ <b>Баланс успешно пополнен!</b>\n\n"
            f"👤 Пользователь: @{username}\n"
            f"💰 Сумма: {amount} $\n"
            f"🆔 ID: {user_id}",
            parse_mode='HTML'
        )

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 <b>Вам начислены средства!</b>\n\n"
                     f"💰 Сумма: <b>{amount} $</b>\n"
                     f"💳 Новый баланс: <b>{user_data[2] + amount} $</b>",
                parse_mode='HTML'
            )
        except Exception as e:
            await update.message.reply_text(f"✅ <b>Баланс пополнен, но не удалось уведомить пользователя: {e}</b>", parse_mode='HTML')

    except ValueError:
        await update.message.reply_text("❌ <b>Неверный формат аргументов! Используйте: /givebalance <user_id> <amount></b>", parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Ошибка: {str(e)}</b>", parse_mode='HTML')

async def show_admin_stats(query, context):
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ <b>Доступ запрещён!</b>", show_alert=True)
        return

    cursor = db.conn.cursor()
    cursor.execute('SELECT COUNT(*), SUM(balance), SUM(total_bet), SUM(total_won) FROM users')
    total_users, total_balance, total_bet, total_won = cursor.fetchone()

    cursor.execute('SELECT COUNT(*) FROM deposits WHERE status = "completed"')
    total_deposits = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM withdrawals WHERE status = "approved"')
    total_withdrawals = cursor.fetchone()[0]

    await query.edit_message_text(
        f"<b>Статистика бота</b>\n\n"
        f"<b>Пользователей:</b> <code>{total_users or 0}</code>\n"
        f"<b>Баланс пользователей:</b> <code>{total_balance or 0:.2f} $</code>\n"
        f"<b>Всего ставок:</b> <code>{total_bet or 0:.2f} $</code>\n"
        f"<b>Всего выиграно:</b> <code>{total_won or 0:.2f} $</code>\n"
        f"<b>Депозитов:</b> <code>{total_deposits}</code>\n"
        f"<b>Выводов:</b> <code>{total_withdrawals}</code>",
        reply_markup=get_admin_keyboard(),
        parse_mode='HTML'
    )

async def show_admin_users(query, context):
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ <b>Доступ запрещён!</b>", show_alert=True)
        return

    cursor = db.conn.cursor()
    cursor.execute('SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT 10')
    users = cursor.fetchall()

    text = "<b>Топ-10 по балансу</b>\n\n"
    for i, (uid, username, balance) in enumerate(users, 1):
        text += f"<b>{i}.</b> @{username or uid} — <code>{balance:.2f} $</code>\n"

    await query.edit_message_text(
        text,
        reply_markup=get_admin_keyboard(),
        parse_mode='HTML'
    )

async def show_admin_withdrawals(query, context):
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ <b>Доступ запрещён!</b>", show_alert=True)
        return

    cursor = db.conn.cursor()
    cursor.execute('SELECT id, user_id, amount, status FROM withdrawals ORDER BY created_at DESC LIMIT 10')
    withdrawals = cursor.fetchall()

    text = "<b>Последние 10 заявок на вывод</b>\n\n"
    for wid, uid, amount, status in withdrawals:
        status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌", "failed": "❗"}.get(status, "❓")
        text += f"{status_emoji} <b>#{wid}</b> — <b>{amount} $</b> — <code>@{uid}</code>\n"

    await query.edit_message_text(
        text,
        reply_markup=get_admin_keyboard(),
        parse_mode='HTML'
    )

async def show_admin_settings(query, context):
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ <b>Доступ запрещён!</b>", show_alert=True)
        return

    welcome_msg = db.get_setting('welcome_message', DEFAULT_SETTINGS['welcome_message'])

    await query.edit_message_text(
        f"<b>Настройки бота</b>\n\n"
        f"<b>Приветственное сообщение:</b>\n<code>{welcome_msg[:500]}{'...' if len(welcome_msg) > 500 else ''}</code>",
        reply_markup=get_admin_keyboard(),
        parse_mode='HTML'
    )

async def show_deposit_settings(query, context):
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ <b>Доступ запрещён!</b>", show_alert=True)
        return

    current_amounts = db.get_setting('deposit_amounts', DEFAULT_SETTINGS['deposit_amounts'])

    context.user_data['waiting_for_deposit_settings'] = True

    await query.edit_message_text(
        f"<b>Настройка сумм пополнения</b>\n\n"
        f"Текущие суммы: <code>{current_amounts}</code>\n\n"
        f"Введите новые суммы через запятую (например: 0.2,1,5,10,50,100):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Назад", callback_data="back_main")]]),
        parse_mode='HTML'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data == "back_main":
        welcome_message = db.get_setting('welcome_message', DEFAULT_SETTINGS['welcome_message'])
        await query.edit_message_text(
            welcome_message,
            reply_markup=get_welcome_keyboard(),
            parse_mode='HTML'
        )
        return

    elif data == "back_games":
        await query.edit_message_text(
            "🎮 <b>Выберите где хотите играть:</b>",
            reply_markup=get_games_keyboard(),
            parse_mode='HTML'
        )
        return

    elif data == "play_in_bot":
        balance = get_balance_rounded(query.from_user.id)
        await query.edit_message_text(
            f"ᴅᴀʀᴋᴇᴅ ɢᴀᴍᴇs [🎲]\n\n<b>Выберете режим игры!</b> 🎮\n<blockquote><b>💰 Ваш баланс: {balance} $</b></blockquote>",
            reply_markup=get_games_bot_keyboard(),
            parse_mode='HTML'
        )
        return

    elif data == "play_in_chat":
        await query.edit_message_text(
            "⚡️ Вступай в игровой чат DarkedCasino!\n\n<blockquote><b>Играй в игры вместе с друзьями! Делись своими выигрышами и выводами 💎</b></blockquote>\n<b>└ Делай ставку и испытай удачу!\n└ получай фриспин по команде /spin</b>",
            reply_markup=get_chat_keyboard(),
            parse_mode='HTML'
        )
        return

    elif data == "back_games_bot":
        balance = get_balance_rounded(query.from_user.id)
        await query.edit_message_text(
            f"ᴅᴀʀᴋᴇᴅ ɢᴀᴍᴇs [🎲]\n\n<b>Выберете режим игры!</b> 🎮\n<blockquote><b>💰 Ваш баланс: {balance} $</b></blockquote>",
            reply_markup=get_games_bot_keyboard(),
            parse_mode='HTML'
        )
        return

    elif data == "back_profile":
        await show_profile_callback(query, context)
        return

    elif data == "back_mines_bet":
        balance = get_balance_rounded(query.from_user.id)
        await query.edit_message_text(
            f"<b>Введите сумму ставки ✅</b>\n\n<b>Минимум: $0.20</b>\n<blockquote><b>💎 Ваш баланс: <code>{balance}</code> $</b></blockquote>",
            reply_markup=get_mines_bet_keyboard(user_id),
            parse_mode='HTML'
        )
        return

    elif data == "back_tower_bet":
        balance = get_balance_rounded(query.from_user.id)
        await query.edit_message_text(
            f"<b>Введите сумму ставки ✅</b>\n\n<b>Минимум: $0.20</b>\n<blockquote><b>💎 Ваш баланс: <code>{balance}</code> $</b></blockquote>",
            reply_markup=get_tower_bet_keyboard(user_id),
            parse_mode='HTML'
        )
        return

    elif data == "back_dice_bet":
        balance = get_balance_rounded(query.from_user.id)
        await query.edit_message_text(
            f"<b>Введите сумму ставки ✅</b>\n\n<b>Минимум: $0.20</b>\n<blockquote><b>💎 Ваш баланс: <code>{balance}</code> $</b></blockquote>",
            reply_markup=get_dice_bet_keyboard(user_id),
            parse_mode='HTML'
        )
        return

    elif data == "back_dice_mode":
        bet_amount = context.user_data.get('current_bet', 10)
        await query.edit_message_text(
            f"🎲 <b>Дайс</b>\n\n🎯 Ставка: <b>{bet_amount} $</b>\n🎮 Выбери режим игры:",
            reply_markup=get_dice_mode_keyboard(),
            parse_mode='HTML'
        )
        return

    elif data in ["mines_disabled", "tower_disabled"]:
        await query.answer("ℹ️ Эта ячейка недоступна", show_alert=False)
        return

    # ВАЖНОЕ ИСПРАВЛЕНИЕ: Добавляем обработку cashout ДО условий с "mine_" и "tower_click_"
    elif data == "mines_cashout":
        if not game_sessions.can_click(user_id):
            await query.answer("⏳ Подождите немного перед следующим действием!", show_alert=True)
            return

        session = game_sessions.get_session(user_id)
        if not session or session.get('state') != 'playing':
            await query.answer("❌ Нет активной игры!", show_alert=True)
            return

        opened_cells = session.get('opened_cells', [])
        if not opened_cells:
            await query.answer("❌ Сначала откройте хотя бы одну ячейку!", show_alert=True)
            return

        bet = session.get('bet')
        mines_count = session.get('mines_count')
        coefficient = get_mines_coefficient(mines_count, len(opened_cells))
        win_amount = round(bet * coefficient, 2)

        db.update_balance(user_id, win_amount)
        db.conn.execute('UPDATE users SET total_bet = total_bet + ?, total_won = total_won + ?, games_played = games_played + 1 WHERE user_id = ?',
                       (bet, win_amount, user_id))
        db.add_transaction(user_id, 'win', win_amount, f'Mines Win x{coefficient}')
        game_sessions.end_session(user_id)

        await query.edit_message_text(
            f"""<b>💣 Мины · {mines_count}</b>
<i>💰 Выигрыш</i> - <code>{bet}$</code> → <b>{win_amount}$ | x{coefficient}</b>

<blockquote><b>✅ Вы забрали {win_amount}$! 🥳</b></blockquote>

<code>🎲 Чтобы сыграть: /mines 0.2 2</code> ⎙
<blockquote>🧨 Игровой бот » @DarkedCasino_bot</blockquote>""",
            parse_mode='HTML',
            reply_markup=get_mines_game_keyboard(opened_cells, session.get('mines_positions'), False, 0, True)
        )
        return

    elif data == "tower_cashout":
        if not game_sessions.can_click(user_id):
            await query.answer("⏳ Подождите немного перед следующим действием!", show_alert=True)
            return

        session = game_sessions.get_session(user_id)
        if not session or session.get('state') != 'playing':
            await query.answer("❌ Нет активной игры!", show_alert=True)
            return

        current_level = session.get('current_level', 0)
        if current_level == 0:
            await query.answer("❌ Сначала пройдите хотя бы один уровень!", show_alert=True)
            return

        bet = session.get('bet')
        mines_count = session.get('mines_count')
        coefficient = TOWER_COEFFICIENTS[mines_count][current_level - 1]
        win_amount = round(bet * coefficient, 2)

        db.update_balance(user_id, win_amount)
        db.conn.execute('UPDATE users SET total_bet = total_bet + ?, total_won = total_won + ?, games_played = games_played + 1 WHERE user_id = ?',
                       (bet, win_amount, user_id))
        db.add_transaction(user_id, 'win', win_amount, f'Tower Win x{coefficient}')
        game_sessions.end_session(user_id)

        await query.edit_message_text(
            f"""<b>[🗼] Башня · [{mines_count} × 💣] завершена <code>#{random.randint(1000, 9999)}</code> ✅</b>

<blockquote><b>💎 Ставка - {bet}$</b>
<b>💣 Мин в ряду - {mines_count} / 6×5</b></blockquote>

<blockquote><b>💸 Вы забрали выигрыш: {win_amount}$ | {coefficient}x</b></blockquote>""",
            parse_mode='HTML',
            reply_markup=get_tower_game_keyboard(current_level, session.get('opened_cells'), [], False, 0, True)
        )
        return

    elif data == "daily_spin":
        await daily_spin_callback(query, context)

    elif data == "do_spin":
        user_id = query.from_user.id
        user_data = db.get_user(user_id)

        if not user_data:
            db.create_user(user_id, query.from_user.username or query.from_user.first_name)
            user_data = db.get_user(user_id)

        spins_count = user_data[6] if len(user_data) > 6 else 1

        if spins_count <= 0:
            await query.answer("❌ <b>У вас нет доступных спинов!</b>", show_alert=True)
            return

        db.update_spins(user_id, spins_count - 1)

        slot_message = await context.bot.send_dice(chat_id=query.message.chat_id, emoji="🎰")
        slot_value = slot_message.dice.value

        await asyncio.sleep(2)

        if slot_value == 777:
            win_amount = 0.77
            result_text = f"""<b>[🎉] Поздравляем, ДЖЕКПОТ!</b>

<blockquote>Вам выпало 777 и множитель 10х, на ваш баланс было начислено <b>0.9$</b> ✅</blockquote>"""
            db.add_spin_result(user_id, 2, win_amount)
        elif slot_value in [1, 22, 43, 64]:
            win_amount = random.choice([0.5, 1, 2, 5])
            result_text = f"<b>🎰 Вы выиграли в спине!</b>\n\n<b>💰 Выигрыш: {win_amount} $</b>"
            db.add_spin_result(user_id, 1, win_amount)
        else:
            win_amount = 0
            result_text = f"<b>🎰 К сожалению, вы ничего не выиграли</b>\n\n<b>Попробуйте еще раз!</b>"
            db.add_spin_result(user_id, 0, 0)

        if win_amount > 0:
            db.update_balance(user_id, win_amount)
            db.add_transaction(user_id, 'spin_win', win_amount, f'Выигрыш в спине')

        await query.edit_message_text(
            result_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Крутить снова", callback_data="daily_spin")],
                [InlineKeyboardButton("« Назад", callback_data="back_main")]
            ]),
            parse_mode='HTML'
        )

    elif data.startswith("join_duel_"):
        duel_id = int(data.split("_")[2])
        await join_duel_callback(query, context, duel_id)
        return

    elif data.startswith("join_blackjack_"):
        game_id = int(data.split("_")[2])
        await join_blackjack_callback(query, context, game_id)
        return

    elif data.startswith("cancel_blackjack_"):
        game_id = int(data.split("_")[2])
        await cancel_blackjack_callback(query, context, game_id)
        return

    elif data.startswith("blackjack_take_"):
        game_id = int(data.split("_")[2])
        await blackjack_take_card_callback(query, context, game_id)
        return

    elif data.startswith("blackjack_stand_"):
        game_id = int(data.split("_")[2])
        await blackjack_stand_callback(query, context, game_id)
        return

    elif data.startswith("join_giveaway_"):
        giveaway_id = int(data.split("_")[2])
        await join_giveaway_callback(query, context, giveaway_id)
        return

    elif data == "game_mines":
        balance = get_balance_rounded(query.from_user.id)
        await query.edit_message_text(
            f"<b>Введите сумму ставки ✅</b>\n\n<b>Минимум: $0.20</b>\n<blockquote><b>💎 Ваш баланс: <code>{balance}</code> $</b></blockquote>",
            reply_markup=get_mines_bet_keyboard(user_id),
            parse_mode='HTML'
        )

    elif data.startswith("bet_"):
        bet_amount = float(data.split("_")[1])
        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < bet_amount:
            await query.answer("❌ <b>Недостаточно средств!</b>", show_alert=True)
            return

        if bet_amount < 0.2:
            await query.answer("❌ <b>Минимальная ставка 0.2$!</b>", show_alert=True)
            return

        await query.edit_message_text(
            f"💣 <b>Мины 5x5</b>\n\n🎯 Ставка: <b>{bet_amount} $</b>\n💣 Выбери количество мин (2-23):",
            reply_markup=get_mines_count_keyboard(),
            parse_mode='HTML'
        )
        context.user_data['current_bet'] = bet_amount

    elif data == "custom_bet":
        context.user_data['waiting_for_bet'] = True
        context.user_data['custom_bet_game'] = 'mines'
        await query.edit_message_text(
            "💣 <b>Мины 5x5</b>\n\n💰 Введите свою ставку в $:",
            parse_mode='HTML'
        )

    elif data.startswith("mines_"):
        mines_count = int(data.split("_")[1])
        bet_amount = context.user_data.get('current_bet', 10)

        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < bet_amount:
            await query.answer("❌ <b>Недостаточно средств!</b>", show_alert=True)
            return

        db.update_balance(user_id, -bet_amount)
        db.add_transaction(user_id, 'bet', -bet_amount, f'Ставка в игре Мины ({mines_count} мин)')

        coefficient = get_mines_coefficient(mines_count, 0)
        current_win = bet_amount * coefficient
        next_coefficient = get_next_mines_coefficient(mines_count, 0)
        next_win = bet_amount * next_coefficient

        game_id = random.randint(1000, 9999)
        game_text = f"""<b>💣 Мины</b> <code>{bet_amount}$</code> • <b>{mines_count}</b>

<blockquote><i>🧨 Мин в поле</i> - <b>{mines_count}</b> / 5x5</blockquote>

<i>👇 Чтобы начать, нажимай на клетки</i>"""

        mines_positions = generate_mines_positions(mines_count)

        game_sessions.create_session(
            user_id=user_id,
            game_type='mines',
            bet=bet_amount,
            mines_count=mines_count,
            opened_cells=[],
            mines_positions=mines_positions
        )

        keyboard = get_mines_game_keyboard([], mines_positions, True, current_win, False)
        await query.edit_message_text(
            game_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    elif data.startswith("mine_"):
        if not game_sessions.can_click(user_id):
            await query.answer("⏳ Подождите немного перед следующим действием!", show_alert=True)
            return

        session = game_sessions.get_session(user_id)
        if not session or session['game_type'] != 'mines':
            await query.answer("❌ <b>Нет активной игры!</b>", show_alert=True)
            return

        coords = data.split("_")[1:]
        if len(coords) != 2:
            return

        row, col = int(coords[0]), int(coords[1])
        cell_index = row * 5 + col

        if cell_index in session['opened_cells']:
            await query.answer("❌ <b>Эта ячейка уже открыта!</b>", show_alert=True)
            return

        session['opened_cells'].append(cell_index)
        session['moves_made'] += 1

        coefficient = get_mines_coefficient(session['mines_count'], len(session['opened_cells']))
        current_win = session['bet'] * coefficient
        next_coefficient = get_next_mines_coefficient(session['mines_count'], len(session['opened_cells']))
        next_win = session['bet'] * next_coefficient

        if cell_index in session['mines_positions']:
            db.conn.execute('UPDATE users SET total_bet = total_bet + ?, games_played = games_played + 1 WHERE user_id = ?',
                           (session['bet'], user_id))
            db.add_transaction(user_id, 'game_lose', 0, f'Проигрыш в игре Мины')

            game_id = random.randint(1000, 9999)
            result_text = f"""<b>💣 Мины · {session["mines_count"]}</b>
<i>🏵️ Проигрыш</i> - <code>{session["bet"]}$</code> → <b>0$ / x0</b>

<blockquote><b>💥 Вы попали на мину 😞</b></blockquote>

<b>🎲 Чтобы сыграть:</b> <code>/mines 0.2 2</code> ⎙
<blockquote>🧨 Игровой бот » @DarkedCasino_bot</blockquote>"""

            await query.edit_message_text(
                result_text,
                reply_markup=get_mines_game_keyboard(session['opened_cells'], session['mines_positions'], False, 0, True),
                parse_mode='HTML'
            )
            game_sessions.end_session(user_id)
        else:
            game_id = random.randint(1000, 9999)

            if len(session['opened_cells']) == 1:
                # Первое нажатие - меняем формат сообщения
                game_text = f"""<b>💣 Мины</b> <code>{session["bet"]}$</code>

<i>🧨 В поле</i> - <b>{session["mines_count"]}</b> 💣
<blockquote><b>💰 Выигрыш - x{coefficient:.2f} / {current_win:.2f}$</b></blockquote>

<i>🚀 Следующий ход</i> ⭢ x{next_coefficient:.2f} / {next_win:.2f}$

<i>🎲 Чтобы сыграть</i> <code>/mines 0.2 2</code> ⎙
<blockquote>🧨 Игровой бот » @DarkedCasino_bot</blockquote>"""
            else:
                # Последующие нажатия
                game_text = f"""<b>💣 Мины</b> <code>{session["bet"]}$</code>

<i>🧨 В поле</i> - <b>{session["mines_count"]}</b> 💣
<blockquote><b>💰 Выигрыш - x{coefficient:.2f} / {current_win:.2f}$</b></blockquote>

<i>🚀 Следующий ход</i> ⭢ x{next_coefficient:.2f} / {next_win:.2f}$

<i>🎲 Чтобы сыграть</i> <code>/mines 0.2 2</code> ⎙
<blockquote>🧨 Игровой бот » @DarkedCasino_bot</blockquote>"""

            can_cashout = len(session['opened_cells']) > 0
            keyboard = get_mines_game_keyboard(session['opened_cells'], session['mines_positions'], can_cashout, current_win, False)
            await query.edit_message_text(
                game_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )

    elif data == "game_tower":
        balance = get_balance_rounded(query.from_user.id)
        await query.edit_message_text(
            f"<b>Введите сумму ставки ✅</b>\n\n<b>Минимум: $0.20</b>\n<blockquote><b>💎 Ваш баланс: <code>{balance}</code> $</b></blockquote>",
            reply_markup=get_tower_bet_keyboard(user_id),
            parse_mode='HTML'
        )

    elif data.startswith("tower_bet_"):
        bet_amount = float(data.split("_")[2])
        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < bet_amount:
            await query.answer("❌ <b>Недостаточно средств!</b>", show_alert=True)
            return

        if bet_amount < 0.2:
            await query.answer("❌ <b>Минимальная ставка 0.2$!</b>", show_alert=True)
            return

        await query.edit_message_text(
            f"🏰 <b>Башня 6x5</b>\n\n🎯 Ставка: <b>{bet_amount} $</b>\n💣 Выбери количество мин:",
            reply_markup=get_tower_mines_keyboard(),
            parse_mode='HTML'
        )
        context.user_data['current_bet'] = bet_amount

    elif data == "tower_custom_bet":
        context.user_data['waiting_for_bet'] = True
        context.user_data['custom_bet_game'] = 'tower'
        await query.edit_message_text(
            "🏰 <b>Башня 6x5</b>\n\n💰 Введите свою ставку в $:",
            parse_mode='HTML'
        )

    elif data.startswith("tower_mines_"):
        mines_count = int(data.split("_")[2])
        bet_amount = context.user_data.get('current_bet', 10)

        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < bet_amount:
            await query.answer("❌ <b>Недостаточно средств!</b>", show_alert=True)
            return

        db.update_balance(user_id, -bet_amount)
        db.add_transaction(user_id, 'bet', -bet_amount, f'Ставка в игре Башня ({mines_count} мин)')

        coefficients = TOWER_COEFFICIENTS.get(mines_count, [1.0] * 6)

        mines_positions = []
        for level in range(6):
            level_mines = generate_tower_level_mines(mines_count, level)
            mines_positions.extend(level_mines)

        game_sessions.create_session(
            user_id=user_id,
            game_type='tower',
            bet=bet_amount,
            mines_count=mines_count,
            coefficients=coefficients,
            current_level=0,
            opened_cells=[],
            mines_positions=mines_positions
        )

        current_coeff = coefficients[0]
        current_win = bet_amount * current_coeff

        game_text = f"""<b>[🗼] Башня · {mines_count} 💣</b>

<blockquote><b>💎 Ставка - {bet_amount}$</b>
<b>💣 Мин в ряду - {mines_count} / 6×5</b></blockquote>"""

        keyboard = get_tower_game_keyboard(0, [], mines_positions, False, current_win, False)
        await query.edit_message_text(
            game_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    elif data.startswith("tower_click_"):
        if not game_sessions.can_click(user_id):
            await query.answer("⏳ Подождите немного перед следующим действием!", show_alert=True)
            return

        session = game_sessions.get_session(user_id)
        if not session or session['game_type'] != 'tower':
            await query.answer("❌ <b>Нет активной игры!</b>", show_alert=True)
            return

        coords = data.split("_")[2:]
        if len(coords) != 2:
            return

        row, col = int(coords[0]), int(coords[1])
        cell_index = row * 5 + col

        if row != session['current_level']:
            await query.answer("❌ <b>Открывай ячейки только на текущем уровне!</b>", show_alert=True)
            return

        if cell_index in session['opened_cells']:
            await query.answer("❌ <b>Эта ячейка уже открыта!</b>", show_alert=True)
            return

        session['opened_cells'].append(cell_index)

        if cell_index in session['mines_positions']:
            db.conn.execute('UPDATE users SET total_bet = total_bet + ?, games_played = games_played + 1 WHERE user_id = ?',
                           (session['bet'], user_id))
            db.add_transaction(user_id, 'game_lose', 0, f'Проигрыш в игре Башня')

            result_text = f"""<b>[🗼] Башня · {session['mines_count']} завершена 💣</b>

<blockquote><b>💎 Ставка - {session['bet']}$</b>
<b>💣 Мин в ряду - {session['mines_count']} / 6×5</b></blockquote>"""

            await query.edit_message_text(
                result_text,
                parse_mode='HTML'
            )
            game_sessions.end_session(user_id)
        else:
            session['current_level'] += 1

            if session['current_level'] >= 6:
                win_amount = session['bet'] * session['coefficients'][-1]
                win_amount = round(win_amount, 2)

                db.update_balance(user_id, win_amount)
                db.conn.execute('UPDATE users SET total_bet = total_bet + ?, total_won = total_won + ?, games_played = games_played + 1 WHERE user_id = ?',
                               (session['bet'], win_amount, user_id))
                db.add_transaction(user_id, 'game_win', win_amount, f'Выигрыш в игре Башня (x{session["coefficients"][-1]})')

                result_text = f"""<b>[🗼] Башня · [{session['mines_count']} × 💣] завершена <code>#{random.randint(1000, 9999)}</code> ✅</b>

<blockquote><b>💎 Ставка - {session['bet']}$</b>
<b>💣 Мин в ряду - {session['mines_count']} / 6×5</b></blockquote>

<blockquote><b>💸 Вы забрали выигрыш: {win_amount}$ | {session['coefficients'][-1]}x</b></blockquote>"""

                await query.edit_message_text(
                    result_text,
                    parse_mode='HTML'
                )
                game_sessions.end_session(user_id)
            else:
                current_coeff = session['coefficients'][session['current_level']]
                current_win = session['bet'] * current_coeff

                game_text = f"""<b>[🗼] Башня · {session["mines_count"]} 💣</b>

<blockquote><b>💎 Ставка - {session["bet"]}$</b>
<b>💣 Мин в ряду - {session["mines_count"]} / 6×5</b></blockquote>"""

                keyboard = get_tower_game_keyboard(session['current_level'], session['opened_cells'], session['mines_positions'], True, current_win, False)
                await query.edit_message_text(
                    game_text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )

    elif data == "game_dice":
        balance = get_balance_rounded(query.from_user.id)
        await query.edit_message_text(
            f"<b>Введите сумму ставки ✅</b>\n\n<b>Минимум: $0.20</b>\n<blockquote><b>💎 Ваш баланс: <code>{balance}</code> $</b></blockquote>",
            reply_markup=get_dice_bet_keyboard(user_id),
            parse_mode='HTML'
        )

    elif data.startswith("dice_bet_"):
        bet_amount = float(data.split("_")[2])
        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < bet_amount:
            await query.answer("❌ <b>Недостаточно средств!</b>", show_alert=True)
            return

        if bet_amount < 0.2:
            await query.answer("❌ <b>Минимальная ставка 0.2$!</b>", show_alert=True)
            return

        await query.edit_message_text(
            f"🎲 <b>Дайс</b>\n\n🎯 Ставка: <b>{bet_amount} $</b>\n🎮 Выбери режим игры:",
            reply_markup=get_dice_mode_keyboard(),
            parse_mode='HTML'
        )
        context.user_data['current_bet'] = bet_amount

    elif data == "dice_custom_bet":
        context.user_data['waiting_for_bet'] = True
        context.user_data['custom_bet_game'] = 'dice'
        await query.edit_message_text(
            "🎲 <b>Дайс</b>\n\n💰 Введите свою ставку в $:",
            parse_mode='HTML'
        )

    elif data.startswith("dice_mode_"):
        mode = data.split("_")[2]
        bet_amount = context.user_data.get('current_bet', 10)

        mode_names = {
            'evenodd': 'Чёт/Нечёт',
            'highlow': 'Больше/Меньше',
            'highlow7': 'Больше/Меньше 7'
        }

        await query.edit_message_text(
            f"🎲 <b>Дайс</b>\n\n🎯 Ставка: <b>{bet_amount} $</b>\n🎮 Режим: <b>{mode_names[mode]}</b>\n🎯 Сделай свой выбор:",
            reply_markup=get_dice_choice_keyboard(mode),
            parse_mode='HTML'
        )
        context.user_data['dice_mode'] = mode

    elif data.startswith("dice_choice_"):
        choice = data.split("_")[2]
        bet_amount = context.user_data.get('current_bet', 10)
        mode = context.user_data.get('dice_mode', 'evenodd')

        user_data = db.get_user(user_id)
        if not user_data or user_data[2] < bet_amount:
            await query.answer("❌ <b>Недостаточно средств!</b>", show_alert=True)
            return

        db.update_balance(user_id, -bet_amount)
        db.add_transaction(user_id, 'bet', -bet_amount, f'Ставка в игре Дайс ({mode})')

        if mode == 'highlow7':
            dice1_message = await context.bot.send_dice(chat_id=query.message.chat_id, emoji="🎲")
            dice2_message = await context.bot.send_dice(chat_id=query.message.chat_id, emoji="🎲")
            dice1_value = dice1_message.dice.value
            dice2_value = dice2_message.dice.value
            dice_value = dice1_value + dice2_value
            dice_text = f"🎲 Результат: {dice1_value} + {dice2_value} = {dice_value}"
        else:
            dice_message = await context.bot.send_dice(chat_id=query.message.chat_id, emoji="🎲")
            dice_value = dice_message.dice.value
            dice_text = f"🎲 Результат: {dice_value}"

        await asyncio.sleep(2)

        won = check_dice_win(dice_value, mode, choice)

        db.conn.execute('UPDATE users SET total_bet = total_bet + ?, games_played = games_played + 1 WHERE user_id = ?',
                       (bet_amount, user_id))

        if won:
            win_amount = bet_amount * 1.8
            win_amount = round(win_amount, 2)
            db.update_balance(user_id, win_amount)
            db.conn.execute('UPDATE users SET total_won = total_won + ? WHERE user_id = ?',
                           (win_amount, user_id))
            db.add_transaction(user_id, 'game_win', win_amount, f'Выигрыш в игре Дайс')
            result_text = f"<b>🎲 Победа!</b>\n\n<b>{dice_text}</b>\n<b>💰 Выигрыш: {win_amount} $</b>"
        else:
            db.add_transaction(user_id, 'game_lose', 0, f'Проигрыш в игре Дайс')
            result_text = f"<b>🎲 Проигрыш</b>\n\n<b>{dice_text}</b>\n<b>💸 Потеряно: {bet_amount} $</b>"

        await query.edit_message_text(
            result_text,
            parse_mode='HTML'
        )

    elif data == "deposit":
        await query.edit_message_text(
            "💰 <b>Пополнение баланса</b>\n\n👇 Выбери сумму пополнения:",
            reply_markup=get_deposit_keyboard(),
            parse_mode='HTML'
        )

    elif data.startswith("deposit_"):
        if data == "deposit_custom":
            context.user_data['waiting_for_deposit'] = True
            await query.edit_message_text(
                "💰 <b>Пополнение баланса</b>\n\n💵 Введите сумму пополнения в $:",
                parse_mode='HTML'
            )
        else:
            amount = float(data.split("_")[1])
            if amount < 0.2:
                await query.answer("❌ <b>Минимальная сумма пополнения 0.2$!</b>", show_alert=True)
                return
            context.user_data['deposit_amount'] = amount
            await create_cryptobot_invoice_callback(query, context, amount)

    elif data == "withdraw":
        await query.edit_message_text(
            "💸 <b>Вывод средств</b>\n\n👇 Выбери сумму вывода:",
            reply_markup=get_withdrawal_keyboard(),
            parse_mode='HTML'
        )

    elif data.startswith("withdraw_"):
        if data == "withdraw_custom":
            context.user_data['waiting_for_withdrawal'] = True
            await query.edit_message_text(
                "<b>💰 Введите сумму вывода:</b>",
                reply_markup=get_withdrawal_cancel_keyboard(),
                parse_mode='HTML'
            )
        else:
            amount = float(data.split("_")[1])
            user_data = db.get_user(user_id)
            if not user_data or user_data[2] < amount:
                await query.answer("❌ <b>Недостаточно средств!</b>", show_alert=True)
                return

            if amount < 0.2:
                await query.answer("❌ <b>Минимальная сумма вывода 0.2$!</b>", show_alert=True)
                return

            if user_data[3] <= 0:
                await query.answer("❌ <b>Для вывода необходимо сделать хотя бы одну ставку!</b>", show_alert=True)
                return

            await create_withdrawal_request_callback(query, context, amount)

    elif data == "cancel_withdrawal":
        context.user_data['waiting_for_withdrawal'] = False
        await query.edit_message_text(
            "💸 <b>Вывод средств</b>\n\n👇 Выбери сумму вывода:",
            reply_markup=get_withdrawal_keyboard(),
            parse_mode='HTML'
        )

    elif data.startswith("approve_withdrawal_"):
        withdrawal_id = int(data.split("_")[2])
        await approve_withdrawal(query, context, withdrawal_id)

    elif data.startswith("reject_withdrawal_"):
        withdrawal_id = int(data.split("_")[2])
        await reject_withdrawal(query, context, withdrawal_id)

    elif data == "admin_stats":
        await show_admin_stats(query, context)

    elif data == "admin_users":
        await show_admin_users(query, context)

    elif data == "admin_withdrawals":
        await show_admin_withdrawals(query, context)

    elif data == "admin_settings":
        await show_admin_settings(query, context)

    elif data == "admin_deposit_settings":
        await show_deposit_settings(query, context)

async def create_cryptobot_invoice_callback(query, context, amount: float):
    user_id = query.from_user.id

    try:
        headers = {
            'Crypto-Pay-API-Token': CRYPTO_BOT_TOKEN,
            'Content-Type': 'application/json'
        }

        data = {
            'asset': 'USDT',
            'amount': str(amount),
            'description': f'Пополнение баланса на {amount}$',
            'hidden_message': f'ID пользователя: {user_id}',
            'paid_btn_name': 'callback',
            'paid_btn_url': f'https://t.me/darkedcasino_bot',
            'payload': str(user_id)
        }

        response = requests.post(
            'https://pay.crypt.bot/api/createInvoice',
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                invoice_url = result['result']['pay_url']
                invoice_id = result['result']['invoice_id']

                cursor = db.conn.cursor()
                cursor.execute(
                    'INSERT INTO deposits (user_id, amount, status, invoice_url, invoice_id, currency) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, amount, 'pending', invoice_url, str(invoice_id), 'USDT')
                )
                db.conn.commit()

                db.add_transaction(user_id, 'deposit', amount, f'Создан счет CryptoBot для пополнения #{invoice_id}')

                await query.edit_message_text(
                    f"<b>✅ Счет создан на сумму {amount} USDT (CryptoBot)</b>",
                    reply_markup=get_deposit_invoice_keyboard(invoice_url),
                    parse_mode='HTML'
                )
            else:
                error_msg = result.get('error', {}).get('name', 'Неизвестная ошибка')
                await query.edit_message_text(f"❌ <b>Ошибка при создании счета: {error_msg}</b>", parse_mode='HTML')
        else:
            await query.edit_message_text(f"❌ <b>Ошибка подключения к платежной системе! Статус: {response.status_code}</b>", parse_mode='HTML')

    except requests.exceptions.RequestException as e:
        await query.edit_message_text(f"❌ <b>Ошибка сети при создании счета: {str(e)}</b>", parse_mode='HTML')
    except Exception as e:
        await query.edit_message_text(f"❌ <b>Неожиданная ошибка при создании счета: {str(e)}</b>", parse_mode='HTML')

def main():
    try:
        application = Application.builder().token(BOT_TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("profile", quick_profile))
        application.add_handler(CommandHandler("admin", admin_command))
        application.add_handler(CommandHandler("givebalance", give_balance))
        application.add_handler(CommandHandler("o", reset_balance_command))
        application.add_handler(CommandHandler("spin", daily_spin_command))
        application.add_handler(CommandHandler("cg", create_duel_command))
        application.add_handler(CommandHandler("fast", create_giveaway_command))
        application.add_handler(CommandHandler("21", create_blackjack_command))

        application.add_handler(CommandHandler("mines", quick_mines_command))
        application.add_handler(CommandHandler("tower", quick_tower_command))
        application.add_handler(CommandHandler("cube", quick_dice_command))

        # Добавляем обработчик команды депозит
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_callback))

        application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^/п\b'), transfer_money))

        if hasattr(application, 'job_queue') and application.job_queue is not None:
            application.job_queue.run_repeating(check_payments, interval=10, first=10)

        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()