# -*- coding: utf-8 -*-

import os
import sys
import glob
import signal
import logging

import matplotlib
#matplotlib.use('Qt4Agg')

try:
    from PySide.QtCore import *
    from PySide.QtGui  import *
    os.environ['QT_API'] = 'pyside'
    matplotlib.rcParams['backend.qt4']='PySide'
    try:
        import Resources_pyside
    except ImportError:
        print "Missing file Resources_pyside.py: Run script update_resources.sh"
except ImportError:
    print "Can't import PySide modules."
    sys.exit()

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import matplotlib.pyplot as plt

import GetDistPlots
import MCSamples

import batchJob

# ==============================================================================

class MainWindow(QMainWindow):

    def __init__(self):
        """
        Initialize of GUI components.
        """
        super(MainWindow, self).__init__()

        self.setAttribute(Qt.WA_DeleteOnClose)

        self.createDockWidgets()
        self.createActions()
        self.createMenus()
        self.createStatusBar()

        self.setWindowTitle("GetDist GUI")
        self.resize(800, 600)

        # Allow to shutdown the GUI with Ctrl+C
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self.iniFile = ""

        # Root directory
        self.rootdir = ""
        self.root = ""
        self.other_roots = {}

        self.plotter = None


    def createActions(self):
        self.exportAct = QAction(QIcon(":/images/file_export.png"),
                                 "&Export as PDF", self,
                                 statusTip="Export image as PDF",
                                 triggered=self.export)

        self.scriptAct = QAction(QIcon(":/images/file_save.png"),
                                 "Save script", self,
                                 statusTip="Export commands to script",
                                 triggered=self.script)

        self.exitAct = QAction(QIcon(":/images/application_exit.png"),
                               "E&xit", self,
                               shortcut="Ctrl+Q",
                               statusTip="Exit application",
                               triggered=self.close)

        self.statsAct = QAction(QIcon(":/images/view_text.png"),
                               "Marge Stats", self,
                               shortcut="",
                               statusTip="Show Marge Stats",
                               triggered=self.showMargeStats)

        self.aboutAct = QAction(QIcon(":/images/help_about.png"),
                                "&About", self,
                                statusTip="Show About box",
                                triggered=self.about)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.exportAct)
        self.separatorAct = self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.menuBar().addSeparator()
        self.dataMenu = self.menuBar().addMenu("&Data")
        self.dataMenu.addAction(self.statsAct)

        self.menuBar().addSeparator()

        self.windowMenu = self.menuBar().addMenu("&Windows")
        self.windowMenu.addAction(self.dockTop.toggleViewAction())

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def createStatusBar(self):
        self.statusBar().showMessage("Ready", 2000)

    def createDockWidgets(self):

        # Top: select Widget
        self.dockTop = QDockWidget(self.tr("Filters"), self)
        self.dockTop.setAllowedAreas(Qt.LeftDockWidgetArea)

        self.selectWidget = QWidget(self.dockTop)

        self.lineEditDirectory = QLineEdit(self.selectWidget)
        self.lineEditDirectory.clear()
        self.lineEditDirectory.setReadOnly(True)

        self.pushButtonSelect = QPushButton(QIcon(":/images/folder_open.png"),
                                            "", self.selectWidget)
        self.pushButtonSelect.setToolTip("Choose root directory")
        self.connect(self.pushButtonSelect, SIGNAL("clicked()"), self.selectRootDir)
        shortcut = QShortcut(QKeySequence(self.tr("Ctrl+O")), self)
        self.connect(shortcut, SIGNAL("activated()"), self.selectRootDir)

        self.pushButtonRoots = QPushButton("Manage additional chain roots", self.selectWidget)
        self.connect(self.pushButtonRoots, SIGNAL("clicked()"), self.manageOtherRoots)
        self.pushButtonAdd = QPushButton(QIcon(":/images/file_add.png"),
                                            "", self.selectWidget)
        self.pushButtonAdd.setToolTip("Add a root directory")
        self.connect(self.pushButtonAdd, SIGNAL("clicked()"), self.addRoot)

        self.comboBoxParamTag = QComboBox(self.selectWidget)
        self.comboBoxParamTag.clear()
        self.connect(self.comboBoxParamTag, SIGNAL("activated(const QString&)"), self.setParamTag)

        self.comboBoxDataTag = QComboBox(self.selectWidget)
        self.comboBoxDataTag.clear()
        self.connect(self.comboBoxDataTag, SIGNAL("activated(const QString&)"), self.setDataTag)

        self.listParametersX = QListWidget(self.selectWidget)
        self.listParametersX.clear()
        self.connect(self.listParametersX, SIGNAL("itemChanged(QListWidgetItem *)"), self.itemParamXChanged)

        self.listParametersY = QListWidget(self.selectWidget)
        self.listParametersY.clear()
        self.connect(self.listParametersY, SIGNAL("itemChanged(QListWidgetItem *)"), self.itemParamYChanged)

        self.selectAllX = QCheckBox("Select All", self.selectWidget)
        self.selectAllX.setCheckState(Qt.Unchecked)
        self.connect(self.selectAllX, SIGNAL("clicked()"), self.statusSelectAllX)

        self.selectAllY = QCheckBox("Select All", self.selectWidget)
        self.selectAllY.setCheckState(Qt.Unchecked)
        self.connect(self.selectAllY, SIGNAL("clicked()"), self.statusSelectAllY)

        self.toggleFilled = QRadioButton("Filled")
        self.toggleLine = QRadioButton("Line")
        self.toggleColor = QRadioButton("Color by:")
        self.comboBoxColor = QComboBox(self)
        self.comboBoxColor.clear()
        self.toggleFilled.setChecked(True)

        self.trianglePlot = QCheckBox("Triangle Plot", self.selectWidget)
        self.trianglePlot.setCheckState(Qt.Unchecked)

        self.pushButtonPlot = QPushButton("Make plot", self.selectWidget)
        self.connect(self.pushButtonPlot, SIGNAL("clicked()"), self.plotData)

        # Graphic Layout
        layoutTop = QGridLayout()
        layoutTop.setSpacing(5)
        layoutTop.addWidget(self.lineEditDirectory, 0, 0, 1, 3)
        layoutTop.addWidget(self.pushButtonSelect,  0, 3, 1, 1)
        layoutTop.addWidget(self.pushButtonRoots,   1, 0, 1, 3)
        layoutTop.addWidget(self.pushButtonAdd,     1, 3, 1, 1)
        layoutTop.addWidget(self.comboBoxParamTag,  2, 0, 1, 2)
        layoutTop.addWidget(self.comboBoxDataTag,   2, 2, 1, 2)
        layoutTop.addWidget(self.selectAllX,        3, 0, 1, 2)
        layoutTop.addWidget(self.selectAllY,        3, 2, 1, 2)
        layoutTop.addWidget(self.listParametersX,   4, 0, 5, 2)
        layoutTop.addWidget(self.listParametersY,   4, 2, 1, 2)
        layoutTop.addWidget(self.toggleFilled,      5, 2, 1, 2)
        layoutTop.addWidget(self.toggleLine,        6, 2, 1, 2)
        layoutTop.addWidget(self.toggleColor,       7, 2, 1, 1)
        layoutTop.addWidget(self.comboBoxColor,     7, 3, 1, 1)
        layoutTop.addWidget(self.trianglePlot,      8, 2, 1, 2)
        layoutTop.addWidget(self.pushButtonPlot,   10, 0, 1, 4)
        self.selectWidget.setLayout(layoutTop)

        self.pushButtonRoots.hide()
        self.pushButtonAdd.hide()
        self.comboBoxParamTag.hide()
        self.comboBoxDataTag.hide()

        # Minimum size for initial resize of dock widget
        #self.selectWidget.setMinimumSize(250, 250)
        self.selectWidget.setMaximumSize(350, 800)

        self.dockTop.setWidget(self.selectWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockTop)

    def setIniFile(self, iniFile):
        self.iniFile = iniFile

    # slots for menu actions

    def export(self):
        filename, filt = QFileDialog.getSaveFileName(
            self, "Choose a file name", '.', "PDF (*.pdf)")
        if not filename: return
        filename = str(filename)
        if self.plotter:
            logging.debug("Saving PDF in file %s"%filename)
            self.plotter.export(filename)

    def script(self):
        filename, filt = QFileDialog.getSaveFileName(
            self, "Choose a file name", '.', "Python (*.py)")
        if not filename: return

    def showMargeStats(self):
        if self.plotter is None:
            self.statusBar().showMessage("No data available", 2000)
            return

        text = self.plotter.sampleAnalyser.getMargeStats()
        text = text.replace('\t', '\t\t') # uses double tab
        dlg = DialogMargeStats(self, text)
        dlg.exec_()

    def about(self):
        QMessageBox.about(
            self, "About GetDist GUI",
            "Qt application for GetDist plots.")

    def manageOtherRoots(self):
        dlg = DialogManageOtherRoots(self, self.other_roots)
        val = dlg.exec_()


    # slots for selectWidget

    def selectRootDir(self):
        """
        Slot function called when pushButtonSelect is pressed.
        """
	settings = QSettings('cosmomc', 'gui')
        last_dir = settings.value('lastSearchDirectory')

	# Search in current directory, if no previous path available
        if not last_dir: last_dir = os.getcwd()

        title = self.tr("Choose an existing case")
        dirName = QFileDialog.getExistingDirectory(
            self, title, last_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        dirName = str(dirName)

        if dirName:
            settings.setValue('lastSearchDirectory', dirName)

            # Grid chain
            filebatch = os.path.join(dirName, "batch.pyobj")
            if os.path.isfile(filebatch):
                self.rootdir = dirName
                self.lineEditDirectory.setText(self.rootdir)
                self.pushButtonRoots.hide()
                self.pushButtonAdd.hide()
                self._readGridChain(self.rootdir)
                return

            # Root directory
            self.rootdir = dirName
            self.lineEditDirectory.setText(self.rootdir)

            # File .paramnames
            filesparam = glob.glob(os.path.join(self.rootdir, "*.paramnames"))
            if len(filesparam)>1:
                fileparam, ok = QInputDialog.getItem(self, "Select file", "Param name:",
                                                     filesparam, 0, False)
                if ok and fileparam:
                    self.root = str(fileparam).replace(".paramnames", "")
                    logging.debug("self.root = %s"%self.root)
            else:
                # Root file name
                self.root = MCSamples.GetRootFileName(self.rootdir)

            chainFiles = MCSamples.GetChainFiles(self.root)
            if len(chainFiles)==0:
                logging.debug("No chain files in %s"%self.rootdir)
                self._updateComboBoxParamTag()
                self._updateComboBoxColor()
            else:

                self.statusBar().showMessage("Reading chain files in %s"%str(self.root))
                self.plotter = GetDistPlots.GetDistPlotter(
                    file_root=self.root, ini_file=self.iniFile)

                if filesparam:
                    # Directory contains file .paramnames
                    paramNames = self.plotter.sampleAnalyser.paramsForRoot(self.root).list()

                    # Hide combo boxes and fill list
                    self.comboBoxParamTag.hide()
                    self.comboBoxDataTag.hide()
                    self.pushButtonRoots.show()
                    self.pushButtonAdd.show()
                    self._updateListParametersX(paramNames)
                    self._updateListParametersY(paramNames)
                    self._updateComboBoxColor(paramNames)

                self.statusBar().showMessage("Ready", 2000)

        else:
            logging.debug("No directory specified")


    def _readGridChain(self, batchPath):
        logging.debug("Read grid chain in %s"%batchPath)
        batch = batchJob.readobject(batchPath)
        items = dict()
        for jobItem in batch.items(True, True):
            if jobItem.chainExists():
                if not jobItem.paramtag in items: items[jobItem.paramtag] = []
                items[jobItem.paramtag].append(jobItem)
        names = sorted(items.keys())
        self.comboBoxParamTag.show()
        self.comboBoxDataTag.show()
        self._updateComboBoxParamTag(names)


    def addRoot(self):

	settings = QSettings('cosmomc', 'gui')
        last_dir = settings.value('lastSearchDirectory')

	# Search in current directory, if no previous path available
        if not last_dir: last_dir = os.getcwd()

        filt = "Param names (*.paramnames)"
        title = self.tr("Choose a chain root")
        fileName, filt = QFileDialog.getOpenFileName(
            self, title, last_dir, filt)

        if fileName:
            dirName = os.path.dirname(fileName)
            settings.setValue('lastSearchDirectory', dirName)

            root = fileName.replace('.paramnames', '')

            baseName = os.path.basename(root)
            if not self.other_roots.has_key(baseName):
                logging.debug("Add root %s"%baseName)
                self.other_roots[baseName] = True

                if self.plotter is not None:
                    self.plotter.sampleAnalyser.addRoot(root)


    def _updateComboBoxParamTag(self, listOfParams=[]):
        if self.rootdir and os.path.isdir(self.rootdir):
            self.comboBoxParamTag.show()
            self.comboBoxParamTag.clear()
            if not listOfParams:
                listOfParams = [ d for d in os.listdir(self.rootdir)
                                 if os.path.isdir(os.path.join(self.rootdir, d)) ]
            self.comboBoxParamTag.addItems(listOfParams)

    def setParamTag(self, strParamTag):
        """
        Slot function called on change of comboBoxParamTag.
        """
        self.paramTag = str(strParamTag)
        paramDir = os.path.join(self.rootdir, self.paramTag)
        if os.path.isdir(paramDir):
            dirs = [ d for d in os.listdir(paramDir)
                     if os.path.isdir(os.path.join(paramDir, d)) ]
            self.comboBoxDataTag.addItems(dirs)

    def setDataTag(self, strDataTag):
        """
        Slot function called on change of comboBoxDataTag.
        """
        logging.debug("Data tag is %s"%strDataTag)


    def _updateListParametersX(self, items):
        """
        """
        logging.debug("Fill ListParametersX with %i items"%(len(items)))
        self.listParametersX.clear()
        for item in items:
            listItem = QListWidgetItem()
            listItem.setText(item)
            listItem.setFlags(listItem.flags() | Qt.ItemIsUserCheckable)
            listItem.setCheckState(Qt.Unchecked)
            self.listParametersX.addItem(listItem)

    def itemParamXChanged(self, item):
        """
        Slot function called when item in listParametersX changes.
        """
        if item.checkState()==Qt.Checked:
            logging.debug("Change of Item %s: now in check state"%str(item.text()))

    def _updateListParametersY(self, items):
        """
        """
        logging.debug("Fill ListParametersY with %i items"%(len(items)))
        self.listParametersY.clear()
        for item in items:
            listItem = QListWidgetItem()
            listItem.setText(item)
            listItem.setFlags(listItem.flags() | Qt.ItemIsUserCheckable)
            listItem.setCheckState(Qt.Unchecked)
            self.listParametersY.addItem(listItem)

    def itemParamYChanged(self, item):
        """
        Slot function called when item in listParametersY changes.
        """
        if item.checkState()==Qt.Checked:
            logging.debug("Change of Item %s: now in check state"%str(item.text()))

    def statusSelectAllX(self):
        """
        Slot function called when selectAllX is modified.
        """
        if self.selectAllX.isChecked():
            state = Qt.Checked
        else:
            state = Qt.Unchecked

        for i in range(self.listParametersX.count()):
            self.listParametersX.item(i).setCheckState(state)

    def statusSelectAllY(self):
        """
        Slot function called when selectAllY is modified.
        """
        if self.selectAllY.isChecked():
            state = Qt.Checked
        else:
            state = Qt.Unchecked

        for i in range(self.listParametersY.count()):
            self.listParametersY.item(i).setCheckState(state)

    def _updateComboBoxColor(self, listOfParams=[]):
        if self.rootdir and os.path.isdir(self.rootdir):
            self.comboBoxParamTag.clear()
            if not listOfParams:
                listOfParams = [ d for d in os.listdir(self.rootdir)
                                 if os.path.isdir(os.path.join(self.rootdir, d)) ]
            self.comboBoxColor.addItems(listOfParams)


    def plotData(self):
        """
        Slot function called when pushButtonPlot is pressed.
        """

        # X items
        items_x = []
        count = self.listParametersX.count()
        for i in range(count):
            item = self.listParametersX.item(i)
            if item.checkState()==Qt.Checked:
                items_x.append(str(item.text()))

        # X items
        items_y = []
        count = self.listParametersY.count()
        for i in range(count):
            item = self.listParametersY.item(i)
            if item.checkState()==Qt.Checked:
                items_y.append(str(item.text()))

        if self.plotter is None:
            logging.warning("No GetDistPlotter instance")
            return

        self.plotter.settings.setWithSubplotSize(3.000000)

        roots = []
        roots.append(os.path.basename(self.root))
        for other_root, state in self.other_roots.items():
            if state: roots.append(os.path.basename(other_root))
        logging.debug("Plotting with roots = %s"%str(roots))



        #
        if self.trianglePlot.isChecked():
            if len(items_x)>1:
                params = items_x
                logging.debug("Triangle plot ")
                logging.debug("roots  = %s"%str(roots))
                logging.debug("params = %s"%str(params))
                self.plotter.triangle_plot(roots, params)
                self.updatePlot()
            else:
                self.statusBar().showMessage("Need more than 1 x-param", 2000)

        elif len(items_x)>0 and len(items_y)==0:
            params = items_x
            logging.debug("1D plot")
            logging.debug("roots = %s"%str(roots))
            logging.debug("params = %s"%str(params))
            self.plotter.plots_1d(roots, params=params)
            self.updatePlot()

        elif len(items_x)>0 and len(items_y)>0:
            # only one X item selected
            if self.toggleFilled.isChecked() or self.toggleLine.isChecked():
                filled=self.toggleFilled.isChecked()
                logging.debug("2D plot ")
                logging.debug("roots  = %s"%str(roots))
                #
                pairs = []
                item_x = items_x[0]
                for item_y in items_y:
                    pairs.append([item_x, item_y])

                logging.debug("pairs  = %s"%str(pairs))
                self.plotter.plots_2d(roots, param_pairs=pairs, filled=filled)
                self.updatePlot()

            if self.toggleColor.isChecked():
                sets = []
                sets.append(items_x)
                x = items_x[0]
                y = items_y[0]
                color = str(self.comboBoxColor.currentText())
                logging.debug("3D plot")
                logging.debug("roots = %s"%str(roots))
                sets = [[x, y, color]]
                self.plotter.plots_3d(roots, sets)
                self.updatePlot()

    def updatePlot(self):

        if self.plotter.fig is None:
            logging.debug("Define an empty central widget")
            self.centralWidget = QWidget()
            self.setCentralWidget(self.centralWidget)

            #self.figure = None
            self.canvas = None
        else:
            logging.debug("Define new canvas in central widget")
            self.centralWidget = QWidget()
            self.setCentralWidget(self.centralWidget)

            self.canvas = FigureCanvas(self.plotter.fig)
            self.toolbar = NavigationToolbar(self.canvas, self)
            layout = QVBoxLayout()
            layout.addWidget(self.toolbar)
            layout.addWidget(self.canvas)
            self.centralWidget.setLayout(layout)

            self.canvas.draw()

# ==============================================================================

class DialogMargeStats(QDialog):

    def __init__(self, parent=None, text=""):
        QDialog.__init__(self, parent)

        self.textBrowser = QTextEdit(self)

        layout = QGridLayout()
        #layout.setColumnStretch(1, 1)
        #layout.setColumnMinimumWidth(1, 250)
        layout.addWidget(self.textBrowser, 0, 0)
        self.setLayout(layout)

        self.setWindowTitle(self.tr("Dialog for MargeStats"))

        if (text):
            self.textBrowser.setPlainText(text)
            self.textBrowser.setReadOnly(True)


# ==============================================================================

class DialogManageOtherRoots(QDialog):

    def __init__(self, parent, other_roots):
        QDialog.__init__(self, parent)
        self.parent = parent

        self.list = QListWidget(self)
        self.list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)

        self.pushButton = QPushButton(QIcon(":/images/file_remove.png"),
                                            "", self)
        self.pushButton.setToolTip("Remove a root directory")
        self.connect(self.pushButton, SIGNAL("clicked()"), self.removeRoot)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QGridLayout()
        layout.addWidget(self.list, 0, 0, 1, 4)
        layout.addWidget(self.pushButton, 1, 0, 1, 1)
        layout.addWidget(self.buttonBox, 2, 0, 1, 4)

        self.setLayout(layout)

        self.setWindowTitle(self.tr("Manage additional chain roots"))

        #
        for chain, state in other_roots.items():
            item = QListWidgetItem(self.list,)
            item.setText(str(chain))
            if state:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

    def removeRoot(self):
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.isSelected():
                root = str(item.text())
                logging.debug("Remove root %s"%root)
                self.parent.plotter.sampleAnalyser.removeRoot(root)
                self.list.takeItem(i)

    def accept(self):
        roots = {}
        for i in range(self.list.count()):
            item = self.list.item(i)
            root = str(item.text())
            state = (item.checkState()==Qt.Checked)
            roots[root] = state

        self.parent.other_roots = roots
        QDialog.accept(self)

# ==============================================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())

# ==============================================================================


