import sys

#Add utilities folder to sys path
if not './utilities' in sys.path:
  sys.path.append('./utilities')


from utilities.Bot import Bot
from configparser import ConfigParser    

#Read bot token from config
tokens = ConfigParser()
tokens.read('config/tokens.ini')
bot_token = tokens['Slack']['bot_token2']

#Create bot
bot_karsten = Bot('bot_karsten', bot_token, default_channel='#general')
bot_karsten.connect()

#Start
bot_karsten.listen()
