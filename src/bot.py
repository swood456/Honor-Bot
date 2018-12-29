# Work with Python 3.6
import random
import asyncio
import json
import os
import pymongo
from discord import Game
from discord.ext.commands import Bot
from honorbot import *

'''main documentation for API that I am using is at:
    https://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html
    https://discordpy.readthedocs.io/en/rewrite/api.html?highlight=description
    https://discordpy.readthedocs.io/en/rewrite/ext/commands/index.html
    https://discordpy.readthedocs.io/en/latest/api.html
'''
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

user_collection = UserCollection(honorBot_db)
bet_collection = BetCollection(honorBot_db)
# TODO: something that keeps track of info about what commands are used/when used wrong, etc.

@client.command()
async def source():
    await client.say('Honor bot is open source! Source code can be found at https://github.com/swood456/Honor-Bot')

@client.command(name='user_honor',
                desciption='Gives the amount of honor for the given user. Name is case sensitive and accepts nickname or username',
                brief='Gives honor of user',
                aliases=['user'],
                pass_context=True)
async def user_honor(context, name):
    member = context.message.server.get_member_named(name)

    if member:
        check_user(member)
        member_honor = user_collection.find_user(member.id)['honor']
        await client.say(member.display_name + ' has ' + str(member_honor) + ' honor')
    else:
        await client.say(name + ' not recognized as a user on this server. Make sure capitalization is correct and try again')

@client.command(name='all_honor',
                description='Lists the honor of all users on the server. If there are more than 20 users, it will only list 20',
                brief='List the honor of all users',
                aliases=['allHonor', 'honor_all', 'honorAll'],
                pass_context=True)
async def all_honor(context):
    server = context.message.server

    message = '```\n'

    for member in list(server.members)[:20]:
        if member.bot: continue
        check_user(member)
        member_honor = user_collection.find_user(member.id)['honor']
        message += member.display_name + ': ' + str(member_honor) + '\n'

    message += '```'

    await client.say(message)

@client.command(name='openBets',
                description='Lists all honor bets that have not yet been accepted',
                brief='Lists all open bets',
                aliases=['open_bets', 'openbets', 'open'],
                pass_context=True)
async def open_bets(context):
    bets = bet_collection.find_all_open_bets()

    message = '```\n'
    for bet in bets:
        message += print_bet(bet, context.message.server)
    message += '```'

    await client.say(message)

@client.command(name='myBets',
                description='Lists all open honor bets that you are a part of',
                brief='Lists all of your bets',
                aliases=['my_bets'],
                pass_context=True)
async def my_bets(context):
    user_id = context.message.author.id
    bets = bet_collection.find_all_user_bets(user_id)

    message = '```\n'
    for bet in bets:
        message += print_bet(bet, context.message.server)
    message += '```'

    await client.say(message)

@client.command(name='betInfo',
                description='Gives info on a specific bet',
                aliases=['betinfo', 'bet_info', 'info'],
                pass_context=True)
async def bet_info(context, bet_display_id):
    try:
        display_id = int(bet_display_id)
    except ValueError:
        await client.say('Error parsing display id. Make sure that you put an integer!')
        return
    
    bet = bet_collection.find_by_display_id(display_id)

    message = '```\n' + print_bet(bet, context.message.server) + '\n```'

    await client.say(message)

# TODO: command to accept an open bet
@client.command(name='accept',
                description='Gives info on a specific bet',
                aliases=['acceptBet', 'Accept', 'acceptbet', 'accept_bet'],
                pass_context=True)
async def accept(context, bet_display_id):
    try:
        display_id = int(bet_display_id)
    except ValueError:
        await client.say('Error parsing display id. Make sure that you put an integer!')
        return
    
    bet = bet_collection.find_by_display_id(display_id)

    # Various error checking to make sure bet is valid for this user to accept
    if (bet.player1 == context.message.author.id):
        await client.say('You cannot accept a bet that you created')
        return

    if bet.player2 is not None:
        await client.say('This bet has already been accepted, you cannot accept it')
        return

# TODO: command to mark a bet as complete

# TODO: command to user/transfer some honor to give another user nickname for peroid of time

@client.command(name='make_bet',
                description='Creates a new honor bet for another user to accept.\nUsage: !make_bet [amount] [message]',
                brief='Create a new honor bet for another user to accept',
                aliases=['createBet', 'makeBet', 'create_bet', 'newBet', 'new_bet', 'honorBet', 'honor_bet'],
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
    next_display_id = bet_collection.find_next_display_id()
    
    bet = HonorBet(context.message.author.id, amount, message, next_display_id)
    bet_collection.insert_bet(bet)

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
    if not user_collection.user_exists(member.id):
        add_new_user(member)
    return True

# Adds new user into database
def add_new_user(member):
    user_collection.add_user(member.id)

def check_user_has_honor(userId, honor_amount):
    result = user_collection.find_user(userId)
    return result['honor'] >= honor_amount

def print_bet(bet, server):
    return '{}: {}\n\tcreated by: {}\n'.format(bet.display_id, bet.message, server.get_member(bet.player1))

@client.event
async def on_ready():
    print("Logged in as " + client.user.name)

# randomly selects an item from the list of statuses and changes the current game to it. Updates every 10 minutes
async def update_status():
    await client.wait_until_ready()
    while not client.is_closed:
        await client.change_presence(game=Game(name=random.choice(statuses)))
        await asyncio.sleep(600)


client.loop.create_task(update_status())
client.run(TOKEN)