#!/home/n02/n02/fcm/metomi/conda/mambaforge/bin/python

import sys
sys.path.insert(0,'/home/n02/n02/fcm/metomi/conda/mambaforge/lib/python3.10')

import argparse
import http
import json
import urllib3

# Send Slack notification based on the given message
def slack_notification(message):
    webhook_url = 'https://hooks.slack.com/services/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'
    try:
        slack_message = {'text': message}

        http = urllib3.PoolManager()
        response = http.request('POST',
                                webhook_url,
                                body = json.dumps(slack_message),
                                headers = {'Content-Type': 'application/json'},
                                retries = False)
    except:
        traceback.print_exc()

    return True

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('event')
    parser.add_argument('suite')
    parser.add_argument('id')
    parser.add_argument('message')
    args = parser.parse_args()


    message = '*{}*: ERROR {} {} '.format(args.suite, args.id, args.message)
    slack_notification(message)


