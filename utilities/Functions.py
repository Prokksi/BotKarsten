import os
import json
import uuid
from apiclient.discovery import build

class Function_Helper:

    #define custom functions in here

    #SIMPLE ACTIONS

    def self_shutdown(self):

        os.system('shutdown -h now')

        return 'Bye, bye'


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
            hit_cnt = 0
            for key in image['keys']:
                if key in params:
                    hit_cnt += 1

            if  hit_cnt > max_cnt:
                image_url = image['url']

        #optional: read out caption for picture from library

        if image_url:
            return ['', [{"fallback": "spicy meme", "image_url": image_url }]]

        
        #just do a google image search, lol
        service = build("customsearch", "v1", developerKey="")
        res = service.cse().list(
            q=params,
            cx='',
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


    def teach_reaction(self, bot, cmd, text):

        #Get parameters
        param = text.replace(cmd, '')
        #params = text.split(' ')

        #try to parse
        try:
            reaction_obj = json.loads(param)

        except Exception as e:
            print(e)
            return ['Parameter is not a valid reaction object', None]

        #print('parsed')

        #check basic structure
        for key in ['matches', 'responses']:
            if not key in reaction_obj.keys():
                #print(key)
                return ['Parameter is not a valid reaction object', None]

        #generate uuid
        obj_uuid = str(uuid.uuid4())

        reactions = bot.text_conf['reactions']
        reactions[obj_uuid] = reaction_obj

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
