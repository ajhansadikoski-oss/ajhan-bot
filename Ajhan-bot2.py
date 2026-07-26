import os
import sys
import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== LOGGING =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== НАСТРОЙКИ =====
TOKEN = "8674559116:AAFuzWJJLVY-qMAHBSr7Z6om686b1zeGxKc"
ADMIN_IDS = [8694942406]

# ===== БАЗА ДАННИ =====
def init_db():
    try:
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
        for i in range(1, 21):
            c.execute('INSERT OR IGNORE INTO parking_spots (spot_number) VALUES (?)', (i,))
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"Database init error: {e}")
        return False

def get_user(user_id):
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        return user
    except Exception as e:
        logger.error(f"get_user error: {e}")
        return None

def register_user(user_id, username, full_name):
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)',
                  (user_id, username, full_name))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"register_user error: {e}")

def update_user_car(user_id, car_number):
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('UPDATE users SET car_number = ? WHERE user_id = ?', (car_number, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"update_user_car error: {e}")

def get_active_reservations(user_id):
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('SELECT * FROM reservations WHERE user_id = ? AND status = "active"', (user_id,))
        res = c.fetchall()
        conn.close()
        return res
    except Exception as e:
        logger.error(f"get_active_reservations error: {e}")
        return []

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
        c.execute('INSERT INTO reservations (user_id, spot_number, car_number, start_time, end_time) VALUES (?, ?, ?, ?, ?)',
                  (user_id, spot_number, car_number, start_time, end_time))
        c.execute('UPDATE parking_spots SET is_occupied = 1 WHERE spot_number = ?', (spot_number,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"occupy_spot error: {e}")

def free_spot(reservation_id):
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('SELECT spot_number FROM reservations WHERE id = ?', (reservation_id,))
        spot = c.fetchone()
        if spot:
            c.execute('UPDATE parking_spots SET is_occupied = 0 WHERE spot_number = ?', (spot[0],))
            c.execute('UPDATE reservations SET status = "completed" WHERE id = ?', (reservation_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"free_spot error: {e}")

def get_all_reservations():
    try:
        conn = sqlite3.connect('parking.db')
        c = conn.cursor()
        c.execute('''SELECT r.id, u.username, u.car_number, r.spot_number, r.start_time, r.end_time 
                     FROM reservations r 
                     JOIN users u ON r.user_id = u.user_id 
                     WHERE r.status = "active"''')
        data = c.fetchall()
        conn.close()
        return data
    except Exception as e:
        logger.error(f"get_all_reservations error: {e}")
        return []

# ===== КОМАНДИ ЗА БОТА =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
            f"🚗 Здраво, {user.full_name}!\n\n"
            "Добредојде во системот за паркинг.\n"
            "Избери опција од менито:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"start error: {e}")
        await update.message.reply_text("❌ Грешка, обидете се повторно!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        if query.data == 'free_spots':
            free = get_free_spots()
            if free:
                text = f"🟢 Слободни места: {', '.join(map(str, free))}\n\n"
                text += "Избери место со:\n/reserve [број] [часови]\n"
                text += "Пример: /reserve 5 2 (за 2 часа)"
            else:
                text = "🔴 Нема слободни места!"
            await query.edit_message_text(text)
        
        elif query.data == 'register_car':
            await query.edit_message_text(
                "📝 Внеси го бројот на колата.\n"
                "Пример: CA1234AB\n\n"
                "Користи: /setcar [број]"
            )
        
        elif query.data == 'my_reservations':
            res = get_active_reservations(user_id)
            if res:
                text = "📋 Твоите резервации:\n\n"
                for r in res:
                    text += f"📍 Место {r[2]} | Кола: {r[3]}\n"
                    text += f"⏰ До: {r[5][:16]}\n"
                    text += f"🆔 ID: {r[0]} (за ослободување: /free {r[0]})\n\n"
            else:
                text = "Немаш резервации."
            await query.edit_message_text(text)
        
        elif query.data == 'help':
            await query.edit_message_text(
                "📖 Помош:\n\n"
                "/start - Старт\n"
                "/reserve [место] [часови] - Резервирај\n"
                "/free [ID] - Ослободи\n"
                "/setcar [број] - Внеси кола\n"
                "/myres - Мои резервации\n"
                "/spots - Слободни места\n\n"
                "Админ команди:\n"
                "/admin - Админ панел\n"
                "/allres - Сите резервации"
            )
        
        elif query.data == 'admin_panel':
            if user_id not in ADMIN_IDS:
                await query.edit_message_text("⛔ Немаш права!")
                return
            keyboard = [
                [InlineKeyboardButton("📊 Сите резервации", callback_data='all_reservations')],
                [InlineKeyboardButton("👥 Сите корисници", callback_data='all_users')],
                [InlineKeyboardButton("🗑️ Изчисти стари", callback_data='cleanup')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("⚙️ Админ панел:", reply_markup=reply_markup)
        
        elif query.data == 'all_reservations':
            if user_id not in ADMIN_IDS:
                await query.edit_message_text("⛔ Немаш права!")
                return
            data = get_all_reservations()
            if data:
                text = "📊 Сите активни резервации:\n\n"
                for r in data:
                    text += f"🆔 {r[0]} | 👤 {r[1]} | 🚗 {r[2]}\n"
                    text += f"📍 Место {r[3]} | ⏰ {r[4][:16]} - {r[5][:16]}\n\n"
            else:
                text = "Нема активни резервации."
            await query.edit_message_text(text)
        
        elif query.data == 'all_users':
            if user_id not in ADMIN_IDS:
                await query.edit_message_text("⛔ Немаш права!")
                return
            conn = sqlite3.connect('parking.db')
            c = conn.cursor()
            c.execute('SELECT user_id, username, full_name, phone, car_number FROM users')
            users = c.fetchall()
            conn.close()
            text = "👥 Корисници:\n\n"
            for u in users:
                text += f"🆔 {u[0]} | @{u[1] or 'нема'} | {u[2]}\n"
                text += f"📞 {u[3] or 'не'} | 🚗 {u[4] or 'не'}\n\n"
            await query.edit_message_text(text)
        
        elif query.data == 'cleanup':
            if user_id not in ADMIN_IDS:
                await query.edit_message_text("⛔ Немаш права!")
                return
            conn = sqlite3.connect('parking.db')
            c = conn.cursor()
            c.execute('UPDATE reservations SET status = "expired" WHERE end_time < datetime("now") AND status = "active"')
            c.execute('UPDATE parking_spots SET is_occupied = 0 WHERE spot_number IN (SELECT spot_number FROM reservations WHERE status = "expired")')
            conn.commit()
            conn.close()
            await query.edit_message_text("✅ Изчистени стари резервации!")
    except Exception as e:
        logger.error(f"button_handler error: {e}")

async def reserve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        user = get_user(user_id)
        if not user or not user[4]:
            await update.message.reply_text("⚠️ Прво внеси кола!\nКористи: /setcar [број]")
            return
        
        try:
            spot = int(context.args[0])
            hours = float(context.args[1]) if len(context.args) > 1 else 1
        except:
            await update.message.reply_text("❌ Грешен формат!\nКористи: /reserve [број_на_место] [часови]")
            return
        
        free = get_free_spots()
        if spot not in free:
            await update.message.reply_text(f"❌ Место {spot} не е слободно!")
            return
        
        if hours > 24:
            await update.message.reply_text("❌ Максимум 24 часа!")
            return
        
        car_number = user[4]
        occupy_spot(spot, user_id, car_number, hours)
        await update.message.reply_text(f"✅ Резервирано место {spot} за {hours} часа!\nКола: {car_number}")
    except Exception as e:
        logger.error(f"reserve error: {e}")
        await update.message.reply_text("❌ Грешка, обидете се повторно!")

async def free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        try:
            res_id = int(context.args[0])
        except:
            await update.message.reply_text("❌ Користи: /free [ID_на_резервација]")
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
            await update.message.reply_text("⛔ Ова не е твоја резервација!")
            return
        
        free_spot(res_id)
        await update.message.reply_text(f"✅ Ослободена резервација {res_id}!")
    except Exception as e:
        logger.error(f"free error: {e}")
        await update.message.reply_text("❌ Грешка, обидете се повторно!")

async def setcar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("❌ Користи: /setcar [број на кола]")
            return
        car = context.args[0].upper()
        update_user_car(update.effective_user.id, car)
        await update.message.reply_text(f"✅ Кола {car} е регистрирана!")
    except Exception as e:
        logger.error(f"setcar error: {e}")
        await update.message.reply_text("❌ Грешка, обидете се повторно!")

async def myres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = get_active_reservations(update.effective_user.id)
        if res:
            text = "📋 Твоите резервации:\n\n"
            for r in res:
                text += f"🆔 {r[0]} | Место {r[2]} | {r[3]}\n"
                text += f"⏰ До: {r[5][:16]}\n\n"
        else:
            text = "Немаш резервации."
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"myres error: {e}")
        await update.message.reply_text("❌ Грешка, обидете се повторно!")

async def spots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        free = get_free_spots()
        if free:
            await update.message.reply_text(f"🟢 Слободни: {', '.join(map(str, free))}")
        else:
            await update.message.reply_text("🔴 Нема слободни места!")
    except Exception as e:
        logger.error(f"spots error: {e}")
        await update.message.reply_text("❌ Грешка, обидете се повторно!")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("⛔ Немаш права!")
            return
        keyboard = [
            [InlineKeyboardButton("📊 Сите резервации", callback_data='all_reservations')],
            [InlineKeyboardButton("👥 Сите корисници", callback_data='all_users')],
            [InlineKeyboardButton("🗑️ Изчисти стари", callback_data='cleanup')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚙️ Админ панел:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"admin error: {e}")

async def allres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("⛔ Немаш права!")
            return
        data = get_all_reservations()
        if data:
            text = "📊 Сите резервации:\n\n"
            for r in data:
                text += f"🆔 {r[0]} | {r[1]} | {r[2]} | Место {r[3]}\n"
                text += f"⏰ {r[4][:16]} - {r[5][:16]}\n\n"
        else:
            text = "Нема активни резервации."
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"allres error: {e}")

# ===== СТАРТИРАНЕ =====
def main():
    try:
        # Иницијализација на база
        if not init_db():
            logger.error("Failed to initialize database!")
            sys.exit(1)
        
        # Креирај апликација
        app = Application.builder().token(TOKEN).build()
        
        # Додај команди
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("reserve", reserve))
        app.add_handler(CommandHandler("free", free))
        app.add_handler(CommandHandler("setcar", setcar))
        app.add_handler(CommandHandler("myres", myres))
        app.add_handler(CommandHandler("spots", spots))
        app.add_handler(CommandHandler("admin", admin))
        app.add_handler(CommandHandler("allres", allres))
        
        # Додај обработка на копчиња
        app.add_handler(CallbackQueryHandler(button_handler))
        
        # Стартувај
        logger.info("🚀 Ботот стартува...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Main error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
