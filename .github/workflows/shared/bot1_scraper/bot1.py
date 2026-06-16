import os
import sys
import asyncio
import logging
import aiohttp
import re
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.database import is_post_copied, mark_post_copied, init_db

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT1_TOKEN')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL')
SOURCE_CHANNELS = [ch.strip().lstrip('@') for ch in os.getenv('SOURCE_CHANNELS', '').split(',') if ch.strip()]
CHANNEL_NAME = os.getenv('CHANNEL_DISPLAY_NAME', 'کاریابی ایران')
CHANNEL_USERNAME = os.getenv('TARGET_CHANNEL', '@yourchannel')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL_SECONDS', '300'))

KEYWORDS = [
    'استخدام', 'کارجو', 'فریلنس', 'پروژه', 'همکار',
    'حقوق', 'دورکاری', 'job', 'hire', 'فرصت شغلی',
    'نیازمند', 'جذب نیرو', 'موقعیت شغلی', 'developer',
    'طراح', 'برنامه نویس', 'حسابدار', 'بازاریاب'
]

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def is_relevant(text):
    t = text.lower()
    return any(kw.lower() in t for kw in KEYWORDS)

def format_post(text):
    sep = "\n" + "─" * 28 + "\n"
    footer = f"{sep}📢 {CHANNEL_NAME}\n🔗 {CHANNEL_USERNAME}\n💼 برای ثبت آگهی به ربات مراجعه کن 👆"
    return f"{text}{footer}"

async def send_message(session, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": TARGET_CHANNEL, "text": text[:4096], "parse_mode": "HTML", "disable_web_page_preview": True}
    async with session.post(url, json=payload) as resp:
        data = await resp.json()
        return data.get('ok', False)

async def fetch_channel(session, channel):
    try:
        async with session.get(f"https://t.me/s/{channel}", timeout=aiohttp.ClientTimeout(total=15)) as resp:
            html = await resp.text()
        posts = []
        matches = re.findall(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        ids = re.findall(r'data-post="[^/]+/(\d+)"', html)
        for msg_id, match in zip(ids, matches):
            clean = re.sub(r'<br\s*/?>', '\n', match)
            clean = re.sub(r'<[^>]+>', '', clean).strip()
            if clean:
                posts.append({'id': int(msg_id), 'text': clean})
        return posts
    except Exception as e:
        logger.warning(f"خطا در {channel}: {e}")
        return []

async def check_channel(session, channel):
    posts = await fetch_channel(session, channel)
    for post in posts:
        if is_post_copied(channel, post['id']):
            continue
        if not is_relevant(post['text']):
            continue
        success = await send_message(session, format_post(post['text']))
        if success:
            mark_post_copied(channel, post['id'])
            logger.info(f"✅ پست {post['id']} از @{channel} کپی شد")
            await asyncio.sleep(2)

async def main():
    init_db()
    logger.info(f"✅ ربات ۱ شروع کرد — {len(SOURCE_CHANNELS)} کانال")
    async with aiohttp.ClientSession() as session:
        while True:
            for channel in SOURCE_CHANNELS:
                await check_channel(session, channel)
                await asyncio.sleep(3)
            logger.info(f"✅ بررسی تموم شد — {CHECK_INTERVAL}s تا بعدی")
            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    asyncio.run(main())
