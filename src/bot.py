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
K_INITIAL_USER_HONOR = 100
K_DEFAULT_BET_VALUE = 15
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
bet_collection = honorBot_db.bets
# TODO: something that keeps track of info about what commands are used/when used wrong, etc.

class HonorBet:
    def __init__(self, player1, amount, message, display_id, id=None, player2=None):
        self.player1 = player1
        self.amount = amount
        self.message = message
        self.display_id = display_id
        self.player2 = player2
        if id is not None:
            self._id = id

    @classmethod
    def create_from_json(cls, bet_dict):
        return cls(bet_dict['player1'], bet_dict['amount'], bet_dict['message'], bet_dict['display_id'], bet_dict['id'], bet_dict['player2'])

@client.command()
async def source():
    await client.say('Honor bot is open source! Source code can be found at https://github.com/swood456/Honor-Bot')

@client.command(name='honor',
                desciption='Gives the amount of honor for the given user. Name is case sensitive and accepts nickname or username',
                brief='Gives honor of user',
                aliases=['list_honor'],
                pass_context=True)
async def list_honor(context, name):
    member = context.message.server.get_member_named(name)

    if member:
        check_user(member)
        member_honor = user_collection.find_one({ '_id': member.id })['honor']
        await client.say(member.display_name + ' has ' + str(member_honor) + ' honor')
    else:
        await client.say(name + ' not recognized as a user on this server. Make sure capitalization is correct and try again')

@client.command(name='allHonor',
                description='Lists the honor of all users on the server. If there are more than 20 users, it will only list 20',
                brief='List the honor of all users',
                aliases=['all_honor', 'honor_all', 'honorAll'],
                pass_context=True)
async def all_honor(context):
    server = context.message.server

    message = '```\n'

    for member in list(server.members)[:20]:
        if member.bot: continue
        check_user(member)
        member_honor = user_collection.find_one({ '_id': member.id })['honor']
        message += member.display_name + ': ' + str(member_honor) + '\n'

    message += '```'

    await client.say(message)

# TODO: command for listing all open honor bets

# TODO: command for listing all honor bets that I am a part of

# TODO: command for getting info about a specific bet

# TODO: command to accept an open bet

# TODO: command to mark a bet as complete

# TODO: command to user/transfer some honor to give another user nickname for peroid of time

@client.command(name='makeBet',
                description='Creates a new honor bet for another user to accept.\nUsage: !makeBet [amount] [message]',
                brief='Create a new honor bet for another user to accept',
                alias=['createBet', 'make_bet', 'create_bet', 'newBet', 'new_bet', 'honorBet', 'honor_bet'],
                pass_context='true')
async def make_bet(context, amount, *args):
    message = ' '.join(args)

    try:
        amount = float(amount)
    except ValueError:
        await client.say('Error parsing bet amount. Make sure that you put a number!')
        return

    if not check_user_has_honor(context.message.author.id, amount):
        await client.say('You do not have enough honor to make a bet for that much!')
        return

    # There is probably a better way to determine an ID to show to users, but hikjacking id field is bad UX
    max_display_id_document = bet_collection.find_one(sort=[("display_id", pymongo.DESCENDING)])

    max_display_id = 0
    if max_display_id_document is not None:
        max_display_id = max_display_id_document.get('display_id', 0)
    
    bet = HonorBet(context.message.author.id, amount, message, max_display_id + 1)
    bet_collection.insert_one(bet.__dict__)

    await client.say('Bet ID ' + str(bet.display_id) + ' created!')

'''
    Utility functions
'''

# check function is run every time a command is given to the bot
@client.check
def check_global(context):
    return check_user(context.message.author)

# check to see if the member is 
def check_user(member):
    result = user_collection.count_documents({ '_id': member.id })
    if result <= 0:
        add_new_user(member)
    return True

# Adds new user into database
def add_new_user(member):
    user_collection.insert_one({
        "_id": member.id,
        "honor": K_INITIAL_USER_HONOR
    })

def check_user_has_honor(userId, honor_amount):
    result = user_collection.find_one({ '_id': userId })
    return result['honor'] >= honor_amount

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