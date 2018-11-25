# # Work with Python 3.6
import discord
from json import load

with open('auth.json') as auth_file:
    TOKEN = load(auth_file)['token']

K_INITIAL_USER_HONOR = 100.0

client = discord.Client()

honorPool = {}

print("now is when I should pull data from other place")

def get_help_message():
    return "```Honor Bot Commands:\n!help: shows list of commands\n!myhonor: displays how much honor you have```"

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    
    if not message.content.startswith('!'):
        return

    serverHash = hash(message.server)

    if not serverHash in honorPool:
        print("doing initial setup of server")
        honorPool[serverHash] = {}

        for member in message.server.members:
            if member != client.user:
                honorPool[serverHash][hash(member)] = K_INITIAL_USER_HONOR

    if message.content.startswith('!help'):
        await client.send_message(message.channel, get_help_message())

    if message.content.startswith('!myhonor'):
        msg = '{0.author.mention} has {1} honor'.format(message, honorPool[serverHash][hash(message.author)])
        await client.send_message(message.channel, msg)

    #if message.content.startswith('!addhonor'):
        # need to figure out best way to parse username from input. Username can have like emoji and spaces and stuff, so it's not super simple


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

    

client.run(TOKEN)
