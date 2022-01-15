# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Ramsey (for Telegram)
# By: Lemerchand
#
# LAST MODIFICATION:
# 1/15/2022 @  2:30pm
# 7/1/2021  @  10pm
#
#   TODO:
#       + Refactor and abstract
#       +
#       +
#
# cspell:disable
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import lists
from weather import getweather
import imdb
from random import randint
from collections import namedtuple
from richlog import dbg
import pendulum as pend
# Load the Telegram lib
from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    # ReplyKeyboardRemove,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
)

from rich.console import Console

from telegram__token import telegram_token
import re
from vf import *
from pathlib import Path
from string import ascii_lowercase as az
import random
import wolframalpha

wolf = wolframalpha.Client('G9QEXJ-TTYY8Y9JUQ')

# Setup updater without token and alias the dispatcher for ease
updater = Updater(
    token=telegram_token,
    use_context=True
)
# cSPell:enable
######################################################################
#   Misc Init
######################################################################

# Dispatcher Shortcut
dp = updater.dispatcher
jobs = updater.job_queue

# imdb
mdb = imdb.IMDb()

# Console
c = Console()


# Open Rooms
open_files = {}

MAINDIR = Path.cwd()
DATADIR = MAINDIR / 'data'
USERDIR = DATADIR / 'users'

######################################################################
#  Conversation States, Buttons, Keyboards
######################################################################

# Generic lists entries get the 0s
NONE, FIRST, SECOND = 0, 1, 2
# Tracking lists get the 10s'
AWAIT_INSPECT_OR_DONE = 10
AWAIT_BACK_OR_OR_DONE = 11
# Movie lists
ADD_OR_DONE = 20
AWAIT_BACK_OR_ADD_OR_DONE = 21
AWAIT_ANOTHER_OR_DONE = 22
#
cur_state = NONE

BR_YN = [
    InlineKeyboardButton('Yes', callback_data=str('Yes')),
    InlineKeyboardButton('No', callback_data=str('No'))
]

BR_BACK_DONE = [
    InlineKeyboardButton('Back', callback_data=str('back')),
    InlineKeyboardButton('Done', callback_data=str('done'))
]

BR_ANOTHER_OR_DONE = [
    InlineKeyboardButton('Another', callback_data=str('random')),
    InlineKeyboardButton('Done', callback_data=str('done'))
]

BR_DONE = [InlineKeyboardButton('Done', callback_data=str('done'))]

BR_DEL = [
    InlineKeyboardButton('Delete', callback_data=str('del'))
]

BR_RANDOM = [
    InlineKeyboardButton('Random', callback_data=str('random'))
]

BR_ADD_OR_DONE = [
    InlineKeyboardButton('Add', callback_data=str('add')),
    InlineKeyboardButton('Done', callback_data=str('done'))
]

KBD_ADD_OR_DONE = InlineKeyboardMarkup(BR_ADD_OR_DONE)

KBD_BACK_DONE = InlineKeyboardMarkup(BR_BACK_DONE)

KBD_YN = [InlineKeyboardMarkup(BR_YN)]


RE_RANGE = re.compile(r'\d+\-\d+')


######################################################################
# Functions
######################################################################

# # # # # # # # # # # # # # # # # # # # #
#  Silly Stuff
# # # # # # # # # # # # # # # # # # # # #


def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Hello there, Dolly'
    )


def flip_coin(update, context):
    side = random.random()
    side = 'heads' if side >= .5 else 'tails'
    update.message.reply_text(
        'It landed on ' + side + '.'
    )


def roll_dice(update, context):
    args = context.args[0]
    text = ''
    diceRegex = r'(\d+)d(\d+)'
    match = re.match(diceRegex, args)
    q = match.group(1)
    t = match.group(2)
    for _ in range(int(q)):
        roll = random.randint(1, int(t))
        text += str(roll) + '\n'
    update.message.reply_text('You rolled...\n' + text)


def alarm(context):
    """Set this fucker off"""
    job = context.job
    context.bot.send_message(job.context, f'This is a reminder to {job.name}')


def list_timers(update, context):
    """List current timers"""
    jobs = context.job_queue.jobs()
    text = ''
    cancel_timers = []
    for job in jobs:
        log.info('JOB: ' + str(job.name))
        cancel_timers.append(['/unset ' + job.name])
    update.message.reply_text(
        'There are currently ' + str(len(jobs)) + ' timers set:\n' + text,
        reply_markup=ReplyKeyboardMarkup(cancel_timers, one_time_keyboard=True)
    )


def remove_job_if_it_exists(update, context):
    """Removes a timer if one is already set"""
    text = ''
    name = context.args[0]
    currentJobs = context.job_queue.get_jobs_by_name(name)

    if not currentJobs:
        text += 'No timer with that name...'

    for job in currentJobs:
        text += job.name + ' cancled!'
        job.schedule_removal()

    update.message.reply_text(text)


def set_timer(update, context, deadline, name):
    """Set a timer in secs"""
    chatID = update.message.chat_id
    jobs = len((context.job_queue.jobs()))

    try:
        due = deadline - pend.now(tz='America/Los_Angeles')
        if due.seconds <= 0:
            update.message.reply_text('Sorry, but that is impossible.')
            return

        context.job_queue.run_once(
            alarm,
            due.seconds,
            context=chatID,
            name=name
        )

        text = 'Reminder successfully set'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text(
            'You obviously cannot divine the complexities of this command. '
            '\n\nHere, try "/timer X" where "X" is a number in seconds.'
        )

    perserve_job_q()

# # # # # # # # # # # # # # # # # #
# List Handling
# # # # # # # # # # # # # # # # # #


def todo(update, context):

    list_data = find_list_data(update, context, lists.TodoList)
    text, args, quantity, tags, timestamp, start_time, deadline = parse_for_list(
        context.args)

    # Sort into to_remove or into to_add
    todos = [i for i in text.split(', ') if i != '']

    try:
        c.print(f'{context.user_data["query"]=}')

    except KeyError:
        context.user_data['update'] = update
        context.user_data['context'] = context

        for todo in todos:
            list_data.add(timestamp, todo, tags, deadline, commit=False)
        list_data.commit()

        if deadline:
            set_timer(update, context, deadline, todos[0])

    list_response2(
        update,
        context,
        list_data,
        items=todos,
        tags=tags,
        args=args
    )

    return FIRST


def list_response2(update, context,
                   list_data, items,
                   tags, args,
                   deadline=None,
                   start_time=None,
                   quantity=None
                   ):

    entries = []
    if tags[0]:
        entries += [entry
                    for entry in list_data.entries
                    if entry.has_all_tags(tags)
                    ]
    else:
        entries = list_data.entries

    # TODO: Refactor gsbrithis. This is not a very efficient way of doing this!
    # BUG: For some reason some of this shit is crashing in the live version
    #       specifically #miles #squat. It's possible that the error stems from
    #       kbd_btns = [] and not [[]]
    kbd_btns = []
    btn_count = 0
    for i, entry in enumerate(list_data.entries):
        if entry not in entries:
            continue
        col = 0 if btn_count % 2 == 0 else 1
        if col == 0:
            kbd_btns.append([])

        kbd_btns[-1].append(InlineKeyboardButton(
            str(entry.text),
            callback_data=f'{i+1}'
            ))
        btn_count += 1

    kbd_btns.append(BR_DONE)

    kbd_todo = InlineKeyboardMarkup(kbd_btns)
    try:
        cc = context.user_data['context']
        uu = context.user_data['update']
        q = context.user_data['query']
        q.message.edit_text(f'{type(list_data).__name__}',
                            reply_markup=kbd_todo)
    except KeyError:
        update.message.reply_text(
            f'{type(list_data).__name__}', reply_markup=kbd_todo)


def todid(update, context):
    q = update.callback_query
    q.answer()
    c.rule()
    cc = context.user_data['context']
    uu = context.user_data['update']
    context.user_data['query'] = q
    remove_entries(uu, cc, lists.TodoList, q.data)
    todo(uu, cc)


def bought(update, context):
    q = update.callback_query
    q.answer()
    c.rule()
    cc = context.user_data['context']
    uu = context.user_data['update']
    context.user_data['query'] = q
    remove_entries(uu, cc, lists.ShoppingList, q.data)
    shopping_list(uu, cc)


def untrack(update, context):
    q = update.callback_query
    q.answer()

    cc = context.user_data['context']
    uu = context.user_data['update']
    qq = context.user_data['query']
    remove_entries(uu, cc, lists.TrackingList, qq.data)
    tracker(uu, cc)
    return AWAIT_INSPECT_OR_DONE


def find_list_data(update, context, list_type, brute_force_id=None):
    try:
        chatid = str(update.message.chat_id)
    except AttributeError:
        update = context.user_data['update']
        chatid = update.message.chat_id
    except BaseException:
        chatid = brute_force_id
    ramfile = str(chatid) + list_type.__name__
    if ramfile in open_files:
        return open_files[ramfile]

    new_list = list_type(update.message.chat_id)
    new_open_file = {ramfile: new_list}
    open_files.update(new_open_file)
    return new_list


def tracker(update, context):
    try:
        list_data = find_list_data(update, context, lists.TrackingList)
    except AttributeError:
        q = update.callback_query
        q.answer()
        list_data = find_list_data(
            context.user_data['update'],
            lists.TrackingList
        )
        context = context.user_data['context']

    # if the user types more than 'todo'
    text, args, quantity, tags, timestamp, start_time, deadline = parse_for_list(
        context.args)

    # Sort into to_remove or into to_add
    items = [i for i in text.split(', ') if i != '']

    try:
        c.print(f'{context.user_data["query"]=}')

    except KeyError:
        context.user_data['update'] = update
        context.user_data['context'] = context

        for item in items:
            list_data.add(timestamp, item, tags, start_time,
                          deadline, commit=False)
        list_data.commit()

    list_response2(update, context, list_data, items,
                   tags, args, quantity=quantity)

    context.user_data['tracking_list'] = list_data
    cur_state = AWAIT_INSPECT_OR_DONE
    return AWAIT_INSPECT_OR_DONE


def inspect_tracking(update, context):
    q = update.callback_query
    q.answer()
    q_chat_id = q.message.chat_id

    tracking_list = context.user_data['tracking_list']
    entry = tracking_list.entries[int(q.data) - 1]

    display_text = f'🎯 <u><b>{entry.text}</b></u>'
    display_text += f'\n\n⏲️ Start time:        {entry.started()}'
    display_text += f'\n⏲️ End time:          {entry.ended()}'
    display_text += f'\n🏷️ Tags:        {entry.tags}'

    kbd_btns = [BR_BACK_DONE, BR_DEL]
    kbd = InlineKeyboardMarkup(kbd_btns)
    q.message.edit_text(display_text,
                        reply_markup=kbd,
                        parse_mode='HTML'
                        )
    context.user_data['query'] = q
    cur_state = AWAIT_BACK_OR_OR_DONE
    return AWAIT_BACK_OR_OR_DONE


def shopping_list(update, context):

    list_data = find_list_data(update, context, lists.ShoppingList)

    # if the user types more than 'todo'
    text, args, quantity, tags, timestamp, start_time, deadline = parse_for_list(
        context.args)

    # Sort into to_remove or into to_add
    items = [i for i in text.split(', ') if i != '']

    try:
        c.print(f'{context.user_data["query"]=}')

    except KeyError:
        context.user_data['update'] = update
        context.user_data['context'] = context

        for item in items:
            list_data.add(timestamp, item, tags, quantity, commit=False)
        list_data.commit()

    list_response2(update, context, list_data, items,
                   tags, args, quantity=quantity)
    cur_state = FIRST
    return FIRST


def remove_entries(update, context, list_type, cbq=None):
    text = update.message.text
    if cbq:
        text = cbq
    list_data = find_list_data(update, context, list_type)

    c.log(f'{text=}')
    if '!all' in text:
        list_data.entries = []
        return

    command = text[1:text.find(' ')]
    to_remove = []

    ranges = re.findall(RE_RANGE, text)
    if ranges:
        for range_ in ranges:
            text = text.replace(range_, '')
            c.print(f'[blue]Stripped Text: {text}')
            range_s = int(range_[:range_.find('-')])
            range_e = int(range_[range_.find('-') + 1:])
            for d in range(range_s, range_e + 1):
                to_remove.append(d)

    singles = re.findall(r'\d+', text)
    to_remove += [int(s) for s in singles]
    to_rem_filtered = sorted(set(to_remove))
    c.print(f'{to_rem_filtered=}')
    list_data.remove(to_rem_filtered)


def show_watchlist(update, context, list_data, items, tags, args):
    list_response2(update, context, list_data, items, tags, args)


def random_movie(update, context):
    try:
        q = update.callback_query
        q.answer()
        update = context.user_data['update']
        is_another_random_movie = True
    except AttributeError:
        is_another_random_movie = False

    list_data = find_list_data(update, context, lists.watchlist)
    movie_count = len(list_data.entries)
    random_movie_id = randint(0, movie_count - 1)
    context.user_data['movie'] = list_data.entries[random_movie_id]
    inspect_movie(update, context, is_another_random_movie)


def watchlist(update, context):
    try:
        movie_query = ''.join(context.args[:])
    except TypeError:
        movie_url = context.user_data['movie_url']
        movie_id = movie_url[movie_url.rfind('tt') + 2:]
        movie_query = 'LINK'
    if not movie_query:
        context.user_data['update'] = update
        context.user_data['context'] = context
        list_data = find_list_data(update, context, lists.watchlist)
        show_watchlist(update, context, list_data, [], [None], [])
        return AWAIT_INSPECT_OR_DONE
    elif movie_query == 'random':
        context.user_data['update'] = update
        context.user_data['context'] = context
        random_movie(update, context)
        return AWAIT_ANOTHER_OR_DONE

    # TODO: give this it's own function
    if movie_query == 'LINK':
        movie = mdb.get_movie(int(movie_id))
    else:
        movies = mdb.search_movie(movie_query)
        movie = mdb.get_movie(movies[0].movieID)
    imdbID = movie['imdbID']
    title = movie['title']
    cover = movie['cover url']
    year = movie['year']
    runtime = movie['runtime']
    genre = ', '.join(movie['genre'])
    rating = movie['rating']
    try:
        desc = movie['plot outline']
    except KeyError:
        try:
            c.log('"Plot Outline" key not found...trying "Plot"')
            desc = movie['plot'][0]
        except KeyError:
            try:
                c.log('P"lot" key not found...trying "Synopsis"')
                desc = movie['synopsis']
            except KeyError:
                desc = 'N/A'

    director = movie['director'][0]['name']
    writer = movie['writer'][0]['name']
    try:
        composers = ' & '.join([composer.data['name']
                               for composer in movie['composers'][:2]])
    except KeyError:
        composers = 'N/A'
    main_actors = ', '.join([actor.data['name']
                            for actor in movie['actors'][:3]])

    movie_data = lists.movie_to_watch(
        imdbID, title, cover, year, runtime, genre, rating, desc,
        director, writer, composers, main_actors
    )
    context.user_data['movie'] = movie_data
    context.user_data['update'] = update
    context.user_data['context'] = context

    auteur = director == writer

    inspect_movie(update, context)
    return AWAIT_INSPECT_OR_DONE


def add_to_watchlist(update, context):
    q = update.callback_query
    q.answer()
    cc = context.user_data['context']
    movie = context.user_data['movie']
    uu = context.user_data['update']
    list_data = find_list_data(uu, cc, lists.watchlist)
    list_data.add(pend.now(), '', (), movie)
    end_conv(update, context)


def inspect_movie(update, context, is_another_random_movie=False):
    is_random_movie = False
    try:
        if is_another_random_movie or 'random'.casefold() in context.args:
            is_random_movie = True
    except TypeError:
        pass

    isreply = False
    try:
        q = update.callback_query
        q.answer()
        q_chat_id = q.message.chat_id
        update = context.user_data['update']
        movie_list = find_list_data(q_chat_id, context, lists.watchlist)
        entry = movie_list.entries[int(q.data) - 1]
        isreply = True
    except AttributeError:
        q = update
        q_chat_id = update.message.chat_id
        if not is_random_movie:
            entry = context.user_data['movie']
        elif is_another_random_movie:
            isreply = True
            q = context.user_data['update']
        movie_list = find_list_data(q, context, lists.watchlist)
        entry = context.user_data['movie']

    auteur = entry.director == entry.writer

    result = ''
    result += f'<u><b>{entry.text} - {entry.year}</b></u>  -  ⭐ {entry.rating}   -  ⏲️{entry.runtime[0]}mins\n'
    result += f'{entry.genre}\n\n'
    if auteur:
        result += f'🎬 Written and directed by {entry.director}\n'
    else:
        result += f'🎬 Director: {entry.director}\n🖊Writer: {entry.writer}\n'
    result += f'🎼 Composed by {entry.composers}\n'
    result += f'🎭 Staring {entry.main_actors}\n\n'
    result += f'{entry.desc[:350]}\n'
    result += f'<a href="{entry.cover}">Cover Art</a>'

    context.user_data['query'] = q
    kbd_btns = []
    kbd = InlineKeyboardMarkup(kbd_btns)
    if is_random_movie:
        kbd_btns.append(BR_ANOTHER_OR_DONE)
        q.message.reply_text(result,
                             reply_markup=kbd,
                             parse_mode='HTML'
                             )
        return AWAIT_ANOTHER_OR_DONE
    elif isreply:
        kbd_btns.append(BR_BACK_DONE)
        kbd_btns.append(BR_DEL)
        q.message.edit_text(result,
                            reply_markup=kbd,
                            parse_mode='HTML'
                            )
        cur_state = AWAIT_BACK_OR_OR_DONE
        return AWAIT_BACK_OR_OR_DONE
    else:
        kbd_btns.append(BR_ADD_OR_DONE)
        q.message.reply_text(result,
                             reply_markup=kbd,
                             parse_mode='HTML'
                             )
        return AWAIT_BACK_OR_ADD_OR_DONE


def remove_from_watchlist(update, context):
    q = update.callback_query
    q.answer()

    uu = context.user_data['update']
    qq = context.user_data['query']
    cc = context.user_data['context']
    remove_entries(uu, cc, lists.watchlist, qq.data)
    watchlist(uu, cc)
    return AWAIT_INSPECT_OR_DONE

# # # # # # # # # # # # # # # # # #
# Generic Handlers
# # # # # # # # # # # # # # # # # #


def handle_unknown(update, context):
    if update.message.text.startswith('Ramsey, '):
        try:
            q = update.message.text[update.message.text.find('Ramsey, ') + 7:]
            log.info('Query to Wolfram Alpha for ' + q)
            a = wolf.query(update.message.text[7:])
            ans = next(a.results).text
            update.message.reply_text(ans)

        except(Exception):
            update.message.reply_text(
                'Sorry, I couldn\'t find anything on that...'
                'maybe try rephrasing it?'
            )


def periodic(context: CallbackContext):
    time = pend.now()
    c.print(f'{time.hour} and {time.minute}')
    # briefing()


def perserve_job_q():
    jobs_tup = tuple((job.context, job.name, job.next_t)
                     for job in jobs.jobs()
                     if job.name != 'periodic'
                     )

    with open('jobs.pkl', 'wb') as f:
        pickle.dump(jobs_tup, f)


def restore_job_q():
    try:
        with open('jobs.pkl', 'rb') as f:
            jobs_tup = pickle.load(f)
    except FileNotFoundError:
        return

    for job in jobs_tup:
        context, name, time = job
        c.print('[red]SUCCESS!?')
        jobs.run_once(alarm, time, context, name)


def handle_urls(update, context):
    imdb_url = update.message.text[:update.message.text.find('\n')]
    if 'www.imdb.com' in imdb_url:
        context.user_data['context'] = context
        context.user_data['movie_url'] = imdb_url
        context.user_data['update'] = update
        watchlist(update, context)
        return AWAIT_BACK_OR_ADD_OR_DONE

    return ConversationHandler.END


# def briefing():
    # room = 181177492
    # temp, feels_like, low_temp, high_temp, humidity, wind_report = getweather()
    # report = f'🌡️It is currently {temp} but feels like {feels_like}.'
    # report += f'\n🆒Today\'s low: {low_temp} \n🔝Today\'s high: {high_temp}'
    # report += f'\n♨️The humidity is {humidity}%'
    # report += f'\n🌬️Wind be like {wind_report}'
    # updater.bot.send_message(room, report)

    # update = None
    # context = None
    # list_data = (update, context, lists.TodoList, room)

    # updater.bot.send_message(room, list_data[2])


# # # # # # # # # # # # # # # # # #
# Conversations
# # # # # # # # # # # # # # # # # #


def end_conv(update, context):
    q = update.callback_query
    q.answer()
    c.log('Conversation has ended')
    context.user_data.pop('query', None)
    q.message.edit_text('List closed.')
    return ConversationHandler.END


def back_out_watchlist(update, context):
    back_conv(update, context, lists.watchlist)
    return AWAIT_INSPECT_OR_DONE


def back_out_tracklist(update, context):
    back_conv(update, context, lists.TrackingList)
    return AWAIT_INSPECT_OR_DONE


def back_conv(update, context, list_type):
    q = update.callback_query
    q.answer()
    c.log('Back out of Conversation')
    uu = context.user_data['update']
    cc = context.user_data['context']
    if list_type == lists.TrackingList:
        tracker(uu, cc)
    elif list_type == lists.watchlist:
        watchlist(uu, cc)


todo_conv = ConversationHandler(
    entry_points=[CommandHandler('todo', todo)],
    states={
        FIRST: [
            CallbackQueryHandler(todid, pattern='\\d.*'),
            CallbackQueryHandler(end_conv, pattern='done'),
            CommandHandler('todo', todo)

        ]
    },
    fallbacks=[(CommandHandler('end_conv', end_conv))],
    conversation_timeout=120
)

track_conv = ConversationHandler(
    entry_points=[CommandHandler('track', tracker)],
    states={
        AWAIT_INSPECT_OR_DONE: [
            CallbackQueryHandler(inspect_tracking, pattern='\\d.*'),
            CallbackQueryHandler(end_conv, pattern='done'),
            CommandHandler('track', tracker),

        ],
        AWAIT_BACK_OR_OR_DONE: [
            CallbackQueryHandler(back_out_tracklist, pattern='back'),
            CallbackQueryHandler(end_conv, pattern='done'),
            CallbackQueryHandler(untrack, pattern='del'),
            CommandHandler('track', tracker),

        ]
    },
    fallbacks=[(CommandHandler('end_conv', end_conv))],
    conversation_timeout=120
)

shopping_conv = ConversationHandler(
    entry_points=[CommandHandler('buy', shopping_list)],
    states={
        FIRST: [
            CallbackQueryHandler(bought, pattern='\\d.*'),
            CallbackQueryHandler(end_conv, pattern='done'),
            CommandHandler('buy', shopping_list),
        ]
    },
    fallbacks=[(CommandHandler('end_conv', end_conv))],
    conversation_timeout=120
)

watchlist_conv = ConversationHandler(
    entry_points=[
        CommandHandler('watchlist', watchlist),
        MessageHandler(Filters.text & Filters.entity(
            'url') & ~Filters.command, handle_urls)
    ],
    states={
        AWAIT_INSPECT_OR_DONE: [
            CallbackQueryHandler(add_to_watchlist, pattern='add'),
            CallbackQueryHandler(inspect_movie, pattern='\\d.*'),
            CallbackQueryHandler(end_conv, pattern='done'),
            CommandHandler('watchlist', watchlist),
        ],
        AWAIT_BACK_OR_OR_DONE: [
            CallbackQueryHandler(back_out_watchlist, pattern='back'),
            CallbackQueryHandler(end_conv, pattern='done'),
            CallbackQueryHandler(remove_from_watchlist, pattern='del'),
            CommandHandler('watchlist', watchlist),

        ],
        AWAIT_BACK_OR_ADD_OR_DONE: [
            CallbackQueryHandler(back_out_watchlist, pattern='back'),
            CallbackQueryHandler(end_conv, pattern='done'),
            CallbackQueryHandler(add_to_watchlist, pattern='add'),
            CommandHandler('watchlist', watchlist),
        ],
        AWAIT_ANOTHER_OR_DONE: [
            CallbackQueryHandler(random_movie, pattern='random'),
            CallbackQueryHandler(end_conv, pattern='done'),
            CommandHandler('watchlist', watchlist),
        ]
    },
    fallbacks=[(CommandHandler('end_conv', end_conv))],
    conversation_timeout=120
)

######################################################################
#  MAIN                                                       #
######################################################################


def main():
    """Main"""
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('timer', set_timer))
    dp.add_handler(CommandHandler('timers', list_timers))
    dp.add_handler(CommandHandler('flip', flip_coin))
    dp.add_handler(CommandHandler('roll', roll_dice))
    dp.add_handler(CommandHandler('unset', remove_job_if_it_exists))

    dp.add_handler(watchlist_conv)
    dp.add_handler(todo_conv)
    dp.add_handler(track_conv)
    dp.add_handler(shopping_conv)

    jobs.run_repeating(periodic, 130, 0, name='periodic')
    restore_job_q()
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
