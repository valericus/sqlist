# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
from time import sleep

import sqlist


class TestSQList(unittest.TestCase):
    def setUp(self):
        self.test_values = [
            {'foo': 'bar', 'baz': None},
            [1, 1, 2, 3, 5, 8, 13, 21, 34, 55],
            set(u'Eyjafjallajökull'),
            u'埃亚菲亚德拉冰盖'
        ]
        self.comparable_values = [
            'aaa',
            'ccc',
            'eee',
            'ddd',
            'bbb'
        ]
        self.sl = sqlist.SQList(self.test_values)

    def tearDown(self):
        del self.test_values
        del self.comparable_values
        del self.sl

    def test_constructor_creates_correct_table(self):
        """
        Constructor should create one table with two columns
        """
        sl = sqlist.SQList()
        expected_pragma = [
            {
                'name': 'key',
                'type': 'BLOB',
                'notnull': False
            },
            {
                'name': 'value',
                'type': 'BLOB',
                'notnull': True
            }
        ]
        pragma = [{'name': i[1], 'type': i[2], 'notnull': i[3]}
                  for i in sl.cursor.execute('''PRAGMA table_info(`data`);''')]
        self.assertEqual(len(pragma), len(expected_pragma))
        for table in expected_pragma:
            self.assertTrue(table in pragma)

    def test_constructor_creates_correct_indexes(self):
        """
        There should be only one not unique index on `key` column
        """
        sl = sqlist.SQList()
        index_list = list(sl.cursor.execute('''PRAGMA index_list(`data`);'''))
        self.assertEqual(len(index_list), 1)
        index_name = index_list[0][1]
        index_info = sl.cursor.execute(
            '''PRAGMA index_info(%s);''' % index_name).fetchone()
        self.assertEqual(index_info[2], 'key')

    def test_constructor_creates_file_of_database(self):
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'test_sqlist.db')
        sl = sqlist.SQList(path=temp_file)

        self.assertTrue(os.path.isfile(temp_file))

        os.remove(temp_file)
        os.removedirs(temp_dir)

    def test_constructor_with_list_of_predefined_values_and_contains_method(self):
        self.assertEqual(len(self.test_values), len(self.sl))
        for i in self.test_values:
            self.assertTrue(i in self.sl)
        self.assertFalse('some_spam_string' in self.sl)

    def test_constructor_with_key_parameter(self):
        def key(x):
            return len(x)

        self.assertEqual(list(sqlist.SQList(self.test_values, key=key)),
                         sorted(self.test_values, key=key))

    def test_eq_method(self):
        self.assertTrue(self.sl.__eq__(self.test_values))

    def test_iter_method(self):
        self.assertEqual(self.test_values, list(self.sl))

    def test_len_method(self):
        self.assertEqual(len(self.test_values), len(self.sl))

    def test_setitem_and_getitem_methods(self):
        for i in range(len(self.sl)):
            self.sl[i] = self.test_values[i]
            self.assertEqual(self.sl[i], self.test_values[i])

        self.assertEqual(self.sl[0:3], self.test_values[0:3])

        with self.assertRaises(IndexError):
            spam = self.sl[len(self.sl) + 5]
            self.sl[len(self.sl) + 5] = 3

    def test_delitem_method(self):
        del self.sl[0]

        self.assertEqual(len(self.sl), len(self.test_values) - 1)
        self.assertFalse(self.test_values[0] in self.sl)

        with self.assertRaises(IndexError):
            del self.sl[len(self.sl) + 5]

    def test_append_method(self):
        test_appendix = (1, 2, 3)
        self.sl.append(test_appendix)

        self.assertEqual(len(self.sl), len(self.test_values) + 1)
        self.assertEqual(self.sl[-1], test_appendix)
        self.assertTrue(test_appendix in self.sl)

    def test_pop_method(self):
        self.assertEqual(self.sl.pop(), self.test_values.pop())
        self.assertEqual(self.sl.pop(0), self.test_values.pop(0))
        self.assertEqual(self.sl.pop(1), self.test_values.pop(1))
        self.assertEqual(len(self.test_values), len(self.sl))

    def test_sort_method_direct_with_key(self):
        def key(x):
            return len(x)
        sl = sqlist.SQList(self.comparable_values)

        sl.sort(key=key)
        self.comparable_values.sort(key=key)
        self.assertEqual(sl, self.comparable_values)
        self.assertTrue(sl.key is None)

    def test_sort_method_reversed_with_key(self):
        def key(x):
            return len(x)
        sl = sqlist.SQList(self.comparable_values)

        sl.sort(key=key, reverse=True)
        self.comparable_values.sort(key=key, reverse=True)
        self.assertEqual(sl, self.comparable_values)
        self.assertTrue(sl.key is None)

    def test_sort_method_direct_without_key(self):
        sl = sqlist.SQList(self.comparable_values, key=lambda x: hash(x))

        sl.sort()
        self.comparable_values.sort()
        self.assertEqual(list(sl), self.comparable_values)
        self.assertTrue(sl.key is None)

    def test_sort_method_reversed_without_key(self):
        sl = sqlist.SQList(self.comparable_values, key=lambda x: hash(x))

        sl.sort(reverse=True)
        self.comparable_values.sort(reverse=True)
        self.assertEqual(sl, self.comparable_values)
        self.assertTrue(sl.key is None)

    def test_iadd_method(self):
        self.sl += self.comparable_values

        self.assertEqual(self.sl, self.test_values + self.comparable_values)

    def test_iadd_method_with_noniterable(self):
        with self.assertRaises(TypeError):
            self.sl += 24

    def test_temp_class_method(self):
        sl = sqlist.SQList.temp()
        self.assertTrue(os.path.exists(sl.path))

    def test_temp_sqlist_auto_remove(self):
        sl = sqlist.SQList.temp(prefix='auto_remove_test', auto_remove=True)
        temp_path = sl.path
        del sl
        sleep(5)
        self.assertFalse(os.path.exists(temp_path))
