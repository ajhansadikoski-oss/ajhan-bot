import logging
import sqlite3
import os
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
ADMIN_MENU, CEKA_BRISI_ID, CEKA_CUSTOM_DAYS, ADMIN_ODOBRI_LICENCA = range(4)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8674559116:AAFuZWJJLVY-qMAHBSr7Z6om686b1zeGxKc")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8694942406"))

# ==================== БАЗА ====================
def inicijaliziraj_baza():
    try:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS korisnici (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                istekuvanje TEXT,
                datum_dodeluvanje TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS baranja_za_pari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                iznos TEXT,
                datum TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Базата е креирана")
        return True
    except Exception as e:
        logger.error(f"❌ Грешка при креирање на база: {e}")
        return False

inicijaliziraj_baza()

# ==================== GG СКРИПТИ ====================
def generiraj_gg_skripta(funkcija, user_id):
    """ВИСТИНСКИ GG СКРИПТИ - 30K КОИНСИ + 50M ПАРИ"""
    
    if funkcija == "PARI":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.setVisible(false)

-- 💰 50,000,000 ПАРИ
gg.searchNumber('1000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('50000000', gg.TYPE_DWORD)

gg.searchNumber('5000', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('50000000', gg.TYPE_DWORD)

gg.searchNumber('10000', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('50000000', gg.TYPE_DWORD)

gg.toast('💰 ДОДАДЕНИ $50,000,000!')
gg.alert('✅ УСПЕШНО! 50,000,000 пари се додадени!')"""
    
    elif funkcija == "COINS":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.setVisible(false)

-- 🪙 30,000 КОИНСИ
gg.searchNumber('100', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('30000', gg.TYPE_DWORD)

gg.searchNumber('500', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('30000', gg.TYPE_DWORD)

gg.searchNumber('1000', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('30000', gg.TYPE_DWORD)

gg.toast('🪙 ДОДАДЕНИ 30,000 КОИНСИ!')
gg.alert('✅ УСПЕШНО! 30,000 коинси се додадени!')"""
    
    elif funkcija == "PARI_COINS":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.setVisible(false)

-- 💰 50,000,000 ПАРИ
gg.searchNumber('1000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('50000000', gg.TYPE_DWORD)

gg.searchNumber('5000', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('50000000', gg.TYPE_DWORD)

gg.searchNumber('10000', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('50000000', gg.TYPE_DWORD)

-- 🪙 30,000 КОИНСИ
gg.searchNumber('100', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('30000', gg.TYPE_DWORD)

gg.searchNumber('500', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('30000', gg.TYPE_DWORD)

gg.searchNumber('1000', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('30000', gg.TYPE_DWORD)

gg.toast('💰 $50,000,000 + 🪙 30,000 КОИНСИ!')
gg.alert('✅ УСПЕШНО! Пари и коинси се додадени!')"""
    
    elif funkcija == "UnlockAll":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.setVisible(false)

-- 💰 50,000,000 ПАРИ
gg.searchNumber('1000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('50000000', gg.TYPE_DWORD)

-- 🪙 30,000 КОИНСИ
gg.searchNumber('100', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('30000', gg.TYPE_DWORD)

-- W16
gg.searchNumber('2000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('5000', gg.TYPE_DWORD)

-- ХОРНИ
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(1000)
gg.editAll('1', gg.TYPE_DWORD)

-- БЕЗ ШТЕТА
gg.searchNumber('100', gg.TYPE_FLOAT)
gg.getResults(50)
gg.editAll('999999', gg.TYPE_FLOAT)

-- ГОРИВО
gg.searchNumber('100', gg.TYPE_FLOAT)
gg.getResults(50)
gg.editAll('999999', gg.TYPE_FLOAT)

-- ЧАД
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('1', gg.TYPE_DWORD)

-- АНИМАЦИИ
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(500)
gg.editAll('1', gg.TYPE_DWORD)

-- ТРКАЛА
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(200)
gg.editAll('1', gg.TYPE_DWORD)

-- КУЌИ
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('1', gg.TYPE_DWORD)

-- НИВО
gg.searchNumber('1', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('999', gg.TYPE_DWORD)

-- РАНГ
gg.searchNumber('1', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('999999', gg.TYPE_DWORD)

gg.toast('🌟 СЕ Е ОТКЛУЧЕНО!')
gg.alert('🎉 50M Пари + 30K Коинси + СЕ!')"""
    
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
    
    elif funkcija == "Animations":
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
    
    else:
        return "-- Непозната функција"

# ==================== СТАРТ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "N/A"
    first_name = update.message.from_user.first_name or "User"
    
    logger.info(f"📱 START од {user_id} (@{username})")

    # ===== АДМИН =====
    if user_id == ADMIN_ID:
        try:
            conn = sqlite3.connect('licenci.db')
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM korisnici WHERE user_id = ?', (user_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO korisnici (user_id, username, first_name, status, istekuvanje) 
                    VALUES (?, ?, ?, 'approved', 'forever')
                ''', (user_id, "admin", "Admin"))
                conn.commit()
            else:
                cursor.execute('UPDATE korisnici SET status = "approved", istekuvanje = "forever" WHERE user_id = ?', (user_id,))
                conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Грешка: {e}")
        
        await prikazi_admin_panel(update)
        return ADMIN_MENU

    # ===== НОРМАЛЕН КОРИСНИК =====
    try:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT status, istekuvanje FROM korisnici WHERE user_id = ?', (user_id,))
        rezultat = cursor.fetchone()
        conn.close()
    except:
        rezultat = None
    
    if not rezultat:
        try:
            conn = sqlite3.connect('licenci.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO korisnici (user_id, username, first_name, status, datum_dodeluvanje) 
                VALUES (?, ?, ?, 'pending', ?)
            ''', (user_id, username, first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Грешка: {e}")
            await update.message.reply_text("❌ Грешка при зачувување!")
            return
        
        await update.message.reply_text(
            f"✅ **Барањето е испратено!**\n\n"
            f"👤 @{username}\n"
            f"🆔 `{user_id}`\n\n"
            f"📌 Почекајте администраторот.",
            parse_mode='Markdown'
        )
        
        tastatura = [
            [InlineKeyboardButton("♾️ Forever", callback_data=f"lic_forever_{user_id}")],
            [InlineKeyboardButton("📅 30 Days", callback_data=f"lic_30_{user_id}")],
            [InlineKeyboardButton("📅 7 Days", callback_data=f"lic_7_{user_id}")],
            [InlineKeyboardButton("📝 Custom", callback_data=f"lic_custom_{user_id}")],
            [InlineKeyboardButton("❌ Deny", callback_data=f"lic_deny_{user_id}")]
        ]
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **НОВО БАРАЊЕ!**\n\n"
                 f"👤 {first_name}\n"
                 f"🆔 `{user_id}`\n"
                 f"📌 @{username}\n"
                 f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            reply_markup=InlineKeyboardMarkup(tastatura),
            parse_mode='Markdown'
        )
        return
    
    status, istekuvanje = rezultat
    
    if status == 'denied':
        await update.message.reply_text("❌ **Одбиен!**", parse_mode='Markdown')
        return
    
    if status == 'pending':
        await update.message.reply_text("⏳ **Чекате одобрување!**", parse_mode='Markdown')
        return
    
    if status == 'approved':
        if istekuvanje and istekuvanje != "forever":
            try:
                istek_datum = datetime.strptime(istekuvanje, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > istek_datum:
                    await update.message.reply_text("❌ **Лиценцата истекна!**", parse_mode='Markdown')
                    return
            except:
                pass
        
        await prikazi_gg_menu(update, context)
        return
    
    if status == 'expired':
        await update.message.reply_text("❌ **Лиценцата истекна!**", parse_mode='Markdown')
        return

# ==================== GG МЕНИ ====================
async def prikazi_gg_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user_id = query.from_user.id if query else update.message.from_user.id
    
    try:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username, istekuvanje FROM korisnici WHERE user_id = ?', (user_id,))
        rezultat = cursor.fetchone()
        conn.close()
    except:
        rezultat = None
    
    username = rezultat[0] if rezultat else "N/A"
    istek = rezultat[1] if rezultat else "N/A"
    
    if istek != "forever" and istek != "N/A" and istek:
        try:
            istek_datum = datetime.strptime(istek, "%Y-%m-%d %H:%M:%S")
            preostanato = istek_datum - datetime.now()
            if preostanato.days > 0:
                istek = f"{preostanato.days} дена"
            else:
                istek = "🔴 ИСТЕКНА"
        except:
            pass
    
    menu_text = f"""<b>🎮 GAME GUARDIAN - CAR PARKING</b>

👤 <b>Корисник:</b> @{username}
🆔 <b>ID:</b> {user_id}
📅 <b>Лиценца:</b> {istek}

<b>⚡ ИЗБЕРИ ФУНКЦИЈА:</b>"""

    keyboard = [
        [InlineKeyboardButton("💰 50M ПАРИ", callback_data="gg_money")],
        [InlineKeyboardButton("🪙 30K КОИНСИ", callback_data="gg_coins")],
        [InlineKeyboardButton("💎 50M + 30K", callback_data="gg_pari_coins")],
        [InlineKeyboardButton("🔊 W16", callback_data="gg_w16"), InlineKeyboardButton("📯 Horns", callback_data="gg_horns")],
        [InlineKeyboardButton("🛡️ No Dmg", callback_data="gg_nodmg"), InlineKeyboardButton("⛽ Fuel", callback_data="gg_fuel")],
        [InlineKeyboardButton("💨 Smoke", callback_data="gg_smoke"), InlineKeyboardButton("🎭 Animations", callback_data="gg_animations")],
        [InlineKeyboardButton("⚙️ Wheels", callback_data="gg_wheels"), InlineKeyboardButton("🏠 Houses", callback_data="gg_houses")],
        [InlineKeyboardButton("📈 Levels", callback_data="gg_levels"), InlineKeyboardButton("👑 Rank", callback_data="gg_rank")],
        [InlineKeyboardButton("🌟 UNLOCK ALL ★", callback_data="gg_unlock_all")]
    ]
    
    if query:
        await query.edit_message_text(
            menu_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        await query.answer()
    else:
        await update.message.reply_text(
            menu_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

# ==================== GG ФУНКЦИЈА ====================
async def gg_funkcija(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    funkcija = query.data.replace('gg_', '')
    
    # Провери лиценца
    try:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT status, istekuvanje FROM korisnici WHERE user_id = ?', (user_id,))
        rezultat = cursor.fetchone()
        conn.close()
    except:
        rezultat = None
    
    if not rezultat or rezultat[0] != 'approved':
        await query.edit_message_text("❌ **Немате лиценца!**", parse_mode='Markdown')
        return
    
    if rezultat[1] and rezultat[1] != "forever":
        try:
            istek_datum = datetime.strptime(rezultat[1], "%Y-%m-%d %H:%M:%S")
            if datetime.now() > istek_datum:
                await query.edit_message_text("❌ **Лиценцата истекна!**", parse_mode='Markdown')
                return
        except:
            pass
    
    # Генерирај скрипта
    funkcii = {
        'money': '💰 50M ПАРИ',
        'coins': '🪙 30K КОИНСИ',
        'pari_coins': '💎 50M + 30K',
        'w16': 'W16 Motor',
        'horns': 'Хорни',
        'nodmg': 'Без Штета',
        'fuel': 'Гориво',
        'smoke': 'Чад',
        'animations': 'Анимации',
        'wheels': 'Тркала',
        'houses': 'Куќи',
        'levels': 'Нивоа',
        'rank': 'Ранг',
        'unlock_all': '🌟 UNLOCK ALL'
    }
    
    ime = funkcii.get(funkcija, funkcija)
    
    if funkcija == 'unlock_all':
        skripta = generiraj_gg_skripta('UnlockAll', user_id)
    elif funkcija == 'money':
        skripta = generiraj_gg_skripta('PARI', user_id)
    elif funkcija == 'coins':
        skripta = generiraj_gg_skripta('COINS', user_id)
    elif funkcija == 'pari_coins':
        skripta = generiraj_gg_skripta('PARI_COINS', user_id)
    else:
        skripta = generiraj_gg_skripta(funkcija.capitalize(), user_id)
    
    await query.edit_message_text(
        f"""<b>🎮 {ime} - GG СКРИПТА</b>

📝 <b>Копирај ја скриптата:</b>

<code>{skripta}</code>

📌 <b>Чекори:</b>
1️⃣ Отвори Game Guardian
2️⃣ Избери Car Parking Multiplayer
3️⃣ Кликни на иконата 📜
4️⃣ Paste - Вметни
5️⃣ Run - Изврши

⚠️ <b>ВАЖНО:</b> Скриптата работи САМО со активна лиценца!""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 КОПИРАЈ", callback_data=f"copy_{funkcija}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="gg_menu")]
        ]),
        parse_mode='HTML'
    )

# ==================== КОПИРАЈ СКРИПТА ====================
async def copy_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    funkcija = query.data.replace('copy_', '')
    user_id = query.from_user.id
    
    if funkcija == 'unlock_all':
        skripta = generiraj_gg_skripta('UnlockAll', user_id)
    elif funkcija == 'money':
        skripta = generiraj_gg_skripta('PARI', user_id)
    elif funkcija == 'coins':
        skripta = generiraj_gg_skripta('COINS', user_id)
    elif funkcija == 'pari_coins':
        skripta = generiraj_gg_skripta('PARI_COINS', user_id)
    else:
        skripta = generiraj_gg_skripta(funkcija.capitalize(), user_id)
    
    await query.edit_message_text(
        f"<b>📋 СКРИПТА ЗА КОПИРАЊЕ</b>\n\n"
        f"<code>{skripta}</code>\n\n"
        f"📌 Селектирај и копирај (Ctrl+C)",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="gg_menu")]
        ])
    )

# ==================== АДМИН ПАНЕЛ ====================
async def prikazi_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM korisnici')
        vkupno = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status = "approved"')
        aktivni = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status = "pending"')
        baranja = cursor.fetchone()[0]
        conn.close()
    except:
        vkupno = aktivni = baranja = 0
    
    admin_text = f"""<b>👑 АДМИН ПАНЕЛ</b>

📊 <b>Статистика:</b>
• Вкупно: {vkupno}
• Активни: {aktivni}
• Барања: {baranja}"""

    keyboard = [
        [InlineKeyboardButton("📋 Корисници", callback_data="admin_users")],
        [InlineKeyboardButton("❌ Бриши", callback_data="admin_remove")],
        [InlineKeyboardButton("💵 Барања за Пари", callback_data="admin_money")],
        [InlineKeyboardButton("🔧 Поправи", callback_data="admin_fix_user")],
        [InlineKeyboardButton("🎮 GG МЕНИ", callback_data="gg_menu")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        await update.callback_query.answer()
    else:
        await update.message.reply_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

# ==================== АДМИН ФУНКЦИИ ====================
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, status, istekuvanje FROM korisnici')
        users = cursor.fetchall()
        conn.close()
    except:
        users = []
    
    if not users:
        await query.edit_message_text("📋 Нема корисници.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin_back")]]))
        return
    
    tekst = "<b>📋 КОРИСНИЦИ:</b>\n\n"
    for user in users[:20]:
        emoji = "✅" if user[2] == "approved" else "⏳" if user[2] == "pending" else "❌"
        istek = user[3] or "Нема"
        if istek != "forever" and istek != "Нема":
            try:
                d = datetime.strptime(istek, "%Y-%m-%d %H:%M:%S")
                if d > datetime.now():
                    istek = f"{(d - datetime.now()).days} дена"
                else:
                    istek = "🔴 ИСТЕКНА"
            except:
                pass
        tekst += f"{emoji} {user[0]} | @{user[1] or 'N/A'} | {istek}\n"
    
    await query.edit_message_text(
        tekst,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin_back")]])
    )

async def admin_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Внесете ID:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin_back")]]))
    return CEKA_BRISI_ID

async def primi_id_za_brisenje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ Валиден ID!")
        return CEKA_BRISI_ID
    
    try:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM korisnici WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM baranja_za_pari WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    except:
        pass
    
    await update.message.reply_text(f"✅ Избришан {user_id}")
    await prikazi_admin_panel(update)
    return ADMIN_MENU

async def admin_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, iznos FROM baranja_za_pari WHERE status="pending"')
        requests = cursor.fetchall()
        conn.close()
    except:
        requests = []
    
    if not requests:
        await query.edit_message_text("💵 Нема барања.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin_back")]]))
        return
    
    tekst = "<b>💵 БАРАЊА ЗА ПАРИ</b>\n\n"
    for req in requests:
        tekst += f"{req[0]} | @{req[1] or 'N/A'} | {req[2]}\n"
    
    await query.edit_message_text(tekst, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin_back")]]))

async def admin_fix_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Внесете ID за поправка:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin_back")]]))
    return ADMIN_ODOBRI_LICENCA

async def primi_fix_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ Валиден ID!")
        return ADMIN_ODOBRI_LICENCA
    
    try:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        novo = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('UPDATE korisnici SET status = "approved", istekuvanje = ? WHERE user_id = ?', (novo, user_id))
        conn.commit()
        conn.close()
    except:
        pass
    
    await update.message.reply_text(f"✅ Поправен {user_id} (7 дена)")
    await prikazi_admin_panel(update)
    return ADMIN_MENU

# ==================== LICENCA HANDLER ====================
async def licenca_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    akcija = data[1]
    user_id = int(data[2])
    
    if akcija == "custom":
        context.user_data['custom_user_id'] = user_id
        await query.edit_message_text("Внесете денови (1-30):")
        return CEKA_CUSTOM_DAYS
    
    if akcija == "deny":
        try:
            conn = sqlite3.connect('licenci.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE korisnici SET status = "denied" WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
        except:
            pass
        await query.edit_message_text(f"❌ Одбиен {user_id}")
        return
    
    # Одобри
    if akcija == "forever":
        istekuvanje = "forever"
        opis = "Forever"
    else:
        istekuvanje = (datetime.now() + timedelta(days=int(akcija))).strftime("%Y-%m-%d %H:%M:%S")
        opis = f"{akcija} дена"
    
    try:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE korisnici SET status = "approved", istekuvanje = ? WHERE user_id = ?', (istekuvanje, user_id))
        conn.commit()
        conn.close()
    except:
        pass
    
    await query.edit_message_text(f"✅ Одобрен {user_id} ({opis})")
    
    try:
        await context.bot.send_message(
            user_id,
            f"✅ **ДОБИВТЕ ПРИСТАП!** 🎉\n\n📅 {opis}\n🔑 /start",
            parse_mode='Markdown'
        )
    except:
        pass

async def primi_custom_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text.strip())
        if days < 1 or days > 30:
            await update.message.reply_text("❌ 1-30!")
            return CEKA_CUSTOM_DAYS
        
        user_id = context.user_data.get('custom_user_id')
        if not user_id:
            await update.message.reply_text("❌ Грешка!")
            return
        
        istekuvanje = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE korisnici SET status = "approved", istekuvanje = ? WHERE user_id = ?', (istekuvanje, user_id))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(f"✅ Одобрен! ({days} дена)")
        
        try:
            await context.bot.send_message(
                user_id,
                f"✅ **ДОБИВТЕ ПРИСТАП!** 🎉\n\n📅 {days} дена\n🔑 /start",
                parse_mode='Markdown'
            )
        except:
            pass
        
        del context.user_data['custom_user_id']
        await prikazi_admin_panel(update)
        
    except:
        await update.message.reply_text("❌ Внесете број!")
        return CEKA_CUSTOM_DAYS

# ==================== MAIN ====================
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ADMIN_MENU: [
                CallbackQueryHandler(prikazi_admin_panel, pattern='^admin_back$'),
                CallbackQueryHandler(admin_users, pattern='^admin_users$'),
                CallbackQueryHandler(admin_remove, pattern='^admin_remove$'),
                CallbackQueryHandler(admin_money, pattern='^admin_money$'),
                CallbackQueryHandler(admin_fix_user, pattern='^admin_fix_user$'),
            ],
            CEKA_BRISI_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, primi_id_za_brisenje)
            ],
            CEKA_CUSTOM_DAYS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND
