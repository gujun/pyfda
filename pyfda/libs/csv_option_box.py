# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with classes and functions for file and text IO
"""
# TODO: import data from files doesn't update FIR / IIR and data changed

from .pyfda_qt_lib import (qget_cmb_box, qset_cmb_box, qcmb_box_populate,
                           qwindow_stay_on_top)
from pyfda.pyfda_rc import params
from .compat import (QLabel, QComboBox, QDialog, QPushButton, QRadioButton,
                     QCheckBox, QVBoxLayout, QGridLayout, pyqtSignal)

import logging
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
class CSV_option_box(QDialog):
    """
    Create a pop-up widget for setting CSV options. This is needed when storing /
    reading Comma-Separated Value (CSV) files containing coefficients or poles
    and zeros.
    """
    sig_tx = pyqtSignal(object)  # outgoing  # was: (dict)
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent, has_cmsis=True):
        super(CSV_option_box, self).__init__(parent)

        self.has_cmsis = has_cmsis
        self.cmb_delimiter_default = "auto"
        self.cmb_terminator_default = "auto"

        self._construct_UI()
        qwindow_stay_on_top(self, True)

# ------------------------------------------------------------------------------
    def closeEvent(self, event):
        """
        Override closeEvent (user has tried to close the window) and send a
        signal to parent where window closing is registered before actually
        closing the window.
        """
        self.emit({'closeEvent': ''})
        event.accept()

# ------------------------------------------------------------------------------
    def _construct_UI(self):
        """ initialize the User Interface """
        self.setWindowTitle("CSV Options")

        lbl_delimiter = QLabel("CSV-Delimiter", self)
        cmb_delimiter_items = ["<span>Select delimiter between data fields for im- and export."
                       "</span>",
            ("auto", "Auto / ','", "<span>Detect the delimiter automatically for import, "
             "use ',' for exporting data.</span>"),
            (',', '< , >', "<span>Use ',' as delimiter between data fields.</span>"),
            (';', '< ; >', "<span>Use ';' as delimiter between data fields.</span>"),
            ( '\t', '<TAB>', "<span>Use &lt;TAB&gt; as delimiter between data fields."
             "</span>"),
            ( ' ', '<SPACE>', "<span>Use &lt;SPACE&gt; as delimiter between data "
             "fields.</span>"),
            ( '|', '< | >',"<span>Use '|' as delimiter between data fields.</span>")
            ]
        self.cmb_delimiter = QComboBox(self)
        qcmb_box_populate(self.cmb_delimiter, cmb_delimiter_items,
                          self.cmb_delimiter_default)


        lbl_terminator = QLabel("Line Terminator", self)
        cmb_terminator_items = [
            ('Auto', 'auto', "<span>Use operating system's line terminator default "
             'characters.</span>'),
            ('CRLF (Win)', '\r\n', 'Use &lt;CRLF&gt; as line terminator (Windows '
             'convention)</span>'),
            ('CR (Mac)', '\r', 'Use &lt;CR&gt; for line termination (MacOS '
             'convention)</span>'),
            ('LF (Unix)', '\n', 'Use &lt;LF&gt; for line termination (Unix '
             'convention)</span>')
            # ('None', '\a')  # WTF?
            ]
        self.cmb_terminator = QComboBox(self)
        self.cmb_terminator.setToolTip(
            "<span>Terminator at the end of a data row."
            " (depending on the operating system). 'None' can be used for a single "
            "row of data with added line breaks.</span>")
        for t in cmb_terminator_items:
            self.cmb_terminator.addItem(t[0], t[1])

        butClose = QPushButton(self)
        butClose.setText("Close")

        lbl_orientation = QLabel("Table orientation", self)
        cmb_orientation_items = [
            ('Auto/Vert.', 'auto'),
            ('Vertical', 'vert'),
            ('Horizontal', 'horiz')
            ]
        self.cmb_orientation = QComboBox(self)
        self.cmb_orientation.setToolTip("<span>Select orientation of table.</span>")
        for o in cmb_orientation_items:
            self.cmb_orientation.addItem(o[0], o[1])

        lblHeader = QLabel("Enable header", self)
        header = [('Auto', 'auto'), ('On', 'on'), ('Off', 'off')]
        self.cmbHeader = QComboBox(self)
        self.cmbHeader.setToolTip("First row is a header.")
        for h in header:
            self.cmbHeader.addItem(h[0], h[1])

        lbl_cmsis = QLabel("CMSIS SOS format", self)
        lbl_cmsis.setVisible(self.has_cmsis)
        self.chk_cmsis = QCheckBox()
        self.chk_cmsis.setChecked(False)
        self.chk_cmsis.setToolTip(
            "<span>Use CMSIS DSP second-order sections format "
            "(only for IIR coefficients).</span>")
        self.chk_cmsis.setVisible(self.has_cmsis)

        self.radClipboard = QRadioButton("Clipboard", self)
        self.radClipboard.setChecked(False)
        self.radFile = QRadioButton("File", self)
        # setting is read later on from params['CSV']['clipboard']
        self.radFile.setChecked(True)

        lay_grid = QGridLayout()
        lay_grid.addWidget(lbl_delimiter, 1, 1)
        lay_grid.addWidget(self.cmb_delimiter, 1, 2)
        lay_grid.addWidget(lbl_terminator, 2, 1)
        lay_grid.addWidget(self.cmb_terminator, 2, 2)
        lay_grid.addWidget(lbl_orientation, 3, 1)
        lay_grid.addWidget(self.cmb_orientation, 3, 2)
        lay_grid.addWidget(lblHeader, 4, 1)
        lay_grid.addWidget(self.cmbHeader, 4, 2)
        lay_grid.addWidget(lbl_cmsis, 5, 1)
        lay_grid.addWidget(self.chk_cmsis, 5, 2)
        lay_grid.addWidget(self.radClipboard, 6, 1)
        lay_grid.addWidget(self.radFile, 6, 2)

        layVMain = QVBoxLayout()
        # layVMain.setAlignment(Qt.AlignTop) # only affects first widget (intended here)
        layVMain.addLayout(lay_grid)
        layVMain.addWidget(butClose)
        layVMain.setContentsMargins(*params['wdg_margins'])
        self.setLayout(layVMain)

        self.load_settings()

        # ============== Signals & Slots ================================
        butClose.clicked.connect(self.close)
        self.cmb_orientation.currentIndexChanged.connect(self.store_settings)
        self.cmb_delimiter.currentIndexChanged.connect(self.store_settings)
        self.cmb_terminator.currentIndexChanged.connect(self.store_settings)
        self.cmbHeader.currentIndexChanged.connect(self.store_settings)
        self.chk_cmsis.clicked.connect(self.store_settings)
        self.radClipboard.clicked.connect(self.store_settings)
        self.radFile.clicked.connect(self.store_settings)

    def store_settings(self):
        """
        Store settings of CSV options widget in ``pyfda_rc.params``.
        """

        try:
            params['CSV']['orientation'] = qget_cmb_box(self.cmb_orientation, data=True)
            params['CSV']['delimiter'] = qget_cmb_box(self.cmb_delimiter, data=True)
            params['CSV']['lineterminator'] = qget_cmb_box(self.cmb_terminator,
                                                           data=True)
            params['CSV']['header'] = qget_cmb_box(self.cmbHeader, data=True)
            params['CSV']['cmsis'] = self.chk_cmsis.isChecked()
            params['CSV']['clipboard'] = self.radClipboard.isChecked()

            self.emit({'ui_global_changed': 'csv'})

        except KeyError as e:
            logger.error(e)

    def load_settings(self):
        """
        Load settings of CSV options widget from ``pyfda_rc.params``.
        """
        try:
            qset_cmb_box(self.cmb_orientation, params['CSV']['orientation'], data=True)
            qset_cmb_box(self.cmb_delimiter, params['CSV']['delimiter'], data=True)
            qset_cmb_box(self.cmb_terminator, params['CSV']['lineterminator'],
                         data=True)
            qset_cmb_box(self.cmbHeader, params['CSV']['header'], data=True)
            self.chk_cmsis.setChecked(params['CSV']['cmsis'])

            self.radClipboard.setChecked(params['CSV']['clipboard'])
            self.radFile.setChecked(not params['CSV']['clipboard'])

        except KeyError as e:
            logger.error(f"Unknown key {e}")


# ==============================================================================
if __name__ == '__main__':
    """
    Run a simple test with python -m pyfda.libs.csv_option_box
    """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = CSV_option_box(parent=None)
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
