import logging
import sqlite3
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== КОНСТАНТИ ====================
EMAIL, PASSWORD, MONEY_AMOUNT, COINS_AMOUNT, SETTINGS_NAME, SETTINGS_ID, SETTINGS_WINS, SETTINGS_LOSES = range(8)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8674559116:AAFuZWJJLVY-qMAHBSr7Z6om686b1zeGxKc")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8694942406"))

# ==================== БАЗА ====================
def inicijaliziraj_baza():
    try:
        conn = sqlite3.connect('ajhan.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS korisnici (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                email TEXT,
                password TEXT,
                player_id TEXT,
                money INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                loses INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                registered TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS features (
                user_id INTEGER,
                feature TEXT,
                unlocked INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, feature)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Базата е креирана")
    except Exception as e:
        logger.error(f"❌ Грешка: {e}")

inicijaliziraj_baza()

# ==================== GG СКРИПТИ ====================
def generiraj_gg_skripta(funkcija, user_id, value=None):
    if funkcija == "MONEY":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.setVisible(false)
gg.searchNumber('1000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('{value}', gg.TYPE_DWORD)
gg.searchNumber('5000', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('{value}', gg.TYPE_DWORD)
gg.toast('💰 ДОДАДЕНИ ${value}!')
gg.alert('✅ УСПЕШНО! ${value} се додадени!')"""
    
    elif funkcija == "COINS":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.setVisible(false)
gg.searchNumber('100', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('{value}', gg.TYPE_DWORD)
gg.searchNumber('200', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('{value}', gg.TYPE_DWORD)
gg.searchNumber('500', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('{value}', gg.TYPE_DWORD)
gg.toast('🪙 ДОДАДЕНИ {value} КОИНСИ!')
gg.alert('✅ {value} коинси се додадени!')"""
    
    elif funkcija == "W16":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('2000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('5000', gg.TYPE_DWORD)
gg.alert('✅ W16 Motor отклучен!')"""
    
    elif funkcija == "Horns":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(1000)
gg.editAll('1', gg.TYPE_DWORD)
gg.alert('✅ Хорни отклучени!')"""
    
    elif funkcija == "NoDmg":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('100', gg.TYPE_FLOAT)
gg.getResults(50)
gg.editAll('999999', gg.TYPE_FLOAT)
gg.alert('🛡️ Без штета!')"""
    
    elif funkcija == "Fuel":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('100', gg.TYPE_FLOAT)
gg.getResults(50)
gg.editAll('999999', gg.TYPE_FLOAT)
gg.alert('⛽ Бесконечно гориво!')"""
    
    elif funkcija == "Smoke":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('1', gg.TYPE_DWORD)
gg.alert('💨 Чад отклучен!')"""
    
    elif funkcija == "Anims":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(500)
gg.editAll('1', gg.TYPE_DWORD)
gg.alert('🎭 Анимации отклучени!')"""
    
    elif funkcija == "Wheels":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(200)
gg.editAll('1', gg.TYPE_DWORD)
gg.alert('⚙️ Тркала отклучени!')"""
    
    elif funkcija == "Houses":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('1', gg.TYPE_DWORD)
gg.alert('🏠 Куќи отклучени!')"""
    
    elif funkcija == "Levels":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('1', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('999', gg.TYPE_DWORD)
gg.alert('📈 Ниво 999!')"""
    
    elif funkcija == "Rank":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('1', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('999999', gg.TYPE_DWORD)
gg.alert('👑 Макс ранг!')"""
    
    elif funkcija == "UnlockAll":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.setVisible(false)
gg.searchNumber('1000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('50000000', gg.TYPE_DWORD)
gg.searchNumber('100', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('500000', gg.TYPE_DWORD)
gg.searchNumber('2000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('5000', gg.TYPE_DWORD)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(1000)
gg.editAll('1', gg.TYPE_DWORD)
gg.searchNumber('100', gg.TYPE_FLOAT)
gg.getResults(50)
gg.editAll('999999', gg.TYPE_FLOAT)
gg.searchNumber('1', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('999', gg.TYPE_DWORD)
gg.toast('🌟 СЕ Е ОТКЛУЧЕНО!')
gg.alert('🎉 СЕ Е ОТКЛУЧЕНО!')"""
    else:
        return ""

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "N/A"
    
    logger.info(f"📱 START од {user_id} (@{username})")
    
    # Провери дали корисникот е регистриран
    conn = sqlite3.connect('ajhan.db')
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM korisnici WHERE user_id = ?', (user_id,))
    rezultat = cursor.fetchone()
    conn.close()
    
    if rezultat:
        # Веќе регистриран - прикажи Dashboard
        await prikazi_dashboard(update, context, user_id)
        return
    
    # Не е регистриран - барај Email
    await update.message.reply_text(
        "🔑 **AJHAN X TOOL - НАЈАВА**\n\n"
        "Добредојде во AJHAN X TOOL!\n\n"
        "Внесете го вашиот CPM Email за да започнете:",
        parse_mode='Markdown'
    )
    return EMAIL

# ==================== EMAIL ====================
async def primi_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "N/A"
    
    context.user_data['email'] = email
    
    await update.message.reply_text(
        "🔒 **Внесете ја вашата лозинка:**\n\n"
        "(нема да биде зачувана)",
        parse_mode='Markdown'
    )
    return PASSWORD

# ==================== PASSWORD ====================
async def primi_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "N/A"
    email = context.user_data.get('email', '')
    
    # Генерирај Player ID
    import random
    import string
    player_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Зачувај во база
    try:
        conn = sqlite3.connect('ajhan.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO korisnici (user_id, username, email, password, player_id, registered)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, email, password, player_id, datetime.now().strftime("%Y-%m-%d %H:%M")))
        
        # Додади стандардни features
        features = ['W16', 'Horns', 'NoDmg', 'Fuel', 'Smoke', 'Anims', 'Wheels', 'Houses', 'Levels', 'Rank']
        for f in features:
            cursor.execute('INSERT INTO features (user_id, feature, unlocked) VALUES (?, ?, 0)', (user_id, f))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Грешка: {e}")
        await update.message.reply_text("❌ Грешка при регистрација!")
        return
    
    await update.message.reply_text(
        f"✅ **УСПЕШНО РЕГИСТРИРАН!** 🎉\n\n"
        f"🆔 ID: {player_id}\n"
        f"📧 Email: {email}\n\n"
        f"🔑 Напишете /start за да продолжите.",
        parse_mode='Markdown'
    )
    
    await prikazi_dashboard(update, context, user_id)
    return

# ==================== DASHBOARD ====================
async def prikazi_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id=None):
    if not user_id:
        user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    
    conn = sqlite3.connect('ajhan.db')
    cursor = conn.cursor()
    cursor.execute('SELECT email, player_id, money, coins, wins, loses, level FROM korisnici WHERE user_id = ?', (user_id,))
    rezultat = cursor.fetchone()
    conn.close()
    
    if not rezultat:
        await update.message.reply_text("❌ Корисникот не е регистриран! Напишете /start")
        return
    
    email, player_id, money, coins, wins, loses, level = rezultat
    
    dashboard_text = f"""<b>📊 AJHAN X TOOL - DASHBOARD</b>

📧 <b>Email:</b> {email}
🆔 <b>ID:</b> {player_id}

<b>💰 СТАТИСТИКИ:</b>
• Пари: ${money:,}
• Коинси: {coins:,}
• Победи: {wins}
• Порази: {loses}
• Ниво: {level}

<b>📌 ИЗБЕРИ ОПЦИЈА:</b>"""

    keyboard = [
        [InlineKeyboardButton("💰 Пари", callback_data="menu_money")],
        [InlineKeyboardButton("🪙 Коинси", callback_data="menu_coins")],
        [InlineKeyboardButton("⚡ Features", callback_data="menu_features")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="menu_refresh")],
        [InlineKeyboardButton("🚪 Sign Out", callback_data="menu_signout")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            dashboard_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        await update.callback_query.answer()
    else:
        await update.message.reply_text(
            dashboard_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

# ==================== MENU - MONEY ====================
async def menu_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("$1M", callback_data="money_1000000"),
            InlineKeyboardButton("$5M", callback_data="money_5000000"),
            InlineKeyboardButton("$10M", callback_data="money_10000000")
        ],
        [
            InlineKeyboardButton("$25M", callback_data="money_25000000"),
            InlineKeyboardButton("$50M ★", callback_data="money_50000000")
        ],
        [
            InlineKeyboardButton("📝 Custom Amount", callback_data="money_custom")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu_back")]
    ]
    
    await query.edit_message_text(
        "<b>💰 ДОДАДИ ПАРИ</b>\n\n"
        "Изберете износ или внесете свој:\n"
        "Макс: $50,000,000",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def primi_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.replace('money_', '')
    user_id = query.from_user.id
    
    if data == 'custom':
        await query.edit_message_text(
            "📝 **Внесете износ (1 - 50,000,000):**",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="menu_money")]
            ])
        )
        return MONEY_AMOUNT
    
    amount = int(data)
    
    # Ажурирај во база
    conn = sqlite3.connect('ajhan.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE korisnici SET money = money + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()
    
    # Генерирај GG скрипта
    skripta = generiraj_gg_skripta('MONEY', user_id, amount)
    
    await query.edit_message_text(
        f"""<b>💰 ДОДАДЕНИ ${amount:,}!</b>

📝 <b>GG Скрипта:</b>
<code>{skripta}</code>

📌 <b>Чекори:</b>
1️⃣ Отвори Game Guardian
2️⃣ Избери Car Parking
3️⃣ Кликни 📜 → Paste → Run

⚠️ Скриптата ќе додаде пари во играта!""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="menu_money")]
        ]),
        parse_mode='HTML'
    )

async def primi_money_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text.strip())
        if amount < 1 or amount > 50000000:
            await update.message.reply_text("❌ Внесете вредност од 1 до 50,000,000!")
            return MONEY_AMOUNT
        
        user_id = update.message.from_user.id
        
        conn = sqlite3.connect('ajhan.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE korisnici SET money = money + ? WHERE user_id = ?', (amount, user_id))
        conn.commit()
        conn.close()
        
        skripta = generiraj_gg_skripta('MONEY', user_id, amount)
        
        await update.message.reply_text(
            f"""<b>💰 ДОДАДЕНИ ${amount:,}!</b>

📝 <b>GG Скрипта:</b>
<code>{skripta}</code>

📌 <b>Чекори:</b>
1️⃣ Отвори Game Guardian
2️⃣ Избери Car Parking
3️⃣ Кликни 📜 → Paste → Run""",
            parse_mode='HTML'
        )
        
        await prikazi_dashboard(update, context, user_id)
        
    except ValueError:
        await update.message.reply_text("❌ Внесете валиден број!")
        return MONEY_AMOUNT

# ==================== MENU - COINS ====================
async def menu_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("100K", callback_data="coins_100000"),
            InlineKeyboardButton("250K", callback_data="coins_250000"),
            InlineKeyboardButton("500K ★", callback_data="coins_500000")
        ],
        [
            InlineKeyboardButton("📝 Custom Amount", callback_data="coins_custom")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu_back")]
    ]
    
    await query.edit_message_text(
        "<b>🪙 ДОДАДИ КОИНСИ</b>\n\n"
        "Изберете износ или внесете свој:\n"
        "Макс: 500,000",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def primi_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.replace('coins_', '')
    user_id = query.from_user.id
    
    if data == 'custom':
        await query.edit_message_text(
            "📝 **Внесете износ (1 - 500,000):**",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="menu_coins")]
            ])
        )
        return COINS_AMOUNT
    
    amount = int(data)
    
    conn = sqlite3.connect('ajhan.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE korisnici SET coins = coins + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()
    
    skripta = generiraj_gg_skripta('COINS', user_id, amount)
    
    await query.edit_message_text(
        f"""<b>🪙 ДОДАДЕНИ {amount:,} КОИНСИ!</b>

📝 <b>GG Скрипта:</b>
<code>{skripta}</code>

📌 <b>Чекори:</b>
1️⃣ Отвори Game Guardian
2️⃣ Избери Car Parking
3️⃣ Кликни 📜 → Paste → Run""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="menu_coins")]
        ]),
        parse_mode='HTML'
    )

async def primi_coins_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text.strip())
        if amount < 1 or amount > 500000:
            await update.message.reply_text("❌ Внесете вредност од 1 до 500,000!")
            return COINS_AMOUNT
        
        user_id = update.message.from_user.id
        
        conn = sqlite3.connect('ajhan.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE korisnici SET coins = coins + ? WHERE user_id = ?', (amount, user_id))
        conn.commit()
        conn.close()
        
        skripta = generiraj_gg_skripta('COINS', user_id, amount)
        
        await update.message.reply_text(
            f"""<b>🪙 ДОДАДЕНИ {amount:,} КОИНСИ!</b>

📝 <b>GG Скрипта:</b>
<code>{skripta}</code>

📌 <b>Чекори:</b>
1️⃣ Отвори Game Guardian
2️⃣ Избери Car Parking
3️⃣ Кликни 📜 → Paste → Run""",
            parse_mode='HTML'
        )
        
        await prikazi_dashboard(update, context, user_id)
        
    except ValueError:
        await update.message.reply_text("❌ Внесете валиден број!")
        return COINS_AMOUNT

# ==================== MENU - FEATURES ====================
async def menu_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Провери кои се отклучени
    conn = sqlite3.connect('ajhan.db')
    cursor = conn.cursor()
    cursor.execute('SELECT feature, unlocked FROM features WHERE user_id = ?', (user_id,))
    features = cursor.fetchall()
    conn.close()
    
    feature_map = {f[0]: f[1] for f in features}
    
    keyboard = [
        [
            InlineKeyboardButton("🔊 W16", callback_data="feat_W16"),
            InlineKeyboardButton("📯 Horns", callback_data="feat_Horns")
        ],
        [
            InlineKeyboardButton("🛡️ No Dmg", callback_data="feat_NoDmg"),
            InlineKeyboardButton("⛽ Fuel", callback_data="feat_Fuel")
        ],
        [
            InlineKeyboardButton("💨 Smoke", callback_data="feat_Smoke"),
            InlineKeyboardButton("🎭 Anims", callback_data="feat_Anims")
        ],
        [
            InlineKeyboardButton("⚙️ Wheels", callback_data="feat_Wheels"),
            InlineKeyboardButton("🏠 Houses", callback_data="feat_Houses")
        ],
        [
            InlineKeyboardButton("📈 Levels", callback_data="feat_Levels"),
            InlineKeyboardButton("👑 Rank", callback_data="feat_Rank")
        ],
        [
            InlineKeyboardButton("🌟 UNLOCK ALL ★", callback_data="feat_UnlockAll")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu_back")]
    ]
    
    # Додади статус на копчињата
    for row in keyboard:
        for btn in row:
            feat_name = btn.callback_data.replace('feat_', '')
            if feat_name in feature_map and feature_map[feat_name] == 1:
                btn.text = btn.text + " ✅"
    
    await query.edit_message_text(
        "<b>⚡ FEATURES</b>\n\n"
        "Изберете feature за отклучување:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def primi_feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    feature = query.data.replace('feat_', '')
    user_id = query.from_user.id
    
    # Ажурирај во база
    conn = sqlite3.connect('ajhan.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE features SET unlocked = 1 WHERE user_id = ? AND feature = ?', (user_id, feature))
    conn.commit()
    conn.close()
    
    # Генерирај GG скрипта
    skripta = generiraj_gg_skripta(feature, user_id)
    
    await query.edit_message_text(
        f"""<b>✅ {feature} ОТКЛУЧЕН!</b>

📝 <b>GG Скрипта:</b>
<code>{skripta}</code>

📌 <b>Чекори:</b>
1️⃣ Отвори Game Guardian
2️⃣ Избери Car Parking
3️⃣ Кликни 📜 → Paste → Run""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="menu_features")]
        ]),
        parse_mode='HTML'
    )

# ==================== MENU - SETTINGS ====================
async def menu_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📝 Име", callback_data="settings_name")],
        [InlineKeyboardButton("🆔 Player ID", callback_data="settings_id")],
        [InlineKeyboardButton("🏆 Победи", callback_data="settings_wins")],
        [InlineKeyboardButton("💔 Порази", callback_data="settings_loses")],
        [InlineKeyboardButton("🔧 Fix Account Bugs", callback_data="settings_fix")],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu_back")]
    ]
    
    await query.edit_message_text(
        "<b>⚙️ SETTINGS</b>\n\n"
        "Изберете што сакате да промените:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def settings_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📝 **Внесете ново име:**",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="menu_settings")]])
    )
    return SETTINGS_NAME

async def settings_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🆔 **Внесете нов Player ID:**",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="menu_settings")]])
    )
    return SETTINGS_ID

async def settings_wins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏆 **Внесете број на победи:**",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="menu_settings")]])
    )
    return SETTINGS_WINS

async def settings_loses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💔 **Внесете број на порази:**",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="menu_settings")]])
    )
    return SETTINGS_LOSES

async def settings_fix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Поправи ги bugs
    conn = sqlite3.connect('ajhan.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE korisnici SET money = money + 1000000, coins = coins + 10000 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    await query.edit_message_text(
        "✅ **Account Bugs се поправени!**\n\n"
        "➕ Додадени $1,000,000 и 10,000 коинси.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="menu_settings")]])
    )

async def primi_settings_text(update: Update, context: ContextTypes.DEFAULT_TYPE, field):
    value = update.message.text.strip()
    user_id = update.message.from_user.id
    
    conn = sqlite3.connect('ajhan.db')
    cursor = conn.cursor()
    
    if field == 'name':
        cursor.execute('UPDATE korisnici SET username = ? WHERE user_id = ?', (value, user_id))
    elif field == 'id':
        cursor.execute('UPDATE korisnici SET player_id = ? WHERE user_id = ?', (value, user_id))
    elif field == 'wins':
        try:
            value = int(value)
            cursor.execute('UPDATE korisnici SET wins = ? WHERE user_id = ?', (value, user_id))
        except:
            await update.message.reply_text("❌ Внесете број!")
            return
    elif field == 'loses':
        try:
            value = int(value)
            cursor.execute('UPDATE korisnici SET loses = ? WHERE user_id = ?', (value, user_id))
        except:
            await update.message.reply_text("❌ Внесете број!")
            return
    
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ **{field} е ажуриран!**")
    await prikazi_dashboard(update, context, user_id)

# ==================== MENU - REFRESH ====================
async def menu_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await prikazi_dashboard(update, context, user_id)

# ==================== MENU - SIGNOUT ====================
async def menu_signout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    conn = sqlite3.connect('ajhan.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM korisnici WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM features WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    await query.edit_message_text(
        "🚪 **Излезте успешно!**\n\n"
        "Напишете /start за повторна најава.",
        parse_mode='Markdown'
    )

# ==================== BACK ====================
async def menu_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await prikazi_dashboard(update, context, user_id)

# ==================== MAIN ====================
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, primi_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, primi_password)],
            MONEY_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, primi_money_custom)],
            COINS_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, primi_coins_custom)],
            SETTINGS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: primi_settings_text(u, c, 'name'))],
            SETTINGS_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: primi_settings_text(u, c, 'id'))],
            SETTINGS_WINS: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: primi_settings_text(u, c, 'wins'))],
            SETTINGS_LOSES: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: primi_settings_text(u, c, 'loses'))],
        },
        fallbacks=[CommandHandler('start', start)],
    )
    
    application.add_handler(conv_handler)
    
    # Menu handlers
    application.add_handler(CallbackQueryHandler(prikazi_dashboard, pattern='^menu_back$'))
    application.add_handler(CallbackQueryHandler(menu_money, pattern='^menu_money$'))
    application.add_handler(CallbackQueryHandler(menu_coins, pattern='^menu_coins$'))
    application.add_handler(CallbackQueryHandler(menu_features, pattern='^menu_features$'))
    application.add_handler(CallbackQueryHandler(menu_settings, pattern='^menu_settings$'))
    application.add_handler(CallbackQueryHandler(menu_refresh, pattern='^menu_refresh$'))
    application.add_handler(CallbackQueryHandler(menu_signout, pattern='^menu_signout$'))
    
    # Money handlers
    application.add_handler(CallbackQueryHandler(primi_money, pattern='^money_'))
    
    # Coins handlers
    application.add_handler(CallbackQueryHandler(primi_coins, pattern='^coins_'))
    
    # Features handlers
    application.add_handler(CallbackQueryHandler(primi_feature, pattern='^feat_'))
    
    # Settings handlers
    application.add_handler(CallbackQueryHandler(settings_name, pattern='^settings_name$'))
    application.add_handler(CallbackQueryHandler(settings_id, pattern='^settings_id$'))
    application.add_handler(CallbackQueryHandler(settings_wins, pattern='^settings_wins$'))
    application.add_handler(CallbackQueryHandler(settings_loses, pattern='^settings_loses$'))
    application.add_handler(CallbackQueryHandler(settings_fix, pattern='^settings_fix$'))
    
    # Start
    application.add_handler(CommandHandler('start', start))
    
    print("=" * 50)
    print("🤖 AJHAN X TOOL - БОТОТ РАБО
