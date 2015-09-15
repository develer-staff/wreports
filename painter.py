#!/usr/bin/env python
# encoding: utf-8
from __future__ import division, print_function, absolute_import

import sys

from PyQt4.Qt import *


def paint_page(painter, page):
    """
    Given a `painter` and a `page` (a widget presumably created parsing a
    wreport), renders the widget on the painter and returns a QPicture.
    """
    printer = painter.device()
    page_rect = printer.pageRect(QPrinter.DevicePixel)
    # make qwidget output vectorial, rendering directly on a painter
    # results in a raster image in the pdf
    page_pic = QPicture()
    wpainter = QPainter(page_pic)
    pdevice = painter.device()
    wdevice = wpainter.device()
    ratioX = pdevice.physicalDpiX() / wdevice.physicalDpiX()
    ratioY = pdevice.physicalDpiY() / wdevice.physicalDpiY()
    page.resize(page_rect.width()/ratioX, page_rect.height()/ratioY)
    page.render(wpainter, flags=QWidget.DrawChildren)
    wpainter.end()
    painter.drawPicture(0, 0, page_pic)
    return page_pic


def paint_pages(printer, pages):
    """
    Given a `printer` and a list of `pages`, renders the widgets on the
    printer, one per page, and returns a list of QPictures.
    """
    pictures = []
    print("Composing output pdf")
    painter = QPainter(printer)
    print("Adding %d pages..." % len(pages))
    for i, page in enumerate(pages):
        if i > 0: # dopo la prima
            printer.newPage()
        print("Printing page %d..." % (i+1))
        pictures.append(paint_page(painter, page))
    painter.end()
    return pictures


__all__ = [paint_page, paint_pages]

def main():
    import parser
    app = QApplication(sys.argv)

    def go(w):
        print("Setup printer...")
        printer = QPrinter(QPrinter.HighResolution)
        #printer.setOutputFormat(QPrinter.PdfFormat)
        #printer.setOutputFileName("report.pdf")
        #printer.setColorMode(QPrinter.Color)
        #printer.setPaperSize(QPrinter.A4)
        #printer.setOrientation(QPrinter.Landscape)

        pd = QPrintDialog(printer, w)
        if pd.exec_() != QDialog.Accepted:
            return

        print("Parsing template")
        pages = parser.parse(open("image-preview.wrp"))
        paint_pages(printer, pages)

        print("done!")

    print("Show print dialog...")
    w = QPushButton("Click to close")
    w.connect(w, SIGNAL("clicked(bool)"), w.close)
    w.show()
    go(w)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

