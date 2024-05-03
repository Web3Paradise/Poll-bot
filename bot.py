import datetime
import logging
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define states
SELECTING_ACTION, ENTERING_QUESTION, ENTERING_OPTIONS, ENTERING_DATE, ENTERING_TIME, ANONYMOUS, LIMIT_VOTES = range(7)

# Store poll data
poll_data = {}

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Welcome to the Poll Bot! To create a poll, use the /poll command."
    )

# Create poll command handler
def poll(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Please enter your poll question."
    )
    return ENTERING_QUESTION

# Receive poll question handler
def receive_question(update: Update, context: CallbackContext) -> None:
    poll_data[update.message.chat_id] = {"question": update.message.text, "options": [], "users_voted": [], "anonymous": False, "limit_votes": False}

    update.message.reply_text(
        f"Your poll question is: {poll_data[update.message.chat_id]['question']}\n\nNow send the options separated by commas."
    )
    return ENTERING_OPTIONS

# Receive poll options handler
def receive_options(update: Update, context: CallbackContext) -> None:
    options = update.message.text.split(',')
    poll_data[update.message.chat_id]['options'] = options

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Yes", callback_data="anonymous_yes"),
                                          InlineKeyboardButton("No", callback_data="anonymous_no")]])

    update.message.reply_text(
        f"Your poll options are: {', '.join(options)}\n\nDo you want the votes to be anonymous?",
        reply_markup=reply_markup
    )
    return ANONYMOUS

# Anonymous voting handler
def anonymous(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id

    if query.data == "anonymous_yes":
        poll_data[chat_id]['anonymous'] = True

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Yes", callback_data="limit_yes"),
                                          InlineKeyboardButton("No", callback_data="limit_no")]])

    query.message.edit_text(
        query.message.text + f"\n\nDo you want to limit the number of votes per user?",
        reply_markup=reply_markup
    )
    return LIMIT_VOTES

# Limit votes handler
def limit_votes(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id

    if query.data == "limit_yes":
        poll_data[chat_id]['limit_votes'] = True

    query.message.edit_text(
        query.message.text,
        reply_markup=None
    )

    if poll_data[chat_id]['limit_votes']:
        update.message.reply_text(
            "Please enter the maximum number of votes per user."
        )
        return SELECTING_ACTION
    else:
        return create_poll(update, context)

# Receive maximum votes handler
def receive_max_votes(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    max_votes = int(update.message.text)
    poll_data[chat_id]['max_votes'] = max_votes

    return create_poll(update, context)

# Create poll
def create_poll(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    options = "\n".join([f"{index+1}. {option}" for index, option in enumerate(poll_data[chat_id]['options'])])
    poll_question = poll_data[chat_id]['question']

    update.message.reply_text(
        f"Poll created successfully!\n\n{poll_question}\n\n{options}"
    )

    return SELECTING_ACTION

# Error handler
def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main() -> None:
    updater = Updater("YOUR_TELEGRAM_BOT_TOKEN")

    dispatcher = updater.dispatcher

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('poll', poll)],
        states={
            SELECTING_ACTION: [
                MessageHandler(Filters.regex('^Create Poll$'), poll),
                MessageHandler(Filters.regex('^Cancel$'), cancel),
            ],
            ENTERING_QUESTION: [MessageHandler(Filters.text & ~Filters.command, receive_question)],
            ENTERING_OPTIONS: [MessageHandler(Filters.text & ~Filters.command, receive_options)],
            ANONYMOUS: [CallbackQueryHandler(anonymous)],
            LIMIT_VOTES: [CallbackQueryHandler(limit_votes)],
            ENTERING_DATE: [MessageHandler(Filters.text & ~Filters.command, receive_date)],
            ENTERING_TIME: [MessageHandler(Filters.text & ~Filters.command, receive_time)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
