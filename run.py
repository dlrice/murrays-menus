from slackbot.bot import Bot, default_reply, listen_to
import re
from lxml import html
import json
import requests
from datetime import datetime, timedelta

cache = {}
NOT_WORD_CHARACTERS = re.compile(r'\W+')
DAYS_OF_WEEK = ['monday', 'tuesday', 'wednesday','thursday','friday', 'saturday', 'sunday']
WEEKDAYS = ['monday', 'tuesday', 'wednesday','thursday','friday']
WEEKEND = ['saturday', 'sunday']

@default_reply
@listen_to('@murrays-menus')
def defaultHanlder(message):
    
    now = datetime.now()
    nowWeekday = now.strftime('%A').lower()
    if now.weekday() in [5, 6]:
        message.reply("It's the weekend and the lunch Gods haven't posted a menu yet. Try again Monday morning.")
        return

    messageText = message.body['text']
    if messageText:
        days = getDaysFromMessage(messageText)
    else:
        days = set([nowWeekday])

    # Determine what days we can get a menu for
    late = ''
    if (now.hour >= 14) and (nowWeekday in days):
        days.remove(nowWeekday)
        if nowWeekday == 'friday':
            nextFriday = now + timedelta(weeks=1)
            if nextFriday.month != now.month:
                sentence = "Don't worry about lunch, it's Drinks & Nibbles at 4pm!"
            else:
                sentence = "You're too late, it's already after 2pm!"
        else:
            sentence = "You're too late, it's already after 2pm!"
        late = formatLine(nowWeekday, sentence)

    # Days in the past
    pastDays = set(DAYS_OF_WEEK[:now.weekday()])
    intersection = pastDays.intersection(days)
    history = []
    for day in intersection:
        history.append(day)
    days.difference_update(intersection)

    weekend = days.intersection(WEEKEND)
    days.difference_update(weekend)
    
    good2go = {}
    for day in days:
        good2go[day] = getMenu(day)

    reply = ''
    if history:
        reply += formatLine(history, "Why do you care about the past?")

    reply += late + '\n'
    
    for day in sortDays(good2go):
        menu = good2go[day]
        day = formatDays([day])
        reply += '{}\n{}\n'.format(day, menu)
    
    if weekend:
        reply += formatLine(weekend, 'Get your own food.')

    if not reply.strip():
        reply = "Hmmm... I didn't understand that. Maybe you're too hungry to type properly?"
    
    reply += "\n\n*P.S. Mari don't forget that you are vegetarian for this month! Stay committed to the cause.*"

    message.reply(reply)

def formatLine(days, sentence):
    days = formatDays(days)
    return '{}: {}\n'.format(days, sentence)

def formatDays(days):
    days = sortDays(days)
    days = [titleCase(day) for day in days]
    days = ', '.join(days)
    return '*{}*'.format(days)
    
def getMenu(day):
    date = getDate(day)
    if date in cache:
        return cache[date]
    
    r = requests.get('http://www.tkmenus.com/elior/marketfresh')
    tree = html.fromstring(r.text)
    menuJson = tree.xpath('//input[@id="menuJson"]')[0]
    menu = json.loads(menuJson.value)
    menuDay = [x for x in menu['ms'] if day in x['n'].lower()][0]
    reply = ''
    for item in menuDay['ss'][0]['rs']:
        if 'n' in item:
            dish = item['n']
            if 'sp' in item:
                price = item['sp']
                reply += '*£{}* {}\n'.format(price, dish) 
            else:
                reply += '{}\n'.format(dish)
    cache[date] = reply
    return reply


def sortDays(days):
    return sorted(days, key=lambda x: DAYS_OF_WEEK.index(x))


def getDate(day):
    now = datetime.now()
    delta = DAYS_OF_WEEK.index(day) - now.weekday()
    date = now + timedelta(days=delta)
    return date.strftime('%x')


def getDaysFromMessage(messageText):
    messageText = messageText.lower()
    tokens = set(NOT_WORD_CHARACTERS.split(messageText))
    now = datetime.now()

    if 'today' in tokens:
        dayName = now.strftime('%A').lower()
        tokens.add(dayName)

    if 'tomorrow' in tokens:
        tomorrow = now + timedelta(days=1)
        dayName = tomorrow.strftime('%A').lower()
        tokens.add(dayName)

    if 'week' in tokens:
        tokens.update(WEEKDAYS)

    set_DAYS_OF_WEEK = set(DAYS_OF_WEEK)
    return set_DAYS_OF_WEEK.intersection(tokens)

def titleCase(word):
    return word[0].upper() + word[1:].lower()

def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
