import sqlite3

from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5 import QtCore

def parse_sqlite(filename):
    items = []
    if filename != '':
        con = sqlite3.connect(filename)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute('''SELECT * FROM PUBLICATIONS''')

        rows = cur.fetchall()
        for row in rows:
            items.append(dict(row))
        cur.close()
        con.close()
    return items


def save_tdt(filename, items):
    return None


def update_sqlite(db_table, items):
    db_table.setRowCount(len(items))
    for i in range(0, len(items)):
        db_table.setItem(i, 0, QTableWidgetItem(str(items[i]['PMC'])))
        db_table.setItem(i, 1, QTableWidgetItem(items[i]['TITLE']))
        db_table.setItem(i, 2, QTableWidgetItem(items[i]['JOURNAL']))
        db_table.setItem(i, 3, QTableWidgetItem(items[i]['AUTHORS']))
        db_table.setItem(i, 4, QTableWidgetItem(items[i]['DATE']))
        db_table.setItem(i, 5, QTableWidgetItem(items[i]['DOI']))
    db_table.sortItems(4, QtCore.Qt.DescendingOrder)
    return db_table
