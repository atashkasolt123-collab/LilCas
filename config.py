# --- Основные настройки ---
# Токен бота
BOT_TOKEN = "7734038463:AAHklhMrdCy-ggN97vd85DhmKt10za9fqe4"

# Список ID администраторов
ADMINS = [8473589780, 7313407194]

# --- API Ключи (Заполните свои данные) ---
CRYPTO_PAY_TOKEN = "551312:AAF9IUpyXy2xlpTT7KsjXs8R541eWeixIbL" # Токен от @CryptoBot (Crypto Pay API)
XROCKET_API_KEY = "24c549a2a94584276334ee753"  # API Key от @xRocket

# --- Лимиты ---
MIN_DEPOSIT = 0.4  # Минимальное пополнение в 💰
MIN_WITHDRAW = 1 # Минимальный вывод в 💰
MAX_BET = 100    # Максимальная ставка в 💰

# --- Ссылки ---
CHANNEL_URL = "https://t.me/weqcazino"  # Ссылка на канал
SUPPORT_URL = "https://t.me/scamerusdt"  # Ссылка на поддержку/помощь
SITE_URL = "https://t.me/weqcazino"       # Ссылка на сайт
CHAT_URL = "https://t.me/weqchatcazino"     # Ссылка на чат
ALERTS_CHANNEL = "@weqcazino"        # Канал для крупных выигрышей/выводов

# --- Премиум эмодзи (только для текстовых сообщений) ---
PREMIUM_EMOJIS = {
    "rocket": "5377336433692412420🛸",
    "dollar": "5377852667286559564💲",
    "dice": "5377346496800786271🎯",
    "transfer": "5377720025811555309🔄",
    "lightning": "5375469677696815127⚡",
    "casino": "5969709082049779216🎰",
    "balance": "5262509177363787445💰",
    "withdraw": "5226731292334235524💸",
    "deposit": "5226731292334235524💳",
    "game": "5258508428212445001🎮",
    "mine": "4979035365823219688💣",
    "win": "5436386989857320953🏆",
    "lose": "4979035365823219688💥",
    "prize": "5323761960829862762🎁",
    "user": "5168063997575956782👤",
    "stats": "5231200819986047254📊",
    "time": "5258419835922030550🕒",
    "min": "5447183459602669338📌",
    "card": "5902056028513505203💳",
    "rules": "5258328383183396223📋",
    "info": "5258334872878980409ℹ️",
    "back": "5877629862306385808↩️",
    "play": "5467583879948803288▶️",
    "bet": "5893048571560726748🎯",
    "multiplier": "5201691993775818138📈",
    "history": "5353025608832004653📋"
}

# --- Тексты ---
TEXTS = {
    "ru": {
        "welcome": (
            "<b>{casino} Привет, добро пожаловать в AdvanceCasino</b>\n\n"
            "<blockquote>{info} Подписывайся на <a href='" + CHANNEL_URL + "'>наш канал</a> чтобы следить за новостями и конкурсами.</blockquote>"
        ),
        
        "profile": (
            "<b>{user} #{player_id} {name}</b>\n\n"
            "<blockquote><b>{card} Баланс — {balance:.2f} {balance_emoji}\n"
            "{multiplier} Ваш VIP прогресс — {rank_progress:.0f}%\n"
            "{progress_bar}\n"
            "{current_rank} → {next_rank}\n\n"
            "{stats} Оборот — {turnover:.2f} {balance_emoji}\n"
            "{game} Сыграно — {bets} ставок\n"
            "{time} Аккаунту — {days}</b></blockquote>"
        ),
        
        "chats": "<blockquote>{transfer} Игровые чаты это отличное место чтобы найти друзей, обсудить игру или поднять денег в конкурсах и раздачах!</blockquote>",
        
        "referral": (
            "<b>{user} Реферальная программа</b>\n\n"
            "{min} 1 уровень — <b>60%</b> от реферальных\n"
            "{min} 2 уровень — <b>30%</b> от рефералов 1 уровня\n"
            "{min} 3 уровень — <b>10%</b> от рефералов 2 уровня\n\n"
            "{user} Ваши рефералы: <b>{ref_count}</b>\n"
            "{balance} Реф. баланс: <b>{ref_balance:.2f} {balance_emoji}</b>\n"
            "{prize} Заработано всего: <b>{total_earned:.2f} {balance_emoji}</b>\n\n"
            "{rocket} Ваша реферальная ссылка:\n"
            "<code>{ref_link}</code>"
        ),
        
        "play": (
            "<b>{game} Выбирайте мини-игру!</b>\n\n"
            "<blockquote>{balance} Баланс — {balance:.2f} {balance_emoji}\n"
            "{bet} Ставка — {bet:.2f} {balance_emoji}</blockquote>\n\n"
            "{info} Пополняй и сыграй на реальные деньги"
        ),
        
        "modes_menu": (
            "<b>{mine} Выбирайте мини-игру!</b>\n\n"
            "<blockquote>{balance} Баланс — {balance:.2f} {balance_emoji}\n"
            "{bet} Ставка — {bet:.2f} {balance_emoji}</blockquote>\n\n"
            "{info} Пополняй и сыграй на реальные деньги"
        ),
        
        "mines_main": (
            "<b>{mine} Мины</b>\n\n"
            "{user} Игрок #{player_id}\n"
            "<blockquote>{card} Баланс — {balance:,.2f} {balance_emoji}\n"
            "{bet} Ставка — {bet:,.2f} {balance_emoji}</blockquote>\n\n"
            "{min} Выбрано — {mines} {mine}"
        ),
        
        "mines_select": (
            "{casino} <b>Выберите количество</b>\n\n"
            "{min} Выбрано — <b>{mines} {mine}</b>\n\n"
            "<blockquote>{coefs}</blockquote>"
        ),
        
        "mines_playing": (
            "<blockquote><b>{mine} Мины · {mines} {mine}</b></blockquote>\n\n"
            "<b>{bet:,.2f} {balance_emoji} × {coef:.2f} ➔ {win:,.2f} {balance_emoji}</b>\n\n"
            "<blockquote>{coefs}</blockquote>"
        ),
        
        "deposit_method": "{deposit} Выберите способ пополнения",
        "enter_deposit_amount": "{balance} Введите сумму пополнения в <b>{balance_emoji}</b>\n\n{info} Минимальная сумма: {min_amount:.2f} {balance_emoji}",
        "enter_withdraw_amount": "{withdraw} Введите сумму вывода в <b>{balance_emoji}</b>\n\n{info} Минимальная сумма: {min_amount:.2f} {balance_emoji}",
        "deposit_created": "{lightning} Нажмите ниже, чтобы пополнить баланс",
        "check_payment": "{transfer} Проверить оплату",
        "payment_success": "{win} Баланс успешно пополнен на <b>{amount:.2f} {balance_emoji}</b>!",
        "payment_not_found": "{lose} Оплата не найдена. Пожалуйста, оплатите счет и нажмите кнопку еще раз.",
        "error_min_deposit": "{lose} Минимальная сумма пополнения — {min_amount:.2f} {balance_emoji}",
        "error_min_withdraw": "{lose} Минимальная сумма вывода — {min_amount:.2f} {balance_emoji}",
        "language_select": "{dice} Выберите язык бота",
        
        "privacy": (
            "<b>{user} Приватность</b>\n\n"
            "{min} Крупные ставки и победы в @wins_alerts\n"
            "{min} Топ игроков по обороту и балансу\n"
            "{min} Ставки в чатах\n\n"
            "{info} Отображается {display_mode}"
        ),
        
        "privacy_set_nickname": "{rules} Введите ваш новый псевдоним (до 15 символов):",
        "nickname_updated": "{win} Псевдоним успешно обновлен!",
        "privacy_updated": "{win} Настройки приватности обновлены!",
        
        "stats_text": (
            "{stats} <b>Статистика {name}</b>\n\n"
            "{game} Сыграно — {bets} ставок\n"
            "{stats} Оборот — {turnover:.2f} {balance_emoji}\n"
            "{time} Аккаунту — {days} {days_label}\n\n"
            "{deposit} Пополнений — {deposits:.2f} {balance_emoji}\n"
            "{withdraw} Выводов — {withdrawals:.2f} {balance_emoji}"
        ),
        
        "admin_menu": (
            "<b>{rocket} Админ-панель</b>\n\n"
            "{min} Выберите действие:"
        ),
        
        "admin_broadcast": (
            "{transfer} Введите сообщение для рассылки всем пользователям:\n\n"
            "{back} /cancel - отмена"
        ),
        
        "admin_add_balance": (
            "{deposit} Введите ID пользователя и сумму через пробел:\n"
            "Пример: <code>123456789 100</code>\n\n"
            "{back} /cancel - отмена"
        ),
        
        "admin_set_balance": (
            "{balance} Введите ID пользователя и новую сумму через пробел:\n"
            "Пример: <code>123456789 500</code>\n\n"
            "{back} /cancel - отмена"
        ),
        
        "admin_broadcast_sent": "{win} Сообщение отправлено {count} пользователям!",
        "admin_broadcast_cancel": "{back} Рассылка отменена",
        "admin_balance_added": "{win} Баланс игрока {user_id} увеличен на {amount:.2f} {balance_emoji}",
        "admin_balance_set": "{win} Баланс игрока {user_id} установлен на {amount:.2f} {balance_emoji}",
        "admin_user_not_found": "{lose} Пользователь с ID {user_id} не найден",
        "admin_invalid_format": "{lose} Неверный формат. Используйте: ID СУММА",
        
        "buttons": {
            "play": "🎮 Играть",
            "chats": "💬 Игровые чаты",
            "profile": "👤 Профиль",
            "referral": "👥 Реф. программа",
            "language": "🌐 Язык",
            "back": "⬅️ Назад",
            "deposit": "💸 Пополнить",
            "withdraw": "📥 Вывести",
            "stats": "📊 Статистика",
            "privacy": "🥷 Приватность",
            "bonuses": "🍬 Бонусы",
            "main_chat": "🇷🇺 Основной чат",
            "claim_ref": "🎁 Забрать на баланс · {amount:.2f} {balance_emoji}",
            "invite_friend": "🚀 Пригласить друга",
            "details": "ℹ️ Подробнее",
            "game_soccer": "⚽",
            "game_basket": "🏀",
            "game_darts": "🎯",
            "game_bowling": "🎳",
            "game_slots": "🎰",
            "provider_custom": "🐋 Авторские",
            "site": "❄️ Сайт",
            "change_bet": "✏️ Изменить ставку",
            "crypto_bot": "🤖 Crypto Bot",
            "xrocket": "🤖 xRocket",
            "lang_ru": "🇷🇺 RU",
            "lang_en": "🇺🇸 EN",
            "pay": "💳 Пополнить · {amount:.2f} {balance_emoji}",
            "change_amount": "🔄 Изменить сумму",
            "settings": "⚙️ Настройки",
            "transactions": "📠 Транзакции",
            "game_history": "🔬 История игр",
            "modes": "💣 Режимы",
            "game_mines": "💣 Мины",
            "game_tower": "🗼 Башня"
        }
    },
    "en": {
        "welcome": (
            "<b>{casino} Hello, welcome to AdvanceCasino</b>\n\n"
            "<blockquote>{info} Subscribe to <a href='" + CHANNEL_URL + "'>our channel</a> to follow news and contests.</blockquote>"
        ),
        
        "profile": (
            "<b>{user} #{player_id} {name}</b>\n\n"
            "<blockquote><b>{card} Balance — {balance:.2f} {balance_emoji}\n"
            "{multiplier} Your VIP progress — {rank_progress:.0f}%\n"
            "{progress_bar}\n"
            "{current_rank} → {next_rank}\n\n"
            "{stats} Turnover — {turnover:.2f} {balance_emoji}\n"
            "{game} Played — {bets} bets\n"
            "{time} Account — {days}</b></blockquote>"
        ),
        
        "chats": "<blockquote>{transfer} Game chats are a great place to find friends, discuss the game or make money in contests and giveaways!</blockquote>",
        
        "referral": (
            "<b>{user} Referral Program</b>\n\n"
            "{min} Level 1 — <b>60%</b> from referrals\n"
            "{min} Level 2 — <b>30%</b> from level 1 referrals\n"
            "{min} Level 3 — <b>10%</b> from level 2 referrals\n\n"
            "{user} Your referrals: <b>{ref_count}</b>\n"
            "{balance} Ref. balance: <b>{ref_balance:.2f} {balance_emoji}</b>\n"
            "{prize} Total earned: <b>{total_earned:.2f} {balance_emoji}</b>\n\n"
            "{rocket} Your referral link:\n"
            "<code>{ref_link}</code>"
        ),
        
        "play": (
            "<b>{game} Choose a mini-game!</b>\n\n"
            "<blockquote>{balance} Balance — {balance:.2f} {balance_emoji}\n"
            "{bet} Bet — {bet:.2f} {balance_emoji}</blockquote>\n\n"
            "{info} Deposit and play for real money"
        ),
        
        "modes_menu": (
            "<b>{mine} Choose a mini-game!</b>\n\n"
            "<blockquote>{balance} Balance — {balance:.2f} {balance_emoji}\n"
            "{bet} Bet — {bet:.2f} {balance_emoji}</blockquote>\n\n"
            "{info} Deposit and play for real money"
        ),
        
        "mines_main": (
            "<b>{mine} Mines</b>\n\n"
            "{user} Player #{player_id}\n"
            "<blockquote>{card} Balance — {balance:,.2f} {balance_emoji}\n"
            "{bet} Bet — {bet:,.2f} {balance_emoji}</blockquote>\n\n"
            "{min} Selected — {mines} {mine}"
        ),
        
        "mines_select": (
            "{casino} <b>Select amount</b>\n\n"
            "{min} Selected — <b>{mines} {mine}</b>\n\n"
            "<blockquote>{coefs}</blockquote>"
        ),
        
        "mines_playing": (
            "<blockquote><b>{mine} Mines · {mines} {mine}</b></blockquote>\n\n"
            "<b>{bet:,.2f} {balance_emoji} × {coef:.2f} ➔ {win:,.2f} {balance_emoji}</b>\n\n"
            "<blockquote>{coefs}</blockquote>"
        ),
        
        "deposit_method": "{deposit} Choose deposit method",
        "enter_deposit_amount": "{balance} Enter deposit amount in <b>{balance_emoji}</b>\n\n{info} Minimum amount: {min_amount:.2f} {balance_emoji}",
        "enter_withdraw_amount": "{withdraw} Enter withdrawal amount in <b>{balance_emoji}</b>\n\n{info} Minimum amount: {min_amount:.2f} {balance_emoji}",
        "deposit_created": "{lightning} Click below to top up your balance",
        "check_payment": "{transfer} Check Payment",
        "payment_success": "{win} Balance successfully topped up by <b>{amount:.2f} {balance_emoji}</b>!",
        "payment_not_found": "{lose} Payment not found. Please pay the invoice and click the button again.",
        "error_min_deposit": "{lose} Minimum deposit amount is {min_amount:.2f} {balance_emoji}",
        "error_min_withdraw": "{lose} Minimum withdrawal amount is {min_amount:.2f} {balance_emoji}",
        "language_select": "{dice} Choose bot language",
        
        "privacy": (
            "<b>{user} Privacy</b>\n\n"
            "{min} Big bets and wins in @wins_alerts\n"
            "{min} Top players by turnover and balance\n"
            "{min} Bets in chats\n\n"
            "{info} Displayed: {display_mode}"
        ),
        
        "privacy_set_nickname": "{rules} Enter your new pseudonym (up to 15 characters):",
        "nickname_updated": "{win} Pseudonym successfully updated!",
        "privacy_updated": "{win} Privacy settings updated!",
        
        "stats_text": (
            "{stats} <b>Statistics {name}</b>\n\n"
            "{game} Played — {bets} bets\n"
            "{stats} Turnover — {turnover:.2f} {balance_emoji}\n"
            "{time} Account — {days} {days_label}\n\n"
            "{deposit} Deposits — {deposits:.2f} {balance_emoji}\n"
            "{withdraw} Withdrawals — {withdrawals:.2f} {balance_emoji}"
        ),
        
        "admin_menu": (
            "<b>{rocket} Admin Panel</b>\n\n"
            "{min} Choose an action:"
        ),
        
        "admin_broadcast": (
            "{transfer} Enter message to broadcast to all users:\n\n"
            "{back} /cancel - cancel"
        ),
        
        "admin_add_balance": (
            "{deposit} Enter user ID and amount separated by space:\n"
            "Example: <code>123456789 100</code>\n\n"
            "{back} /cancel - cancel"
        ),
        
        "admin_set_balance": (
            "{balance} Enter user ID and new balance separated by space:\n"
            "Example: <code>123456789 500</code>\n\n"
            "{back} /cancel - cancel"
        ),
        
        "admin_broadcast_sent": "{win} Message sent to {count} users!",
        "admin_broadcast_cancel": "{back} Broadcast cancelled",
        "admin_balance_added": "{win} User {user_id} balance increased by {amount:.2f} {balance_emoji}",
        "admin_balance_set": "{win} User {user_id} balance set to {amount:.2f} {balance_emoji}",
        "admin_user_not_found": "{lose} User with ID {user_id} not found",
        "admin_invalid_format": "{lose} Invalid format. Use: ID AMOUNT",
        
        "buttons": {
            "play": "🎮 Play",
            "chats": "💬 Game Chats",
            "profile": "👤 Profile",
            "referral": "👥 Referral Program",
            "language": "🌐 Language",
            "back": "⬅️ Back",
            "deposit": "💸 Deposit",
            "withdraw": "📥 Withdraw",
            "stats": "📊 Statistics",
            "privacy": "🥷 Privacy",
            "bonuses": "🍬 Bonuses",
            "main_chat": "🇺🇸 Main Chat",
            "claim_ref": "🎁 Claim to balance · {amount:.2f} {balance_emoji}",
            "invite_friend": "🚀 Invite a friend",
            "details": "ℹ️ Details",
            "game_soccer": "⚽",
            "game_basket": "🏀",
            "game_darts": "🎯",
            "game_bowling": "🎳",
            "game_slots": "🎰",
            "provider_custom": "🐋 Custom",
            "site": "❄️ Site",
            "change_bet": "✏️ Change bet",
            "crypto_bot": "🤖 Crypto Bot",
            "xrocket": "🤖 xRocket",
            "lang_ru": "🇷🇺 RU",
            "lang_en": "🇺🇸 EN",
            "pay": "💳 Deposit · {amount:.2f} {balance_emoji}",
            "change_amount": "🔄 Change amount",
            "settings": "⚙️ Settings",
            "transactions": "📠 Transactions",
            "game_history": "🔬 Game History",
            "modes": "💣 Modes",
            "game_mines": "💣 Mines",
            "game_tower": "🗼 Tower"
        }
    }
}
