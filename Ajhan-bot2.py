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

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "N/A"
    first_name = update.message.from_user.first_name or "User"

    # АКО Е АДМИН - ОДМАА ВО АДМИН ПАНЕЛ
    if user_id == ADMIN_ID:
        await prikazi_admin_panel(update)
        return ADMIN_MENU

    # ПРОВЕРКА ДАЛИ КОРИСНИКОТ ИМА ЛИЦЕНЦА
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

    # АКО НЕМА ЛИЦЕНЦА - БАРА ПРИСТАП
    if not dozvolen:
        # Провери дали веќе има pending барање
        if rezultat and rezultat[1] == 'pending':
            await update.message.reply_text(
                "⏳ **Веќе имате испратено барање!**\n\n"
                "Почекајте администраторот да го одобри.",
                parse_mode='Markdown'
            )
            return
        
        # Зачувај го барањето во база
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO korisnici (user_id, username, first_name, status) 
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, username, first_name))
        conn.commit()
        conn.close()
        
        # Порака до корисникот
        await update.message.reply_text(
            f"✅ **Барањето е испратено!**\n\n"
            f"👤 Корисник: @{username}\n"
            f"🆔 ID: {user_id}\n\n"
            f"📌 Почекајте администраторот да ве одобри.",
            parse_mode='Markdown'
        )
        
        # Порака до админот
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

    # АКО ИМА ЛИЦЕНЦА - КОРИСНИЧКО МЕНИ
    await prikazi_user_menu(update, context)

# ========== КОРИСНИЧКО МЕНИ ==========
async def prikazi_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    
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
    
    menu_text = f"""<b>💰 CPMAJHANBOT v5.0</b>

👤 **Корисник:** @{username}
🆔 **ID:** {user_id}
📅 **Истекува:** {istek}

📌 **Изберете опција:**"""

    keyboard = [
        [InlineKeyboardButton("💵 БАРАЈ ПАРИ", callback_data="baraj_pari")],
        [InlineKeyboardButton("🔓 ОТКЛУЧИ СЕ", callback_data="unlock_all")],
        [InlineKeyboardButton("🚪 ИЗЛЕЗ", callback_data="signout")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            menu_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        await update.callback_query.answer()
    else:
        await update.message.reply_text(
            menu_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

# ========== БАРАЊЕ ПАРИ ==========
async def baraj_pari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username or "N/A"
    
    keyboard = [
        [
            InlineKeyboardButton("$1M", callback_data="pari_1m"),
            InlineKeyboardButton("$5M", callback_data="pari_5m"),
            InlineKeyboardButton("$10M", callback_data="pari_10m")
        ],
        [
            InlineKeyboardButton("$25M", callback_data="pari_25m"),
            InlineKeyboardButton("$50M ★", callback_data="pari_50m"),
            InlineKeyboardButton("$100M", callback_data="pari_100m")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="nazad_glavno")]
    ]
    
    await query.edit_message_text(
        "<b>💵 БАРАЊЕ ПАРИ</b>\n\nИзберете износ:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def primi_baranje_pari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username or "N/A"
    iznos = query.data.split('_')[1]
    iznos_tekst = f"${iznos}"
    
    # Зачувај во база
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO baranja_za_pari (user_id, username, iznos, datum, status)
        VALUES (?, ?, ?, ?, 'pending')
    ''', (user_id, username, iznos_tekst, datetime.now().strftime('%d.%m.%Y %H:%M')))
    conn.commit()
    conn.close()
    
    # Порака до корисникот
    await query.edit_message_text(
        f"✅ **Барањето е испратено!**\n\n"
        f"💰 Износ: {iznos_tekst}\n"
        f"📅 Датум: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"⏳ Почекајте администраторот да го одобри.",
        parse_mode='Markdown'
    )
    await asyncio.sleep(2)
    await prikazi_user_menu(update, context)
    
    # Порака до админот
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💵 **БАРАЊЕ ЗА ПАРИ!**\n\n"
             f"👤 Корисник: @{username}\n"
             f"🆔 ID: `{user_id}`\n"
             f"💰 Износ: {iznos_tekst}\n"
             f"📅 Датум: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
             f"✅ Одобри во админ панелот.",
        parse_mode='Markdown'
    )

# ========== UNLOCK ALL ==========
async def unlock_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    await query.edit_message_text(
        "🔥 **СЕ Е ОТКЛУЧЕНО!**\n\n"
        "✅ Сите функции се активирани!\n"
        "💰 $50,000,000 додадени!\n"
        "🪙 500,000 коинси додадени!\n"
        "🏎️ Сите возила отклучени!\n"
        "🎭 Сите анимации отклучени!",
        parse_mode='Markdown'
    )
    await asyncio.sleep(2)
    await prikazi_user_menu(update, context)

# ========== SIGN OUT ==========
async def signout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "👋 **Излезте успешно!**\n\n"
        "Напишете /start за повторна најава.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# ========== АДМИН ПАНЕЛ ==========
async def prikazi_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Статистика
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    
    # Вкупно корисници
    cursor.execute('SELECT COUNT(*) FROM korisnici')
    vkupno = cursor.fetchone()[0]
    
    # Активни
    cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status = "approved"')
    aktivni = cursor.fetchone()[0]
    
    # Барања за пристап
    cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status = "pending"')
    baranja_pristap = cursor.fetchone()[0]
    
    # Барања за пари
    cursor.execute('SELECT COUNT(*) FROM baranja_za_pari WHERE status = "pending"')
    baranja_pari = cursor.fetchone()[0]
    
    conn.close()
    
    admin_text = f"""<b>👑 CPMAJHANBOT v5.0 - ADMIN PANEL</b>

📊 **Статистика:**
• Вкупно корисници: {vkupno}
• Активни: {aktivni}
• Барања за пристап: {baranja_pristap}
• Барања за пари: {baranja_pari}

📌 **Изберете опција:**"""

    keyboard = [
        [InlineKeyboardButton("📋 Корисничка Листа", callback_data="admin_user_list")],
        [InlineKeyboardButton("❌ Бриши Корисник", callback_data="admin_remove_user")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("💵 Барања за Пари", callback_data="admin_baranja_pari")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
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

# ========== АДМИН - КОРИСНИЧКА ЛИСТА ==========
async def admin_user_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, first_name, status, istekuvanje FROM korisnici ORDER BY user_id')
    korisnici = cursor.fetchall()
    conn.close()
    
    if not korisnici:
        await query.edit_message_text(
            "📋 **Корисничка Листа**\n\nНема регистрирани корисници.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
            ])
        )
        return
    
    tekst = "<b>📋 КОРИСНИЧКА ЛИСТА</b>\n\n"
    for user in korisnici:
        user_id, username, first_name, status, istek = user
        status_emoji = "✅" if status == "approved" else "⏳" if status == "pending" else "❌"
        istek_tekst = istek if istek else "Нема"
        if istek and istek != "forever":
            try:
                istek_datum = datetime.strptime(istek, "%Y-%m-%d %H:%M:%S")
                if istek_datum > datetime.now():
                    preostanato = istek_datum - datetime.now()
                    istek_tekst = f"{preostanato.days} дена"
                else:
                    istek_tekst = "ИСТЕКНА"
            except:
                pass
        tekst += f"🆔 `{user_id}` | @{username} | {first_name}\n"
        tekst += f"   Статус: {status_emoji} {status} | Истекува: {istek_tekst}\n\n"
        if len(tekst) > 3000:
            break
    
    keyboard = [
        [InlineKeyboardButton("🔄 Освежи", callback_data="admin_user_list")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]
    
    await query.edit_message_text(
        tekst,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

# ========== АДМИН - БРИШИ КОРИСНИК ==========
async def admin_remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "❌ **БРИШИ КОРИСНИК**\n\n"
        "Внесете го ID на корисникот што сакате да го избришете:\n\n"
        "Пример: `8793457956`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
        ])
    )
    return CEKA_BRISI_ID

async def primi_id_za_brisenje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
    except:
        await update.message.reply_text(
            "❌ **Грешка!**\n\nВнесете валиден ID (само броеви).",
            parse_mode='Markdown'
        )
        return CEKA_BRISI_ID
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM korisnici WHERE user_id = ?', (user_id,))
    korisnik = cursor.fetchone()
    
    if not korisnik:
        await update.message.reply_text(
            f"❌ **Корисникот со ID {user_id} не постои!**",
            parse_mode='Markdown'
        )
        conn.close()
        return CEKA_BRISI_ID
    
    cursor.execute('DELETE FROM korisnici WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM baranja_za_pari WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"✅ **Корисникот е избришан!**\n\n"
        f"👤 Корисник: @{korisnik[0]}\n"
        f"🆔 ID: {user_id}",
        parse_mode='Markdown'
    )
    
    # Извести го корисникот
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ **Вашиот пристап е отстранет од администраторот.**",
            parse_mode='Markdown'
        )
    except:
        pass
    
    await prikazi_admin_panel(update)
    return ADMIN_MENU

# ========== АДМИН - СТАТИСТИКА ==========
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM korisnici')
    vkupno = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status = "approved"')
    aktivni = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status = "pending"')
    pending = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status = "denied"')
    denied = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM baranja_za_pari WHERE status = "pending"')
    baranja_pari = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM baranja_za_pari WHERE status = "approved"')
    odobreni_pari = cursor.fetchone()[0]
    
    conn.close()
    
    stats_text = f"""<b>📊 СТАТИСТИКА</b>

👥 **Корисници:**
• Вкупно: {vkupno}
• Активни: {aktivni}
• Чекаат: {pending}
• Одбиени: {denied}

💵 **Барања за пари:**
• Чекаат: {baranja_pari}
• Одобрени: {odobreni_pari}

📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"""

    await query.edit_message_text(
        stats_text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
        ])
    )

# ========== АДМИН - БАРАЊА ЗА ПАРИ ==========
async def admin_baranja_pari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, username, iznos, datum FROM baranja_za_pari WHERE status = "pending" ORDER BY id DESC')
    baranja = cursor.fetchall()
    conn.close()
    
    if not baranja:
        await query.edit_message_text(
            "💵 **БАРАЊА ЗА ПАРИ**\n\nНема нови барања.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
            ])
        )
        return
    
    tekst = "<b>💵 БАРАЊА ЗА ПАРИ</b>\n\n"
    for baranje in baranja:
        id, user_id, username, iznos, datum = baranje
        tekst += f"🆔 ID: `{user_id}` | @{username}\n"
        tekst += f"💰 {iznos} | 📅 {datum}\n"
        tekst += f"✅ /odobri_{id} | ❌ /odbi_{id}\n\n"
    
    await query.edit_message_text(
        tekst,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Освежи", callback_data="admin_baranja_pari")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
        ])
    )

# ========== АДМИН - ОДОБРИ/ОДБИЈ ПАРИ ==========
async def odobri_odbi_pari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ова е за команди /odobri_1 /odbi_1
    pass

# ========== ЛИЦЕНЦА HANDLER ==========
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
    
    # Одобри лиценца
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
    
    # Земете ги податоците за корисникот
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, first_name FROM korisnici WHERE user_id = ?', (user_id,))
    korisnik = cursor.fetchone()
    conn.close()
    
    await query.edit_message_text(
        f"✅ **Корисникот е одобрен!**\n\n"
        f"👤 @{korisnik[0] if korisnik else 'N/A'}\n"
        f"🆔 `{user_id}`\n"
        f"📅 Времетраење: {opis}",
        parse_mode='Markdown'
    )
    
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

# ========== НАЗАД ВО АДМИН ==========
async def admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await prikazi_admin_panel(update)

# ========== КОМАНДИ ==========
async def komanda_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text(
            "❓ **Помош**\n\n"
            "Напишете /start за да започнете.\n"
            "Ако немате лиценца, ќе побарате пристап.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        "👑 **Админ Команди**\n\n"
        "/start - Админ панел\n"
        "/help - Оваа порака\n"
        "/status - Статус на ботот\n\n"
        "📌 Корисниците автоматски бараат пристап.",
        parse_mode='Markdown'
    )

async def komanda_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    
    await update.message.reply_text(
        f"🟢 **Ботот е активен!**\n\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"✅ Сите системи работат.",
        parse_mode='Markdown'
    )

# ========== MAIN ==========
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Конверзација
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ADMIN_MENU: [
                CallbackQueryHandler(admin_back, pattern='^admin_back$'),
                CallbackQueryHandler(admin_user_list, pattern='^admin_user_list$'),
                CallbackQueryHandler(admin_remove_user, pattern='^admin_remove_user$'),
                CallbackQueryHandler(admin_stats, pattern='^admin_stats$'),
                CallbackQueryHandler(admin_baranja_pari, pattern='^admin_baranja_pari$'),
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
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(baraj_pristap, pattern='^baraj_pristap$'))
    application.add_handler(CallbackQueryHandler(baraj_pari, pattern='^baraj_pari$'))
    application.add_handler(CallbackQueryHandler(primi_baranje_pari, pattern='^pari_'))
    application.add_handler(CallbackQueryHandler(unlock_all, pattern='^unlock_all$'))
    application.add_handler(CallbackQueryHandler(signout, pattern='^signout$'))
    application.add_handler(CallbackQueryHandler(licenca_handler, pattern='^lic_'))
    application.add_handler(CallbackQueryHandler(prikazi_user_menu, pattern='^nazad_glavno$'))
    application.add_handler(CallbackQueryHandler(admin_back, pattern='^admin_back$'))
    application.add_handler(CallbackQueryHandler(admin_user_list, pattern='^admin_user_list$'))
    application.add_handler(CallbackQueryHandler(admin_remove_user, pattern='^admin_remove_user$'))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    application.add_handler(CallbackQueryHandler(admin_baranja_pari, pattern='^admin_baranja_pari$'))
    
    # Команди
    application.add_handler(CommandHandler('help', komanda_help))
    application.add_handler(CommandHandler('status', komanda_status))
    application.add_handler(CommandHandler('start', start))

    print("🤖 Ботот е стартуван!")
    print(f"👑 Админ ID: {ADMIN_ID}")
    application.run_polling()

if __name__ == '__main__':
    import asyncio
    main()
