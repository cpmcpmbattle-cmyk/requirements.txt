import asyncio
import logging
import random
import threading
from datetime import datetime
from bson import ObjectId

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
    ChatJoinRequest
)
from motor.motor_asyncio import AsyncIOMotorClient
from flask import Flask

# ==========================================
# BOT VA BAZA SOZLAMALARI
# ==========================================
BOT_TOKEN = "8734592942:AAFeKV1VP5F6hCxM4cIuQZUOYvD3298yOPI"
MONGO_URL = "mongodb+srv://cpmcpmbattle_db_user:lKQN2ePocUCIM9zi@cluster0.brsfu0p.mongodb.net/?appName=Cluster0"  # MongoDB Atlas havolasi (Render uchun) yoki lokal "mongodb://localhost:27017"
DB_NAME = "konkurs_bot_db"
ADMIN_ID = 6968399046  # Telegram ID ingiz (son ko'rinishida)

# ==========================================
# FLASK SERVER (24/7 Uptime uchun)
# ==========================================
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running perfectly 24/7!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ==========================================
# MONGODB BAZA BAG'LANISHI
# ==========================================
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
users_col = db.users
contests_col = db.contests
channels_col = db.channels
join_requests_col = db.join_requests
prizes_col = db.prizes

# ==========================================
# BOT VA DISPATCHER INITIALIZATION
# ==========================================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ==========================================
# MULTI-LANGUAGE MATNLAR (UZ, RU, EN)
# ==========================================
TEXTS = {
    'uz': {
        'choose_lang': "Tilni tanlang 🇺🇿 / 🇺🇸 / 🇷🇺",
        'welcome': "Xush kelibsiz! Kerakli bo'limni tanlang:",
        'btn_prizes': "| MEN YUTGAN SOVRINLAR 🛒|",
        'btn_lang': "| TIL ALMASHTIRISH 🌐 |",
        'btn_admin_create': "| KONKURS YARATISH 🛒 |",
        'btn_admin_stat': "| BOT STATISTIKASI📊 |",
        'btn_admin_channels': "| MAJBURIY OBUNA ULASH 📣 |",
        'ask_prizes_count': "Nechta akkaunt qoʻyamiz?\nYozing📦\n(Faqat son koʻrinishida)",
        'ask_max_users': "Endi nechta odam qatnasha oladi?\nYozing ✉️\n(Faqat son koʻrinishida)",
        'ask_accounts': "Akkauntlarni quyidagi formatda yuboring🔖:\n\n<code>01 | email | parol | OK</code>\n<code>02 | email | parol | OK</code>\n\n(Har bir akkauntni yangi qatordan yozing)",
        'channel_msg_title': "Konkurs boshlandi 📣\n\nYutuqlar🎁: {prizes_count}ta akkaunt\nTugashi: {current}/{max_users}\n\nQatnashish uchun pastdagi tugmani bosing!",
        'btn_channel_join': "KOʻNKURSGA QATNASHING🎁",
        'must_subscribe': "Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
        'already_joined': "Siz allaqachon ushbu konkursda qatnashmoqdasiz!",
        'joined_success': "Siz muvaffaqiyatli qatnashdingiz✅",
        'no_prizes': "Sizda hali yutib olingan sovrinlar yo'q 🛒",
        'your_prizes': "🛒 Siz yutgan sovrinlar:\n\n",
        'contest_finished_channel': "🏁 <b>KOʻNKURS YAKUNLANDI</b>\n\n{winners_text}",
        'won_notify': "🎉 TASHAKKURLAR! Siz konkursda g'olib bo'ldingiz!\n\nSizning sovriningiz:\n<code>{account}</code>",
        'invalid_number': "Xatolik! Iltimos, faqat musbat son kiriting.",
        'accounts_mismatch': "Akkauntlar soni kam yoki noto'g'ri. Kamida {prizes_count} ta akkaunt yuboring:",
        'channels_menu': "Majburiy obuna boshqaruvi bo'limi:",
        'btn_add_channel': "➕ Kanal/Guruh qo'shish",
        'btn_del_channel': "➖ Majburiy obunani olib tashlash",
        'select_ch_type': "Qaysi turdagi kanal/guruh qo'shmoqchisiz?",
        'type_channel': "ODDIY KANAL📣",
        'type_group': "CHAT GURUH ✉️",
        'type_request': "ZAYAFKA KANAL📦",
        'ask_channel_link': "Kanal username yoki havolasini yuboring (Masalan: @kanal yoki https://t.me/kanal):\n<i>Bot kanalga admin bo'lishi shart!</i>",
        'ask_group_link': "Guruh username yoki havolasini yuboring (Masalan: @guruh yoki https://t.me/guruh):\n<i>Bot guruhda admin bo'lishi shart!</i>",
        'ask_request_link': "Zayafka (Join Request) taklif havolasini yuboring (Masalan: https://t.me/+AbCdEfGhIj):\n<i>Bot ushbu kanalda admin bo'lishi shart!</i>",
        'channel_added': "✅ Muvaffaqiyatli qo'shildi!",
        'channel_deleted': "🗑 Majburiy obuna muvaffaqiyatli olib tashlandi!",
        'check_sub_btn': "✅ Tekshirish",
        'no_channels_to_del': "Hali hech qanday majburiy obuna qo'shilmagan."
    },
    'ru': {
        'choose_lang': "Tilni tanlang 🇺🇿 / 🇺🇸 / 🇷🇺",
        'welcome': "Добро пожаловать! Выберите нужный раздел:",
        'btn_prizes': "| МОИ ПРИЗЫ 🛒|",
        'btn_lang': "| СМЕНА ЯЗЫКА 🌐 |",
        'btn_admin_create': "| СОЗДАТЬ КОНКУРС 🛒 |",
        'btn_admin_stat': "| СТАТИСТИКА БОТА 📊 |",
        'btn_admin_channels': "| ОБЯЗАТЕЛЬНАЯ ПОДПИСКА 📣 |",
        'ask_prizes_count': "Сколько аккаунтов разыгрываем?\nНапишите 📦\n(Только число)",
        'ask_max_users': "Сколько человек может участвовать?\nНапишите ✉️\n(Только число)",
        'ask_accounts': "Отправьте аккаунты в формате🔖:\n\n<code>01 | email | pass | OK</code>\n<code>02 | email | pass | OK</code>",
        'channel_msg_title': "Конкурс начался 📣\n\nПризы🎁: {prizes_count} шт. аккаунтов\nЗавершение: {current}/{max_users}\n\nНажмите кнопку ниже для участия!",
        'btn_channel_join': "УЧАСТВОВАТЬ В КОНКУРСЕ🎁",
        'must_subscribe': "Для использования бота подпишитесь на каналы:",
        'already_joined': "Вы уже участвуете в этом конкурсе!",
        'joined_success': "Вы успешно участвовали✅",
        'no_prizes': "У вас пока нет выигранных призов 🛒",
        'your_prizes': "🛒 Ваши выигранные призы:\n\n",
        'contest_finished_channel': "🏁 <b>КОНКУРС ЗАВЕРШЕН</b>\n\n{winners_text}",
        'won_notify': "🎉 ПОЗДРАВЛЯЕМ! Вы выиграли в конкурсе!\n\nВаш приз:\n<code>{account}</code>",
        'invalid_number': "Ошибка! Введите только положительное число.",
        'accounts_mismatch': "Количество аккаунтов меньше указанного ({prizes_count} шт.). Отправьте снова:",
        'channels_menu': "Управление обязательной подпиской:",
        'btn_add_channel': "➕ Добавить канал/группу",
        'btn_del_channel': "➖ Удалить обязательную подписку",
        'select_ch_type': "Какой тип подписки добавить?",
        'type_channel': "ОБЫЧНЫЙ КАНАЛ📣",
        'type_group': "ЧАТ ГРУППА ✉️",
        'type_request': "ЗАЯВКА КАНАЛ📦",
        'ask_channel_link': "Отправьте username или ссылку на канал (Например: @channel):\n<i>Бот должен быть админом!</i>",
        'ask_group_link': "Отправьте username или ссылку на группу (Например: @group):\n<i>Бот должен быть админом!</i>",
        'ask_request_link': "Отправьте ссылку-заявку (Например: https://t.me/+...):\n<i>Бот должен быть админом в этом канале!</i>",
        'channel_added': "✅ Успешно добавлено!",
        'channel_deleted': "🗑 Обязательная подписка успешно удалена!",
        'check_sub_btn': "✅ Проверить",
        'no_channels_to_del': "Список обязательных подписок пуст."
    },
    'en': {
        'choose_lang': "Tilni tanlang 🇺🇿 / 🇺🇸 / 🇷🇺",
        'welcome': "Welcome! Select an option below:",
        'btn_prizes': "| MY PRIZES 🛒|",
        'btn_lang': "| CHANGE LANGUAGE 🌐 |",
        'btn_admin_create': "| CREATE CONTEST 🛒 |",
        'btn_admin_stat': "| BOT STATS 📊 |",
        'btn_admin_channels': "| MANDATORY SUBS 📣 |",
        'ask_prizes_count': "How many accounts to giveaway?\nWrite 📦\n(Numbers only)",
        'ask_max_users': "How many participants can join?\nWrite ✉️\n(Numbers only)",
        'ask_accounts': "Send accounts as format🔖:\n\n<code>01 | email | pass | OK</code>\n<code>02 | email | pass | OK</code>",
        'channel_msg_title': "Contest started 📣\n\nPrizes🎁: {prizes_count} accounts\nProgress: {current}/{max_users}\n\nClick button below to participate!",
        'btn_channel_join': "JOIN CONTEST🎁",
        'must_subscribe': "Subscribe to channels to use the bot:",
        'already_joined': "You are already participating in this contest!",
        'joined_success': "Successfully participated✅",
        'no_prizes': "You haven't won any prizes yet 🛒",
        'your_prizes': "🛒 Your prizes:\n\n",
        'contest_finished_channel': "🏁 <b>CONTEST FINISHED</b>\n\n{winners_text}",
        'won_notify': "🎉 CONGRATULATIONS! You won in the contest!\n\nYour prize:\n<code>{account}</code>",
        'invalid_number': "Error! Please send a positive number.",
        'accounts_mismatch': "Number of accounts doesn't match ({prizes_count}). Send again:",
        'channels_menu': "Mandatory Subscription Management:",
        'btn_add_channel': "➕ Add Channel/Group",
        'btn_del_channel': "➖ Remove Subscription",
        'select_ch_type': "Select subscription type to add:",
        'type_channel': "REGULAR CHANNEL📣",
        'type_group': "CHAT GROUP ✉️",
        'type_request': "REQUEST CHANNEL📦",
        'ask_channel_link': "Send channel username or link:\n<i>Bot must be admin in channel!</i>",
        'ask_group_link': "Send group username or link:\n<i>Bot must be admin in group!</i>",
        'ask_request_link': "Send Join Request invite link:\n<i>Bot must be admin in channel!</i>",
        'channel_added': "✅ Successfully added!",
        'channel_deleted': "🗑 Mandatory subscription removed!",
        'check_sub_btn': "✅ Check",
        'no_channels_to_del': "No mandatory subscriptions added yet."
    }
}

ALL_PRIZES_BTNS = [t['btn_prizes'] for t in TEXTS.values()]
ALL_LANG_BTNS = [t['btn_lang'] for t in TEXTS.values()]
ALL_ADMIN_CREATE_BTNS = [t['btn_admin_create'] for t in TEXTS.values()]
ALL_ADMIN_STAT_BTNS = [t['btn_admin_stat'] for t in TEXTS.values()]
ALL_ADMIN_CHANNELS_BTNS = [t['btn_admin_channels'] for t in TEXTS.values()]

# ==========================================
# FSM STATES
# ==========================================
class AdminCreateContest(StatesGroup):
    waiting_prizes_count = State()
    waiting_max_users = State()
    waiting_accounts = State()
    waiting_target_channel = State()

class ChannelManageStates(StatesGroup):
    waiting_link = State()

# ==========================================
# YORDAMCHI FUNKSIYALAR
# ==========================================
async def get_user_lang(user_id: int):
    user = await users_col.find_one({"user_id": user_id})
    if user and user.get('lang'):
        return user['lang']
    return None

def get_main_keyboard(user_id: int, lang: str):
    t = TEXTS[lang]
    buttons = [
        [KeyboardButton(text=t['btn_prizes'])],
        [KeyboardButton(text=t['btn_lang'])]
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text=t['btn_admin_create'])])
        buttons.append([KeyboardButton(text=t['btn_admin_stat']), KeyboardButton(text=t['btn_admin_channels'])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="choose_lang_uz"),
            InlineKeyboardButton(text="🇺🇸 English", callback_data="choose_lang_en"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="choose_lang_ru")
        ]
    ])

def fix_url(url_str: str) -> str:
    if not url_str: return "https://t.me"
    url_str = url_str.strip()
    if url_str.startswith(("http://", "https://")): return url_str
    if url_str.startswith("@"): return f"https://t.me/{url_str[1:]}"
    return f"https://t.me/{url_str}"

async def check_user_subscriptions(user_id: int) -> bool:
    channels = await channels_col.find().to_list(length=100)
    if not channels:
        return True
    for ch in channels:
        ch_type = ch.get('type', 'channel')
        chat_id = ch.get('chat_id') or ch.get('channel_id')
        
        if ch_type in ['channel', 'group'] and chat_id:
            try:
                member = await bot.get_chat_member(chat_id=int(chat_id), user_id=user_id)
                if member.status in ['left', 'kicked']:
                    return False
            except Exception:
                pass
        elif ch_type == 'request':
            req = await join_requests_col.find_one({"user_id": user_id, "chat_id": chat_id})
            if not req:
                return False
    return True

async def get_required_channels_keyboard(lang: str, contest_id: str = None):
    channels = await channels_col.find().to_list(length=100)
    buttons = []
    for channel in channels:
        title = channel.get("title", "Kanal")
        raw_url = channel.get("url")
        if raw_url:
            clean_url = fix_url(raw_url)
            buttons.append([InlineKeyboardButton(text=f"📣 {title}", url=clean_url)])

    callback_data = "check_main_sub"
    if contest_id:
        callback_data = f"check_contest_sub_{contest_id}"

    buttons.append([InlineKeyboardButton(text=TEXTS[lang]["check_sub_btn"], callback_data=callback_data)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==========================================
# CHAT JOIN REQUEST LISTENER (ZAYAFKA)
# ==========================================
@dp.chat_join_request()
async def handle_join_request(update: ChatJoinRequest):
    await join_requests_col.update_one(
        {"user_id": update.from_user.id, "chat_id": update.chat.id},
        {"$set": {"user_id": update.from_user.id, "chat_id": update.chat.id, "date": datetime.now()}},
        upsert=True
    )

# ==========================================
# START VA TIL TANLASH
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    contest_id = args[1].replace("contest_", "") if len(args) > 1 and args[1].startswith("contest_") else None

    lang = await get_user_lang(user_id)

    if not lang:
        await users_col.update_one(
            {"user_id": user_id},
            {"$set": {"pending_contest_id": contest_id, "username": message.from_user.username, "first_name": message.from_user.first_name}},
            upsert=True
        )
        await message.answer(TEXTS['uz']['choose_lang'], reply_markup=language_keyboard())
        return

    is_subbed = await check_user_subscriptions(user_id)
    if not is_subbed:
        keyboard = await get_required_channels_keyboard(lang=lang, contest_id=contest_id)
        await message.answer(TEXTS[lang]['must_subscribe'], reply_markup=keyboard)
        return

    if contest_id:
        await process_join_contest(user_id, contest_id, message)
        return

    await message.answer(TEXTS[lang]['welcome'], reply_markup=get_main_keyboard(user_id, lang))

@dp.callback_query(F.data.in_(["choose_lang_uz", "choose_lang_ru", "choose_lang_en", "setlang_uz", "setlang_ru", "setlang_en"]))
async def choose_language(call: CallbackQuery):
    user_id = call.from_user.id
    new_lang = call.data.split("_")[-1]

    if new_lang not in TEXTS:
        await call.answer("Error", show_alert=True)
        return

    user = await users_col.find_one({"user_id": user_id})
    pending_contest_id = user.get("pending_contest_id") if user else None

    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"lang": new_lang, "updated_at": datetime.now()}, "$unset": {"pending_contest_id": ""}},
        upsert=True
    )

    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass

    is_subbed = await check_user_subscriptions(user_id)
    if not is_subbed:
        keyboard = await get_required_channels_keyboard(lang=new_lang, contest_id=pending_contest_id)
        await call.message.answer(TEXTS[new_lang]['must_subscribe'], reply_markup=keyboard)
        return

    if pending_contest_id:
        await process_join_contest(user_id, pending_contest_id, call.message)
        return

    await call.message.answer(TEXTS[new_lang]['welcome'], reply_markup=get_main_keyboard(user_id, new_lang))

@dp.callback_query(F.data == "check_main_sub")
async def check_main_subscription(call: CallbackQuery):
    user_id = call.from_user.id
    lang = await get_user_lang(user_id) or 'uz'

    is_subbed = await check_user_subscriptions(user_id)
    if not is_subbed:
        err_msg = "Siz hali barcha kanallarga obuna bo'lmadingiz! ❌" if lang == 'uz' else ("Вы еще не подписались на все каналы! ❌" if lang == 'ru' else "You have not subscribed to all channels! ❌")
        await call.answer(err_msg, show_alert=True)
        return

    await call.message.delete()
    await call.message.answer(TEXTS[lang]['welcome'], reply_markup=get_main_keyboard(user_id, lang))

@dp.callback_query(F.data.startswith("check_contest_sub_"))
async def check_contest_subscription(call: CallbackQuery):
    user_id = call.from_user.id
    contest_id = call.data.replace("check_contest_sub_", "")

    is_subbed = await check_user_subscriptions(user_id)
    if not is_subbed:
        lang = await get_user_lang(user_id) or 'uz'
        err_msg = "Siz hali barcha kanallarga obuna bo'lmadingiz! ❌" if lang == 'uz' else ("Вы еще не подписались на все каналы! ❌" if lang == 'ru' else "You have not subscribed to all channels! ❌")
        await call.answer(err_msg, show_alert=True)
        return

    await call.message.delete()
    await process_join_contest(user_id, contest_id, call.message)

# ==========================================
# MENYU TUGMALARI
# ==========================================
@dp.message(F.text.in_(ALL_LANG_BTNS) | F.text.contains("TIL ALMASHTIRISH") | F.text.contains("СМЕНА ЯЗЫКА") | F.text.contains("CHANGE LANGUAGE"))
async def process_change_lang(message: types.Message):
    await message.answer("Tilni tanlang 🇺🇿 / 🇺🇸 / 🇷🇺:", reply_markup=language_keyboard())

@dp.message(F.text.in_(ALL_PRIZES_BTNS) | F.text.contains("YUTGAN SOVRINLAR") | F.text.contains("МОИ ПРИЗЫ") | F.text.contains("MY PRIZES"))
async def show_prizes(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_lang(user_id) or 'uz'

    is_subbed = await check_user_subscriptions(user_id)
    if not is_subbed:
        keyboard = await get_required_channels_keyboard(lang=lang)
        await message.answer(TEXTS[lang]['must_subscribe'], reply_markup=keyboard)
        return

    t = TEXTS[lang]
    prizes = await prizes_col.find({"user_id": user_id}).to_list(length=100)
    
    if not prizes:
        await message.answer(t['no_prizes'])
    else:
        text = t['your_prizes']
        for idx, p in enumerate(prizes, 1):
            text += f"{idx}. <code>{p['account']}</code>\n"
        await message.answer(text, parse_mode="HTML")

@dp.message(F.text.in_(ALL_ADMIN_CHANNELS_BTNS) | F.text.contains("MAJBURIY OBUNA") | F.text.contains("ОБЯЗАТЕЛЬНАЯ ПОДПИСКА") | F.text.contains("MANDATORY SUBS"))
async def admin_channels_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    lang = await get_user_lang(message.from_user.id) or 'uz'
    t = TEXTS[lang]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t['btn_add_channel'], callback_data="sub_add_menu")],
        [InlineKeyboardButton(text=t['btn_del_channel'], callback_data="sub_del_menu")]
    ])
    await message.answer(t['channels_menu'], reply_markup=kb)

@dp.message(F.text.in_(ALL_ADMIN_CREATE_BTNS) | F.text.contains("KONKURS YARATISH") | F.text.contains("СОЗДАТЬ КОНКУРС") | F.text.contains("CREATE CONTEST"))
async def admin_start_create(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    lang = await get_user_lang(message.from_user.id) or 'uz'
    await state.update_data(admin_lang=lang)
    await message.answer(TEXTS[lang]['ask_prizes_count'])
    await state.set_state(AdminCreateContest.waiting_prizes_count)

@dp.message(F.text.in_(ALL_ADMIN_STAT_BTNS) | F.text.contains("STATISTIKASI") | F.text.contains("СТАТИСТИКА") | F.text.contains("STATS"))
async def show_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    users_count = await users_col.count_documents({})
    contests_count = await contests_col.count_documents({})
    await message.answer(f"📊 <b>Bot Statistikasi:</b>\n\n👤 Jami foydalanuvchilar: {users_count}\n🛒 O'tkazilgan konkurslar: {contests_count}", parse_mode="HTML")

# ==========================================
# ADMIN: MAJBURIY OBUNA BOSHQARUVI
# ==========================================
@dp.callback_query(F.data == "sub_add_menu")
async def choose_sub_type(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id) or 'uz'
    t = TEXTS[lang]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t['type_channel'], callback_data="add_type_channel")],
        [InlineKeyboardButton(text=t['type_group'], callback_data="add_type_group")],
        [InlineKeyboardButton(text=t['type_request'], callback_data="add_type_request")]
    ])
    await call.message.edit_text(t['select_ch_type'], reply_markup=kb)

@dp.callback_query(F.data.startswith("add_type_"))
async def prompt_channel_link(call: CallbackQuery, state: FSMContext):
    ch_type = call.data.replace("add_type_", "")
    lang = await get_user_lang(call.from_user.id) or 'uz'
    t = TEXTS[lang]
    await state.update_data(ch_type=ch_type)
    
    if ch_type == 'channel':
        await call.message.edit_text(t['ask_channel_link'], parse_mode="HTML")
    elif ch_type == 'group':
        await call.message.edit_text(t['ask_group_link'], parse_mode="HTML")
    else:
        await call.message.edit_text(t['ask_request_link'], parse_mode="HTML")
        
    await state.set_state(ChannelManageStates.waiting_link)

@dp.message(ChannelManageStates.waiting_link)
async def process_save_channel(message: types.Message, state: FSMContext):
    data = await state.get_data()
    ch_type = data['ch_type']
    lang = await get_user_lang(message.from_user.id) or 'uz'
    t = TEXTS[lang]
    input_val = message.text.strip()
    
    try:
        if ch_type in ['channel', 'group']:
            chat_identifier = input_val.replace("https://t.me/", "@") if "t.me/" in input_val and not "+" in input_val else input_val
            chat = await bot.get_chat(chat_identifier)
            chat_id = chat.id
            title = chat.title
            link = fix_url(f"https://t.me/{chat.username}" if chat.username else input_val)
        else:
            link = fix_url(input_val)
            title = f"Zayafka Kanal ({input_val})"
            chat_id = None
            
        await channels_col.insert_one({
            "type": ch_type,
            "chat_id": chat_id,
            "channel_id": chat_id,
            "title": title,
            "url": link,
            "created_at": datetime.now()
        })
        await message.answer(t['channel_added'])
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}\nBot kanal/guruhda administrator ekanligiga ishonch hosil qiling!")
        
    await state.clear()

@dp.callback_query(F.data == "sub_del_menu")
async def show_del_channels(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id) or 'uz'
    t = TEXTS[lang]
    channels = await channels_col.find().to_list(length=100)
    
    if not channels:
        await call.message.edit_text(t['no_channels_to_del'])
        return
        
    buttons = []
    for ch in channels:
        ch_id_str = str(ch['_id'])
        buttons.append([InlineKeyboardButton(text=f"🗑 {ch.get('title', 'Kanal')}", callback_data=f"del_ch_{ch_id_str}")])
        
    await call.message.edit_text("Olib tashlamoqchi bo'lgan majburiy obunani tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("del_ch_"))
async def confirm_del_channel(call: CallbackQuery):
    ch_id_str = call.data.replace("del_ch_", "")
    lang = await get_user_lang(call.from_user.id) or 'uz'
    t = TEXTS[lang]
    
    await channels_col.delete_one({"_id": ObjectId(ch_id_str)})
    await call.message.edit_text(t['channel_deleted'])

# ==========================================
# ADMIN: KONKURS YARATISH (FORMAT QABUL QILISHI BILAN)
# ==========================================
@dp.message(AdminCreateContest.waiting_prizes_count)
async def process_prizes_count(message: types.Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id) or 'uz'
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer(TEXTS[lang]['invalid_number'])
        return
    await state.update_data(prizes_count=int(message.text))
    await message.answer(TEXTS[lang]['ask_max_users'])
    await state.set_state(AdminCreateContest.waiting_max_users)

@dp.message(AdminCreateContest.waiting_max_users)
async def process_max_users(message: types.Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id) or 'uz'
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer(TEXTS[lang]['invalid_number'])
        return
    await state.update_data(max_users=int(message.text))
    await message.answer(TEXTS[lang]['ask_accounts'], parse_mode="HTML")
    await state.set_state(AdminCreateContest.waiting_accounts)

@dp.message(AdminCreateContest.waiting_accounts)
async def process_accounts(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = await get_user_lang(message.from_user.id) or 'uz'
    prizes_count = data['prizes_count']
    
    accounts = [line.strip() for line in message.text.split("\n") if line.strip()]
    if len(accounts) < prizes_count:
        await message.answer(TEXTS[lang]['accounts_mismatch'].format(prizes_count=prizes_count))
        return
    
    await state.update_data(accounts=accounts)
    
    channels = await channels_col.find().to_list(length=100)
    valid_channels = [ch for ch in channels if (ch.get('type') == 'channel' or 'type' not in ch) and (ch.get('chat_id') or ch.get('channel_id'))]
    
    if not valid_channels:
        await message.answer("⚠️ Konkurs chiqarish uchun avval Majburiy Obuna bo'limidan 'ODDIY KANAL' qo'shing!")
        await state.clear()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ch.get('title', 'Kanal'), callback_data=f"target_chan_{ch.get('chat_id') or ch.get('channel_id')}")] for ch in valid_channels
    ])
    await message.answer("Konkurs yuborilishi kerak bo'lgan kanalni tanlang:", reply_markup=kb)
    await state.set_state(AdminCreateContest.waiting_target_channel)

@dp.callback_query(F.data.startswith("target_chan_"), AdminCreateContest.waiting_target_channel)
async def publish_contest(call: CallbackQuery, state: FSMContext):
    channel_id = int(call.data.replace("target_chan_", ""))
    data = await state.get_data()
    lang = data.get('admin_lang', 'uz')
    t = TEXTS[lang]
    
    prizes_count = data['prizes_count']
    max_users = data['max_users']
    accounts = data['accounts']
    
    contest_doc = {
        "prizes_count": prizes_count,
        "max_users": max_users,
        "current_users": 0,
        "status": "active",
        "channel_id": channel_id,
        "accounts": accounts,
        "participants": [],
        "lang": lang,
        "created_at": datetime.now()
    }
    result = await contests_col.insert_one(contest_doc)
    contest_id = str(result.inserted_id)

    bot_info = await bot.get_me()
    btn_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t['btn_channel_join'],
            url=f"https://t.me/{bot_info.username}?start=contest_{contest_id}"
        )]
    ])
    
    msg_text = t['channel_msg_title'].format(prizes_count=prizes_count, current=0, max_users=max_users)
    
    try:
        sent_msg = await bot.send_message(chat_id=channel_id, text=msg_text, reply_markup=btn_kb)
        await contests_col.update_one({"_id": result.inserted_id}, {"$set": {"channel_msg_id": sent_msg.message_id}})
        await call.message.edit_text("✅ Konkurs kanalga muvaffaqiyatli joylandi!")
    except Exception as e:
        await call.message.edit_text(f"❌ Xatolik: {e}")
        
    await state.clear()

# ==========================================
# KONKURSGA QATNASHISH VA YAKUNLASH
# ==========================================
async def process_join_contest(user_id: int, contest_id_str: str, message: types.Message):
    lang = await get_user_lang(user_id) or 'uz'
    t = TEXTS[lang]
    
    try:
        contest_obj_id = ObjectId(contest_id_str)
    except Exception:
        await message.answer("⚠️ Noto'g'ri konkurs havolasi.", reply_markup=get_main_keyboard(user_id, lang))
        return

    contest = await contests_col.find_one({"_id": contest_obj_id})
    if not contest or contest['status'] != 'active':
        await message.answer("⚠️ Bu konkurs yakunlangan yoki mavjud emas.", reply_markup=get_main_keyboard(user_id, lang))
        return

    is_subbed = await check_user_subscriptions(user_id)
    if not is_subbed:
        keyboard = await get_required_channels_keyboard(lang=lang, contest_id=contest_id_str)
        await message.answer(t['must_subscribe'], reply_markup=keyboard)
        return

    if user_id in contest['participants']:
        await message.answer(t['already_joined'], reply_markup=get_main_keyboard(user_id, lang))
        return

    await contests_col.update_one(
        {"_id": contest_obj_id},
        {"$push": {"participants": user_id}, "$inc": {"current_users": 1}}
    )
    
    updated_contest = await contests_col.find_one({"_id": contest_obj_id})
    curr = updated_contest['current_users']
    max_u = updated_contest['max_users']
    prizes_c = updated_contest['prizes_count']
    ch_id = updated_contest['channel_id']
    ch_msg_id = updated_contest.get('channel_msg_id')
    c_lang = updated_contest['lang']

    await message.answer(t['joined_success'], reply_markup=get_main_keyboard(user_id, lang))

    try:
        admin_t = TEXTS[c_lang]
        bot_info = await bot.get_me()
        updated_text = admin_t['channel_msg_title'].format(prizes_count=prizes_c, current=curr, max_users=max_u)
        btn_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=admin_t['btn_channel_join'],
                url=f"https://t.me/{bot_info.username}?start=contest_{contest_id_str}"
            )]
        ])
        if ch_msg_id:
            await bot.edit_message_text(chat_id=ch_id, message_id=ch_msg_id, text=updated_text, reply_markup=btn_kb)
    except Exception:
        pass

    if curr >= max_u:
        await finish_contest(contest_obj_id)

async def finish_contest(contest_obj_id: ObjectId):
    contest = await contests_col.find_one({"_id": contest_obj_id})
    if not contest or contest['status'] != 'active':
        return

    await contests_col.update_one({"_id": contest_obj_id}, {"$set": {"status": "finished"}})
    
    participants = contest['participants']
    accounts = contest['accounts']
    prizes_count = contest['prizes_count']
    channel_id = contest['channel_id']
    ch_msg_id = contest.get('channel_msg_id')
    c_lang = contest['lang']

    winners_count = min(len(participants), prizes_count)
    winners = random.sample(participants, winners_count) if participants else []

    winners_text = ""
    medals = ["1️⃣ OʻRIN🥇", "2️⃣ OʻRIN🥈", "3️⃣ OʻRIN🥉", "4️⃣ OʻRIN🏆", "5️⃣ OʻRIN🏆", "6️⃣ OʻRIN🏆", "7️⃣ OʻRIN🏆", "8️⃣ OʻRIN🏆", "9️⃣ OʻRIN🏆", "🔟 OʻRIN🏆"]

    for idx, winner_id in enumerate(winners):
        account = accounts[idx] # Format: 01 | email | parol | OK
        await prizes_col.insert_one({
            "user_id": winner_id,
            "contest_id": str(contest_obj_id),
            "account": account,
            "won_at": datetime.now()
        })
        
        try:
            chat_member = await bot.get_chat(winner_id)
            if chat_member.username:
                user_display = f"@{chat_member.username}"
            else:
                user_display = chat_member.first_name
        except Exception:
            user_display = f"ID: {winner_id}"

        medal_title = medals[idx] if idx < len(medals) else f"{idx+1} OʻRIN🏆"
        winners_text += f"{medal_title} - {user_display}\n"

        u_lang = await get_user_lang(winner_id) or 'uz'
        try:
            await bot.send_message(winner_id, TEXTS[u_lang]['won_notify'].format(account=account), parse_mode="HTML")
        except Exception:
            pass

    admin_t = TEXTS[c_lang]
    final_text = admin_t['contest_finished_channel'].format(winners_text=winners_text)
    try:
        if ch_msg_id:
            await bot.edit_message_text(chat_id=channel_id, message_id=ch_msg_id, text=final_text, parse_mode="HTML", reply_markup=None)
    except Exception:
        pass

# ==========================================
# ASOSIY ISHGA TUSHIRISH (MAIN)
# ==========================================
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    logging.basicConfig(level=logging.INFO)
    
    # Render konflikti oldini olish uchun webhookni tozalash
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("Bot 100% mukammal va barcha funksiyalar bilan ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
