import unittest

import sqlist


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

    def test_constructor(self):
        chell = sqlist.SQList()
        expected_schema = '''CREATE TABLE `data` (`key` BLOB,
                                    `value` BLOB NOT NULL)'''
        current_schema = chell.cursor.execute(
                        '''SELECT `sql`
                           FROM `sqlite_master`
                           WHERE `type` = 'table' AND `name` = 'data';'''
                ).fetchone()[0]
        print(current_schema)
        self.assertEqual(current_schema, expected_schema)

