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
                aliases=['user', 'userHonor', 'UserHonor'],
                pass_context=True)
async def user_honor(context, name):
    member = context.message.server.get_member_named(name)

    member = member or context.message.server.get_member(name.lstrip('<@!').rstrip('>'))

    if member:
        check_user(member)
        member_doc = user_collection.find_user(member.id)
        message = '```\n'
        message += '{}\t\tWon Bets: {}\t\tLost Bets: {}\n'.format(member.display_name, member_doc.get('won_bets', 0), member_doc.get('lost_bets', ))
        message += 'Current Punishment:\t'
        if member_doc.get('current_punishment', None):
            message += '{}\tends: {}\n'.format(member_doc['current_punishment']['name'], format_date(member_doc['current_punishment']['end_date']))
        else:
            message += 'None\n'
        message += 'Punishment Queue:\n'
        for punishment in member_doc.get('punishment_nicknames', []):
            message += '\t{}\t{} day(s)\n'.format(punishment['punishment_nickname'], punishment['duration'])
        
        message += '```'
        await client.say(message)
    else:
        await client.say(name + ' not recognized as a user on this server. Make sure capitalization is correct and try again')


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
    punishments.append({'duration': bet.duration, 'punishment_nickname': bet.punishment_nickname})
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

@client.command(name='cancel',
                description='Cancel a bet that you made before someone else has accepted it',
                brief='Cancel a bet',
                aliases=['Cancel'],
                pass_context=True)
async def cancel(context, bet_display_id):
    bet = check_display_id(bet_display_id)
    if not bet:
        return
    
    user_id = context.message.author.id

    if bet.state != HonorBet.open_state:
        await client.say('Bet {} is not in the open state, so you can not cancel it'.format(bet.display_id))
        return
    if bet.player1 != user_id:
        await client.say('You did not create Bet {}, so you can not cancel it'.format(bet.display_id))
        return
    
    bet.state = HonorBet.closed_state
    bet_collection.update_bet(bet)

    await client.say('Bet {} has been canceled'.format(bet.display_id))

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

@client.command(name='punishment',
                description='Accept your punishment after setting your nickname to the required nickname',
                brief='Accept your punishment',
                aliases=['accept_punishment', 'acceptPunishment'],
                pass_context='true')
async def punishment(context):
    user = context.message.author

    user_doc = user_collection.find_user(user.id)

    if user_doc.get('current_punishment') is not None:
        # Make sure that the date didn't get mistakenly not erased
        if user_doc['current_punishment']['end_date'] < datetime.now():
            user_doc['current_punishment'] = None
            user_collection.update_user(user_doc)
        else:
            await client.say('Your current punishment is not yet expired, wait until {} and get your next punishment'.format(format_date(user_doc['current_punishment']['end_date'])))
            return

    punishments = user_doc.get('punishment_nicknames', [])
    if len(punishments) > 0:
        if user.nick != punishments[0]['punishment_nickname']:
            await client.say('Your nickname is not set up to match the punishment, set your nickname to \"{}\" and run the command again'.format(punishments[0]['punishment_nickname']))
            return
        user_doc['current_punishment'] = {}
        user_doc['current_punishment']['end_date'] = datetime.now() + timedelta(days=punishments[0]['duration'])
        user_doc['current_punishment']['name'] = punishments[0]['punishment_nickname']
        punishments.pop(0)

        user_collection.update_user(user_doc)

        await client.say('Your punishment has been recorded. You will be free from this punishment on {}'.format(format_date(user_doc['current_punishment']['end_date'])))
    else:
        await client.say('You currently do not have any punishments, so you have no fate to accept')

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
    message = 'Bet {}: {}\n\tCreated by: {}\n\tDuration: {} day(s)\n'.format(bet.display_id, bet.message, server.get_member(bet.player1), bet.duration)
    if bet.player2:
        message += '\tAccepted by: {}\n'.format(server.get_member(bet.player2))
    if bet.claimed_user:
        message += '\tClaimed by: {}\n'.format(server.get_member(bet.claimed_user))
        message += '\t\tLoser\'s nickname: {}\n'.format(bet.punishment_nickname)
    message += '\tState: {}\n'.format(bet.state)
    return message

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

def format_date(date):
    return date.strftime('%b %d, %Y %I:%M %p EST')

@client.event
async def on_ready():
    print("Logged in as " + client.user.name)

# randomly selects an item from the list of statuses and changes the current game to it. Updates every 10 minutes
async def update_status():
    await client.wait_until_ready()
    while not client.is_closed:
        await client.change_presence(game=Game(name=random.choice(statuses)))
        users = user_collection.get_all_users()
        for user in users:
            if user.get('current_punishment') is not None:
                if user['current_punishment']['end_date'] < datetime.now():
                    user['current_punishment'] = None
                    user_collection.update_user(user)
        await asyncio.sleep(600)


client.loop.create_task(update_status())
client.run(TOKEN)