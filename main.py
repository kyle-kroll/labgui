import sys
import webbrowser

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, QLabel, QMainWindow, QMenuBar
from PyQt5.QtWidgets import QMenu, QAction, qApp, QTableWidget, QTableWidgetItem, QGroupBox, QGridLayout, QLineEdit, QHeaderView
from PyQt5 import QtCore, Qt
import json
import ssl
import requests
import time


class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title = "Reeves Lab - PMC Fetch"
        self.left = 10
        self.top = 10
        self.width = 800
        self.height = 600
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.initUI()
        self._createMenuBar()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.createGridLayout()
        self._createTableWidget()
        tempButton = QPushButton("Testing")
        tempButton.clicked.connect(self.get_pmc_info)
        self.centralWidget.layout().addWidget(tempButton)
        self.show()

    def createGridLayout(self):
        layout = QGridLayout()
        run_label = QLabel("Search Query")
        layout.addWidget(run_label, 0, 0)
        self.textBox = QLineEdit()
        self.textBox.resize(25, 25)
        self.textBox.setStatusTip("Search PMC for this query.")
        layout.addWidget(self.textBox, 1, 0)
        searchButton = QPushButton("Run Query")
        searchButton.setStatusTip("Run the entered query against PMC database.")
        searchButton.clicked.connect(self.load_db)
        self.textBox.returnPressed.connect(searchButton.click)
        layout.addWidget(searchButton)
        self.centralWidget.setLayout(layout)

    def _createTableWidget(self):
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setHorizontalHeaderLabels(["Keep", "PMC ID", "Title", "Date", "Authors", "Journal", "DOI"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableWidget.cellDoubleClicked.connect(self.open_link)
        self.centralWidget.layout().addWidget(self.tableWidget)

    def _createMenuBar(self):
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False)
        # Creating file menu
        fileMenu = menuBar.addMenu("File")
        openAct = QAction("Load DB", self)
        openAct.setStatusTip("Load the Publication DB")
        openAct.triggered.connect(self.load_db)
        fileMenu.addAction(openAct)
        # Create a menu item to exit the application
        exitAct = QAction("&Exit", self)
        exitAct.setShortcut("Ctrl+Q")
        exitAct.setStatusTip("Exit application | Ctrl (⌘) + Q")
        exitAct.triggered.connect(qApp.quit)

        # Start a status bar at the bottom of the application
        self.statusBar()
        menuBar.addAction(exitAct)

    def load_db(self):
        if hasattr(ssl, "_create_unverified_context"):
            ssl._create_default_https_context = ssl._create_unverified_context
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc" \
                     f"&term={self.textBox.text()}&retmode=json&retmax=500" \
                     f"&tool=reevestool&email=kylekroll@outlook.com"
        pmc_ids = requests.get(search_url)
        pmc_ids = pmc_ids.json()
        ids = pmc_ids['esearchresult']['idlist']
        self.tableWidget.setRowCount( len(ids) )
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&retmode=json&tool=my_tool&email=my_email@example.com&id="
        detailed_url = f"{url}{','.join(pmc_ids['esearchresult']['idlist'])}"
        details = requests.get(detailed_url).json()
        for i in range(0, len(details['result']['uids'])):
            id = details['result']['uids'][i]
            chkBoxItem = QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Checked)
            self.tableWidget.setItem(i, 0, chkBoxItem)
            self.tableWidget.setItem(i, 1, QTableWidgetItem(details['result'][id]['uid']))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(details['result'][id]['title']))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(details['result'][id]['pubdate']))
            authors = [x['name'].replace(" ",", ") for x in details['result'][id]['authors']]
            self.tableWidget.setItem(i, 4, QTableWidgetItem("., ".join(authors)))
            self.tableWidget.setItem(i, 5, QTableWidgetItem(details['result'][id]['fulljournalname']))
            for item in details['result'][id]['articleids']:
                if item['idtype'] == 'doi':
                    self.tableWidget.setItem(i, 6, QTableWidgetItem(f"https://doi.org/{item['value']}"))

    def open_link(self, row, column):
        item = self.tableWidget.item(row, column).text()
        if item.startswith("https"):
            webbrowser.open(item)

    def get_pmc_info(self, url):

        header = []
        items = []
        for row in range(0, self.tableWidget.rowCount()):
            litems = []
            if self.tableWidget.item(row, 0).checkState() == QtCore.Qt.Checked:
                for col in range(1, self.tableWidget.columnCount()):
                    litems.append(self.tableWidget.item(row, col).text())
                    if row == 0:
                        header.append(self.tableWidget.horizontalHeaderItem(col).text())
            items.append(litems)
        with open(f"/Users/kkroll1/Desktop/{self.textBox.text()}.tdt", "w+") as f:
            f.write("\t".join(header))
            f.write("\n")
            for it in items:
                f.write("\t".join(it))
                f.write("\n")





if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
