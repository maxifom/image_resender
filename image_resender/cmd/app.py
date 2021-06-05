import argparse
import asyncio
import logging
import os
import random
from typing import Any, Dict

import aiohttp
from aiohttp import FormData

from image_resender.vk_api import get_photo_url, NeedNewServerException, VKClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

bot_messages = [
    "Are you a RETARD or WHAT? I accept only IMAGES! Not documents",
    "I am a bot, not a sverhrazum",
    "IMAGES ONLY! ARE YOU FCKING KIDDING ME?",
    "Zakrito, idite nahui",
    "WHYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY?????????",
    "Are you a fucking gamburger or WHAT?",
    "STFU RETARD",
    "TA ZA WO",
    "VIRIBAITE pls",
    "WTF ARE you writing?",
    "Tebe vawe nehui zanetsya?",
    "Красава ваще, спс за текст",
    "МБ Голосовуху еще кинешь?",
    "Не, ну гений конечно",
    "ПОНИМАЮ!",
    "Без комментариев"
]


async def send_not_an_image(user_id, client: VKClient):
    await client.send_message(chat_id=user_id, text=random.choice(bot_messages), attachment="photo-183502784_456239035")


async def handle(msg: Dict[str, Any], client: VKClient):
    chat_id = msg["object"]["message"]["from_id"]
    attachments = msg["object"]["message"]["attachments"]
    if msg.get("type") != "message_new" or len(attachments) <= 0:
        return await send_not_an_image(chat_id, client)

    attachments = [a for a in attachments if "photo" == a['type']]
    attachments_to_send = []
    for attachment in attachments:
        url = get_photo_url(attachment['photo']['sizes'])
        filename = url.split("/")[-1]
        async with client.session.get(url) as r:
            image_content = await r.read()

        image_upload_url = (await client.get_messages_upload_server())["response"]["upload_url"]
        data = FormData()
        data.add_field("photo", image_content, filename=filename)
        async with client.session.post(image_upload_url, data=data) as r:
            photo = await r.json(content_type='text/html')
            photo_save_response = await client.save_messages_photo(**photo)
            for photo in photo_save_response['response']:
                attachments_to_send.append(f"photo{photo['owner_id']}_{photo['id']}_{photo['access_key']}")
    send_str = f"Sent {len(attachments_to_send)} photos"
    if len(attachments_to_send) == 1:
        send_str = f"Sent {len(attachments_to_send)} photo"
    await client.send_message(chat_id=chat_id, text=send_str, attachment=','.join(attachments_to_send))


async def long_poll(server_url: str, key: str, ts: str, client: VKClient):
    post_form = {'wait': 25, 'ts': ts, 'key': key, 'act': "a_check"}
    max_ts = ts
    async with client.session.post(server_url, data=post_form) as r:
        js = await r.json()
        if int(js.get("failed", 0)) > 0:
            raise NeedNewServerException
        max_ts = js["ts"]
        for message in js["updates"]:
            if message["type"] != "message_new":
                continue
            logger.info("Handling %s", message)
            await handle(message, client)
    return max_ts


async def amain(access_token: str, group_id: str, api_version: str):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=25)) as s:
        client = VKClient(api_version=api_version, session=s, access_token=access_token)
        long_poll_dict = await client.get_long_poll_server(group_id=group_id)
        server_url = long_poll_dict["response"]["server"]
        key = long_poll_dict["response"]["key"]
        ts = long_poll_dict["response"]["ts"]
        while True:
            try:
                ts = await long_poll(server_url, key, ts, client)
            except NeedNewServerException:
                long_poll_dict = await client.get_long_poll_server(group_id=group_id)
                server_url = long_poll_dict["response"]["server"]
                key = long_poll_dict["response"]["key"]
                ts = long_poll_dict["response"]["ts"]
                continue
            except asyncio.TimeoutError:
                logger.debug("timeout doing long poll")


def main():
    logger.info("Start long poller")
    argparser = argparse.ArgumentParser("image_resender")
    argparser.add_argument("--access-token", default=os.getenv("ACCESS_TOKEN"))
    argparser.add_argument("--group-id", type=int, default=os.getenv("GROUP_ID"))
    argparser.add_argument("--api-version", default=os.getenv("API_VERSION"))
    args, _ = argparser.parse_known_args()
    print("Config: ", args)

    asyncio.run(amain(access_token=args.access_token, group_id=args.group_id, api_version=args.api_version))


if __name__ == '__main__':
    main()
