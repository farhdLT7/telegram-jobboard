import os
import sys
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.database import init_db, create_order, get_order, update_order_status

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT2_TOKEN')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '0'))
PRICE_JOB = int(os.getenv('PRICE_JOB_AD', '150000'))
PRICE_FREE = int(os.getenv('PRICE_FREELANCE_PROJECT', '100000'))

CHOOSE_TYPE, GET_TITLE, GET_DESC, GET_CONTACT, GET_SALARY, CONFIRM = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("💼 آگهی استخدام", callback_data='type_job')],
          [InlineKeyboardButton("🚀 پروژه فریلنسری", callback_data='type_freelance')]]
    await update.message.reply_text(
        "👋 سلام! به ربات ثبت آگهی خوش اومدی.\n\nچه نوع آگهی میخوای ثبت کنی؟",
        reply_markup=InlineKeyboardMarkup(kb))
    return CHOOSE_TYPE

async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    t = query.data.replace('type_', '')
    context.user_data['type'] = t
    context.user_data['price'] = PRICE_JOB if t == 'job' else PRICE_FREE
    name = "آگهی استخدام" if t == 'job' else "پروژه فریلنسری"
    await query.edit_message_text(f"✅ نوع: {name}\n💰 هزینه: {context.user_data['price']:,} تومان\n\n📝 عنوان آگهی رو بنویس:")
    return GET_TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(update.message.text) < 5:
        await update.message.reply_text("❌ خیلی کوتاهه، بیشتر بنویس:")
        return GET_TITLE
    context.user_data['title'] = update.message.text.strip()
    await update.message.reply_text("📄 توضیحات کامل آگهی رو بنویس:")
    return GET_DESC

async def get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(update.message.text) < 20:
        await update.message.reply_text("❌ بیشتر توضیح بده:")
        return GET_DESC
    context.user_data['desc'] = update.message.text.strip()
    await update.message.reply_text("📞 اطلاعات تماس رو وارد کن (یوزرنیم، ایمیل یا تلفن):")
    return GET_CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['contact'] = update.message.text.strip()
    label = "💵 حقوق پیشنهادی" if context.user_data['type'] == 'job' else "💵 بودجه پروژه"
    await update.message.reply_text(f"{label} رو بنویس (یا بنویس: توافقی):")
    return GET_SALARY

async def get_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['salary'] = update.message.text.strip()
    d = context.user_data
    emoji = "💼" if d['type'] == 'job' else "🚀"
    preview = f"{emoji} {d['title']}\n\n{d['desc']}\n\n💰 {d['salary']}\n📞 {d['contact']}"
    kb = [[InlineKeyboardButton("✅ تایید و ثبت", callback_data='confirm')],
          [InlineKeyboardButton("❌ انصراف", callback_data='cancel')]]
    await update.message.reply_text(
        f"👀 پیش‌نمایش:\n\n{preview}\n\n─────────\n💳 هزینه: {d['price']:,} تومان\n\nتایید میکنی؟",
        reply_markup=InlineKeyboardMarkup(kb))
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'cancel':
        await query.edit_message_text("❌ لغو شد. برای شروع مجدد /start بزن")
        return ConversationHandler.END
    user = query.from_user
    d = context.user_data
    order_id = create_order(user.id, user.username or '', user.full_name or '', d['type'], d['title'], d['desc'], d['contact'], d['salary'], d['price'])
    await query.edit_message_text(
        f"✅ سفارش #{order_id} ثبت شد!\n\nمنتظر تایید ادمین باش. بعد از تایید در کانال منتشر میشه. ⏳")
    await notify_admin(order_id, context)
    return ConversationHandler.END

async def notify_admin(order_id, context):
    if not ADMIN_CHAT_ID:
        return
    order = get_order(order_id)
    emoji = "💼" if order['order_type'] == 'job' else "🚀"
    text = (f"🔔 سفارش جدید #{order_id}\n\n{emoji} {order['title']}\n\n"
            f"👤 {order['full_name']} (@{order['username']})\n"
            f"📝 {order['description'][:200]}\n"
            f"💰 {order['salary_or_budget']}\n📞 {order['contact']}\n"
            f"💳 {order['amount']:,} تومان")
    kb = [[InlineKeyboardButton("✅ تایید و انتشار", callback_data=f'approve_{order_id}'),
           InlineKeyboardButton("❌ رد", callback_data=f'reject_{order_id}')]]
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, reply_markup=InlineKeyboardMarkup(kb))

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_CHAT_ID:
        await query.answer("❌ شما ادمین نیستید!", show_alert=True)
        return
    action, order_id = query.data.split('_', 1)
    order_id = int(order_id)
    order = get_order(order_id)
    if action == 'approve':
        update_order_status(order_id, 'published')
        emoji = "💼" if order['order_type'] == 'job' else "🚀"
        type_name = "فرصت شغلی" if order['order_type'] == 'job' else "پروژه فریلنسری"
        post = (f"{emoji} {type_name}\n\n🔷 {order['title']}\n\n{order['description']}\n\n"
                f"💰 {order['salary_or_budget']}\n📞 {order['contact']}\n\n"
                f"─────────\n💼 ثبت آگهی: @{context.bot.username}")
        await context.bot.send_message(chat_id=TARGET_CHANNEL, text=post)
        await context.bot.send_message(chat_id=order['user_id'], text=f"🎉 آگهی #{order_id} تایید و در کانال منتشر شد!")
        await query.edit_message_text(f"✅ سفارش #{order_id} منتشر شد.")
    else:
        update_order_status(order_id, 'rejected')
        await context.bot.send_message(chat_id=order['user_id'], text=f"❌ آگهی #{order_id} رد شد. برای اطلاعات بیشتر با ادمین تماس بگیر.")
        await query.edit_message_text(f"❌ سفارش #{order_id} رد شد.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ لغو شد. با /start دوباره شروع کن.")
    return ConversationHandler.END

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_TYPE: [CallbackQueryHandler(choose_type, pattern='^type_')],
            GET_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            GET_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_desc)],
            GET_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            GET_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_salary)],
            CONFIRM: [CallbackQueryHandler(confirm, pattern='^(confirm|cancel)$')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_decision, pattern='^(approve|reject)_'))
    logger.info("✅ ربات ۲ شروع کرد")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
