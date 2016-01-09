import sqlite3
import pickle


class SQList:
    """
    List-like object that stores data in SQLite database
    """
    def __init__(self, values=None, path=':memory:', key=None, drop=True):
        """
        :param values: iterable with elemets of new list
        :param path: path to file of database
        :param key: callable object used to sort values of SQList
        :param drop: drop any data in file at path
        """
        if key:
            if callable(key):
                self.key = key
            else:
                raise TypeError('{} object is not callable'.format(type(key)))
        else:
            self.key = lambda x: None

        self.sql = sqlite3.connect(path)
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
                zip(map(key, values), values)
            )

    def __repr__(self):
        return 'sqlist.SQList({})'.format(repr(list(self[:50])))

    @staticmethod
    def __calc_index(index):
        return (- index - 1) if index < 0 else index

    @staticmethod
    def __get_order(index):
        return 'DESC' if index < 0 else 'ASC'

    def __len__(self):
        result = self.cursor.execute(
            '''SELECT COUNT(*) FROM `data`;'''
        ).fetchone()
        return result[0]

    def __getitem__(self, index):
        result = self.cursor.execute(
            '''SELECT `value`
               FROM `data`
               ORDER BY `key` {order}
               LIMIT 1 OFFSET ?;'''.format(order=self.__get_order(index)),
            (self.__calc_index(index), )
        )
        if not result.rowcount:
            raise IndexError('{} is out of range'.format(index))
        else:
            return pickle.loads(result.fetchone()[0])

    def __setitem__(self, index, value):
        result = self.cursor.execute(
            '''UPDATE `data`
               SET `key` = ?, `value` = ?
               WHERE `_rowid_` = (
                  SELECT `_rowid_`
                  FROM `data`
                  ORDER BY `key` {order}
                  LIMIT 1 OFFSET ?
               );'''.format(order=self.__get_order(index)),
            (self.key(value), pickle.dumps(value), self.__calc_index(index))
        )
        if not result.rowcount:
            raise IndexError('{} is out of range'.format(index))
        else:
            self.sql.commit()

    def __delitem__(self, index):
        self.cursor.execute(
            '''DELETE FROM `data`
               WHERE `_rowid_` = (
                  SELECT `_rowid_`
                  FROM `data`
                  ORDER BY `key` {order}
               );'''.format(order=self.__get_order(index)),
            (self.__calc_index(index), )
        )

    def __iter__(self):
        length = len(self)
        try:
            for i in xrange(length):
                yield self[i]
        except NameError:
            for i in xrange(length):
                yield self[i]
        raise StopIteration

    def __contains__(self, item):
        result = self.cursor.execute(
            '''SELECT `_rowid_`
               FROM `data`
               WHERE `value` = ?;''',
            (pickle.dumps(item))
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
        self.cursor.execute('BEGIN TRANSACTION;')
        result = self.cursor.execute(
            '''SELECT `_rowid_`, `value`
               FROM `data`
               ORDER BY `key` {order}
               LIMIT 1 OFFSET ?;'''.format(order=self.__get_order(index)),
            (self.__calc_index(index), )
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

    def sort(self, key=None):
        if key is None:
            self.cursor.execute('''UPDATE `data` SET `key` = NULL;''')
        elif not callable(key):
            raise TypeError('{} object is not callable'.format(type(key)))
        else:
            self.cursor.execute('''BEGIN TRANSACTION;''')
            old_key = self.key
            self.key = key
            for index, value in enumerate(self):
                self[index] = value
            self.key = old_key
        self.sql.commit()
