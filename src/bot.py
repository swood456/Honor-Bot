# Work with Python 3.6
import random
import asyncio
import json
import os
import pymongo
from discord import Game
from discord.ext.commands import Bot
from datetime import datetime, timedelta
from honorbot import *

'''main documentation for API that I am using is at:
    https://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html
    https://discordpy.readthedocs.io/en/rewrite/api.html?highlight=description
    https://discordpy.readthedocs.io/en/rewrite/ext/commands/index.html
    https://discordpy.readthedocs.io/en/latest/api.html
'''
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
                desciption='Gives the duration of the user\'s current nickname and any future debts that they owe',
                brief='Gives info about user',
                aliases=['user'],
                pass_context=True)
async def user_honor(context, name):
    # TODO: figure out how to make with work with @username#0123 format
    member = context.message.server.get_member_named(name)

    if member:
        check_user(member)
        member_honor = user_collection.find_user(member.id)['honor']
        await client.say(member.display_name + ' has ' + str(member_honor) + ' honor')
    else:
        await client.say(name + ' not recognized as a user on this server. Make sure capitalization is correct and try again')

# TODO: determine if this command is at all useful, and if not kill it off
# @client.command(name='all_honor',
#                 description='Lists the honor of all users on the server. If there are more than 20 users, it will only list 20',
#                 brief='List the honor of all users',
#                 aliases=['allHonor', 'honor_all', 'honorAll'],
#                 pass_context=True)
# async def all_honor(context):
#     server = context.message.server

#     message = '```\n'

#     for member in list(server.members)[:20]:
#         if member.bot: continue
#         check_user(member)
#         member_honor = user_collection.find_user(member.id)['honor']
#         message += member.display_name + ': ' + str(member_honor) + '\n'

#     message += '```'

#     await client.say(message)

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
                brief='gives info for a specific bet',
                aliases=['betinfo', 'bet_info', 'info'],
                pass_context=True)
async def bet_info(context, bet_display_id):
    bet = check_display_id(bet_display_id)
    if not bet:
        return
    message = '```\n' + print_bet(bet, context.message.server) + '\n```'

    await client.say(message)

@client.command(name='accept',
                description='Accept a bet using the display id of the bet',
                brief='Accept an open bet',
                aliases=['acceptBet', 'Accept', 'acceptbet', 'accept_bet'],
                pass_context=True)
async def accept(context, bet_display_id):
    bet = check_display_id(bet_display_id)
    if not bet:
        return

    mention = context.message.author.mention
    user_id = context.message.author.id

    # Various error checking to make sure bet is valid for this user to accept
    if bet.player2 is not None or bet.state != HonorBet.open_state:
        await client.say('{} Bet {} is not open any more, you cannot accept it'.format(mention, bet.display_id))
        return
    if (bet.player1 == user_id):
        await client.say('{} You cannot accept Bet {} because you created it'.format(mention, bet.display_id))
        return
    
    bet.player2 = user_id
    bet.state = HonorBet.active_state
    bet_collection.update_bet(bet)
    await client.say('{} Bet {} was accepted by {}'.format(context.message.server.get_member(bet.player1).mention, bet.display_id, mention))

@client.command(name='claim',
                description='Claim that you won the bet with the given display_id',
                brief='Claim that you won a bet',
                aliases=['Claim'],
                pass_context=True)
async def claim(context, bet_display_id, *losers_nickname):
    bet = check_display_id(bet_display_id)
    if not bet:
        return
    
    nickname = ' '.join(losers_nickname)
    user_id = context.message.author.id

    if bet.state != HonorBet.active_state:
        await client.say('Bet {} is not marked as active, thus cannot be claimed'.format(bet.display_id))
        return

    if bet.player1 != user_id and bet.player2 != user_id:
        await client.say('You are not participating in Bet {} so you cannot claim it'.format(bet.display_id))
        return
    
    bet.claimed_user = user_id
    bet.state = HonorBet.claimed_state
    bet.punishment_nickname = nickname
    bet_collection.update_bet(bet)

    await client.say('Bet {} has been marked as completed. {} use commands !approve or !reject to accept or reject that the bet is completed in favor of {}'.format(bet.display_id, context.message.server.get_member(bet.player1).mention, context.message.author.mention))

@client.command(name='approve',
                description='Approve that you lost the bet, giving the honor to the person who claimed the bet',
                brief='Approve that you lost a bet',
                aliases=['Approve'],
                pass_context=True)
async def approve(context, bet_display_id):
    bet = check_display_id(bet_display_id)
    if not bet:
        return
    
    user_id = context.message.author.id

    if bet.state != HonorBet.claimed_state:
        await client.say('Bet {} is not in the claimed state, so you can not approve it'.format(bet.display_id))
        return
    if bet.player1 != user_id and bet.player2 != user_id:
        await client.say('You are not a participant in Bet {}, so you can not approve it'.format(bet.display_id))
        return
    if bet.claimed_user == user_id:
        await client.say('You cannot approve your own bet, the loser of the bet must approve it')
        return

    bet.state = HonorBet.closed_state
    bet_collection.update_bet(bet)

    winning_user = user_collection.find_user(bet.claimed_user)
    winning_user['won_bets'] = winning_user.get('won_bets', 0) + 1
    user_collection.update_user(winning_user)

    losing_user = user_collection.find_user(user_id)
    losing_user['lost_bets'] = losing_user.get('lost_bets', 0) + 1
    punishments = losing_user.get('punishment_nicknames', [])
    punishments.append({'ending' : datetime.now() + timedelta(days=bet.duration), 'punishment_nickname': bet.punishment_nickname})
    losing_user['punishment_nicknames'] = punishments
    user_collection.update_user(losing_user)

    await client.say('Bet {} completed'.format(bet.display_id))
    return

@client.command(name='reject',
                description='Reject that the bet is lost, putting it back as avilable to be claimed by either party',
                brief='Reject that you lost a bet',
                aliases=['Reject'],
                pass_context=True)
async def reject(context, bet_display_id):
    bet = check_display_id(bet_display_id)
    if not bet:
        return
    
    user_id = context.message.author.id

    if bet.state != HonorBet.claimed_state:
        await client.say('Bet {} is not in the claimed state, so you can not reject it'.format(bet.display_id))
        return
    if bet.player1 != user_id and bet.player2 != user_id:
        await client.say('You are not a participant in Bet {}, so you can not reject it'.format(bet.display_id))
        return
    
    bet.state = HonorBet.active_state
    bet.claimed_user = None
    bet.punishment_nickname = None
    bet_collection.update_bet(bet)

    await client.say('Bet {} has been rejected, and can now be claimed by either party'.format(bet.display_id))

# TODO: command to cancel bet made by author that has not been accepted yet 

# TODO: V2: command to user/transfer some honor to give another user nickname for peroid of time

# TODO: V2: command to somehow resolve disagreement where it is unclear bet is complete or not

@client.command(name='make_bet',
                description='Creates a new honor bet for another user to accept',
                brief='Create a new honor bet for another user to accept',
                aliases=['createBet', 'makeBet', 'create_bet', 'newBet', 'new_bet', 'honorBet', 'honor_bet'],
                pass_context='true')
async def make_bet(context, nickname_duration, *bet):
    message = ' '.join(bet)

    try:
        duration = int(nickname_duration)
    except ValueError:
        await client.say('Error parsing loss duration. Make sure that you put a number!')
        return

    # There is probably a better way to determine an ID to show to users, but hikjacking id field is bad UX
    next_display_id = bet_collection.find_next_display_id()
    
    bet = HonorBet(context.message.author.id, duration, message, next_display_id)
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

def print_bet(bet, server):
    # TODO: there is a lot more info that needs to be shown for this
    return '{}: {}\n\tcreated by: {}\n'.format(bet.display_id, bet.message, server.get_member(bet.player1))

def check_display_id(bet_display_id):
    try:
        display_id = int(bet_display_id)
    except ValueError:
        asyncio.ensure_future(client.say('Error parsing display id {}. Make sure that you put an integer!'.format(bet_display_id)))
        return False
    
    bet = bet_collection.find_by_display_id(display_id)
    if bet is None:
        asyncio.ensure_future(client.say('Could not find a bet with display id {}'.format(display_id)))
        return False
    return bet

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