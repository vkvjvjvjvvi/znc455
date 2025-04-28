from telethon import TelegramClient, events
import asyncio
import time
import random
import datetime

# بيانات الحساب الشخصي
api_id = 27404031
api_hash = '82e969739914ccf489e11db575be4d46'

# بيانات البوت الرسمي (من BotFather)
bot_token = '7114378456:AAEptlcJpGG80v_xGHUTXC11i3PpfEyzQ00'

# عملاء منفصلين
user_client = TelegramClient('user_session', api_id, api_hash)
bot_client = TelegramClient('bot_session', api_id, api_hash)

# متغيرات التحكم
replied_users = {}
spam_users = {}
total_replies = 0
paused = False
user_message_counts = {}

# رد واحد رئيسي
main_reply = "أهلاً بك، {name}! أنا بوت الرد التلقائي. كيف يمكنني مساعدتك؟"

# قائمة التحذيرات
warning_replies = [
    "يرجى عدم إرسال العديد من الرسائل بشكل متتالي.",
    "الرجاء الانتظار قليلاً قبل إرسال المزيد من الرسائل.",
    "أنا هنا لمساعدتك، لكن أرجو منك التخفيف قليلاً.",
    "إذا كنت بحاجة للمساعدة، لا تتردد في طلب ذلك!"
]

def log_message(message):
    with open("log.txt", "a", encoding="utf-8") as file:
        file.write(f"{message}\n")

@user_client.on(events.NewMessage)
async def auto_reply(event):
    global total_replies, paused

    if not event.is_private or paused:
        return

    sender = await event.get_sender()
    name = sender.first_name or "صديقي"
    now = time.time()
    
    # تتبع عدد الرسائل لما يستخدم كل مستخدم
    user_message_counts.setdefault(sender.id, [])
    user_message_counts[sender.id].append(now)

    # حذف الرسائل القديمة (أكثر من دقيقة)
    user_message_counts[sender.id] = [
        msg_time for msg_time in user_message_counts[sender.id]
        if now - msg_time <= 60
    ]

    # إذا داز أكثر من 10 رسائل خلال دقيقة ➔ نوقفه
    if len(user_message_counts[sender.id]) >= 25:
        spam_users[sender.id] = now
        log_message(f"[{time.ctime(now)}] سبام: {sender.id} تم حظره مؤقتاً ساعة.")
        print(f"مستخدم سبامر {sender.id} تم توقيفه مؤقتاً.")
        return

    # الرد بعد أول رسالة
    if len(user_message_counts[sender.id]) == 1:
        await event.respond(main_reply.format(name=name))
        replied_users[sender.id] = now  # تحديث زمن الرد
        total_replies += 1
        log_message(f"[{time.ctime(now)}] رد إلى {name} ({sender.id}): {main_reply.format(name=name)}")
        print(f"رد على {sender.id} | مجموع الردود: {total_replies}")
        
    # ردود تحذيرية بعد الرسالة الأولى
    elif len(user_message_counts[sender.id]) % 3 == 0:  # بعد كل ثلاث رسائل
        warning_reply = random.choice(warning_replies).format(name=name)
        await event.respond(warning_reply)
        log_message(f"[{time.ctime(now)}] تحذير: {name} ({sender.id}) بسبب الحاحه.")

@bot_client.on(events.NewMessage(pattern='/start'))
async def handle_start(event):
    global paused
    paused = False
    await event.respond("✅ تم تشغيل الردود التلقائية.")
    log_message(f"[{time.ctime()}] استلم أمر /start.")
    print("تم تشغيل الردود عن طريق بوت!")

@bot_client.on(events.NewMessage(pattern='/stop'))
async def handle_stop(event):
    global paused
    paused = True
    await event.respond("⛔ تم إيقاف الردود التلقائية مؤقتاً.")
    log_message(f"[{time.ctime()}] استلم أمر /stop.")
    print("تم إيقاف الردود عن طريق بوت!")

@bot_client.on(events.NewMessage(pattern='/status'))
async def handle_status(event):
    status_text = "✅ شغال" if not paused else "⛔ متوقف مؤقتا"
    await event.respond(f"حالة البوت: {status_text}\nعدد الردود الكلية: {total_replies}")
    log_message(f"[{time.ctime()}] استلم أمر /status.")
    print("تم طلب الحالة.")
bot_client.on(events.NewMessage(pattern='/reset'))
async def handle_reset(event):
    global replied_users, spam_users, total_replies, user_message_counts
    replied_users = {}
    spam_users = {}
    user_message_counts = {}
    total_replies = 0
    await event.respond("♻️ تم تصفير جميع البيانات.")
    log_message(f"[{time.ctime()}] استلم أمر /reset وتم تصفير العدادات.")
    print("تم تصفير العدادات.")

@bot_client.on(events.NewMessage(pattern='/help'))
async def handle_help(event):
    help_text = (
        "💡 كيفية استخدام البوت:\n"
        "- `/start` - لتشغيل الردود التلقائية.\n"
        "- `/stop` - لإيقاف الردود التلقائية مؤقتًا.\n"
        "- `/status` - لمعرفة حالة البوت وعداد الردود الكلية.\n"
        "- `/reset` - لتصفير جميع البيانات.\n"
        "تجنب إرسال الكثير من الرسائل في وقت قصير حتى لا تُعتبر سبام."
    )
    await event.respond(help_text)
    log_message(f"[{time.ctime()}] استلم أمر /help.")
    print("تم طلب المساعدة.")

async def auto_reset():
    while True:
        now = datetime.datetime.now()
        next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        wait_seconds = (next_reset - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        
        global replied_users, spam_users, total_replies, user_message_counts
        replied_users = {}
        spam_users = {}
        user_message_counts = {}
        total_replies = 0
        log_message(f"[{time.ctime()}] تم التصفير التلقائي اليومي.")
        print("✅ تم التصفير التلقائي بالليل.")

 #تشغيل الكل
async def main():
    await user_client.start()
    await bot_client.start(bot_token=bot_token)
    print("✅ الحساب الشخصي اشتغل.")
    print("✅ البوت الرسمي اشتغل.")

   #  تشغيل المهام مع بعض
    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected(),
        auto_reset()
    )

# بدء حلقة الأحداث
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.close()
