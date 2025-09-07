import asyncio
import re
import logging
from datetime import datetime
import pytz
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, SessionPasswordNeededError, PhoneNumberInvalidError

# ==========================
# إعدادات الـ logging
# ==========================
logging.basicConfig(
    filename=f'bot_log_{datetime.now().strftime("%Y%m%d")}.log',
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# ==========================
# إعدادات الحسابات
# ==========================
accounts = [
    {
        "api_id": 26581091,
        "api_hash": "904d8f35a501653e53e08bf7268d1f1f",
        "phone_number": "+967736859022",  # الحساب 1
        "session_name": "user_session_1"
    },
    {
        "api_id": 29508560,
        "api_hash": "35d503fdaced793b421d35aa32a6edbf",
        "phone_number": "+966578568011",  # الحساب 2
        "session_name": "user_session_2"
    },
    {
        "api_id": 29723861,
        "api_hash": "89c8d8880d4c4ddd6e04c0f944619384",
        "phone_number": "+966540413854",  # الحساب 3
        "session_name": "user_session_3"
    },
]

# الحساب الرئيسي لإرسال التنبيهات
MAIN_ACCOUNT = {
    "api_id": 29508560,
    "api_hash": "35d503fdaced793b421d35aa32a6edbf",
    "phone_number": "+966578568011",
    "session_name": "main_session"
}

TARGET_GROUP = "@Alzuriqey711"

# ==========================
# التحقق من أرقام الهواتف
# ==========================
for account in accounts + [MAIN_ACCOUNT]:
    if not account["phone_number"] or account["phone_number"] == "+966xxxxxxxxx":
        logger.error(f"❌ يرجى تعيين رقم هاتف صحيح للحساب {account['session_name']}")
        print(f"❌ يرجى تعيين رقم هاتف صحيح للحساب {account['session_name']}")
        raise ValueError(f"رقم هاتف غير صحيح للحساب {account['session_name']}.")

# ==========================
# الكلمات المفتاحية
# ==========================
keywords = [
    "يحل", "من يحل واجب", "من يكتب بحث", "يسوي لي بحث",
    "تكفون حل", "احتاج احد يسوي لي", "اريد مختص يحل",
    "من يساعدني", "تقرير", "سكليف", "سكاليف", "اعذار", "اعذار طبية",
    "يسوي بحث", "حل واجب", "تلخيص", "شرح", "يحل لي", "واجب", "مساعدة", "واجبات",
    "ابغى حل", "يكتب", "ابغى بحث", "عذر", "يزين لي بحث", "يزين",
    "يسوي لي سكليف", "يجمل", "يسوي سكليف ينزل في صحتي",
    "يحل بحث", "يحل مشاريع"
]

# ==========================
# كلمات الإعلانات
# ==========================
advertiser_keywords = [
    "للتواصل", "عبر حسابنا", "مكتبنا", "خدمات طلابية",
    "بأسعار مناسبة", "تواصل خاص", "تواصل واتساب", "عرض احتياجك", "سجل طلبك",
    "https://", "t.me/", "wa.me/", "+966", "واتساب", "وتساب", "056", "053", "050", "054", "055", "058", "059"
]

# مجموعة لتتبع الرسائل المعالجة
processed_messages = set()

# ==========================
# دوال مساعدة
# ==========================
def is_advertiser_message(text):
    text_lower = text.lower()
    if len(text.splitlines()) >= 6:
        logger.info("تم تجاهل رسالة بسبب الطول (6 أسطر أو أكثر)")
        return True
    if any(kw in text_lower for kw in advertiser_keywords):
        logger.info(f"تم تجاهل رسالة تحتوي على كلمة إعلانية: {text_lower[:50]}...")
        return True
    if re.search(r"\+966\d{9}", text_lower) or re.search(r"\b05\d{8}\b", text_lower):
        logger.info(f"تم تجاهل رسالة تحتوي على رقم هاتف: {text_lower[:50]}...")
        return True
    return False

async def start_account(account, main_client, max_retries=5):
    retry_count = 0
    while retry_count < max_retries:
        try:
            client = TelegramClient(account["session_name"], account["api_id"], account["api_hash"])
            await client.start(phone=account["phone_number"])
            logger.info(f"✅ الحساب {account['phone_number']} جاهز ويعمل...")
            print(f"✅ الحساب {account['phone_number']} جاهز ويعمل...")

            async for dialog in client.iter_dialogs():
                logger.info(f"الحساب {account['phone_number']} يراقب: {dialog.title} (ID: {dialog.id})")
                print(f"الحساب {account['phone_number']} يراقب: {dialog.title} (ID: {dialog.id})")

            @client.on(events.NewMessage(chats=None))
            async def handler(event):
                message = event.message
                if not message.text:
                    return

                message_text = message.text.lower()
                unique_key = (event.chat_id, message.id)
                if unique_key in processed_messages:
                    return
                processed_messages.add(unique_key)

                matched_keyword = next((kw for kw in keywords if kw in message_text), None)
                if matched_keyword and not is_advertiser_message(message_text):
                    sender = await event.get_sender()
                    username = f"@{sender.username}" if getattr(sender, 'username', None) else "غير متوفر"
                    chat = await event.get_chat()
                    chat_title = getattr(chat, 'title', "غير متوفر")
                    chat_link = f"https://t.me/{chat.username}" if hasattr(chat, 'username') and chat.username else "قروب خاص"
                    mecca_tz = pytz.timezone("Asia/Riyadh")
                    message_time = message.date.astimezone(mecca_tz).strftime("%Y-%m-%d %H:%M:%S AST")

                    final_message = (
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📢 تنبيه جديد: زبون مهتم بالخدمة 📢\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"📝 نص الرسالة:\n{message.text}\n\n"
                        f"👤 اسم المستخدم: {username}\n"
                        f"🏷️ اسم القروب: {chat_title}\n"
                        f"🔗 رابط القروب: {chat_link}\n"
                        f"⏰ الوقت: {message_time}\n"
                        f"📱 الحساب المراقب: {account['phone_number']}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    )

                    for attempt in range(3):
                        try:
                            await main_client.send_message(TARGET_GROUP, final_message, parse_mode='markdown')
                            print(f"📢 أرسل تنبيه إلى {TARGET_GROUP}")
                            break
                        except FloodWaitError as e:
                            await asyncio.sleep(e.seconds)
                        except Exception as e:
                            if attempt == 2:
                                print(f"❌ فشل الإرسال: {e}")

            await client.run_until_disconnected()

        except (SessionPasswordNeededError, PhoneNumberInvalidError) as e:
            print(f"❌ خطأ تسجيل دخول {account['phone_number']}: {e}")
            break
        except Exception as e:
            retry_count += 1
            await asyncio.sleep(60)

async def main():
    while True:
        try:
            main_client = TelegramClient(MAIN_ACCOUNT["session_name"], MAIN_ACCOUNT["api_id"], MAIN_ACCOUNT["api_hash"])
            await main_client.start(phone=MAIN_ACCOUNT["phone_number"])
            print(f"✅ الحساب الرئيسي {MAIN_ACCOUNT['phone_number']} جاهز ويعمل...")

            tasks = [start_account(account, main_client) for account in accounts]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            print(f"❌ خطأ في الحساب الرئيسي: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
