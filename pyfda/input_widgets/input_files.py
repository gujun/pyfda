# -*- coding: utf-8 -*-
"""
Widget for exporting / importing and saving / loading filter data

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os, io
import logging
logger = logging.getLogger(__name__)
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

import scipy.io
import numpy as np
import re
import datetime
#import json

#import shelve
try:
    import cPickle as pickle
except:
    import pickle

try:
    import xlwt
except ImportError:
    XLWT = False
    logger.info("Module xlwt not installed -> no *.xls import / export")
else:
    XLWT = True

try:
    import XlsxWriter as xlsx
except ImportError:
    XLSX = False
    logger.info("Module XlsxWriter not installed -> no *.xlsx import / export")
else:
    XLSX = True

#try:
#    import xlrd
#except ImportError:
#    XLRD = False
#    logger.info("Module xlrd not installed -> no *.xls coefficient import")
#else:
#    XLRD = True
    

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
import pyfda.pyfda_rc as rc 
import pyfda.pyfda_fix_lib as fix

# TODO: Save P/Z as well if possible
# TODO: Line 192 in save_filter: Attribute Error: QString object has no attribute "endswith"

class InputFiles(QtGui.QWidget):
    """
    Create the widget for entering exporting / importing / saving / loading data
    """
    
    sigFilterLoaded = pyqtSignal() # emitted when filter has been loaded successfully
    sigReadFilters = pyqtSignal()  # emitted when button "Read Filters" is pressed

    def __init__(self):
        super(InputFiles, self).__init__()
        
#        rc.basedir = os.path.dirname(os.path.abspath(__file__))

        self.initUI()

    def initUI(self):
        """
        Intitialize the user interface
        -
        """
        # widget / subwindow for parameter selection
        self.butExport = QtGui.QPushButton("Export Coefficients", self)
        self.butExport.setToolTip("Export Coefficients in various formats.")

        self.butImport = QtGui.QPushButton("Import Coefficients", self)
        self.butImport.setToolTip("Import Coefficients in various formats.")

        self.butSave = QtGui.QPushButton("Save Filter", self)
        self.butLoad = QtGui.QPushButton("Load Filter", self)
        
        self.butReadFiltTree = QtGui.QPushButton("Read Filters", self)
        self.butReadFiltTree.setToolTip("Re-read filter design directory and build filter design tree.\n"
                                        "(For developing and debugging).")

        self.cmbSeparator = QtGui.QComboBox(self)
        self.cmbSeparator.addItems(['","','";"','<TAB>','<CR>'])
        self.cmbSeparator.setToolTip("Specify separator for number fields.")


        # ============== UI Layout =====================================
        bfont = QtGui.QFont()
        bfont.setBold(True)
        
        bifont = QtGui.QFont()
        bifont.setBold(True)
        bifont.setItalic(True)

        ifont = QtGui.QFont()
        ifont.setItalic(True)

        self.layVIO = QtGui.QVBoxLayout()
        self.layVIO.addWidget(self.butSave) # save filter dict -> various formats
        self.layVIO.addWidget(self.butLoad) # load filter dict -> various formats
        self.layVIO.addWidget(self.HLine())
        self.layVIO.addWidget(self.butExport) # export coeffs -> various formats
        self.layVIO.addWidget(self.butImport) # export coeffs -> various formats
        self.layVIO.addWidget(self.HLine())
        self.layVIO.addWidget(self.cmbSeparator)
        self.layVIO.addWidget(self.HLine())
        self.layVIO.addStretch(1)
        
        self.layVIO.addWidget(self.butReadFiltTree) # re-read filter tree (for debugging)


        layVMain = QtGui.QVBoxLayout()
        layVMain.addLayout(self.layVIO)
            
        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.butExport.clicked.connect(self.export_coeffs)
        self.butImport.clicked.connect(self.import_coeffs)
        self.butSave.clicked.connect(self.save_filter)
        self.butLoad.clicked.connect(self.load_filter)
        
        self.butReadFiltTree.clicked.connect(self.sigReadFilters.emit)


#------------------------------------------------------------------------------
    def HLine(self):
        # http://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
        # solution 
        """
        Create a horizontal line
        """
        line = QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        return line

#------------------------------------------------------------------------------        
    def load_filter(self):
        """
        Load filter from zipped binary numpy array or (c)pickled object to
        filter dictionary and update input and plot widgets
        """
        file_types = ("Zipped Binary Numpy Array (*.npz);;Pickled (*.pkl)")
#        file_types = ("Zipped Binary Numpy Array (*.npz)")
        dlg=QtGui.QFileDialog( self )
        file_name, file_type = dlg.getOpenFileNameAndFilter(self,
                caption = "Load filter ", directory = rc.save_dir,
                filter = file_types)
        file_name = str(file_name) # QString -> str
        file_type = str(file_type) # needed for Python 2.x
        
        if file_name != "": # cancelled file operation returns empty string
            file_type_err = False              
            try:
                with io.open(file_name, 'rb') as f:
                    if file_name.endswith('npz'):
                        # http://stackoverflow.com/questions/22661764/storing-a-dict-with-np-savez-gives-unexpected-result
                        a = np.load(f) # array containing dict, dtype 'object'
                        
                        for key in a:
                            if np.ndim(a[key]) == 0:
                                # scalar objects may be extracted with the item() method
                                fb.fil[0][key] = a[key].item()
                            else:
                                # array objects are converted to list first
                                fb.fil[0][key] = a[key].tolist()
                    elif file_name.endswith('pkl'):
                        if sys.version_info[0] < 3:
                            fb.fil = pickle.load(f)
                        else:
                        # this only works for python >= 3.3
                            fb.fil = pickle.load(f, fix_imports = True, encoding = 'bytes')
                    else:
                        logger.error('Unknown file type "%s"' 
                                            %os.path.splitext(file_name)[1])
                        file_type_err = True
                    if not file_type_err:
                        logger.info('Loaded filter "%s"' %file_name)
                         # emit signal -> InputTabWidgets.load_all:
                        self.sigFilterLoaded.emit()
                        rc.save_dir = os.path.dirname(file_name)
            except IOError as e:
                logger.error("Failed loading %s!" %file_name, "\n", e)
            except Exception as e:
                logger.error("Unexpected error:", e)
#------------------------------------------------------------------------------
    def save_filter(self):
        """
        Save filter as zipped binary numpy array or pickle object
        """
        file_types = ("Zipped Binary Numpy Array (*.npz);;Pickled (*.pkl)")
#        file_types = ("Zipped Binary Numpy Array (*.npz)")
        dlg = QtGui.QFileDialog( self )
        file_name, file_type = dlg.getSaveFileNameAndFilter(self,
                caption = "Save filter as", directory = rc.save_dir,
                filter = file_types)
        file_name = str(file_name) # QString -> str
        file_type = str(file_type) # needed for Python 2.x
        
        if file_name != "": # cancelled file operation returns empty string 
            file_type_err = False
            try:
                with io.open(file_name, 'wb') as f:
                    if file_name.endswith('npz'):
                        np.savez(f, **fb.fil[0])
                    elif file_name.endswith('pkl'):
                        # save as a version compatible with Python 2.x
                        pickle.dump(fb.fil, f, protocol = 2)
                    else:
                        logger.error('Unknown file type "%s"' 
                                            %os.path.splitext(file_name)[1])
                        file_type_err = True
                    if not file_type_err:
                        logger.info('Filter saved as "%s"' %file_name)
                        rc.save_dir = os.path.dirname(file_name)
                            
            except IOError as e:
                    logger.error('Failed saving "%s"!\n' %file_name, e)

#------------------------------------------------------------------------------
    def export_coeffs(self):
        """
        Export filter coefficients in various formats - see also
        Summerfield p. 192 ff
        """
        dlg=QtGui.QFileDialog( self )

        file_types = ("CSV (*.csv);;Matlab-Workspace (*.mat)"
            ";;Binary Numpy Array (*.npy);;Zipped Binary Numpy Array (*.npz)")

        if fb.fil[0]['ft'] == 'FIR':
            file_types += ";;Xilinx coefficient format (*.coe)"

        # Add further file types if modules could be imported:
        if XLWT:
            file_types += ";;Excel Worksheet (.xls)"
        if XLSX:
            file_types += ";;Excel 2007 Worksheet (.xlsx)"

        file_name, file_type = dlg.getSaveFileNameAndFilter(self,
                caption = "Export filter coefficients as", 
                directory = rc.save_dir, filter = file_types) 
        file_name = str(file_name) # QString -> str
        file_type = str(file_type) # needed for Python 2.x
        if file_name != '': # cancelled file operation returns empty string   
            ba = fb.fil[0]['ba']
            file_type_err = False
            try:
                with io.open(file_name, 'wb') as f:
                    if file_name.endswith('mat'):   
                        scipy.io.savemat(f, mdict={'ba':fb.fil[0]['ba']})
                    elif file_name.endswith('csv'):
                        np.savetxt(f, ba, delimiter = ', ')
                        # newline='\n', header='', footer='', comments='# ', fmt='%.18e'
                    elif file_name.endswith('npy'):
                        # can only store one array in the file:
                        np.save(f, ba)
                    elif file_name.endswith('npz'):
                        # would be possible to store multiple array in the file
                        np.savez(f, ba = ba)
                    elif file_name.endswith('coe'):
                        self.save_file_coe(f)
                    elif file_name.endswith('xls'):
                        # see
                        # http://www.dev-explorer.com/articles/excel-spreadsheets-and-python
                        # https://github.com/python-excel/xlwt/blob/master/xlwt/examples/num_formats.py
                        # http://reliablybroken.com/b/2011/07/styling-your-excel-data-with-xlwt/
                        workbook = xlwt.Workbook(encoding="utf-8")
                        worksheet = workbook.add_sheet("Python Sheet 1")
                        bold = xlwt.easyxf('font: bold 1')
                        worksheet.write(0, 0, 'b', bold)
                        worksheet.write(0, 1, 'a', bold)
                        for col in range(2):
                            for row in range(np.shape(ba)[1]):
                                worksheet.write(row+1, col, ba[col][row]) # vertical
                        workbook.save(f)
            
                    elif file_name.endswith('xlsx'):
                        # from https://pypi.python.org/pypi/XlsxWriter
                        # Create an new Excel file and add a worksheet.
                        workbook = xlsx.Workbook(f)
                        worksheet = workbook.add_worksheet()
                        # Widen the first column to make the text clearer.
                        worksheet.set_column('A:A', 20)
                        # Add a bold format to use to highlight cells.
                        bold = workbook.add_format({'bold': True})
                        # Write labels with formatting.
                        worksheet.write('A1', 'b', bold)
                        worksheet.write('B1', 'a', bold)
            
                        # Write some numbers, with row/column notation.
                        for col in range(2):
                            for row in range(np.shape(ba)[1]):
                                worksheet.write(row+1, col, ba[col][row]) # vertical
            #                    worksheet.write(row, col, coeffs[col][row]) # horizontal
            
            
                        # Insert an image - useful for documentation export ?!.
            #            worksheet.insert_image('B5', 'logo.png')
            
                        workbook.close()
            
                    else:
                        logger.error('Unknown file type "%s"' 
                                            %os.path.splitext(file_name)[1])
                        file_type_err = True
                        
                    if not file_type_err:
                        logger.info('Exported coefficients as %s - file\n"%s"' 
                                %(self.prune_file_ext(file_type), file_name))
                        rc.save_dir = os.path.dirname(file_name)
                    
            except IOError as e:
                logger.error('Failed saving "%s"!\n' %file_name, e)

    
            # Download the Simple ods py module:
            # http://simple-odspy.sourceforge.net/
            # http://codextechnicanum.blogspot.de/2014/02/write-ods-for-libreoffice-calc-from_1.html

#------------------------------------------------------------------------------
    def import_coeffs(self):
        """
        Import filter coefficients from a file
        """
        file_types = ("Matlab-Workspace (*.mat);;Binary Numpy Array (*.npy);;"
        "Zipped Binary Numpy Array(*.npz)")
        dlg=QtGui.QFileDialog( self )
        file_name, file_type = dlg.getOpenFileNameAndFilter(self,
                caption = "Import filter coefficients ", 
                directory = rc.save_dir, filter = file_types)
        file_name = str(file_name) # QString -> str
        file_type = str(file_type) # needed for Python 2.x
        
        if file_name != '': # cancelled file operation returns empty string  
            file_type_err = False
            try:
                with io.open(file_name, 'r') as f:
                    if file_name.endswith('mat'):
                        data = scipy.io.loadmat(f)
                        fb.fil[0]['ba'] = data['ba']
                    elif file_name.endswith('npy'):
                        fb.fil[0]['ba'] = np.load(f)
                        # can only store one array in the file
                    elif file_name.endswith('npz'):
                        fb.fil[0]['ba'] = np.load(f)['ba']
                        # would be possible to store several arrays in one file
                    else:
                        logger.error('Unknown file type "%s"' 
                                            %os.path.splitext(file_name)[1])
                        file_type_err = True
                        
                    if not file_type_err:
                        logger.info('Loaded coefficient file\n"%s"' %file_name)
                        self.sigFilterDesigned.emit() # emit signal -> pyFDA                     
                        rc.save_dir = os.path.dirname(file_name)
            except IOError as e:
                logger.error("Failed loading %s!\n" %file_name, e)



#------------------------------------------------------------------------------
    def prune_file_ext(self, file_type):
        """
        Prune file extension, e.g. '(*.txt)' from file type description
        """
        # regular expression: re.sub(pattern, repl, string) 
        #  Return the string obtained by replacing the leftmost non-overlapping 
        #  occurrences of the pattern in string by repl
        #   '.' means any character
        #   '+' means one or more
        #   '[^a]' means except for 'a'
        # '([^)]+)' : match '(', gobble up all characters except ')' till ')'
        # '(' must be escaped as '\('

        return re.sub('\([^\)]+\)', '', file_type)


#------------------------------------------------------------------------------
    def save_file_coe(self, file_name):
        """
        Save filter coefficients in Xilinx coefficient format, specifying
        the number base and the quantized coefficients
        """

        frmt = fb.fil[0]['q_coeff']['frmt'] # store old format
        fb.fil[0]['q_coeff']['frmt'] = 'dec'
        qc = fix.Fixed(fb.fil[0]['q_coeff'])
        b10 = qc.fix(fb.fil[0]['ba'][0]) # Quantize coefficients to integer format
        fb.fil[0]['q_coeff']['frmt'] = frmt # restore old coefficient format

        coe_width = qc.QF + qc.QI + 1 # quantized word length; Int. + Frac. + Sign bit
        coe_radix = 10
        info_str = (
            "; #############################################################################\n"
             ";\n; XILINX CORE Generator(tm) Distributed Arithmetic FIR filter coefficient (.COE) file\n"
             ";\n; Generated by pyFDA 0.1 (https://github.com/chipmuenk/pyfda)\n;\n; ")
        date_str = datetime.datetime.now().strftime("%d-%B-%Y %H:%M:%S")

        file_name.write(info_str + date_str + "\n;\n")
        filt_str = "; Filter order = %d, type: %s\n" %(fb.fil[0]["N"], fb.fil[0]['rt'])
        file_name.write(filt_str)
        file_name.write("; #############################################################################\n")
        file_name.write("Radix = %d;\n" %coe_radix)
        file_name.write("Coefficient_width = %d;\n" %coe_width)
        coeff_str = "CoefData = "
        for b in b10:
            coeff_str += str(b) + ",\n"
        file_name.write(coeff_str[:-2] + ";") # replace last "," by ";"


#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputFiles()
    form.show()

    app.exec_()