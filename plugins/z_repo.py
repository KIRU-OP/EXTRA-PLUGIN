import asyncio
import time

from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait, UserAlreadyParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from VIPMUSIC import app
from VIPMUSIC.utils.database import add_served_chat, get_assistant
from config import OWNER_ID


# ══════════════════════════════════════════════════════════════
#  ⚙️  SETTINGS
# ══════════════════════════════════════════════════════════════

REPO_URL = "https://github.com/KIRU-OP/VIP-MUSIC"
FORK_URL = f"{REPO_URL}/fork"
BANNER = "https://envs.sh/wWo.jpg"

EXCLUDED_CHAT = -1003760069374  # /gadd is chat me bot add nahi karega
ADD_DELAY = 3  # har add ke beech ka gap (sec) — flood se bachne ke liye
EDIT_EVERY = 5  # progress message kitne sec me ek baar update ho

GREETING_TRIGGERS = ["hi", "hii", "hello", "hui", "good", "gm", "ok", "bye", "welcome", "thanks"]
GREETING_PREFIXES = ["/", "!", "%", ",", "", ".", "@", "#"]


# ══════════════════════════════════════════════════════════════
#  🎨  DESIGN HELPERS
# ══════════════════════════════════════════════════════════════

LINE = "━━━━━━━━━━━━━━━━━━"
_SMALL_CAPS = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ",
)


def sc(text: str) -> str:
    """Normal text ko ꜱᴍᴀʟʟ ᴄᴀᴘs me badalta hai (sirf labels/headings ke liye)."""
    return text.lower().translate(_SMALL_CAPS)


def bar(done: int, total: int, width: int = 12) -> str:
    filled = width if total == 0 else round(width * done / total)
    return "▰" * filled + "▱" * (width - filled)


def fmt_time(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


async def reply_card(message: Message, caption: str, buttons: list):
    """Photo ke saath card bhejta hai. Photo fail ho to simple text bhej deta hai."""
    markup = InlineKeyboardMarkup(buttons)
    try:
        await message.reply_photo(photo=BANNER, caption=caption, reply_markup=markup)
    except Exception:
        await message.reply_text(caption, reply_markup=markup)


# ══════════════════════════════════════════════════════════════
#  📦  /repo
# ══════════════════════════════════════════════════════════════

@app.on_message(filters.command("repo"))
async def repo_command(client: Client, message: Message):
    caption = (
        f"✦ **{sc('vip music')}** ✦\n"
        f"{LINE}\n\n"
        f"📦 **{sc('official source code')}**\n\n"
        "Hamara poora source code GitHub par openly available hai.\n"
        "Fork karke apna khud ka premium music bot banao!\n\n"
        f"🔐 {sc('licensed & verified repository')}\n"
        f"{LINE}\n"
        f"✦ {sc('powered by aaru music bot')}"
    )
    buttons = [
        [
            InlineKeyboardButton(f"📂 {sc('view repo')}", url=REPO_URL),
            InlineKeyboardButton(f"🍴 {sc('fork')}", url=FORK_URL),
        ]
    ]
    await reply_card(message, caption, buttons)


# ══════════════════════════════════════════════════════════════
#  🍴  /clone
# ══════════════════════════════════════════════════════════════

@app.on_message(filters.command("clone"))
async def clone_command(client: Client, message: Message):
    caption = (
        f"🚫 **{sc('permission denied')}**\n"
        f"{LINE}\n\n"
        "Bhai, tu sudo user nahi hai — isliye seedha clone nahi kar sakta. 😅\n\n"
        f"💡 **{sc('kya karein?')}**\n"
        "  ①  GitHub se fork karke khud host karo 🍴\n"
        "  ②  Ya owner / sudo users se clone ki request karo 📩\n\n"
        f"{LINE}\n"
        f"✦ {sc('vip music — official')}"
    )
    buttons = [
        [
            InlineKeyboardButton(f"🍴 {sc('fork & host')}", url=FORK_URL),
            InlineKeyboardButton(f"📂 {sc('view repo')}", url=REPO_URL),
        ]
    ]
    await reply_card(message, caption, buttons)


# ══════════════════════════════════════════════════════════════
#  💬  Greetings  →  served chat tracker
# ══════════════════════════════════════════════════════════════

# Alag group (11) me rakha hai taaki ye dusre handlers ko block na kare.
# Pyrogram ek group me sirf pehla matching handler chalata hai.
@app.on_message(
    filters.command(GREETING_TRIGGERS, prefixes=GREETING_PREFIXES) & filters.group,
    group=11,
)
async def track_served_chat(_, message: Message):
    await add_served_chat(message.chat.id)


# ══════════════════════════════════════════════════════════════
#  🚀  /gadd  —  bot ko assistant ke saare groups me add karo
# ══════════════════════════════════════════════════════════════

_gadd_running = False


def gadd_text(title: str, bot: str, assistant: str, done: int, total: int, stats: dict, elapsed: float) -> str:
    percent = 100 if total == 0 else int(done * 100 / total)
    return (
        f"{title}\n"
        f"{LINE}\n\n"
        f"🤖 **{sc('bot')}**  ➜  `@{bot}`\n"
        f"👤 **{sc('assistant')}**  ➜  {assistant}\n\n"
        f"`{bar(done, total)}`  **{percent}%**\n"
        f"📊 **{sc('progress')}**  ➜  {done} / {total}\n\n"
        f"✅ **{sc('added')}**  ➜  {stats['added']}\n"
        f"♻️ **{sc('already there')}**  ➜  {stats['already']}\n"
        f"❌ **{sc('failed')}**  ➜  {stats['failed']}\n\n"
        f"⏱ **{sc('time')}**  ➜  {fmt_time(elapsed)}"
    )


async def safe_edit(msg: Message, text: str):
    try:
        await msg.edit(text)
    except FloodWait as e:
        await asyncio.sleep(getattr(e, "value", 5))
    except Exception:
        pass  # MessageNotModified etc.


async def try_add(userbot, chat_id: int, bot_id: int) -> str:
    """'added' / 'already' / 'failed' return karta hai. FloodWait par ruk kar retry karta hai."""
    for _ in range(2):
        try:
            await userbot.add_chat_members(chat_id, bot_id)
            return "added"
        except UserAlreadyParticipant:
            return "already"
        except FloodWait as e:
            await asyncio.sleep(getattr(e, "value", 5) + 1)
        except Exception:
            return "failed"
    return "failed"


async def run_gadd(message: Message, bot_username: str):
    userbot = await get_assistant(message.chat.id)
    bot_user = await app.get_users(bot_username)

    if not bot_user.is_bot:
        return await message.reply(
            f"❌ **{sc('invalid bot')}**\n{LINE}\n\n"
            f"`@{bot_username}` bot nahi hai, kisi user ka username hai."
        )

    # sirf groups / supergroups — private chats aur channels me add nahi ho sakta
    chat_ids = [
        d.chat.id
        async for d in userbot.get_dialogs()
        if d.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP) and d.chat.id != EXCLUDED_CHAT
    ]
    total = len(chat_ids)
    if total == 0:
        return await message.reply(
            f"😕 **{sc('no groups found')}**\n{LINE}\n\n"
            "Assistant kisi group me nahi mila."
        )

    username = getattr(userbot, "username", None)
    assistant = f"@{username}" if username else sc("assistant")
    stats = {"added": 0, "already": 0, "failed": 0}
    started = time.monotonic()

    status = await message.reply(
        gadd_text(f"🚀 **{sc('global add — started')}**", bot_user.username, assistant, 0, total, stats, 0)
    )

    # Start ka message bot ko bhejna zaroori nahi hai, fail ho to bhi aage badho
    try:
        await userbot.send_message(bot_user.username, "/start")
    except Exception:
        pass

    last_edit = time.monotonic()
    for done, chat_id in enumerate(chat_ids, 1):
        stats[await try_add(userbot, chat_id, bot_user.id)] += 1

        if time.monotonic() - last_edit >= EDIT_EVERY:
            await safe_edit(
                status,
                gadd_text(
                    f"🔄 **{sc('global add — in progress')}**",
                    bot_user.username, assistant, done, total, stats, time.monotonic() - started,
                ),
            )
            last_edit = time.monotonic()

        await asyncio.sleep(ADD_DELAY)

    await safe_edit(
        status,
        gadd_text(
            f"🎉 **{sc('completed successfully')}**",
            bot_user.username, assistant, total, total, stats, time.monotonic() - started,
        ),
    )


@app.on_message(filters.command("gadd") & filters.user(OWNER_ID))
async def gadd_command(client: Client, message: Message):
    global _gadd_running

    if len(message.command) != 2:
        return await message.reply(
            f"⚠️ **{sc('wrong format')}**\n"
            f"{LINE}\n\n"
            "📌 Sahi tarika:\n"
            "`/gadd @bot_username`"
        )

    if _gadd_running:
        return await message.reply(
            f"⏳ **{sc('already running')}**\n"
            f"{LINE}\n\n"
            "Ek /gadd process pehle se chal raha hai. Khatam hone ka wait karo."
        )

    _gadd_running = True
    try:
        await run_gadd(message, message.command[1].lstrip("@"))
    except Exception as e:
        await message.reply(f"❗ **{sc('error')}**\n{LINE}\n\n`{e}`")
    finally:
        _gadd_running = False


# ══════════════════════════════════════════════════════════════
#  📖  HELP
# ══════════════════════════════════════════════════════════════

__MODULE__ = "sᴏᴜʀᴄᴇ"
__HELP__ = f"""
✦ {sc('vip music — source module')}
{LINE}

Ye module bot ke source aur utility commands handle karta hai.

📌 {sc('commands')}

🔗 /repo
   ➜ GitHub source code aur fork link.

🍴 /clone
   ➜ Manual hosting ki info (non-sudo users ke liye).

🚀 /gadd @username   👑 {sc('owner only')}
   ➜ Diye hue bot ko assistant ke saare groups me add karta hai.
   ➜ Live progress bar ke saath.

💬 {sc('greetings (group me)')}
   hi · hello · gm · bye · thanks · welcome
   ➜ Bot chupchaap us group ko served-list me track kar leta hai.

{LINE}
✦ {sc('powered by aaru music bot')}
"""
