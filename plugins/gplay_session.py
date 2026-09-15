"""
gplay_session.py
-----------------
Personal-assistant voice-chat music feature.

Flow:
  1. User sends `/session <string_session>` to the bot IN PRIVATE (PM).
     -> The session string is validated by actually logging in with it.
     -> It is saved ONLY in your own MongoDB (nowhere else, no external
        forwarding of any kind).
     -> A confirmation is also posted to that account's own "Saved Messages"
        so the user can see it there.
     -> The user's personal account (assistant) is connected and kept ready.

  2. Inside any group where that personal account is present (and a video
     chat exists / can be started), the user runs:
        /gplay <song name>
     -> Their own account automatically joins the group's voice chat and
        starts streaming the requested song.

  3. From PM / Saved Messages, the user can also trigger it remotely by
     giving the group id:
        /gplay -1001234567890 <song name>

  4. `/gend` (in the group, or `/gend <group_id>` from PM) stops playback
     and leaves the call.

  5. `/session_remove` deletes the stored session and disconnects.

SECURITY NOTES (read before deploying):
  - A Pyrogram string session is equivalent to full access to that Telegram
    account. It is only ever stored in your own database, only ever used to
    start a Pyrogram client in this process, and is NEVER sent to any chat,
    bot, or user other than a confirmation copy sent to the account's own
    Saved Messages (i.e. the same account talking to itself).
  - `/session` only works in a private chat and the triggering message is
    deleted immediately after processing so the raw string doesn't sit in
    chat history.
  - Only the user who added a session can use /gplay with it (looked up by
    their own Telegram user_id).

Requirements (add to requirements.txt):
    pytgcalls>=2.1.4
    yt-dlp
And ffmpeg must be installed on the host system.
"""

import asyncio

from pyrogram import filters
from pyrogram.client import Client
from pyrogram.errors import RPCError
from pyrogram.types import Message

from VIPMUSIC import app
from VIPMUSIC.core.mongo import mongodb

try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types import MediaStream, AudioQuality
    from pytgcalls.exceptions import NoActiveGroupCall
    PYTGCALLS_AVAILABLE = True
except ImportError:
    PYTGCALLS_AVAILABLE = False

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False


sessiondb = mongodb.gplay_sessions

# in-memory runtime caches (per running process)
ASSISTANTS: dict[int, Client] = {}
CALLS: dict[int, "PyTgCalls"] = {}
LOCKS: dict[int, asyncio.Lock] = {}


def _lock_for(user_id: int) -> asyncio.Lock:
    if user_id not in LOCKS:
        LOCKS[user_id] = asyncio.Lock()
    return LOCKS[user_id]


async def get_running_assistant(user_id: int):
    """Return (client, pytgcalls) for a user, starting them from the saved
    session if they aren't already running in this process."""
    if user_id in ASSISTANTS and user_id in CALLS:
        return ASSISTANTS[user_id], CALLS[user_id]

    doc = await sessiondb.find_one({"user_id": user_id})
    if not doc:
        return None, None

    client = Client(
        name=f"gplay_{user_id}",
        api_id=app.api_id,
        api_hash=app.api_hash,
        session_string=doc["session"],
        in_memory=True,
    )
    await client.start()

    pytgcalls = PyTgCalls(client)
    await pytgcalls.start()

    ASSISTANTS[user_id] = client
    CALLS[user_id] = pytgcalls
    return client, pytgcalls


async def stop_running_assistant(user_id: int):
    pytgcalls = CALLS.pop(user_id, None)
    client = ASSISTANTS.pop(user_id, None)
    if pytgcalls:
        try:
            await pytgcalls.stop()
        except Exception:
            pass
    if client:
        try:
            await client.stop()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# /session — register + connect a personal string session
# ---------------------------------------------------------------------------
@app.on_message(filters.command("session") & filters.private)
async def add_session(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "**Apna Pyrogram string session bhejo:**\n"
            "`/session <string_session>`\n\n"
            "⚠️ Yeh command sirf PM me kaam karta hai, aur session sirf "
            "apke database me save hota hai, kahin aur forward nahi hota."
        )

    string_session = message.text.split(None, 1)[1].strip()
    user_id = message.from_user.id

    status = await message.reply_text("🔄 Session verify kiya ja raha hai...")

    # try to delete the message containing the raw session for safety
    try:
        await message.delete()
    except Exception:
        pass

    async with _lock_for(user_id):
        # stop any previous instance for this user before re-validating
        await stop_running_assistant(user_id)

        test_client = Client(
            name=f"verify_{user_id}",
            api_id=app.api_id,
            api_hash=app.api_hash,
            session_string=string_session,
            in_memory=True,
        )
        try:
            await test_client.start()
            me = await test_client.get_me()
        except Exception as e:
            return await status.edit_text(f"❌ Invalid session: `{e}`")

        # save (only in our own DB, nothing forwarded elsewhere)
        await sessiondb.update_one(
            {"user_id": user_id},
            {"$set": {
                "user_id": user_id,
                "session": string_session,
                "name": me.first_name,
                "tg_id": me.id,
            }},
            upsert=True,
        )

        confirm_text = (
            "✅ **Session connected successfully!**\n\n"
            f"**Account:** {me.first_name}\n"
            f"**User ID:** `{me.id}`\n\n"
            "Ab aap kisi bhi group me `/gplay <song name>` bhejo, aapka "
            "account uss group ke voice chat me automatically join karke "
            "gaana bajayega."
        )

        # confirmation also shown in that account's own Saved Messages
        try:
            await test_client.send_message("me", confirm_text)
        except Exception:
            pass

        pytgcalls = PyTgCalls(test_client)
        await pytgcalls.start()
        ASSISTANTS[user_id] = test_client
        CALLS[user_id] = pytgcalls

    await status.edit_text(confirm_text)


@app.on_message(filters.command("session_remove") & filters.private)
async def remove_session(_, message: Message):
    user_id = message.from_user.id
    await stop_running_assistant(user_id)
    result = await sessiondb.delete_one({"user_id": user_id})
    if result.deleted_count:
        await message.reply_text("🗑️ Session removed aur account disconnect kar diya gaya.")
    else:
        await message.reply_text("Koi session saved nahi mila.")


# ---------------------------------------------------------------------------
# /gplay — join the video chat and stream a song via the user's own account
# ---------------------------------------------------------------------------
async def _extract_stream_url(query: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "default_search": "ytsearch1",
        "nocheckcertificate": True,
    }
    loop = asyncio.get_event_loop()

    def _extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            return info

    info = await loop.run_in_executor(None, _extract)
    return info["url"], info.get("title", query)


@app.on_message(filters.command("gplay"))
async def gplay(_, message: Message):
    if not PYTGCALLS_AVAILABLE or not YTDLP_AVAILABLE:
        return await message.reply_text(
            "⚠️ `pytgcalls` aur `yt-dlp` install nahi hai. "
            "`pip install pytgcalls yt-dlp` (aur ffmpeg host par install hona chahiye)."
        )

    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        return await message.reply_text(
            "**Usage:**\n"
            "`/gplay <song name>` — group ke andar use karo.\n"
            "`/gplay <group_id> <song name>` — PM/Saved Message se remote use karne ke liye."
        )

    rest = args[1].strip()

    if message.chat.type.name == "PRIVATE":
        parts = rest.split(None, 1)
        if len(parts) < 2 or not parts[0].lstrip("-").isdigit():
            return await message.reply_text(
                "PM se use karne ke liye: `/gplay <group_id> <song name>`"
            )
        target_chat = int(parts[0])
        query = parts[1]
    else:
        target_chat = message.chat.id
        query = rest

    client, pytgcalls = await get_running_assistant(user_id)
    if not client:
        return await message.reply_text(
            "❌ Pehle apna session connect karo: `/session <string_session>` (PM me)."
        )

    status = await message.reply_text(f"🔎 Searching: `{query}` ...")

    try:
        stream_url, title = await _extract_stream_url(query)
    except Exception as e:
        return await status.edit_text(f"❌ Song nahi mil paya: `{e}`")

    # make sure the assistant account is actually in the target chat
    try:
        await client.get_chat(target_chat)
    except RPCError as e:
        return await status.edit_text(
            f"❌ Apka session-account `{target_chat}` group me nahi hai ya access nahi hai: `{e}`"
        )

    try:
        await pytgcalls.play(
            target_chat,
            MediaStream(stream_url, audio_parameters=AudioQuality.STUDIO),
        )
    except NoActiveGroupCall:
        return await status.edit_text(
            "❌ Uss group me abhi koi voice chat active nahi hai. Pehle VC start karo."
        )
    except Exception as e:
        return await status.edit_text(f"❌ Play nahi kar paya: `{e}`")

    await status.edit_text(f"🎶 **Now playing:** {title}\nin chat `{target_chat}`")


@app.on_message(filters.command("gend"))
async def gend(_, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)

    if message.chat.type.name == "PRIVATE":
        if len(args) < 2 or not args[1].strip().lstrip("-").isdigit():
            return await message.reply_text("Usage (PM): `/gend <group_id>`")
        target_chat = int(args[1].strip())
    else:
        target_chat = message.chat.id

    _, pytgcalls = await get_running_assistant(user_id)
    if not pytgcalls:
        return await message.reply_text("❌ Koi active session nahi mila.")

    try:
        await pytgcalls.leave_call(target_chat)
        await message.reply_text("⏹️ Call se leave kar diya.")
    except Exception as e:
        await message.reply_text(f"❌ Error: `{e}`")


__MODULE__ = "Gᴘᴀʏ (Pᴇʀsᴏɴᴀʟ Assɪsᴛᴀɴᴛ Mᴜsɪᴄ)"
__HELP__ = """
**Pᴇʀsᴏɴᴀʟ sᴛʀɪɴɢ-sᴇssɪᴏɴ Vᴏɪᴄᴇ Cʜᴀᴛ Mᴜsɪᴄ**

• `/session <string_session>` (PM only) — apna account connect karo.
• `/session_remove` (PM only) — session hataao aur disconnect karo.
• `/gplay <song name>` — group ke andar, apke account se seedha VC me gaana bajta hai.
• `/gplay <group_id> <song name>` — PM/Saved Message se remote trigger.
• `/gend` — playback stop karke call se leave karo.

⚠️ String session apke Telegram account jaisi sensitive cheez hai — sirf apne trusted bot/deployment me hi daalo. Yeh sirf apke database me store hota hai, kahin aur bheja/forward nahi hota.
"""
