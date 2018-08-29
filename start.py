import sys

#Add utilities folder to sys path
if not './utilities' in sys.path:
  sys.path.append('./utilities')


from utilities.Bot import Bot
from configparser import ConfigParser
import argparse

#Read arguments
parser = argparse.ArgumentParser(description="Start a bot in a specific workspace")
parser.add_argument('--token', '-t', default='bot_token_pw', help='Bot user token description')
parser.add_argument('--channel', '-c', default='#random', help='Default channel for bot')

namespace_object = parser.parse_args()
print(namespace_object)


#Read bot token from config
tokens = ConfigParser()
tokens.read('config/tokens.ini')
bot_token = tokens['Slack'][namespace_object.token]

#Create bot
bot_karsten = Bot('bot_karsten', bot_token, default_channel='#random')
bot_karsten.connect()

#Start
bot_karsten.listen()
