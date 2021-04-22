import sqlite3
import ssl
import html
import xml.etree.ElementTree as ET
import requests
import os
import errno
from string import Template

from PyQt5.QtWidgets import QTableWidgetItem, QDialog, QVBoxLayout, QSizePolicy, QLabel, QScrollArea
from PyQt5 import QtCore


def parse_sqlite(filename):
    """Opens connection to SQLite3 database file and returns all rows in the table."""
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


def update_sqlite(db_table, items):
    """Updates the supplied QTableWidget - db_table - with items."""
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
    """Searched the PMC database using the supplied query and returns n_max results."""
    if hasattr(ssl, "_create_unverified_context"):
        ssl._create_default_https_context = ssl._create_unverified_context
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc" \
                 f"&term={html.escape(query)}&retmode=json&retmax={n_max}" \
                 f"&tool=reevestool&email=kylekroll@outlook.com"
    return requests.get(search_url).json()['esearchresult']['idlist']


def write_results_file(filename, table):
    """Writes the data in supplied table to the specified filename"""
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


def abstract_window(self, pmc, authors, title):
    """Opens a new window with the abstract for the selected item."""

    abstract_label = QLabel(ncbi_fetch(pmc))
    abstract_label.setWordWrap(True)
    abstract_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
    widget = QDialog(self)

    layout = QVBoxLayout()
    layout.addWidget(QLabel("Title: " + title))
    layout.addWidget(QLabel("Authors: " + authors))

    test = QScrollArea()
    test.setWidget(abstract_label)

    layout.addWidget(test)

    widget.setLayout(layout)
    widget.resize(abstract_label.width() + 50, abstract_label.height() + 50)

    widget.setWindowTitle("Abstract")
    widget.show()

    return None

def ncbi_fetch(pmc):
    req = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&retmode=xml&id=" + pmc).content
    tree = ET.ElementTree(ET.fromstring(req))
    root = tree.getroot()
    all_text = root.findall('.//abstract/p')
    abstract = ""
    for texts in all_text:
        abstract = "".join(texts.itertext())
    return abstract

def write_to_md(items):
    with open("./template.md", "r") as f:
        src = Template(f.read())
    for item in items:
        abstract = ncbi_fetch(item['PMC'])
        authors = item['AUTHORS'].split(",")
        authors = [x.strip() for x in authors]
        authors = [x.split(" ")[0] for x in authors]
        d = {'abstract': abstract, 'authors': authors, 'date': item['DATE'],
             'doi': item['DOI'], 'journal': item['JOURNAL'], 'title': item['TITLE']}

        results = src.substitute(d).encode("utf-8")

        filename = f"publication/{item['PMC']}/index.md"
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
        with open(filename, "w") as f:
            f.write(results.decode('ascii', 'ignore'))


