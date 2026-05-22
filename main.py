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

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive 💀"

# ---------- FILE ----------
def load(file, default=[]):
    if not os.path.exists(file):
        json.dump(default, open(file, "w"))
        return default
    try:
        return json.load(open(file))
    except:
        return default

def save(file, data):
    json.dump(data, open(file, "w"), indent=2)

# ---------- DEFAULT ----------
if not os.path.exists(CHANNELS_FILE):
    save(CHANNELS_FILE, [
        {"name":"💗 CHANNEL 1","username":"@verfiy_id"},
        {"name":"🔥 CHANNEL 2","username":"@funny_tym"},
        {"name":"⚡ CHANNEL 3","username":"@teamflux"},
        {"name":"💎 CHANNEL 4","username":"@tymm_pass"},
        {"name":"🎯 CHANNEL 5","username":"@masti_tym"},
        {"name":"🚀 CHANNEL 6","username":"@tmkc_okh"}
    ])

if not os.path.exists(REWARDS_FILE):
    save(REWARDS_FILE, [
        {"name":"💋 REWARD","url":"https://t.me/yourlink"}
    ])

# ---------- HELP ----------
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

# ---------- UI ----------
def join_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for ch in channels():
        btns.append(types.InlineKeyboardButton(
            ch["name"],
            url=f"https://t.me/{ch['username'].replace('@','')}"
        ))
    for i in range(0,len(btns),2):
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
    kb.row("Add Channel","Remove Channel")
    kb.row("List Channels","Add Reward")
    kb.row("Remove Reward","List Rewards")
    kb.row("Stats","Broadcast")
    return kb

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(m):
    add_user(m.from_user.id)

    if is_admin(m.from_user.id):
        bot.send_message(m.chat.id,"👑 ADMIN PANEL",reply_markup=admin_menu())

    # PROFILE PIC + WELCOME
    try:
        photos = bot.get_user_profile_photos(m.from_user.id)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            bot.send_photo(
                m.chat.id,
                file_id,
                caption=f"""🔥 WELCOME {m.from_user.first_name} 😈💗

👥 Users: {len(load(USERS_FILE,[]))}

💗 Join all channels
🎯 Then click VERIFY""",
                reply_markup=join_kb()
            )
            return
    except:
        pass

    bot.send_message(
        m.chat.id,
        f"""🔥 WELCOME {m.from_user.first_name} 😈💗

👥 Users: {len(load(USERS_FILE,[]))}

💗 Join all channels
🎯 Then click VERIFY""",
        reply_markup=join_kb()
    )

# ---------- VERIFY ANIMATION ----------
@bot.callback_query_handler(func=lambda c:c.data=="verify")
def verify(c):
    msg = bot.send_message(c.message.chat.id,"Checking... 0%")
    for i in range(1,6):
        time.sleep(0.3)
        try:
            bot.edit_message_text(
                f"Checking... {i*20}%",
                c.message.chat.id,
                msg.message_id
            )
        except:
            pass

    bot.send_message(c.message.chat.id,"💗 VERIFIED 😈",reply_markup=reward_kb())

# ---------- ADMIN ----------
@bot.message_handler(func=lambda m:is_admin(m.from_user.id))
def admin(m):
    t = m.text

    if t == "Add Channel":
        msg = bot.send_message(m.chat.id,"Name | @username")
        bot.register_next_step_handler(msg, add_channel)

    elif t == "Remove Channel":
        msg = bot.send_message(m.chat.id,"Send number")
        bot.register_next_step_handler(msg, remove_channel)

    elif t == "List Channels":
        text=""
        for i,ch in enumerate(channels(),1):
            text+=f"{i}. {ch['name']} - {ch['username']}\n"
        bot.send_message(m.chat.id,text)

    elif t == "Add Reward":
        msg = bot.send_message(m.chat.id,"Name | link")
        bot.register_next_step_handler(msg, add_reward)

    elif t == "Remove Reward":
        msg = bot.send_message(m.chat.id,"Send number")
        bot.register_next_step_handler(msg, remove_reward)

    elif t == "List Rewards":
        text=""
        for i,r in enumerate(rewards(),1):
            text+=f"{i}. {r['name']} - {r['url']}\n"
        bot.send_message(m.chat.id,text)

    elif t == "Stats":
        bot.send_message(m.chat.id,f"Users: {len(load(USERS_FILE,[]))}")

    elif t == "Broadcast":
        msg = bot.send_message(m.chat.id,"Send message")
        bot.register_next_step_handler(msg, do_broadcast)

# ---------- ACTIONS ----------
def add_channel(m):
    try:
        name,username = m.text.split("|")
        data = channels()
        data.append({"name":name.strip(),"username":username.strip()})
        save(CHANNELS_FILE,data)
        bot.send_message(m.chat.id,"Added")
    except:
        bot.send_message(m.chat.id,"Error")

def remove_channel(m):
    try:
        data = channels()
        data.pop(int(m.text)-1)
        save(CHANNELS_FILE,data)
        bot.send_message(m.chat.id,"Removed")
    except:
        bot.send_message(m.chat.id,"Error")

def add_reward(m):
    try:
        name,url = m.text.split("|")
        data = rewards()
        data.append({"name":name.strip(),"url":url.strip()})
        save(REWARDS_FILE,data)
        bot.send_message(m.chat.id,"Added")
    except:
        bot.send_message(m.chat.id,"Error")

def remove_reward(m):
    try:
        data = rewards()
        data.pop(int(m.text)-1)
        save(REWARDS_FILE,data)
        bot.send_message(m.chat.id,"Removed")
    except:
        bot.send_message(m.chat.id,"Error")

def do_broadcast(m):
    for uid in load(USERS_FILE,[]):
        try:
            bot.send_message(uid,m.text)
        except:
            pass
    bot.send_message(m.chat.id,"Broadcast done")

# ---------- RUN ----------
def run():
    while True:
        try:
            bot.infinity_polling()
        except:
            time.sleep(5)

if __name__=="__main__":
    Thread(target=run).start()
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))