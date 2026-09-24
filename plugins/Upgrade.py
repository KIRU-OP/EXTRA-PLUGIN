import os
import zipfile
import shutil
import time
from pyrogram import filters
from pyrogram.types import Message
from github import Github
from motor.motor_asyncio import AsyncIOMotorClient

# --- DATABASE & APP CONFIG ---
try:
    try:
        from config import MONGO_DB_URI as MONGO_DB_URL
    except ImportError:
        from config import MONGO_DB_URL
except ImportError:
    MONGO_DB_URL = None 

from VIPMUSIC import app 

if MONGO_DB_URL:
    mongo_client = AsyncIOMotorClient(MONGO_DB_URL)
    db = mongo_client["GitHubPublicBot"]
    tokens_col = db["user_tokens"]

# --- HELP GUIDE ---
HELP_TEXT = """
🚀 **GITHUB REPO UPGRADER BOT**
━━━━━━━━━━━━━━━━━━━━━━
This bot allows you to upload and refactor repositories (Change imports/folder names automatically).

🔐 **SETUP:**
๏ `/settoken <token>` : Save your GitHub Personal Access Token.
๏ `/deltoken` : Delete your saved token.

📤 **COMMANDS:**
๏ `/upload_repo <repo_name> <old_string> <new_string>`
๏ `/upgrade_repo <repo_name> <old_string> <new_string>`

**Example:** 
`/upload_repo MyNewBot VIPMUSIC ALEX_MUSIC`
*(This will replace all 'VIPMUSIC' imports and folders with 'ALEX_MUSIC' before uploading)*
━━━━━━━━━━━━━━━━━━━━━━
"""

async def get_token(user_id):
    if not MONGO_DB_URL: return None
    res = await tokens_col.find_one({"user_id": user_id})
    return res["token"] if res else None

@app.on_message(filters.command(["start", "help"]))
async def help_handler(_, message: Message):
    await message.reply_text(HELP_TEXT)

@app.on_message(filters.command(["upload_repo", "upgrade_repo"]))
async def upgrade_upload_handler(_, message: Message):
    user_id = message.from_user.id
    token = await get_token(user_id)
    
    if not token:
        return await message.reply_text("🔑 **Please set your token first:** `/settoken <token>`")

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply_text("❌ Please reply to a **.zip** file.")

    # Format: /upload_repo <repo_name> <old_word> <new_word>
    if len(message.command) < 4:
        return await message.reply_text(
            "❌ **Invalid Format!**\n\n"
            "**Usage:** `/upload_repo <repo_name> <word_to_find> <word_to_replace>`\n"
            "**Example:** `/upload_repo MyBot VIPMUSIC NEW_BRAND`"
        )

    repo_name = message.command[1]
    old_word = message.command[2]
    new_word = message.command[3]

    status = await message.reply_text(f"⏳ **Initializing...**\n🔄 Task: Replacing `{old_word}` with `{new_word}`")

    try:
        g = Github(token)
        user = g.get_user()

        # Repository Setup
        try:
            repo = user.get_repo(repo_name)
        except:
            await status.edit(f"🔨 Creating new repository: `{repo_name}`...")
            repo = user.create_repo(repo_name, auto_init=True)
            time.sleep(2)

        # Download and Extract
        await status.edit("📥 **Downloading ZIP from Telegram...**")
        file_path = await message.reply_to_message.download()
        extract_dir = f"work_{user_id}_{int(time.time())}"
        os.makedirs(extract_dir)

        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        await status.edit("🚀 **Refactoring Code & Uploading to GitHub...**")
        
        # Identify base directory
        upload_from = extract_dir
        subdirs = os.listdir(extract_dir)
        if len(subdirs) == 1 and os.path.isdir(os.path.join(extract_dir, subdirs[0])):
            upload_from = os.path.join(extract_dir, subdirs[0])

        count = 0
        for root, dirs, files in os.walk(upload_from):
            for f in files:
                local_path = os.path.join(root, f)
                
                # 1. READ & REPLACE CONTENT (Refactor Imports/Strings)
                try:
                    with open(local_path, "rb") as file_data:
                        content = file_data.read()
                    
                    # Only refactor text-based files
                    if f.endswith(('.py', '.txt', '.md', '.yml', '.yaml', '.conf', '.env', '.json')):
                        try:
                            text = content.decode('utf-8')
                            if old_word in text:
                                text = text.replace(old_word, new_word)
                                content = text.encode('utf-8')
                        except:
                            pass # Binary or unknown encoding
                except Exception as e:
                    print(f"Error reading {f}: {e}")

                # 2. RENAME PATHS (Refactor Folder/File names)
                relative_path = os.path.relpath(local_path, upload_from)
                # Replace the old word in the directory structure
                git_path = relative_path.replace(old_word, new_word).replace("\\", "/")

                # 3. UPLOAD TO GITHUB
                try:
                    try:
                        # Update existing file (SHA required)
                        existing_file = repo.get_contents(git_path)
                        repo.update_file(existing_file.path, f"Refactored: {old_word} to {new_word}", content, existing_file.sha)
                    except:
                        # Create new file
                        repo.create_file(git_path, f"Uploaded: {git_path}", content)
                    count += 1
                except Exception as upload_err:
                    print(f"Failed to upload {git_path}: {upload_err}")

        await status.edit(
            f"✅ **Repository Upgraded Successfully!**\n\n"
            f"📦 **Repository:** `{repo_name}`\n"
            f"🔄 **Refactored:** `{old_word}` ➔ `{new_word}`\n"
            f"📄 **Total Files:** `{count}`\n\n"
            f"🔗 **[View on GitHub]({repo.html_url})**",
            disable_web_page_preview=True
        )

        # Cleanup temporary files
        shutil.rmtree(extract_dir)
        if os.remove(file_path): os.remove(file_path)

    except Exception as e:
        await status.edit(f"❌ **GitHub Error:** `{str(e)}`")

@app.on_message(filters.command("settoken"))
async def set_token_cmd(_, message: Message):
    if len(message.command) < 2: 
        return await message.reply_text("Usage: `/settoken <your_github_token>`")
    await tokens_col.update_one({"user_id": message.from_user.id}, {"$set": {"token": message.command[1]}}, upsert=True)
    await message.reply_text("✅ GitHub Token saved!")

@app.on_message(filters.command("deltoken"))
async def del_token_cmd(_, message: Message):
    await tokens_col.delete_one({"user_id": message.from_user.id})
    await message.reply_text("🗑️ GitHub Token deleted.")

__MODULE__ = "Upgrade"
__HELP__ = HELP_TEXT
