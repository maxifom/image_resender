from dataclasses import dataclass
import logging
from typing import Union

import aiohttp
from ratelimit import limits

import random

logger = logging.getLogger(__name__)


def get_random_id():
    return random.getrandbits(31) * random.choice([-1, 1])


def get_photo_url(sizes):
    photo_sizes = ["w", "z", "y", "r", "q", "p", "o", "x", "m", "s"]
    for size in photo_sizes:
        for s in sizes:
            if s["type"] == size:
                return s["url"]
    return ""


class NeedNewServerException(Exception):
    pass


@dataclass
class VKClient:
    api_version: str
    access_token: str
    session: aiohttp.ClientSession

    # VK API Limit - 20 per second, 18 for safety
    @limits(calls=18, period=1)
    async def call_method(self, method: str, **params) -> dict:
        u = f"https://api.vk.com/method/{method}"
        request_params = dict(**params)
        request_params["v"] = self.api_version
        request_params["access_token"] = self.access_token
        async with self.session.post(u, data=request_params) as r:
            data = await r.json()
            logger.info(f"{method}: {data}")
            return data

    async def get_messages_upload_server(self) -> dict:
        return await self.call_method("photos.getMessagesUploadServer")

    async def save_messages_photo(self, *, server: int, photo: str, hash: str) -> dict:
        return await self.call_method('photos.saveMessagesPhoto', server=server, photo=photo, hash=hash)

    async def send_message(self, *, chat_id: Union[int, str], text: str, attachment: str):
        random_id = random.getrandbits(31) * random.choice([-1, 1])
        return await self.call_method("messages.send", message=text, random_id=random_id, peer_id=chat_id,
                                      attachment=attachment)

    async def get_long_poll_server(self, *, group_id: str) -> dict:
        return await self.call_method("groups.getLongPollServer", group_id=group_id)
