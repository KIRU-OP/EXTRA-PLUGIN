"""
╔══════════════════════════════════════════════════════════════╗
║           🧠  ULTIMATE AI QUIZ BOT  🧠                       ║
║  All 24 OpenTDB Subjects + AI Custom Questions               ║
║  Leaderboard | Achievements | Daily Challenge | Streaks      ║
╚══════════════════════════════════════════════════════════════╝
"""

import html
import json
import random
import time
import asyncio
import aiohttp
from datetime import date

from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
)

from VIPMUSIC import app

# ══════════════════════════════════════════════════════════════
#  STATE
# ══════════════════════════════════════════════════════════════
last_cmd_time: dict = {}
user_data: dict = {}
active_questions: dict = {}   # msg_id → question info
daily_done: dict = {}

COOLDOWN = 7

# ══════════════════════════════════════════════════════════════
#  ALL 24 OPENTDB CATEGORIES + AI
# ══════════════════════════════════════════════════════════════
CATEGORIES = {
    "🎭 General Knowledge":    9,
    "📚 Books":               10,
    "🎬 Film":                11,
    "🎵 Music":               12,
    "🎭 Musicals & Theatre":  13,
    "📺 Television":          14,
    "🎮 Video Games":         15,
    "🎲 Board Games":         16,
    "🔬 Science & Nature":    17,
    "💻 Computers":           18,
    "🧮 Mathematics":         19,
    "🔭 Mythology":           20,
    "⚽ Sports":              21,
    "🌍 Geography":           22,
    "📜 History":             23,
    "🏛️ Politics":            24,
    "🎨 Art":                 25,
    "⭐ Celebrities":         26,
    "🐾 Animals":             27,
    "🚗 Vehicles":            28,
    "📖 Comics":              29,
    "🔧 Gadgets":             30,
    "🍜 Anime & Manga":       31,
    "🃏 Cartoon & Animation": 32,
    "🤖 AI Custom (Claude)":  "ai",
}

DIFFICULTY = {
    "easy":   {"label": "🟢 Easy",   "pts": 10,  "time": 30},
    "medium": {"label": "🟡 Medium", "pts": 25,  "time": 22},
    "hard":   {"label": "🔴 Hard",   "pts": 50,  "time": 15},
    "expert": {"label": "💀 Expert", "pts": 100, "time": 10},
}

ACHIEVEMENTS = {
    "first_blood": ("🩸 First Blood",  "Pehla sahi jawab!",         lambda s: s["correct"] >= 1),
    "streak_3":    ("🔥 On Fire",      "3 streak!",                  lambda s: s["streak"] >= 3),
    "streak_5":    ("⚡ Lightning",    "5 streak!",                  lambda s: s["streak"] >= 5),
    "streak_10":   ("💫 Unstoppable",  "10 streak!",                 lambda s: s["streak"] >= 10),
    "score_500":   ("🥉 Bronze",       "500 points!",                lambda s: s["score"] >= 500),
    "score_1000":  ("🥈 Silver",       "1000 points!",               lambda s: s["score"] >= 1000),
    "score_5000":  ("🥇 Gold",         "5000 points!",               lambda s: s["score"] >= 5000),
    "century":     ("💯 Century",      "100 sahi jawab!",            lambda s: s["correct"] >= 100),
    "veteran":     ("🎖️ Veteran",      "500 questions attempt!",     lambda s: s["total"] >= 500),
    "explorer":    ("🗺️ Explorer",     "10 alag subjects try kiye!", lambda s: len(s.get("cats_tried", set())) >= 10),
    "daily_hero":  ("📅 Daily Hero",   "Daily challenge complete!",  lambda s: s.get("daily_count", 0) >= 1),
}

# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════
def get_user(uid: int) -> dict:
    if uid not in user_data:
        user_data[uid] = {
            "score": 0, "correct": 0, "total": 0,
            "streak": 0, "best_streak": 0,
            "achievements": set(),
            "cats_tried": set(),
            "daily_count": 0,
            "name": "Player",
        }
    return user_data[uid]


def cooldown_left(uid: int) -> float:
    return max(0.0, COOLDOWN - (time.time() - last_cmd_time.get(uid, 0)))


def accuracy(st: dict) -> int:
    return round(st["correct"] / st["total"] * 100) if st["total"] else 0


def bar(pct: int, w: int = 10) -> str:
    f = round(pct / 100 * w)
    return "█" * f + "░" * (w - f)


def streak_label(n: int) -> str:
    if n >= 10: return f"{n} 💫"
    if n >= 5:  return f"{n} ⚡"
    if n >= 3:  return f"{n} 🔥"
    return str(n)


def streak_mult(n: int) -> float:
    if n >= 10: return 3.0
    if n >= 5:  return 2.0
    if n >= 3:  return 1.5
    return 1.0


def rank_emoji(pos: int) -> str:
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(pos, f"#{pos}")


def check_achievements(uid: int, st: dict) -> list:
    new = []
    for key, (title, desc, cond) in ACHIEVEMENTS.items():
        if key not in st["achievements"]:
            try:
                if cond(st):
                    st["achievements"].add(key)
                    new.append(f"🏅 **Achievement Unlocked!**\n{title} — _{desc}_")
            except Exception:
                pass
    return new

# ══════════════════════════════════════════════════════════════
#  QUESTION FETCHERS
# ══════════════════════════════════════════════════════════════
async def fetch_opentdb(cat_id: int, diff: str) -> dict | None:
    api_diff = diff if diff != "expert" else "hard"
    url = f"https://opentdb.com/api.php?amount=1&category={cat_id}&difficulty={api_diff}&type=multiple"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                data = await r.json(content_type=None)
        if data.get("response_code") == 0 and data["results"]:
            return data["results"][0]
    except Exception:
        pass
    return None


async def fetch_ai_question(diff: str) -> dict | None:
    topics = [
        "Indian history", "space exploration", "human biology", "world geography",
        "famous inventions", "cricket", "Bollywood", "programming", "mythology",
        "economics", "chemistry", "famous leaders", "animals", "mathematics",
        "world cuisine", "music history", "sports records", "ancient civilizations",
    ]
    topic = random.choice(topics)
    prompt = (
        f"Create a {diff} difficulty multiple choice trivia question about {topic}. "
        f"Return ONLY valid JSON, no markdown, no extra text:\n"
        f'{{"question":"...","correct":"...","wrong":["...","...","..."]}}'
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                resp = await r.json()
        raw = resp["content"][0]["text"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        obj = json.loads(raw)
        return {
            "question": obj["question"],
            "correct_answer": obj["correct"],
            "incorrect_answers": obj["wrong"][:3],
            "category": "AI Generated",
            "difficulty": diff,
        }
    except Exception:
        return None

# ══════════════════════════════════════════════════════════════
#  KEYBOARDS
# ══════════════════════════════════════════════════════════════
def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Subject Choose", callback_data="qz_subjects_0"),
            InlineKeyboardButton("Random Quick",   callback_data="qz_random"),
        ],
        [
            InlineKeyboardButton("Daily Challenge", callback_data="qz_daily"),
            InlineKeyboardButton("Leaderboard",     callback_data="qz_lb"),
        ],
        [
            InlineKeyboardButton("Achievements",    callback_data="qz_ach"),
            InlineKeyboardButton("My Stats",        callback_data="qz_stats"),
        ],
    ])


def subjects_kb(page: int = 0) -> InlineKeyboardMarkup:
    items = list(CATEGORIES.items())
    per_page = 12
    start = page * per_page
    chunk = items[start:start + per_page]
    rows = []
    for i in range(0, len(chunk), 2):
        row = [InlineKeyboardButton(n, callback_data=f"qz_sub_{c}") for n, c in chunk[i:i+2]]
        rows.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("< Prev", callback_data=f"qz_subjects_{page-1}"))
    if start + per_page < len(items):
        nav.append(InlineKeyboardButton("Next >", callback_data=f"qz_subjects_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("Back", callback_data="qz_main")])
    return InlineKeyboardMarkup(rows)


def difficulty_kb(cat_id) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Easy (+10)",    callback_data=f"qz_diff_{cat_id}_easy"),
            InlineKeyboardButton("Medium (+25)",  callback_data=f"qz_diff_{cat_id}_medium"),
        ],
        [
            InlineKeyboardButton("Hard (+50)",    callback_data=f"qz_diff_{cat_id}_hard"),
            InlineKeyboardButton("Expert (+100)", callback_data=f"qz_diff_{cat_id}_expert"),
        ],
        [InlineKeyboardButton("Back", callback_data="qz_subjects_0")],
    ])


def answer_kb(msg_id: int, options: list, correct_idx: int) -> InlineKeyboardMarkup:
    """Build answer buttons A/B/C/D — clean, no emoji."""
    letters = ["A", "B", "C", "D"]
    rows = []
    for i, opt in enumerate(options):
        short = opt[:32] + "…" if len(opt) > 32 else opt
        rows.append([InlineKeyboardButton(
            f"{letters[i]}.  {short}",
            callback_data=f"qz_ans_{msg_id}_{i}"
        )])
    return InlineKeyboardMarkup(rows)

# ══════════════════════════════════════════════════════════════
#  /quiz COMMAND
# ══════════════════════════════════════════════════════════════
@app.on_message(filters.command(["quiz"]))
async def quiz_cmd(client, message: Message):
    uid  = message.from_user.id
    name = message.from_user.first_name or "Player"
    st   = get_user(uid)
    st["name"] = name

    wait = cooldown_left(uid)
    if wait:
        return await message.reply_text(f"⏳ **{wait:.1f}s** baad try karo!")

    last_cmd_time[uid] = time.time()
    acc = accuracy(st)

    await message.reply_text(
        f"🧠 **Ultimate Quiz Arena**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {name}\n"
        f"🏆 Score: **{st['score']}** pts\n"
        f"✅ {st['correct']} sahi  |  ❌ {st['total'] - st['correct']} galat\n"
        f"📊 Accuracy: `{bar(acc)}` {acc}%\n"
        f"🔥 Streak: **{streak_label(st['streak'])}**  |  Best: {st['best_streak']}\n"
        f"🏅 Badges: {len(st['achievements'])}/{len(ACHIEVEMENTS)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Kya karna chahte ho?",
        reply_markup=main_menu_kb()
    )


# ══════════════════════════════════════════════════════════════
#  EXTRA COMMANDS
# ══════════════════════════════════════════════════════════════
@app.on_message(filters.command(["quizscore", "myscore"]))
async def score_cmd(client, message: Message):
    st  = get_user(message.from_user.id)
    acc = accuracy(st)
    await message.reply_text(
        f"📊 **Tera Quiz Report Card**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Score:    `{st['score']}` pts\n"
        f"✅ Correct:  {st['correct']}\n"
        f"❌ Wrong:    {st['total'] - st['correct']}\n"
        f"📈 Accuracy: `{bar(acc)}` {acc}%\n"
        f"🔥 Streak:   {streak_label(st['streak'])}\n"
        f"⚡ Best:     {st['best_streak']}\n"
        f"🗺️ Subjects: {len(st['cats_tried'])}\n"
        f"🏅 Badges:   {len(st['achievements'])}/{len(ACHIEVEMENTS)}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )


@app.on_message(filters.command(["quiztop", "leaderboard"]))
async def leaderboard_cmd(client, message: Message):
    if not user_data:
        return await message.reply_text("Koi data nahi! /quiz se shuru karo.")
    top = sorted(user_data.items(), key=lambda x: x[1]["score"], reverse=True)[:10]
    lines = ["🏆 **Quiz Leaderboard — Top 10**\n━━━━━━━━━━━━━━━━━━━━"]
    for i, (uid, st) in enumerate(top, 1):
        name = st.get("name", f"User{uid}")[:18]
        lines.append(f"{rank_emoji(i)} **{name}** — {st['score']} pts  ({accuracy(st)}%)")
    await message.reply_text("\n".join(lines))


@app.on_message(filters.command(["achievements", "badges"]))
async def ach_cmd(client, message: Message):
    st = get_user(message.from_user.id)
    lines = [f"🏅 **Achievements** ({len(st['achievements'])}/{len(ACHIEVEMENTS)})\n━━━━━━━━━━━━━━━━━━━━"]
    for key, (title, desc, _) in ACHIEVEMENTS.items():
        lines.append(f"{'✅' if key in st['achievements'] else '🔒'} **{title}** — _{desc}_")
    await message.reply_text("\n".join(lines))


@app.on_message(filters.command(["quizhelp"]))
async def help_cmd(client, message: Message):
    await message.reply_text(
        "🧠 **Ultimate Quiz Bot — Help**\n\n"
        "**Commands:**\n"
        "/quiz — Main menu\n"
        "/quizscore — Apna score\n"
        "/quiztop — Top 10 leaderboard\n"
        "/achievements — Badges dekho\n"
        "/quizhelp — Yeh help\n\n"
        "**24 Subjects available hain:**\n"
        "General, Books, Film, Music, Theatre, TV, Video Games, Board Games,\n"
        "Science, Computers, Maths, Mythology, Sports, Geography, History,\n"
        "Politics, Art, Celebrities, Animals, Vehicles, Comics, Gadgets,\n"
        "Anime, Cartoons + 🤖 AI Custom!\n\n"
        "**Scoring:**\n"
        "🟢 Easy: 10  |  🟡 Medium: 25  |  🔴 Hard: 50  |  💀 Expert: 100\n\n"
        "**Streak Bonus:**\n"
        "3x → ×1.5  |  5x → ×2.0  |  10x → ×3.0\n"
    )

# ══════════════════════════════════════════════════════════════
#  CALLBACKS — NAVIGATION
# ══════════════════════════════════════════════════════════════
@app.on_callback_query(filters.regex(r"^qz_main$"))
async def cb_main(client, cb: CallbackQuery):
    uid = cb.from_user.id
    st  = get_user(uid)
    acc = accuracy(st)
    await cb.message.edit_text(
        f"🧠 **Ultimate Quiz Arena**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Score: **{st['score']}** pts  |  🔥 {streak_label(st['streak'])}\n"
        f"📊 Accuracy: `{bar(acc)}` {acc}%\n"
        f"━━━━━━━━━━━━━━━━━━━━\nKya karna chahte ho?",
        reply_markup=main_menu_kb()
    )
    await cb.answer()


@app.on_callback_query(filters.regex(r"^qz_subjects_(\d+)$"))
async def cb_subjects(client, cb: CallbackQuery):
    page = int(cb.matches[0].group(1))
    await cb.message.edit_text(
        f"📚 **Subject Choose Karo** ({len(CATEGORIES)} available)\n━━━━━━━━━━━━━━━━━━━━",
        reply_markup=subjects_kb(page)
    )
    await cb.answer()


@app.on_callback_query(filters.regex(r"^qz_sub_(.+)$"))
async def cb_sub(client, cb: CallbackQuery):
    raw = cb.matches[0].group(1)
    cat_id = raw if raw == "ai" else int(raw)
    cat_name = next((n for n, c in CATEGORIES.items() if str(c) == str(cat_id)), "Quiz")
    await cb.message.edit_text(
        f"**{cat_name}**\n\nDifficulty choose karo:",
        reply_markup=difficulty_kb(cat_id)
    )
    await cb.answer()


@app.on_callback_query(filters.regex(r"^qz_random$"))
async def cb_random(client, cb: CallbackQuery):
    uid = cb.from_user.id
    wait = cooldown_left(uid)
    if wait:
        return await cb.answer(f"⏳ {wait:.1f}s baad!", show_alert=True)
    opentdb = {k: v for k, v in CATEGORIES.items() if v != "ai"}
    cat_name, cat_id = random.choice(list(opentdb.items()))
    diff = random.choice(["easy", "medium", "hard"])
    await cb.answer(f"🎲 {cat_name}!")
    await _send_question(cb.message, uid, cat_id, diff, cat_name)


@app.on_callback_query(filters.regex(r"^qz_daily$"))
async def cb_daily(client, cb: CallbackQuery):
    uid   = cb.from_user.id
    today = str(date.today())
    if daily_done.get(uid) == today:
        return await cb.answer("✅ Aaj ka daily already complete! Kal phir aana.", show_alert=True)
    random.seed(int(today.replace("-", "")))
    opentdb_vals = [v for v in CATEGORIES.values() if v != "ai"]
    cat_id  = random.choice(opentdb_vals)
    diff    = random.choice(["medium", "hard"])
    random.seed()
    cat_name = next((n for n, c in CATEGORIES.items() if c == cat_id), "Quiz")
    daily_done[uid] = today
    st = get_user(uid)
    st["daily_count"] = st.get("daily_count", 0) + 1
    await cb.answer("📅 Daily Challenge!")
    await _send_question(cb.message, uid, cat_id, diff, cat_name, is_daily=True)


@app.on_callback_query(filters.regex(r"^qz_lb$"))
async def cb_lb(client, cb: CallbackQuery):
    if not user_data:
        return await cb.answer("Koi data nahi!", show_alert=True)
    top = sorted(user_data.items(), key=lambda x: x[1]["score"], reverse=True)[:10]
    lines = ["🏆 **Top 10 Players**\n━━━━━━━━━━━━━━━━━━━━"]
    for i, (uid, st) in enumerate(top, 1):
        lines.append(f"{rank_emoji(i)} **{st.get('name','?')[:18]}** — {st['score']} pts")
    await cb.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="qz_main")]])
    )
    await cb.answer()


@app.on_callback_query(filters.regex(r"^qz_ach$"))
async def cb_ach(client, cb: CallbackQuery):
    st = get_user(cb.from_user.id)
    lines = [f"🏅 **Achievements** ({len(st['achievements'])}/{len(ACHIEVEMENTS)})\n━━━━━━━━━━━━━━━━━━━━"]
    for key, (title, desc, _) in ACHIEVEMENTS.items():
        lines.append(f"{'✅' if key in st['achievements'] else '🔒'} {title}")
    await cb.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="qz_main")]])
    )
    await cb.answer()


@app.on_callback_query(filters.regex(r"^qz_stats$"))
async def cb_stats(client, cb: CallbackQuery):
    st  = get_user(cb.from_user.id)
    acc = accuracy(st)
    await cb.message.edit_text(
        f"📊 **My Stats**\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Score:    {st['score']}\n"
        f"✅ Correct:  {st['correct']}\n"
        f"❌ Wrong:    {st['total'] - st['correct']}\n"
        f"📈 Accuracy: {acc}%\n"
        f"🔥 Streak:   {streak_label(st['streak'])}\n"
        f"⚡ Best:     {st['best_streak']}\n"
        f"🗺️ Subjects: {len(st['cats_tried'])}\n"
        f"🏅 Badges:   {len(st['achievements'])}/{len(ACHIEVEMENTS)}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="qz_main")]])
    )
    await cb.answer()

# ══════════════════════════════════════════════════════════════
#  DIFFICULTY CALLBACK → FETCH + SEND
# ══════════════════════════════════════════════════════════════
@app.on_callback_query(filters.regex(r"^qz_diff_(.+)_(\w+)$"))
async def cb_diff(client, cb: CallbackQuery):
    raw  = cb.matches[0].group(1)
    diff = cb.matches[0].group(2)
    uid  = cb.from_user.id

    wait = cooldown_left(uid)
    if wait:
        return await cb.answer(f"⏳ {wait:.1f}s baad!", show_alert=True)

    last_cmd_time[uid] = time.time()
    cat_id   = raw if raw == "ai" else int(raw)
    cat_name = next((n for n, c in CATEGORIES.items() if str(c) == str(cat_id)), "Quiz")

    await cb.answer()
    await _send_question(cb.message, uid, cat_id, diff, cat_name)

# (Answer callback is handled below in cb_answer_v2 which covers both solo + group quiz)

# ══════════════════════════════════════════════════════════════
#  CORE: FETCH + SEND QUESTION
# ══════════════════════════════════════════════════════════════
async def _send_question(
    message: Message,
    uid: int,
    cat_id,
    diff: str,
    cat_name: str,
    is_daily: bool = False,
):
    cfg  = DIFFICULTY.get(diff, DIFFICULTY["medium"])
    st   = get_user(uid)
    st["cats_tried"].add(str(cat_id))

    mult = streak_mult(st["streak"])
    pts  = round(cfg["pts"] * mult)
    bonus_txt = f"  ×{mult:.1f} bonus" if mult > 1 else ""
    daily_txt = "📅 **DAILY CHALLENGE**\n" if is_daily else ""

    try:
        await message.edit_text(
            f"{daily_txt}⏳ **{cat_name}** — {cfg['label']}\n"
            f"💎 {pts} pts{bonus_txt}\n_Fetching question..._"
        )
    except Exception:
        pass

    await app.send_chat_action(message.chat.id, ChatAction.TYPING)

    # Fetch question
    if cat_id == "ai":
        q = await fetch_ai_question(diff if diff != "expert" else "hard")
    else:
        q = await fetch_opentdb(cat_id, diff)
        if not q:
            await asyncio.sleep(1.5)
            q = await fetch_opentdb(cat_id, "medium")

    if not q:
        try:
            await message.edit_text(
                "❌ Question fetch nahi hua. Retry karo!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Retry", callback_data=f"qz_diff_{cat_id}_{diff}"),
                    InlineKeyboardButton("Menu",  callback_data="qz_main"),
                ]])
            )
        except Exception:
            pass
        return

    question    = html.unescape(q["question"])
    correct_ans = html.unescape(q["correct_answer"])
    options     = [html.unescape(a) for a in q["incorrect_answers"]] + [correct_ans]
    random.shuffle(options)
    correct_idx = options.index(correct_ans)

    letters = ["🅐", "🅑", "🅒", "🅓"]
    opts_text = "\n".join(f"{letters[i]} {opt}" for i, opt in enumerate(options))

    header = (
        f"{daily_txt}"
        f"🧠 **{cat_name}**\n"
        f"{cfg['label']}  |  ⏱ {cfg['time']}s  |  💎 {pts} pts{bonus_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"❓ {question}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{opts_text}"
    )

    try:
        sent = await message.edit_text(
            header,
            reply_markup=answer_kb(message.id, options, correct_idx)
        )
        ref_id = message.id
    except Exception:
        try:
            sent = await message.reply_text(
                header,
                reply_markup=answer_kb(message.id, options, correct_idx)
            )
            ref_id = sent.id
        except Exception:
            return

    # Store question info
    active_questions[ref_id] = {
        "correct_idx":  correct_idx,
        "options":      options,
        "pts":          pts,
        "cat":          cat_name,
        "diff":         diff,
        "chat_id":      message.chat.id,
        "answered_by":  set(),
        "created_at":   time.time(),
    }

    # Auto-expire after time limit + 5s buffer
    async def expire():
        await asyncio.sleep(cfg["time"] + 5)
        if ref_id in active_questions:
            del active_questions[ref_id]

    asyncio.create_task(expire())

# ══════════════════════════════════════════════════════════════
#  BACK-TO-BACK GROUP QUIZ  (/groupquiz)
#  Flow:
#    1. /groupquiz  → subject selection keyboard
#    2. User picks subject → difficulty keyboard
#    3. User picks difficulty → 20 questions fire one by one
#       with GROUP_QUIZ_GAP seconds gap between each
# ══════════════════════════════════════════════════════════════

GROUP_QUIZ_TOTAL = 20
GROUP_QUIZ_GAP   = 8   # seconds between questions
group_quiz_sessions: dict = {}  # chat_id → session dict


def gq_subjects_kb(page: int = 0) -> InlineKeyboardMarkup:
    """Subject picker for group quiz (paginated, 12 per page)."""
    items = list(CATEGORIES.items())
    per_page = 12
    start = page * per_page
    chunk = items[start:start + per_page]
    rows = []
    for i in range(0, len(chunk), 2):
        row = [
            InlineKeyboardButton(n, callback_data=f"gq_sub_{c}_p{page}")
            for n, c in chunk[i:i+2]
        ]
        rows.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("< Prev", callback_data=f"gq_page_{page-1}"))
    if start + per_page < len(items):
        nav.append(InlineKeyboardButton("Next >", callback_data=f"gq_page_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("Cancel", callback_data="gq_cancel")])
    return InlineKeyboardMarkup(rows)


def gq_difficulty_kb(cat_id) -> InlineKeyboardMarkup:
    """Difficulty picker for group quiz — all 4 levels."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Easy (+10 x 20Q)",  callback_data=f"gq_start_{cat_id}_easy"),
            InlineKeyboardButton("Medium (+25 x 20Q)",  callback_data=f"gq_start_{cat_id}_medium"),
        ],
        [
            InlineKeyboardButton("Hard (+50 x 20Q)",  callback_data=f"gq_start_{cat_id}_hard"),
            InlineKeyboardButton("Expert (+100 x 20Q)", callback_data=f"gq_start_{cat_id}_expert"),
        ],
        [InlineKeyboardButton("Back to Subjects", callback_data="gq_page_0")],
        [InlineKeyboardButton("Cancel",            callback_data="gq_cancel")],
    ])


# ── /groupquiz command ────────────────────────────────────────
@app.on_message(filters.command(["groupquiz", "gquiz"]))
async def groupquiz_cmd(client, message: Message):
    chat_id = message.chat.id

    # Block if a session already running in this group
    if chat_id in group_quiz_sessions and group_quiz_sessions[chat_id].get("running"):
        sess       = group_quiz_sessions[chat_id]
        starter_nm = sess.get("starter_name", "kisi ne")
        cat_name   = sess.get("cat_name", "Quiz")
        diff       = sess.get("diff", "medium")
        cfg        = DIFFICULTY.get(diff, DIFFICULTY["medium"])
        q_done     = sess.get("current", 0)
        return await message.reply_text(
            f"⚠️ **{message.chat.title or 'Is group'} mein pehle se quiz chal raha hai!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Started by: **{starter_nm}**\n"
            f"📚 Subject:    **{cat_name}**\n"
            f"🎯 Difficulty: **{cfg['label']}**\n"
            f"📊 Progress:   **{q_done}/{GROUP_QUIZ_TOTAL}** questions\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Khatam hone do ya /stopquiz se band karo."
        )

    chat_title = message.chat.title or "Group"
    await message.reply_text(
        f"🏆 **Group Back-to-Back Quiz — 20 Questions!**\n"
        f"🏠 **{chat_title}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 Pehle **subject** choose karo:",
        reply_markup=gq_subjects_kb(0),
    )


# ── /stopquiz command ─────────────────────────────────────────
@app.on_message(filters.command(["stopquiz"]))
async def stopquiz_cmd(client, message: Message):
    chat_id    = message.chat.id
    uid        = message.from_user.id
    chat_title = message.chat.title or "Group"
    sess       = group_quiz_sessions.get(chat_id)

    if not sess or not sess.get("running"):
        return await message.reply_text(
            f"❌ **{chat_title}** mein koi active quiz nahi chal raha."
        )

    # Private chat mein admin check nahi — group mein sirf admin
    is_private = message.chat.type.value == "private"
    is_admin   = is_private  # private chat mein sender hi owner hota hai
    if not is_private:
        try:
            member   = await client.get_chat_member(chat_id, uid)
            is_admin = member.status.value in ("administrator", "creator")
        except Exception:
            pass

    if not is_admin:
        return await message.reply_text(
            "Sirf group admin quiz band kar sakte hain."
        )

    # Authorized — stop
    sess["running"] = False
    group_quiz_sessions.pop(chat_id, None)

    q_done     = sess.get("current", 0)
    cat_name   = sess.get("cat_name", "Quiz")
    diff       = sess.get("diff", "medium")
    cfg        = DIFFICULTY.get(diff, DIFFICULTY["medium"])
    stopper_nm = message.from_user.first_name or "Admin"
    scoreboard = sess.get("scores", {})

    lines = [
        f"🛑 **Quiz Rokk Diya!**",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"🏠 Group:      **{chat_title}**",
        f"👤 Roka by:    **{stopper_nm}**",
        f"📚 Subject:    **{cat_name}**",
        f"🎯 Difficulty: **{cfg['label']}**",
        f"📊 Completed:  **{q_done}/{GROUP_QUIZ_TOTAL}** questions",
        f"━━━━━━━━━━━━━━━━━━━━",
    ]

    if scoreboard:
        top = sorted(scoreboard.items(), key=lambda x: x[1]["pts"], reverse=True)
        lines.append("📋 **Partial Results:**")
        for i, (_, v) in enumerate(top[:5], 1):
            lines.append(
                f"{rank_emoji(i)} **{v['name'][:18]}** — "
                f"{v['pts']} pts  ✅{v['correct']}/{q_done}"
            )
    else:
        lines.append("😶 Kisi ne jawab nahi diya.")

    await message.reply_text("\n".join(lines))


# ── Callback: page navigation ─────────────────────────────────
@app.on_callback_query(filters.regex(r"^gq_page_(\d+)$"))
async def gq_page_cb(client, cb: CallbackQuery):
    page = int(cb.matches[0].group(1))
    await cb.message.edit_text(
        "🏆 **Group Back-to-Back Quiz — 20 Questions!**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📚 Pehle **subject** choose karo:",
        reply_markup=gq_subjects_kb(page),
    )
    await cb.answer()


# ── Callback: subject selected → show difficulty ──────────────
@app.on_callback_query(filters.regex(r"^gq_sub_(.+)_p(\d+)$"))
async def gq_sub_cb(client, cb: CallbackQuery):
    raw    = cb.matches[0].group(1)
    cat_id = raw if raw == "ai" else int(raw)
    cat_name = next((n for n, c in CATEGORIES.items() if str(c) == str(cat_id)), "Quiz")

    await cb.message.edit_text(
        f"✅ Subject: **{cat_name}**\n\n"
        f"🎯 Ab **difficulty** choose karo:\n"
        f"_(Streak bonus bhi milega — 3x=×1.5, 5x=×2, 10x=×3)_",
        reply_markup=gq_difficulty_kb(cat_id),
    )
    await cb.answer()


# ── Callback: cancel ─────────────────────────────────────────
@app.on_callback_query(filters.regex(r"^gq_cancel$"))
async def gq_cancel_cb(client, cb: CallbackQuery):
    chat_id = cb.message.chat.id
    sess = group_quiz_sessions.pop(chat_id, None)
    if sess:
        sess["running"] = False
    await cb.message.edit_text("❌ Group quiz cancel kar diya.")
    await cb.answer()


# ── Callback: difficulty selected → LAUNCH SESSION ───────────
@app.on_callback_query(filters.regex(r"^gq_start_(.+)_(\w+)$"))
async def gq_start_cb(client, cb: CallbackQuery):
    raw    = cb.matches[0].group(1)
    diff   = cb.matches[0].group(2)
    cat_id = raw if raw == "ai" else int(raw)
    chat_id = cb.message.chat.id

    if chat_id in group_quiz_sessions and group_quiz_sessions[chat_id].get("running"):
        return await cb.answer("⚠️ Quiz pehle se chal raha hai!", show_alert=True)

    cat_name   = next((n for n, c in CATEGORIES.items() if str(c) == str(cat_id)), "Quiz")
    cfg        = DIFFICULTY.get(diff, DIFFICULTY["medium"])
    starter_id = cb.from_user.id
    starter_nm = cb.from_user.first_name or "Player"
    chat_title = cb.message.chat.title or "Group"

    session = {
        "running":      True,
        "cat_id":       cat_id,
        "cat_name":     cat_name,
        "diff":         diff,
        "current":      0,
        "scores":       {},
        "started_by":   starter_id,
        "starter_name": starter_nm,
        "chat_title":   chat_title,
    }
    group_quiz_sessions[chat_id] = session

    await cb.message.edit_text(
        f"🚀 **Group Quiz Shuru!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏠 Group:      **{chat_title}**\n"
        f"👤 Started by: **{starter_nm}**\n"
        f"📚 Subject:    **{cat_name}**\n"
        f"🎯 Difficulty: **{cfg['label']}**\n"
        f"📝 Questions:  **{GROUP_QUIZ_TOTAL}**\n"
        f"💎 Per Q:      **{cfg['pts']} pts** (+ streak bonus)\n"
        f"⏱ Time/Q:     **{cfg['time']}s**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Pehla question aane wala hai... 🔥\n"
        f"_/stopquiz — Sirf group admin band kar sakte hain_"
    )
    await cb.answer("Quiz start! 🎉")

    # Launch the marathon as a background task
    asyncio.create_task(_run_group_quiz(client, chat_id, session))


# ── Core runner: fires 20 questions one by one ────────────────
async def _run_group_quiz(client, chat_id: int, session: dict):
    cat_id   = session["cat_id"]
    cat_name = session["cat_name"]
    diff     = session["diff"]
    cfg      = DIFFICULTY.get(diff, DIFFICULTY["medium"])
    total    = GROUP_QUIZ_TOTAL

    await asyncio.sleep(3)  # Small countdown buffer

    for q_num in range(1, total + 1):
        if not session.get("running"):
            break

        session["current"] = q_num

        # ── Fetch question ────────────────────────────────────
        if cat_id == "ai":
            q = await fetch_ai_question(diff if diff != "expert" else "hard")
        else:
            q = await fetch_opentdb(cat_id, diff)
            if not q:
                await asyncio.sleep(1.5)
                q = await fetch_opentdb(cat_id, "medium")

        if not q:
            await client.send_message(
                chat_id,
                f"❌ Q{q_num}: Question fetch nahi hua, skip kar rahe hain..."
            )
            await asyncio.sleep(3)
            continue

        # ── Build question message ────────────────────────────
        question    = html.unescape(q["question"])
        correct_ans = html.unescape(q["correct_answer"])
        options     = [html.unescape(a) for a in q["incorrect_answers"]] + [correct_ans]
        random.shuffle(options)
        correct_idx = options.index(correct_ans)

        letters   = ["A", "B", "C", "D"]
        opts_text = "\n".join(f"{letters[i]}.  {opt}" for i, opt in enumerate(options))
        progress  = f"[{'█' * q_num}{'░' * (total - q_num)}] {q_num}/{total}"

        def build_msg(secs_left: int) -> str:
            bar_filled = round(secs_left / cfg["time"] * 10)
            bar = "█" * bar_filled + "░" * (10 - bar_filled)
            return (
                f"**Group Quiz** — {cat_name} | {cfg['label']}\n"
                f"{progress}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"**Q{q_num}.** {question}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"{opts_text}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"[{bar}] {secs_left}s  |  {cfg['pts']} pts"
            )

        # ── Send question ─────────────────────────────────────
        try:
            sent = await client.send_message(
                chat_id,
                build_msg(cfg["time"]),
                reply_markup=answer_kb(0, options, correct_idx),
            )
        except Exception:
            await asyncio.sleep(3)
            continue

        real_id = sent.id
        try:
            await sent.edit_reply_markup(answer_kb(real_id, options, correct_idx))
        except Exception:
            pass

        active_questions[real_id] = {
            "correct_idx":    correct_idx,
            "options":        options,
            "pts":            cfg["pts"],
            "cat":            cat_name,
            "diff":           diff,
            "chat_id":        chat_id,
            "answered_by":    set(),
            "created_at":     time.time(),
            "gq_session":     session,
        }

        # ── Live countdown timer (edit every 5s) ──────────────
        time_left = cfg["time"]
        while time_left > 0 and session.get("running"):
            await asyncio.sleep(min(5, time_left))
            time_left -= 5
            if time_left > 0 and real_id in active_questions:
                try:
                    await sent.edit_text(
                        build_msg(max(0, time_left)),
                        reply_markup=answer_kb(real_id, options, correct_idx),
                    )
                except Exception:
                    pass

        # Remove from active so no more answers accepted
        active_questions.pop(real_id, None)

        # Build result text
        result_lines = [
            f"**Q{q_num} Answer:**",
            f"✅  {letters[correct_idx]}.  **{options[correct_idx]}**",
            "",
        ]

        # Show who got it right
        scoreboard = session["scores"]
        correct_users = [
            f"  {rank_emoji(i+1)} {v['name']} (+{v.get('last_pts', cfg['pts'])} pts)"
            for i, (uid, v) in enumerate(scoreboard.items())
            if v.get("last_q") == q_num and v.get("last_correct")
        ]
        if correct_users:
            result_lines.append("Sahi jawab:\n" + "\n".join(correct_users))
        else:
            result_lines.append("Kisi ne sahi jawab nahi diya.")

        try:
            await client.send_message(chat_id, "\n".join(result_lines))
        except Exception:
            pass

        # Gap before next question
        if q_num < total and session.get("running"):
            await asyncio.sleep(GROUP_QUIZ_GAP)

    # ── Session over → Final Leaderboard ─────────────────────
    if not session.get("running"):
        return  # Was stopped manually

    session["running"] = False
    group_quiz_sessions.pop(chat_id, None)

    scoreboard = session["scores"]
    if not scoreboard:
        await client.send_message(
            chat_id,
            "🏁 **Group Quiz Khatam!**\n\nKisi ne participate nahi kiya. 😢"
        )
        return

    top = sorted(scoreboard.items(), key=lambda x: x[1]["pts"], reverse=True)
    lines = [
        f"🏁 **Group Quiz Khatam! — Final Results**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 {cat_name}  |  {cfg['label']}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    ]
    for i, (uid, v) in enumerate(top[:10], 1):
        acc_pct = round(v["correct"] / total * 100)
        lines.append(
            f"{rank_emoji(i)} **{v['name'][:18]}** — "
            f"{v['pts']} pts  ✅{v['correct']}/{total}  ({acc_pct}%)"
        )
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🥇 Champion: **{top[0][1]['name']}** 🎉")

    await client.send_message(chat_id, "\n".join(lines))


# ── Patch cb_answer to also update group quiz scoreboard ──────
# Override the original cb_answer to handle group quiz scoring

@app.on_callback_query(filters.regex(r"^qz_ans_(-?\d+)_(\d+)$"))
async def cb_answer_v2(client, cb: CallbackQuery):
    msg_id = int(cb.matches[0].group(1))
    chosen = int(cb.matches[0].group(2))
    uid    = cb.from_user.id
    name   = cb.from_user.first_name or "Player"

    if msg_id not in active_questions:
        return await cb.answer("❌ Yeh question expire ho gaya!", show_alert=True)

    info = active_questions[msg_id]
    answered_by = info.setdefault("answered_by", set())
    if uid in answered_by:
        return await cb.answer("⚠️ Tu pehle hi jawab de chuka hai!", show_alert=True)
    answered_by.add(uid)

    st = get_user(uid)
    st["name"]  = name
    st["total"] += 1

    correct_idx = info["correct_idx"]
    options     = info["options"]
    pts         = info["pts"]
    won         = (chosen == correct_idx)
    letters     = ["A", "B", "C", "D"]

    # ── Group quiz session score tracking ─────────────────────
    gq_sess = info.get("gq_session")
    if gq_sess is not None:
        scoreboard = gq_sess["scores"]
        if uid not in scoreboard:
            scoreboard[uid] = {"name": name, "pts": 0, "correct": 0,
                               "last_q": 0, "last_correct": False, "last_pts": 0}
        entry = scoreboard[uid]
        entry["last_q"]       = gq_sess["current"]
        entry["last_correct"] = won
        if won:
            bonus    = round(pts * streak_mult(st["streak"]))
            entry["pts"]      += bonus
            entry["correct"]  += 1
            entry["last_pts"]  = bonus
            st["correct"]     += 1
            st["streak"]      += 1
            st["score"]       += bonus
            st["best_streak"]  = max(st["best_streak"], st["streak"])
            await cb.answer(f"✅ Sahi! +{bonus} pts", show_alert=False)
        else:
            st["streak"] = 0
            await cb.answer("❌ Galat jawab!", show_alert=False)

        new_ach = check_achievements(uid, st)
        for ach in new_ach:
            try:
                await asyncio.sleep(0.3)
                await cb.message.reply_text(ach)
            except Exception:
                pass
        return  # Don't send individual result in group quiz mode

    # ── Normal solo quiz scoring ──────────────────────────────
    if won:
        st["correct"]     += 1
        st["streak"]      += 1
        st["score"]       += pts
        st["best_streak"]  = max(st["best_streak"], st["streak"])
        acc = accuracy(st)
        result = (
            f"✅ **Sahi jawab, {name}!**\n"
            f"{letters[correct_idx]} {options[correct_idx]}\n\n"
            f"💎 +{pts} pts  |  🔥 Streak: {streak_label(st['streak'])}\n"
            f"🏆 Total: {st['score']} pts  |  📊 {acc}%"
        )
        await cb.answer("✅ Sahi! +" + str(pts) + " pts", show_alert=False)
    else:
        st["streak"] = 0
        result = (
            f"❌ **Galat, {name}!**\n"
            f"Tera jawab: {letters[chosen]} {options[chosen]}\n"
            f"Sahi jawab: {letters[correct_idx]} **{options[correct_idx]}**\n\n"
            f"💔 Streak reset  |  Score: {st['score']} pts"
        )
        await cb.answer("❌ Galat jawab!", show_alert=False)

    new_ach = check_achievements(uid, st)
    try:
        await cb.message.reply_text(result)
        for ach in new_ach:
            await asyncio.sleep(0.4)
            await cb.message.reply_text(ach)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
#  MODULE META
# ══════════════════════════════════════════════════════════════
__MODULE__ = "Quiz"
__HELP__ = (
    "/quiz        — Ultimate AI Quiz (24 subjects + AI)\n"
    "/groupquiz   — Group back-to-back 20Q marathon\n"
    "               (subject + difficulty choose karo)\n"
    "/stopquiz    — Chal rahe group quiz ko band karo\n"
    "/quizscore   — Apna score\n"
    "/quiztop     — Leaderboard\n"
    "/achievements — Badges\n"
    "/quizhelp    — Full help"
)
