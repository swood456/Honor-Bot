# Work with Python 3.6
import random
import asyncio
import json
import os
import pymongo
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

# Load auth token
with open(os.path.join('data', 'auth.json')) as auth_file:
    TOKEN = json.load(auth_file)['token']

# load statuses
with open(os.path.join('data', 'statuses.json')) as status_file:
    statuses = json.load(status_file)['statuses']

client = Bot(command_prefix=BOT_PREFIX)

# Load honor stuff from mongo
mongoClient = pymongo.MongoClient("mongodb://localhost:27017/")

honorBot_db = mongoClient.honorBot

user_collection = honorBot_db.users

class HonorBet:
    def __init__(self, value = 10, player1 = None, player2 = None):
        self.value = value
        self.player1 = player1
        self.player2 = player2

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

@client.command(name='honor',
                desciption='Gives the amount of honor for the given user. Name is case sensitive and accepts nickname or username',
                brief='Gives honor of user',
                aliases=['list_honor'],
                pass_context=True)
async def list_honor(context, name):
    member = context.message.server.get_member_named(name)

    if member:
        check_user(member)
        member_honor = user_collection.find_one({ '_id': member.id })
        await client.say(member.display_name + ' has ' + str(member_honor['honor']) + ' honor')
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

    for member in server.members:
        if member.bot: continue
        check_user(member)
        member_honor = user_collection.find_one({ '_id': member.id })['honor']
        message += member.display_name + ': ' + str(member_honor) + '\n'
        count += 1
        if count >= 20:
            break

    message += '```'

    await client.say(message)

# TODO: command for listing all open honor bets

# TODO: command for listing all honor bets that I am a part of

# TODO: command for creating an honor bet
@client.command(name='makeBet',
                description='Creates a new honor bet for another user to accept. You may specify a value for the bet',
                brief='Create a new honor bet for another user to accept',
                alias=['createBet', 'make_bet', 'create_bet', 'newBet', 'new_bet'],
                pass_context='true')
async def make_bet(context):
    await client.say('this still needs to be implemented OOPS')

@client.check
def check_global(context):
    return check_user(context.message.author)

def check_user(member):
    result = user_collection.count_documents({ '_id': member.id })
    if result <= 0:
        add_new_user(member)
    return True

def add_new_user(member):
    user_collection.insert_one({
        "_id": member.id,
        "honor": K_INITIAL_USER_HONOR
    })

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