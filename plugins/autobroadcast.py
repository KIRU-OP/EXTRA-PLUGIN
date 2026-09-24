import asyncio
import datetime
import pytz
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import AUTO_GCAST, AUTO_GCAST_MSG, LOG_GROUP_ID
from VIPMUSIC import app
from VIPMUSIC.utils.database import get_served_chats

# Convert AUTO_GCAST to boolean
AUTO_GCASTS = AUTO_GCAST.strip().lower() == "on"

# Image and Messages
START_IMG_URLS = "https://envs.sh/BjZ.jpg"

# ✨ Unique broadcast caption (bot name auto-inserted) ✨
MESSAGE = f"""🎧 ˹@{app.username}˼ ɪs ʙᴀᴄᴋ ᴡɪᴛʜ ᴀ ʙʟᴀᴢɪɴɢ-ғᴀsᴛ ᴜᴘɢʀᴀᴅᴇ ⚡ ᴢᴇʀᴏ ʟᴀɢ • 24×7 ᴜᴘᴛɪᴍᴇ • ᴄʀʏsᴛᴀʟ-ᴄʟᴇᴀʀ sᴏᴜɴᴅ 💜 ᴛᴜʀɴ ᴀɴʏ ᴠᴄ ɪɴᴛᴏ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴍᴜsɪᴄ ʀᴏᴏᴍ — ᴀᴅᴅ ᴍᴇ ᴀɴᴅ ʜɪᴛ ᴘʟᴀʏ ✨"""

BUTTON = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "๏ ᴀᴅᴅ ᴍᴇ ๏",
                url=f"https://t.me/aaru_music_rbot?startgroup=s&admin=delete_messages+manage_video_chats+pin_messages+invite_users",
            )
        ]
    ]
)

caption = f"""{AUTO_GCAST_MSG}""" if AUTO_GCAST_MSG else MESSAGE

TEXT = """**ᴀᴜᴛᴏ ɢᴄᴀsᴛ ɪs ᴇɴᴀʙʟᴇᴅ. ʙᴏᴛ sᴛᴀʀᴛ ʜᴏɴᴇ ᴋᴇ 10 ɢʜᴀɴᴛᴇ ʙᴀᴀᴅ ᴘᴀʜʟᴀ ʙʀᴏᴀᴅᴄᴀsᴛ ʜᴏɢᴀ, ᴜsᴋᴇ ʙᴀᴀᴅ ʜᴀʀ 10 ɢʜᴀɴᴛᴇ ᴍᴇɪɴ ᴇᴋ ʙᴀᴀʀ.**\n**ɪsᴇ ʀᴏᴋɴᴇ ᴋᴇ ʟɪʏᴇ ᴠᴀʀɪᴀʙʟᴇ [ᴀᴜᴛᴏ_ɢᴄᴀsᴛ = (Off)] sᴇᴛ ᴋᴀʀᴇɴ.**"""

# Broadcast interval: har 10 ghante mein ek baar
BROADCAST_INTERVAL_SECONDS = 10 * 60 * 60  # 10 hours

# Timezone set to India (rakha gaya hai agar future mein logging ke liye chahiye ho)
IST = pytz.timezone('Asia/Kolkata')


async def send_text_once():
    try:
        await app.send_message(LOG_GROUP_ID, TEXT)
    except Exception:
        pass


async def send_message_to_chats():
    try:
        chats = await get_served_chats()
        for chat_info in chats:
            chat_id = chat_info.get("chat_id")
            if isinstance(chat_id, int):
                try:
                    await app.send_photo(
                        chat_id,
                        photo=START_IMG_URLS,
                        caption=caption,
                        reply_markup=BUTTON,
                    )
                    # Har message ke baad 3 second ka gap taaki bot spam mein na aaye
                    await asyncio.sleep(3)
                except Exception:
                    pass
    except Exception:
        pass


async def continuous_broadcast():
    # Bot start hone par ek baar log group mein sirf info text bhejega (broadcast nahi)
    await send_text_once()

    while True:
        if AUTO_GCASTS:
            # Pehle 10 ghante wait karega, tabhi broadcast karega
            # (start hote hi turant broadcast NAHI hoga)
            await asyncio.sleep(BROADCAST_INTERVAL_SECONDS)

            try:
                await send_message_to_chats()
            except Exception:
                pass
        else:
            # Agar AUTO_GCASTS off hai to har 30 sec mein recheck karega
            await asyncio.sleep(30)


# Start the task
if AUTO_GCASTS:
    asyncio.create_task(continuous_broadcast())
