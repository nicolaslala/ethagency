from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = "8287479790:AAGbpC8or7Jx940J3WLXmDLZIq4GpbuEZZE"
ADMIN_ID = 8744987991

SELECTING_USER, CHATTING = range(2)
conversations = {}
current_chat = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        return await show_user_list(update, context)
    else:
        await update.message.reply_text(f"👋 Hi {user.first_name}! Send your message here and I'll reply personally.")

async def show_user_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for uid, data in conversations.items():
        name = data.get("name", "Unknown")
        username = data.get("username", "")
        unread = sum(1 for m in data.get("messages", []) if not m["read"])
        label = f"📩 {name}"
        if username:
            label += f" (@{username})"
        if unread > 0:
            label += f" [{unread} new]"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"chat_{uid}")])
    if not keyboard:
        await update.message.reply_text("📭 No messages yet. Share @ethagent_bot in your groups!")
        return ConversationHandler.END
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh")])
    await update.message.reply_text("📋 Your Conversations:\nTap a user to reply:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_USER

async def select_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "refresh":
        await query.message.delete()
        return await show_user_list(update, context)
    if query.data.startswith("chat_"):
        user_id = int(query.data.split("_")[1])
        current_chat[ADMIN_ID] = user_id
        for msg in conversations[user_id]["messages"]:
            msg["read"] = True
        data = conversations[user_id]
        history = ""
        for m in data["messages"][-5:]:
            prefix = "🧑" if m["from_user"] else "👤"
            history += f"{prefix}: {m['text'][:40]}\n"
        await query.message.reply_text(
            f"💬 Chatting: {data['name']} (@{data.get('username', 'no username')})\n\n{history}\n✏️ Type reply. /back for list."
        )
        return CHATTING

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in conversations:
        conversations[user.id] = {"name": user.full_name, "username": user.username or "", "messages": []}
    conversations[user.id]["messages"].append({"text": update.message.text, "from_user": True, "read": False})
    await update.message.reply_text("✅ Got it! I'll reply soon.")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if update.message.text == '/back':
        current_chat.pop(ADMIN_ID, None)
        return await show_user_list(update, context)
    target_user = current_chat.get(ADMIN_ID)
    if not target_user:
        await update.message.reply_text("⚠️ No user selected. Send /start")
        return ConversationHandler.END
    await context.bot.send_message(chat_id=target_user, text=update.message.text)
    conversations[target_user]["messages"].append({"text": update.message.text, "from_user": False, "read": True})
    await update.message.reply_text(f"✅ Sent!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_chat.pop(ADMIN_ID, None)
    return await show_user_list(update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    admin_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_USER: [CallbackQueryHandler(select_user)],
            CHATTING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_reply),
                CommandHandler('back', cancel)
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    user_handler = MessageHandler(filters.TEXT & filters.CHAT_TYPE.private, handle_user_message)
    app.add_handler(admin_handler)
    app.add_handler(user_handler)
    print("✅ Bot is running!")
    app.run_polling()

if __name__ == '__main__':
    main()
