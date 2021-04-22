import asyncio
import os
import sqlite3
import sys
import webbrowser

import aiohttp
import requests
from PyQt5 import QtCore
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, \
    QMainWindow, QAction, qApp, QTableWidget, QTableWidgetItem, QGridLayout, \
    QLineEdit, QHeaderView, QFileDialog, QMessageBox

from pmcutilities import parse_sqlite, update_sqlite, pmc_query, write_results_file, abstract_window


class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_table = QTableWidget()
        self.search_table = QTableWidget()
        self.onlyInt = QIntValidator()
        self.textBox = QLineEdit()
        self.query_max = QLineEdit()
        self.title = "Reeves Lab - PMC Fetch"
        self.left = 10
        self.top = 10
        self.width = 800
        self.height = 600
        self.checked = True
        self.search_results = {}
        self.db_data = {}
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.init_ui()
        self._create_menu_bar()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.create_grid_layout()
        self._create_table_widget(0, 7, ["Keep", "PMC ID", "Title", "Date", "Authors", "Journal", "DOI"])
        self.show()

    '''
        Defining the menu bar
        Currently contains two items:
            1. File
                - Save search results to tab-delimited text file
            2. Exit the application
    '''

    def _create_menu_bar(self):
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False)

        # Creating file menu
        fileMenu = menuBar.addMenu("File")

        # Reset program
        reset_app = QAction("&Reset", self)
        reset_app.setShortcut("Ctrl+R")
        reset_app.setStatusTip("Reset application to default. | Ctrl (⌘) + R")
        reset_app.triggered.connect(self.reset_application)
        fileMenu.addAction(reset_app)

        # Save button
        saveAct = QAction("&Save", self)
        saveAct.setShortcut("Ctrl+S")
        saveAct.setStatusTip("Save search results to file. | Ctrl (⌘) + S")
        saveAct.triggered.connect(self.save_results)
        fileMenu.addAction(saveAct)

        # Export button
        export_menu = fileMenu.addMenu("Export")
        export_act = QAction("&Bibtex", self)
        export_act.setStatusTip("Export selected results to Bibtex")
        export_act.triggered.connect(self.export_bib)
        export_menu.addAction(export_act)

        # Export selected items to NEW SQLite3 DB
        db_export_act = QAction("&SQLite3 DB", self)
        db_export_act.setStatusTip("Export selected results to new SQLite3 DB")
        db_export_act.triggered.connect(self.export_db)
        export_menu.addAction(db_export_act)

        # Menu item for loading DB
        load_db_act = QAction("&Load", self)
        load_db_act.setShortcut("Ctrl+O")
        load_db_act.setStatusTip("Load DB | Ctrl (⌘) + O")
        load_db_act.triggered.connect(self.load_db)
        menuBar.addAction(load_db_act)

        # Create a menu item to exit the application
        exitAct = QAction("&Exit", self)
        exitAct.setShortcut("Ctrl+Q")
        exitAct.setStatusTip("Exit application | Ctrl (⌘) + Q")
        exitAct.triggered.connect(qApp.quit)
        menuBar.addAction(exitAct)

        # Start a status bar at the bottom of the application
        self.statusBar()

    def create_grid_layout(self):
        layout = QGridLayout()
        run_label = QLabel("Search Query")
        layout.addWidget(run_label, 0, 0)

        self.textBox.resize(25, 25)
        self.textBox.setStatusTip("Search PMC for this query.")
        layout.addWidget(self.textBox, 1, 0, 1, 1)

        query_label = QLabel("Num. Results to Return")
        layout.addWidget(query_label, 0, 1)

        self.query_max.resize(25, 25)
        self.query_max.setStatusTip("Max number of results to return.")
        self.query_max.setText("500")
        self.query_max.setValidator(self.onlyInt)

        layout.addWidget(self.query_max, 1, 1, 1, 1)

        toggle_keep = QPushButton("Check/Uncheck All")
        toggle_keep.clicked.connect(self.check_uncheck)
        layout.addWidget(toggle_keep, 2, 0, QtCore.Qt.AlignLeft)

        searchButton = QPushButton("Run Query")
        searchButton.setStatusTip("Run the entered query against PMC database.")
        searchButton.clicked.connect(self.search_pmc)
        self.textBox.returnPressed.connect(searchButton.click)
        layout.addWidget(searchButton, 2, 1, 1, 2)

        self.centralWidget.setLayout(layout)

    def _create_table_widget(self, row_count, col_count, header_labels):
        # Initialize the table with a single row and the 7 columns we have
        self.search_table.setRowCount(row_count)
        self.search_table.setColumnCount(col_count)
        self.search_table.setHorizontalHeaderLabels(header_labels)

        # Some of the table components should be allowed to stretch, like title
        # Others should expand to fit the contents
        self.search_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.search_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.search_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.search_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.search_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)

        # Disable editing of cells
        self.search_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Link function to double click of cell - if the user double clicks the cell with the DOI link
        # it opens the link in the browser
        self.search_table.cellDoubleClicked.connect(self.open_link)
        self.centralWidget.layout().addWidget(self.search_table, 3, 0, 1, 3)

    '''
        Reset Application
        Resets application to default settings.
    '''

    def reset_application(self):
        self.textBox.setText("")
        self.centralWidget.layout().removeWidget(self.search_table)
        self._create_table_widget()

    '''
        Search PMC Function
        Take user input from search bar and use that to search PMC database
    '''

    def search_pmc(self):
        ids = pmc_query(self.textBox.text(), int(self.query_max.text()))
        self.search_table.setRowCount(len(ids))
        i = 0
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/" \
              "esummary.fcgi?db=pmc&retmode=json&tool=reevestool&email=kylekroll@outlook,com&id="
        chunks = [ids[i:i + 200] for i in range(0, len(ids), 200)]
        for chunk in chunks:
            detailed_url = url + ','.join(chunk)
            details = requests.post(detailed_url)
            details = details.json()
            for id in chunk:
                chkBoxItem = QTableWidgetItem()
                chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                chkBoxItem.setCheckState(QtCore.Qt.Checked)
                self.search_table.setItem(i, 0, chkBoxItem)
                self.search_table.setItem(i, 1, QTableWidgetItem(details['result'][id]['uid']))
                self.search_table.setItem(i, 2, QTableWidgetItem(details['result'][id]['title']))
                self.search_table.setItem(i, 3, QTableWidgetItem(details['result'][id]['pubdate']))
                authors = [x['name'] for x in details['result'][id]['authors']]
                self.search_table.setItem(i, 4, QTableWidgetItem(", ".join(authors)))
                self.search_table.setItem(i, 5, QTableWidgetItem(details['result'][id]['fulljournalname']))
                for item in details['result'][id]['articleids']:
                    if item['idtype'] == 'doi':
                        self.search_table.setItem(i, 6, QTableWidgetItem(f"https://doi.org/{item['value']}"))
                i = i + 1
        self.search_table.sortItems(3, QtCore.Qt.DescendingOrder)
        self.statusBar().showMessage("Search complete.")

    '''
        Open DOI link
        If the user double clicks the cell with the DOI link, it opens it in the default browser
    '''

    def open_link(self, row, column):
        try:
            item = self.search_table.item(row, column).text()
            if item.startswith("https"):
                webbrowser.open(item)
            else:
                pmc = self.search_table.item(row, 1).text()
                auths = self.search_table.item(row, 4).text()
                title = self.search_table.item(row, 2).text()
                abstract_window(self, pmc, auths, title)
        except AttributeError:
            pass

    '''
        Check Uncheck
        Iterate through items in table checking or unchecking
    '''

    def check_uncheck(self):
        for row in range(0, self.search_table.rowCount()):
            if self.checked:
                self.search_table.item(row, 0).setCheckState(0)
            else:
                self.search_table.item(row, 0).setCheckState(2)
        self.checked = not self.checked

    '''
        Save Results
        When the user performs a search they can save the checked items to file
    '''

    def save_results(self):
        if self.search_table.rowCount() >= 1:
            save_file = QFileDialog.getSaveFileName(None, 'Title', '', 'Tab-delimited text (*.tdt)')[0]
            write_results_file(save_file, self.search_table)
        else:
            QMessageBox.about(self, "", "Please run query before trying to save!")

    '''
        Export to Bibtex
        Take the selected references and export to Bibtex based on DOI
    '''

    def export_bib(self):
        self.statusBar().showMessage("Generating Bibtex")
        if self.search_table.rowCount() >= 1:
            items = self.get_bibs()
            save_file = QFileDialog.getSaveFileName(None, 'Title', '', 'Bibtex (*.bib)')[0]
            if save_file != '':
                with open(f"{save_file}", "w+") as f:
                    for item in items:
                        f.write(item + "\n")
        else:
            QMessageBox.about(self, "", "Please run query before trying to save!")

    def get_bibs(self):
        websites = []
        for row in range(0, self.search_table.rowCount()):
            if self.search_table.item(row, 0).checkState() == QtCore.Qt.Checked:
                url = "/".join(self.search_table.item(row, 6).text().split("/")[3:5])
                url = f"http://api.crossref.org/works/{url}/transform/application/x-bibtex"
                websites.append(url)
        urls = websites
        items = asyncio.run(self.async_main(urls))
        return items

    async def async_get(self, url, session):
        try:
            async with session.get(url=url) as response:
                resp = await response.read()
                return resp.decode()
        except Exception as e:
            print("Unable to get url {} due to {}.".format(url, e.__class__))

    async def async_main(self, urls):
        async with aiohttp.ClientSession() as session:
            ret = await asyncio.gather(*[self.async_get(url, session) for url in urls])
            return ret

    def load_db(self):
        self.open_db = QFileDialog.getOpenFileName(None, 'SQLite3 DB', '', 'SQLite3 (*.sqlite3)')[0]
        items = parse_sqlite(self.open_db)
        self.db_table.setRowCount(len(items))
        self.db_table.setColumnCount(len(items[0].keys()))
        self.db_table.setHorizontalHeaderLabels(items[0].keys())
        # Some of the table components should be allowed to stretch, like title
        # Others should expand to fit the contents
        self.db_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.db_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.db_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.db_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        self.db_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.db_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)

        # Disable editing of cells
        self.db_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # Link function to double click of cell - if the user double clicks the cell with the DOI link
        # it opens the link in the browser
        self.db_table.cellDoubleClicked.connect(self.open_link)

        self.centralWidget.layout().addWidget(QLabel("Database"), 4, 0)
        insert_value_button = QPushButton("Insert ↓")
        insert_value_button.clicked.connect(self.insert_values)
        self.centralWidget.layout().addWidget(insert_value_button, 4, 1)
        self.centralWidget.layout().addWidget(self.db_table, 5, 0, 1, 3)
        self.update_db_table()

    def update_db_table(self):
        items = parse_sqlite(self.open_db)

        self.db_table = update_sqlite(self.db_table, items)

    def insert_values(self):
        if not self.con:
            print("Error: Connection closed to DB!")
            sys.exit()
        else:
            items = []
            for row in range(0, self.search_table.rowCount()):
                litems = {}
                if self.search_table.item(row, 0).checkState() == QtCore.Qt.Checked:
                    litems['PMC'] = self.search_table.item(row, 1).text()
                    litems['TITLE'] = self.search_table.item(row, 2).text()
                    litems['DATE'] = self.search_table.item(row, 3).text()
                    litems['AUTHORS'] = self.search_table.item(row, 4).text()
                    litems['JOURNAL'] = self.search_table.item(row, 5).text()
                    litems['DOI'] = self.search_table.item(row, 6).text()
                    items.append(litems)
            for item in items:
                self.con.execute('INSERT OR IGNORE INTO PUBLICATIONS '
                                 '(PMC, TITLE, DATE, AUTHORS, JOURNAL, DOI) '
                                 'VALUES (?, ?, ?, ?, ?, ?)',
                                 (item['PMC'], item['TITLE'], item['DATE'],
                                  item['AUTHORS'], item['JOURNAL'], item['DOI']))
            self.con.commit()
            self.update_db_table()

    def export_db(self):
        save_db = QFileDialog.getSaveFileName(None, 'SQLite3 DB', '', 'SQLite3 (*.sqlite3)')[0]
        if save_db != '':
            # Checks if file exists, if not creates the file
            if not os.path.exists(save_db):
                con = sqlite3.connect(save_db)
                con.execute('''CREATE TABLE PUBLICATIONS(
                            PMC NUMERIC(20) PRIMARY KEY,
                            TITLE TEXT NOT NULL,
                            JOURNAL TEXT NOT NULL,
                            AUTHORS TEXT NOT NULL,
                            DATE TEXT NOT NULL,
                            DOI TEXT NOT NULL);''')
                items = []
                for row in range(0, self.search_table.rowCount()):
                    litems = {}
                    if self.search_table.item(row, 0).checkState() == QtCore.Qt.Checked:
                        litems['PMC'] = self.search_table.item(row, 1).text()
                        litems['TITLE'] = self.search_table.item(row, 2).text()
                        litems['DATE'] = self.search_table.item(row, 3).text()
                        litems['AUTHORS'] = self.search_table.item(row, 4).text()
                        litems['JOURNAL'] = self.search_table.item(row, 5).text()
                        litems['DOI'] = self.search_table.item(row, 6).text()
                        items.append(litems)
                for item in items:
                    con.execute('INSERT OR IGNORE INTO PUBLICATIONS '
                                '(PMC, TITLE, DATE, AUTHORS, JOURNAL, DOI) '
                                'VALUES (?, ?, ?, ?, ?, ?)',
                                (item['PMC'], item['TITLE'], item['DATE'],
                                 item['AUTHORS'], item['JOURNAL'], item['DOI']))
                con.commit()
                con.close()
            else:
                raise Exception("Error: DB file already exists. Please choose a new file.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
