# -*- coding: utf-8 -*-

import sqlite3
import pickle
import logging


class SQList(object):
    """
    List-like object that stores data in SQLite database
    """
    def __init__(self, values=None, path=':memory:', key=None, drop=True):
        """
        :param values: iterable with elements of new list
        :param path: path to file with SQLite database
        :param key: callable object used to sort values of SQList
        :param drop: drop any data in file at path
        """
        if key:
            if callable(key):
                self.key = key
                logging.debug('Key %s is callable' % key)
            else:
                raise TypeError('{} object is not callable'.format(type(key)))
        else:
            self.key = lambda x: None
            logging.debug('Key is not specified, so lambda %s will be used' % self.key)

        self.path = path
        self.sql = sqlite3.connect(path)
        self.sql.text_factory = str
        logging.debug('File %s opened as SQLite database' % path)
        self.cursor = self.sql.cursor()
        if drop:
            self.cursor.execute('''DROP TABLE IF EXISTS `data`;''')
            logging.debug('Tried to drop table `data` in %s' % path)
        self.cursor.execute(
            '''CREATE TABLE `data` (`key` BLOB,
                                    `value` BLOB NOT NULL);''')
        self.cursor.execute('''CREATE INDEX `keys_index` ON `data` (`key`);''')
        if values:
            logging.debug('Trying to insert values into database')
            self.cursor.executemany(
                '''INSERT INTO `data`
                   (`key`, `value`)
                   VALUES (?, ?);''',
                zip(map(self.key, values), map(pickle.dumps, values))
            )
            self.sql.commit()

    def __repr__(self):
        return 'sqlist.SQList({})'.format(repr(list(self[:50])))

    def __len__(self):
        result = self.cursor.execute(
            '''SELECT COUNT(*) FROM `data`;'''
        ).fetchone()
        return result[0]

    def __getitem__(self, index):
        if type(index) == int:
            offset, stop, stride = slice(index, index + 1).indices(len(self))
        elif type(index) == slice:
            offset, stop, stride = index.indices(len(self))
        else:
            raise TypeError('Int or slice expected, %s found' % type(index))
        limit = stop - offset

        result = self.cursor.execute(
                '''SELECT `value`
                   FROM `data`
                   ORDER BY `key` ASC
                   LIMIT ? OFFSET ?;''',
                (limit, offset)
        )

        if type(index) == int:
            result = result.fetchone()
            if result is None:
                raise IndexError('%s is out of range' % index)
            else:
                return pickle.loads(result[0])
        else:
            return [pickle.loads(i[0]) for i in result]

    def __setitem__(self, index, value):
        offset, stop, stride = slice(index, index + 1).indices(len(self))

        result = self.cursor.execute(
            '''UPDATE `data`
               SET `key` = ?, `value` = ?
               WHERE `_rowid_` = (
                  SELECT `_rowid_`
                  FROM `data`
                  ORDER BY `key` ASC
                  LIMIT 1 OFFSET ?
               );''',
            (self.key(value), pickle.dumps(value), offset)
        )
        if not result.rowcount:
            raise IndexError('%s is out of range' % index)
        else:
            self.sql.commit()

    def __delitem__(self, index):
        offset, stop, stride = slice(index, index + 1).indices(len(self))

        result = self.cursor.execute(
            '''DELETE FROM `data`
               WHERE `_rowid_` = (
                  SELECT `_rowid_`
                  FROM `data`
                  ORDER BY `key` ASC
                  LIMIT 1 OFFSET ?
               );''',
            (offset, )
        )
        if not result.rowcount:
            raise IndexError('%s is out of range' % index)
        else:
            self.sql.commit()

    def __iter__(self):
        for item in self.cursor.execute(
                '''SELECT `value` FROM `data` ORDER BY `key` ASC;'''):
            yield pickle.loads(item[0])
        raise StopIteration

    def __contains__(self, item):
        logging.debug('Check if %s (%s) is in SQList' % (repr(item), pickle.dumps(item)))
        result = self.cursor.execute(
            '''SELECT `_rowid_`
               FROM `data`
               WHERE `value` = ?;''',
            (pickle.dumps(item),)
        )
        return bool(result.fetchone())

    def append(self, value):
        result = self.cursor.execute(
            '''INSERT INTO `data`
               (`key`, `value`)
               VALUES (?, ?);''',
            (self.key(value), pickle.dumps(value))
        )
        self.sql.commit()

    def pop(self, index=-1):
        offset, stop, stride = slice(index, index + 1).indices(len(self))

        self.cursor.execute('BEGIN TRANSACTION;')
        result = self.cursor.execute(
            '''SELECT `_rowid_`, `value`
               FROM `data`
               ORDER BY `key` ASC
               LIMIT 1 OFFSET ?;''',
            (offset, )
        )
        if result.rowcount:
            rowid, value = result.fetchone()
            self.cursor.execute(
                '''DELETE FROM `data` WHERE `_rowid_` = ?;''', (rowid, )
            )
            self.sql.commit()
            return pickle.loads(value)
        else:
            raise IndexError('{} is out of range'.format(index))
