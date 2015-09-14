#!/usr/bin/env python
# encoding: utf-8

from __future__ import division, print_function, absolute_import

import sys

from PyQt4.Qt import *

import parser


def main():
    app = QApplication(sys.argv)


    def paint_svg(printer, painter, page):
        page_rect = printer.pageRect(QPrinter.Point)
        print("  Rendering page size = %s, resolution = %s" % (page_rect.size(), printer.resolution()))
        page.resize(page_rect.width()/0.6, page_rect.height()/0.6)
        print("  physicalDpi = %s %s" % (printer.physicalDpiX(), printer.physicalDpiY()))
        # make qwidget output vectorial, rendering directly on a painter
        # results in a raster image in the pdf
        page_pic = QPicture()
        wpainter = QPainter(page_pic)
        page.render(wpainter, flags=QWidget.DrawChildren)
        wpainter.end()
        painter.drawPicture(0, 0, page_pic)

    def go():
        print("Setup pdf flags...")
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName("report.pdf")
        printer.setColorMode(QPrinter.Color)
        printer.setFullPage(True)

        print("Parsing template")
        pages = parser.parse(open("image-preview.wrp"))

        print("Composing output pdf")
        painter = QPainter(printer)
        print("Adding %d pages..." % len(pages))
        for i, page in enumerate(pages):
            if i > 0: # dopo la prima
                printer.newPage()
            print("Printing page %d..." % (i+1))
            paint_svg(printer, painter, page)
        painter.end()

        print("done!")
        app.quit()

    timer = QTimer()
    timer.singleShot(100, go)
    timer.start()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

