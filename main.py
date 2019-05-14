import sys
import os, platform
import io
from PyQt5 import QtWidgets, Qt, QtGui, QtCore, uic
from APIs import Kegg, SeqFromFasta
from bioservices import KEGG
from Bio import Entrez
from CoTargeting import CoTargeting

from Results import Results
from NewGenome import NewGenome
from multitargeting import Multitargeting
import requests
import GlobalSettings

from bs4 import BeautifulSoup


# =========================================================================================
# CLASS NAME: AnnotationsWindow
# Inputs: Greg: fill in this information
# Outputs: Greg: fill in this information
# =========================================================================================

class AnnotationsWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(AnnotationsWindow, self).__init__()
        uic.loadUi('Annotation Details.ui', self)
        self.setWindowIcon(QtGui.QIcon("cas9image.png"))
        self.Submit_button.clicked.connect(self.submit)
        self.Go_Back_Button.clicked.connect(self.go_Back)
        self.mainWindow=""

    def submit(self):
        self.mainWindow.collect_table_data()
        self.hide()
        self.mainWindow.show()

    def go_Back(self):
        self.tableWidget.clear()
        self.mainWindow.checkBoxes.clear()
        self.mainWindow.searches.clear()
        self.tableWidget.setColumnCount(0)
        self.mainWindow.show()
        self.hide()

    def fill_Table(self,mainWindow):

        self.mainWindow = mainWindow
        index = 0
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels("Description;Gene ID;Select".split(";"))

        mainWindow.checkBoxes = []
        for sValues in mainWindow.searches:
            for definition in mainWindow.searches[sValues]:
                index = index+1
                for gene in mainWindow.searches[sValues][definition]:
                    index = index+1
        self.tableWidget.setRowCount(index)
        if index == 0:
            return -1
        index= 0
        for sValues in mainWindow.searches:
            for definition in mainWindow.searches[sValues]:
                defin_obj = QtWidgets.QTableWidgetItem(definition)
                self.tableWidget.setItem(index,0,defin_obj)
                index+=1
                for gene in mainWindow.searches[sValues][definition]:
                    ckbox = QtWidgets.QCheckBox()
                    mainWindow.checkBoxes.append([definition + " " + gene])
                    mainWindow.checkBoxes[len(mainWindow.checkBoxes)-1].append(ckbox)
                    gene_obj = QtWidgets.QTableWidgetItem(gene)
                    self.tableWidget.setItem(index,1 , gene_obj)
                    self.tableWidget.setCellWidget(index, 2,ckbox)
                    index = index+1
        self.tableWidget.resizeColumnsToContents()
        if mainWindow.Show_All_Results.isChecked():
            mainWindow.hide()
            self.show()
        else:
            for obj in mainWindow.checkBoxes:
                obj[1].setChecked(True)
        return 0


# =========================================================================================
# CLASS NAME: CMainWindow
# Inputs: Takes in the path information from the startup window and also all input parameters
# that define the search for targets e.g. endonuclease, organism genome, gene target etc.
# Outputs: The results of the target search process by generating a new Results window
# =========================================================================================


class CMainWindow(QtWidgets.QMainWindow):
    def __init__(self,info_path):
        super(CMainWindow, self).__init__()
        uic.loadUi('CASPER_main.ui', self)
        self.dbpath = ""
        self.info_path = info_path
        self.data = {}
        self.TNumbers = {}
        self.shortHand ={}
        self.orgcodes = {}  # Stores the Kegg organism code by the format {full name : organism code}
        self.gene_list = {}
        self.searches = {}
        self.checkBoxes = []
        self.add_orgo = []
        self.checked_info = {}

        # --- Button Modifications --- #
        self.setWindowIcon(QtGui.QIcon("cas9image.png"))
        self.pushButton_FindTargets.clicked.connect(self.gather_settings)
        self.pushButton_ViewTargets.clicked.connect(self.view_results)
        self.pushButton_ViewTargets.setEnabled(False)
        self.radioButton_Gene.clicked.connect(self.toggle_annotation)
        self.radioButton_Position.clicked.connect(self.toggle_annotation)
        self.radioButton_Sequence.clicked.connect(self.toggle_annotation)
        self.Search_Button.clicked.connect(self.search_kegg_ncbi_browse_own)
        self.Annotation_Kegg.clicked.connect(self.change_annotation)
        self.Annotation_Ownfile.clicked.connect(self.change_annotation)
        self.NCBI_Select.clicked.connect(self.change_annotation)
        self.actionUpload_New_Genome.triggered.connect(self.launch_newGenome)
        self.actionCo_Targeting.triggered.connect(self.launch_CoTargeting)
        self.Add_Orgo_Button.clicked.connect(self.add_Orgo)
        self.Remove_Organism_Button.clicked.connect(self.remove_Orgo)
        self.endoChoice.currentIndexChanged.connect(self.endo_Changed)


        self.change_annotation()
        #self.test_button.clicked.connect(self.Ann_Window)

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.reset()
        self.Annotation_Window = AnnotationsWindow()

        #Hide Added orgo boxes
        self.Added_Org_Combo.hide()
        self.Remove_Organism_Button.hide()
        self.Added_Org_Label.hide()
        # --- Menubar commands --- #
        self.actionChange_Directory.triggered.connect(self.change_directory)
        # --- Setup for Gene Entry Field --- #
        self.geneEntryField.setPlainText("Example Inputs: \n"
                                               "Gene (LocusID): YOL086C  *for Saccharomyces Cerevisiae ADH1 gene* \n"
                                               "Position: (chromosome,start,stop)(chromosome,start,stop)...\n"
                                               "Sequence: *Pure sequence. CASPER will search for targets and report off"
                                               "targets based on the genome selected if any*")

        #self.Kegg_Search_Imput.setPlainText("test")
        #show functionalities on window
        ############################self.view_my_results = Results()
        self.newGenome = NewGenome(info_path)
        self.CoTargeting = CoTargeting(info_path)
        self.Results = Results()

    def endo_Changed(self):
        i=3
        self.add_orgo.clear()
        self.Add_Orgo_Combo.clear()
        self.Added_Org_Combo.clear()
        self.addOrgoCombo()
        self.Added_Org_Combo.hide()
        self.Added_Org_Label.hide()
        self.Remove_Organism_Button.hide()

    ####---FUNCTIONS TO RUN EACH BUTTON---####
    def remove_Orgo(self):
        self.add_orgo.remove(self.Added_Org_Combo.currentText())
        self.Add_Orgo_Combo.addItem(self.Added_Org_Combo.currentText())
        self.Added_Org_Combo.removeItem(self.Added_Org_Combo.currentIndex())
        if len(self.add_orgo)==0:
            self.Added_Org_Combo.hide()
            self.Added_Org_Label.hide()
            self.Remove_Organism_Button.hide()

    def add_Orgo(self):
        if self.Add_Orgo_Combo.currentText() == "Select Organism":
            QtWidgets.QMessageBox.question(self, "Must Select Organism",
                                           "You must select an Organism to add",
                                           QtWidgets.QMessageBox.Ok)
            return

        self.add_orgo.append(self.Add_Orgo_Combo.currentText())
        self.Added_Org_Combo.addItem(self.Add_Orgo_Combo.currentText())
        self.Add_Orgo_Combo.removeItem(self.Add_Orgo_Combo.currentIndex())
        self.Added_Org_Combo.show()
        self.Added_Org_Label.show()
        self.Remove_Organism_Button.show()

    # Function for collecting the settings from the input field and transferring them to run_results
    def gather_settings(self):
        inputstring = str(self.geneEntryField.toPlainText())
        self.progressBar.setValue(10)
        if self.radioButton_Gene.isChecked():
            ginput = inputstring.split(',')
            self.run_results("gene", ginput)
        elif self.radioButton_Position.isChecked():
            pinput = inputstring.split(';')
            self.run_results("position", pinput)
        elif self.radioButton_Sequence.isChecked():
            sinput = inputstring
            self.run_results("sequence", sinput)


# ---- Following functions are for running the auxillary algorithms and windows ---- #
    def run_results(self, inputtype, inputstring):
        kegginfo = Kegg()
        org = str(self.orgChoice.currentText())
        endo = str(self.endoChoice.currentText())
        progvalue = 15
        self.searches = {}
        self.gene_list = {}
        self.progressBar.setValue(progvalue)
        if inputtype == "gene":
            if self.Annotations_Organism.currentText() == "":
                error = QtWidgets.QMessageBox.question(self, "No Annotation", "You have not searched for an annotation "
                                                                            "yet, if you continue your organism will be"
                                                                            " searched in kegg and the first match"
                                                                            " will be used.\n\n"
                                                                            "Do you wish to continue?"
                                                                            , QtWidgets.QMessageBox.Yes |
                                                                            QtWidgets.QMessageBox.No,
                                                                            QtWidgets.QMessageBox.No)
                if error == QtWidgets.QMessageBox.No:
                    self.progressBar.setValue(0)
                    return
                else:
                    self.search_kegg()
            self.make_dictonary()
            list_sVal = self.separate_line(inputstring[0])
            for sValue in list_sVal:
                sValue = self.removeWhiteSpace(sValue)
                if len(sValue) == 0:
                    continue
                self.searches[sValue] = {}
                for defin in self.gene_list:
                    if sValue in defin or (sValue in self.gene_list[defin]):
                        if defin in self.searches[sValue]:
                            if self.gene_list[defin] not in self.searches[sValue][defin]:
                                self.searches[sValue][defin].append(self.gene_list[defin])
                        else:
                            self.searches[sValue][defin] = self.gene_list[defin]
                        #print(self.searches[sValue][defin][0])
            did_work = self.Annotation_Window.fill_Table(self)
            if did_work == -1:
                QtWidgets.QMessageBox.question(self, "Gene Database Error",
                                               "The Gene you entered could not be found in the Kegg database. "
                                               "Please make sure you entered everything correctly and try again.",
                                               QtWidgets.QMessageBox.Ok)
                self.progressBar.setValue(0)
        if inputtype == "position":
            ginfo = inputstring[1:-1].split(",")
            self.progressBar.setValue(45)
        if inputtype == "sequence":
            self.progressBar.setValue(45)
        self.progressBar.setValue(100)
        # For processing the gene sequence from a specified fasta file.
        """s = SeqFromFasta()
        filename = self.dbpath + org + ".fna"
        s.setfilename(filename)
        progvalue = 75
        self.progressBar.setValue(progvalue)
        for gene in inputstring:
            s.getsequenceandtargets(ginfo[gene], 100, 100, self.dbpath+'/'+org, endo)
            progvalue += 25/len(inputstring)
            self.progressBar.setValue(progvalue)
            self.view_my_results.loadGenesandTargets(s.getgenesequence(), ginfo[gene][2]+100, ginfo[gene][3]-100,
                                                     s.gettargets(), gene)
        self.progressBar.setValue(100)



        self.pushButton_ViewTargets.setEnabled(True)"""

    def launch_newGenome(self):
       self.newGenome.show()

    def collect_table_data(self):
        self.checked_info.clear()

        k = Kegg()
        full_org = str(self.orgChoice.currentText())
        organism= self.shortHand[full_org]
        nameFull = ""
        holder = ()
        for item in self.checkBoxes:
            if item[1].isChecked() ==True:
                nameFull = item[0].split(" ")
                name  = nameFull[len(nameFull)-1]

                gene_info = k.gene_locator(organism+":"+name)
                print(gene_info)
                holder = (gene_info[0],gene_info[2],gene_info[3])
                self.checked_info[item[0]]=holder

        self.Results.transfer_data(organism,str(self.endoChoice.currentText()),os.getcwd(),self.checked_info,"")
        self.pushButton_ViewTargets.setEnabled(True)


    def launch_CoTargeting(self):
        self.CoTargeting.launch(self.data,self.dbpath,self.shortHand)
        self.hide()

# ------------------------------------------------------------------------------------------------------ #

# ----- Following Code is helper functions for processing input data ----- #
    def separate_line(self, input_string):
        export_array = []
        while True:
            index = input_string.find('\n')
            if index==-1:
                if len(input_string)==0:
                    return export_array
                else:
                    export_array.append(input_string)
                    return export_array
            export_array.append(input_string[:index])
            input_string= input_string[index+1:]

    def removeWhiteSpace(self, strng):
        while True:
            if len(strng)==0 or (strng[0] != " " and strng[0]!="\n"):
                break
            strng = strng[1:]
        while True:
            if len(strng)==0 or (strng[len(strng)-1]!=" " and strng[0]!="\n"):
                return strng
            strng = strng[:len(strng)-1]

    # Function to enable and disable the Annotation function if searching by position or sequence
    def toggle_annotation(self):
        if self.radioButton_Gene.isChecked():
            s = True
        else:
            s = False
        current = self.selected_annotation()
        if current == "Own":
            self.Search_Button.setText("Browse")
            self.Search_Button.setEnabled(s)
            self.Search_Input.setEnabled(s)
            self.Search_Label.setText("Select an annotation file...")
        elif current == "Kegg":
            self.Search_Button.setText("Search")
            self.Search_Button.setEnabled(s)
            self.Search_Input.setEnabled(s)
            self.Search_Label.setText("Search KEGG Database for genes")
        else:
            self.Search_Button.setText("Search")
            self.Search_Button.setEnabled(s)
            self.Search_Input.setEnabled(s)
            self.Search_Label.setText("Search NCBI Database for genes")
        self.Annotations_Organism.setEnabled(s)
        self.Annotation_Ownfile.setEnabled(s)
        self.Annotation_Kegg.setEnabled(s)
        self.NCBI_Select.setEnabled(s)

    def selected_annotation(self):
        if self.Annotation_Ownfile.isChecked():
            return "Own"
        elif self.Annotation_Kegg.isChecked():
            return "Kegg"
        else:
            return "NCBI"

    def change_annotation(self):
        if self.Annotation_Ownfile.isChecked():
            self.Search_Button.setText("Browse")
            self.Search_Label.setText("Select an annotation file...")
        elif self.Annotation_Kegg.isChecked():
            self.Search_Button.setText("Search")
            self.Search_Label.setText("Search KEGG Database for genome annotation")
        elif self.NCBI_Select.isChecked():
            self.Search_Button.setText("Search")
            self.Search_Label.setText("Search NCBI Database for genome annotation")



    # This function works as a way to look up a search term in the Kegg database to potentially get the code
    # for the gene


    def search_kegg_ncbi_browse_own(self):
        if self.Annotation_Ownfile.isChecked():
            poo = 1
            #Open file browser
        elif self.Annotation_Kegg.isChecked():
            k = KEGG()

            All_org = k.lookfor_organism(self.Search_Input.text())
            """ self.lineEdit_search.text()"""
            for item in All_org:
                hold = self.organism_finder(item)
                self.Annotations_Organism.addItem(hold)
                self.TNumbers[hold] = item[:6]
        elif self.NCBI_Select.isChecked():
            poo = 1
            #Connect to NCBI database

    def make_dictonary(self):
        url = "https://www.genome.jp/dbget-bin/get_linkdb?-t+genes+gn:"+self.TNumbers[self.Annotations_Organism.currentText()]
        source_code = requests.get(url)
        plain_text = source_code.text
        buf = io.StringIO(plain_text)

        while True:
            line = buf.readline()
            if line[0] == "-":
                break
        while True:
            line = buf.readline()
            if line[1] != "a":
                return
            line = line[line.find(">")+1:]
            seq = line[line.find(":")+1:line.find("<")]
            line = line[line.find(">")+1:]

            i =0
            while True:
                if line[i] == " ":
                    i = i+1
                else:
                    break
            key = line[i:line.find("\n") - 1]
            if key in self.gene_list:
                if seq not in self.gene_list[key]:
                    self.gene_list[key].append(seq)
            else:
                self.gene_list[key] = [seq]
            z=5

    def organism_finder(self, long_str):
        semi = long_str.find(";")
        index =1
        while True:
            if long_str[semi-index] == " ":
                break
            index = index+1
        return long_str[:semi-index]

    def search_own_file(self):
        print("searching for own file")

    # This method is for testing the execution of a button call to make sure the button is linked properly
    def testexe(self):
        choice = QtWidgets.QMessageBox.question(self, "Extract!", "Are you sure you want to Quit?",
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            print(self.orgChoice.currentText())
            sys.exit()
        else:
            pass

    # This method checks if a check button or radio button works appropriately by printing the current organism
    def testcheckandradio(self):
         print(str(self.orgChoice.currentText()))

    def addOrgoCombo(self):
        self.Add_Orgo_Combo.addItem("Select Organism")
        for item in self.data:
            if (self.endoChoice.currentText() in self.data[item]) and (item != str(self.orgChoice.currentText())):
                self.Add_Orgo_Combo.addItem(item)

    def addOrgoCombo(self):
        self.Add_Orgo_Combo.addItem("Select Organism")
        for item in self.data:
            if (self.endoChoice.currentText() in self.data[item]) and (item != str(self.orgChoice.currentText())):
                self.Add_Orgo_Combo.addItem(item)

    # ----- CALLED IN STARTUP WINDOW ------ #
    def getData(self):
        mypath = os.getcwd()
        found = False;
        self.dbpath = mypath
        onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
        orgsandendos = {}
        shortName = {}
        for file in onlyfiles:
            if file.find('.cspr')!=-1:
                found=True;
                newname = file[0:-4]
                s = newname.split('_')
                hold = open(file)
                buf = (hold.readline())
                species = buf[8:buf.find('\n')]
                endo = str(s[1][:len(s[1])-1])
                if species not in shortName:
                    shortName[species] = s[0]
                if species in orgsandendos:
                    orgsandendos[species].append(endo)
                else:
                    orgsandendos[species] =[endo]
                    self.orgChoice.addItem(species)

        if found==False:
            return False
        self.data = orgsandendos
        self.shortHand= shortName
        self.endoChoice.addItems(self.data[str(self.orgChoice.currentText())])
        self.orgChoice.currentIndexChanged.connect(self.changeEndos)

    def changeEndos(self):

        self.endoChoice.clear()
        self.endoChoice.addItems(self.data[str(self.orgChoice.currentText())])
        self.Search_Input.setText(self.orgChoice.currentText())

    def change_directory(self):
        filed = QtWidgets.QFileDialog()
        mydir = QtWidgets.QFileDialog.getExistingDirectory(filed, "Open a Folder",
                                                           self.dbpath, QtWidgets.QFileDialog.ShowDirsOnly)
        os.chdir(mydir)
        self.getData()

    @QtCore.pyqtSlot()
    def view_results(self):
        self.hide()
        self.Results.show()



# ----------------------------------------------------------------------------------------------------- #
# =========================================================================================
# CLASS NAME: StartupWindow
# Inputs: Takes information from the main application window and displays the gRNA results
# Outputs: The display of the gRNA results search
# =========================================================================================



class StartupWindow(QtWidgets.QDialog):
    def __init__(self):
        super(StartupWindow, self).__init__()
        uic.loadUi('startupCASPER.ui', self)
        self.setWindowTitle('WELCOME TO CASPER!')
        self.setWindowModality(2)  # sets the modality of the window to Application Modal
        #self.make_window = annotations_Window()
        #---Button Modifications---#
        self.setWindowIcon(QtGui.QIcon("cas9image.png"))
        pixmap = QtGui.QPixmap('mainart.jpg')
        self.labelforart.setPixmap(pixmap)
        self.pushButton_2.setDefault(True)
        # Check to see the operating system you are on and change this in Global Settings:
        GlobalSettings.OPERATING_SYSTEM_ID = platform.system()
        self.info_path = os.getcwd()
        self.gdirectory = self.check_dir()
        GlobalSettings.CSPR_DB = self.gdirectory

        self.lineEdit.setText(self.gdirectory)

        self.pushButton_3.clicked.connect(self.changeDir)
        self.pushButton_2.clicked.connect(self.show_window)
        self.pushButton.clicked.connect(self.errormsgmulti)
        self.multi_targeting_window = Multitargeting("hold")
        GlobalSettings.mainWindow = CMainWindow(self.info_path)

        #show functionalities on window
        self.show()

    ####---FUNCTIONS TO RUN EACH BUTTON---####
    def changeDir(self):
        filed = QtWidgets.QFileDialog()
        mydir = QtWidgets.QFileDialog.getExistingDirectory(filed, "Open a Folder",
                                                       self.gdirectory, QtWidgets.QFileDialog.ShowDirsOnly)
        if mydir == "":
            return

        self.lineEdit.setText(mydir)
        cdir = self.lineEdit.text()
        self.gdirectory = mydir
        GlobalSettings.CSPR_DB = cdir
        print(mydir)
        print(cdir)




    def errormsgmulti(self):
            self.gdirectory = str(self.lineEdit.text())
            print(self.gdirectory)
            if "Please select a directory that contains .capr files" in self.gdirectory:
                QtWidgets.QMessageBox.question(self, "Must select directory", "You must select your directory",
                                               QtWidgets.QMessageBox.Ok)
            elif (os.path.isdir(self.gdirectory)):
                os.chdir(self.gdirectory)
                self.multi_targeting_window.launch(self.gdirectory)
                self.close()
            else:
                QtWidgets.QMessageBox.question(self, "Not a directory", "The directory you selected does not exist.",
                                                                                    QtWidgets.QMessageBox.Ok)
    def check_dir(self):
        if GlobalSettings.OPERATING_SYSTEM_ID == "Windows":
            cspr_info = open(self.info_path+"\\CASPERinfo",'r+')
        else:
            cspr_info = open(self.info_path+"/CASPERinfo", 'r+')
        cspr_info = cspr_info.read()
        lines = cspr_info.split('\n')
        line = ""
        for item in lines:
            if 'DIRECTORY:' in item:
                line = item
                break
        if len(line)<11:
            return os.path.expanduser("~\Documents").replace('\\','/')
        else:
            return line[10:]

    def re_write_dir(self):
        if GlobalSettings.OPERATING_SYSTEM_ID == "Windows":
            cspr_info = open(self.info_path+"\\CASPERinfo",'r+')
        else:
            cspr_info = open(self.info_path+"/CASPERinfo", 'r+')
        cspr_info_text = cspr_info.read()
        cspr_info_text = cspr_info_text.split('\n')
        full_doc = ""
        for item in cspr_info_text:
            if 'DIRECTORY:' in item:
                line = item
                break
        line_final  = "DIRECTORY:"+self.gdirectory
        for item in cspr_info_text:
            if item == line:
                full_doc= full_doc+"\n"+line_final
            else:
                full_doc = full_doc+"\n" + item
        full_doc = full_doc[1:]
        cspr_info.close()
        if GlobalSettings.OPERATING_SYSTEM_ID == "Windows":
            cspr_info = open(self.info_path+"\\CASPERinfo",'w+')
        else:
            cspr_info = open(self.info_path+"/CASPERinfo", 'w+')
        cspr_info.write(full_doc)

        cspr_info.close()

    def show_window(self):

        self.gdirectory = str(self.lineEdit.text())
        print(self.gdirectory)
        if "Please select a directory that contains .capr files" in self.gdirectory:
            QtWidgets.QMessageBox.question(self, "Must select directory", "You must select your directory",
                                                                                      QtWidgets.QMessageBox.Ok)
        elif(os.path.isdir(self.gdirectory)):

            os.chdir(self.gdirectory)
            found = GlobalSettings.mainWindow.getData()
            if found==False:
                QtWidgets.QMessageBox.question(self, "No Cspr files", "Please select a directory that contains cspr files.",
                                               QtWidgets.QMessageBox.Ok)
                return

            self.re_write_dir()
            GlobalSettings.CASPER_FOLDER_LOCATION = self.info_path
            GlobalSettings.mainWindow.show()
            self.close()
        else:
            QtWidgets.QMessageBox.question(self, "Not a directory", "The directory you selected does not exist.",
                                                                                      QtWidgets.QMessageBox.Ok)




if __name__ == '__main__':
    #enable DPI scaling
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    app = Qt.QApplication(sys.argv)
    app.setOrganizationName("TrinhLab-UTK")
    app.setApplicationName("CASPER")
    startup = StartupWindow()
    sys.exit(app.exec_())
