import os, json, time
from threading import Thread, Timer
from flask import Flask
import telebot
from telebot import types
from telebot.types import ReplyKeyboardMarkup

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
ADMINS = [7142950609]

USERS_FILE = "users.json"
CHANNELS_FILE = "channels.json"
REWARDS_FILE = "rewards.json"
SETTINGS_FILE = "settings.json"

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive 💗"

def load(file, default):
    if not os.path.exists(file):
        save(file, default)
        return default
    try:
        return json.load(open(file, "r"))
    except:
        return default

def save(file, data):
    json.dump(data, open(file, "w"), indent=2)

def setup():
    load(USERS_FILE, [])
    load(SETTINGS_FILE, {"allow_forward": False})
    load(CHANNELS_FILE, [
        {"name": "💗 CHANNEL 1", "username": "@verfiy_id"},
        {"name": "🔥 CHANNEL 2", "username": "@funny_tym"},
        {"name": "⚡ CHANNEL 3", "username": "@teamflux"},
        {"name": "💎 CHANNEL 4", "username": "@tymm_pass"},
        {"name": "🎯 CHANNEL 5", "username": "@masti_tym"},
        {"name": "🚀 CHANNEL 6", "username": "@tmkc_okh"}
    ])
    load(REWARDS_FILE, [
        {"name": "💋 SLIDESHARE", "url": "http://slideshare.com"},
        {"name": "🔥 STUDOCU", "url": "http://studocu.com"}
    ])

setup()

def is_admin(uid):
    return uid in ADMINS

def add_user(uid):
    users = load(USERS_FILE, [])
    if uid not in users:
        users.append(uid)
        save(USERS_FILE, users)

def channels():
    return load(CHANNELS_FILE, [])

def rewards():
    return load(REWARDS_FILE, [])

def settings():
    return load(SETTINGS_FILE, {"allow_forward": False})

def is_joined(uid):
    for ch in channels():
        try:
            member = bot.get_chat_member(ch["username"], uid)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def join_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for ch in channels():
        btns.append(types.InlineKeyboardButton(ch["name"], url=f"https://t.me/{ch['username'].replace('@','')}"))
    for i in range(0, len(btns), 2):
        kb.add(*btns[i:i+2])
    kb.add(types.InlineKeyboardButton("🎯 VERIFY", callback_data="verify"))
    return kb

def reward_kb():
    kb = types.InlineKeyboardMarkup()
    for r in rewards():
        kb.add(types.InlineKeyboardButton(r["name"], url=r["url"]))
    return kb

def admin_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Add Channel", "❌ Remove Channel")
    kb.row("📋 List Channels", "🎁 Add Reward")
    kb.row("🗑 Remove Reward", "📦 List Rewards")
    kb.row("📊 Stats", "📢 Broadcast")
    kb.row("🔘 Button Broadcast", "🖼 Media Broadcast")
    kb.row("🔐 Forward OFF/ON")
    return kb

@bot.message_handler(commands=["start"])
def start(m):
    add_user(m.from_user.id)

    if is_admin(m.from_user.id):
        bot.send_message(m.chat.id, "👑 ADMIN PANEL", reply_markup=admin_menu())

    caption = f"""🔥 WELCOME {m.from_user.first_name} 😈💗

👥 Users: {len(load(USERS_FILE, []))}

💗 Join all channels
🎯 Then click VERIFY"""

    try:
        photos = bot.get_user_profile_photos(m.from_user.id)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            return bot.send_photo(m.chat.id, file_id, caption=caption, reply_markup=join_kb())
    except:
        pass

    bot.send_message(m.chat.id, caption, reply_markup=join_kb())

@bot.callback_query_handler(func=lambda c: c.data == "verify")
def verify(c):
    msg = bot.send_message(c.message.chat.id, "⏳ CHECKING...\n▱▱▱▱▱▱▱▱▱▱ 0%")
    steps = ["▰▰▱▱▱▱▱▱▱▱ 20%", "▰▰▰▰▱▱▱▱▱▱ 40%", "▰▰▰▰▰▰▱▱▱▱ 60%", "▰▰▰▰▰▰▰▰▱▱ 80%", "▰▰▰▰▰▰▰▰▰▰ 100%"]
    for s in steps:
        time.sleep(0.35)
        try:
            bot.edit_message_text(f"⏳ CHECKING...\n{s}", c.message.chat.id, msg.message_id)
        except:
            pass

    if not is_joined(c.from_user.id):
        return bot.send_message(c.message.chat.id, "❌ Pehle sab channels join karo 😡", reply_markup=join_kb())

    st = settings()
    sent = bot.send_message(
        c.message.chat.id,
        "💋 HERE IS YOUR REWARD 😈💗\n\n⏳ Delete in 5 minutes.",
        reply_markup=reward_kb(),
        protect_content=not st.get("allow_forward", False)
    )

    Timer(300, lambda: safe_delete(c.message.chat.id, sent.message_id)).start()

def safe_delete(chat_id, msg_id):
    try:
        bot.delete_message(chat_id, msg_id)
    except:
        pass

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "➕ Add Channel")
def ask_add_channel(m):
    msg = bot.send_message(m.chat.id, "Send:\nNAME | @username")
    bot.register_next_step_handler(msg, add_channel)

def add_channel(m):
    try:
        name, username = [x.strip() for x in m.text.split("|")]
        data = channels()
        data.append({"name": name, "username": username})
        save(CHANNELS_FILE, data)
        bot.send_message(m.chat.id, "✅ Channel added")
    except:
        bot.send_message(m.chat.id, "❌ Format wrong")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "❌ Remove Channel")
def ask_remove_channel(m):
    msg = bot.send_message(m.chat.id, "Send channel number:")
    bot.register_next_step_handler(msg, remove_channel)

def remove_channel(m):
    try:
        data = channels()
        removed = data.pop(int(m.text.strip()) - 1)
        save(CHANNELS_FILE, data)
        bot.send_message(m.chat.id, f"✅ Removed {removed['username']}")
    except:
        bot.send_message(m.chat.id, "❌ Invalid number")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📋 List Channels")
def list_channels(m):
    text = "📋 CHANNELS\n\n"
    for i, ch in enumerate(channels(), 1):
        text += f"{i}. {ch['name']} — {ch['username']}\n"
    bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🎁 Add Reward")
def ask_add_reward(m):
    msg = bot.send_message(m.chat.id, "Send:\nNAME | https://link.com")
    bot.register_next_step_handler(msg, add_reward)

def add_reward(m):
    try:
        name, url = [x.strip() for x in m.text.split("|")]
        data = rewards()
        data.append({"name": name, "url": url})
        save(REWARDS_FILE, data)
        bot.send_message(m.chat.id, "✅ Reward added")
    except:
        bot.send_message(m.chat.id, "❌ Format wrong")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🗑 Remove Reward")
def ask_remove_reward(m):
    msg = bot.send_message(m.chat.id, "Send reward number:")
    bot.register_next_step_handler(msg, remove_reward)

def remove_reward(m):
    try:
        data = rewards()
        removed = data.pop(int(m.text.strip()) - 1)
        save(REWARDS_FILE, data)
        bot.send_message(m.chat.id, f"✅ Removed {removed['name']}")
    except:
        bot.send_message(m.chat.id, "❌ Invalid number")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📦 List Rewards")
def list_rewards(m):
    text = "📦 REWARDS\n\n"
    for i, r in enumerate(rewards(), 1):
        text += f"{i}. {r['name']} — {r['url']}\n"
    bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📊 Stats")
def stats(m):
    st = "ON ✅" if settings().get("allow_forward", False) else "OFF 🔒"
    bot.send_message(m.chat.id, f"📊 Users: {len(load(USERS_FILE, []))}\n🔁 Forward: {st}")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📢 Broadcast")
def ask_broadcast(m):
    msg = bot.send_message(m.chat.id, "Broadcast text bhejo:")
    bot.register_next_step_handler(msg, do_broadcast)

def do_broadcast(m):
    sent = failed = 0
    for uid in load(USERS_FILE, []):
        try:
            bot.send_message(uid, m.text)
            sent += 1
        except:
            failed += 1
    bot.send_message(m.chat.id, f"✅ Broadcast done\nSent: {sent}\nFailed: {failed}")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🔘 Button Broadcast")
def ask_button_broadcast(m):
    msg = bot.send_message(m.chat.id, "Format:\nMessage | Button Text | https://link.com")
    bot.register_next_step_handler(msg, do_button_broadcast)

def do_button_broadcast(m):
    try:
        text, btn, url = [x.strip() for x in m.text.split("|")]
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(btn, url=url))
        sent = failed = 0
        for uid in load(USERS_FILE, []):
            try:
                bot.send_message(uid, text, reply_markup=kb)
                sent += 1
            except:
                failed += 1
        bot.send_message(m.chat.id, f"✅ Button broadcast done\nSent: {sent}\nFailed: {failed}")
    except:
        bot.send_message(m.chat.id, "❌ Format wrong")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🖼 Media Broadcast")
def media_hint(m):
    bot.send_message(m.chat.id, "Photo/video caption ke sath bhejo, sab users ko jayega.")

@bot.message_handler(content_types=["photo", "video"])
def media_broadcast(m):
    if not is_admin(m.from_user.id):
        return
    sent = failed = 0
    for uid in load(USERS_FILE, []):
        try:
            if m.photo:
                bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption or "")
            else:
                bot.send_video(uid, m.video.file_id, caption=m.caption or "")
            sent += 1
        except:
            failed += 1
    bot.send_message(m.chat.id, f"✅ Media broadcast done\nSent: {sent}\nFailed: {failed}")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🔐 Forward OFF/ON")
def toggle_forward(m):
    st = settings()
    st["allow_forward"] = not st.get("allow_forward", False)
    save(SETTINGS_FILE, st)
    status = "ON ✅ Reward forward ho sakega" if st["allow_forward"] else "OFF 🔒 Reward forward nahi hoga"
    bot.send_message(m.chat.id, status)

def run():
    print("Telegram bot polling started...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print("BOT ERROR:", e)
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
