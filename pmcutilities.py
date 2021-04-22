import sqlite3
import ssl
import html

import requests

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


def pmc_query(query, n_max):
    if hasattr(ssl, "_create_unverified_context"):
        ssl._create_default_https_context = ssl._create_unverified_context
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc" \
                 f"&term={html.escape(query)}&retmode=json&retmax={n_max}" \
                 f"&tool=reevestool&email=kylekroll@outlook.com"
    return requests.get(search_url).json()['esearchresult']['idlist']


'''
    
'''
def write_results_file(filename, table):
    header = [table.horizontalHeaderItem(i).text() for i in range(0, table.columnCount())]
    items = []
    for row in range(0, table.rowCount()):
        row_items = []
        if table.item(row, 0).checkState() == QtCore.Qt.Checked:
            for col in range(1, table.columnCount()):
                row_items.append(table.item(row, col).text())
            items.append(row_items)
    if filename != '':
        with open(f"{filename}", "w+") as f:
            f.write("\t".join(header))
            f.write("\n")
            for it in items:
                f.write("\t".join(it))
                f.write("\n")
    return None
