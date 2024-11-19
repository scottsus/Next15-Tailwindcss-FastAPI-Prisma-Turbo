import logging
from multiprocessing import Process

from app.lib.logger import get_logger
from app.services.clone import construct_clone
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

router = APIRouter()

logger = get_logger(__name__, logging.DEBUG)


@router.post("/")
async def dial_clone(req: Request, bg_tasks: BackgroundTasks):
    logger.info("/clone endpoint hit")

    data = await req.json()
    room_url = data.get("room_url")

    def spawn_clone():
        process = Process(target=construct_clone, args=((room_url,)))
        process.start()
        process.join()

    bg_tasks.add_task(spawn_clone)

    return {"message": "dial_clone success"}
