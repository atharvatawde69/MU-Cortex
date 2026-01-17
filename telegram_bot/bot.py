"""Main Telegram bot file using Aiogram v3."""

import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
import os

from handlers import FileProcessor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Get bot token from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Get channel ID from environment
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# Subject tag to code mapping
SUBJECT_TAG_TO_CODE = {
    "artificialintelligence": "CSC503",
    "computernetworks": "CSC501",
}

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Initialize file processor
processor = FileProcessor(bot)


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    welcome_text = (
        "👋 Welcome to MU-Cortex Bot!\n\n"
        "📚 Upload your study materials (PDFs or images) with hashtags in the caption.\n\n"
        "Example:\n"
        "Upload a PDF with caption: #OperatingSystems #Module1\n\n"
        "The bot will process your files and tag them accordingly.\n\n"
        "Use /help for more information."
    )
    await message.reply(welcome_text)


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    help_text = (
        "📖 How to upload notes:\n\n"
        "1. Upload a PDF document or image\n"
        "2. Add hashtags in the caption (e.g., #SubjectName #Module2)\n"
        "3. The bot will confirm receipt and process your file\n\n"
        "Supported formats:\n"
        "• PDF documents\n"
        "• Images (JPG, PNG, etc.)\n\n"
        "Note: Files are currently being logged. Full processing will be available soon."
    )
    await message.reply(help_text)


# ======================
# CHANNEL POST HANDLERS
# ======================

@dp.channel_post(F.document)
async def handle_channel_document(message: Message):
    logger.info(f"[CHANNEL] Document received: {message.document.file_name}")

    caption = message.caption or ""
    hashtags = [word for word in caption.split() if word.startswith('#')]

    if not hashtags:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=(
                "⚠️ Missing tags.\n\n"
                "Please REPLY to this file with:\n"
                "#SubjectName #2019Scheme"
            ),
            reply_to_message_id=message.message_id
        )
        return

    logger.info(
        f"[CHANNEL] File: {message.document.file_name}, "
        f"Size: {message.document.file_size}, "
        f"Tags: {hashtags}"
    )

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=(
            f"✅ Received: {message.document.file_name}\n"
            f"Tags: {', '.join(hashtags) if hashtags else 'No tags'}\n"
            f"Processing..."
        )
    )


@dp.channel_post(F.photo)
async def handle_channel_photo(message: Message):
    photo = message.photo[-1]

    caption = message.caption or ""
    hashtags = [word for word in caption.split() if word.startswith('#')]

    if not hashtags:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=(
                "⚠️ Missing tags.\n\n"
                "Please REPLY to this file with:\n"
                "#SubjectName #2019Scheme"
            ),
            reply_to_message_id=message.message_id
        )
        return

    logger.info(f"[CHANNEL] Photo received: {photo.file_id}")
    logger.info(f"[CHANNEL] Tags: {hashtags}")

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=(
            "✅ Received image\n"
            f"Tags: {', '.join(hashtags) if hashtags else 'No tags'}\n"
            "Processing..."
        )
    )


@dp.channel_post(F.reply_to_message & (F.reply_to_message.document | F.reply_to_message.photo))
async def handle_channel_reply_with_tags(message: Message):
    """Handle replies to channel posts with documents/photos to add tags."""
    reply_text = message.text or ""
    hashtags = [word for word in reply_text.split() if word.startswith('#')]

    if hashtags:
        logger.info(f"[CHANNEL] Tags received via reply: {hashtags}")
        
        # Extract subject tag and scheme_id from hashtags
        # Expected format: #SubjectName #SchemeID (e.g., #OperatingSystems #2019Scheme)
        subject_tag = hashtags[0].replace('#', '').lower() if len(hashtags) > 0 else ""
        scheme_tag = hashtags[1].replace('#', '').lower() if len(hashtags) > 1 else ""
        
        # Look up subject code from tag
        subject_code = SUBJECT_TAG_TO_CODE.get(subject_tag)
        if not subject_code:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text="❌ Unknown subject. Please use a valid subject tag.",
                reply_to_message_id=message.message_id
            )
            return
        
        # Normalize scheme_id: extract "2019" or "2024" from tags like "2019scheme", "2024scheme", etc.
        if "2019" in scheme_tag:
            scheme_id = "2019"
        elif "2024" in scheme_tag:
            scheme_id = "2024"
        else:
            scheme_id = scheme_tag  # Fallback to original if no match
        
        tags = [tag.replace('#', '') for tag in hashtags]
        
        # Process document only if replying to a document (not photo)
        if message.reply_to_message and message.reply_to_message.document:
            await processor.process_document(
                message=message.reply_to_message,
                subject_code=subject_code,
                scheme_id=scheme_id,
                tags=tags,
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text="✅ Tags received. Processing file..."
            )
    else:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text="⚠️ Tags still missing. Please include scheme and subject hashtags.",
            reply_to_message_id=message.message_id
        )




async def main() -> None:
    """Start the bot with polling."""
    logger.info("Starting MU-Cortex Telegram bot...")
    
    try:
        # Start polling
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
