import requests
import vk_api
from vk_api import VkUpload
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
from aiogram.utils import executor
from aiogram import Bot, Dispatcher
import asyncio
import random

scheduler = AsyncIOScheduler()
scheduler.start()

access_token_vk = str(input("Enter your vk"))
telegram_bot_token = str(input("Enter your telegram "))
chat_id = str(input("Enter your chat id "))
vk_session = vk_api.VkApi(token=access_token_vk)
vk = vk_session.get_api()
upload = VkUpload(vk_session)

bot = Bot(token=telegram_bot_token)
dp = Dispatcher(bot)

images_folder = "images"


async def upload_photo(photo_path):
    upload_url = vk.photos.getWallUploadServer()['upload_url']

    with open(photo_path, 'rb') as photo_file:
        response = requests.post(upload_url, files={'photo': photo_file}).json()

    photo = vk.photos.saveWallPhoto(
        server=response['server'],
        photo=response['photo'],
        hash=response['hash']
    )[0]

    return photo


async def post_photo(message, photo_path):
    photo = await upload_photo(photo_path)

    photo_id = f"photo{photo['owner_id']}_{photo['id']}"
    post = vk.wall.post(
        message=message,
        attachments=photo_id,
        random_id=vk_api.utils.get_random_id()
    )
    with open(photo_path, 'rb') as photo_file:
        await bot.send_photo(chat_id, photo_file, caption=f"Изображение опубликовано!")
    os.remove(photo_path)


async def send_error_notification():
    await bot.send_message(chat_id, "Произошла ошибка в процессе постинга.")


async def daily_post():
    post_text = ""

    image_files = [os.path.join(images_folder, f) for f in os.listdir(images_folder) if
                   os.path.isfile(os.path.join(images_folder, f))]

    if image_files:
        selected_image = image_files[random.randrange(0, len(image_files))]

        loop = asyncio.get_event_loop()
        loop.run_until_complete(await post_photo(post_text, selected_image))
    else:
        await bot.send_message(chat_id, "Нет изображений для поста.")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_error_notification())


# Will not work choose the correct time or use interval
scheduler.add_job(daily_post, "cron", minute="17", hour="20")


async def on_startup(dp):
    await bot.send_message(chat_id, "All Works")


scheduler.add_job(on_startup(), "interval", minutes=120)
if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
