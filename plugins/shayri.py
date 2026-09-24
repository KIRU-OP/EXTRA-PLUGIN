import random
from VIPMUSIC.utils.database import get_served_chats
from pyrogram import Client, filters

from VIPMUSIC import app

# Define a dictionary to track the last message timestamp for each user
user_last_message_time = {}
user_command_count = {}
# Define the threshold for command spamming (e.g., 20 commands within 60 seconds)
SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

SHAYRI = [
    " 🌺**बहुत अच्छा लगता है तुझे सताना और फिर प्यार से तुझे मनाना।**🌺 \n\n**🥀Bahut aacha lagta hai tujhe satana Aur fir pyar se tujhe manana.🥀** ",
    " 🌺**मेरी जिंदगी मेरी जान हो तुम मेरे सुकून का दुसरा नाम हो तुम।**🌺 \n\n**🥀Meri zindagi Meri jaan ho tum Mere sukoon ka Dusra naam ho tum.🥀** ",
    " 🌺**तुम मेरी वो खुशी हो जिसके बिना, मेरी सारी खुशी अधूरी लगती है।**🌺 \n\n**🥀**Tum Meri Wo Khushi Ho Jiske Bina, Meri Saari Khushi Adhuri Lagti Ha.🥀** ",
    " 🌺**काश वो दिन जल्दी आए,जब तू मेरे साथ सात फेरो में बन्ध जाए।**🌺 \n\n**🥀Kash woh din jldi aaye Jb tu mere sath 7 feron me bndh jaye.🥀** ",
    " 🌺**अपना हाथ मेरे दिल पर रख दो और अपना दिल मेरे नाम कर दो।**🌺 \n\n**🥀apna hath mere dil pr rakh do aur apna dil mere naam kar do.🥀** ",
    " 🌺**महादेव ना कोई गाड़ी ना कोई बंगला चाहिए सलामत रहे मेरा प्यार बस यही दुआ चाहिए।**🌺 \n\n**🥀Mahadev na koi gadi na koi bangla chahiye salamat rhe mera pyar bas yahi dua chahiye.🥀** ",
    " 🌺**फिक्र तो होगी ना तुम्हारी इकलौती मोहब्बत हो तुम मेरी।**🌺 \n\n**🥀Fikr to hogi na tumhari ikloti mohabbat ho tum meri.🥀** ",
    " 🌺**सुनो जानू आप सिर्फ किचन संभाल लेना आप को संभालने के लिए मैं हूं ना।**🌺 \n\n**🥀suno jaanu aap sirf kitchen sambhal lena ap ko sambhlne ke liye me hun naa.🥀** ",
    " 🌺**सौ बात की एक बात मुझे चाहिए बस तेरा साथ।**🌺 \n\n**🥀So bat ki ek bat mujhe chahiye bas tera sath.🥀** ",
    " 🌺**बहुत मुश्किलों से पाया हैं तुम्हें, अब खोना नहीं चाहते,कि तुम्हारे थे तुम्हारे हैं अब किसी और के होना नहीं चाहते।**🌺 \n\n**🥀Bahut muskilon se paya hai tumhe Ab khona ni chahte ki tumhare they tumhare hai ab kisi or k hona nhi chahte.🥀** ",
    " 🌺**बेबी बातें तो रोज करते है चलो आज रोमांस करते है।**🌺 \n\n**🥀Baby baten to roj karte haichalo aaj romance karte hai..🥀** ",
    " 🌺**सुबह शाम तुझे याद करते है हम और क्या बताएं की तुमसे कितना प्यार करते है हम।**🌺 \n\n**🥀subha sham tujhe yad karte hai hum aur kya batayen ki tumse kitna pyar karte hai hum.🥀** ",
    " 🌺**किसी से दिल लग जाने को मोहब्बत नहीं कहते जिसके बिना दिल न लगे उसे मोहब्बत कहते हैं।**🌺 \n\n**🥀Kisi se dil lag jane ko mohabbat nahi kehte jiske nina dil na lage use mohabbat kehte hai.🥀** ",
    " 🌺**मेरे दिल के लॉक की चाबी हो तुम क्या बताएं जान मेरे जीने की एकलौती वजह हो तुम।**🌺 \n\n**🥀mere dil ke lock ki chabi ho tum kya batayen jaan mere jeene ki eklauti wajah ho tum..🥀** ",
    " 🌺**हम आपकी हर चीज़ से प्यार कर लेंगे, आपकी हर बात पर ऐतबार कर लेंगे, बस एक बार कह दो कि तुम सिर्फ मेरे हो, हम ज़िन्दगी भर आपका इंतज़ार कर लेंगे।**🌺 \n\n**🥀Hum apki har cheez se pyar kar lenge apki har baat par etvar kar lenge bas ek bar keh do ki tum sirf mere ho hum zindagi bhar apka intzaar kar lenge..🥀** ",
    " 🌺**मोहब्बत कभी स्पेशल लोगो से नहीं होती जिससे होती है वही स्पेशल बन जाता है।**🌺 \n\n**🥀Mohabbat kabhi special logo se nahi hoti jisse bhi hoti hai wahi special ban jate hai,.🥀**",
    " 🌺**तू मेरी जान है इसमें कोई शक नहीं तेरे अलावा मुझ पर किसी और का हक़ नहीं।**🌺 \n\n**🥀Tu meri jaan hai isme koi shak nahi tere alawa mujhe par kisi aur ka hak nhi..🥀** ",
    " 🌺**पहली मोहब्बत मेरी हम जान न सके, प्यार क्या होता है हम पहचान न सके, हमने उन्हें दिल में बसा लिया इस कदर कि, जब चाहा उन्हें दिल से निकाल न सके।**🌺 \n\n**🥀Pehli mohabbat meri hum jaan na sake pyar kya hota hai hum pehchan na sake humne unhe dil me basa liya is kadar ki jab chaha unhe dil se nikal na sake.🥀** ",
    " 🌺**खुद नहीं जानती वो कितनी प्यारी हैं , जान है हमारी पर जान से प्यारी हैं, दूरियों के होने से कोई फर्क नहीं पड़ता वो कल भी हमारी थी और आज भी हमारी है.**🌺 \n\n**🥀khud nahi janti vo kitni pyari hai jan hai hamari par jan se jyda payari hai duriya ke hone se frak nahi pdta vo kal bhe hamari the or aaj bhe hamari hai.🥀** ",
    " 🌺**चुपके से आकर इस दिल में उतर जाते हो, सांसों में मेरी खुशबु बनके बिखर जाते हो, कुछ यूँ चला है तेरे इश्क का जादू, सोते-जागते तुम ही तुम नज़र आते हो।**🌺 \n\n**🥀Chupke Se Aakar Iss Dil Mein Utar Jate Ho, Saanso Mein Meri Khushbu BanKe Bikhar Jate Ho,Kuchh Yun Chala Hai Tere Ishq Ka Jadoo, Sote-Jagte Tum Hi Tum Najar Aate Ho..🥀** ",
    " 🌺**प्यार करना सिखा है नफरतो का कोई ठौर नही, बस तु ही तु है इस दिल मे दूसरा कोई और नही.**🌺 \n\n**🥀Pyar karna sikha hai naftaro ka koi thor nahi bas tu hi tu hai is dil me dusra koi aur nahi hai.🥀** ",
    " 🌺**रब से आपकी खुशीयां मांगते है, दुआओं में आपकी हंसी मांगते है, सोचते है आपसे क्या मांगे,चलो आपसे उम्र भर की मोहब्बत मांगते है।**🌺\n\n**🥀Rab se apki khushiyan mangte hai duao me apki hansi mangte hai sochte hai apse kya mange chalo apse umar bhar ki mohabbat mangte hai..🥀** ",
    " 🌺**काश मेरे होंठ तेरे होंठों को छू जाए देखूं जहा बस तेरा ही चेहरा नज़र आए हो जाए हमारा रिश्ता कुछ ऐसा होंठों के साथ हमारे दिल भी जुड़ जाए.**🌺\n\n**🥀kash mere hoth tere hontho ko chu jayen dekhun jaha bas teri hi chehra nazar aaye ho jayen humara rishta kuch easa hothon ke sath humare dil bhi jud jaye.🥀** ",
    " 🌺**आज मुझे ये बताने की इजाज़त दे दो, आज मुझे ये शाम सजाने की इजाज़त दे दो, अपने इश्क़ मे मुझे क़ैद कर लो,आज जान तुम पर लूटाने की इजाज़त दे दो.**🌺\n\n**🥀Aaj mujhe ye batane ki izazat de do, aaj mujhe ye sham sajane ki izazat de do, apne ishq me mujhe ked kr lo aaj jaan tum par lutane ki izazat de do..🥀** ",
    " 🌺**जाने लोग मोहब्बत को क्या क्या नाम देते है, हम तो तेरे नाम को ही मोहब्बत कहते है.**🌺\n\n**🥀Jane log mohabbat ko kya kya naam dete hai hum to tere naam ko hi mohabbat kehte hai..🥀** ",
    " 🌺**देख के हमें वो सिर झुकाते हैं। बुला के महफिल में नजर चुराते हैं। नफरत हैं हमसे तो भी कोई बात नहीं। पर गैरो से मिल के दिल क्यों जलाते हो।**🌺\n\n**🥀Dekh Ke Hame Wo Sir Jhukate Hai Bula Ke Mahfhil Me Najar Churate Hai Nafrat Hai Hamse To Bhi Koei Bat Nhi Par Gairo Se Mil Ke Dil Kyo Jalate Ho.🥀** ",
    " 🌺**तेरे बिना टूट कर बिखर जायेंगे,तुम मिल गए तो गुलशन की तरह खिल जायेंगे, तुम ना मिले तो जीते जी ही मर जायेंगे, तुम्हें जो पा लिया तो मर कर भी जी जायेंगे।**🌺\n\n**🥀Tere bina tut kar bikhar jeynge tum mil gaye to gulshan ki tarha khil jayenge tum na mile to jite ji hi mar jayenge tumhe jo pa liya to mar kar bhi ji jayenge..🥀** ",
    " 🌺**सनम तेरी कसम जेसे मै जरूरी हूँ तेरी ख़ुशी के लिये, तू जरूरी है मेरी जिंदगी के लिये.**🌺\n\n**🥀Sanam teri kasam jese me zaruri hun teri khushi ke liye tu zaruri hai meri zindagi ke liye.🥀** ",
    " 🌺**तुम्हारे गुस्से पर मुझे बड़ा प्यार आया हैं इस बेदर्द दुनिया में कोई तो हैं जिसने मुझे पुरे हक्क से धमकाया हैं.**🌺\n\n**🥀Tumharfe gusse par mujhe pyar aaya hai is bedard duniya me koi to hai jisne mujhe pure hakk se dhamkaya hai.🥀** ",
    " 🌺**पलको से आँखो की हिफाजत होती है धडकन दिल की अमानत होती है ये रिश्ता भी बडा प्यारा होता है कभी चाहत तो कभी शिकायत होती है.**🌺\n\n**🥀Palkon se Aankho ki hifajat hoti hai dhakad dil ki Aamanat hoti hai, ye rishta bhi bada pyara hota hai, kabhi chahat to kabhi shikayat hoti hai.🥀** ",
    " 🌺**मुहब्बत को जब लोग खुदा मानते हैं प्यार करने वाले को क्यों बुरा मानते हैं। जब जमाना ही पत्थर दिल हैं। फिर पत्थर से लोग क्यों दुआ मांगते है।**🌺\n\n**🥀Muhabbt Ko Hab Log Khuda Mante Hai, Payar Karne Walo Ko Kyu Bura Mante Hai,Jab Jamana Hi Patthr Dil Hai,Fhir Patthr Se Log Kyu Duaa Magte Hai.🥀** ",
    " 🌺**हुआ जब इश्क़ का एहसास उन्हें आकर वो पास हमारे सारा दिन रोते रहे हम भी निकले खुदगर्ज़ इतने यारो कि ओढ़ कर कफ़न, आँखें बंद करके सोते रहे।**🌺\n\n**🥀Hua jab ishq ka ehsaas unhe akar wo pass humare sara din rate rahe, hum bhi nikale khudgarj itne yaro ki ood kar kafan ankhe band krke sote rhe.🥀** ",
    " 🌺**दिल के कोने से एक आवाज़ आती हैं। हमें हर पल उनकी याद आती हैं। दिल पुछता हैं बार -बार हमसे के जितना हम याद करते हैं उन्हें क्या उन्हें भी हमारी याद आती हैं।**🌺\n\n**🥀Dil Ke Kone Se Ek Aawaj Aati Hai, Hame Har Pal Uaski Yad Aati Hai, Dil Puchhta Hai Bar Bar Hamse Ke, Jitna Ham Yad Karte Hai Uanhe, Kya Uanhe Bhi Hamari Yad Aati Hai,🥀** ",
    " 🌺**कभी लफ्ज़ भूल जाऊं कभी बात भूल जाऊं, तूझे इस कदर चाहूँ कि अपनी जात भूल जाऊं, कभी उठ के तेरे पास से जो मैं चल दूँ, जाते हुए खुद को तेरे पास भूल जाऊं।**🌺\n\n**🥀Kabhi Lafz Bhool Jaaun Kabhi Baat Bhool Jaaun, Tujhe Iss Kadar Chahun Ki Apni Jaat Bhool Jaaun, Kabhi Uthh Ke Tere Paas Se Jo Main Chal Dun, Jaate Huye Khud Ko Tere Paas Bhool Jaaun..🥀** ",
    " 🌺**आईना देखोगे तो मेरी याद आएगी साथ गुज़री वो मुलाकात याद आएगी पल भर क लिए वक़्त ठहर जाएगा, जब आपको मेरी कोई बात याद आएगी.**🌺\n\n**🥀Aaina dekhoge to meri yad ayegi sath guzari wo mulakat yad ayegi pal bhar ke waqt thahar jayega jab apko meri koi bat yad ayegi.🥀** ",
    " 🌺**प्यार किया तो उनकी मोहब्बत नज़र आई दर्द हुआ तो पलके उनकी भर आई दो दिलों की धड़कन में एक बात नज़र आई दिल तो उनका धड़का पर आवाज़ इस दिल की आई.**🌺\n\n**🥀Pyar kiya to unki mohabbat nazar aai dard hua to palke unki bhar aai do dilon ki dhadkan me ek baat nazar aai dil to unka dhadka par awaz dil ki aai.🥀** ",
    " 🌺**कई चेहरे लेकर लोग यहाँ जिया करते हैं हम तो बस एक ही चेहरे से प्यार करते हैं ना छुपाया करो तुम इस चेहरे को,क्योंकि हम इसे देख के ही जिया करते हैं.**🌺\n\n**🥀Kai chehre lekar log yahn jiya karte hai hum to bas ek hi chehre se pyar karte hai na chupaya karo tum is chehre ko kyuki hum ise dekh ke hi jiya karte hai.🥀** ",
    " 🌺**सबके bf को अपनी gf से बात करके नींद आजाती है और मेरे वाले को मुझसे लड़े बिना नींद नहीं आती।**🌺\n\n**🥀Sabke bf ko apni gf se baat karke nind aajati hai aur mere wale ko mujhse lade bina nind nhi aati.🥀** ",
    " 🌺**सच्चा प्यार कहा किसी के नसीब में होता है. एसा प्यार कहा इस दुनिया में किसी को नसीब होता है.**🌺\n\n**🥀Sacha pyar kaha kisi ke nasib me hota hai esa pyar kahan is duniya me kisi ko nasib hota hai.🥀** ",
]

# Command
SHAYRI_COMMAND = ["gf", "bf", "shayri", "sari", "shari", "love"]


@app.on_message(filters.command(SHAYRI_COMMAND) & filters.group)
async def help(client: Client, message: Message):
    await message.reply_text(
        text=random.choice(SHAYRI),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✨𝚂𝚄𝙿𝙿𝙾𝚁𝚃✨", url=f"https://t.me/+w00BnR_Z_rA5NTY1"
                    ),
                    InlineKeyboardButton(
                        "✨𝙾𝚆𝙽𝙴𝚁✨", url=f"https://t.me/kiru_op"
                    ),
                ]
            ]
        ),
    )


@app.on_message(filters.command(SHAYRI_COMMAND) & filters.private)
async def help(client: Client, message: Message):
    await message.reply_text(
        text=random.choice(SHAYRI),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✨𝚂𝚄𝙿𝙿𝙾𝚁𝚃✨", url=f"https://t.me/+w00BnR_Z_rA5NTY1"
                    ),
                    InlineKeyboardButton(
                        "✨𝙾𝚆𝙽𝙴𝚁✨", url=f"https://t.me/kiru_op"
                    ),
                ]
            ]
        ),
    )


__MODULE__ = "Sʜᴀʏᴀʀɪ"
__HELP__ = """
/ɢғ, /ʙғ, /sʜᴀʏʀɪ, /sᴀʀɪ, /sʜᴀʀɪ, /ᴏᴠᴇ: Gᴇᴛ ᴀ ʀᴀɴᴅᴏᴍ Sʜᴀʏᴀʀɪ.

Tʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ɪɴ ʙᴏᴛʜ ᴘʀɪᴠᴀᴛᴇ ᴀɴᴅ ɢʀᴏᴜᴘ ᴄʜᴀᴛs. Iᴛ ᴘʀᴏᴠɪᴅᴇs ᴀ ʀᴀɴᴅᴏᴍ ᴘɪᴇᴄᴇ ᴏғ Sʜᴀʏᴀʀɪ ғʀᴏᴍ ᴀ ᴘʀᴇᴅᴇғɪɴᴇᴅ ɪsᴛ. Tʜᴇ ʀᴇᴘʏ ɪɴᴄᴜᴅᴇs ʙᴜᴛᴛᴏɴs ғᴏʀ sᴜᴘᴘᴏʀᴛ ᴀɴᴅ ᴏғғɪᴄɪᴀ ᴄʜᴀɴɴᴇs.

Fᴇᴀᴛᴜʀᴇs:
- Pʀᴏᴠɪᴅᴇs ᴀ ʀᴀɴᴅᴏᴍ Sʜᴀʏᴀʀɪ ᴏɴ ᴄᴏᴍᴍᴀɴᴅ.
- Aᴠᴀɪᴀʙᴇ ɪɴ ʙᴏᴛʜ ᴘʀɪᴠᴀᴛᴇ ᴀɴᴅ ɢʀᴏᴜᴘ ᴄʜᴀᴛs.
- Iɴᴄᴜᴅᴇs ɪɴɪɴᴇ ᴋᴇʏʙᴏᴀʀᴅ ʙᴜᴛᴛᴏɴs ғᴏʀ ᴀᴅᴅɪᴛɪᴏɴᴀ sᴜᴘᴘᴏʀᴛ ᴀɴᴅ ᴏғғɪᴄɪᴀ ɪɴᴋs.

Cᴏᴍᴍᴀɴᴅs:
- /ɢғ
- /ʙғ
- /sʜᴀʏʀɪ
- /sᴀʀɪ
- /sʜᴀʀɪ
- /ᴏᴠᴇ

Nᴏᴛᴇ: Tʜɪs ʙᴏᴛ ᴘʀᴏᴠɪᴅᴇs ɪɴᴋs ᴛᴏ sᴜᴘᴘᴏʀᴛ ᴀɴᴅ ᴏғғɪᴄɪᴀ ᴄʜᴀɴɴᴇs ғᴏʀ ғᴜʀᴛʜᴇʀ ᴀssɪsᴛᴀɴᴄᴇ.
"""





from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random

from VIPMUSIC import app

# Define the scheduler
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

# List of funny and cute shayari for night


night_shayari = [ "🌙 ɢᴏᴏᴅ ɴɪɢʜᴛ! ᴍᴀʏ ʏᴏᴜʀ ᴅʀᴇᴀᴍꜱ ʙᴇ ᴀꜱ ꜱᴡᴇᴇᴛ ᴀꜱ ᴛʜᴇ ꜰɪʀꜱᴛ ʙɪᴛᴇ ᴏꜰ ʏᴏᴜʀ ꜰᴀᴠᴏʀɪᴛᴇ ᴅᴇꜱꜱᴇʀᴛ. ᴀꜱ ʏᴏᴜ ᴅʀɪꜰᴛ ᴏꜰꜰ ᴛᴏ ꜱʟᴇᴇᴘ, ᴍᴀʏ ʏᴏᴜʀ ᴍɪɴᴅ ʙᴇ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ᴘᴇᴀᴄᴇꜰᴜʟ ᴛʜᴏᴜɢʜᴛꜱ ᴀɴᴅ ʏᴏᴜʀ ʜᴇᴀʀᴛ ʙᴇ ʟɪɢʜᴛ. ʀᴇᴍᴇᴍʙᴇʀ, ᴇᴠᴇʀʏ ᴅʀᴇᴀᴍ ɪꜱ ᴀ ᴡɪꜱʜ ʏᴏᴜʀ ʜᴇᴀʀᴛ ᴍᴀᴋᴇꜱ, ꜱᴏ ʟᴇᴛ ᴛʜᴇ ɴɪɢʜᴛ ʙᴇ ꜰᴜʟʟ ᴏꜰ ᴡᴏɴᴅᴇʀ ᴀɴᴅ ᴊᴏʏ ꜰᴏʀ ʏᴏᴜ. ꜱʟᴇᴇᴘ ᴛɪɢʜᴛ ᴀɴᴅ ʜᴀᴠᴇ ᴛʜᴇ ꜱᴡᴇᴇᴛᴇꜱᴛ ᴅʀᴇᴀᴍꜱ. ɢᴏᴏᴅ ɴɪɢʜᴛ!", "🌜 ꜱʟᴇᴇᴘ ᴡᴇʟʟ, ᴀɴᴅ ᴍᴀʏ ʏᴏᴜʀ ɴɪɢʜᴛ ʙᴇ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ꜱᴛᴀʀꜱ ᴛʜᴀᴛ ʟɪɢʜᴛ ᴜᴘ ʏᴏᴜʀ ᴅʀᴇᴀᴍꜱ. ɪᴍᴀɢɪɴᴇ ᴀ ᴡᴏʀʟᴅ ᴡʜᴇʀᴇ ᴇᴠᴇʀʏᴛʜɪɴɢ ʏᴏᴜ ᴅᴇꜱɪʀᴇ ᴄᴏᴍᴇꜱ ᴛʀᴜᴇ, ᴀɴᴅ ʟᴇᴛ ᴛʜᴀᴛ ᴛʜᴏᴜɢʜᴛ ᴄᴀʀʀʏ ʏᴏᴜ ɪɴᴛᴏ ᴀ ʙʟɪꜱꜱꜰᴜʟ ꜱʟᴇᴇᴘ. ᴍᴀʏ ʏᴏᴜʀ ᴘɪʟʟᴏᴡ ʙᴇ ᴀꜱ ꜱᴏꜰᴛ ᴀꜱ ᴄʟᴏᴜᴅꜱ ᴀɴᴅ ʏᴏᴜʀ ᴅʀᴇᴀᴍꜱ ᴀꜱ ᴍᴀɢɪᴄᴀʟ ᴀꜱ ꜰᴀɪʀʏ ᴛᴀʟᴇꜱ. ɢᴏᴏᴅ ɴɪɢʜᴛ ᴀɴᴅ ꜱᴡᴇᴇᴛ ᴅʀᴇᴀᴍꜱ, ᴍᴀʏ ʏᴏᴜ ᴡᴀᴋᴇ ᴜᴘ ʀᴇꜰʀᴇꜱʜᴇᴅ ᴀɴᴅ ʀᴇᴀᴅʏ ᴛᴏ ᴄᴏɴQᴜᴇʀ ᴛʜᴇ ᴅᴀʏ!", "✨ ɢᴏᴏᴅ ɴɪɢʜᴛ! ᴍᴀʏ ʏᴏᴜʀ ꜱʟᴇᴇᴘ ʙᴇ ᴀꜱ ᴅᴇᴇᴘ ᴀꜱ ᴛʜᴇ ᴏᴄᴇᴀɴ ᴀɴᴅ ᴀꜱ ᴘᴇᴀᴄᴇꜰᴜʟ ᴀꜱ ᴀ ᴄᴀʟᴍ ʟᴀᴋᴇ. ᴀꜱ ʏᴏᴜ ᴄʟᴏꜱᴇ ʏᴏᴜʀ ᴇʏᴇꜱ, ʟᴇᴛ ɢᴏ ᴏꜰ ᴀʟʟ ᴡᴏʀʀɪᴇꜱ ᴀɴᴅ ꜱᴛʀᴇꜱꜱ. ᴅʀᴇᴀᴍ ᴏꜰ ʙᴇᴀᴜᴛɪꜰᴜʟ ᴘʟᴀᴄᴇꜱ ᴀɴᴅ ᴊᴏʏꜰᴜʟ ᴍᴏᴍᴇɴᴛꜱ, ᴀɴᴅ ʟᴇᴛ ᴛʜᴏꜱᴇ ᴅʀᴇᴀᴍꜱ ꜰɪʟʟ ʏᴏᴜʀ ɴɪɢʜᴛ ᴡɪᴛʜ ʜᴀᴘᴘɪɴᴇꜱꜱ. ʀᴇᴍᴇᴍʙᴇʀ, ᴛʜᴇ ɴɪɢʜᴛ ɪꜱ ᴀ ᴄᴀɴᴠᴀꜱ ꜰᴏʀ ʏᴏᴜʀ ᴅʀᴇᴀᴍꜱ, ꜱᴏ ᴘᴀɪɴᴛ ɪᴛ ᴡɪᴛʜ ᴛʜᴇ ᴄᴏʟᴏʀꜱ ᴏꜰ ᴊᴏʏ ᴀɴᴅ ᴄᴏɴᴛᴇɴᴛᴍᴇɴᴛ. ꜱʟᴇᴇᴘ ᴡᴇʟʟ!", "🌟 ᴡɪꜱʜɪɴɢ ʏᴏᴜ ᴀ ʀᴇꜱᴛꜰᴜʟ ɴɪɢʜᴛ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ꜱᴡᴇᴇᴛ ᴅʀᴇᴀᴍꜱ ᴀɴᴅ ᴡᴀʀᴍ ʜᴜɢꜱ. ᴍᴀʏ ʏᴏᴜʀ ᴅʀᴇᴀᴍꜱ ʙᴇ ᴀꜱ ᴅᴇʟɪɢʜᴛꜰᴜʟ ᴀꜱ ᴀ ꜱᴜʀᴘʀɪꜱᴇ ɢɪꜰᴛ ᴀɴᴅ ᴀꜱ ᴄᴏᴍꜰᴏʀᴛɪɴɢ ᴀꜱ ᴀ ᴄᴏᴢʏ ʙʟᴀɴᴋᴇᴛ. ᴀꜱ ʏᴏᴜ ᴅʀɪꜰᴛ ɪɴᴛᴏ ꜱʟᴜᴍʙᴇʀ, ᴍᴀʏ ʏᴏᴜʀ ᴍɪɴᴅ ʙᴇ ᴀᴛ ᴇᴀꜱᴇ ᴀɴᴅ ʏᴏᴜʀ ʜᴇᴀʀᴛ ʙᴇ ʟɪɢʜᴛ. ɢᴏᴏᴅ ɴɪɢʜᴛ, ᴀɴᴅ ᴍᴀʏ ʏᴏᴜ ᴡᴀᴋᴇ ᴜᴘ ᴡɪᴛʜ ᴀ ꜱᴍɪʟᴇ ᴀɴᴅ ᴀ ʜᴇᴀʀᴛ ꜰᴜʟʟ ᴏꜰ ᴘᴏꜱɪᴛɪᴠɪᴛʏ!", "🌙 ɢᴏᴏᴅ ɴɪɢʜᴛ! ᴍᴀʏ ʏᴏᴜʀ ᴅʀᴇᴀᴍꜱ ʙᴇ ᴀꜱ ꜱᴡᴇᴇᴛ ᴀꜱ ʜᴏɴᴇʏ ᴀɴᴅ ᴀꜱ ᴄᴏᴍꜰᴏʀᴛɪɴɢ ᴀꜱ ᴀ ᴡᴀʀᴍ ᴄᴜᴘ ᴏꜰ ᴄᴏᴄᴏᴀ. ᴀꜱ ʏᴏᴜ ʟᴀʏ ᴅᴏᴡɴ ᴛᴏ ʀᴇꜱᴛ, ʟᴇᴛ ᴛʜᴇ ᴛʀᴀɴQᴜɪʟɪᴛʏ ᴏꜰ ᴛʜᴇ ɴɪɢʜᴛ ᴡʀᴀᴘ ᴀʀᴏᴜɴᴅ ʏᴏᴜ ʟɪᴋᴇ ᴀ ꜱᴏꜰᴛ ʙʟᴀɴᴋᴇᴛ. ꜱʟᴇᴇᴘ ᴡᴇʟʟ, ᴀɴᴅ ᴍᴀʏ ʏᴏᴜ ᴡᴀᴋᴇ ᴜᴘ ᴡɪᴛʜ ᴀ ʜᴇᴀʀᴛ ꜰᴜʟʟ ᴏꜰ ɢʀᴀᴛɪᴛᴜᴅᴇ ᴀɴᴅ ᴀ ꜱᴍɪʟᴇ ᴛʜᴀᴛ ʙʀɪɢʜᴛᴇɴꜱ ᴛʜᴇ ᴅᴀʏ. ꜱᴡᴇᴇᴛ ᴅʀᴇᴀᴍꜱ!", "🌛 ᴍᴀʏ ʏᴏᴜʀ ɴɪɢʜᴛ ʙᴇ ᴀꜱ ꜱᴏᴏᴛʜɪɴɢ ᴀꜱ ᴀ ʟᴜʟʟᴀʙʏ ᴀɴᴅ ᴀꜱ ᴄᴏᴍꜰᴏʀᴛɪɴɢ ᴀꜱ ᴀ ʜᴜɢ ꜰʀᴏᴍ ᴀ ʟᴏᴠᴇᴅ ᴏɴᴇ. ᴀꜱ ʏᴏᴜ ᴄʟᴏꜱᴇ ʏᴏᴜʀ ᴇʏᴇꜱ, ɪᴍᴀɢɪɴᴇ ᴀ ᴡᴏʀʟᴅ ᴡʜᴇʀᴇ ᴇᴠᴇʀʏᴛʜɪɴɢ ɪꜱ ᴘᴇʀꜰᴇᴄᴛ ᴀɴᴅ ʏᴏᴜʀ ᴅʀᴇᴀᴍꜱ ᴄᴏᴍᴇ ᴛʀᴜᴇ. ʟᴇᴛ ᴛʜᴇ ᴘᴇᴀᴄᴇ ᴏꜰ ᴛʜᴇ ɴɪɢʜᴛ ᴇᴍʙʀᴀᴄᴇ ʏᴏᴜ ᴀɴᴅ ᴄᴀʀʀʏ ʏᴏᴜ ᴛᴏ ᴀ ᴘʟᴀᴄᴇ ᴏꜰ ᴛʀᴀɴQᴜɪʟɪᴛʏ. ɢᴏᴏᴅ ɴɪɢʜᴛ, ᴀɴᴅ ᴍᴀʏ ʏᴏᴜ ᴡᴀᴋᴇ ᴜᴘ ᴡɪᴛʜ ʀᴇɴᴇᴡᴇᴅ ᴇɴᴇʀɢʏ ᴀɴᴅ ᴊᴏʏ!", "🌌 ɢᴏᴏᴅ ɴɪɢʜᴛ! ᴍᴀʏ ʏᴏᴜʀ ᴅʀᴇᴀᴍꜱ ʙᴇ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ᴍᴀɢɪᴄᴀʟ ᴍᴏᴍᴇɴᴛꜱ ᴀɴᴅ ʏᴏᴜʀ ꜱʟᴇᴇᴘ ʙᴇ ᴀꜱ ᴅᴇᴇᴘ ᴀꜱ ᴛʜᴇ ɴɪɢʜᴛ ꜱᴋʏ. ᴀꜱ ʏᴏᴜ ᴅʀɪꜰᴛ ᴏꜰꜰ ᴛᴏ ꜱʟᴇᴇᴘ, ʟᴇᴛ ʏᴏᴜʀ ᴍɪɴᴅ ᴡᴀɴᴅᴇʀ ᴛᴏ ʙᴇᴀᴜᴛɪꜰᴜʟ ᴘʟᴀᴄᴇꜱ ᴀɴᴅ ʏᴏᴜʀ ʜᴇᴀʀᴛ ʙᴇ ᴀᴛ ᴘᴇᴀᴄᴇ. ʀᴇᴍᴇᴍʙᴇʀ, ᴛʜᴇ ɴɪɢʜᴛ ɪꜱ ᴀ ᴛɪᴍᴇ ꜰᴏʀ ʀᴇꜱᴛ ᴀɴᴅ ʀᴇᴊᴜᴠᴇɴᴀᴛɪᴏɴ, ꜱᴏ ᴇᴍʙʀᴀᴄᴇ ɪᴛ ꜰᴜʟʟʏ. ꜱʟᴇᴇᴘ ᴡᴇʟʟ ᴀɴᴅ ᴡᴀᴋᴇ ᴜᴘ ʀᴇᴀᴅʏ ꜰᴏʀ ᴀ ʙʀᴀɴᴅ ɴᴇᴡ ᴅᴀʏ!", "💤 ꜱᴡᴇᴇᴛ ᴅʀᴇᴀᴍꜱ! ᴍᴀʏ ʏᴏᴜʀ ɴɪɢʜᴛ ʙᴇ ᴀꜱ ᴘᴇᴀᴄᴇꜰᴜʟ ᴀꜱ ᴀ ꜱᴇʀᴇɴᴇ ʟᴀᴋᴇ ᴀɴᴅ ᴀꜱ ᴄᴀʟᴍ ᴀꜱ ᴀ ɢᴇɴᴛʟᴇ ʙʀᴇᴇᴢᴇ. ᴀꜱ ʏᴏᴜ ᴄʟᴏꜱᴇ ʏᴏᴜʀ ᴇʏᴇꜱ, ʟᴇᴛ ɢᴏ ᴏꜰ ᴀʟʟ ᴛʜᴇ ᴅᴀʏ'ꜱ ᴡᴏʀʀɪᴇꜱ ᴀɴᴅ ʟᴇᴛ ʏᴏᴜʀ ᴅʀᴇᴀᴍꜱ ᴛᴀᴋᴇ ʏᴏᴜ ᴛᴏ ᴀ ᴡᴏʀʟᴅ ᴏꜰ ʜᴀᴘᴘɪɴᴇꜱꜱ ᴀɴᴅ ᴊᴏʏ. ɢᴏᴏᴅ ɴɪɢʜᴛ, ᴀɴᴅ ᴍᴀʏ ʏᴏᴜ ᴡᴀᴋᴇ ᴜᴘ ʀᴇꜰʀᴇꜱʜᴇᴅ ᴀɴᴅ ᴇxᴄɪᴛᴇᴅ ꜰᴏʀ ᴛʜᴇ ᴀᴅᴠᴇɴᴛᴜʀᴇꜱ ᴏꜰ ᴛʜᴇ ɴᴇᴡ ᴅᴀʏ ᴀʜᴇᴀᴅ!", "🌙 ɢᴏᴏᴅ ɴɪɢʜᴛ! ᴍᴀʏ ᴛʜᴇ ꜱᴛᴀʀꜱ ꜱʜɪɴᴇ ʙʀɪɢʜᴛʟʏ ᴏᴠᴇʀ ʏᴏᴜ ᴀɴᴅ ɢᴜɪᴅᴇ ʏᴏᴜ ᴛᴏ ᴀ ᴘᴇᴀᴄᴇꜰᴜʟ ꜱʟᴇᴇᴘ. ᴀꜱ ʏᴏᴜ ᴅʀɪꜰᴛ ɪɴᴛᴏ ᴅʀᴇᴀᴍʟᴀɴᴅ, ᴍᴀʏ ʏᴏᴜʀ ᴍɪɴᴅ ʙᴇ ꜰʀᴇᴇ ᴏꜰ ᴡᴏʀʀɪᴇꜱ ᴀɴᴅ ʏᴏᴜʀ ʜᴇᴀʀᴛ ʙᴇ ꜰᴜʟʟ ᴏꜰ ᴊᴏʏ. ʀᴇᴍᴇᴍʙᴇʀ, ᴇᴠᴇʀʏ ɴɪɢʜᴛ ɪꜱ ᴀ ᴄʜᴀɴᴄᴇ ᴛᴏ ʀᴇꜱᴇᴛ ᴀɴᴅ ʀᴇᴄʜᴀʀɢᴇ, ꜱᴏ ᴛᴀᴋᴇ ᴛʜɪꜱ ᴛɪᴍᴇ ᴛᴏ ʀᴇʟᴀx ᴀɴᴅ ᴇɴᴊᴏʏ ᴛʜᴇ ꜱᴇʀᴇɴɪᴛʏ ᴏꜰ ᴛʜᴇ ɴɪɢʜᴛ. ꜱʟᴇᴇᴘ ᴛɪɢʜᴛ!", "🌜 ɢᴏᴏᴅ ɴɪɢʜᴛ! ᴍᴀʏ ʏᴏᴜʀ ᴅʀᴇᴀᴍꜱ ʙᴇ ᴀꜱ ꜱᴡᴇᴇᴛ ᴀꜱ ᴛʜᴇ ꜰɪʀꜱᴛ ʙɪᴛᴇ ᴏꜰ ʏᴏᴜʀ ꜰᴀᴠᴏʀɪᴛᴇ ᴅᴇꜱꜱᴇʀᴛ ᴀɴᴅ ᴀꜱ ᴄᴏᴍꜰᴏʀᴛɪɴɢ ᴀꜱ ᴀ ᴡᴀʀᴍ ʜᴜɢ. ᴀꜱ ʏᴏᴜ ᴅʀɪꜰᴛ ᴏꜰꜰ ᴛᴏ ꜱʟᴇᴇᴘ, ʟᴇᴛ ʏᴏᴜʀ ᴍɪɴᴅ ʙᴇ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ᴘᴇᴀᴄᴇꜰᴜʟ ᴛʜᴏᴜɢʜᴛꜱ ᴀɴᴅ ʏᴏᴜʀ ʜᴇᴀʀᴛ ʙᴇ ʟɪɢʜᴛ. ʀᴇᴍᴇᴍʙᴇʀ, ᴇᴠᴇʀʏ ᴅʀᴇᴀᴍ ɪꜱ ᴀ ᴄʜᴀɴᴄᴇ ᴛᴏ ᴇxᴘʟᴏʀᴇ ɴᴇᴡ ᴡᴏʀʟᴅꜱ ᴀɴᴅ ᴍᴀᴋᴇ ɴᴇᴡ ᴍᴇᴍᴏʀɪᴇꜱ. ꜱʟᴇᴇᴘ ᴡᴇʟʟ ᴀɴᴅ ʜᴀᴠᴇ ᴀ ᴡᴏɴᴅᴇʀꜰᴜʟ ɴɪɢʜᴛ ✨𝙾𝚆𝙽𝙴𝚁✨ @kiru_op", ]
morning_shayari = [ "🌅 ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ! ᴍᴀʏ ʏᴏᴜʀ ᴅᴀʏ ʙᴇ ᴀꜱ ʙʀɪɢʜᴛ ᴀɴᴅ ᴄʜᴇᴇʀꜰᴜʟ ᴀꜱ ᴛʜᴇ ʀɪꜱɪɴɢ ꜱᴜɴ. ᴀꜱ ʏᴏᴜ ꜱᴛᴀʀᴛ ʏᴏᴜʀ ᴅᴀʏ, ʟᴇᴛ ᴘᴏꜱɪᴛɪᴠɪᴛʏ ᴀɴᴅ ᴊᴏʏ ꜰɪʟʟ ʏᴏᴜʀ ʜᴇᴀʀᴛ. ᴇᴍʙʀᴀᴄᴇ ᴇᴠᴇʀʏ ᴍᴏᴍᴇɴᴛ ᴡɪᴛʜ ᴀ ꜱᴍɪʟᴇ ᴀɴᴅ ʟᴇᴛ ʏᴏᴜʀ ᴇɴᴛʜᴜꜱɪᴀꜱᴍ ꜱʜɪɴᴇ ᴛʜʀᴏᴜɢʜ. ᴍᴀʏ ʏᴏᴜʀ ᴍᴏʀɴɪɴɢ ʙᴇ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ᴛʜᴇ ᴀʀᴏᴍᴀ ᴏꜰ ꜰʀᴇꜱʜ ᴄᴏꜰꜰᴇᴇ ᴀɴᴅ ᴛʜᴇ ᴘʀᴏᴍɪꜱᴇ ᴏꜰ ᴀ ᴡᴏɴᴅᴇʀꜰᴜʟ ᴅᴀʏ ᴀʜᴇᴀᴅ. ʀɪꜱᴇ ᴀɴᴅ ꜱʜɪɴᴇ, ᴀɴᴅ ᴍᴀᴋᴇ ᴛᴏᴅᴀʏ ᴀᴍᴀᴢɪɴɢ!", "🌞 ʀɪꜱᴇ ᴀɴᴅ ꜱʜɪɴᴇ! ᴀ ɴᴇᴡ ᴅᴀʏ ɪꜱ ʜᴇʀᴇ, ꜰᴜʟʟ ᴏꜰ ᴏᴘᴘᴏʀᴛᴜɴɪᴛɪᴇꜱ ᴀɴᴅ ᴀᴅᴠᴇɴᴛᴜʀᴇꜱ ᴡᴀɪᴛɪɴɢ ꜰᴏʀ ʏᴏᴜ. ᴍᴀʏ ʏᴏᴜʀ ᴍᴏʀɴɪɴɢ ʙᴇ ᴀꜱ ʀᴇꜰʀᴇꜱʜɪɴɢ ᴀꜱ ᴀ ᴄᴏᴏʟ ʙʀᴇᴇᴢᴇ ᴀɴᴅ ᴀꜱ ᴠɪʙʀᴀɴᴛ ᴀꜱ ᴀ ʙʟᴏᴏᴍɪɴɢ ꜰʟᴏᴡᴇʀ. ꜱᴛᴀʀᴛ ʏᴏᴜʀ ᴅᴀʏ ᴡɪᴛʜ ᴀ ꜱᴍɪʟᴇ ᴀɴᴅ ᴀ ʜᴇᴀʀᴛ ꜰᴜʟʟ ᴏꜰ ʜᴏᴘᴇ. ʀᴇᴍᴇᴍʙᴇʀ, ᴇᴠᴇʀʏ ꜱᴜɴʀɪꜱᴇ ɪꜱ ᴀ ɴᴇᴡ ʙᴇɢɪɴɴɪɴɢ, ꜱᴏ ᴍᴀᴋᴇ ᴛʜᴇ ᴍᴏꜱᴛ ᴏꜰ ɪᴛ ᴀɴᴅ ʜᴀᴠᴇ ᴀ ꜰᴀɴᴛᴀꜱᴛɪᴄ ᴅᴀʏ!", "🌄 ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ! ᴍᴀʏ ʏᴏᴜʀ ᴅᴀʏ ʙᴇ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ʜᴀᴘᴘɪɴᴇꜱꜱ ᴀɴᴅ ꜱᴜᴄᴄᴇꜱꜱ. ᴀꜱ ʏᴏᴜ ᴏᴘᴇɴ ʏᴏᴜʀ ᴇʏᴇꜱ ᴛᴏ ᴛʜᴇ ɴᴇᴡ ᴅᴀʏ, ʟᴇᴛ ɢᴏ ᴏꜰ ᴀɴʏ ɴᴇɢᴀᴛɪᴠɪᴛʏ ᴀɴᴅ ᴇᴍʙʀᴀᴄᴇ ᴛʜᴇ ᴘᴏꜱɪᴛɪᴠᴇ ᴇɴᴇʀɢʏ ᴀʀᴏᴜɴᴅ ʏᴏᴜ. ᴍᴀʏ ʏᴏᴜʀ ᴍᴏʀɴɪɴɢ ʙᴇ ʙʀɪɢʜᴛ ᴀɴᴅ ʏᴏᴜʀ ꜱᴘɪʀɪᴛ ʜɪɢʜ. ᴡɪᴛʜ ᴇᴀᴄʜ ꜱᴛᴇᴘ ʏᴏᴜ ᴛᴀᴋᴇ, ᴍᴀʏ ʏᴏᴜ ꜰɪɴᴅ ᴊᴏʏ ᴀɴᴅ ꜰᴜʟꜰɪʟʟᴍᴇɴᴛ. ʜᴀᴠᴇ ᴀ ᴡᴏɴᴅᴇʀꜰᴜʟ ᴅᴀʏ ᴀʜᴇᴀᴅ!", "🌻 ᴡᴀᴋᴇ ᴜᴘ ᴀɴᴅ ꜱᴛᴀʀᴛ ʏᴏᴜʀ ᴅᴀʏ ᴡɪᴛʜ ᴀ ʜᴇᴀʀᴛ ꜰᴜʟʟ ᴏꜰ ɢʀᴀᴛɪᴛᴜᴅᴇ ᴀɴᴅ ᴀ ꜱᴍɪʟᴇ ᴏɴ ʏᴏᴜʀ ꜰᴀᴄᴇ. ᴍᴀʏ ʏᴏᴜʀ ᴍᴏʀɴɪɴɢ ʙᴇ ᴀꜱ ʟᴏᴠᴇʟʏ ᴀꜱ ᴀ ʙᴏᴜQᴜᴇᴛ ᴏꜰ ꜰʀᴇꜱʜ ꜰʟᴏᴡᴇʀꜱ ᴀɴᴅ ᴀꜱ ᴜᴘʟɪꜰᴛɪɴɢ ᴀꜱ ᴀ ᴄʜᴇᴇʀꜰᴜʟ ꜱᴏɴɢ. ᴇᴍʙʀᴀᴄᴇ ᴛʜᴇ ɴᴇᴡ ᴅᴀʏ ᴡɪᴛʜ ᴇɴᴛʜᴜꜱɪᴀꜱᴍ ᴀɴᴅ ʟᴇᴛ ɪᴛ ʙʀɪɴɢ ʏᴏᴜ ᴀʟʟ ᴛʜᴇ ʜᴀᴘᴘɪɴᴇꜱꜱ ᴀɴᴅ ꜱᴜᴄᴄᴇꜱꜱ ʏᴏᴜ ᴅᴇꜱᴇʀᴠᴇ. ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ᴀɴᴅ ʜᴀᴠᴇ ᴀ ꜰᴀʙᴜʟᴏᴜꜱ ᴅᴀʏ!", "🌞 ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ! ᴍᴀʏ ʏᴏᴜʀ ᴅᴀʏ ʙᴇ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ᴊᴏʏ ᴀɴᴅ ᴇxᴄɪᴛᴇᴍᴇɴᴛ. ᴀꜱ ʏᴏᴜ ꜱᴛᴇᴘ ɪɴᴛᴏ ᴛʜᴇ ɴᴇᴡ ᴅᴀʏ, ʟᴇᴛ ʏᴏᴜʀ ᴘᴏꜱɪᴛɪᴠɪᴛʏ ᴀɴᴅ ᴇɴᴇʀɢʏ ꜱʜɪɴᴇ ʙʀɪɢʜᴛʟʏ. ᴍᴀʏ ʏᴏᴜʀ ᴍᴏʀɴɪɴɢ ʙᴇ ᴀꜱ ᴠɪʙʀᴀɴᴛ ᴀꜱ ᴀ ꜱᴜɴɴʏ ᴅᴀʏ ᴀɴᴅ ᴀꜱ ʀᴇꜰʀᴇꜱʜɪɴɢ ᴀꜱ ᴀ ᴄᴏᴏʟ ᴅʀɪɴᴋ. ꜱᴛᴀʀᴛ ʏᴏᴜʀ ᴅᴀʏ ᴡɪᴛʜ ᴀ ꜱᴍɪʟᴇ ᴀɴᴅ ʟᴇᴛ ᴛʜᴇ ᴡᴏʀʟᴅ ꜱᴇᴇ ʏᴏᴜʀ ᴡᴏɴᴅᴇʀꜰᴜʟ ꜱᴘɪʀɪᴛ. ʜᴀᴠᴇ ᴀ ɢʀᴇᴀᴛ ᴅᴀʏ ᴀʜᴇᴀᴅ!", "🌄 ʀɪꜱᴇ ᴀɴᴅ ꜱʜɪɴᴇ! ᴀ ɴᴇᴡ ᴅᴀʏ ɪꜱ ʜᴇʀᴇ, ꜰᴜʟʟ ᴏꜰ ᴘʀᴏᴍɪꜱᴇ ᴀɴᴅ ᴘᴏꜱꜱɪʙɪʟɪᴛɪᴇꜱ. ᴍᴀʏ ʏᴏᴜʀ ᴍᴏʀɴɪɴɢ ʙᴇ ᴀꜱ ʙᴇᴀᴜᴛɪꜰᴜʟ ᴀꜱ ᴀ ꜱᴜɴʀɪꜱᴇ ᴀɴᴅ ᴀꜱ ɪɴꜱᴘɪʀɪɴɢ ᴀꜱ ᴀ ɴᴇᴡ ʙᴇɢɪɴɴɪɴɢ. ꜱᴛᴀʀᴛ ʏᴏᴜʀ ᴅᴀʏ ᴡɪᴛʜ ᴀ ᴘᴏꜱɪᴛɪᴠᴇ ᴍɪɴᴅꜱᴇᴛ ᴀɴᴅ ʟᴇᴛ ʏᴏᴜʀ ᴊᴏʏ ᴀɴᴅ ᴇɴᴛʜᴜꜱɪᴀꜱᴍ ɢᴜɪᴅᴇ ʏᴏᴜ. ᴍᴀʏ ᴛᴏᴅᴀʏ ʙᴇ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ᴡᴏɴᴅᴇʀꜰᴜʟ ᴍᴏᴍᴇɴᴛꜱ ᴀɴᴅ ᴀᴍᴀᴢɪɴɢ ᴏᴘᴘᴏʀᴛᴜɴɪᴛɪᴇꜱ. ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ!", "🌻 ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ! ᴍᴀʏ ʏᴏᴜʀ ᴅᴀʏ ʙᴇ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ꜱᴜɴꜱʜɪɴᴇ ᴀɴᴅ ʏᴏᴜʀ ʜᴇᴀʀᴛ ᴡɪᴛʜ ʜᴀᴘᴘɪɴᴇꜱꜱ. ᴀꜱ ʏᴏᴜ ʙᴇɢɪɴ ʏᴏᴜʀ ᴅᴀʏ, ʟᴇᴛ ɢᴏ ᴏꜰ ᴀɴʏ ᴡᴏʀʀɪᴇꜱ ᴀɴᴅ ꜰᴏᴄᴜꜱ ᴏɴ ᴛʜᴇ ᴊᴏʏ ᴀɴᴅ ᴇxᴄɪᴛᴇᴍᴇɴᴛ ᴛʜᴀᴛ ʟɪᴇ ᴀʜᴇᴀᴅ. ᴍᴀʏ ʏᴏᴜʀ ᴍᴏʀɴɪɴɢ ʙᴇ ᴀꜱ ᴅᴇʟɪɢʜᴛꜰᴜʟ ᴀꜱ ᴀ ꜰʀᴇꜱʜ ᴄᴜᴘ ᴏꜰ ᴄᴏꜰꜰᴇᴇ ᴀɴᴅ ᴀꜱ ᴜᴘʟɪꜰᴛɪɴɢ ᴀꜱ ᴀ ꜰʀɪᴇɴᴅʟʏ ꜱᴍɪʟᴇ. ʀɪꜱᴇ ᴀɴᴅ ꜱʜɪɴᴇ, ᴀɴᴅ ᴍᴀᴋᴇ ᴛᴏᴅᴀʏ ɪɴᴄʀᴇᴅɪʙʟᴇ!", "🌞 ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ! ᴍᴀʏ ʏᴏᴜʀ ᴅᴀʏ ʙᴇ ᴀꜱ ʙʀɪɢʜᴛ ᴀɴᴅ ᴄʜᴇᴇʀꜰᴜʟ ᴀꜱ ʏᴏᴜʀ ꜱᴍɪʟᴇ. ᴀꜱ ʏᴏᴜ ᴏᴘᴇɴ ʏᴏᴜʀ ᴇʏᴇꜱ ᴛᴏ ᴛʜᴇ ɴᴇᴡ ᴅᴀʏ, ʟᴇᴛ ʏᴏᴜʀ ᴘᴏꜱɪᴛɪᴠɪᴛʏ ᴀɴᴅ ᴇɴᴛʜᴜꜱɪᴀꜱᴍ ꜱᴇᴛ ᴛʜᴇ ᴛᴏɴᴇ ꜰᴏʀ ᴛʜᴇ ʜᴏᴜʀꜱ ᴀʜᴇᴀᴅ. ᴍᴀʏ ʏᴏᴜʀ ᴍᴏʀɴɪɴɢ ʙᴇ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ʟᴏᴠᴇ, ʟᴀᴜɢʜᴛᴇʀ, ᴀɴᴅ ᴀʟʟ ᴛʜᴇ ᴛʜɪɴɢꜱ ᴛʜᴀᴛ ᴍᴀᴋᴇ ʏᴏᴜ ʜᴀᴘᴘʏ. ᴇᴍʙʀᴀᴄᴇ ᴛʜᴇ ᴅᴀʏ ᴡɪᴛʜ ᴏᴘᴇɴ ᴀʀᴍꜱ ᴀɴᴅ ᴀ ᴊᴏʏꜰᴜʟ ʜᴇᴀʀᴛ!", "🌄 ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ! ᴍᴀʏ ʏᴏᴜʀ ᴅᴀʏ ʙᴇ ꜰɪʟʟᴇᴅ ᴡɪᴛʜ ᴇɴᴅʟᴇꜱꜱ ᴘᴏꜱꜱɪʙɪʟɪᴛɪᴇꜱ ᴀɴᴅ ᴊᴏʏꜰᴜʟ ᴍᴏᴍᴇɴᴛꜱ. ᴀꜱ ʏᴏᴜ ꜱᴛᴀʀᴛ ʏᴏᴜʀ ᴅᴀʏ, ʟᴇᴛ ʏᴏᴜʀ ꜱᴘɪʀɪᴛ ꜱᴏᴀʀ ᴀɴᴅ ʏᴏᴜʀ ʜᴇᴀʀᴛ ʙᴇ ʟɪɢʜᴛ. ᴍᴀʏ ʏᴏᴜʀ ᴍᴏʀɴɪɴɢ ʙᴇ ᴀꜱ ꜰʀᴇꜱʜ ᴀɴᴅ ɪɴᴠɪɢᴏʀᴀᴛɪɴɢ ᴀꜱ ᴀ ɢᴇɴᴛʟᴇ ʙʀᴇᴇᴢᴇ ᴀɴᴅ ᴀꜱ ʙʀɪɢʜᴛ ᴀꜱ ᴛʜᴇ ꜱᴜɴ. ᴡᴇʟᴄᴏᴍᴇ ᴛʜᴇ ɴᴇᴡ ᴅᴀʏ ᴡɪᴛʜ ᴀ ꜱᴍɪʟᴇ ᴀɴᴅ ʟᴇᴛ ɪᴛ ʙʀɪɴɢ ʏᴏᴜ ᴀʟʟ ᴛʜᴇ ʜᴀᴘᴘɪɴᴇꜱꜱ ʏᴏᴜ ᴅᴇꜱᴇʀᴠᴇ.", "🌞 ʀɪꜱᴇ ᴀɴᴅ ꜱʜɪɴᴇ! ɪᴛ’ꜱ ᴀ ʙʀᴀɴᴅ ɴᴇᴡ ᴅᴀʏ ꜰᴜʟʟ ᴏꜰ ᴏᴘᴘᴏʀᴛᴜɴɪᴛɪᴇꜱ ᴀɴᴅ ᴀᴅᴠᴇɴᴛᴜʀᴇꜱ. ᴍᴀʏ ʏᴏᴜʀ ᴍᴏʀɴɪɴɢ ʙᴇ ᴀꜱ ʟɪᴠᴇʟʏ ᴀꜱ ᴀ ꜱᴜɴʀɪꜱᴇ ᴀɴᴅ ᴀꜱ ɪɴꜱᴘɪʀɪɴɢ ᴀꜱ ᴀ ɴᴇᴡ ʙᴇɢɪɴɴɪɴɢ. ꜱᴛᴀʀᴛ ʏᴏᴜʀ ᴅᴀʏ ᴡɪᴛʜ ᴀ ᴘᴏꜱɪᴛɪᴠᴇ ᴀᴛᴛɪᴛᴜᴅᴇ ᴀɴᴅ ʟᴇᴛ ᴛʜᴇ ᴡᴏʀʟᴅ ꜱᴇᴇ ʏᴏᴜʀ ʙʀɪʟʟɪᴀɴᴄᴇ. ᴍᴀʏ ᴛᴏᴅᴀʏ ʙʀɪɴɢ ʏᴏᴜ ᴊᴏʏ, ꜱᴜᴄᴄᴇꜱꜱ, ᴀɴᴅ ᴀʟʟ ᴛʜᴇ ᴛʜɪɴɢꜱ ᴛʜᴀᴛ ᴍᴀᴋᴇ ʏᴏᴜ ꜱᴍɪʟᴇ. ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ! ✨𝙾𝚆𝙽𝙴𝚁✨ @kiru_op", ]



add_buttons = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                text="๏ ᴀᴅᴅ ᴍᴇ ɪɴ ɢʀᴏᴜᴘ ๏",
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ]
    ]
)

# Function to send a "Good Night" message
async def send_good_night():
    chats = []
    schats = await get_served_chats()
    for chat in schats:
        chats.append(int(chat["chat_id"]))
    if len(chats) == 0:
        return
    for chat_id in chats:
        try:
            if chat_id == -1002146211959:
                continue
            shayari = random.choice(night_shayari)
            await app.send_photo(
                chat_id,
                photo="https://telegra.ph//file/06649d4d0bbf4285238ee.jpg",
                caption=f"**{shayari}**",
                reply_markup=add_buttons,
            )
        except Exception as e:
            print(f"[bold red] Unable to send Good Night message to Group {chat_id} - {e}")

scheduler.add_job(send_good_night, trigger="cron", hour=23, minute=59)

# Function to send a "Good Morning" message
async def send_good_morning():
    chats = []
    schats = await get_served_chats()
    for chat in schats:
        chats.append(int(chat["chat_id"]))
    if len(chats) == 0:
        return
    for chat_id in chats:
        try:
            if chat_id == -1002146211959:
                continue
            shayari = random.choice(morning_shayari)
            await app.send_photo(
                chat_id,
                photo="https://telegra.ph//file/14ec9c3ff42b59867040a.jpg",
                caption=f"**{shayari}**",
                reply_markup=add_buttons,
            )
        except Exception as e:
            print(f"[bold red] Unable to send Good Morning message to Group {chat_id} - {e}")

scheduler.add_job(send_good_morning, trigger="cron", hour=6, minute=1)
scheduler.start()

