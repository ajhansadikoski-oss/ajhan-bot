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

# Константи
ADMIN_MENU, CEKA_BRISI_ID, CEKA_CUSTOM_DAYS = range(3)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8674559116:AAFuZWJJLVY-qMAHBSr7Z6om686b1zeGxKc")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8694942406"))

# Иницијализација на базата
def inicijaliziraj_baza():
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

inicijaliziraj_baza()

# ========== GG СКРИПТИ ==========
def generiraj_gg_skripta(funkcija, user_id):
    """Генерира вистински Lua скрипти за Game Guardian"""
    
    if funkcija == "W16":
        return f"""
-- W16 MOTOR UNLOCK
-- Корисник: {user_id}
-- Car Parking Multiplayer

function W16()
    gg.setRanges(gg.REGION_C_ALLOC)
    gg.searchNumber('2000', gg.TYPE_DWORD)
    gg.getResults(100)
    gg.editAll('5000', gg.TYPE_DWORD)
    
    gg.searchNumber('1000', gg.TYPE_DWORD)
    gg.getResults(50)
    gg.editAll('5000', gg.TYPE_DWORD)
    
    gg.alert('✅ W16 Motor отклучен!')
end

W16()
"""
    
    elif funkcija == "PARI":
        return f"""
-- $$$ MONEY HACK $$$
-- Корисник: {user_id}
-- Car Parking Multiplayer

function MONEY()
    gg.setRanges(gg.REGION_C_ALLOC)
    
    -- Барај ја моменталната вредност на парите
    gg.searchNumber('1000', gg.TYPE_DWORD)
    gg.getResults(100)
    gg.editAll('999999999', gg.TYPE_DWORD)
    
    gg.searchNumber('5000', gg.TYPE_DWORD)
    gg.getResults(50)
    gg.editAll('999999999', gg.TYPE_DWORD)
    
    gg.alert('💰 Додадени $999,999,999!')
end

MONEY()
"""
    
    elif funkcija == "Horns":
        return f"""
-- 🎺 ALL HORNS UNLOCK
-- Корисник: {user_id}

function HORNS()
    gg.setRanges(gg.REGION_C_ALLOC)
    gg.searchNumber('0', gg.TYPE_DWORD)
    gg.getResults(1000)
    gg.editAll('1', gg.TYPE_DWORD)
    
    gg.alert('✅ Сите хорни отклучени!')
end

HORNS()
"""
    
    elif funkcija == "NoDmg":
        return f"""
-- 🛡️ NO DAMAGE
-- Корисник: {user_id}

function NODMG()
    gg.setRanges(gg.REGION_C_ALLOC)
    gg.searchNumber('100', gg.TYPE_FLOAT)
    gg.getResults(50)
    gg.editAll('999999', gg.TYPE_FLOAT)
    
    gg.alert('🛡️ Штетата е исклучена!')
end

NODMG()
"""
    
    elif funkcija == "Fuel":
        return f"""
-- ⛽ INFINITE FUEL
-- Корисник: {user_id}

function FUEL()
    gg.setRanges(gg.REGION_C_ALLOC)
    gg.searchNumber('100', gg.TYPE_FLOAT)
    gg.getResults(50)
    gg.editAll('999999', gg.TYPE_FLOAT)
    
    gg.alert('⛽ Бесконечно гориво!')
end

FUEL()
"""
    
    elif funkcija == "Smoke":
        return f"""
-- 💨 SMOKE EFFECTS
-- Корисник: {user_id}

function SMOKE()
    gg.setRanges(gg.REGION_C_ALLOC)
    gg.searchNumber('0', gg.TYPE_DWORD)
    gg.getResults(100)
    gg.editAll('1', gg.TYPE_DWORD)
    
    gg.alert('💨 Ефекти на чад отклучени!')
end

SMOKE()
"""
    
    elif funkcija == "Animations":
        return f"""
-- 🎭 ALL ANIMATIONS
-- Корисник: {user_id}

function ANIMATIONS()
    gg.setRanges(gg.REGION_C_ALLOC)
    gg.searchNumber('0', gg.TYPE_DWORD)
    gg.getResults(500)
    gg.editAll('1', gg.TYPE_DWORD)
    
    gg.alert('🎭 Сите анимации отклучени!')
end

ANIMATIONS()
"""
    
    elif funkcija == "Wheels":
        return f"""
-- ⚙️ ALL WHEELS
-- Корисник: {user_id}

function WHEELS()
    gg.setRanges(gg.REGION_C_ALLOC)
    gg.searchNumber('0', gg.TYPE_DWORD)
    gg.getResults(200)
    gg.editAll('1', gg.TYPE_DWORD)
    
    gg.alert('⚙️ Сите тркала отклучени!')
end

WHEELS()
"""
    
    elif funkcija == "Houses":
        return f"""
-- 🏠 ALL HOUSES
-- Корисник: {user_id}

function HOUSES()
    gg.setRanges(gg.REGION_C_ALLOC)
    gg.searchNumber('0', gg.TYPE_DWORD)
    gg.getResults(100)
    gg.editAll('1', gg.TYPE_DWORD)
    
    gg.alert('🏠 Сите куќи отклучени!')
end

HOUSES()
"""
    
    elif funkcija == "Levels":
        return f"""
-- 📈 MAX LEVEL
-- Корисник: {user_id}

function LEVELS()
    gg.setRanges(gg.REGION_C_ALLOC)
    gg.searchNumber('1', gg.TYPE_DWORD)
    gg.getResults(100)
    gg.editAll('999', gg.TYPE_DWORD)
    
    gg.alert('📈 Макс ниво 999!')
end

LEVELS()
"""
    
    elif funkcija == "Rank":
        return f"""
-- 👑 MAX RANK
-- Корисник: {user_id}

function RANK()
    gg.setRanges(gg.REGION_C_ALLOC)
    gg.searchNumber('1', gg.TYPE_DWORD)
    gg.getResults(50)
    gg.editAll('999999', gg.TYPE_DWORD)
    
    gg.alert('👑 Макс ранг!')
end

RANK()
"""
    
    elif funkcija == "UnlockAll":
        return f"""
-- 🌟 UNLOCK ALL ★
-- Корисник: {user_id}
-- Car Parking Multiplayer - СЕ ОТКЛУЧУВА

function UNLOCK_ALL()
    gg.setRanges(gg.REGION_C_ALLOC)
    
    -- Пари
    gg.searchNumber('1000', gg.TYPE_DWORD)
    gg.getResults(100)
    gg.editAll('999999999', gg.TYPE_DWORD)
    
    gg.searchNumber('5000', gg.TYPE_DWORD)
    gg.getResults(50)
    gg.editAll('999999999', gg.TYPE_DWORD)
    
    -- W16 Motor
    gg.searchNumber('2000', gg.TYPE_DWORD)
    gg.getResults(100)
    gg.editAll('5000', gg.TYPE_DWORD)
    
    -- Хорни
    gg.searchNumber('0', gg.TYPE_DWORD)
    gg.getResults(1000)
    gg.editAll('1', gg.TYPE_DWORD)
    
    -- Штета
    gg.searchNumber('100', gg.TYPE_FLOAT)
    gg.getResults(50)
    gg.editAll('999999', gg.TYPE_FLOAT)
    
    -- Гориво
    gg.searchNumber('100', gg.TYPE_FLOAT)
    gg.getResults(50)
    gg.editAll('999999', gg.TYPE_FLOAT)
    
    -- Чад
    gg.searchNumber('0', gg.TYPE_DWORD)
    gg.getResults(100)
    gg.editAll('1', gg.TYPE_DWORD)
    
    -- Анимации
    gg.searchNumber('0', gg.TYPE_DWORD)
    gg.getResults(500)
    gg.editAll('1', gg.TYPE_DWORD)
    
    -- Тркала
    gg.searchNumber('0', gg.TYPE_DWORD)
    gg.getResults(200)
    gg.editAll('1', gg.TYPE_DWORD)
    
    -- Куќи
    gg.searchNumber('0', gg.TYPE_DWORD)
    gg.getResults(100)
    gg.editAll('1', gg.TYPE_DWORD)
    
    -- Ниво
    gg.searchNumber('1', gg.TYPE_DWORD)
    gg.getResults(100)
    gg.editAll('999', gg.TYPE_DWORD)
    
    -- Ранг
    gg.searchNumber('1', gg.TYPE_DWORD)
    gg.getResults(50)
    gg.editAll('999999', gg.TYPE_DWORD)
    
    gg.alert('🌟 СЕ Е ОТКЛУЧЕНО! 🎉')
end

UNLOCK_ALL()
"""

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "N/A"
    first_name = update.message.from_user.first_name or "User"

    if user_id == ADMIN_ID:
        await prikazi_admin_panel(update)
        return ADMIN_MENU

    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT istekuvanje, status FROM korisnici WHERE user_id = ?', (user_id,))
    rezultat = cursor.fetchone()
    conn.close()

    sega = datetime.now()
    dozvolen = False

    if rezultat:
        istekuvanje_str = rezultat[0]
        status = rezultat[1]
        
        if status == 'denied':
            await update.message.reply_text(
                "❌ **Вашето барање е одбиено!**\n\n"
                "Контактирајте го администраторот.",
                parse_mode='Markdown'
            )
            return
        
        if istekuvanje_str == "forever":
            dozvolen = True
        elif istekuvanje_str:
            istekuvanje_datum = datetime.strptime(istekuvanje_str, "%Y-%m-%d %H:%M:%S")
            dozvolen = sega < istekuvanje_datum

    if not dozvolen:
        if rezultat and rezultat[1] == 'pending':
            await update.message.reply_text(
                "⏳ **Веќе имате испратено барање!**\n\n"
                "Почекајте администраторот да го одобри.",
                parse_mode='Markdown'
            )
            return
        
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO korisnici (user_id, username, first_name, status) 
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, username, first_name))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ **Барањето е испратено!**\n\n"
            f"👤 Корисник: @{username}\n"
            f"🆔 ID: {user_id}\n\n"
            f"📌 Почекајте администраторот да ве одобри.",
            parse_mode='Markdown'
        )
        
        tastatura = [
            [
                InlineKeyboardButton("♾️ Forever", callback_data=f"lic_forever_{user_id}"),
                InlineKeyboardButton("📅 30 Days", callback_data=f"lic_30_{user_id}")
            ],
            [
                InlineKeyboardButton("📅 7 Days", callback_data=f"lic_7_{user_id}"),
                InlineKeyboardButton("📝 Custom", callback_data=f"lic_custom_{user_id}")
            ],
            [
                InlineKeyboardButton("❌ Deny", callback_data=f"lic_deny_{user_id}")
            ]
        ]
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **НОВО БАРАЊЕ ЗА ПРИСТАП!**\n\n"
                 f"👤 **Корисник:** {first_name}\n"
                 f"🆔 **ID:** `{user_id}`\n"
                 f"👤 **Username:** @{username}\n"
                 f"📅 **Датум:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                 f"Изберете тип на лиценца:",
            reply_markup=InlineKeyboardMarkup(tastatura),
            parse_mode='Markdown'
        )
        return

    # ✅ ПРИКАЖИ GG МЕНИ
    await prikazi_gg_menu(update, context)

# ========== GG МЕНИ ==========
async def prikazi_gg_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user_id = query.from_user.id if query else update.message.from_user.id
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, istekuvanje FROM korisnici WHERE user_id = ?', (user_id,))
    rezultat = cursor.fetchone()
    conn.close()
    
    username = rezultat[0] if rezultat else "N/A"
    istek = rezultat[1] if rezultat else "N/A"
    
    if istek != "forever" and istek != "N/A":
        try:
            istek_datum = datetime.strptime(istek, "%Y-%m-%d %H:%M:%S")
            preostanato = istek_datum - datetime.now()
            istek = f"{preostanato.days} дена"
        except:
            pass
    
    menu_text = f"""<b>🎮 GAME GUARDIAN - CAR PARKING</b>

👤 <b>Корисник:</b> @{username}
🆔 <b>ID:</b> {user_id}
📅 <b>Лиценца:</b> {istek}

<b>⚡ ИЗБЕРИ ФУНКЦИЈА:</b>"""

    keyboard = [
        [
            InlineKeyboardButton("🔊 W16", callback_data="gg_w16"),
            InlineKeyboardButton("📯 Horns", callback_data="gg_horns")
        ],
        [
            InlineKeyboardButton("🛡️ No Dmg", callback_data="gg_nodmg"),
            InlineKeyboardButton("⛽ Fuel", callback_data="gg_fuel")
        ],
        [
            InlineKeyboardButton("💨 Smoke", callback_data="gg_smoke"),
            InlineKeyboardButton("🎭 Animations", callback_data="gg_animations")
        ],
        [
            InlineKeyboardButton("⚙️ Wheels", callback_data="gg_wheels"),
            InlineKeyboardButton("🏠 Houses", callback_data="gg_houses")
        ],
        [
            InlineKeyboardButton("📈 Levels", callback_data="gg_levels"),
            InlineKeyboardButton("👑 Rank", callback_data="gg_rank")
        ],
        [
            InlineKeyboardButton("🌟 UNLOCK ALL ★", callback_data="gg_unlock_all")
        ],
        [
            InlineKeyboardButton("💵 ДОБИЈ ПАРИ", callback_data="gg_money")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="gg_back")
        ]
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

# ========== GG HANDLERS ==========
async def gg_funkcija(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    funkcija = query.data.replace('gg_', '')
    
    # Мапа на функции
    funkcii = {
        'w16': 'W16 Motor',
        'horns': 'Хорни',
        'nodmg': 'Без Штета',
        'fuel': 'Бесконечно Гориво',
        'smoke': 'Чад',
        'animations': 'Анимации',
        'wheels': 'Тркала',
        'houses': 'Куќи',
        'levels': 'Нивоа',
        'rank': 'Ранг',
        'unlock_all': 'СЕ ОТКЛУЧУВА',
        'money': 'ПАРИ'
    }
    
    ime = funkcii.get(funkcija, funkcija)
    
    # Генерирај GG скрипта
    if funkcija == 'unlock_all':
        skripta = generiraj_gg_skripta('UnlockAll', user_id)
    elif funkcija == 'money':
        skripta = generiraj_gg_skripta('PARI', user_id)
    else:
        skripta = generiraj_gg_skripta(funkcija.capitalize(), user_id)
    
    # Порака со скриптата
    await query.edit_message_text(
        f"""<b>🎮 {ime} - GG СКРИПТА</b>

📝 <b>Копирај ја скриптата:</b>

<code>{skripta}</code>

📌 <b>Инструкции:</b>
1. Отвори Game Guardian
2. Избери Car Parking Multiplayer
3. Кликни на иконата за скрипти (📜)
4. Paste - Вметни ја скриптата
5. Run - Изврши

⚠️ <b>ВАЖНО:</b> Скриптата работи само ако имаш активна лиценца!""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Копирај", callback_data=f"copy_{funkcija}")],
            [InlineKeyboardButton("🔙 Назад во Мени", callback_data="gg_menu")]
        ]),
        parse_mode='HTML'
    )

# ========== АДМИН ПАНЕЛ ==========
async def prikazi_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM korisnici')
    vkupno = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status = "approved"')
    aktivni = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status = "pending"')
    baranja = cursor.fetchone()[0]
    
    conn.close()
    
    admin_text = f"""<b>👑 GG ADMIN PANEL</b>

📊 <b>Статистика:</b>
• Вкупно: {vkupno}
• Активни: {aktivni}
• Барања: {baranja}

📌 <b>Избери опција:</b>"""

    keyboard = [
        [InlineKeyboardButton("📋 Корисници", callback_data="admin_users")],
        [InlineKeyboardButton("❌ Бриши Корисник", callback_data="admin_remove")],
        [InlineKeyboardButton("💵 Барања за Пари", callback_data="admin_money_requests")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
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

# ========== LICENCA HANDLER ==========
async def licenca_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    akcija = data[1]
    user_id = int(data[2])
    
    if akcija == "custom":
        context.user_data['custom_user_id'] = user_id
        await query.edit_message_text(
            f"📝 **Внесете број на денови (1-30)**\n\n"
            f"Корисник ID: `{user_id}`",
            parse_mode='Markdown'
        )
        return CEKA_CUSTOM_DAYS
    
    if akcija == "deny":
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE korisnici SET status = "denied" WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(f"❌ Корисникот {user_id} е одбиен.")
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Вашето барање за пристап е одбиено.",
            parse_mode='Markdown'
        )
        return
    
    if akcija == "forever":
        istekuvanje = "forever"
        opis = "Forever ♾️"
    else:
        istekuvanje = (datetime.now() + timedelta(days=int(akcija))).strftime("%Y-%m-%d %H:%M:%S")
        opis = f"{akcija} дена"
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE korisnici 
        SET istekuvanje = ?, status = "approved", datum_dodeluvanje = ? 
        WHERE user_id = ?
    ''', (istekuvanje, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
    conn.commit()
    conn.close()
    
    await query.edit_message_text(f"✅ Корисникот {user_id} е одобрен! ({opis})")
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ **ДОБИВТЕ ПРИСТАП!** 🎉\n\n"
             f"📅 Времетраење: {opis}\n"
             f"📆 Доделено: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
             f"🔑 Напишете /start за да почнете.",
        parse_mode='Markdown'
    )

async def primi_custom_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text.strip())
        if days < 1 or days > 30:
            await update.message.reply_text("❌ Внесете број од 1 до 30.")
            return CEKA_CUSTOM_DAYS
        
        user_id = context.user_data.get('custom_user_id')
        if not user_id:
            await update.message.reply_text("❌ Грешка!")
            return
        
        istekuvanje = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE korisnici 
            SET istekuvanje = ?, status = "approved", datum_dodeluvanje = ? 
            WHERE user_id = ?
        ''', (istekuvanje, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(f"✅ Custom лиценца доделена! ({days} дена)")
        
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ **ДОБИВТЕ ПРИСТАП!** 🎉\n\n"
                 f"📅 Времетраење: {days} дена\n"
                 f"📆 Истекува: {(datetime.now() + timedelta(days=days)).strftime('%d.%m.%Y %H:%M')}\n\n"
                 f"🔑 Напишете /start за да почнете.",
            parse_mode='Markdown'
        )
        
        del context.user_data['custom_user_id']
        await prikazi_admin_panel(update)
        
    except ValueError:
        await update.message.reply_text("❌ Внесете валиден број!")
        return CEKA_CUSTOM_DAYS

# ========== MAIN ==========
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Конверзација
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ADMIN_MENU: [
                CallbackQueryHandler(prikazi_admin_panel, pattern='^admin_back$'),
                CallbackQueryHandler(admin_users, pattern='^admin_users$'),
                CallbackQueryHandler(admin_remove, pattern='^admin_remove$'),
                CallbackQueryHandler(admin_stats, pattern='^admin_stats$'),
                CallbackQueryHandler(admin_money, pattern='^admin_money_requests$'),
            ],
            CEKA_BRISI_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, primi_id_za_brisenje)
            ],
            CEKA_CUSTOM_DAYS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, primi_custom_days)
            ]
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)
    
    # GG handlers
    application.add_handler(CallbackQueryHandler(prikazi_gg_menu, pattern='^gg_menu$'))
    application.add_handler(CallbackQueryHandler(prikazi_gg_menu, pattern='^gg_back$'))
    application.add_handler(CallbackQueryHandler(gg_funkcija, pattern='^gg_'))
    
    # Админ handlers
    application.add_handler(CallbackQueryHandler(prikazi_admin_panel, pattern='^admin_back$'))
    application.add_handler(CallbackQueryHandler(admin_users, pattern='^admin_users$'))
    application.add_handler(CallbackQueryHandler(admin_remove, pattern='^admin_remove$'))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    application.add_handler(CallbackQueryHandler(admin_money, pattern='^admin_money_requests$'))
    
    # Лиценца handler
    application.add_handler(CallbackQueryHandler(licenca_handler, pattern='^lic_'))
    
    # Команди
    application.add_handler(CommandHandler('start', start))

    print("🤖 GG Ботот е стартуван!")
    print(f"👑 Админ ID: {ADMIN_ID}")
    application.run_polling()

if __name__ == '__main__':
    main()
