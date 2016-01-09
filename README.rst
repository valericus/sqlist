.. image:: https://travis-ci.org/valericus/sqlist.svg?branch=master
    :target: https://travis-ci.org/valericus/sqlist

SQList is like `shelve <https://docs.python.org/3/library/shelve.html>`_ but for lists. It serializes data with `pickle <https://docs.python.org/3/library/pickle.html>`_ and puts into SQLite database.

Usage
=====

SQLite object behaves mostly like casual Python list. For example you can create SQList from list.

>>> import sqlist
>>> values = sqlist.SQList([1, 2, 3])
>>> values
sqlist.SQList([1, 2, 3])

You can get item from list by index.

>>> values[0]
1
>>> values[-1]
3

Slices are available too.

>>> values[0:2]
[1, 2]

You can easily append item to SQList and pop them from it.

>>> values.append(23)
>>> values
sqlist.SQList([1, 2, 3, 23])
>>> valuea.pop(0)
1
>>> values
sqlist.SQList([2, 3, 23])

Unfortunately inserting is not available yet but planned for future versions.

By the way, you can also sort SQList just in place, but be careful, this sorting a bit differs from usual list sorting. If you specify ``key`` parameter, it will be used for sorting, but if you leave it ``None``, sorting order will be restored to order of appending items to SQList.

>>> values.sort(key=lambda x: 1 / x)
>>> values
sqlist.SQList([23, 3, 2])
>>> values.sort()
>>> values
sqlist.SQList([2, 3, 23])
