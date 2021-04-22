import sqlite3
import ssl
import html
import xml.etree.ElementTree as ET
import requests
import os
import errno
import time
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
        chkBoxItem = QTableWidgetItem()
        chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        chkBoxItem.setCheckState(QtCore.Qt.Checked)
        db_table.setItem(i, 0, chkBoxItem)
        db_table.setItem(i, 1, QTableWidgetItem(str(items[i]['PMC'])))
        db_table.setItem(i, 2, QTableWidgetItem(items[i]['TITLE']))
        db_table.setItem(i, 3, QTableWidgetItem(items[i]['DATE']))
        db_table.setItem(i, 4, QTableWidgetItem(items[i]['AUTHORS']))
        db_table.setItem(i, 5, QTableWidgetItem(items[i]['JOURNAL']))
        db_table.setItem(i, 6, QTableWidgetItem(items[i]['DOI']))
    db_table.sortItems(5, QtCore.Qt.DescendingOrder)
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
    abstract_label = QLabel(ncbi_fetch([pmc]).get(pmc))
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
    req = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&retmode=xml&id=" + ",".join(pmc)).content
    tree = ET.ElementTree(ET.fromstring(req))
    root = tree.getroot()

    articles = root.findall('article')
    abstracts = {}
    for article in articles:
        pmc_id = article.findall(".//article-id")
        for id in pmc_id:
            if id.attrib['pub-id-type'] == 'pmc':
                pmc_id = id.text
        all_text = article.findall('.//abstract/p')
        abstract = ""
        for texts in all_text:
            abstract = "".join(texts.itertext())
        abstracts[pmc_id] = abstract
    return abstracts

def write_to_md(table, out_dir):
    # TODO
    # Need to refactor this so that it calls ncbi_fetch on a list of IDs and then parses them into abstracts
    # Currently running into API rate limits
    items = []
    for row in range(0, table.rowCount()):
        row_items = {}
        if table.item(row, 0).checkState() == QtCore.Qt.Checked:
            for col in range(1, table.columnCount()):
                row_items[table.horizontalHeaderItem(col).text()] = table.item(row, col).text()
            items.append(row_items)
    with open("./template.md", "r") as f:
        src = Template(f.read())
    ids = [item['PMC ID'] for item in items]
    chunks = [ids[i:i + 200] for i in range(0, len(ids), 200)]
    abstracts = {}
    for chunk in chunks:
        abstracts.update(ncbi_fetch(chunk))

    for item in items:
        abstract = abstracts[item['PMC ID']]
        authors = item['Authors'].split(",")
        authors = [x.strip() for x in authors]
        authors = [x.split(" ")[0] for x in authors]
        link = item['DOI'] if item['DOI'] != "" else "https://www.ncbi.nlm.nih.gov/pubmed/PMC" + item['PMC ID']
        d = {'abstract': abstract, 'authors': authors, 'date': item['Date'],
             'doi': link, 'journal': item['Journal'], 'title': item['Title']}

        results = src.substitute(d).encode("utf-8")

        filename = f"{out_dir}/{item['PMC ID']}/index.md"
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
        with open(filename, "w") as f:
            f.write(results.decode('ascii', 'ignore'))




