from slackbot.bot import Bot, default_reply, listen_to
import re
from lxml import html
import json
import requests
from datetime import datetime, timedelta

cache = {}

@default_reply
@listen_to('@murrays-menus')
def my_default_hanlder(message):
    now = datetime.now()
    
    if now.weekday() in [5, 6]:    
        message.reply("It's the weekend, you have to make your own lunch.")
        return

    if now.hour >= 14:
       now = now + timedelta(days=1)

    date = now.strftime('%d.%-m.%y')

    if date in cache:
        message.reply(cache[date])
        return

    r = requests.get('http://www.tkmenus.com/elior/marketfresh')
    tree = html.fromstring(r.text)
    menuJson = tree.xpath('//input[@id="menuJson"]')[0]
    menu = json.loads(menuJson.value)
    day = [x for x in menu['ms'] if date in x['n']][0]
    reply = '\n*--- MENU FOR {} ---*\n'.format(date)
    for item in day['ss'][0]['rs']:
        reply += '£{} *{}*\n'.format(item['sp'], item['n']) 

    cache[date] = reply
    message.reply(reply)

def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
