import re
import asyncio
import yt_dlp
from pyrogram import filters
from VIPMUSIC import app
from config import LOG_GROUP_ID

# Instagram URL validation regex
INSTAGRAM_RE = re.compile(r"https?://(www\.)?instagram\.com/(reel|p|tv)/[a-zA-Z0-9_-]+/")

# Function to fetch video info using yt-dlp
def fetch_insta_info(url):
    opts = {
        "format": "best",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        # Agar server IP block ho toh yahan cookies add ki ja sakti hain
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                return info.get("url"), info.get("title")
    except Exception as e:
        print(f"yt-dlp error: {e}")
    return None, None

@app.on_message(filters.command(["ig", "instagram", "reel"]))
async def download_instagram_video(client, message):
    # Command check
    if len(message.command) < 2:
        return await message.reply_text(
            "✨ **ᴜsᴀɢᴇ:**\n\n`/ig [Instagram-URL]`\n\nᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɪɴsᴛᴀɢʀᴀᴍ ʀᴇᴇʟ ᴏʀ ᴘᴏsᴛ ʟɪɴᴋ."
        )

    url = message.text.split()[1]
    
    # URL Validation
    if not INSTAGRAM_RE.match(url):
        return await message.reply_text(
            "❌ **ɪɴᴠᴀʟɪᴅ URL!**\n\nᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɪɴsᴛᴀɢʀᴀᴍ ʀᴇᴇʟ, ᴘᴏsᴛ, ᴏʀ ᴛᴠ ʟɪɴᴋ."
        )

    m = await message.reply_text("🔎 **ᴘʀᴏᴄᴇssɪɴɢ... ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.**")

    try:
        # Run yt-dlp in a separate thread to prevent bot freezing
        loop = asyncio.get_event_loop()
        video_url, title = await loop.run_in_executor(None, fetch_insta_info, url)

        if not video_url:
            return await m.edit(
                "❌ **ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴠɪᴅᴇᴏ!**\n\nᴛʜɪs ʜᴀᴘᴘᴇɴs ɪғ:\n"
                "1. ᴛʜᴇ ᴀᴄᴄᴏᴜɴᴛ ɪs **ᴘʀɪᴠᴀᴛᴇ**.\n"
                "2. ᴛʜᴇ ʟɪɴᴋ ɪs ʙʀᴏᴋᴇɴ.\n"
                "3. ɪɴsᴛᴀɢʀᴀᴍ ɪs ʙʟᴏᴄᴋɪɴɢ ᴛʜᴇ sᴇʀᴠᴇʀ ɪᴘ."
            )

        await m.edit("🚀 **ᴜᴘʟᴏᴀᴅɪɴɢ ᴛᴏ ᴛᴇʟᴇɢʀᴀᴍ...**")
        
        # Sending the video
        await message.reply_video(
            video=video_url,
            caption=f"✨ **ᴅᴏᴡɴʟᴏᴀᴅᴇᴅ ʙʏ:** @{app.username}\n\n🎬 **ᴛɪᴛʟᴇ:** {title if title else 'Instagram Video'}",
        )
        await m.delete()

    except Exception as e:
        await m.edit(f"⚠️ **ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ:**\n`{str(e)}`")
        await app.send_message(LOG_GROUP_ID, f"#IG_ERROR\nUser: {message.from_user.id}\nError: {e}")


__MODULE__ = "Rᴇᴇʟ"
__HELP__ = """
**ɪɴsᴛᴀɢʀᴀᴍ ᴅᴏᴡɴʟᴏᴀᴅᴇʀ:**

• `/ig [URL]`: ᴅᴏᴡɴʟᴏᴀᴅ ɪɴsᴛᴀɢʀᴀᴍ ʀᴇᴇʟs, ᴘᴏsᴛs, ᴏʀ ɪɢᴛᴠ ᴠɪᴅᴇᴏs.
• `/reel [URL]`: sᴀᴍᴇ ᴀs ᴀʙᴏᴠᴇ.
• `/instagram [URL]`: sᴀᴍᴇ ᴀs ᴀʙᴏᴠᴇ.

**ɴᴏᴛᴇ:** ᴏɴʟʏ ᴘᴜʙʟɪᴄ ᴘᴏsᴛs ᴀʀᴇ sᴜᴘᴘᴏʀᴛᴇᴅ.
"""
