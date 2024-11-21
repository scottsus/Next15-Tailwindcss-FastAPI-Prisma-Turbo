import logging
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from queue import Empty, Queue
from time import time
from typing import Any, Dict, List, Tuple

from app.lib.logger import get_logger
from app.services.stt import STT, Deepgram
from app.services.transcript import Role, Transcript
from app.services.tts import TTS, ElevenLabs
from daily import CallClient, Daily, EventHandler, VirtualMicrophoneDevice
from pydantic import BaseModel

logger = get_logger(__name__, logging.DEBUG)


class DataPacket(BaseModel):
    text: str
    audio: bytes


class ExchangeState(Enum):
    CLOSED = "closed"
    IDLE = "idle"
    SPEAKING = "speaking"
    LISTENING = "listening"
    POST_PROCESSING = "post-processing"


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
        self.packets: List[DataPacket] = []

        self.stt: STT = Deepgram()
        self.tts: TTS = ElevenLabs()

        self.audio_data_queue: Queue[Tuple[bytes, bool]] = Queue()

        self.exchange_state = ExchangeState.IDLE
        self.is_in_conversation = True

        self.start_time: float
        self.transcript = Transcript("123")

        # self.intro = """
        # Yo what's up. I'm Scott's AI - and although I'm not actually Scott himself,
        # I have his voice completely cloned. How are you doing today?"""
        self.intro = "Yo what's up. I'm Scott's AI"

    def start(self):
        try:
            self.start_time = time()

            logger.info("Clone.start()...")
            self.packets = [self._speak(self.intro)]
            self._run()

        except Exception as e:
            logger.error(e)
            raise

    def _run(self):
        # Send welcome message
        for packet in self.packets:
            self._send_audio(packet)
        self.packets = []

        while self.is_in_conversation:
            with ThreadPoolExecutor() as executor:

                # Listen
                try:
                    logger.info("trying to open pipeline")
                    self.stt = (executor.submit(self.stt.open)).result()
                except Exception as e:
                    logger.error("stt.open failed:", e)
                    raise

                self.exchange_state = ExchangeState.LISTENING
                while self.exchange_state == ExchangeState.LISTENING:
                    try:
                        audio_frames, ok = self.audio_data_queue.get(timeout=0.5)
                        if not ok:
                            logger.debug("ending audio pipeline")
                            break
                        self.stt.write(audio_frames)
                    except Empty:
                        pass
                    except Exception as e:
                        logger.warn(e)

                try:
                    self.stt = (executor.submit(self.stt.close)).result()
                except Exception as e:
                    logger.error("stt.close failed:", e)
                    raise

                # @TODO: should be message instead of segment
                message = self.stt.get_result()
                relative_start_time = time() - self.start_time
                self.transcript.append(
                    role=Role.USER, start_time=relative_start_time, content=message
                )
                logger.info(f"segment: {message}")

                # Respond
                # @TODO: speak should include these packet stuff
                self.packets = [self._speak("I see. That is indeed really interesting")]
                for packet in self.packets:
                    self._send_audio(packet)

                self.is_in_conversation = False

            # End the conversation
            self.is_in_conversation = False

    def _speak(self, text: str):
        logger.debug(f"generating TTS for '{text}'...")

        try:
            text = text.strip()
            audio = self.tts.speak(text)
            return DataPacket(text=text, audio=audio)

        except Exception as e:
            logger.warn(e)
            raise

    def _send_audio(self, data: DataPacket):
        try:
            self.microphone.write_frames(data.audio)
            logger.debug("sent to microphone")

        except Exception as e:
            logger.warn(e)
            raise

    def on_participant_joined(self, participant: Dict[str, Any]) -> None:
        """Callback from EventHandler"""
        try:
            participant_id = participant["id"]
            self.call_client.set_audio_renderer(participant_id, self.on_audio_data)
            logger.info(f"participant with id [{participant_id}] has joined the room.")

        except Exception as e:
            logger.error(e)
            raise

    def on_app_message(self, message: Any, sender: str):
        """Callback from EventHandler"""
        try:
            if (
                self.exchange_state == ExchangeState.LISTENING
                and message["type"] == "speechend"
            ):
                logger.debug("received 'speechend' signal")
                self.exchange_state = ExchangeState.SPEAKING

        except Exception as e:
            logger.warn(e)
            pass

    def on_audio_data(self, _, audio_data):
        """API from CallClient.set_audio_renderer"""
        try:
            if self.exchange_state == ExchangeState.LISTENING:
                audio_frames = audio_data.audio_frames
                self.audio_data_queue.put((audio_frames, True))

        except Exception as e:
            logger.error(e)
            self.audio_data_queue.put((b"", False))
