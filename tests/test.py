# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
import logging

import sqlist

logging.basicConfig(level=logging.DEBUG)


class TestSQList(unittest.TestCase):
    def setUp(self):
        self.test_values = [
            {'foo': 'bar', 'baz': None},
            [1, 1, 2, 3, 5, 8, 13, 21, 34, 55],
            set(u'Eyjafjallajökull'),
            u'埃亚菲亚德拉冰盖'
        ]
        self.sl = sqlist.SQList(self.test_values)

    def tearDown(self):
        del self.sl

    def test_calc_index(self):
        self.assertEqual(sqlist.SQList._SQList__calc_index(0), 0)
        self.assertEqual(sqlist.SQList._SQList__calc_index(-1), 0)
        self.assertEqual(sqlist.SQList._SQList__calc_index(5), 5)
        self.assertEqual(sqlist.SQList._SQList__calc_index(-5), 4)

    def test_get_order(self):
        self.assertEqual(sqlist.SQList._SQList__get_order(0), 'ASC')
        self.assertEqual(sqlist.SQList._SQList__get_order(-1), 'DESC')
        self.assertEqual(sqlist.SQList._SQList__get_order(5), 'ASC')
        self.assertEqual(sqlist.SQList._SQList__get_order(-5), 'DESC')

    def test_constructor_creates_correct_table(self):
        """
        Consrtuctor should create one table with two columns
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
        logging.debug('Pragma: %s' % pragma)
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
        logging.debug('''PRAGMA index_info(%s);''' % index_name)
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

    def test_iter_method(self):
        self.assertEqual(self.test_values, list(self.sl))

    def test_len_method(self):
        self.assertEqual(len(self.test_values), len(self.sl))

    def test_setitem_and_getitem_methods(self):
        for i in range(len(self.sl)):
            self.sl[i] = self.test_values[i]
            self.assertEqual(self.sl[i], self.test_values[i])

        self.assertRaises(IndexError, self.sl.__getitem__, len(self.sl) + 5)
        self.assertRaises(IndexError, self.sl.__setitem__, len(self.sl) + 5, 3)

    def test_delitem_method(self):
        pass