# -*- coding: utf-8 -*-

import pickle
import sqlite3
import tempfile

from os import close, remove

from collections import Iterable


class SQList(object):
    """
    List-like object that stores data in SQLite database
    """
    def __init__(self, values=None, path=':memory:', key=None, drop=True,
                 auto_remove=False):
        """
        :param values: iterable with elements of new list
        :param path: path to file with SQLite database
        :param key: callable object used to sort values of SQList
        :param drop: drop any data in file at path
        :param auto_remove: remove file `path` during garbage collection
        """
        if key:
            if callable(key):
                self.key = key
            else:
                raise TypeError('%s object is not callable' % type(key))
        else:
            self.key = lambda x: None

        self.path = path
        self.auto_remove = auto_remove
        self.sql = sqlite3.connect(path)
        self.sql.text_factory = str
        self.cursor = self.sql.cursor()
        if drop:
            self.cursor.execute('''DROP TABLE IF EXISTS `data`;''')
        self.cursor.execute(
            '''CREATE TABLE `data` (`key` BLOB,
                                    `value` BLOB NOT NULL);''')
        self.cursor.execute('''CREATE INDEX `keys_index` ON `data` (`key`);''')
        if values:
            self.cursor.executemany(
                '''INSERT INTO `data`
                   (`key`, `value`)
                   VALUES (?, ?);''',
                zip(map(self.key, values), map(pickle.dumps, values))
            )
            self.sql.commit()

    def __repr__(self):
        if len(self) < 20:
            return 'sqlist.SQList([%s])' % ', '.join(map(repr, self))
        else:
            return 'sqlist.SQList([%s]...)' % ', '.join(map(repr, self[:20]))

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

    def __out_of_range_check(self, index, result):
        if not result.rowcount:
            self.sql.rollback()
            raise IndexError('%s is out of range' % index)
        else:
            self.sql.commit()

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
        self.__out_of_range_check(index, result)

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
        self.__out_of_range_check(index, result)

    def __iter__(self):
        for item in self.cursor.execute(
                '''SELECT `value` FROM `data` ORDER BY `key` ASC;'''):
            yield pickle.loads(item[0])
        raise StopIteration

    def __contains__(self, item):
        result = self.cursor.execute(
            '''SELECT `_rowid_`
               FROM `data`
               WHERE `value` = ?;''',
            (pickle.dumps(item),)
        )
        return bool(result.fetchone())

    def __eq__(self, other):
        if not hasattr(other, '__len__') and len(self) != len(other):
                return False

        this = self.cursor.execute(
                '''SELECT `value` FROM `data` ORDER BY `key` ASC;''')
        for a, b in zip((pickle.loads(i[0]) for i in this), other):
            if a != b:
                return False
        return True

    def __del__(self):
        self.sql.close()
        if self.auto_remove:
            remove(self.path)

    @classmethod
    def temp(cls, key=None, auto_remove=True,
             suffix='', prefix='', dir=None):
        """
        Create on-disk instance located in system temporary directory
        (see :func:`tempfile.mkstemp`).

        :param key: callable object used to sort values of SQList
        :param auto_remove: remove file `path` during garbage collection
        :param suffix: temporary file name suffix (see :func:`tempfile.mkstemp`)
        :param prefix: temporary file name prefix (see :func:`tempfile.mkstemp`)
        :param dir: directory instead of system temporary directory
         (see :func:`tempfile.mkstemp`)
        :return: instance of :class:`sqlist.SQList` object
        """
        handle, path = tempfile.mkstemp(suffix, prefix, dir)
        close(handle)
        result = cls(path=path, key=key, auto_remove=auto_remove)
        return result

    def __iadd__(self, other):
        if isinstance(other, Iterable):
            self.cursor.executemany(
                '''INSERT INTO `data`
                   (`key`, `value`)
                   VALUES (?, ?);''',
                zip(map(self.key, other), map(pickle.dumps, other))
            )
            self.sql.commit()
            return self
        else:
            raise TypeError('unsupported operand type(s) for +=: '
                            '\'sqlist.SQList\' and \'%s\'' % type(other))

    def append(self, value):
        self.cursor.execute(
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
            self.sql.rollback()
            raise IndexError('{} is out of range'.format(index))

    def sort(self, key=None, reverse=False):
        def swap_required(a, b):
            """Check if items should be swapped considering reverse order"""
            try:
                if reverse:
                    return a < b
                else:
                    return a > b
            except TypeError as e:
                # Values are not comparable
                self.sql.rollback()
                raise TypeError(e)

        if key:
            if not callable(key):
                raise TypeError('{} object is not callable'.format(type(key)))
        else:
            def key(x):
                return x

        self.cursor.execute('BEGIN TRANSACTION;')
        if self.key:
            self.cursor.execute('''UPDATE `data` SET `key` = NULL;''')
            self.key = None
        position = 0
        while True:
            values = self.cursor.execute(
                '''SELECT `_rowid_`, `value` FROM `data` LIMIT 2 OFFSET ?''',
                (position, )
            ).fetchall()
            if len(values) < 2:
                break
            unpacked = [pickle.loads(i[1]) for i in values]
            q = ((values[1][1], values[1][0]), (values[0][1], values[0][0]))
            if swap_required(key(unpacked[0]), key(unpacked[1])):
                self.cursor.executemany(
                        '''UPDATE `data` SET `value` = ? WHERE `_rowid_` = ?''',
                        ((values[1][1], values[0][0]),
                         (values[0][1], values[1][0]))
                )
                if position:
                    position -= 1
            else:
                position += 1
        self.sql.commit()
