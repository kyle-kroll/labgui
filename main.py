import ssl
import sys
import webbrowser
import html

import requests
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, \
    QMainWindow, QAction, qApp, QTableWidget, QTableWidgetItem, QGridLayout, \
    QLineEdit, QHeaderView, QFileDialog, QMessageBox


class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.textBox = QLineEdit()
        self.title = "Reeves Lab - PMC Fetch"
        self.left = 10
        self.top = 10
        self.width = 800
        self.height = 600
        self.checked = True
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.init_ui()
        self._create_menu_bar()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.create_grid_layout()
        self._create_table_widget()
        self.show()

    def create_grid_layout(self):
        layout = QGridLayout()
        run_label = QLabel("Search Query")
        layout.addWidget(run_label, 0, 0)

        self.textBox.resize(25, 25)
        self.textBox.setStatusTip("Search PMC for this query.")
        layout.addWidget(self.textBox, 1, 0, 1, 3)

        toggle_keep = QPushButton("Check/Uncheck All")
        toggle_keep.clicked.connect(self.check_uncheck)
        layout.addWidget(toggle_keep, 2, 0, QtCore.Qt.AlignLeft)

        searchButton = QPushButton("Run Query")
        searchButton.setStatusTip("Run the entered query against PMC database.")
        searchButton.clicked.connect(self.search_pmc)
        self.textBox.returnPressed.connect(searchButton.click)
        layout.addWidget(searchButton, 2, 1, 1, 2)

        self.centralWidget.setLayout(layout)

    def _create_table_widget(self):
        # Initialize the table with a single row and the 7 columns we have
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setHorizontalHeaderLabels(["Keep", "PMC ID", "Title", "Date", "Authors", "Journal", "DOI"])

        # Some of the table components should be allowed to stretch, like title
        # Others should expand to fit the contents
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)

        # Disable editing of cells
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        # Link function to double click of cell - if the user double clicks the cell with the DOI link
        # it opens the link in the browser
        self.tableWidget.cellDoubleClicked.connect(self.open_link)
        self.centralWidget.layout().addWidget(self.tableWidget, 3, 0, 1, 3)

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
        reset_app = QAction("Reset", self)
        reset_app.setShortcut("Ctrl+R")
        reset_app.setStatusTip("Reset application to default. | Ctrl (⌘) + R")
        fileMenu.triggered.connect(self.reset_application)
        fileMenu.addAction(reset_app)


        # Save button
        saveAct = QAction("Save", self)
        saveAct.setShortcut("Ctrl+S")
        saveAct.setStatusTip("Save search results to file. | Ctrl (⌘) + S")
        saveAct.triggered.connect(self.save_results)
        fileMenu.addAction(saveAct)

        # Create a menu item to exit the application
        exitAct = QAction("&Exit", self)
        exitAct.setShortcut("Ctrl+Q")
        exitAct.setStatusTip("Exit application | Ctrl (⌘) + Q")
        exitAct.triggered.connect(qApp.quit)

        # Start a status bar at the bottom of the application
        self.statusBar()
        menuBar.addAction(exitAct)


    '''
        Reset Application
        Resets application to default settings.
    '''
    def reset_application(self):
        self.textBox.setText("")
        self.centralWidget.layout().removeWidget(self.tableWidget)
        self._create_table_widget()


    '''
        Search PMC Function
        Take user input from search bar and use that to search PMC database
    '''
    def search_pmc(self):
        if hasattr(ssl, "_create_unverified_context"):
            ssl._create_default_https_context = ssl._create_unverified_context
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc" \
                     f"&term={html.escape(self.textBox.text())}&retmode=json&retmax=500" \
                     f"&tool=reevestool&email=kylekroll@outlook.com"
        pmc_ids = requests.get(search_url)
        pmc_ids = pmc_ids.json()
        ids = pmc_ids['esearchresult']['idlist']
        self.tableWidget.setRowCount(len(ids))
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc" \
              "&retmode=json&tool=my_tool&email=my_email@example.com&id="
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
            # authors = [x['name'].replace(" ", ", ") for x in details['result'][id]['authors']]
            authors = [x['name'] for x in details['result'][id]['authors']]
            self.tableWidget.setItem(i, 4, QTableWidgetItem(", ".join(authors)))
            self.tableWidget.setItem(i, 5, QTableWidgetItem(details['result'][id]['fulljournalname']))
            for item in details['result'][id]['articleids']:
                if item['idtype'] == 'doi':
                    self.tableWidget.setItem(i, 6, QTableWidgetItem(f"https://doi.org/{item['value']}"))
        self.tableWidget.sortItems(3, QtCore.Qt.DescendingOrder)

    '''
        Open DOI link
        If the user double clicks the cell with the DOI link, it opens it in the default browser
    '''

    def open_link(self, row, column):
        item = self.tableWidget.item(row, column).text()
        if item.startswith("https"):
            webbrowser.open(item)

    '''
        Check Uncheck
        Iterate through items in table checking or unchecking
    '''

    def check_uncheck(self):
        for row in range(0, self.tableWidget.rowCount()):
            if self.checked:
                self.tableWidget.item(row, 0).setCheckState(0)
            else:
                self.tableWidget.item(row, 0).setCheckState(2)
        self.checked = not self.checked

    '''
        Save Results
        When the user performs a search they can save the checked items to file
    '''

    def save_results(self):
        if self.tableWidget.rowCount() >= 1:
            header = []
            items = []
            save_file = QFileDialog.getSaveFileName(None, 'Title', '', 'Tab-delimited text (*.tdt)')[0]
            for row in range(0, self.tableWidget.rowCount()):
                litems = []
                if self.tableWidget.item(row, 0).checkState() == QtCore.Qt.Checked:
                    for col in range(1, self.tableWidget.columnCount()):
                        litems.append(self.tableWidget.item(row, col).text())
                        if row == 0:
                            header.append(self.tableWidget.horizontalHeaderItem(col).text())
                    items.append(litems)
            if save_file != '':
                with open(f"{save_file}", "w+") as f:
                    f.write("\t".join(header))
                    f.write("\n")
                    for it in items:
                        f.write("\t".join(it))
                        f.write("\n")
        else:
            QMessageBox.about(self, "", "Please run query before trying to save!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
