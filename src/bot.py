# Work with Python 3.6
import random
import asyncio
import aiohttp
import json
import os
from discord import Game
from discord.ext.commands import Bot

'''main documentation for API that I am using is at:
    https://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html
    https://discordpy.readthedocs.io/en/rewrite/api.html?highlight=description
    https://discordpy.readthedocs.io/en/rewrite/ext/commands/index.html
    https://discordpy.readthedocs.io/en/latest/api.html
'''
K_INITIAL_USER_HONOR = 100.0
BOT_PREFIX = ("!")

# with open(os.path.join(os.pardir, 'data', 'auth.json')) as auth_file:
with open(os.path.join('data', 'auth.json')) as auth_file:
    TOKEN = json.load(auth_file)['token']

with open(os.path.join('data', 'statuses.json')) as status_file:
    statuses = json.load(status_file)['statuses']

client = Bot(command_prefix=BOT_PREFIX)

# name is the main way to use command
# description is the long explaination of what the thing does when getting help for that specific command
# brief is the info in default help command
# aliases are other things that work for command
# pass_context I think gives info about message/server/etc.

# name of command also is an alias I think??
honorPool = {}


# checks to see if server is in map and if not adds it
# need to find some way to run this every time command is thrown, or just once when new server is added
def check_server(server):
    if hash(server) not in honorPool:
        honorPool[hash(server)] = {}

        for member in server.members:
            if member != client.user:
                honorPool[hash(server)][hash(member)] = K_INITIAL_USER_HONOR

# example thing don't keep
@client.command(name='8ball',
                description="Answers a yes/no question.",
                brief="Answers from the beyond.",
                aliases=['eight_ball', 'eightball', '8-ball'],
                pass_context=True)
async def eight_ball(context):
    possible_responses = [
        'That is a resounding no',
        'It is not looking likely',
        'Too hard to tell',
        'It is quite possible',
        'Definitely',
    ]
    await client.say(random.choice(possible_responses) + ", " + context.message.author.mention)


@client.command()
async def square(number):
    squared_value = int(number) * int(number)
    await client.say(str(number) + " squared is " + str(squared_value))


@client.event
async def on_ready():
    # await client.change_presence(game=Game(name="Please replace"))
    print("Logged in as " + client.user.name)

# randomly selects an item from the list of statuses and changes the current game to it. Updates every 10 minutes
async def update_status():
    await client.wait_until_ready()
    while not client.is_closed:
        await client.change_presence(game=Game(name=random.choice(statuses)))
        await asyncio.sleep(600)


client.loop.create_task(update_status())
client.run(TOKEN)