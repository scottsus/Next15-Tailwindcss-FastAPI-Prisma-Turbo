import logging
from typing import List

from app.lib.logger import get_logger
from app.services.tts import ElevenLabs
from daily import CallClient, Daily, EventHandler, VirtualMicrophoneDevice
from pydantic import BaseModel

logger = get_logger(__name__, logging.DEBUG)


class DataPacket(BaseModel):
    text: str
    audio: bytes


def construct_clone(room_url: str):
    Daily.init()
    clone = Clone(room_url)

    client = CallClient(event_handler=clone)
    client.update_subscription_profiles(
        {"base": {"camera": "unsubscribed", "microphone": "subscribed"}}
    )

    sample_rate = 44_100  # 44.1Khz
    microphone = Daily.create_microphone_device(
        "my-mic", sample_rate=sample_rate, channels=1
    )

    client.update_inputs(
        {
            "camera": False,
            "microphone": {"isEnabled": True, "settings": {"deviceId": "my-mic"}},
        }
    )

    client.join(room_url)

    clone.call_client = client
    clone.microphone = microphone

    clone.start()


class Clone(EventHandler):
    def __init__(self, room_url: str):
        self.name = "Scott"
        self.call_client: CallClient = None
        self.microphone: VirtualMicrophoneDevice = None
        self.tts = ElevenLabs()
        self.packets: List[DataPacket] = []
        self.intro = """
        Yo what's up. I'm Scott's AI - and although I'm not actually Scott himself,
        I have his voice completely cloned. How are you doing today?"""

    def start(self):
        try:
            logger.info("Clone.start()...")
            self.packets = [self._speak(self.intro)]
            self._run()

        except Exception as e:
            logger.error(str(e))

    def _run(self):
        for packet in self.packets:
            self._send_audio(packet)

    def _speak(self, text: str):
        logger.debug(f"generating TTS for '{text}'...")

        try:
            text = text.strip()
            audio = self.tts.speak(text)
            return DataPacket(text=text, audio=audio)

        except Exception as e:
            logger.warn(e)

    def _send_audio(self, data: DataPacket):
        try:
            self.microphone.write_frames(data.audio)
            logger.debug("written frames to microphone")

        except Exception as e:
            logger.warn(e)
