# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
import logging

import sqlist

logging.basicConfig(level=logging.DEBUG)


class TestSQList(unittest.TestCase):
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

    def test_constructor_with_list_of_predefined_values(self):
        test_values = [
            {'foo': 'bar', 'baz': None},
            [1, 1, 2, 3, 5, 8, 13, 21, 34, 55],
            set(u'Eyjafjallajökull'),
            u'埃亚菲亚德拉冰盖'
        ]
        sl = sqlist.SQList(test_values)

        self.assertEqual(len(test_values), len(sl))
        for i in test_values:
            self.assertTrue(i in sl)
