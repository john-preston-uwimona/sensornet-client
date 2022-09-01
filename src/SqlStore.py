import collections
import sys
import sqlite3
import json
import logging
import time
from contextlib import closing


class SqlStore(collections.MutableMapping):
    ELAPSED = "ELAPSED: {:.7f} seconds"
    FORMATTING_STR = "[%(module)s][%(funcName)s] %(message)s"

    def __init__(self, path, clear=False, debug=False):
        self.debug = debug
        self.log = logging.getLogger()
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(self.FORMATTING_STR))
        self.log.addHandler(handler)
        self.log.setLevel(logging.DEBUG)
        self.iter_c = None
        self.iter_result = None
        self.t0 = 0
        conn = sqlite3.connect(path)
        self.conn = conn
        conn.text_factory = sqlite3.OptimizedUnicode
        c = conn.cursor()
        if clear:
            self.__execute(c, 'DROP TABLE IF EXISTS sqlstore')
            self.__execute(c, 'CREATE TABLE sqlstore (msgid text not null, message text, priority integer not null, primary key(msgid, priority))')
        else:
            self.__execute(c, 'SELECT name FROM sqlite_master WHERE type=? AND name=?', ('table', 'sqlstore'))
            result = c.fetchone()
            if result is None:
                self.__execute(c, 'CREATE TABLE sqlstore (msgid text not null, message text, priority integer not null, primary key(msgid, priority))')
        c.close()
        conn.commit()
        self.key = 'msgid'

    def __debug_query(self, query, *args):
        # test for mismatch in number of '?' tokens and given arguments
        number_of_question_marks = query.count('?')
        number_of_arguments = len(args)
        # When no args are given, an empty tuple is passed
        if len(args) == 1 and (not args[0]):
            number_of_arguments = 0
        if number_of_arguments != number_of_question_marks:
            self.log.debug(
                "Incorrect number of bindings supplied. The current statement uses {}, and there are {} supplied.".format(
                    number_of_question_marks, number_of_arguments))
            return
        # compile query
        for a in args:
            query = query.replace('?', "'" + str(a) + "'", 1)
        self.log.debug(query)

    def __execute(self, cursor, query, args=()):
        # Did some profiling, and it is quicker to compute the sql query
        # then print it, and then execute the parameterized query.
        if self.debug:
            self.__debug_query(query[:], *args)
        return cursor.execute(query, args)

    def __len__(self):
        if self.debug:
            self.t0 = time.perf_counter()
        with closing(self.conn.cursor()) as c:
            self.__execute(c, 'SELECT COUNT(*) FROM sqlstore')
            if self.debug:
                self.log.debug(self.ELAPSED.format(time.perf_counter()-self.t0))
            return c.fetchone()[0]

    def __iter__(self):
        self.iter_c = self.conn.cursor()
        self.__execute(self.iter_c, 'SELECT message FROM sqlstore order by priority desc')
        while True:
            self.iter_result = self.iter_c.fetchone()
            return self

    def __next__(self):
        if self.iter_result is None:
            self.iter_c.close()
            raise StopIteration
        result = self.iter_result
        self.iter_result = self.iter_c.fetchone()
        return json.loads(result[0])

    def __getitem__(self, k):
        if self.debug:
            self.t0 = time.perf_counter()
        with closing(self.conn.cursor()) as c:
            self.__execute(c, 'SELECT message FROM sqlstore WHERE {}=?'.format(self.key), (k,))
            result = json.loads(c.fetchone()[0])
            if self.debug:
                self.log.debug(self.ELAPSED.format(time.perf_counter()-self.t0))
            return result

    def __contains__(self, k):
        if self.debug:
            self.t0 = time.perf_counter()
        with closing(self.conn.cursor()) as c:
            self.__execute(c, 'SELECT msgid FROM sqlstore WHERE {}=?'.format(self.key), (k,))
            if self.debug:
                self.log.debug(self.ELAPSED.format(time.perf_counter()-self.t0))
            return c.fetchone() is not None

    def __delitem__(self, k):
        if self.debug:
            self.t0 = time.perf_counter()
        with closing(self.conn.cursor()) as c:
            self.__execute(c, 'DELETE FROM sqlstore WHERE {}=?'.format(self.key), (k,))
            if self.debug:
                self.log.debug(self.ELAPSED.format(time.perf_counter()-self.t0))
            self.conn.commit()

    def __setitem__(self, k, v):
        if self.debug:
            self.t0 = time.perf_counter()
        priority = int(v["priority"]) if "priority" in v else 1 
        with closing(self.conn.cursor()) as c:
            self.__execute(c, 'REPLACE INTO sqlstore (msgid, message, priority) VALUES (?,?,?)', (k, json.dumps(v), priority,))
            self.conn.commit()
            if self.debug:
                self.log.debug(self.ELAPSED.format(time.perf_counter()-self.t0))

    def clear(self):
        if self.debug:
            self.t0 = time.perf_counter()
        with closing(self.conn.cursor()) as c:
            self.__execute(c, 'DELETE FROM sqlstore')
            if self.debug:
                self.log.debug(self.ELAPSED.format(time.perf_counter()-self.t0))
            self.conn.commit()

    def close(self):
        self.conn.close()

