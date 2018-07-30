from utilities.Bot import Bot
from configparser import ConfigParser    

#Read bot token from config
tokens = ConfigParser()
tokens.read('config/tokens.ini')
bot_token = tokens['Slack']['bot_token']

#Create bot
bot_karsten = Bot('bot_karsten', bot_token)
bot_karsten.connect()

#Start
bot_karsten.listen()
