import os
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from VIPMUSIC import app


def upload_to_catbox(file_path):
    url = "https://catbox.moe/user/api.php"

    with open(file_path, "rb") as f:
        response = requests.post(
            url,
            data={"reqtype": "fileupload"},
            files={"fileToUpload": f},
            timeout=120,
        )

    if response.status_code != 200:
        raise Exception("Upload Failed")

    return response.text.strip()


@app.on_message(filters.command(["tgm", "tgt", "telegraph", "tl"]))
async def get_link_group(client, message):

    if not message.reply_to_message:
        return await message.reply_text(
            "❌ Reply To A Media File."
        )

    media = message.reply_to_message
    file_size = 0

    if media.photo:
        file_size = media.photo.file_size

    elif media.video:
        file_size = media.video.file_size

    elif media.document:
        file_size = media.document.file_size

    else:
        return await message.reply_text(
            "❌ Supported Media:\nPhoto, Video, Document"
        )

    if file_size > 200 * 1024 * 1024:
        return await message.reply_text(
            "❌ File Size Must Be Under 200MB."
        )

    text = await message.reply_text(
        "📥 Downloading..."
    )

    try:

        async def progress(current, total):
            try:
                percentage = current * 100 / total
                await text.edit_text(
                    f"📥 Downloading... {percentage:.1f}%"
                )
            except Exception:
                pass

        local_path = await media.download(
            progress=progress
        )

        await text.edit_text(
            "📤 Uploading To Catbox..."
        )

        upload_path = upload_to_catbox(local_path)

        await text.edit_text(
            f"✅ File Uploaded Successfully\n\n🌐 {upload_path}",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🌐 Open Link",
                            url=upload_path
                        )
                    ]
                ]
            )
        )

    except Exception as e:

        await text.edit_text(
            f"❌ Upload Failed\n\nReason:\n{e}"
        )

    finally:

        try:
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
        except Exception:
            pass


__MODULE__ = "telegram"

__HELP__ = """
➠ Reply To Any Media File With:

/tgm
/tgt
/tl
/telegraph

➠ Supported:
• Photos
• Videos
• Documents

➠ Upload Limit:
200MB
"""
