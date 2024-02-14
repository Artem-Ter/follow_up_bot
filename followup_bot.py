import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from olx_scraper import get_new_posts_file
from finance import get_report
from utils import get_file_path

load_dotenv()

secret_token = os.getenv('TOKEN')
chat_id = os.getenv('BOT_CHAT_ID')


def new_ads(update, context) -> None:
    """Bot send file with new posts to Telegram chat"""
    file_name = get_new_posts_file()
    # Send the XLS file
    with open(file_name, 'rb') as file:
        context.bot.send_document(chat_id=chat_id, document=file)
    os.remove(file_name)


def wake_up(update, context) -> None:
    """Bot send message to chat and send photo from func get_new_image"""
    button = ReplyKeyboardMarkup([['/casas_terrenos']], resize_keyboard=True)
    context.bot.send_message(
        chat_id=chat_id,
        text='Bot is active',
        reply_markup=button
    )


def handle_document(update, context) -> None:
    document = update.message.document
    file_id = document.file_id
    file = context.bot.get_file(file_id)
    downloaded_file_path = get_file_path('trading_data.csv')
    file.download(downloaded_file_path)
    report_file_path = get_report(downloaded_file_path)
    with open(report_file_path, 'rb') as file:
        context.bot.send_document(chat_id=chat_id, document=file)
    os.remove(downloaded_file_path)
    os.remove(report_file_path)


def main():
    updater = Updater(secret_token)
    # Get the dispatcher from the bot
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler('start', wake_up))
    dp.add_handler(CommandHandler('casas_terrenos', new_ads))
    dp.add_handler(MessageHandler(filters.Filters.attachment, handle_document))

    # Start polling
    updater.start_polling(11)

    # Run the bot until you send a signal to stop it
    updater.idle()


if __name__ == '__main__':
    main()
