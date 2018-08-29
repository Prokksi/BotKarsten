import os
import json
import uuid
from apiclient.discovery import build
from configparser import ConfigParser
import requests
import argparse
import time

class Function_Helper:

    tokens = None

    def __init__(self):

        #Read tokens from config
        tokens = ConfigParser()
        tokens.read('config/tokens.ini')

        self.tokens = tokens



    #define custom functions in here

    #SIMPLE ACTIONS

    # def self_shutdown(self):
    #
    #     os.system('shutdown -h now')
    #
    #     return 'Bye, bye'


    #COMMANDS

    def get_meme(self, bot, cmd, text):

        #Get parameters
        params = text.replace(cmd, '')
        #params = text.split(' ')

        #search in image library for matching images
        images = bot.image_library['images']
        max_cnt = 0
        image_url = None
        for image in images:
            if image['type'] == 'meme':
                hit_cnt = 0
                for key in image['keys']:
                    if key in params:
                        hit_cnt += 1

                #Check if enough hits and more hits than previously found image
                if  hit_cnt >= image['required_hits'] and hit_cnt > max_cnt:
                    image_url = image['url']

        #optional: read out caption for picture from library

        if image_url:
            return ['', [{"fallback": "spicy meme", "image_url": image_url }]]


        #just do a google image search, lol
        developer_key = self.tokens['Google']['developer_key']
        cx = self.tokens['Google']['custom_search_meme']

        service = build("customsearch", "v1", developerKey=developer_key)
        res = service.cse().list(
            q=params,
            cx=cx,
            searchType='image',
            num=1,
            #imgType='clipart',
            #fileType='png',
            safe= 'off'
        ).execute()

        if 'items' in res:
            items = res.get('items')
            item = items[0]
            link = item.get('link')

            return ['', [{"fallback": "spicy meme", "image_url": link }]]


        #Well, when nothong helps, do this
        return ['No image with your keywords found, sorry buddy', None]


    def get_image(self, bot, cmd, text):

        #Get parameters
        params = text.replace(cmd, '')

        #search in image library for matching images
        images = bot.image_library['images']
        max_cnt = 0
        image_url = None
        for image in images:
            hit_cnt = 0
            for key in image['keys']:
                if key in params:
                    hit_cnt += 1

            #Check if enough hits and more hits than previously found image
            if  hit_cnt >= image['required_hits'] and hit_cnt > max_cnt:
                image_url = image['url']

        #optional: read out caption for picture from library

        if image_url:
            return ['', [{"fallback": "spicy meme", "image_url": image_url }]]


        #just do a google image search, lol
        cx = self.tokens['Google']['custom_search_meme']
        link = self.image_search(cx, params)

        if link:
            return ['', [{"fallback": "spicy meme", "image_url": link }]]
        else:
            return ['No image with your keywords found, sorry buddy', None]




    def image_search(self, cx, keywords):

        developer_key = self.tokens['Google']['developer_key']
        cx = self.tokens['Google']['custom_search_meme']

        service = build("customsearch", "v1", developerKey=developer_key)
        res = service.cse().list(
            q=keywords,
            cx=cx,
            searchType='image',
            num=1,
            #imgType='clipart',
            #fileType='png',
            safe= 'off'
        ).execute()

        if 'items' in res:
            items = res.get('items')
            item = items[0]
            link = item.get('link')

            return link

        else:
            return None


    def teach_reaction(self, bot, cmd, text):

        #Get parameters
        # param = text.replace(cmd, '')
        # #params = text.split(' ')
        #
        # #try to parse
        # try:
        #     reaction_obj = json.loads(param)
        #
        # except Exception as e:
        #     print(e)
        #     return ['Parameter is not a valid reaction object', None]
        #
        # #print('parsed')
        #
        # #check basic structure
        # for key in ['matches', 'responses']:
        #     if not key in reaction_obj.keys():
        #         #print(key)
        #         return ['Parameter is not a valid reaction object', None]


        params = text.replace(cmd, '')
        params = params.strip()

        #Read arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--tags', '-t', nargs='+')
        parser.add_argument('--required-hits', '-rh')
        parser.add_argument('--responses', '-r', nargs='+')

        #help_text = 'View weather for a location\n\nParameters:\n\nRequired:\n-z, --zip\tPostcode/Zipcode\nor\n-c, --city\tCity name\n\nOptional:\n-t, --type\tSupply forecast for n day forecast\n-d, --days\tAmount of days forecast (up to 5)'
        help_text = 'Wrong usage'

        try:
            namespace_object = parser.parse_args(params.split())
            print(namespace_object)

        #Prevents parser from exiting script
        except SystemExit:
            return [help_text, None]

        #Check if all supplied
        if not namespace_object.tags or not namespace_object.required_hits or not namespace_object.responses:
            return [help_text, None]

        #Clean
        #keys = namespace_object.tags.split(',')
        #keys = [key.strip() for key in keys]
        keys = ' '.join(namespace_object.tags).split(',')
        keys = [key.strip() for key in keys]
        print(keys)

        try:
            required_hits = int(namespace_object.required_hits)
        except ValueError as e:
            return [help_text, None]

        #responses = namespace_object.responses.split(',')
        #responses = [key.strip() for response in responses]
        responses = ' '.join(namespace_object.responses).split(',')
        responses = [response.strip() for response in responses]

        #Build json
        reaction = {}
        reaction['matches'] = [{
            "keys": keys,
            "required_hits": required_hits,
            "type": "key"
        }]
        reaction['responses'] = {
            "default": {
                "values": responses,
                "type": "text"
            }
        }


        #generate uuid
        obj_uuid = str(uuid.uuid4())

        reactions = bot.text_conf['reactions']
        reactions[obj_uuid] = reaction

        #save json file
        with open(bot.text_conf_location, 'w') as f:
            json.dump(bot.text_conf, f)

        return ['Reaction successfully added', None]



    def save_meme(self, bot, cmd, text):

        param = text.replace(cmd, '')

        #remove automatically added symbols
        param = param.replace('<', '')
        param = param.replace('>', '')

        #try to parse
        try:
            image_obj = json.loads(param)

        except Exception as e:
            print(e)
            return ['Parameter is not a valid image object', None]

        #check basic structure
        for key in ['keys', 'url']:
            if not key in image_obj.keys():
                #print(key)
                return ['Parameter is not a valid image object', None]


        images = bot.image_library['images']
        images.append(image_obj)

        #save json file
        with open(bot.image_library_location, 'w') as f:
            json.dump(bot.image_library, f)

        return ['Image successfully added', None]


    def give_subreddit(self, bot, cmd, text):

        param = text.replace(cmd, '')
        param = param.strip()

        url = 'https://www.reddit.com/r/' + param
        return [url, None]


    def find_weather(self, bot, cmd, text):

        params = text.replace(cmd, '')
        params = params.strip()

        #Pattern: weather [--type][--city or --zip]
        parser = argparse.ArgumentParser(description='Weather api arguments')
        parser.add_argument('--type', '-t')
        parser.add_argument('--city', '-c')
        parser.add_argument('--zip', '-z')
        parser.add_argument('--days', '-d')

        help_text = 'View weather for a location\n\nParameters:\n\nRequired:\n-z, --zip\tPostcode/Zipcode\nor\n-c, --city\tCity name\n\nOptional:\n-t, --type\tSupply forecast for n day forecast\n-d, --days\tAmount of days forecast (up to 5)'

        try:
            namespace_object = parser.parse_args(params.split())
            print(namespace_object)

        #Prevents parser from exiting script
        except SystemExit:
            return [help_text, None]


        #Build url
        api_key = self.tokens['OpenWeatherMap']['api_key']
        base_url = 'http://api.openweathermap.org/data/2.5/'

        if namespace_object.type:
            endpoint = namespace_object.type
        else:
            endpoint = 'weather'

        if namespace_object.zip:
            dest = 'zip=' + namespace_object.zip + ',de'
        elif namespace_object.city:
            dest = 'q=' + namespace_object.city + ',de'
        else:
            return [help_text, None]

        url = base_url + endpoint + '?' + dest + '&units=metric&APPID=' + api_key
        print(url)


        #Api request
        response = requests.get(url)
        response_json = response.json()
        #print(response.content)


        #Build response (maybe use attachments and/or slack message formatting?)
        text = ''
        if endpoint == 'weather':
            text += 'Current weather for ' + response_json['name'] + '\n'
            text += 'Description: ' +  response_json['weather'][0]['description'] + '\n'
            text += 'Mean Temperature: ' + str(response_json['main']['temp']) + '\n'
            text += 'Min Temperature: ' + str(response_json['main']['temp_min']) + '\n'
            text += 'Max Temperature: ' + str(response_json['main']['temp_max']) + '\n\n'


        elif endpoint == 'forecast':

            #Limit amount of days
            if namespace_object.days:
                limit = float(namespace_object.days)
            else:
                limit = 1

            #there is one entry per 3 hours -> 8 entries per day
            amt_entries = int(limit * 8)
            flist = response_json['list']
            #reduce list
            flist = flist[:amt_entries]

            #Place
            text += 'Weather forecast for ' + response_json['city']['name'] + '\n\n'

            for entry in flist:
                text += time.strftime("%d %b %Y %H:%M:%S %Z", time.localtime(entry['dt'])) + '\n'
                text += 'Description: ' +  entry['weather'][0]['description'] + '\n'
                text += 'Mean Temperature: ' + str(entry['main']['temp']) + '\n'
                text += 'Min Temperature: ' + str(entry['main']['temp_min']) + '\n'
                text += 'Max Temperature: ' + str(entry['main']['temp_max']) + '\n\n'

        return [text, None]
