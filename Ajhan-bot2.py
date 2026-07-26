import os
import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== НАСТРОЙКИ =====
TOKEN = "8674559116:AAFuzWJJLVY-qMAHBSr7Z6om686b1zeGxKc"  # Твоят токен от BotFather
ADMIN_IDS = [8694942406]  # Твоето ID от User Info бота

# ===== БАЗА ДАННИ =====
def init_db():
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        phone TEXT,
        car_number TEXT,
        is_admin INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservations (
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
    # Създаваме 20 паркоместа
    for i in range(1, 21):
        c.execute('INSERT OR IGNORE INTO parking_spots (spot_number) VALUES (?)', (i,))
    conn.commit()
    conn.close()

# ===== ПОМОЩНИ ФУНКЦИИ =====
def get_user(user_id):
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def register_user(user_id, username, full_name):
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)',
              (user_id, username, full_name))
    conn.commit()
    conn.close()

def update_user_phone(user_id, phone):
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('UPDATE users SET phone = ? WHERE user_id = ?', (phone, user_id))
    conn.commit()
    conn.close()

def update_user_car(user_id, car_number):
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('UPDATE users SET car_number = ? WHERE user_id = ?', (car_number, user_id))
    conn.commit()
    conn.close()

def get_active_reservations(user_id):
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('SELECT * FROM reservations WHERE user_id = ? AND status = "active"', (user_id,))
    res = c.fetchall()
    conn.close()
    return res

def get_free_spots():
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('SELECT spot_number FROM parking_spots WHERE is_occupied = 0')
    spots = [row[0] for row in c.fetchall()]
    conn.close()
    return spots

def occupy_spot(spot_number, user_id, car_number, hours):
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    start_time = datetime.now().isoformat()
    end_time = (datetime.now() + timedelta(hours=hours)).isoformat()
    c.execute('INSERT INTO reservations (user_id, spot_number, car_number, start_time, end_time) VALUES (?, ?, ?, ?, ?)',
              (user_id, spot_number, car_number, start_time, end_time))
    c.execute('UPDATE parking_spots SET is_occupied = 1 WHERE spot_number = ?', (spot_number,))
    conn.commit()
    conn.close()

def free_spot(reservation_id):
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('SELECT spot_number FROM reservations WHERE id = ?', (reservation_id,))
    spot = c.fetchone()
    if spot:
        c.execute('UPDATE parking_spots SET is_occupied = 0 WHERE spot_number = ?', (spot[0],))
        c.execute('UPDATE reservations SET status = "completed" WHERE id = ?', (reservation_id,))
    conn.commit()
    conn.close()

def get_all_reservations():
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('''SELECT r.id, u.username, u.car_number, r.spot_number, r.start_time, r.end_time 
                 FROM reservations r 
                 JOIN users u ON r.user_id = u.user_id 
                 WHERE r.status = "active"''')
    data = c.fetchall()
    conn.close()
    return data

# ===== КОМАНДИ ЗА БОТА =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username, user.full_name)
    
    keyboard = [
        [InlineKeyboardButton("🚗 Виж свободни места", callback_data='free_spots')],
        [InlineKeyboardButton("📝 Регистрирай кола", callback_data='register_car')],
        [InlineKeyboardButton("📋 Моите резервации", callback_data='my_reservations')],
        [InlineKeyboardButton("🆘 Помощ", callback_data='help')]
    ]
    
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("⚙️ Админ панел", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🚗 Здравей, {user.full_name}!\n\n"
        "Добре дошли в системата за паркинг.\n"
        "Избери опция от менюто:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == 'free_spots':
        free = get_free_spots()
        if free:
            text = f"🟢 Свободни места: {', '.join(map(str, free))}\n\n"
            text += "Избери място като напишеш:\n/reserve [номер] [часове]\n"
            text += "Пример: /reserve 5 2 (за 2 часа)"
        else:
            text = "🔴 Няма свободни места в момента!"
        await query.edit_message_text(text)
    
    elif query.data == 'register_car':
        await query.edit_message_text(
            "📝 Моля, въведи номера на колата си.\n"
            "Пример: CA1234AB\n\n"
            "Използвай командата:\n/setcar [номер]"
        )
    
    elif query.data == 'my_reservations':
        res = get_active_reservations(user_id)
        if res:
            text = "📋 Твоите активни резервации:\n\n"
            for r in res:
                text += f"📍 Място {r[2]} | Кола: {r[3]}\n"
                text += f"⏰ До: {r[5][:16]}\n"
                text += f"🆔 ID: {r[0]} (за освобождаване: /free {r[0]})\n\n"
        else:
            text = "Нямаш активни резервации."
        await query.edit_message_text(text)
    
    elif query.data == 'help':
        await query.edit_message_text(
            "📖 Помощ:\n\n"
            "/start - Стартирай бота\n"
            "/reserve [място] [часове] - Резервирай място\n"
            "/free [ID] - Освободи резервация\n"
            "/setcar [номер] - Задай номер на кола\n"
            "/myres - Моите резервации\n"
            "/spots - Свободни места\n\n"
            "Админ команди:\n"
            "/admin - Админ панел\n"
            "/allres - Всички активни резервации"
        )
    
    elif query.data == 'admin_panel':
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("⛔ Нямаш права за това!")
            return
        keyboard = [
            [InlineKeyboardButton("📊 Всички резервации", callback_data='all_reservations')],
            [InlineKeyboardButton("👥 Всички потребители", callback_data='all_users')],
            [InlineKeyboardButton("🗑️ Изчисти стари резервации", callback_data='cleanup')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⚙️ Админ панел:", reply_markup=reply_markup)
    
    elif query.data == 'all_reservations':
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("⛔ Нямаш права!")
            return
        data = get_all_reservations()
        if data:
            text = "📊 Всички активни резервации:\n\n"
            for r in data:
                text += f"🆔 {r[0]} | 👤 {r[1]} | 🚗 {r[2]}\n"
                text += f"📍 Място {r[3]} | ⏰ {r[4][:16]} - {r[5][:16]}\n\n"
        else:
            text = "Няма активни резервации."
        await query.edit_message_text(text)
    
    elif query.data == 'all_users':
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("⛔ Нямаш права!")
            return
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('SELECT user_id, username, full_name, phone, car_number FROM users')
        users = c.fetchall()
        conn.close()
        text = "👥 Потребители:\n\n"
        for u in users:
            text += f"🆔 {u[0]} | @{u[1] or 'няма'} | {u[2]}\n"
            text += f"📞 {u[3] or 'не' } | 🚗 {u[4] or 'не'}\n\n"
        await query.edit_message_text(text)
    
    elif query.data == 'cleanup':
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("⛔ Нямаш права!")
            return
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('UPDATE reservations SET status = "expired" WHERE end_time < datetime("now") AND status = "active"')
        c.execute('UPDATE parking_spots SET is_occupied = 0 WHERE spot_number IN (SELECT spot_number FROM reservations WHERE status = "expired")')
        conn.commit()
        conn.close()
        await query.edit_message_text("✅ Изчистени стари резервации!")

async def reserve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or not user[4]:  # няма регистрирана кола
        await update.message.reply_text("⚠️ Първо регистрирай кола!\nИзползвай: /setcar [номер]")
        return
    
    try:
        spot = int(context.args[0])
        hours = float(context.args[1]) if len(context.args) > 1 else 1
    except:
        await update.message.reply_text("❌ Грешен формат!\nИзползвай: /reserve [номер_на_място] [часове]\nПример: /reserve 5 2")
        return
    
    free = get_free_spots()
    if spot not in free:
        await update.message.reply_text(f"❌ Място {spot} не е свободно!")
        return
    
    if hours > 24:
        await update.message.reply_text("❌ Максимум 24 часа!")
        return
    
    car_number = user[4]
    occupy_spot(spot, user_id, car_number, hours)
    await update.message.reply_text(f"✅ Резервира място {spot} за {hours} часа!\nКола: {car_number}")

async def free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ Използвай: /free [ID_на_резервация]")
        return
    
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM reservations WHERE id = ? AND status = "active"', (res_id,))
    res = c.fetchone()
    conn.close()
    
    if not res:
        await update.message.reply_text("❌ Невалиден ID!")
        return
    
    if res[0] != update.effective_user.id and update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Това не е твоя резервация!")
        return
    
    free_spot(res_id)
    await update.message.reply_text(f"✅ Освободена резервация {res_id}!")

async def setcar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Използвай: /setcar [номер на кола]")
        return
    car = context.args[0].upper()
    update_user_car(update.effective_user.id, car)
    await update.message.reply_text(f"✅ Кола {car} е регистрирана!")

async def myres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = get_active_reservations(update.effective_user.id)
    if res:
        text = "📋 Твоите резервации:\n\n"
        for r in res:
            text += f"🆔 {r[0]} | Място {r[2]} | {r[3]}\n"
            text += f"⏰ До: {r[5][:16]}\n\n"
    else:
        text = "Нямаш резервации."
    await update.message.reply_text(text)

async def spots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    free = get_free_spots()
    if free:
        await update.message.reply_text(f"🟢 Свободни: {', '.join(map(str, free))}")
    else:
        await update.message.reply_text("🔴 Няма свободни места!")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Нямаш права!")
        return
    keyboard = [
        [InlineKeyboardButton("📊 Всички резервации", callback_data='all_reservations')],
        [InlineKeyboardButton("👥 Всички потребители", callback_data='all_users')],
        [InlineKeyboardButton("🗑️ Изчисти стари", callback_data='cleanup')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ Админ панел:", reply_markup=reply_markup)

async def allres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Нямаш права!")
        return
    data = get_all_reservations()
    if data:
        text = "📊 Всички резервации:\n\n"
        for r in data:
            text += f"🆔 {r[0]} | {r[1]} | {r[2]} | Място {r[3]}\n"
            text += f"⏰ {r[4][:16]} - {r[5][:16]}\n\n"
    else:
        text = "Няма активни резервации."
    await update.message.reply_text(text)

# ===== СТАРТИРАНЕ =====
def main():
    init_db()
    
    app = Application.builder().token(TOKEN).build()
    
    # Команди
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reserve", reserve))
    app.add_handler(CommandHandler("free", free))
    app.add_handler(CommandHandler("setcar", setcar))
    app.add_handler(CommandHandler("myres", myres))
    app.add_handler(CommandHandler("spots", spots))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("allres", allres))
    
    # Бутони
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 Ботът стартира...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
