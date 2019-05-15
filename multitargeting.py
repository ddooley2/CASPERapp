"""This file is for generating data on multitargeting from a CASPER_Seq_Finder file.  It will simply decompress and
    print out in the command line in readable format the repeated sequences found in the organsim with the given
    endonuclease. Before doing anything, change the path object below to the appropriate path."""

# Please insert the appropriate path where you are storing your CASPER_Seq_Finder files

import operator
import sys
import os



import io
import pyqtgraph as pg
from PyQt5.QtChart import (QBarCategoryAxis,QBarSet, QChartView, QBarSeries,QChart,QLineSeries)


from Algorithms import SeqTranslate
from PyQt5 import QtWidgets, Qt, QtGui, QtCore, uic





# ----------------------------------CODE BELOW CAN BE IGNORED BY USER------------------------------------------------ #


class Multitargeting(QtWidgets.QMainWindow):

    BAD_instances = {}
    sorted_instances = []

    def __init__(self,path, parent = None):

        super(Multitargeting, self).__init__()
        uic.loadUi('multitargetingwindow.ui', self)
        self.setWindowIcon(QtGui.QIcon("cas9image.png"))
        #self.show()
        self.repeats = {}
        #self.cursor = Qt.Cursor()
        self.sq=SeqTranslate()
        self.seeds = {}
        self.chart_view_chro_bar=QChartView()
        self.chart_view_repeat_bar = QChartView()
        self.chart_view_repeat_line = QChartView()
        self.seqTrans = SeqTranslate()
        self.data = ""
        self.shortHand =""
        self.chromo_length = [-1]
        self.layout_chromo_bar = QtGui.QGridLayout()
        self.layout_repeat_bar = QtGui.QGridLayout()
        self.layout_repeat_line = QtGui.QGridLayout()
        self.bar_graph_chro.setLayout(self.layout_chromo_bar)
        self.Bar_Graph_1.setLayout(self.layout_repeat_bar)
        self.LineGraph.setLayout(self.layout_repeat_line)
        self.max_chromo.currentIndexChanged.connect(self.fill_seed_id_chrom)
        self.min_chromo.currentIndexChanged.connect(self.fill_seed_id_chrom)
        self.chromo_seed.currentIndexChanged.connect(self.chro_bar_data)
        self.Analyze_Button.clicked.connect(self.make_graphs)
        self.max_repeats=1
        self.average = 0
        self.median = 0
        self.mode = 0
        self.average_unique = 0
        self.average_rep = 0


        self.ready_chromo_min_max = True
        self.ready_chromo_make_graph = True
        self.directory = 'C:/Users/GregCantrall/Documents/Cspr files'
        #self.parse_repeates("10001\nchr1,pos1,seq1,scr1\tchr2,pos2,seq2,scr2\n10002\nchr1,pos1,seq1,scr1\tchr2,pos2,seq2,scr2\tchr3,pos3,seq3,scr3\n")
        #self.make_graphs(self.get_file_info("sce_asCpf1"))

        """self.file_name = CASPER_Seq_Finder_file
        self.get_instances()"""

    def launch(self,path):


        self.directory = path
        self.get_data()
        self.make_graphs()
        self.show()
        self.chromo_length = [-1]

    def get_data(self):
        onlyfiles = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
        print(onlyfiles)
        orgsandendos = {}
        shortName = {}
        for file in onlyfiles:
            if file.find('.cspr')!=-1:
                newname = file[0:-4]
                s = newname.split('_')
                hold = open(file)
                buf = (hold.readline())
                species = buf[8:buf.find('\n')]
                endo = str(s[1])
                if species not in shortName:
                    shortName[species] = s[0]
                if species in orgsandendos:
                    orgsandendos[species].append(endo)
                else:
                    orgsandendos[species] =[endo]
                    self.organism_drop.addItem(species)
        self.data = orgsandendos
        self.shortHand = shortName
        self.endo_drop.addItems(self.data[str(self.organism_drop.currentText())])
        self.organism_drop.currentIndexChanged.connect(self.changeEndos)

    def changeEndos(self):
        self.endo_drop.clear()
        self.endo_drop.addItems(self.data[str(self.organism_drop.currentText())])



    def make_graphs(self):
        file = self.get_file_info()
        split_info = file.split("\n")
        index = 0
        sum = 0
        count = 0

        self.repeats.clear()
        self.seeds.clear()
        while True:
            if split_info[index] == "REPEATS":
                index = index + 1
                break
            index = index + 1
        while index+1<len(split_info):
            seed = self.seqTrans.decompress64(split_info[index])
            repeat = split_info[index+1].split("\t")
            self.repeats[seed] =0
            self.seeds[seed] = []
            for item in repeat:
                if item !="":
                    self.repeats[seed] +=1
                    sequence = item.split(",")
                    self.seeds[seed].append(sequence)
                    sum += self.sq.decompress64(sequence[3])
                    count += 1
            index +=2
        self.average_rep = sum/count
        self.plot_repeats_vs_seeds()
        self.seeds_vs_repeats_bar()
        self.fill_min_max()
        #self.chro_bar_data()
        self.nbr_seq.setText(str(len(self.seeds)))
        self.avg_rep.setText(str(self.average))
        self.med_rep.setText(str(self.median))
        self.mode_rep.setText(str(self.mode))
        self.scr_lbl.setText(str(self.average_rep/self.average_unique))


    def get_chromo_length(self):
        file_info = self.get_file_info()
        lines = file_info.split("\n")
        holder= 0
        sum = 0
        prev_line = ""
        for line in lines:
            if line.startswith(">") or "GENOME:" in line:
                continue
            if line.startswith(">"):
                if prev_line == "CHROMO":
                    self.chromo_length.append(-2)
                    continue
                self.chromo_length.append(self.seqTrans.decompress64(prev_line.split(",")[0]))
                prev_line = "CHROMO"
                continue
            if "REPEAT" in line:
                self.chromo_length.append(self.seqTrans.decompress64(prev_line.split(",")[0]))
                break
            holder += 1

            mytuple = line.split(",")
            hold = self.sq.decompress64(mytuple[2])
            sum+=hold
            prev_line = line
        self.average_unique = sum/holder
        self.nbr_unq.setText(str(holder))

    def get_file_info(self):
        file_name = self.shortHand[self.organism_drop.currentText()]+"_"+self.endo_drop.currentText()
        if self.directory.find("/") != -1:
            file = open(self.directory+"/"+file_name+"cspr")
        else:
            file = open(self.directory + "\\" + file_name + "cspr")
        return file.read()


    def parse_repeates(self, uncomp):
        split_info = uncomp.split("\n")
        index = 0
        while index+1<len(split_info):
            seed = split_info[index]
            repeat = split_info[index+1].split("\t")
            self.seeds[seed] =[]
            for item in repeat:
                self.seeds[seed].append(item.split(","))
            index +=2




    def chro_bar_data(self):
        if self.ready_chromo_make_graph==False:
            return
        dic_info = {}
        for seed in self.seeds:
            dic_info[seed] = {}
            for repeat in self.seeds[seed]:
                if repeat[0] in dic_info[seed]:
                    dic_info[seed][repeat[0]].append(self.seqTrans.decompress64(repeat[1]))
                else:
                    dic_info[seed][repeat[0]]=[self.seqTrans.decompress64(repeat[1])]
        self.chro_bar_create(dic_info)
        self.get_chromo_length()
        self.fill_Chromo_Text(dic_info)
    def chromo_length_helper(self,chromo,info):
        max = 0;
        for position in info[self.sq.decompress64(self.chromo_seed.currentText())][chromo]:
            if int(position)>max:
                max = int(position);
        self.chromo_length[chromo] = max;

    def fill_Chromo_Text(self, info):
        chromo_pos = {}
        for chromo in info[self.sq.decompress64(self.chromo_seed.currentText())]:
            pos = []

            if chromo == "-1":
                continue
            if self.chromo_length[int(chromo)]=="-2":
                chromo = self.chromo_length_helper(chromo, info)
            for position in info[self.sq.decompress64(self.chromo_seed.currentText())][chromo]:

                pos_space = int(round(((position/self.chromo_length[int(chromo)])*100)/1.3157))
                pos.append(pos_space)
            chromo_pos[chromo] = pos

        self.GeneText.find("3")
        black = Qt.QColor('black')
        white = Qt.QColor("white")
        green = Qt.QColor('green')

        self.GeneText.setTextBackgroundColor(black)
        self.GeneText.setTextColor(black)
        self.GeneText.append("testing")
        self.GeneText.clear()
        index = 0

        for chromo in chromo_pos:
            self.GeneText.setTextBackgroundColor(black)
            self.GeneText.setTextColor(black)
            index = 0

            while index<90:

                self.GeneText.insertPlainText("0")
                index+=1

            self.GeneText.insertPlainText("\n000")
            self.GeneText.setTextColor(white)
            self.GeneText.insertPlainText(chromo)
            self.GeneText.setTextColor(black)
            index=len(chromo)
            while index<3:
                self.GeneText.insertPlainText("0")
                index+=1
            index=0
            self.GeneText.setTextColor(white)
            self.GeneText.setTextBackgroundColor(white)
            while index<78:
                if index in chromo_pos[chromo]:
                    self.GeneText.setTextColor(green)
                    self.GeneText.setTextBackgroundColor(green)
                    self.GeneText.insertPlainText("0")
                    self.GeneText.setTextColor(white)
                    self.GeneText.setTextBackgroundColor(white)
                    index+=1
                    continue
                self.GeneText.insertPlainText("0")
                index+=1
            self.GeneText.setTextBackgroundColor(black)
            self.GeneText.setTextColor(black)
            self.GeneText.insertPlainText("000000\n")
        x=2
        index = 0
        while index < 90:
            self.GeneText.insertPlainText("0")
            index += 1

    def chro_bar_create(self,info):
        x_Vals = QBarSeries()
        Axes = []
        holder = QBarSet("test")
        for chromo in info[self.sq.decompress64(self.chromo_seed.currentText())]:

            holder.append(len(info[self.sq.decompress64(self.chromo_seed.currentText())][chromo]))
            Axes.append(chromo)
            x_Vals.append(holder)
        chart  = QChart()
        chart.addSeries(x_Vals)
        chart.legend().hide()
        Full_Axes = QBarCategoryAxis()
        Full_Axes.append(Axes)
        chart.createDefaultAxes()
        chart.setAxisX(Full_Axes,x_Vals)
        chartView = QChartView()
        chartView.setChart(chart)
        self.layout_chromo_bar.addWidget(chartView,0,1)
        self.chart_view_chro_bar = chartView


    def seeds_vs_repeats_bar(self):
        data = {}
        self.average = 0
        for seed in self.repeats:
            self.average  += int(self.repeats[seed])
            number = self.repeats[seed]
            if number in data:
                data[number]+=1
            else:
                data[number] =1
        data = self.order_high_low_rep(data)
        self.average = round(self.average/(len(self.repeats)))
        x_Vals = QBarSeries()
        Axes = []
        holder = QBarSet("test")
        max = 0
        for number in data:
            #holder = QBarSet(str(number))
            if data[number]>max:
                max = data[number]
            if (data[number]/max)>.01:
                holder.append(data[number])
                Axes.append(str(int(number)))
                x_Vals.append(holder)
        chart  = QChart()
        chart.addSeries(x_Vals)
        chart.legend().hide()
        Full_Axes = QBarCategoryAxis()
        Full_Axes.append(Axes)
        chart.createDefaultAxes()
        chart.setAxisX(Full_Axes,x_Vals)
        chartView = QChartView()
        chartView.setChart(chart)
        self.layout_repeat_bar.addWidget(chartView,0,1)
        self.chart_view_repeat_bar = chartView


    def plot_repeats_vs_seeds(self):
        data = {}
        for seed in self.repeats:
            number = self.repeats[seed]
            if number in data:
                data[number]+=1
            else:
                data[number] =1

        max = 0



        y=[]
        axisy = 0
        while axisy<self.max_repeats:
            y.append(str(axisy))
            axisy+=1
        series = QLineSeries()
        index = 0
        time = 0
        for number in self.order(data):
            time+=1

            if int(data[number]) >max:
                max = int(data[number])
                self.mode = number

            hold = 0
            while hold<data[number]:
                if index == int(round(len(self.repeats) / 2)):
                    self.median = number
                series.append(index,number)
                index= index+1
                hold +=1
        Full_Axes = QBarCategoryAxis()
        Full_Axes.append(y)
        chart = QChart()
        chartView = QChartView()
        chart.addSeries(series)
        chart.legend().hide()
        chart.setAxisY(Full_Axes)
        chart.createDefaultAxes()
        chartView.setChart(chart)

        self.layout_repeat_line.addWidget(chartView, 0, 1)
        self.chart_view_repeat_plot = chartView
        """plot = pg.PlotWidget()
        plot.plot(xb,y,title="Number of Repeats Vs. Seed Id's")
        layout = QtGui.QGridLayout()
        self.LineGraph.setLayout(layout)
        layout.addWidget(plot,0,1)"""

    def fill_min_max(self,run_seed_fill=True):
        self.ready_chromo_min_max = False
        index =1
        self.max_chromo.clear()
        self.min_chromo.clear()
        while index<self.max_repeats+1:
            self.min_chromo.addItem(str(index))
            self.max_chromo.addItem(str(self.max_repeats+1-index))
            index+=1
        self.ready_chromo_min_max = True
        if run_seed_fill:
            self.fill_seed_id_chrom()


    def fill_seed_id_chrom(self):
        if self.ready_chromo_min_max==False:
            return
        if int(self.min_chromo.currentText())>int(self.max_chromo.currentText()):
            self.ready_chromo_min_max=False
            self.max_chromo.clear()
            self.min_chromo.clear()
            self.ready_chromo_min_max = True
            self.fill_min_max(False)
            QtWidgets.QMessageBox.question(self, "Maximum cant be less than Minimum",
                                           "The Minimum number of repeats cant be more than the Maximum",
                                           QtWidgets.QMessageBox.Ok)
            self.fill_seed_id_chrom()
            return
        self.ready_chromo_make_graph = False
        self.chromo_seed.clear()
        any = False
        for seed in self.repeats:
            if self.repeats[seed] >= int(self.min_chromo.currentText()) and self.repeats[seed]<=int(self.max_chromo.currentText()):
                any = True
                self.chromo_seed.addItem(str(self.sq.compress(seed,64)))
        if any==False:
            QtWidgets.QMessageBox.question(self, "No matches found",
                                           "No seed that is within the specifications could be found",
                                           QtWidgets.QMessageBox.Ok)
            self.ready_chromo_min_max = False
            self.max_chromo.clear()
            self.min_chromo.clear()
            self.ready_chromo_min_max = True
            self.fill_min_max(False)
            self.fill_seed_id_chrom()
            return
        self.ready_chromo_make_graph=True
        self.chro_bar_data()


    def order(self,data_par):
        data = dict(data_par)
        data2  = []
        while len(data)>0:
            max=0
            for item in data:
                if item>max:
                    max=item
            data2.append(max)
            if len(data2) ==1:
                self.max_repeats =max
            del data[max]
        return data2


    def order_high_low_rep(self,dictionary):
        data = dict(dictionary)
        data_ordered = {}
        while len(data)>0:
            max=0
            max_index=0
            for item in data:

                if data[item]>max:
                    max_index=item
                    max = data[item]

            data_ordered[max_index] = max

            del data[max_index]
        return data_ordered






    def get_instances(self):
            ST = SeqTranslate()
            os.chdir(path)
            f = open(self.file_name, 'r')
            while True:
                x = f.readline()
                if x == 'REPEATS\n':
                    print("reached repeat sequences")
                    break
            while True:
                t = f.readline()
                if t == 'END_OF_FILE':
                    print("reached end of repeat sequences")
                    break
                ukey = t[:-1]  # takes away the "\n" in the string
                key = ST.decompress64(ukey, True)
                key = ST.fill_As(key, 16)
                self.BAD_instances[key] = list()
                # Add sequences and locations to the list
                v = f.readline().split('\t')[:-1]
                for item in v:
                    loctup = item.split(',')
                    chrom = loctup[0]
                    location = ST.decompress64(loctup[1])
                    seq = ST.decompress64(loctup[2][1:],True)
                    seq = ST.fill_As(seq, 4)  # when A's get lost in the compression this fills them back in
                    mytup = (chrom, location, seq)
                    self.BAD_instances[key].append(mytup)
            f.close()
            print("currently sorting")
            for key in self.BAD_instances:
                size = len(self.BAD_instances[key])
                newtuple = (key, self.BAD_instances[key], size)  # sequence, location, size
                self.sorted_instances.append(newtuple)

    # Returns the container self.sorted_instances but removes all "single" repeats. Old Code to fix an off-by-1 error
    def return_all_seqs(self):
        myseqs = []
        for instance in self.sorted_instances:
            if instance[2] > 1:
                myseqs.append(instance)
        return myseqs

    def return_sorted(self):
        sorted_seqs = sorted(self.sorted_instances, key=operator.itemgetter(2), reverse=True)
        amounts = {}
        for instance in sorted_seqs:
            if instance[2] > 1:
                if instance[2] in amounts:
                    amounts[instance[2]] += 1
                else:
                    amounts[instance[2]] = 1
                print(str(instance[0]) + "," + str(instance[2]) + "," + str(instance[1]))
        for element in amounts:
            print("Number of seed sequences with " + str(element) + " appearances: " + str(amounts[element]))

    def return_positions(self):
        positions_mapped = []  # chromosme, beginning of range, end of range, and number of hits
        for instance in self.sorted_instances:
            if instance[2] > 1:
                for pos in instance[1]:
                    chrom = pos[0]
                    loc = int(pos[1])
                    # check to see if its already in the map
                    need_new = True
                    for position in positions_mapped:
                        if chrom == position[0]:
                            if position[1] < loc < position[2]:
                                position[3] += 1
                                position[4].append(instance[0])
                                need_new = False
                                print("position added")
                    if need_new:
                        newtuple = [chrom, loc-1000, loc+1000, 1, [" ", instance[0]]]
                        positions_mapped.append(newtuple)
        sorted_positions = sorted(positions_mapped, key=operator.itemgetter(3), reverse=True)
        for element in sorted_positions:
            print(str(element[0]) + "," + str(element[1]) + "," + str(element[2]) + "," + str(element[3]))
        for element in sorted_positions:
            sequences = ""
            for sequence in element[4]:
                sequences += sequence + ","
            print(sequences)
        return sorted_positions

    def int_to_char(self, i):
        switcher = {
            0: 'A',
            1: 'T',
            2: 'C',
            3: 'G'
        }
        return switcher[i]

#r = Multitargeting()
#r.return_sorted()
#r.return_positions()
