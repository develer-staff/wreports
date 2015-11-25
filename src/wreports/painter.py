#!/usr/bin/env python2
# encoding: utf-8
from __future__ import division, print_function, absolute_import

from PyQt4.Qt import *

from parser import TextViewer

__all__ = ["paint_page"]


# public api

def paint_page(painter, page, page_rect):
    """
    Given a `painter` and a `page` (a widget presumably created parsing a
    wreport), renders the widget on the painter and returns a QPicture.
    """
    # make qwidget output vectorial, rendering directly on a printer
    # results in a raster image in the pdf
    page_pic = QPicture()
    wpainter = QPainter(page_pic)

    # set the BoundingRect of page_pic and the page size to page_rect
    page_pic.setBoundingRect(page_rect.toRect())
    page.resize(page_rect.toRect().width(), page_rect.toRect().height())

    page.render(wpainter, flags=QWidget.DrawChildren)
    wpainter.end()
    painter.drawPicture(0, 0, page_pic)
    return page_pic


# demo code

def paint_pages(printer, pages, unit=QPrinter.DevicePixel):
    """
    Given a `printer` and a list of `pages`, renders the widgets on the
    printer, one per page, and returns a list of QPictures.
    """
    pictures = []
    painter = QPainter(printer)
    for i, page in enumerate(pages):
        # newPage before all pages after the first
        if i > 0:
            printer.newPage()
        pictures.append(paint_page(painter, page, printer.pageRect(unit)))
        for text_viewer in page.findChildren(TextViewer):
            for num_page in range(1, text_viewer.pageCount()):
                printer.newPage()
                text_viewer.setPageNumber(num_page)
                pictures.append(paint_page(painter, text_viewer, printer.pageRect(unit)))
    painter.end()
    return pictures


def demo(template, preview=True):
    import os
    from os.path import dirname, basename
    import parser
    app = QApplication([])

    print("Setup printer...")
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName("report.pdf")
    printer.setColorMode(QPrinter.Color)
    printer.setPaperSize(QPrinter.A4)
    #printer.setOrientation(QPrinter.Landscape)

    def print_pages(requested_printer):
        print("Parsing template")
        current_dir = os.getcwd()
        template_dir = dirname(template)
        os.chdir(template_dir)
        pages = parser.parse(open(basename(template)))
        paint_pages(requested_printer, pages)
        os.chdir(current_dir)

    if preview:
        pd = QPrintPreviewDialog(printer)
        pd.connect(pd, SIGNAL("paintRequested(QPrinter *)"), print_pages)
    else:
        pd = QPrintDialog(printer)
        if pd.exec_() != QDialog.Accepted:
            return
        print_pages(printer)

    print("Show print dialog...")
    QTimer.singleShot(500, pd.exec_)
    sys.exit(app.exec_())


if __name__ == '__main__':
    import os
    import sys
    if sys.argv[1:] and os.path.exists(sys.argv[1]):
        template = sys.argv[1]
        print("Parsing template %s" % template)
        preview = "--preview" in sys.argv
        demo(template, preview)
    else:
        print("Provide a wreport template [--preview]")
