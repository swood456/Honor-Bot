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

honor_pool = {}

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

# Testing basic command, remove eventually
@client.command()
async def square(number):
    squared_value = int(number) * int(number)
    await client.say(str(number) + " squared is " + str(squared_value))

@client.command(name='honor',
                desciption='Gives the amount of honor for the given user. Name is case sensitive and accepts nickname or username',
                brief='Gives honor of user',
                aliases=['list_honor'],
                pass_context=True)
async def list_honor(context, name):
    member = context.message.server.get_member_named(name)

    if member:
        await client.say(member.display_name + ' has ' + str(int(honor_pool[context.message.server.id][member.id])) + ' honor')
    else:
        await client.say(name + ' not recognized as a user on this server. Make sure capitalization is correct and try again')


@client.command(name='allHonor',
                description='Lists the honor of all users on the server. If there are more than 20 users, it will only list 20',
                brief='List the honor of all users',
                aliases=['all_honor', 'honor_all', 'honorAll'],
                pass_context=True)
async def all_honor(context):
    server = context.message.server

    count = 0
    message = '```\n'

    for mem in server.members:
        if mem.id in honor_pool[server.id]:
            message += mem.display_name + ': ' + str(int(honor_pool[server.id][mem.id])) + '\n'
            count += 1
            if count >= 20:
                break

    message += '```'

    await client.say(message)

# TODO: command for listing all open honor bets

# TODO: command for listing all honor bets that I am a part of

# TODO: command for creating an honor bet

@client.check
def check_global(context):
    server = context.message.server
    if server.id not in honor_pool:
        honor_pool[server.id] = {}

        for member in server.members:
            if not member.bot:
                honor_pool[server.id][member.id] = K_INITIAL_USER_HONOR
    # Make sure the author is in the database
    elif context.message.author.id not in honor_pool[server.id]:
        honor_pool[server.id][context.message.author.id] = K_INITIAL_USER_HONOR
    return True

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