import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

# ================= SOZLAMALAR =================
BOT_TOKEN = "8701789752:AAH0_E_NPDkKhy4DJF9zCIg2mJdZ0QcV5Fc"
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 8672128042
CHANNELS = ["@sukuna_pc7", "@asensoakk", "@asensoyt"]
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({
                "android": None, "iphone": None, 
                "android_video": None, "iphone_video": None,
                "android_caption": None, "iphone_caption": None,
                "android_video_caption": None, "iphone_video_caption": None
            }, f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

def check_sub(user_id):
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"❌ KANALDA XATOLIK ({channel}): {e}")
            return False
    return True

def ask_for_sub(chat_id):
    markup = InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        markup.add(InlineKeyboardButton(text=f"{ch} ga obuna bo'lish", url=f"https://t.me/{ch[1:]}"))
    markup.add(InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub"))
    bot.send_message(chat_id, "⚠️ **Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz shart!**\n\nObuna bo'lgach, tekshirish tugmasini bosing.", reply_markup=markup, parse_mode="Markdown")

def send_main_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("📱 Android Proxy"), KeyboardButton("🍏 iPhone Proxy"))
    bot.send_message(chat_id, "Quyidagilardan birini tanlang:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    if not check_sub(message.from_user.id):
        ask_for_sub(message.chat.id)
        return
    bot.send_message(message.chat.id, "Salom! Botga xush kelibsiz.")
    send_main_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def sub_callback(call):
    bot.answer_callback_query(call.id)
    if check_sub(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Obuna tasdiqlandi!")
        send_main_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Hali hamma kanallarga obuna bo'lmadingiz!", show_alert=True)

@bot.message_handler(func=lambda msg: msg.text in ["📱 Android Proxy", "🍏 iPhone Proxy"])
def send_proxy(message):
    if not check_sub(message.from_user.id):
        ask_for_sub(message.chat.id)
        return

    db = load_db()
    if message.text == "📱 Android Proxy":
        file_id = db.get("android")
        file_caption = db.get("android_caption") or f"Mana sizga {message.text}:"
        video_id = db.get("android_video")
        video_caption = db.get("android_video_caption") or "🎥 Yuklash va ishlatish bo'yicha qo'llanma"
    else:
        file_id = db.get("iphone")
        file_caption = db.get("iphone_caption") or f"Mana sizga {message.text}:"
        video_id = db.get("iphone_video")
        video_caption = db.get("iphone_video_caption") or "🎥 Yuklash va ishlatish bo'yicha qo'llanma"

    if not file_id:
        bot.send_message(message.chat.id, f"❌ {message.text} fayli hali admin tomonidan yuklanmagan.")
        return

    # Faylni yuborish (tagidagi yozuvi bilan birga)
    bot.send_document(message.chat.id, file_id, caption=file_caption)

    # Videoni yuborish (tagidagi yozuvi bilan birga)
    if video_id:
        try:
            bot.send_video(message.chat.id, video_id, caption=video_caption)
        except Exception:
            try:
                bot.send_document(message.chat.id, video_id, caption=video_caption)
            except Exception:
                bot.send_animation(message.chat.id, video_id, caption=video_caption)
    else:
        bot.send_message(message.chat.id, "❌ Ushbu proxy uchun video qo'llanma hali admin tomonidan yuklanmagan.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, f"❌ Siz admin emassiz! Sizning ID raqamingiz: {message.from_user.id}")
        return
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📱 Android Proxy (Fayl) yangilash", callback_data="update_android"),
        InlineKeyboardButton("🍏 iPhone Proxy (Fayl) yangilash", callback_data="update_iphone"),
        InlineKeyboardButton("🎥 Android Video (MP4) yangilash", callback_data="update_android_video"),
        InlineKeyboardButton("🎥 iPhone Video (MP4) yangilash", callback_data="update_iphone_video")
    )
    bot.send_message(message.chat.id, "🛠 **Admin panel**. Nima yangilaymiz?", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("update_"))
def admin_update_callback(call):
    bot.answer_callback_query(call.id)
    if call.from_user.id != ADMIN_ID:
        bot.send_message(call.message.chat.id, "❌ Siz admin emassiz!")
        return
    
    update_type = call.data.replace("update_", "")
    display_name = update_type.replace("_", " ").title()
    
    msg = bot.send_message(
        call.message.chat.id, 
        f"📥 Iltimos, yangi **{display_name}** ni botga yuboring:\n\n*(Fayl yoki videoni yuborayotganda tagiga izoh yozsangiz, bot uni ham saqlab oladi va foydalanuvchilarga matni bilan ko'rsatadi!)*", 
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_new_file, update_type)

def save_new_file(message, update_type):
    if message.from_user.id != ADMIN_ID:
        return
    db = load_db()
    
    # Fayl tagidagi izohni olish (agar bo'lsa)
    caption = message.caption if message.caption else ""
    
    if update_type in ["android", "iphone"]:
        if message.content_type != 'document':
            bot.send_message(message.chat.id, f"❌ Xato! Siz botga **{message.content_type}** yubordingiz. Proxy uchun faqat **Fayl (Document)** yuboring! /admin ni qayta bosing.")
            return
        db[update_type] = message.document.file_id
        db[f"{update_type}_caption"] = caption  # Izohni saqlash
        save_db(db)
        bot.send_message(message.chat.id, f"✅ {update_type.capitalize()} proxy fayli va izohi muvaffaqiyatli saqlandi!")
        
    elif update_type in ["android_video", "iphone_video"]:
        file_id = None
        if message.content_type == 'video':
            file_id = message.video.file_id
        elif message.content_type == 'document':
            file_id = message.document.file_id
        elif message.content_type == 'animation':
            file_id = message.animation.file_id
            
        if not file_id:
            bot.send_message(message.chat.id, f"❌ Xato! Siz botga **{message.content_type}** yubordingiz. Iltimos, faqat Video, Fayl yoki GIF yuboring! /admin ni qayta bosing.")
            return
            
        db[update_type] = file_id
        db[f"{update_type}_caption"] = caption  # Video izohini saqlash
        save_db(db)
        bot.send_message(message.chat.id, f"✅ {update_type.replace('_', ' ').capitalize()} va izohi muvaffaqiyatli saqlandi!")

if __name__ == '__main__':
    print('Bot ishga tushdi...')
    bot.polling(none_stop=True)
