import os
import logging
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from aiogram import Bot
from aiogram.types import Message
from dotenv import load_dotenv

from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Load root .env (Supabase credentials)
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Load telegram_bot/.env (Telegram credentials)
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


class FileProcessor:
    """Handles processing of Telegram-uploaded files."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def process_document(
        self,
        message: Message,
        subject_code: str,
        scheme_id: str,
        tags: List[str],
    ) -> Optional[dict]:
        """
        Store metadata for a PDF/document uploaded to Telegram.
        Assumes tags are already validated (two-step flow).
        """

        document = message.document

        file_id = document.file_id
        file_name = document.file_name
        file_size = document.file_size

        # Fetch subject_id from DB
        subject = (
            supabase.table("subjects")
            .select("id, name")
            .eq("code", subject_code)
            .eq("scheme_id", str(scheme_id))
            .execute()
        )

        if not subject.data:
            await self.bot.send_message(
                chat_id=message.chat.id,
                text="❌ Subject not found for this scheme.",
            )
            return None

        subject_id = subject.data[0]["id"]
        subject_name = subject.data[0]["name"]

        channel_username = os.getenv("TELEGRAM_CHANNEL_USERNAME")
        message_link = (
            f"https://t.me/{channel_username.replace('@', '')}"
            f"/{message.message_id}"
        )

        # TODO: Manual moderation required before frontend visibility
        # moderated_at and moderated_by remain NULL on upload
        # Admin must manually approve notes before they appear in the frontend
        data = {
            "subject_id": subject_id,
            "scheme_id": scheme_id,
            "resource_type": "pdf",
            "file_name": file_name,
            "file_size": file_size,
            "telegram_file_id": file_id,
            "telegram_message_link": message_link,
            "tags": tags,
            "uploaded_at": datetime.utcnow().isoformat(),
            # moderated_at and moderated_by are intentionally NOT set here
            # They remain NULL until manually approved by admin
        }

        result = (
            supabase.table("community_resources")
            .insert(data)
            .execute()
        )

        logger.info(
            f"Stored resource: {file_name} "
            f"→ {subject_name} ({scheme_id})"
        )

        await self.bot.send_message(
            chat_id=message.chat.id,
            text=(
                "✅ Successfully stored!\n\n"
                f"Subject: {subject_name}\n"
                f"Scheme: {scheme_id}\n"
                f"File: {file_name}"
            ),
        )

        return result.data[0]
