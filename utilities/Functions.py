import os
import json
import uuid
from apiclient.discovery import build
from configparser import ConfigParser
import requests
import argparse
import time
import gitlab

class Function_Helper:

    tokens = None

    def __init__(self):

        #Read tokens from config
        tokens = ConfigParser()
        tokens.read('config/tokens.ini')

        self.tokens = tokens

        self.searcher = Google_Searcher()
        self.gc = Gitlab_Connector()

    #define custom functions in here

    #SIMPLE ACTIONS

    # def self_shutdown(self):
    #
    #     os.system('shutdown -h now')
    #
    #     return 'Bye, bye'


    #COMMANDS



    def print_help(self, bot, cmd, text):
        params = text.replace(cmd, '')
        params = params.strip()

        reactions = bot.text_conf['reactions']

        if params == '':
            #Get own helptext
            helptext = get_helptext(reactions, 'help')
            usage = '\nUsage: '
            return [helptext, None]
        
        else:
            #Get helptext of command
            helptext = get_helptext(reactions, params)
            return [helptext, None]



    def list_commands(self, bot, cmd, text):

        reactions = bot.text_conf['reactions']

        command_list = list()
        for reaction in reactions.values():
            for match in reaction.get('matches'):
                if match.get('type') == 'command':
                    command_list.append(match.get('pattern'))

        return [', '.join(command_list), None]


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
        link = self.searcher.search('custom_search_meme', params, search_type='image')

        if link:
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
        link = self.searcher.search('custom_search_images', params, search_type='image')
        print(link)


        if link:
            return ['', [{"fallback": "spicy meme", "image_url": link }]]
        else:
            return ['No image with your keywords found, sorry buddy', None]



    def google(self, bot, cmd, text):

        #Get parameters
        params = text.replace(cmd, '')

        parser = argparse.ArgumentParser()
        parser.add_argument('keywords', nargs='*')
        parser.add_argument('--number', '-n', nargs='?', default=1)

        help_text = 'Wrong usage'

        try:
            namespace_object = parser.parse_args(params.split())
            print(namespace_object)

        #Prevents parser from exiting script
        except SystemExit:
            return [help_text, None]

        
        num = namespace_object.number
        keywords = ' '.join(namespace_object.keywords)
    
        #Perform google search
        links = self.searcher.search('custom_search_full', keywords, num_results=num)


        if links:
            return [links, None]
        
        return ['Nothing found', None]





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
        except ValueError:
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


    #Gitlab wrapper

    def get_issues(self, bot, cmd, text):
        issues = self.gc.get_issues()
        return [issues, None]

    def get_users(self, bot, cmd, text):
        users = self.gc.get_users()
        return [users, None]
    
    def assign_user(self, bot, cmd, text):
        params = text.replace(cmd, '')
        params = params.strip()
        parts = params.split()

        if len(parts) == 2:
            #Only relevant information
            user, iid = parts
        elif len(parts) == 3:
            #Remove linkage word
            user, _, iid = parts
        else:
            return ['Wrong amount of parameters. Check \'help assign user\'.', None]

        msg = self.gc.assign_user(user, iid)

        return [msg, None]



class Google_Searcher():

    service = None

    def __init__(self):
        
        tokens = ConfigParser()
        tokens.read('config/tokens.ini')

        self.tokens = tokens


    def search(self, search_engine, keywords, search_type=None, num_results=1):

        if self.service is None:
            developer_key = self.tokens['Google']['developer_key']
            self.service = build("customsearch", "v1", developerKey=developer_key)

        cx = self.tokens['Google'][search_engine]
    
        res = self.service.cse().list(
            q=keywords,
            cx=cx,
            num=num_results,
            searchType=search_type,
            safe='off'
        ).execute()

        
        if 'items' in res.keys():
            items = res.get('items')
            
            links = ''
            for item in items:
                links += item.get('link') + '\n'
            
            return links
        
        return None


class Gitlab_Connector():

    connection = None
    project = None

    def __init__(self):

        tokens = ConfigParser()
        tokens.read('config/tokens.ini')

        self.tokens = tokens
    
    def _connect(self):

        url = self.tokens['Gitlab']['url']
        project_id = self.tokens['Gitlab']['project_id']
        api_key = self.tokens['Gitlab']['api_key']

        self.connection = gitlab.Gitlab(url, private_token=api_key)
        self.project = self.connection.projects.get(project_id, lazy=True)


    def _get_user(self, name):
        user = self.connection.users.list(username=name)
        if len(user) == 0:
            return None

        return user[0]


    def get_users(self):
        users = self.connection.users.list(all=True)
        res = ''
        for user in users:
            res += user.attributes.get('username') + '\n'

        return res

    
    def get_issues(self):

        if self.connection is None:
            self._connect()
        
        issues = self.project.issues.list(state='opened', all=True)

        res = ''
        for issue in issues:
            iid = issue.attributes.get('iid')
            title = issue.attributes.get('title')
            url = issue.attributes.get('web_url')
            res += '#' + str(iid) + ' ' + title + ' (' + url + ')\n'

        return res


    def assign_user(self, username, iid):

        if self.connection is None:
            self._connect()

        user = self._get_user(username)
        if user is None:
            return 'No user with name ' + username + ' found.'
  
        try:
            issue = self.project.issues.get(iid, lazy=True)

        except gitlab.exceptions.GitlabGetError as e:
            return 'Issue with id ' + iid + ' not found.'
        
        issue.assignee_id = user.id
        issue.save()

        return 'Successfully assigned ' + username + ' to issue ' + str(iid) + '.'



#Utils

def get_helptext(reactions, command):
        for reaction in reactions.values():
            for match in reaction.get('matches'):
                if match.get('command') == command:
                    if 'helptext' in match.keys():
                        return match.get('helptext') + '\n\nUsage: ' + match.get('pattern')
                    else:
                        return 'No help available'
        
        return 'Could not find specified command'
