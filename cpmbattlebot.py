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
BOT_TOKEN = "8860001735:AAFkws82v2sTzgK1TXtxv-N0MmSseiHFJhk"
MONGO_URL = "mongodb+srv://cpmcpmbattle_db_user:lKQN2ePocUCIM9zi@cluster0.brsfu0p.mongodb.net/?appName=Cluster0" 
DB_NAME = "konkurs_bot_db"
ADMIN_ID = 6968399046  # Telegram ID ingiz

# ==========================================
# FLASK SERVER (24/7 Uptime)
# ==========================================
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running perfectly 24/7!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ==========================================
# MONGODB BAZA
# ==========================================
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
users_col = db.users
contests_col = db.contests
channels_col = db.channels
join_requests_col = db.join_requests
prizes_col = db.prizes

# ==========================================
# AIOGRAM INIT
# ==========================================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ==========================================
# MULTI-LANGUAGE MATNLAR
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
        'select_contest_type': "Qaysi turdagi konkurs qilasiz tanlang 🌟",
        'btn_type_account': "👉🏻 AKKAUNTLI",
        'btn_type_other': "👉🏻 BOSHQA",
        'ask_custom_prizes': "Konkursga nima yutuqlar qoʻyiladi yozing🎁\n(Masalan:\n1🥇- 30K COIN\n2🥈- 500K COIN\n3🥉- CHANGE ID)",
        'ask_winners_count': "Nechta odam gʻolib boʻladi yozing ⚡\n(Faqat son koʻrinishida)",
        'ask_prizes_count': "Nechta akkaunt qoʻyamiz?\nYozing📦\n(Faqat son koʻrinishida)",
        'ask_max_users': "Nechta odam qatnasha oladi yozing 🌟\n(Faqat son koʻrinishida)",
        'ask_accounts': "Akkauntlarni quyidagi formatda yuboring🔖:\n\n<code>01 | email | parol | OK</code>\n<code>02 | email | parol | OK</code>",
        'channel_msg_uz': "Konkurs boshlandi 📣\n\nYutuqlar🎁:\n{prizes_text}\nTugashi: {current}/{max_users}\n\nQatnashish uchun pastdagi tugmani bosing!",
        'channel_msg_en': "The contest has started📣\n\nPrizes 🎁:\n{prizes_text}\nEnds: {current}/{max_users}\n\nClick the button GOO 👇",
        'btn_channel_join': "GOO 🎁",
        'must_subscribe': "Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
        'already_joined': "Siz allaqachon ushbu konkursda qatnashmoqdasiz!",
        'joined_success': "Siz muvaffaqiyatli qatnashdingiz✅",
        'no_prizes': "Sizda hali yutib olingan sovrinlar yo'q 🛒",
        'your_prizes': "🛒 Siz yutgan sovrinlar:\n\n",
        'contest_finished_channel': "🏁 <b>KOʻNKURS YAKUNLANDI</b>\n\n{winners_text}",
        'won_notify': "🎉 TASHAKKURLAR! Siz konkursda g'olib bo'ldingiz!\n\nSizning sovriningiz:\n<code>{account}</code>",
        'invalid_number': "Xatolik! Iltimos, faqat musbat son kiriting.",
        'accounts_mismatch': "Akkauntlar soni {prizes_count} tadan kam. Qaytadan yuboring:",
        'channels_menu': "Majburiy obuna boshqaruvi:",
        'btn_add_channel': "➕ Kanal qo'shish",
        'btn_del_channel': "➖ Olib tashlash",
        'select_ch_type': "Turini tanlang:",
        'type_channel': "ODDIY KANAL📣",
        'type_group': "CHAT GURUH ✉️",
        'type_request': "ZAYAFKA KANAL📦",
        'channel_added': "✅ Qo'shildi!",
        'channel_deleted': "🗑 Olib tashlandi!",
        'check_sub_btn': "✅ Tekshirish",
        'no_channels_to_del': "Hali obuna qo'shilmagan."
    },
    'ru': {
        'choose_lang': "Tilni tanlang 🇺🇿 / 🇺🇸 / 🇷🇺",
        'welcome': "Выберите раздел:",
        'btn_prizes': "| МОИ ПРИЗЫ 🛒|",
        'btn_lang': "| СМЕНА ЯЗЫКА 🌐 |",
        'btn_admin_create': "| СОЗДАТЬ КОНКУРС 🛒 |",
        'btn_admin_stat': "| СТАТИСТИКА 📊 |",
        'btn_admin_channels': "| ПОДПИСКИ 📣 |",
        'select_contest_type': "Выберите тип конкурса 🌟",
        'btn_type_account': "👉🏻 АККАУНТЫ",
        'btn_type_other': "👉🏻 ДРУГОЕ",
        'ask_custom_prizes': "Напишите призы для конкурса🎁:",
        'ask_winners_count': "Сколько будет победителей ⚡:",
        'ask_prizes_count': "Сколько аккаунтов?",
        'ask_max_users': "Сколько участников?",
        'ask_accounts': "Отправьте аккаунты:",
        'channel_msg_uz': "Конкурс начался 📣",
        'channel_msg_en': "Contest started",
        'btn_channel_join': "GOO 🎁",
        'must_subscribe': "Подпишитесь на каналы:",
        'already_joined': "Вы уже участвуете!",
        'joined_success': "Успешно ✅",
        'no_prizes': "Нет призов 🛒",
        'your_prizes': "🛒 Ваши призы:\n\n",
        'contest_finished_channel': "🏁 <b>КОНКУРС ЗАВЕРШЕН</b>\n\n{winners_text}",
        'won_notify': "🎉 Ваш приз:\n<code>{account}</code>",
        'invalid_number': "Введите число.",
        'accounts_mismatch': "Мало аккаунтов:",
        'channels_menu': "Управление подписками:",
        'btn_add_channel': "➕ Добавить",
        'btn_del_channel': "➖ Удалить",
        'select_ch_type': "Тип:",
        'type_channel': "КАНАЛ📣",
        'type_group': "ГРУППА ✉️",
        'type_request': "ЗАЯВКА📦",
        'channel_added': "✅ Добавлено!",
        'channel_deleted': "🗑 Удалено!",
        'check_sub_btn': "✅ Проверить",
        'no_channels_to_del': "Список пуст."
    },
    'en': {
        'choose_lang': "Tilni tanlang 🇺🇿 / 🇺🇸 / 🇷🇺",
        'welcome': "Select option:",
        'btn_prizes': "| MY PRIZES 🛒|",
        'btn_lang': "| CHANGE LANGUAGE 🌐 |",
        'btn_admin_create': "| CREATE CONTEST 🛒 |",
        'btn_admin_stat': "| STATS 📊 |",
        'btn_admin_channels': "| SUBSCRIPTIONS 📣 |",
        'select_contest_type': "Select contest type 🌟",
        'btn_type_account': "👉🏻 ACCOUNTS",
        'btn_type_other': "👉🏻 OTHER",
        'ask_custom_prizes': "Write custom prizes🎁:",
        'ask_winners_count': "How many winners ⚡:",
        'ask_prizes_count': "How many accounts?",
        'ask_max_users': "How many participants?",
        'ask_accounts': "Send accounts:",
        'channel_msg_uz': "Contest started",
        'channel_msg_en': "Contest started",
        'btn_channel_join': "GOO 🎁",
        'must_subscribe': "Subscribe:",
        'already_joined': "Already joined!",
        'joined_success': "Success ✅",
        'no_prizes': "No prizes 🛒",
        'your_prizes': "🛒 Prizes:\n\n",
        'contest_finished_channel': "🏁 <b>FINISHED</b>\n\n{winners_text}",
        'won_notify': "🎉 Prize:\n<code>{account}</code>",
        'invalid_number': "Send number.",
        'accounts_mismatch': "Not enough:",
        'channels_menu': "Manage:",
        'btn_add_channel': "➕ Add",
        'btn_del_channel': "➖ Remove",
        'select_ch_type': "Type:",
        'type_channel': "CHANNEL",
        'type_group': "GROUP",
        'type_request': "REQUEST",
        'channel_added': "✅ Added!",
        'channel_deleted': "🗑 Removed!",
        'check_sub_btn': "✅ Check",
        'no_channels_to_del': "No channels."
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
    waiting_contest_type = State()
    waiting_custom_prizes = State()
    waiting_winners_count = State()
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
    return user.get('lang') if user else None

def get_main_keyboard(user_id: int, lang: str):
    t = TEXTS[lang]
    buttons = [[KeyboardButton(text=t['btn_prizes'])], [KeyboardButton(text=t['btn_lang'])]]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text=t['btn_admin_create'])])
        buttons.append([KeyboardButton(text=t['btn_admin_stat']), KeyboardButton(text=t['btn_admin_channels'])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="choose_lang_uz"),
         InlineKeyboardButton(text="🇺🇸 English", callback_data="choose_lang_en"),
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="choose_lang_ru")]
    ])

def fix_url(url_str: str) -> str:
    if not url_str: return "https://t.me"
    url_str = url_str.strip()
    if url_str.startswith(("http://", "https://")): return url_str
    if url_str.startswith("@"): return f"https://t.me/{url_str[1:]}"
    return f"https://t.me/{url_str}"

async def check_user_subscriptions(user_id: int) -> bool:
    channels = await channels_col.find().to_list(length=100)
    if not channels: return True
    for ch in channels:
        ch_type, chat_id = ch.get('type', 'channel'), ch.get('chat_id')
        if ch_type in ['channel', 'group'] and chat_id:
            try:
                m = await bot.get_chat_member(chat_id=int(chat_id), user_id=user_id)
                if m.status in ['left', 'kicked']: return False
            except: pass
        elif ch_type == 'request':
            if not await join_requests_col.find_one({"user_id": user_id, "chat_id": chat_id}): return False
    return True

async def get_required_channels_keyboard(lang: str, contest_id: str = None):
    channels = await channels_col.find().to_list(length=100)
    buttons = [[InlineKeyboardButton(text=f"📣 {ch.get('title')}", url=fix_url(ch.get('url')))] for ch in channels if ch.get('url')]
    cb = f"check_contest_sub_{contest_id}" if contest_id else "check_main_sub"
    buttons.append([InlineKeyboardButton(text=TEXTS[lang]["check_sub_btn"], callback_data=cb)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==========================================
# CHAT JOIN REQUEST LISTENER
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

    if not await check_user_subscriptions(user_id):
        keyboard = await get_required_channels_keyboard(lang=lang, contest_id=contest_id)
        await message.answer(TEXTS[lang]['must_subscribe'], reply_markup=keyboard)
        return

    if contest_id:
        await process_join_contest(user_id, contest_id, message)
        return

    await message.answer(TEXTS[lang]['welcome'], reply_markup=get_main_keyboard(user_id, lang))

@dp.callback_query(F.data.startswith("choose_lang_"))
async def choose_lang_callback(call: CallbackQuery):
    new_lang = call.data.split("_")[-1]
    user = await users_col.find_one({"user_id": call.from_user.id})
    pending_id = user.get("pending_contest_id") if user else None
    
    await users_col.update_one(
        {"user_id": call.from_user.id},
        {"$set": {"lang": new_lang, "updated_at": datetime.now()}, "$unset": {"pending_contest_id": ""}},
        upsert=True
    )
    
    await call.message.delete()
    
    if not await check_user_subscriptions(call.from_user.id):
        keyboard = await get_required_channels_keyboard(lang=new_lang, contest_id=pending_id)
        await call.message.answer(TEXTS[new_lang]['must_subscribe'], reply_markup=keyboard)
        return

    if pending_id:
        await process_join_contest(call.from_user.id, pending_id, call.message)
        return

    await call.message.answer(TEXTS[new_lang]['welcome'], reply_markup=get_main_keyboard(call.from_user.id, new_lang))

@dp.callback_query(F.data == "check_main_sub")
async def check_main_sub(call: CallbackQuery):
    if not await check_user_subscriptions(call.from_user.id):
        await call.answer("Barcha kanallarga a'zo bo'ling! ❌", show_alert=True)
        return
    lang = await get_user_lang(call.from_user.id) or 'uz'
    await call.message.delete()
    await call.message.answer(TEXTS[lang]['welcome'], reply_markup=get_main_keyboard(call.from_user.id, lang))

@dp.callback_query(F.data.startswith("check_contest_sub_"))
async def check_contest_sub(call: CallbackQuery):
    if not await check_user_subscriptions(call.from_user.id):
        await call.answer("Barcha kanallarga a'zo bo'ling! ❌", show_alert=True)
        return
    cid = call.data.replace("check_contest_sub_", "")
    await call.message.delete()
    await process_join_contest(call.from_user.id, cid, call.message)

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

@dp.message(F.text.in_(ALL_ADMIN_STAT_BTNS) | F.text.contains("STATISTIKASI") | F.text.contains("СТАТИСТИКА") | F.text.contains("STATS"))
async def show_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    u, c = await users_col.count_documents({}), await contests_col.count_documents({})
    await message.answer(f"📊 <b>Bot Statistikasi:</b>\n\n👤 Jami foydalanuvchilar: {u}\n🛒 O'tkazilgan konkurslar: {c}", parse_mode="HTML")

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
    if ch_type == 'channel': await call.message.edit_text(t['ask_channel_link'], parse_mode="HTML")
    elif ch_type == 'group': await call.message.edit_text(t['ask_group_link'], parse_mode="HTML")
    else: await call.message.edit_text(t['ask_request_link'], parse_mode="HTML")
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
            
        await channels_col.insert_one({"type": ch_type, "chat_id": chat_id, "channel_id": chat_id, "title": title, "url": link, "created_at": datetime.now()})
        await message.answer(t['channel_added'])
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}\nBot admin ekanligiga ishonch hosil qiling!")
    await state.clear()

@dp.callback_query(F.data == "sub_del_menu")
async def show_del_channels(call: CallbackQuery):
    channels = await channels_col.find().to_list(length=100)
    if not channels:
        await call.message.edit_text("Hali obuna qo'shilmagan.")
        return
    buttons = [[InlineKeyboardButton(text=f"🗑 {ch.get('title', 'Kanal')}", callback_data=f"del_ch_{ch['_id']}")] for ch in channels]
    await call.message.edit_text("Olib tashlash uchun tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("del_ch_"))
async def confirm_del_channel(call: CallbackQuery):
    await channels_col.delete_one({"_id": ObjectId(call.data.replace("del_ch_", ""))})
    await call.message.edit_text("🗑 Olib tashlandi!")

# ==========================================
# ADMIN: KONKURS YARATISH (BOSHQA VA AKKAUNTLI - FORMAT BILAN)
# ==========================================
@dp.message(F.text.in_(ALL_ADMIN_CREATE_BTNS) | F.text.contains("KONKURS YARATISH") | F.text.contains("СОЗДАТЬ КОНКУРС") | F.text.contains("CREATE CONTEST"))
async def admin_create_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    lang = await get_user_lang(message.from_user.id) or 'uz'
    t = TEXTS[lang]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t['btn_type_account'], callback_data="ctype_account")],
        [InlineKeyboardButton(text=t['btn_type_other'], callback_data="ctype_other")]
    ])
    await message.answer(t['select_contest_type'], reply_markup=kb)
    await state.set_state(AdminCreateContest.waiting_contest_type)

@dp.callback_query(F.data.startswith("ctype_"), AdminCreateContest.waiting_contest_type)
async def process_contest_type(call: CallbackQuery, state: FSMContext):
    ctype = call.data.replace("ctype_", "")
    await state.update_data(ctype=ctype)
    lang = await get_user_lang(call.from_user.id) or 'uz'
    t = TEXTS[lang]

    if ctype == 'other':
        await call.message.edit_text(t['ask_custom_prizes'])
        await state.set_state(AdminCreateContest.waiting_custom_prizes)
    else:
        await call.message.edit_text(t['ask_prizes_count'])
        await state.set_state(AdminCreateContest.waiting_prizes_count)

@dp.message(AdminCreateContest.waiting_custom_prizes)
async def process_custom_prizes(message: types.Message, state: FSMContext):
    await state.update_data(custom_prizes=message.text.strip())
    lang = await get_user_lang(message.from_user.id) or 'uz'
    await message.answer(TEXTS[lang]['ask_winners_count'])
    await state.set_state(AdminCreateContest.waiting_winners_count)

@dp.message(AdminCreateContest.waiting_winners_count)
async def process_winners_count(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    await state.update_data(winners_count=int(message.text), p_count=int(message.text))
    lang = await get_user_lang(message.from_user.id) or 'uz'
    await message.answer(TEXTS[lang]['ask_max_users'])
    await state.set_state(AdminCreateContest.waiting_max_users)

@dp.message(AdminCreateContest.waiting_prizes_count)
async def process_prizes_count(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    await state.update_data(p_count=int(message.text), winners_count=int(message.text))
    lang = await get_user_lang(message.from_user.id) or 'uz'
    await message.answer(TEXTS[lang]['ask_max_users'])
    await state.set_state(AdminCreateContest.waiting_max_users)

@dp.message(AdminCreateContest.waiting_max_users)
async def process_max_users(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    await state.update_data(max_users=int(message.text))
    data = await state.get_data()
    
    if data.get('ctype') == 'other':
        await ask_channel_selection(message, state)
    else:
        lang = await get_user_lang(message.from_user.id) or 'uz'
        await message.answer(TEXTS[lang]['ask_accounts'], parse_mode="HTML")
        await state.set_state(AdminCreateContest.waiting_accounts)

@dp.message(AdminCreateContest.waiting_accounts)
async def process_accounts(message: types.Message, state: FSMContext):
    data = await state.get_data()
    accs = [line.strip() for line in message.text.split("\n") if line.strip()]
    if len(accs) < data['p_count']:
        lang = await get_user_lang(message.from_user.id) or 'uz'
        await message.answer(TEXTS[lang]['accounts_mismatch'].format(prizes_count=data['p_count']))
        return
    await state.update_data(accounts=accs)
    await ask_channel_selection(message, state)

async def ask_channel_selection(message: types.Message, state: FSMContext):
    channels = await channels_col.find({"type": "channel"}).to_list(length=100)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=ch.get('title'), callback_data=f"tchan_{ch.get('chat_id')}")] for ch in channels])
    await message.answer("Konkurs qilinadigan kanalni tanlang:", reply_markup=kb)
    await state.set_state(AdminCreateContest.waiting_target_channel)

@dp.callback_query(F.data.startswith("tchan_"), AdminCreateContest.waiting_target_channel)
async def publish_contest(call: CallbackQuery, state: FSMContext):
    chid = int(call.data.replace("tchan_", ""))
    d = await state.get_data()
    
    ctype = d.get('ctype', 'account')
    p_count = d['p_count']
    max_users = d['max_users']
    accounts = d.get('accounts', [])
    custom_prizes = d.get('custom_prizes', '')

    if ctype == 'other':
        prizes_text = custom_prizes
    else:
        prizes_text = f"{p_count}ta akkaunt"

    res = await contests_col.insert_one({
        "ctype": ctype,
        "p_count": p_count,
        "max_users": max_users,
        "curr": 0,
        "status": "active",
        "chid": chid,
        "accounts": accounts,
        "custom_prizes": custom_prizes,
        "prizes_text": prizes_text,
        "parts": [],
        "at": datetime.now()
    })
    cid = str(res.inserted_id)
    b = await bot.get_me()

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="GOO 🎁", url=f"https://t.me/{b.username}?start=contest_{cid}")]])
    
    uz_text = TEXTS['uz']['channel_msg_uz'].format(prizes_text=prizes_text, current=0, max_users=max_users)
    en_text = TEXTS['en']['channel_msg_en'].format(prizes_text=prizes_text, current=0, max_users=max_users)
    full_msg = f"{uz_text}\n\n<i>{en_text}</i>"

    msg = await bot.send_message(chat_id=chid, text=full_msg, parse_mode="HTML", reply_markup=kb)
    await contests_col.update_one({"_id": res.inserted_id}, {"$set": {"msgid": msg.message_id}})
    await call.message.edit_text("✅ Konkurs kanalga muvaffaqiyatli joylandi!")
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

    if user_id in contest['participants']: # Xavfsizlik uchun tekshiruv
        pass

    if user_id in contest.get('parts', []):
        await message.answer(t['already_joined'], reply_markup=get_main_keyboard(user_id, lang))
        return

    await contests_col.update_one(
        {"_id": contest_obj_id},
        {"$push": {"parts": user_id}, "$inc": {"curr": 1}}
    )
    
    updated_contest = await contests_col.find_one({"_id": contest_obj_id})
    curr = updated_contest['curr']
    max_u = updated_contest['max_users']
    ch_id = updated_contest['chid']
    ch_msg_id = updated_contest.get('msgid')

    await message.answer(t['joined_success'], reply_markup=get_main_keyboard(user_id, lang))

    try:
        b = await bot.get_me()
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="GOO 🎁", url=f"https://t.me/{b.username}?start=contest_{contest_id_str}")]])
        prizes_text = updated_contest['prizes_text']
        uz_text = TEXTS['uz']['channel_msg_uz'].format(prizes_text=prizes_text, current=curr, max_users=max_u)
        en_text = TEXTS['en']['channel_msg_en'].format(prizes_text=prizes_text, current=curr, max_users=max_u)
        full_msg = f"{uz_text}\n\n<i>{en_text}</i>"
        
        if ch_msg_id:
            await bot.edit_message_text(chat_id=ch_id, message_id=ch_msg_id, text=full_msg, parse_mode="HTML", reply_markup=kb)
    except Exception:
        pass

    if curr >= max_u:
        await finish_contest(contest_obj_id)

async def finish_contest(contest_obj_id: ObjectId):
    contest = await contests_col.find_one({"_id": contest_obj_id})
    if not contest or contest['status'] != 'active':
        return

    await contests_col.update_one({"_id": contest_obj_id}, {"$set": {"status": "finished"}})
    
    parts = contest.get('parts', [])
    accounts = contest.get('accounts', [])
    p_count = contest['p_count']
    channel_id = contest['chid']
    ch_msg_id = contest.get('msgid')

    winners_count = min(len(parts), p_count)
    winners = random.sample(parts, winners_count) if parts else []

    winners_text = ""
    medals = ["1️⃣ OʻRIN🥇", "2️⃣ OʻRIN🥈", "3️⃣ OʻRIN🥉", "4️⃣ OʻRIN🏆", "5️⃣ OʻRIN🏆", "6️⃣ OʻRIN🏆", "7️⃣ OʻRIN🏆", "8️⃣ OʻRIN🏆", "9️⃣ OʻRIN🏆", "🔟 OʻRIN🏆"]

    for idx, winner_id in enumerate(winners):
        acc = accounts[idx] if idx < len(accounts) else f"Sovrin #{idx+1}"
        if contest.get('ctype') == 'account':
            await prizes_col.insert_one({
                "user_id": winner_id,
                "contest_id": str(contest_obj_id),
                "account": acc,
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
            if contest.get('ctype') == 'account':
                await bot.send_message(winner_id, TEXTS[u_lang]['won_notify'].format(account=acc), parse_mode="HTML")
            else:
                await bot.send_message(winner_id, f"🎉 TASHAKKURLAR! Siz konkursda g'olib bo'ldingiz!\n\nSovriningiz:\n{contest['custom_prizes']}")
        except Exception:
            pass

    final_text = TEXTS['uz']['contest_finished_channel'].format(winners_text=winners_text)
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
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot 100% to'liq, barcha funksiyalar va akkaunt formatlari bilan ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
