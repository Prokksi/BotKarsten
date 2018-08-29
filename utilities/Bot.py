from slackclient import SlackClient
import time
import json
import os
import sys
from random import randint
import platform
from Functions import Function_Helper

class Bot:

    #bot variables

    #not changeable
    BOT_NAME = ''
    TOKEN = ''
    DM = 'D'
    CHANNEL = 'C'
    SLASH = '/'
    OWN_USER_ID = ''
    ICON = ':penguin:'

    #placeholders
    placeholders = ['USERNAME']

    #can change
    slack_connection = None
    default_channel = None
    language = 'en'
    home_dir = None
    text_resources_dir = None
    image_resources_dir = None
    text_conf_location = None
    image_library_location = None
    text_conf = None
    image_library = None


    def __init__(self, bot_name, token, language='en', default_channel='#random', home_dir=None):

        #Check os
        running_on = platform.system()
        if running_on == 'Linux':
            self.SLASH = '/'
        elif running_on == 'Windows':
            self.SLASH = '\\'

        #Save parameters
        self.BOT_NAME = bot_name
        self.TOKEN = token
        self.language = language
        self.default_channel = default_channel

        if home_dir:
            self.home_dir = home_dir
        else:
            self.home_dir = os.getcwd() + self.SLASH

        self.text_resources_dir = self.home_dir + 'text_resources' + self.SLASH
        self.image_resources_dir = self.home_dir + 'image_resources' + self.SLASH
        self.text_conf_location = self.text_resources_dir + self.language + self.SLASH + 'conf.json'
        self.image_library_location = self.image_resources_dir + self.language + self.SLASH + 'library.json'


        #Import configuration
        with open(self.text_conf_location) as f:
            self.text_conf = json.load(f)

        #Import image library
        with open(self.image_library_location) as f:
            self.image_library = json.load(f)

        #Create function helper
        self.function_helper = Function_Helper()



    def connect(self, channel=None):

        if channel is None:
            channel = self.default_channel

        #set up client
        self.slack_connection = SlackClient(self.TOKEN)

        #get own user id
        res = self.slack_connection.api_call(
            "users.list"
        )
        members = res['members']
        for member in members:
            if member['name'] == self.BOT_NAME:
                own_user_id = member['id']
                #print(own_user_id)
                break
        else:
            print('Error: Bot user not in members')
            sys.exit(1)

        self.OWN_USER_ID = own_user_id


        #Hello message
        greetings = self.text_conf['greetings']
        text = self.get_random(greetings)
        self.send_message(text, None, channel)

        print('connected...')


    def listen(self, all_messages=False):

        if not self.slack_connection:
            print('Error: No slack connection established')
            sys.exit(1)

        sc = self.slack_connection

        #start rtm
        print('trying RTM listening...')
        if sc.rtm_connect(with_team_state=False):
            #wait for slack hello message

            while True:
                response = sc.rtm_read()

                if response:
                    msg = response[0]
                    type = msg['type']

                    if type != 'hello':
                        print('Error: RTM connection failed')
                        sys.exit(1)

                    print('RTM connection successful!')
                    break

                time.sleep(1)




            #start listening
            print('waiting for user messages...')
            while True:
                response = sc.rtm_read()
                if response:
                    try:
                        for msg in response:

                            #Ignore everything but user text messages
                            if 'client_msg_id' in msg.keys():
                                #Read out message info
                                text = msg['text']
                                user = msg['user']
                                channel = msg['channel']
                                print('Message before cleaning: ' + text)

                                result = self.message_valid(text, channel)
                                valid = result[0]
                                bot_mentioned = result[1]

                                if not valid:
                                    #Ignore message
                                    continue

                                user_name = self.identify_user(user)
                                print('Message from: ' + user_name)


                                if bot_mentioned:
                                    to_replace = '<@' + self.OWN_USER_ID + '>'
                                    text = text.replace(to_replace, '')
                                    text = text.strip()


                                #initialize reponse
                                response = [None, None]
                                #response[0] = None   #this is for the text
                                #response[1] = None   #this is for attachments

                                #check for fitting command
                                cmd_reaction_id = self.find_command(text, user_name)
                                if cmd_reaction_id is not None:
                                    response = self.apply_command(cmd_reaction_id, text, user)

                                else:
                                    text_clean = self.clean_message(text)
                                    print('Message after cleaning: ' + text_clean)

                                    possible_reactions = self.match_reactions(text_clean)

                                    if possible_reactions:
                                        chosen_reaction = self.find_best_reaction(possible_reactions)
                                        response = self.trigger_reaction(chosen_reaction, user)
                                    else:
                                        response[0] = self.get_random(self.text_conf['no_reaction'])

                                response_text = response[0]
                                attachments = response[1]

                                #add replacements here
                                replacements = [user_name]
                                response_text = self.replace_placeholders(response_text, replacements)

                                self.send_message(response_text, attachments, channel)

                    except Exception as e:
                        print(e)

                time.sleep(1)

        else:
            print("Error: RTM connection failed")
            sys.exit(1)





    def message_valid(self, message, channel):

        #Check if direct message or in channel or something else
        channel_type = channel[:1]
        bot_mentioned = self.OWN_USER_ID in message

        if not channel_type in [self.DM, self.CHANNEL]:
            print('Unknown channel type')
            #unknown
            return (False, False)


        if channel_type == self.CHANNEL:
            if not bot_mentioned:
                print('not mentioned in channel message - skipping...')
                #channel + not mentioned
                return (False, False)

            #channel + mentioned
            return (True, True)

        else:
            if not bot_mentioned:
                #dm + not mentioned
                return (True, False)

            #dm + mentioned
            return (True, True)



    def clean_message(self, message):

        #remove unwanted characters
        replace_list = ['.', ',', '!', '?']
        for c in replace_list:
            message = message.replace(c, '')

        #To avoid case sensitivity, everything is kept lower case
        message = message.lower()

        #delete leading or trailing whitespaces
        message = message.strip()

        return message


    def identify_user(self, user):
        #get user info
        res = self.slack_connection.api_call(
            "users.info",
            user=user
        )
        user_obj = res['user']
        user_name = user_obj['real_name']

        return user_name


    def match_reactions(self, text):
        reactions = self.text_conf['reactions']
        reaction_ids = reactions.keys()

        possible_reactions = []
        for reaction_id in reaction_ids:
            reaction = reactions[reaction_id]
            matches = reaction['matches']

            exact_hits = 0
            key_hits = 0
            confidence = 0
            reaction_accepted = False

            for match in matches:
                type = match['type']

                if type == 'exact':
                    #print('exact')
                    for key in match['keys']:
                        if key.lower() == text:
                            #print('exact hit')
                            exact_hits += 1

                            #Acknowledge that response is qualified
                            reaction_accepted = True


                elif type == 'key':
                    #print('key')
                    for key in match['keys']:
                        if key in text and self.is_separated(text, key):
                            #print('key hit')
                            key_hits += 1

                    if key_hits >= match['required_hits']:
                        if 'must_hit' in match.keys():
                            for key in match['must_hit']:
                                if key in text:
                                    key_hits += 1
                                else:
                                    break
                            else:
                                #enough hits + all must hits --> qualified
                                reaction_accepted = True
                        else:
                            #enough hits --> qualified
                            reaction_accepted = True


            if reaction_accepted:

                confidence = (exact_hits * 10) + key_hits

                entry = {
                    "id": reaction_id,
                    "confidence": confidence
                }
                possible_reactions.append(entry)

        return possible_reactions



    def find_best_reaction(self, possible_reactions):
        chosen_reaction = None
        for possible_reaction in possible_reactions:
            if chosen_reaction is None:
                chosen_reaction = possible_reaction
            else:
                if possible_reaction['confidence'] > chosen_reaction['confidence']:
                    chosen_reaction = possible_reaction

        return chosen_reaction



    def trigger_reaction(self, chosen_reaction, user):
        reactions = self.text_conf['reactions']
        reaction = reactions[chosen_reaction['id']]
        responses = reaction['responses']

        if user in responses.keys():
            response = responses[user]
        else:
            response = responses['default']

        if response['type'] == 'text':
            values = response['values']
            response_text = self.get_random(values)
        elif response['type'] == 'action':
            function_name = response['function']
            response_text = getattr(self.function_helper, function_name)()

        return [response_text, None]


    def send_message(self, text, attachments, channel):
        self.slack_connection.api_call(
            "chat.postMessage",
            channel=channel,
            text=text,
            icon_emoji=self.ICON,
            attachments=attachments,
            unfurl_media=True,
            unfurl_links=True
        )


    def find_command(self, text, user_name):

        reactions = self.text_conf['reactions']
        reaction_ids = reactions.keys()

        #possible_reactions = []
        for reaction_id in reaction_ids:
            reaction = reactions[reaction_id]
            matches = reaction['matches']

            for match in matches:
                if match['type'] == 'command':
                    #check if command fits
                    if text.startswith(match['pattern']):
                        #save id
                        return reaction_id

                    #Ignore all other matches of this reaction
                    #(only one command pattern per reaction)
                    break

        return None


    def apply_command(self, reaction_id, text, user):

        #find response
        reactions = self.text_conf['reactions']
        reaction = reactions[reaction_id]

        #get command text
        for match in reaction['matches']:
            if match['type'] == 'command':
                cmd = match['pattern']
                break

        responses = reaction['responses']
        if user in responses.keys():
            response = responses[user]
        else:
            response = responses['default']

        function_name = response['function']
        response = getattr(self.function_helper, function_name)(self, cmd, text)

        return response


    def is_separated(self, text, word):
        first_letter = text.find(word)
        last_letter = first_letter + len(word) - 1

        letter_before = first_letter - 1
        following_letter = last_letter + 1

        #check if word is not at beginning
        if letter_before != -1:
            #check if beginning is not separated
            if text[letter_before] != ' ':
                return False

        #check if word is not at end
        if following_letter != len(text):
            #check if end is not separated
            if text[following_letter] != ' ':
                return False

        return True



    def replace_placeholders(self, text, replacements):
        for i in range(0, len(self.placeholders)):
            #TODO: use split + join to enable multiple replacements
            text = text.replace(self.placeholders[i], replacements[i])

        return text


    def get_random(self, options):
        return options[randint(0, len(options) - 1)]
