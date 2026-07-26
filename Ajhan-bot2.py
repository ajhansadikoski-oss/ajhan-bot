import logging
import sqlite3
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
    ConversationHandler
)

# ===== LOGGING =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8674559116:AAFuzWJJLVY-qMAHBSr7Z6om686b1zeGxKc"
ADMIN_ID = 8694942406

# ===== КОНВЕРЗАЦИСКИ СОСТОЈБИ =====
CEKA_EMAIL, CEKA_PASSWORD, GLAVNO_MENI = range(3)

# ===== БАЗА ЗА ЛИЦЕНЦИ =====
def inicijaliziraj_baza():
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS korisnici (user_id INTEGER PRIMARY KEY, istekuvanje TEXT)')
    conn.commit()
    conn.close()

inicijaliziraj_baza()

# ===== БАЗА ЗА ПАРКИНГ =====
def init_parking_db():
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS parking_users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        car_number TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS parking_reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        spot_number INTEGER,
        car_number TEXT,
        start_time TEXT,
        end_time TEXT,
        status TEXT DEFAULT 'active'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS parking_spots (
        spot_number INTEGER PRIMARY KEY,
        is_occupied INTEGER DEFAULT 0
    )''')
    for i in range(1, 21):
        c.execute('INSERT OR IGNORE INTO parking_spots (spot_number) VALUES (?)', (i,))
    conn.commit()
    conn.close()

init_parking_db()

# ===== ПАРКИНГ ФУНКЦИИ =====
def get_free_spots():
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('SELECT spot_number FROM parking_spots WHERE is_occupied = 0')
        spots = [row[0] for row in c.fetchall()]
        conn.close()
        return spots
    except Exception as e:
        logger.error(f"get_free_spots error: {e}")
        return []

def occupy_spot(spot_number, user_id, car_number, hours):
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        start_time = datetime.now().isoformat()
        end_time = (datetime.now() + timedelta(hours=hours)).isoformat()
        c.execute('INSERT INTO parking_reservations (user_id, spot_number, car_number, start_time, end_time) VALUES (?, ?, ?, ?, ?)',
                  (user_id, spot_number, car_number, start_time, end_time))
        c.execute('UPDATE parking_spots SET is_occupied = 1 WHERE spot_number = ?', (spot_number,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"occupy_spot error: {e}")
        return False

def get_active_reservations(user_id):
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('SELECT * FROM parking_reservations WHERE user_id = ? AND status = "active"', (user_id,))
        res = c.fetchall()
        conn.close()
        return res
    except Exception as e:
        logger.error(f"get_active_reservations error: {e}")
        return []

def free_spot(reservation_id):
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('SELECT spot_number FROM parking_reservations WHERE id = ?', (reservation_id,))
        spot = c.fetchone()
        if spot:
            c.execute('UPDATE parking_spots SET is_occupied = 0 WHERE spot_number = ?', (spot[0],))
            c.execute('UPDATE parking_reservations SET status = "completed" WHERE id = ?', (reservation_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"free_spot error: {e}")
        return False

def register_parking_user(user_id, username, full_name):
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO parking_users (user_id, username, full_name) VALUES (?, ?, ?)',
                  (user_id, username, full_name))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"register_parking_user error: {e}")

def update_car(user_id, car_number):
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('UPDATE parking_users SET car_number = ? WHERE user_id = ?', (car_number, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"update_car error: {e}")

def get_user_car(user_id):
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('SELECT car_number FROM parking_users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"get_user_car error: {e}")
        return None

# ===== КОМАНДИ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Nema Username"
    first_name = update.message.from_user.first_name
    
    # Регистрирај за паркинг
    register_parking_user(user_id, username, first_name)

    # Провери лиценца
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT istekuvanje FROM korisnici WHERE user_id = ?', (user_id,))
    rezultat = cursor.fetchone()
    conn.close()

    sega = datetime.now()
    dozvolen = False

    if rezultat:
        istekuvanje_str = rezultat[0]
        if istekuvanje_str == "forever":
            dozvolen = True
        else:
            try:
                istekuvanje_datum = datetime.strptime(istekuvanje_str, "%Y-%m-%d %H:%M:%S")
                dozvolen = sega < istekuvanje_datum
            except Exception: pass

    if not dozvolen:
        await update.message.reply_text("❌ Немаш активна лиценца.\nБарањето за пристап е испратено до сопственикот.")
        tastatura = [
            [InlineKeyboardButton("♾️ Forever", callback_data=f"lic_forever_{user_id}"), InlineKeyboardButton("📅 30 Days", callback_data=f"lic_30_{user_id}")],
            [InlineKeyboardButton("📅 7 Days", callback_data=f"lic_7_{user_id}"), InlineKeyboardButton("❌ Deny", callback_data=f"lic_deny_{user_id}")]
        ]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **Барање за пристап** од {first_name} (@{username})\nID: `{user_id}`",
            reply_markup=InlineKeyboardMarkup(tastatura),
            parse_mode='Markdown'
        )
        return

    datum_sega = sega.strftime("%d %b %Y • %I:%M %p")
    welcome_text = (
        "--------------------------------------------------\n"
        "🎮 **CPM_AJHAN_BOT v5.0**\n"
        "--------------------------------------------------\n\n"
        "              **WELCOME**              \n"
        "┌───────────────────┐\n"
        "  👤 @{username}\n"
        "  🆔 `{user_id}`\n"
        "  📅 {datum_sega}\n"
        "└───────────────────┘\n\n"
        "▶ _Избери опција:_"
    ).format(username=username, user_id=user_id, datum_sega=datum_sega)

    keyboard = [
        [InlineKeyboardButton("🔐 CPM Sign In", callback_data='cpm_signin')],
        [InlineKeyboardButton("🚗 Паркинг систем", callback_data='parking_menu')]
    ]
    await update.message.reply_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ===== ПАРКИНГ МЕНИ =====
async def parking_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    keyboard = [
        [InlineKeyboardButton("🚗 Виж слободни места", callback_data='parking_free')],
        [InlineKeyboardButton("📝 Регистрирај кола", callback_data='parking_register_car')],
        [InlineKeyboardButton("📋 Мои резервации", callback_data='parking_my_res')],
        [InlineKeyboardButton("🆘 Помош", callback_data='parking_help')],
        [InlineKeyboardButton("◀ Назад", callback_data='parking_back')]
    ]
    
    await query.edit_message_text(
        "🚗 **ПАРКИНГ СИСТЕМ**\n"
        "--------------------------------------------------\n\n"
        "Добредојде во системот за паркинг!\n"
        "Избери опција:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def parking_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    free = get_free_spots()
    if free:
        text = f"🟢 Слободни места: {', '.join(map(str, free))}\n\n"
        text += "За резервација напиши:\n/reserve [број] [часови]\n"
        text += "Пример: /reserve 5 2"
    else:
        text = "🔴 Нема слободни места!"
    
    keyboard = [[InlineKeyboardButton("◀ Назад", callback_data='parking_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def parking_register_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📝 Внеси го бројот на колата.\n"
        "Пример: CA1234AB\n\n"
        "Користи команда: /setcar [број]\n\n"
        "На пример: /setcar SK1234AB"
    )

async def parking_my_res(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    res = get_active_reservations(user_id)
    if res:
        text = "📋 Твоите резервации:\n\n"
        for r in res:
            text += f"📍 Место {r[2]} | Кола: {r[3]}\n"
            text += f"⏰ До: {r[5][:16]}\n"
            text += f"🆔 ID: {r[0]}\n\n"
        text += "За ослободување: /free [ID]"
    else:
        text = "Немаш активни резервации."
    
    keyboard = [[InlineKeyboardButton("◀ Назад", callback_data='parking_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def parking_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    help_text = (
        "📖 **Помош за паркинг:**\n\n"
        "/reserve [место] [часови] - Резервирај место\n"
        "/free [ID] - Ослободи резервација\n"
        "/setcar [број] - Внеси број на кола\n"
        "/myres - Мои резервации\n"
        "/spots - Слободни места\n\n"
        "Пример: /reserve 5 2 (за 2 часа)"
    )
    keyboard = [[InlineKeyboardButton("◀ Назад", callback_data='parking_menu')]]
    await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def parking_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Врати се на главното мени - повтори го start
    user_id = query.from_user.id
    username = query.from_user.username or "Nema Username"
    first_name = query.from_user.first_name
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT istekuvanje FROM korisnici WHERE user_id = ?', (user_id,))
    rezultat = cursor.fetchone()
    conn.close()

    sega = datetime.now()
    dozvolen = False

    if rezultat:
        istekuvanje_str = rezultat[0]
        if istekuvanje_str == "forever":
            dozvolen = True
        else:
            try:
                istekuvanje_datum = datetime.strptime(istekuvanje_str, "%Y-%m-%d %H:%M:%S")
                dozvolen = sega < istekuvanje_datum
            except Exception: pass

    datum_sega = sega.strftime("%d %b %Y • %I:%M %p")
    welcome_text = (
        "--------------------------------------------------\n"
        "🎮 **CPM_AJHAN_BOT v5.0**\n"
        "--------------------------------------------------\n\n"
        "              **WELCOME**              \n"
        "┌───────────────────┐\n"
        "  👤 @{username}\n"
        "  🆔 `{user_id}`\n"
        "  📅 {datum_sega}\n"
        "└───────────────────┘\n\n"
        "▶ _Избери опција:_"
    ).format(username=username, user_id=user_id, datum_sega=datum_sega)

    keyboard = [
        [InlineKeyboardButton("🔐 CPM Sign In", callback_data='cpm_signin')],
        [InlineKeyboardButton("🚗 Паркинг систем", callback_data='parking_menu')]
    ]
    await query.edit_message_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ===== CPM КОМАНДИ =====
async def obraboti_klikovi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # ЛИЦЕНЦИ
    if data.startswith("lic_"):
        if query.from_user.id != ADMIN_ID: return
        delovi = data.split("_")
        akcija, target_user_id = delovi[1], int(delovi[2])
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        if akcija == "deny":
            cursor.execute('DELETE FROM korisnici WHERE user_id = ?', (target_user_id,))
            tekst, poraka = "❌ Одбиен", "❌ Твоето барање е одбиено."
        else:
            if akcija == "forever": vrednost, tekst = "forever", "✅ Одобрен засекогаш"
            elif akcija == "30": vrednost, tekst = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"), "✅ Одобрен на 30 дена"
            elif akcija == "7": vrednost, tekst = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"), "✅ Одобрен на 7 дена"
            cursor.execute('INSERT OR REPLACE INTO korisnici (user_id, istekuvanje) VALUES (?, ?)', (target_user_id, vrednost))
            poraka = f"🎉 Администраторот ти одобри пристап {tekst}! Стисни /start за да почнеш."
        conn.commit()
        conn.close()
        await query.edit_message_text(text=f"{query.message.text}\n\nСтатус: {tekst}")
        try: await context.bot.send_message(chat_id=target_user_id, text=poraka)
        except Exception: pass
        return

    # ПАРКИНГ
    if data == 'parking_menu':
        await parking_menu(update, context)
        return
    
    if data == 'parking_free':
        await parking_free(update, context)
        return
    
    if data == 'parking_register_car':
        await parking_register_car(update, context)
        return
    
    if data == 'parking_my_res':
        await parking_my_res(update, context)
        return
    
    if data == 'parking_help':
        await parking_help(update, context)
        return
    
    if data == 'parking_back':
        await parking_back(update, context)
        return

    # CPM
    if data == 'cpm_signin':
        email_text = (
            "--------------------------------------------------\n"
            "📧 **ENTER EMAIL**\n"
            "--------------------------------------------------\n\n"
            "Type your CPM email:"
        )
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data='cpm_cancel')]]
        await query.edit_message_text(text=email_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        context.user_data['состојба'] = 'чека_емаил'
        return

    if data == 'cpm_cancel':
        context.user_data.clear()
        await query.edit_message_text(text="❌ Процесот е откажан. Пишете /start за почеток.")
        return

    if data == 'vnes_uspesen':
        dashboard_text = (
            "--------------------------------------------------\n"
            "🗂️ **DASHBOARD**\n"
            "--------------------------------------------------\n\n"
            "       **ACCOUNT**       \n"
            "📧 `{email}`\n"
            "👤 {first_name}\n\n"
            "▶ _Select an option below:_"
        ).format(email=context.user_data.get('cpm_email', 'N/A'), first_name=query.from_user.first_name)
        
        keyboard = [
            [InlineKeyboardButton("💰 Money", callback_data='meni_money'), InlineKeyboardButton("🪙 Coins", callback_data='meni_coins')],
            [InlineKeyboardButton("⚡ Features", callback_data='meni_features')],
            [InlineKeyboardButton("🚪 Sign Out", callback_data='cpm_cancel')]
        ]
        await query.edit_message_text(text=dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data == 'meni_money':
        money_text = (
            "--------------------------------------------------\n"
            "💰 **MONEY**\n"
            "--------------------------------------------------\n\n"
            "Max: $50,000,000"
        )
        keyboard = [
            [InlineKeyboardButton("$1M", callback_data='inj_1M'), InlineKeyboardButton("$5M", callback_data='inj_5M'), InlineKeyboardButton("$10M", callback_data='inj_10M')],
            [InlineKeyboardButton("$25M", callback_data='inj_25M'), InlineKeyboardButton("$50M ★", callback_data='inj_50M')],
            [InlineKeyboardButton("✏️ Custom Amount", callback_data='inj_custom')],
            [InlineKeyboardButton("◀ Back", callback_data='vnes_uspesen')]
        ]
        await query.edit_message_text(text=money_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data == 'meni_coins':
        coins_text = (
            "--------------------------------------------------\n"
            "🪙 **COINS**\n"
            "--------------------------------------------------\n\n"
            "Max: 500,000"
        )
        keyboard = [
            [InlineKeyboardButton("100K", callback_data='inj_100k'), InlineKeyboardButton("250K", callback_data='inj_250k'), InlineKeyboardButton("500K ★", callback_data='inj_500k')],
            [InlineKeyboardButton("✏️ Custom Amount", callback_data='inj_custom')],
            [InlineKeyboardButton("◀ Back", callback_data='vnes_uspesen')]
        ]
        await query.edit_message_text(text=coins_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data == 'meni_features':
        features_text = (
            "--------------------------------------------------\n"
            "⚡ **FEATURES**\n"
            "--------------------------------------------------\n\n"
            "Select a feature or UNLOCK ALL:"
        )
        keyboard = [
            [InlineKeyboardButton("🚀 ★ UNLOCK ALL ★ 🚀", callback_data='inj_all')],
            [InlineKeyboardButton("◀ Back", callback_data='vnes_uspesen')]
        ]
        await query.edit_message_text(text=features_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data.startswith("inj_"):
        await query.edit_message_text(text="⚠️ **AJHAN INJECTOR v5.0** ⚠️\n\n🌐 Поврзување со CPM Cloud...\n🛡️ Деактивирање на анти-чит систем...\n✅ Успешно аплицирано! Опцијата ќе се појави на вашиот профил за 5-10 минути.")
        await asyncio.sleep(2)
        dashboard_text = (
            "--------------------------------------------------\n"
            "🗂️ **DASHBOARD**\n"
            "--------------------------------------------------\n\n"
            "       **ACCOUNT**       \n"
            "📧 `{email}`\n"
            "👤 {first_name}\n\n"
            "▶ _Select an option below:_"
        ).format(email=context.user_data.get('cpm_email', 'N/A'), first_name=query.from_user.first_name)
        keyboard = [
            [InlineKeyboardButton("💰 Money", callback_data='meni_money'), InlineKeyboardButton("🪙 Coins", callback_data='meni_coins')],
            [InlineKeyboardButton("⚡ Features", callback_data='meni_features')],
            [InlineKeyboardButton("🚪 Sign Out", callback_data='cpm_cancel')]
        ]
        try: 
            await query.message.reply_text(text=dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        except Exception: 
            pass

# ===== ПАРКИНГ КОМАНДИ =====
async def reserve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    car_number = get_user_car(user_id)
    
    if not car_number:
        await update.message.reply_text("⚠️ Прво внеси кола!\nКористи: /setcar [број]")
        return
    
    try:
        spot = int(context.args[0])
        hours = float(context.args[1]) if len(context.args) > 1 else 1
    except:
        await update.message.reply_text("❌ Грешен формат!\nКористи: /reserve [број] [часови]\nПример: /reserve 5 2")
        return
    
    free = get_free_spots()
    if spot not in free:
        await update.message.reply_text(f"❌ Место {spot} не е слободно!")
        return
    
    if hours > 24:
        await update.message.reply_text("❌ Максимум 24 часа!")
        return
    
    if occupy_spot(spot, user_id, car_number, hours):
        await update.message.reply_text(f"✅ Резервирано место {spot} за {hours} часа!\nКола: {car_number}")
    else:
        await update.message.reply_text("❌ Грешка при резервација!")

async def free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ Користи: /free [ID]")
        return
    
    if free_spot(res_id):
        await update.message.reply_text(f"✅ Ослободена резервација {res_id}!")
    else:
        await update.message.reply_text("❌ Грешка при ослободување!")

async def setcar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Користи: /setcar [број на кола]")
        return
    car = context.args[0].upper()
    update_car(update.effective_user.id, car)
    await update.message.reply_text(f"✅ Кола {car} е регистрирана!")

async def myres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = get_active_reservations(update.effective_user.id)
    if res:
        text = "📋 Твоите резервации:\n\n"
        for r in res:
            text += f"🆔 {r[0]} | Место {r[2]} | {r[3]}\n"
            text += f"⏰ До: {r[5][:16]}\n\n"
    else:
        text = "Немаш резервации."
    await update.message.reply_text(text)

async def spots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    free = get_free_spots()
    if free:
        await update.message.reply_text(f"🟢 Слободни места: {', '.join(map(str, free))}")
    else:
        await update.message.reply_text("🔴 Нема слободни места!")

# ===== MAIN =====
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Команди
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reserve", reserve))
    application.add_handler(CommandHandler("free", free))
    application.add_handler(CommandHandler("setcar", setcar))
    application.add_handler(CommandHandler("myres", myres))
    application.add_handler(CommandHandler("spots", spots))
    
    # Копчиња
    application.add_handler(CallbackQueryHandler(obraboti_klikovi))
    
    # Стартувај
    logger.info("🚀 Ботот стартува...")
    application.run_polling()

if __name__ == '__main__':
    main()
