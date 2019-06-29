import driver_utils
import discord
import asyncio
from selenium.webdriver.common.keys import Keys
from collections import defaultdict
from cache import Cache
from uuid import uuid4
from pillow_utils import convert_to_buffer
from selenium import webdriver
from flask import Flask, send_file, abort
from asyncio import sleep
from discord.ext import commands
from threading import Thread

with open('domain.txt') as domain:
    DOMAIN = domain.read().strip()

POTENTIAL_ACTIONS = {
    'cursor left': '⬅',
    'cursor up': '⬆',
    'cursor down': '⬇',
    'cursor right': '➡',
    'left click': '🇱',
    'right click': '🇷',
    'type': '⌨',
    'hard return': '↩',
    'change site': '📝',
    'quit browsing': '🛑'
}
SESSION_INFO = {}
FRAME_CACHE = defaultdict(lambda: defaultdict(lambda: Cache(5)))
bot = commands.Bot(command_prefix='b!')


@bot.event
async def on_reaction_add(reaction, member):

    reaction_type, session_info = str(reaction.emoji), SESSION_INFO.get(reaction.message.id, None)

    if member != bot.user:
        asyncio.create_task(reaction.remove(member))

    if member == bot.user or session_info is None or reaction_type not in POTENTIAL_ACTIONS.values():
        return

    if reaction_type == POTENTIAL_ACTIONS['left click']:
        driver_utils.perform_left_click_at(*session_info)
    elif reaction_type == POTENTIAL_ACTIONS['right click']:
        driver_utils.perform_right_click_at(*session_info)
    elif reaction_type == POTENTIAL_ACTIONS['cursor up']:
        session_info[0][1] -= 15
    elif reaction_type == POTENTIAL_ACTIONS['cursor down']:
        session_info[0][1] += 15
    elif reaction_type == POTENTIAL_ACTIONS['cursor left']:
        session_info[0][0] -= 15
    elif reaction_type == POTENTIAL_ACTIONS['cursor right']:
        session_info[0][0] += 15
    elif reaction_type == POTENTIAL_ACTIONS['type']:
        message = await bot.wait_for('message', check=lambda m: m.author == member)
        driver_utils.send_keys(message.content, session_info[1])
        await message.delete()
    elif reaction_type == POTENTIAL_ACTIONS['hard return']:
        driver_utils.send_keys(Keys.RETURN, session_info[1])
    elif reaction_type == POTENTIAL_ACTIONS['change site']:
        message = await bot.wait_for('message', check=lambda m: m.author == member)
        session_info[1].get(message.content)
        await message.delete()
    elif reaction_type == POTENTIAL_ACTIONS['quit browsing']:
        session_info[1].quit()

    driver_utils.move_mouse_to(*session_info)


@bot.command()
async def browse(ctx, url: str):
    embed_color = discord.Color(0x05058e)
    message = await ctx.send(embed=discord.Embed(description='Loading...', color=embed_color, title='Browser'))

    driver = webdriver.Chrome('./resources/chromedriver.exe')
    driver.get(url)

    SESSION_INFO[message.id] = (list(driver_utils.get_center_of(driver)), driver)

    for reaction in POTENTIAL_ACTIONS.values():
        asyncio.create_task(message.add_reaction(reaction))

    driver.running = True

    def quit_session(driver):
        driver.running = False

    driver.stop_client = quit_session

    while driver.running:
        frame, frame_id = driver_utils.get_screenshot_with_cursor(driver, SESSION_INFO[message.id][0]), uuid4().hex
        FRAME_CACHE[ctx.guild.id][message.id][frame_id] = frame

        new_embed = discord.Embed(color=embed_color, title=driver.title or 'Browser')
        new_embed.set_thumbnail(url=f'http://{DOMAIN}:9340/frame/{ctx.guild.id}/{message.id}/{frame_id}')
        if message.embeds[0].thumbnail:
            new_embed.set_image(url=message.embeds[0].thumbnail.url)
        await message.edit(embed=new_embed)

        await sleep(3.5)


app = Flask(__name__)


@app.route('/frame/<int:guild_id>/<int:message_id>/<frame_id>')
def get_frame(guild_id, message_id, frame_id):
    try:
        frame = FRAME_CACHE[guild_id][message_id][frame_id]
        return send_file(convert_to_buffer(frame, optimize=True, quality=85), mimetype='image/png')
    except KeyError:
        abort(404)


Thread(target=lambda: app.run('0.0.0.0', 9340)).start()

with open('token.txt') as token_file:
    bot.run(token_file.read().strip())
