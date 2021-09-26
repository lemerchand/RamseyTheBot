# # # # # # # # # # # # # # # # # #
# List Classes and Data Types
# for the Ramsey Telegram Bot
#
# TODO: Create & test tracking list
# TODO: Create & test sundries list
# TODO: Document and type hint
#
# Last Modified 4/4/2021 6:44:12 AM
# # # # # # # # # # # # # # # # # #

import pickle
from rich.console import Console
import pendulum as pend
from dataclasses import dataclass
from pathlib import Path
import imdb

testing = True
c = Console()
mdb = imdb.IMDb()
CWD = Path.cwd()

TZ = 'America/Los_Angeles'

# # # # # # # # # # # # # # # # # #
#  Parent Class
# # # # # # # # # # # # # # # # # #


@dataclass
class BasicEntry:
    '''
    The basic datatype for pickling TODO and misc entries
    '''
    __time_entered: pend.datetime
    text: str
    tags: tuple

    def time_entered(self, tm: bool = True, dt: bool = True) -> pend.datetime:
        """
        Retrieve the time this entry was entered in a chosen format.

        :param tm - Show hours/mins
        :param dt - Show date
        :default - Show both
        """
        if dt and not tm:
            return self.__time_entered.format('MMM DD, YYYY')
        elif tm and not dt:
            return self.__time_entered.format('hh:mm:ss')
        else:
            return self.__time_entered.format('MMM DD, YYYY at hh:mm:SS')

    def has_tag(self, tag: str) -> bool:
        '''
        Returns True if tag is in this list's tags
        '''
        if tag in self.tags:
            return True
        return False

    def has_all_tags(self, tags: list) -> bool:
        '''
        Retruns True if this entry has all tags
        '''
        if set(tags).issubset(set(self.tags)):  # cspell:disable-line
            return True
        return False


class BasicList:
    """
    Blueprint for all other Ramsey list types
    """

    def __init__(self, id: int):
        self.id = id
        self.entries = []
        self.list_file = 'basic.pkl'
        self.path = Path(self.set_path())

    def set_path(self):
        if testing:
            return CWD / 'data' / 'rooms' / str(self.id) / self.list_file
        else:
            return CWD / 'data' / 'rooms' / str(self.id) / self.list_file

    def open(self) -> bool:
        c.log(self.list_file)
        if 'basic' in self.list_file:
            return
        try:
            if testing:
                c.log(f'Looking for {self.path}')
            with open(self.path, 'rb') as f:
                self.entries = pickle.load(f)

            if testing:
                c.log(f'{self.path} found...')
            return True

        except (FileNotFoundError, AttributeError):
            if testing:
                c.log('No associated file...one will be created if possible...')
            self.path.parent.mkdir(exist_ok=True, parents=True)
            with open(self.path, 'wb') as f:
                pickle.dump(self.entries, f)
            return False

    def add(self, time, text, tags, commit: bool = False):
        if testing:
            c.log('Attempting to make a list entry...')
        time = time if time else pend.now(tz=TZ)
        text = text if text else ''
        tags = tags if tags else ('None')

        if 'basic' in self.list_file:
            entry = BasicEntry(time, text, tags)
            self.post_add(entry, commit)

    def post_add(self, entry, commit):
        self.entries.append(entry)
        if testing:
            c.log('Entry was successful, but not yet committed.')
        if commit:
            self.commit()

    def remove(self, targets):
        if testing:
            c.log(f'Attempting to remove {targets}')
        for i in range(len(self.entries) - 1, -1, -1):
            for t in targets:
                c.print(t - 1)
                if t - 1 == i:
                    del(self.entries[i])
        if testing:
            c.log(f'Removal was a success, bisch.')

        self.commit()

    def clear_all(self):
        self.entries = []
        self.commit()

    def commit(self) -> None:
        """
        Allows you to save processing time by committing multiple entries
        in one go.
        """
        with open(self.path, 'wb') as f:
            pickle.dump(self.entries, f)
        if testing:
            c.log(f'New changes have been committed to {self.path}.')

# # # # # # # # # # # # # # # # # #
#  A todo list child of Basic List
# # # # # # # # # # # # # # # # # #


@dataclass
class TodoEntry(BasicEntry):
    deadline: pend.datetime

    def due(self, tm: bool = True, dt: bool = True) -> pend.datetime:
        """
        Retrieve the time this entry was entered in a chosen format.

        :param tm - Show hours/mins
        :param dt - Show date
        :default - Show both
        """
        if dt and not tm:
            return self.deadline.format('MMM DD, YYYY')
        elif tm and not dt:
            return self.deadline.format('hh:mm:ss')
        else:
            return self.deadline.format('MMM DD, YYYY at hh:mm:SS')


class TodoList(BasicList):
    """
    An extension of the Basic List class, adding a deadline
    attribute
    """

    def __init__(self, id):
        super().__init__(id)
        self.list_file = 'todo.pkl'
        self.path = Path(self.set_path())
        self.open()

    def add(self, time, text, tags, deadline=None, commit=False):
        self.deadline = deadline
        super().add(time, text, tags, commit)
        entry = TodoEntry(time, text, tags, deadline)
        self.post_add(entry, commit)


@dataclass
class TrackingEntry(BasicEntry):
    start_time: pend.datetime
    end_time: pend.datetime

    def ended(self, tm: bool = True, dt: bool = True) -> pend.datetime:
        """
        Retrieve the time this entry was entered in a chosen format.

        :param tm - Show hours/mins
        :param dt - Show date
        :default - Show both
        """
        try:
            if dt and not tm:
                return self.end_time.format('MMM DD, YYYY')
            elif tm and not dt:
                return self.end_time.format('hh:mm:ss')
            else:
                return self.end_time.format('MMM DD, YYYY at hh:mm:SS')
        except AttributeError:
            return None

    def started(self, tm: bool = True, dt: bool = True) -> pend.datetime:
        """
        Retrieve the time this entry was entered in a chosen format.

        :param tm - Show hours/mins
        :param dt - Show date
        :default - Show both
        """
        try:
            if dt and not tm:
                return self.start_time.format('MMM DD, YYYY')
            elif tm and not dt:
                return self.start_time.format('hh:mm:ss')
            else:
                return self.start_time.format('MMM DD, YYYY at hh:mm:SS')
        except AttributeError:
            return None


class TrackingList(BasicList):
    """
    An extension of the Basic List class, adding a starttime,
    and endtime, and an algorithmically generated duration.
    """

    def __init__(self, id):
        super().__init__(id)
        self.list_file = 'tracking.pkl'
        self.path = Path(self.set_path())
        self.open()

    def add(self, time, text, tags, start_time, end_time, commit=False):
        self.start_time = start_time
        self.end_time = end_time
        super().add(time, text, tags, commit)
        entry = TrackingEntry(time, text, tags, start_time, end_time)
        self.post_add(entry, commit)


@dataclass
class movie_to_watch():
    imdbid: str
    text: str
    cover: str
    year: int
    runtime: list
    genre: str
    rating: float
    desc: str
    director: str
    writer: str
    composers: str
    main_actors: str


class watchlist(BasicList):
    def __init__(self, id):
        super().__init__(id)
        self.list_file = 'watchlist.pkl'
        self.path = Path(self.set_path())
        self.open()

    def add(self, time, text, tags, movie, commit=True):

        super().add(time, text, tags, commit)
        entry = movie_to_watch(
                               movie.imdbid, movie.text,
                               movie.cover, movie.year,
                               movie.runtime, movie.genre,
                               movie.rating, movie.desc,
                               movie.director, movie.writer,
                               movie.composers, movie.main_actors,
                               )
        self.post_add(entry, commit)


# TODO: Make an inventory list whose low items automatically go to
# the shopping list?


@dataclass
class ShoppingEntry(BasicEntry):
    quantity: int = 0


class ShoppingList(BasicList):
    """
    An extension of the Basic List class, adding a starttime,
    and endtime, and an algorithmically generated duration.
    """

    def __init__(self, id):
        super().__init__(id)
        self.list_file = 'shopping.pkl'
        self.path = Path(self.set_path())
        self.open()

    def add(self, time, text, tags, quantity=0, commit=False):
        self.quantity = quantity
        super().add(time, text, tags, commit)
        entry = ShoppingEntry(time, text, tags, quantity)
        self.post_add(entry, commit)


def occurrences(entries, tframe: str):
    """
    Returns how many entries occur in the given time frame.

    :params tframe - str version of a pendulum time attr (eg, 'month')
    """
    p = getattr(pend.now(), tframe)
    count = 0
    for entry in entries:
        if getattr(entry.start_time, tframe) == p:
            count += 1
    return count


# # # # # # # # # # # # # # # # # #
# Functions
# # # # # # # # # # # # # # # # # #
def get_movie_data(movie):
   pass 

def inspect_entry(chat_id, list_type, entries):
    pass

    #:w

    #
    #
    #
    # # # # # # # # # # # # # # # # # #
    # TESTING SHIT
    # # # # # # # # # # # # # # # # # #


if __name__ == '__main__':
    testing = True
    choice = 'ooo'
    trial = TrackingList(66166)
    shopping_trial = ShoppingList(66166)

    while choice:
        # Basic Test
        c.print('[yellow]-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=--=-=-=-=-=-')
        c.print('[yellow]-=-=-< Ramsey List Class Utility and Test Suite >-=-=-')
        c.print('[yellow]-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=--=-=-=-=-=-')
        c.print('')
        c.print('[red]t\t[/red] - add to Test Todo Pickle')
        c.print('[red]s\t[/red] - add to Shopping List Pickle')
        c.print('[red]r\t[/red] - remove entry by number')
        c.print('[red]d\t[/red] - delete test pickle')
        c.print('[red]p\t[/red] - print')

        choice = input()
        if choice == 'd':
            trial.clear_all()
            shopping_trial.clear_all()
        elif choice == 't':
            for i in range(0, 10):
                trial.add(
                    pend.now(),
                    f'Hello I am {i+1}',
                    ('#yolo #bolo'),
                    pend.now(),
                    pend.now().add(days=2)
                )

        elif choice == 's':
            for i in range(0, 10):
                shopping_trial.add(
                    pend.now(),
                    f'Hello I am {i+1}',
                    ('#yolo #bolo'), 5)

        elif choice == 'r':
            d = input('What shall we delete? ')
            trial.remove(int(d))
        elif choice == 'p':

            for entry in trial.entries:
                c.print(entry)
            for entry in shopping_trial.entries:
                c.print(entry)
        shopping_trial.commit()
        trial.commit()

