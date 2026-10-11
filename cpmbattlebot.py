import asyncio
import logging
import os
import random
import threading
from datetime import datetime, timezone
from html import escape

from flask import Flask
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,
    InlineKeyboardButton, CallbackQuery, ChatJoinRequest
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8734592942:AAFeKV1VP5F6hCxM4cIuQZUOYvD3298yOPI")
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://cpmcpmbattle_db_user:lKQN2ePocUCIM9zi@cluster0.brsfu0p.mongodb.net/?appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "konkurs_bot")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6968399046."))
PORT = int(os.getenv("PORT", "8080"))

if BOT_TOKEN == "BOT_TOKENINGIZNI_SHUYERGA_YOZING":
    raise RuntimeError("Set BOT_TOKEN in Render Environment Variables")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("contest-bot")

app = Flask(__name__)
@app.get("/")
def health():
    return "Bot process is running", 200

def run_web():
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)

mongo = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=10000)
db = mongo[DB_NAME]
users = db.users
contests = db.contests
channels = db.channels
join_requests = db.join_requests
prizes = db.prizes

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

TEXTS = {
    "uz": {
        "choose": "Tilni tanlang 🇺🇿 / 🇺🇸 / 🇷🇺", "welcome": "Xush kelibsiz! Kerakli bo'limni tanlang:",
        "prizes_btn": "| MEN YUTGAN SOVRINLAR 🛒|", "lang_btn": "| TIL ALMASHTIRISH 🌐 |",
        "create_btn": "| KONKURS YARATISH 🛒 |", "stats_btn": "| BOT STATISTIKASI📊 |",
        "subs_btn": "| MAJBURIY OBUNA ULASH 📣 |", "select_type": "Qaysi turdagi konkurs qilasiz tanlang 🌟",
        "account": "👉🏻 AKKAUNTLI", "other": "👉🏻 BOSHQA",
        "ask_prizes": "Nechta akkaunt qoʻyamiz? (Faqat son)", "ask_accounts": "Akkauntlarni har birini yangi qatordan yuboring:\n<code>01 | email | parol | OK</code>",
        "ask_custom": "Konkursga nima yutuqlar qoʻyiladi yozing🎁\nMasalan:\n1🥇- 30K COIN\n2🥈- 500K COIN\n3🥉- CHANGE ID",
        "ask_winners": "Nechta odam gʻolib boʻladi yozing ⚡ (Faqat son)", "ask_limit": "Nechta odam qatnasha oladi yozing 🌟 (Faqat son)",
        "pick_channel": "Konkurs qilinadigan kanalni tanlang:", "started": "Konkurs boshlandi 📣\n\nYutuqlar🎁: {prizes}\nTugashi: {current}/{limit}\n\nQatnashish uchun pastdagi tugmani bosing!",
        "started_en": "The contest has started 📣\n\nPrizes 🎁: {prizes}\nEnds: {current}/{limit}\n\nClick the button GOO 👇",
        "goo": "GOO 🎁", "subscribe": "Davom etish uchun quyidagi kanallarga a'zo bo'ling:",
        "check": "✅ Tekshirish", "joined": "Siz muvaffaqiyatli qatnashdingiz✅", "already": "Siz allaqachon qatnashyapsiz!",
        "finished_uz": "🏁 <b>KOʻNKURS YAKUNLANDI</b>\n\n{winners}",
        "finished_en": "🏁 <b>CONTEST FINISHED</b>\n\n{winners}",
        "won_account": "🎉 Tabriklaymiz! Siz yutdingiz:\n<code>{prize}</code>\n\n✨Yutuqni olish uchun\n@cpm_java ga yozing 🎁",
        "won_other": "🎉 Tabriklaymiz! Siz yutdingiz:\n{prize}\n\n✨Yutuqni olish uchun\n@cpm_java ga yozing 🎁",
        "no_prizes": "Siz hali sovrin yutmadingiz.",
        "my_prizes": "🛒 Siz yutgan sovrinlar:\n", "channels_menu": "Majburiy obuna boshqaruvi:",
        "add": "➕ Majburiy obuna qoʻshish", "remove": "➖ Majburiy obunani olib tashlash",
        "choose_sub": "Turini tanlang:", "channel": "ODDIY KANAL📣", "group": "CHAT GURUH ✉️", "request": "ZAYAFKA KANAL📦",
        "ask_channel": "Kanal username yoki linkini yuboring (masalan @kanal yoki https://t.me/kanal). Bot admin bo'lishi kerak.",
        "ask_group": "Guruh username yoki linkini yuboring. Bot guruhda admin bo'lishi kerak.",
        "ask_request": "Join Request kanal linkini yuboring. Bot kanalda admin bo'lishi kerak.",
        "added": "✅ Obuna qoʻshildi", "removed": "🗑 Obuna olib tashlandi", "none": "Obunalar topilmadi.",
        "bad_number": "Faqat musbat son yuboring.", "count_mismatch": "{n} ta akkaunt yuboring.",
        "stats": "📊 Foydalanuvchilar: {users}\nKonkurslar: {contests}"
    },
    "ru": {
        "choose": "Выберите язык 🇺🇿 / 🇺🇸 / 🇷🇺", "welcome": "Добро пожаловать! Выберите раздел:",
        "prizes_btn": "| МОИ ПРИЗЫ 🛒|", "lang_btn": "| СМЕНА ЯЗЫКА 🌐 |", "create_btn": "| СОЗДАТЬ КОНКУРС 🛒 |",
        "stats_btn": "| СТАТИСТИКА 📊 |", "subs_btn": "| ОБЯЗАТЕЛЬНАЯ ПОДПИСКА 📣 |", "select_type": "Выберите тип конкурса 🌟",
        "account": "👉🏻 АККАУНТЫ", "other": "👉🏻 ДРУГОЕ", "ask_prizes": "Сколько аккаунтов разыгрываем? (Число)",
        "ask_accounts": "Отправьте аккаунты по одному в строке:\n<code>01 | email | пароль | OK</code>", "ask_custom": "Напишите призы конкурса🎁",
        "ask_winners": "Сколько будет победителей? (Число)", "ask_limit": "Сколько участников может быть? (Число)",
        "pick_channel": "Выберите канал для конкурса:", "started": "Конкурс начался 📣\n\nПризы🎁: {prizes}\nЗавершение: {current}/{limit}\n\nНажмите кнопку ниже!",
        "started_en": "The contest has started 📣\n\nPrizes 🎁: {prizes}\nEnds: {current}/{limit}\n\nClick the button GOO 👇", "goo": "GOO 🎁",
        "subscribe": "Подпишитесь на каналы, чтобы продолжить:", "check": "✅ Проверить", "joined": "Вы успешно участвуете✅",
        "already": "Вы уже участвуете!",
        "finished_uz": "🏁 <b>КОНКУРС ЗАВЕРШЕН</b>\n\n{winners}",
        "finished_en": "🏁 <b>CONTEST FINISHED</b>\n\n{winners}",
        "won_account": "🎉 Поздравляем! Ваш выигрыш:\n<code>{prize}</code>\n\n✨Для получения приза\nнапишите @cpm_java 🎁",
        "won_other": "🎉 Поздравляем! Ваш выигрыш:\n{prize}\n\n✨Для получения приза\nнапишите @cpm_java 🎁",
        "no_prizes": "Вы пока не выиграли.",
        "my_prizes": "🛒 Ваши призы:\n", "channels_menu": "Управление подписками:", "add": "➕ Добавить подписку",
        "remove": "➖ Удалить подписку", "choose_sub": "Выберите тип:", "channel": "КАНАЛ📣", "group": "ГРУППА ✉️", "request": "ЗАЯВКА📦",
        "ask_channel": "Отправьте username или ссылку канала. Бот должен быть администратором.", "ask_group": "Отправьте username или ссылку группы. Бот должен быть администратором.",
        "ask_request": "Отправьте ссылку Join Request. Бот должен быть администратором.", "added": "✅ Добавлено", "removed": "🗑 Удалено", "none": "Подписок нет.",
        "bad_number": "Введите положительное число.", "count_mismatch": "Отправьте {n} аккаунтов.", "stats": "📊 Пользователи: {users}\nКонкурсы: {contests}"
    },
    "en": {
        "choose": "Choose a language 🇺🇿 / 🇺🇸 / 🇷🇺", "welcome": "Welcome! Choose an option:",
        "prizes_btn": "| MY PRIZES 🛒|", "lang_btn": "| CHANGE LANGUAGE 🌐 |", "create_btn": "| CREATE CONTEST 🛒 |",
        "stats_btn": "| BOT STATS 📊 |", "subs_btn": "| MANDATORY SUBS 📣 |", "select_type": "Select contest type 🌟",
        "account": "👉🏻 ACCOUNTS", "other": "👉🏻 OTHER", "ask_prizes": "How many accounts? (Number)",
        "ask_accounts": "Send one account per line:\n<code>01 | email | password | OK</code>", "ask_custom": "Write the contest prizes 🎁",
        "ask_winners": "How many winners? (Number)", "ask_limit": "Maximum participants? (Number)", "pick_channel": "Choose contest channel:",
        "started": "Contest started 📣\n\nPrizes 🎁: {prizes}\nEnds: {current}/{limit}\n\nClick the button below!",
        "started_en": "The contest has started 📣\n\nPrizes 🎁: {prizes}\nEnds: {current}/{limit}\n\nClick the button GOO 👇", "goo": "GOO 🎁",
        "subscribe": "Subscribe to these channels to continue:", "check": "✅ Check", "joined": "You joined successfully✅", "already": "You already joined!",
        "finished_uz": "🏁 <b>CONTEST FINISHED</b>\n\n{winners}",
        "finished_en": "🏁 <b>CONTEST FINISHED</b>\n\n{winners}",
        "won_account": "🎉 Congratulations! Your prize:\n<code>{prize}</code>\n\n✨To claim your prize,\nmessage @cpm_java 🎁",
        "won_other": "🎉 Congratulations! Your prize:\n{prize}\n\n✨To claim your prize,\nmessage @cpm_java 🎁",
        "no_prizes": "No prizes won yet.",
        "my_prizes": "🛒 Your prizes:\n",
        "channels_menu": "Subscription management:", "add": "➕ Add subscription", "remove": "➖ Remove subscription", "choose_sub": "Choose type:",
        "channel": "CHANNEL📣", "group": "GROUP ✉️", "request": "JOIN REQUEST📦", "ask_channel": "Send channel username/link. Bot must be admin.",
        "ask_group": "Send group username/link. Bot must be admin.", "ask_request": "Send Join Request invite link. Bot must be admin.",
        "added": "✅ Added", "removed": "🗑 Removed", "none": "No subscriptions.", "bad_number": "Enter a positive number.",
        "count_mismatch": "Send {n} accounts.", "stats": "📊 Users: {users}\nContests: {contests}"
    }
}

class ContestFlow(StatesGroup):
    kind = State(); custom_prizes = State(); winners = State(); account_count = State(); limit = State(); accounts = State(); channel = State()
class SubFlow(StatesGroup):
    link = State()

LANG_BUTTONS = [t["lang_btn"] for t in TEXTS.values()]
PRIZE_BUTTONS = [t["prizes_btn"] for t in TEXTS.values()]
CREATE_BUTTONS = [t["create_btn"] for t in TEXTS.values()]
STAT_BUTTONS = [t["stats_btn"] for t in TEXTS.values()]
SUB_BUTTONS = [t["subs_btn"] for t in TEXTS.values()]

async def get_lang(uid):
    doc = await users.find_one({"user_id": uid})
    lang = doc.get("lang") if doc else None
    return lang if lang in TEXTS else None

def main_keyboard(uid, lang):
    t = TEXTS[lang]
    rows = [[KeyboardButton(text=t["prizes_btn"])], [KeyboardButton(text=t["lang_btn"])]]
    if uid == ADMIN_ID:
        rows += [[KeyboardButton(text=t["create_btn"])], [KeyboardButton(text=t["stats_btn"]), KeyboardButton(text=t["subs_btn"])]]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"), InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"), InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]])

def normalize_url(value):
    value = (value or "").strip()
    if value.startswith(("https://", "http://")): return value
    if value.startswith("@"): return "https://t.me/" + value[1:]
    if value.startswith("t.me/"): return "https://" + value
    return "https://t.me/" + value

async def subscription_keyboard(lang, contest_id=None):
    docs = await channels.find().to_list(100)
    rows = []
    for ch in docs:
        if ch.get("url"):
            rows.append([InlineKeyboardButton(text="📣 " + ch.get("title", "Channel"), url=normalize_url(ch["url"]))])
    cb = "checksub:" + (contest_id or "home")
    rows.append([InlineKeyboardButton(text=TEXTS[lang]["check"], callback_data=cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def check_subscriptions(uid):
    for ch in await channels.find().to_list(200):
        kind = ch.get("type", "channel")
        chat_id = ch.get("chat_id") or ch.get("channel_id")
        if kind in ("channel", "group"):
            if not chat_id: return False
            try:
                member = await bot.get_chat_member(int(chat_id), uid)
                if member.status in ("left", "kicked", "restricted"): return False
            except Exception:
                return False
        elif kind == "request":
            if not chat_id or not await join_requests.find_one({"user_id": uid, "chat_id": int(chat_id)}): return False
    return True

async def send_home(message, uid, lang):
    await message.answer(TEXTS[lang]["welcome"], reply_markup=main_keyboard(uid, lang))

@dp.message(CommandStart())
async def start(message: types.Message):
    uid = message.from_user.id
    args = (message.text or "").split(maxsplit=1)
    contest_id = args[1][8:] if len(args) > 1 and args[1].startswith("contest_") else None
    await users.update_one({"user_id": uid}, {"$set": {"username": message.from_user.username, "first_name": message.from_user.first_name, "updated_at": datetime.now(timezone.utc)}}, upsert=True)
    lang = await get_lang(uid)
    if not lang:
        await users.update_one({"user_id": uid}, {"$set": {"pending_contest_id": contest_id}}, upsert=True)
        await message.answer(TEXTS["uz"]["choose"], reply_markup=language_keyboard())
        return
    if not await check_subscriptions(uid):
        await message.answer(TEXTS[lang]["subscribe"], reply_markup=await subscription_keyboard(lang, contest_id))
        return
    if contest_id:
        await join_contest(uid, contest_id, message)
    else:
        await send_home(message, uid, lang)

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(call: CallbackQuery):
    lang = call.data[5:]
    if lang not in TEXTS:
        await call.answer("Invalid language", show_alert=True); return
    old = await users.find_one({"user_id": call.from_user.id})
    pending = old.get("pending_contest_id") if old else None
    await users.update_one({"user_id": call.from_user.id}, {"$set": {"lang": lang, "updated_at": datetime.now(timezone.utc)}, "$unset": {"pending_contest_id": ""}}, upsert=True)
    await call.answer()
    try: await call.message.delete()
    except Exception: pass
    if not await check_subscriptions(call.from_user.id):
        await call.message.answer(TEXTS[lang]["subscribe"], reply_markup=await subscription_keyboard(lang, pending))
    elif pending:
        await join_contest(call.from_user.id, pending, call.message)
    else:
        await send_home(call.message, call.from_user.id, lang)

@dp.callback_query(F.data.startswith("checksub:"))
async def check_sub_callback(call: CallbackQuery):
    lang = await get_lang(call.from_user.id) or "uz"
    if not await check_subscriptions(call.from_user.id):
        await call.answer("Avval barcha kanallarga obuna bo'ling / Subscribe first", show_alert=True); return
    payload = call.data.split(":", 1)[1]
    try: await call.message.delete()
    except Exception: pass
    if payload != "home":
        await join_contest(call.from_user.id, payload, call.message)
    else:
        await send_home(call.message, call.from_user.id, lang)

@dp.message(F.text.in_(LANG_BUTTONS))
async def change_language(message: types.Message):
    await message.answer("Tilni tanlang 🇺🇿 / 🇺🇸 / 🇷🇺", reply_markup=language_keyboard())

@dp.message(F.text.in_(CREATE_BUTTONS))
async def create_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    lang = await get_lang(message.from_user.id) or "uz"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TEXTS[lang]["account"], callback_data="kind:account")], [InlineKeyboardButton(text=TEXTS[lang]["other"], callback_data="kind:other")]])
    await message.answer(TEXTS[lang]["select_type"], reply_markup=kb)
    await state.set_state(ContestFlow.kind)

@dp.callback_query(F.data.startswith("kind:"), ContestFlow.kind)
async def choose_kind(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":", 1)[1]
    await state.update_data(kind=kind, admin_lang=await get_lang(call.from_user.id) or "uz")
    t = TEXTS[(await get_lang(call.from_user.id)) or "uz"]
    if kind == "account":
        await call.message.edit_text(t["ask_prizes"]); await state.set_state(ContestFlow.account_count)
    else:
        await call.message.edit_text(t["ask_custom"]); await state.set_state(ContestFlow.custom_prizes)
    await call.answer()

@dp.message(ContestFlow.custom_prizes)
async def custom_prizes(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Yutuq matnini yuboring."); return
    winners = [line.strip() for line in text.splitlines() if line.strip()]
    await state.update_data(custom_prizes=text, prize_lines=winners)
    t = TEXTS[await get_lang(message.from_user.id) or "uz"]
    await message.answer(t["ask_winners"]); await state.set_state(ContestFlow.winners)

@dp.message(ContestFlow.winners)
async def winners_count(message: types.Message, state: FSMContext):
    if not (message.text or "").isdigit() or int(message.text) < 1:
        await message.answer(TEXTS[await get_lang(message.from_user.id) or "uz"]["bad_number"]); return
    await state.update_data(winners_count=int(message.text), prize_count=int(message.text))
    t = TEXTS[await get_lang(message.from_user.id) or "uz"]
    await message.answer(t["ask_limit"]); await state.set_state(ContestFlow.limit)

@dp.message(ContestFlow.account_count)
async def account_count(message: types.Message, state: FSMContext):
    if not (message.text or "").isdigit() or int(message.text) < 1:
        await message.answer(TEXTS[await get_lang(message.from_user.id) or "uz"]["bad_number"]); return
    await state.update_data(prize_count=int(message.text), winners_count=int(message.text))
    t = TEXTS[await get_lang(message.from_user.id) or "uz"]
    await message.answer(t["ask_limit"]); await state.set_state(ContestFlow.limit)

@dp.message(ContestFlow.limit)
async def participant_limit(message: types.Message, state: FSMContext):
    if not (message.text or "").isdigit() or int(message.text) < 1:
        await message.answer(TEXTS[await get_lang(message.from_user.id) or "uz"]["bad_number"]); return
    await state.update_data(max_users=int(message.text))
    data = await state.get_data()
    if data["kind"] == "account":
        await message.answer(TEXTS[await get_lang(message.from_user.id) or "uz"]["ask_accounts"], parse_mode="HTML")
        await state.set_state(ContestFlow.accounts)
    else:
        await choose_publish_channel(message, state)

@dp.message(ContestFlow.accounts)
async def account_lines(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lines = [line.strip() for line in (message.text or "").splitlines() if line.strip()]
    if len(lines) != data["prize_count"]:
        t = TEXTS[await get_lang(message.from_user.id) or "uz"]
        await message.answer(t["count_mismatch"].format(n=data["prize_count"])); return
    await state.update_data(accounts=lines)
    await choose_publish_channel(message, state)

async def choose_publish_channel(message, state):
    docs = await channels.find({"type": "channel"}).to_list(100)
    docs = [d for d in docs if d.get("chat_id") or d.get("channel_id")]
    if not docs:
        await message.answer("Avval ODDIY KANAL sifatida post chiqariladigan kanalni qo'shing. Bot kanalda admin bo'lsin.")
        await state.clear(); return
    rows = []
    for d in docs:
        cid = d.get("chat_id") or d.get("channel_id")
        rows.append([InlineKeyboardButton(text=d.get("title", "Kanal")[:60], callback_data=f"pub:{cid}")])
    await message.answer(TEXTS[await get_lang(message.from_user.id) or "uz"]["pick_channel"], reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await state.set_state(ContestFlow.channel)

@dp.callback_query(F.data.startswith("pub:"), ContestFlow.channel)
async def publish(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Admin only", show_alert=True); return
    data = await state.get_data()
    try: chat_id = int(call.data.split(":", 1)[1])
    except ValueError:
        await call.answer("Invalid channel", show_alert=True); return
    kind = data["kind"]
    if kind == "account":
        prize_lines = data["accounts"]
        prize_text = f"{len(prize_lines)}ta akkaunt"
    else:
        prize_lines = data["prize_lines"]
        prize_text = data["custom_prizes"]
    doc = {
        "kind": kind, "prize_count": len(prize_lines), "prize_lines": prize_lines,
        "prize_text": prize_text, "max_users": data["max_users"], "current": 0,
        "participants": [], "status": "active", "chat_id": chat_id,
        "lang": data.get("admin_lang", "uz"), "created_at": datetime.now(timezone.utc)
    }
    result = await contests.insert_one(doc)
    cid = str(result.inserted_id)
    me = await bot.get_me()
    markup = contest_markup(me.username, cid)
    body = contest_post(doc, 0)
    try:
        sent = await bot.send_message(chat_id, body, parse_mode="HTML", reply_markup=markup)
        await contests.update_one({"_id": result.inserted_id}, {"$set": {"message_id": sent.message_id}})
        await call.message.edit_text("✅ Konkurs kanalga joylandi!")
    except Exception as exc:
        await contests.delete_one({"_id": result.inserted_id})
        await call.message.edit_text(f"❌ Postni yuborib bo'lmadi: {escape(str(exc))}", parse_mode="HTML")
    await call.answer(); await state.clear()

def contest_markup(username, cid):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="GOO 🎁", url=f"https://t.me/{username}?start=contest_{cid}")]])

def contest_post(c, current):
    prize = escape(c.get("prize_text", ""))
    uz = TEXTS["uz"]["started"].format(prizes=prize, current=current, limit=c["max_users"])
    en = TEXTS["en"]["started_en"].format(prizes=prize, current=current, limit=c["max_users"])
    return uz + "\n\n<blockquote><i>" + en + "</i></blockquote>"

async def join_contest(uid, cid_text, message):
    lang = await get_lang(uid) or "uz"
    try: oid = ObjectId(cid_text)
    except Exception:
        await message.answer("Konkurs havolasi noto'g'ri."); return
    if not await check_subscriptions(uid):
        await message.answer(TEXTS[lang]["subscribe"], reply_markup=await subscription_keyboard(lang, cid_text)); return
    result = await contests.update_one({"_id": oid, "status": "active", "participants": {"$ne": uid}, "$expr": {"$lt": ["$current", "$max_users"]}}, {"$addToSet": {"participants": uid}, "$inc": {"current": 1}})
    if result.modified_count == 0:
        c = await contests.find_one({"_id": oid})
        if not c or c.get("status") != "active":
            await message.answer("Bu konkurs yakunlangan yoki mavjud emas."); return
        if uid in c.get("participants", []):
            await message.answer(TEXTS[lang]["already"]); return
        await message.answer("Konkursda qatnashchilar soni to'lgan."); return
    c = await contests.find_one({"_id": oid})
    await users.update_one({"user_id": uid}, {"$set": {"username": getattr(message.from_user, "username", None), "first_name": getattr(message.from_user, "first_name", "")}}, upsert=True)
    await message.answer(TEXTS[lang]["joined"], reply_markup=main_keyboard(uid, lang))
    try:
        me = await bot.get_me()
        await bot.edit_message_text(chat_id=c["chat_id"], message_id=c["message_id"], text=contest_post(c, c["current"]), parse_mode="HTML", reply_markup=contest_markup(me.username, cid_text))
    except Exception:
        log.exception("Could not update contest post")
    if c["current"] >= c["max_users"]:
        await finish_contest(oid)

async def finish_contest(oid):
    claimed = await contests.update_one({"_id": oid, "status": "active", "$expr": {"$gte": ["$current", "$max_users"]}}, {"$set": {"status": "drawing"}})
    if claimed.modified_count == 0: return
    c = await contests.find_one({"_id": oid})
    participants = c.get("participants", [])
    prize_lines = c.get("prize_lines", [])
    count = min(len(participants), len(prize_lines))
    winners = random.sample(participants, count) if count else []
    rows = []
    medals = ["1️⃣ OʻRIN🥇", "2️⃣ OʻRIN🥈", "3️⃣ OʻRIN🥉"]
    for index, uid in enumerate(winners):
        user = await users.find_one({"user_id": uid}) or {}
        name = user.get("username")
        display = "@" + name if name else escape(user.get("first_name") or str(uid))
        label = medals[index] if index < len(medals) else f"{index+1}-OʻRIN🏆"
        rows.append(f"{label} - {display}")
        prize = prize_lines[index]
        u_lang = await get_lang(uid) or "uz"
        t = TEXTS[u_lang]
        if c["kind"] == "account":
            await prizes.insert_one({"user_id": uid, "contest_id": str(oid), "account": prize, "created_at": datetime.now(timezone.utc)})
            msg_body = t["won_account"].format(prize=escape(prize))
        else:
            msg_body = t["won_other"].format(prize=prize)
        try:
            await bot.send_message(uid, msg_body, parse_mode="HTML")
        except Exception:
            log.info("Could not DM winner %s", uid)
            
    winners_str = "\n".join(rows) if rows else "Gʻolib aniqlanmadi."
    uz_final = TEXTS["uz"]["finished_uz"].format(winners=winners_str)
    en_final = TEXTS["en"]["finished_en"].format(winners=winners_str)
    final = uz_final + "\n\n<blockquote><i>" + en_final + "</i></blockquote>"
    
    try:
        await bot.edit_message_text(chat_id=c["chat_id"], message_id=c["message_id"], text=final, parse_mode="HTML", reply_markup=None)
    except Exception:
        log.exception("Could not publish winner list")
    await contests.update_one({"_id": oid}, {"$set": {"status": "finished", "winners": winners}})

@dp.message(F.text.in_(PRIZE_BUTTONS))
async def show_prizes(message: types.Message):
    lang = await get_lang(message.from_user.id) or "uz"
    docs = await prizes.find({"user_id": message.from_user.id}).to_list(100)
    if not docs:
        await message.answer(TEXTS[lang]["no_prizes"]); return
    text = TEXTS[lang]["my_prizes"] + "\n".join(f"{i}. <code>{escape(p['account'])}</code>" for i, p in enumerate(docs, 1))
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text.in_(SUB_BUTTONS))
async def sub_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    lang = await get_lang(message.from_user.id) or "uz"; t = TEXTS[lang]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t["add"], callback_data="sub:add")], [InlineKeyboardButton(text=t["remove"], callback_data="sub:remove")]])
    await message.answer(t["channels_menu"], reply_markup=kb)

@dp.callback_query(F.data == "sub:add")
async def sub_add_menu(call: CallbackQuery):
    lang = await get_lang(call.from_user.id) or "uz"; t = TEXTS[lang]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t["channel"], callback_data="subtype:channel")], [InlineKeyboardButton(text=t["group"], callback_data="subtype:group")], [InlineKeyboardButton(text=t["request"], callback_data="subtype:request")]])
    await call.message.edit_text(t["choose_sub"], reply_markup=kb); await call.answer()

@dp.callback_query(F.data.startswith("subtype:"))
async def sub_type(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID: await call.answer("Admin only", show_alert=True); return
    kind = call.data.split(":")[1]; lang = await get_lang(call.from_user.id) or "uz"
    prompt = TEXTS[lang][{"channel":"ask_channel", "group":"ask_group", "request":"ask_request"}[kind]]
    await state.update_data(sub_type=kind); await state.set_state(SubFlow.link)
    await call.message.edit_text(prompt); await call.answer()

@dp.message(SubFlow.link)
async def save_sub(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    data = await state.get_data(); kind = data["sub_type"]; raw = (message.text or "").strip()
    if not raw: await message.answer("Link yuboring."); return
    try:
        if kind in ("channel", "group"):
            identifier = raw
            if raw.startswith("https://t.me/"):
                username = raw.rstrip("/").split("/")[-1]
                if username.startswith("+") or username.startswith("joinchat"):
                    raise ValueError("Private invite link orqali chat ID aniqlab bo'lmaydi. Public @username yoki chat ID kerak.")
                identifier = "@" + username
            chat = await bot.get_chat(identifier)
            chat_id, title = chat.id, chat.title or raw
            url = normalize_url(raw) if raw.startswith("@") or "t.me/" in raw else f"https://t.me/{raw.lstrip('@')}"
        else:
            if "|" not in raw:
                raise ValueError("Zayafka kanali uchun CHAT_ID | invite-link ko'rinishida yuboring.")
            left, url = [part.strip() for part in raw.split("|", 1)]
            chat = await bot.get_chat(left)
            chat_id, title = chat.id, chat.title or left
            url = normalize_url(url)
        await channels.insert_one({"type": kind, "chat_id": chat_id, "title": title, "url": url, "created_at": datetime.now(timezone.utc)})
        await message.answer(TEXTS[await get_lang(message.from_user.id) or "uz"]["added"])
    except Exception as exc:
        await message.answer("Kanalni qo'shib bo'lmadi: " + str(exc))
        return
    await state.clear()

@dp.callback_query(F.data == "sub:remove")
async def sub_remove_list(call: CallbackQuery):
    docs = await channels.find().to_list(100)
    if not docs:
        await call.message.edit_text(TEXTS[await get_lang(call.from_user.id) or "uz"]["none"]); await call.answer(); return
    rows = [[InlineKeyboardButton(text="🗑 " + d.get("title", "channel")[:50], callback_data=f"rm:{d['_id']}")] for d in docs]
    await call.message.edit_text("Olib tashlash uchun tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)); await call.answer()

@dp.callback_query(F.data.startswith("rm:"))
async def remove_sub(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID: await call.answer("Admin only", show_alert=True); return
    try: oid = ObjectId(call.data.split(":", 1)[1])
    except Exception: await call.answer("Invalid", show_alert=True); return
    await channels.delete_one({"_id": oid})
    await call.message.edit_text(TEXTS[await get_lang(call.from_user.id) or "uz"]["removed"]); await call.answer()

@dp.chat_join_request()
async def on_join_request(update: ChatJoinRequest):
    await join_requests.update_one({"user_id": update.from_user.id, "chat_id": update.chat.id}, {"$set": {"user_id": update.from_user.id, "chat_id": update.chat.id, "created_at": datetime.now(timezone.utc)}}, upsert=True)

@dp.message(F.text.in_(STAT_BUTTONS))
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    lang = await get_lang(message.from_user.id) ro "uz"
    await message.answer(TEXTS[lang]["stats"].format(users=await users.count_documents({}), contests=await contests.count_documents({})))

async def main():
    threading.Thread(target=run_web, daemon=True).start()
    await mongo.admin.command("ping")
    await bot.delete_webhook(drop_pending_updates=True)
    log.info("MongoDB connected; starting Telegram polling")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        log.exception("Bot stopped, restarting")
        raise
