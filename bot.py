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
        '🤖 *Redirect Bot Commands:*\n\n'
        '/set `<id>` `<url>` - Set redirect for /group/<id>\n'
        '/get `<id>` - Get current target\n'
        '/del `<id>` - Delete mapping\n'
        '/list - List all active redirects\n\n'
        '_Example: /set 1 https://chat.whatsapp.com/ABC123_',
        parse_mode='Markdown'
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
    await update.message.reply_text(
        f'✅ *Saved!*\n\n'
        f'🔗 {BASE_URL}/group/{group_id}\n'
        f'➡️ {url}',
        parse_mode='Markdown'
    )

async def get_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text('Usage: /get <id>')
        return
    
    group_id = context.args[0]
    target = r.get(f'group:{group_id}')
    
    if target:
        target_url = target.decode("utf-8")
        await update.message.reply_text(
            f'📋 *Group {group_id}:*\n\n'
            f'🔗 {BASE_URL}/group/{group_id}\n'
            f'➡️ {target_url}',
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f'❌ No mapping found for group {group_id}.')

async def del_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text('Not authorized.')
        return
    
    if len(context.args) < 1:
        await update.message.reply_text('Usage: /del <id>')
        return
    
    group_id = context.args[0]
    r.delete(f'group:{group_id}')
    await update.message.reply_text(f'✅ Deleted mapping for group {group_id}.')

async def list_targets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text('Not authorized.')
        return
    
    try:
        # Get all group keys
        keys = r.keys('group:*')
        if not keys:
            await update.message.reply_text('No redirects set yet.')
            return
        
        message = '📋 *Active Redirects:*\n\n'
        for key in keys[:20]:  # Limit to 20 to avoid message too long
            group_id = key.decode('utf-8').replace('group:', '')
            target = r.get(key)
            if target:
                target = target.decode('utf-8')
                message += f'• `/group/{group_id}` → {target[:50]}...\n'
        
        if len(keys) > 20:
            message += f'\n_... and {len(keys) - 20} more_'
        
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

def main():
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_target))
    app.add_handler(CommandHandler("get", get_target))
    app.add_handler(CommandHandler("del", del_target))
    app.add_handler(CommandHandler("list", list_targets))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

