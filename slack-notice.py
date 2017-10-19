#!/usr/bin/python

import argparse, requests, sys, psutil, socket, getpass

me = psutil.Process()
parent = ""
parentpid = -1
grandparent = ""
try:
    parent = str(psutil.Process(me.ppid()).cmdline()[0])
    parentpid = psutil.Process(me.ppid()).ppid()
except psutil.AccessDenied:
    pass
try:
    grandparent = str(psutil.Process(parentpid).cmdline()[0])
except AttributeError:
    pass
except psutil.AccessDenied:
    pass

parser = argparse.ArgumentParser(description="Post to a Slack webhook. The default webhook is stored in /etc/slack/webhook-notice . Pipe your message text in via stdin (echo 'my message' | slack-notice)" )

parser.add_argument('--description','-d', type=str, default="")
parser.add_argument('--iconemoji','-i', type=str, default="radio")
parser.add_argument('--messagefile','-m', type=argparse.FileType('r'), default=sys.stdin)
parser.add_argument('--noescape','-n',action='store_true')
parser.add_argument('--severity','-s', type=str, choices=['notice','error','warning'], default="notice")
parser.add_argument('--title','-t', type=str, default="")
parser.add_argument('--username','-u', type=str, default=parent)
parser.add_argument('--webhookfile','-w', type=argparse.FileType('r'), default="/etc/slack/webhook-notice")
# parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)

args = parser.parse_args()

colors = {'notice':'good','error':'danger','warning':'warning'}

webhook_url = args.webhookfile.read().strip()
message=args.messagefile.read().strip()

if args.noescape is not True:
    message = '```' + message + '```'

if args.severity == 'error' and args.description != None:
    args.description = "@channel"

slack_data = {
    'color': colors[args.severity],
    'text' : args.description,
    'icon_emoji' : ':' + str(args.iconemoji) + ':',
    'username' : args.username,
    'parse' : 'full',
    'attachments' : [ {
        'color': colors[args.severity],
        'title' : args.title,
        'text' : message,
        'fields' : [
            {
                "title": "Host",
                "value": socket.gethostname(),
                "short" : True
            },
            {
                "title": "Running as user",
                "value": getpass.getuser(),
                "short" : True
            },
            {
                "title": "Parent process",
                "value": parent,
                "short" : True
            },
            {
                "title": "Grandparent process",
                "value": grandparent,
                "short" : True
            }
        ]
        } ]
    }

slack_data['attachments'][0]['mrkdwn_in'] = ['text', 'pretext', 'fields']
slack_data['mrkdwn'] = True

# print(slack_data)
response = requests.post(
    webhook_url, json=slack_data,
    headers={'Content-Type': 'application/json'}
)
if response.status_code != 200:
    raise ValueError(
        'Request to slack returned an error %s, the response is:\n%s'
        % (response.status_code, response.text)
    )
