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
REFS_FILE = "refs.json"

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot alive"

def load(file, default):
    if not os.path.exists(file):
        save(file, default)
        return default
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return default

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def users(): return load(USERS_FILE, [])
def channels(): return load(CHANNELS_FILE, [])
def rewards(): return load(REWARDS_FILE, [])
def refs(): return load(REFS_FILE, {})
def settings(): return load(SETTINGS_FILE, {"forward": False, "refer": False, "refer_need": 1})

def setup():
    load(USERS_FILE, [])
    load(CHANNELS_FILE, [])
    load(REWARDS_FILE, [])
    load(REFS_FILE, {})
    load(SETTINGS_FILE, {"forward": False, "refer": False, "refer_need": 1})

setup()

def is_admin(uid):
    return uid in ADMINS

def add_user(uid):
    data = users()
    if uid not in data:
        data.append(uid)
        save(USERS_FILE, data)

def is_joined(uid):
    for ch in channels():
        try:
            m = bot.get_chat_member(ch["username"], uid)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def admin_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Add Channel", "❌ Remove Channel")
    kb.row("📋 List Channels", "🎁 Add Reward")
    kb.row("🗑 Remove Reward", "📦 List Rewards")
    kb.row("📊 Stats", "📢 Broadcast")
    kb.row("🔘 Button Broadcast", "🖼 Media Broadcast")
    kb.row("🔐 Forward ON/OFF", "🔁 Refer ON/OFF")
    return kb

def join_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for ch in channels():
        btns.append(types.InlineKeyboardButton(ch["name"], url=f"https://t.me/{ch['username'].replace('@','')}"))
    for i in range(0, len(btns), 2):
        kb.add(*btns[i:i+2])
    kb.add(types.InlineKeyboardButton("🎯 VERIFY", callback_data="verify"))
    return kb

@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    add_user(uid)

    args = m.text.split()
    if len(args) > 1 and args[1] != str(uid):
        ref = args[1]
        data = refs()
        data.setdefault(ref, [])
        if str(uid) not in data[ref]:
            data[ref].append(str(uid))
        save(REFS_FILE, data)

    if is_admin(uid):
        bot.send_message(m.chat.id, "👑 ADMIN PANEL", reply_markup=admin_menu())

    text = f"""🔥 WELCOME {m.from_user.first_name} 😈💗

👥 Users: {len(users())}

💗 Join all channels
🎯 Then click VERIFY"""

    bot.send_message(m.chat.id, text, reply_markup=join_kb())

@bot.callback_query_handler(func=lambda c: c.data == "verify")
def verify(c):
    msg = bot.send_message(c.message.chat.id, "⏳ CHECKING...\n0%")
    for p in ["20%", "40%", "60%", "80%", "100%"]:
        time.sleep(0.3)
        try:
            bot.edit_message_text(f"⏳ CHECKING...\n{p}", c.message.chat.id, msg.message_id)
        except:
            pass

    if not is_joined(c.from_user.id):
        return bot.send_message(c.message.chat.id, "❌ Join all channels first", reply_markup=join_kb())

    st = settings()
    if st.get("refer"):
        need = int(st.get("refer_need", 1))
        done = len(refs().get(str(c.from_user.id), []))
        if done < need:
            link = f"https://t.me/{bot.get_me().username}?start={c.from_user.id}"
            return bot.send_message(c.message.chat.id, f"🔁 Refer required: {need}\n✅ Done: {done}\n\nYour link:\n{link}")

    send_rewards(c.message.chat.id)

def delete_later(chat_id, msg_id, sec=300):
    Timer(sec, lambda: safe_delete(chat_id, msg_id)).start()

def safe_delete(chat_id, msg_id):
    try:
        bot.delete_message(chat_id, msg_id)
    except:
        pass

def send_rewards(chat_id):
    st = settings()
    protect = not st.get("forward", False)

    for r in rewards():
        typ = r["type"]
        name = r["name"]
        value = r["value"]

        try:
            if typ == "text":
                msg = bot.send_message(chat_id, value, protect_content=protect)

            elif typ == "link":
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton(name, url=value))
                msg = bot.send_message(chat_id, "💋 YOUR REWARD 😈", reply_markup=kb, protect_content=protect)

            elif typ in ["file", "apk"]:
                msg = bot.send_document(chat_id, open(value, "rb"), caption=name, protect_content=protect)

            delete_later(chat_id, msg.message_id, 300)
        except:
            pass

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "➕ Add Channel")
def ask_add_channel(m):
    msg = bot.send_message(m.chat.id, "Format:\nNAME | @username")
    bot.register_next_step_handler(msg, add_channel)

def add_channel(m):
    try:
        name, username = [x.strip() for x in m.text.split("|")]
        data = channels()
        data.append({"name": name, "username": username})
        save(CHANNELS_FILE, data)
        bot.send_message(m.chat.id, "✅ Channel added")
    except:
        bot.send_message(m.chat.id, "❌ Wrong format")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "❌ Remove Channel")
def ask_remove_channel(m):
    msg = bot.send_message(m.chat.id, "Send channel number")
    bot.register_next_step_handler(msg, remove_channel)

def remove_channel(m):
    try:
        data = channels()
        removed = data.pop(int(m.text.strip()) - 1)
        save(CHANNELS_FILE, data)
        bot.send_message(m.chat.id, f"✅ Removed {removed['name']}")
    except:
        bot.send_message(m.chat.id, "❌ Invalid number")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📋 List Channels")
def list_channels(m):
    text = "📋 CHANNELS\n\n"
    for i, ch in enumerate(channels(), 1):
        text += f"{i}. {ch['name']} — {ch['username']}\n"
    bot.send_message(m.chat.id, text or "Empty")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🎁 Add Reward")
def ask_add_reward(m):
    msg = bot.send_message(m.chat.id, "Format:\nTYPE | NAME | VALUE\n\nTYPE: text / link / file / apk")
    bot.register_next_step_handler(msg, add_reward)

def add_reward(m):
    try:
        typ, name, value = [x.strip() for x in m.text.split("|", 2)]
        typ = typ.lower()
        if typ not in ["text", "link", "file", "apk"]:
            return bot.send_message(m.chat.id, "❌ Type wrong")
        data = rewards()
        data.append({"type": typ, "name": name, "value": value})
        save(REWARDS_FILE, data)
        bot.send_message(m.chat.id, "✅ Reward added")
    except:
        bot.send_message(m.chat.id, "❌ Wrong format")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🗑 Remove Reward")
def ask_remove_reward(m):
    msg = bot.send_message(m.chat.id, "Send reward number")
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
        text += f"{i}. {r['type']} | {r['name']} | {r['value']}\n"
    bot.send_message(m.chat.id, text or "Empty")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📊 Stats")
def stats(m):
    st = settings()
    bot.send_message(m.chat.id, f"👥 Users: {len(users())}\n📢 Channels: {len(channels())}\n🎁 Rewards: {len(rewards())}\n🔐 Forward: {st.get('forward')}\n🔁 Refer: {st.get('refer')}\n🎯 Refer Need: {st.get('refer_need')}")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📢 Broadcast")
def ask_broadcast(m):
    msg = bot.send_message(m.chat.id, "Send broadcast text")
    bot.register_next_step_handler(msg, do_broadcast)

def do_broadcast(m):
    sent = failed = 0
    for uid in users():
        try:
            bot.send_message(uid, m.text)
            sent += 1
        except:
            failed += 1
    bot.send_message(m.chat.id, f"✅ Sent: {sent}\n❌ Failed: {failed}")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🔘 Button Broadcast")
def ask_button_broadcast(m):
    msg = bot.send_message(m.chat.id, "Format:\nMESSAGE | BUTTON | LINK")
    bot.register_next_step_handler(msg, do_button_broadcast)

def do_button_broadcast(m):
    try:
        text, btn, link = [x.strip() for x in m.text.split("|", 2)]
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(btn, url=link))
        sent = failed = 0
        for uid in users():
            try:
                bot.send_message(uid, text, reply_markup=kb)
                sent += 1
            except:
                failed += 1
        bot.send_message(m.chat.id, f"✅ Sent: {sent}\n❌ Failed: {failed}")
    except:
        bot.send_message(m.chat.id, "❌ Wrong format")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🖼 Media Broadcast")
def media_broadcast_hint(m):
    bot.send_message(m.chat.id, "Now send photo/video with caption")

@bot.message_handler(content_types=["photo", "video"])
def media_broadcast(m):
    if not is_admin(m.from_user.id):
        return
    sent = failed = 0
    for uid in users():
        try:
            if m.photo:
                bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption or "")
            else:
                bot.send_video(uid, m.video.file_id, caption=m.caption or "")
            sent += 1
        except:
            failed += 1
    bot.send_message(m.chat.id, f"✅ Sent: {sent}\n❌ Failed: {failed}")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🔐 Forward ON/OFF")
def toggle_forward(m):
    st = settings()
    st["forward"] = not st.get("forward", False)
    save(SETTINGS_FILE, st)
    bot.send_message(m.chat.id, "✅ Forward ON" if st["forward"] else "🔒 Forward OFF")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🔁 Refer ON/OFF")
def toggle_refer(m):
    st = settings()
    st["refer"] = not st.get("refer", False)
    save(SETTINGS_FILE, st)
    bot.send_message(m.chat.id, "✅ Refer ON" if st["refer"] else "❌ Refer OFF")

@bot.message_handler(commands=["referon"])
def refer_on(m):
    if not is_admin(m.from_user.id):
        return
    st = settings()
    st["refer"] = True
    save(SETTINGS_FILE, st)
    bot.reply_to(m, "✅ Refer ON")

@bot.message_handler(commands=["referoff"])
def refer_off(m):
    if not is_admin(m.from_user.id):
        return
    st = settings()
    st["refer"] = False
    save(SETTINGS_FILE, st)
    bot.reply_to(m, "❌ Refer OFF")

@bot.message_handler(commands=["setrefer"])
def set_refer(m):
    if not is_admin(m.from_user.id):
        return
    try:
        n = int(m.text.split()[1])
        st = settings()
        st["refer_need"] = n
        save(SETTINGS_FILE, st)
        bot.reply_to(m, f"✅ Refer need set: {n}")
    except:
        bot.reply_to(m, "Use: /setrefer 3")

def run():
    print("Telegram bot polling started...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
