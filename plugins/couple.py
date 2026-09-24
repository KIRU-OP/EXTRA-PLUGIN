from datetime import datetime, timedelta
import logging
import pytz
import os
import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatType
from telegraph import upload_file
from PIL import Image, ImageDraw
import requests

from config import SUPPORT_CHAT, SUPPORT_GROUP
from utils import get_image, get_couple, save_couple
from VIPMUSIC import app

logger = logging.getLogger(__name__)


# ── helpers ──────────────────────────────────────────────────────────────────

def get_ist_date(offset_days: int = 0) -> str:
    """Return date string in IST (GMT+5:30), optionally shifted by *offset_days*."""
    tz = pytz.timezone("Asia/Kolkata")
    dt = datetime.now(tz) + timedelta(days=offset_days)
    return dt.strftime("%d/%m/%Y")


def download_image(url: str, path: str) -> str:
    """Download *url* to *path*; raise on HTTP error."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    with open(path, "wb") as f:
        f.write(response.content)
    return path


FALLBACK_AVATAR = "https://telegra.ph/file/05aa686cf52fc666184bf.jpg"
COUPLE_BG      = "https://telegra.ph/file/96f36504f149e5680741a.jpg"


# ── command handler ───────────────────────────────────────────────────────────

@app.on_message(filters.command(["couple", "couples"]))
async def couple_cmd(_, message):
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("Tʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋs ɪɴ ɢʀᴏᴜᴘs.")

    # Compute dates fresh on every invocation — not at import time
    today    = get_ist_date(0)
    tomorrow = get_ist_date(1)

    cid = message.chat.id

    p1_path        = f"downloads/pfp_{cid}.png"
    p2_path        = f"downloads/pfp1_{cid}.png"
    test_img_path  = f"downloads/test_{cid}.png"
    bg_path        = f"downloads/cppic_{cid}.png"

    msg = await message.reply_text("💫")

    try:
        is_selected = await get_couple(cid, today)

        # ── already selected today ────────────────────────────────────────────
        if is_selected:
            img_url  = await get_image(cid)
            c1_id    = int(is_selected["c1_id"])
            c2_id    = int(is_selected["c2_id"])
            c1_name  = (await app.get_users(c1_id)).first_name
            c2_name  = (await app.get_users(c2_id)).first_name

            caption = (
                f"**Tᴏᴅᴀʏ's ᴄᴏᴜᴘʟᴇ ᴏғ ᴛʜᴇ ᴅᴀʏ 🎉:\n\n"
                f"[{c1_name}](tg://openmessage?user_id={c1_id}) + "
                f"[{c2_name}](tg://openmessage?user_id={c2_id}) = 💞\n\n"
                f"Nᴇxᴛ ᴄᴏᴜᴘʟᴇs ᴡɪʟʟ ʙᴇ sᴇʟᴇᴄᴛᴇᴅ ᴏɴ {tomorrow}!!**"
            )
            await message.reply_photo(
                img_url,
                caption=caption,
                reply_markup=_add_me_markup(),
            )
            await msg.delete()
            return

        # ── pick a new couple ─────────────────────────────────────────────────
        members = []
        async for m in app.get_chat_members(cid, limit=200):
            if not m.user.is_bot and not m.user.is_deleted:
                members.append(m.user.id)

        if len(members) < 2:
            await msg.edit_text("Nᴏᴛ ᴇɴᴏᴜɢʜ ᴍᴇᴍʙᴇʀs ᴛᴏ ᴘɪᴄᴋ ᴀ ᴄᴏᴜᴘʟᴇ.")
            return

        # sample(k=2) guarantees two *distinct* users in one call
        c1_id, c2_id = random.sample(members, 2)

        # profile photos
        async def fetch_photo(uid: int, path: str) -> str:
            try:
                chat  = await app.get_chat(uid)
                return await app.download_media(chat.photo.big_file_id, file_name=path)
            except Exception:
                return download_image(FALLBACK_AVATAR, path)

        p1 = await fetch_photo(c1_id, p1_path)
        p2 = await fetch_photo(c2_id, p2_path)

        N1 = (await app.get_users(c1_id)).mention
        N2 = (await app.get_users(c2_id)).mention

        # compose image
        bg = Image.open(download_image(COUPLE_BG, bg_path))

        def circle_crop(img_path: str, size=(437, 437)) -> Image.Image:
            im   = Image.open(img_path).resize(size)
            mask = Image.new("L", size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0) + size, fill=255)
            im.putalpha(mask)
            return im

        bg.paste(circle_crop(p1), (116, 160), circle_crop(p1))
        bg.paste(circle_crop(p2), (789, 160), circle_crop(p2))
        bg.save(test_img_path)

        caption = (
            f"**Tᴏᴅᴀʏ's ᴄᴏᴜᴘʟᴇ ᴏғ ᴛʜᴇ ᴅᴀʏ:\n\n"
            f"{N1} + {N2} = 💞\n\n"
            f"Nᴇxᴛ ᴄᴏᴜᴘʟᴇs ᴡɪʟʟ ʙᴇ sᴇʟᴇᴄᴛᴇᴅ ᴏɴ {tomorrow}!!**"
        )
        await message.reply_photo(
            test_img_path,
            caption=caption,
            reply_markup=_add_me_markup(),
        )
        await msg.delete()

        # upload & persist — must return at least one path
        uploaded = upload_file(test_img_path)
        if not uploaded:
            raise RuntimeError("upload_file returned an empty list")

        img_url = "https://graph.org/" + uploaded[0]
        await save_couple(cid, today, {"c1_id": c1_id, "c2_id": c2_id}, img_url)

    except Exception:
        logger.exception("[couple] error")
        try:
            await msg.edit_text("Sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ, ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")
        except Exception:
            pass

    finally:
        for path in (p1_path, p2_path, test_img_path, bg_path):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
            except Exception as err:
                print(f"[couple] cleanup error for {path}: {err}")


# ── shared markup ─────────────────────────────────────────────────────────────

def _add_me_markup() -> InlineKeyboardMarkup:
    bot_username = getattr(app, "username", None) or "your_bot"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="Aᴅᴅ Mᴇ 💌",
                url=f"https://t.me/{bot_username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton(
                text="Sᴜᴘᴘᴏʀᴛ 💬",
                url=SUPPORT_CHAT,
            )
        ],
    ])


# ── module meta ───────────────────────────────────────────────────────────────

__MODULE__ = "Couple"
__HELP__ = """
**Couple of the Day**

- `/couple` — Pick (or show) today's couple for this group.
  Re-running the command on the same day shows the already-chosen pair.
  A new couple is selected each day at midnight IST.
"""
