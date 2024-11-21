import logging
from typing import List

from app.db import db
from app.lib.logger import get_logger

logger = get_logger(__name__, logging.INFO)
from enum import Enum


class Role(Enum):
    USER = "user"
    CLONE = "clone"


class Message:
    def __init__(self):
        self.role: Role
        self.start_time: float
        self.content: str


class Transcript:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.messages: List[Message] = []

    def get(self):
        return self.messages

    async def get_from_db(self):
        try:
            messages = await db.message.find_many(
                where={"conversationId": self.conversationId}
            )
            return messages

        except Exception as e:
            logger.error(f"unable to get messages in conversation: {e}")

    async def append(self, role: str, start_time: float, content: str):
        message = Message(role=role, start_time=start_time, content=content)
        self.messages.append(message)

        try:
            await db.message.create(
                data={
                    "conversationId": self.conversation_id,
                    "role": message.role,
                    "startTime": message.start_time,
                    "content": message.content,
                }
            )

        except Exception as e:
            logger.warn(f"did not save {message}: {e}")
