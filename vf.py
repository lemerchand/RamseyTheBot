# Load and setup logging
import logging as log
import pickle
from pathlib import Path
from rich.console import Console
from time import strftime, localtime
import pendulum as pend

c = Console()
TZ = 'America/Los_Angeles'

log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=log.INFO)


def save_user(pkl, USERDIR):
    try:
        filename = str(pkl.uid) + '.pkl'
        path = USERDIR / filename
        log.info('Attempting to save user object at ' + str(path))
        pickle.dump(pkl, open(path, 'wb'))
    except Exception:
        log.error('Shit be went down wrong')
        return False


def exists(list, i):
    """Checks for value in list"""
    try:
        return list[i]
    except IndexError:
        return None


def parse_for_list(text):
    remainder = ''
    args = []
    tags = []
    deadline = None
    timestamp = pend.now(tz=TZ)
    start_time = timestamp
    quantity = None

    # Separate arguments from text
    for i in text:
        if i.startswith('!'):
            args.append(i)
        elif i.startswith('#'):
            tags.append(i)
        elif i.startswith('^'):
            quantity = i[1:]
        elif i.startswith('@@'):
            deadline = pend.parse(i[2:], tz=TZ, strict=False) 
        elif i.startswith('@'):
            start_time = pend.parse(i[1:], tz=TZ, strict=False) 
        else:
            remainder += i + ' '

    tags = [None] if not tags else tags
    return remainder, args, quantity, tags, timestamp, start_time, deadline


def get_username_from_uid(users, uid):
    for user in users:
        if uid == user.id:
            return user
