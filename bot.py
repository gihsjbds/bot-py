import os
import redis
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
# Redis connection
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    print("Error: REDIS_URL not set")
    exit(1)

r = redis.from_url(redis_url)
token = os.getenv('TELEGRAM_BOT_TOKEN')
admin_chat_id = os.getenv('ADMIN_CHAT_ID')

if not token:
    print("Error: TELEGRAM_BOT_TOKEN not set")
    exit(1)

BASE_URL = os.getenv('PUBLIC_BASE_URL', 'https://your-domain.vercel.app')

def is_admin(chat_id):
    if not admin_chat_id:
        return True
    return str(chat_id) == admin_chat_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Commands:\n'
        '/set <id> <url> - set target for /group/<id>\n'
        '/get <id> - get current target\n'
        '/del <id> - delete mapping'
    )

async def set_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text('Not authorized.')
        return
    
    if len(context.args) < 2:
        await update.message.reply_text('Usage: /set <id> <url>')
        return
    
    group_id = context.args[0]
    url = ' '.join(context.args[1:])
    
    if not url.startswith('http://') and not url.startswith('https://'):
        await update.message.reply_text('URL must start with http:// or https://')
        return
    
    r.set(f'group:{group_id}', url)
    await update.message.reply_text(f'Saved: {BASE_URL}/group/{group_id} -> {url}')

async def get_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text('Usage: /get <id>')
        return
    
    group_id = context.args[0]
    target = r.get(f'group:{group_id}')
    
    if target:
        await update.message.reply_text(f'Current: {group_id} -> {target.decode("utf-8")}')
    else:
        await update.message.reply_text('No mapping found.')

async def del_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text('Not authorized.')
        return
    
    if len(context.args) < 1:
        await update.message.reply_text('Usage: /del <id>')
        return
    
    group_id = context.args[0]
    r.delete(f'group:{group_id}')
    await update.message.reply_text(f'Deleted mapping for {group_id}.')

def main():
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_target))
    app.add_handler(CommandHandler("get", get_target))
    app.add_handler(CommandHandler("del", del_target))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

