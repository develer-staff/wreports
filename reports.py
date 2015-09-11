#!/usr/bin/env python2
# encoding: utf-8

from PyQt4.Qt import *
from PyQt4 import uic


class ReportPreview(QWidget):
    def __init__(self, parent=None):
        super(ReportPreview, self).__init__(parent)
        uic.loadUi("reportpreview.ui", self)


def main(args):
    app = QApplication(args)
    rp = ReportPreview()
    rp.show()
    def is_widget(w):
        return "widget" in w.objectName()
    widgets = [w for w in rp.findChildren(QWidget) if is_widget(w)]
    for i, w in enumerate(widgets):
        print("%d: %s" % (i, w.frameGeometry()))
    return app.exec_()


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
