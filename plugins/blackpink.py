from pyrogram import filters
import requests
import io
from VIPMUSIC import app
from config import BANNED_USERS

__MODULE__ = "BLACKPINK"

__HELP__ = """
**🌸 BLACKPINK IMAGE GENERATOR 🌸**

Generate stunning AI-powered themed images with your name!

**Commands:**

- `/blackpink [name]` - Generate a BlackPink K-pop styled image with your name
  _Example:_ `/blackpink Piyush`

- `/bp [name]` - Shortcut for `/blackpink`
  _Example:_ `/bp Piyush`

- `/redblue [name]` - Generate a Red & Blue abstract styled image with your name
  _Example:_ `/redblue Piyush`

**Note:**
- Images are AI-generated and may take a few seconds
- Powered by Pollinations AI (Free & No API Key Required)
"""

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1024&height=1024&nologo=true"


@app.on_message(filters.command(["bp", "blackpink", "redblue"]) & ~BANNED_USERS)
async def generate_image(client, message):
    command = message.command[0].replace("/", "")
    args = " ".join(message.command[1:])

    if not args:
        await message.reply_text(
            f"❌ Please provide a name!\n\n"
            f"**Usage:** `/{command} YourName`\n"
            f"**Example:** `/{command} Piyush`"
        )
        return

    status_msg = await message.reply_text(
        f"🎨 Creating **{command.capitalize()}** themed image for `{args}`...\n"
        f"⏳ Please wait a moment..."
    )

    # Build prompt based on command
    if command in ("blackpink", "bp"):
        prompt = (
            f"artistic name art of '{args}', K-pop BlackPink style, "
            f"pink and black color tones, neon lights, music notes, "
            f"microphone, bold trendy font, high quality, ultra detailed"
        )
    elif command == "redblue":
        prompt = (
            f"artistic name art of '{args}', red and blue color theme, "
            f"bold vibrant tones, abstract shapes, dynamic lines, "
            f"sleek modern font, high quality, ultra detailed"
        )
    else:
        prompt = f"stylish artistic name image of '{args}', high quality, ultra detailed"

    try:
        # Step 1: Build URL (no API key needed)
        encoded_prompt = requests.utils.quote(prompt)
        image_url = POLLINATIONS_URL.format(prompt=encoded_prompt)

        # Step 2: Download image bytes (fixes IMAGE_PROCESS_FAILED)
        img_response = requests.get(image_url, timeout=60)
        img_response.raise_for_status()

        # Step 3: Check if response is actually an image
        content_type = img_response.headers.get("Content-Type", "")
        if "image" not in content_type:
            await message.reply_text("❌ Failed to generate image. Please try again.")
            return

        # Step 4: Wrap in BytesIO and send
        image_bytes = io.BytesIO(img_response.content)
        image_bytes.name = f"{args}.png"

        await message.reply_photo(
            photo=image_bytes,
            caption=(
                f"✨ **{command.capitalize()}** theme for `{args}`\n"
                f"🎨 Powered by Pollinations AI"
            )
        )

    except requests.exceptions.Timeout:
        await message.reply_text(
            "❌ Request timed out!\n"
            "Please try again after some time."
        )

    except requests.exceptions.ConnectionError:
        await message.reply_text(
            "❌ Connection error!\n"
            "Please check your internet and try again."
        )

    except requests.exceptions.HTTPError as e:
        await message.reply_text(
            f"❌ HTTP Error:\n`{e}`"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ Something went wrong:\n`{e}`"
        )

    finally:
        try:
            await status_msg.delete()
        except:
            pass
