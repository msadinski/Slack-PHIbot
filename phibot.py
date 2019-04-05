import os
import time
from slackclient import SlackClient

# phibot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

PHI_DESCRIPTION = "Protected health information (PHI) should *NOT* be posted to slack.\nThis includes but is not limited to *MRNs*, *Exam Dates*, *Accession Numbers* and *Patient Names*.\n If you are not sure whether it can be posted, don't do it!" 

punctuation = '.,?!:()#\'"'

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def search_string(text):
    """
    Checks an input string for 8 digit numbers
    Returns none if nothing is found
    Returns text with the numbers converted to XXXXXXXX if something is found
    Ignores punctuation
    """
    text_stripped = text

    for character in punctuation:
        text_stripped = text_stripped.replace(character, ' ')

    trigger_list = [word for word in text.split(' ') if len(word) == 8 and word.isdigit()]
    if not trigger_list:
        return None
    
    for trigger in trigger_list:
        text = text.replace(trigger, 'XXXXXXXX')
    return text 

def set_phi_alert(output, triggered_text):
    """
    Handles the case where phi was found
    Deletes the original message and subs in the anonymized message
    Posts a warning message from the bot
    """
    #slack_client.api_call('chat.update', channel = output['channel'], text = triggered_text, ts = output['ts'], as_user=True)
    #slack_client.api_call('chat.delete', channel = output['channel'], ts = output['ts'])
    #slack_client.api_call('chat.postMessage', channel = output['channel'], user = output['user'], text = triggered_text) 
    slack_client.api_call('chat.postMessage', channel = output['channel'], text = 'WARNING! <@' + output['user'] + '> It looks like you might have posted a patient Identifier. Please resolve now.', as_user = True)

def handle_command(command, channel):
    """
    Receives commands directed at the bot and determines if they are valid commands
    If they are, acts on commands
    """
    response = 'Not sure what you mean. Use the *' + EXAMPLE_COMMAND + '* command.'
    if 'phi' in command.lower():
        response = PHI_DESCRIPTION
    elif command.startswith(EXAMPLE_COMMAND):
        response = "I'm sorry, I'm not programmed to respond to that yet."
    elif 'hello' in command.lower() or 'hi' in command.lower():
        response = 'Hi there.'        

    slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
    Returns none unless a message is directed at the bot, based on its ID
    This also scans the text for PHI and removes it if it finds something suspicious
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output:
                if AT_BOT in output['text']:
                    # return text after the @ mention, whitespace removed
                    return output['text'].split(AT_BOT)[1].strip().lower(), output['channel']
                else:
                    # check for PHI
                    triggered_text = search_string(output['text'])
                    if triggered_text:
                        print('PHI alert triggered by ' + output['user'])
                        set_phi_alert(output, triggered_text)
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 
    if slack_client.rtm_connect():
        print("PHIbot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Check for invalid Slack token or bot ID")
