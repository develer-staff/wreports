#!/usr/bin/env python
# encoding: utf-8

from __future__ import division, print_function, absolute_import

import sys

from PyQt4.Qt import *

import parser


def main():
    app = QApplication(sys.argv)


    def paint_svg(printer, painter, page):
        print("  Rendering page outline")
        page_rect = printer.pageRect(QPrinter.DevicePixel)
        """
        page_pos = QPointF(page_rect.x(), page_rect.y())
        # fake print, triggers the layout at printer resolution for SvgPlaceholder
        page.resize(page_rect.width(), page_rect.height())
        # make qwidget output vectorial providing a non-qprinter device
        page_pic = QPicture()
        wpainter = QPainter(page_pic)
        page.render(wpainter, flags=QWidget.DrawChildren)
        wpainter.end()

        svg_placeholders = page.findChildren(parser.SvgPlaceholder)
        print("  Filling %d svg placeholders..." % len(svg_placeholders))
        for svg_placeholder in svg_placeholders:
            placeholder_box = QRectF(svg_placeholder.frameGeometry())

            # if the page is at screen resolution
            #placeholder_box.translate(placeholder_box.x()*9, placeholder_box.y()*9)
            #placeholder_box.setSize(placeholder_box.size()*9)

            print("    placeholder_box = %s, pos = %s" % (placeholder_box, svg_placeholder.pos()))
            svg = QSvgRenderer(svg_placeholder.src)
            print("    svg size = %s box = %s" % (svg.defaultSize(), svg.viewBox()))
            svg_box = svg.viewBoxF()
            svg_size = svg_box.size()
            svg_size.scale(placeholder_box.size(), Qt.KeepAspectRatio)
            svg_box.setSize(svg_size)
            svg_box.translate(placeholder_box.center() - svg_box.center())
            svg.render(painter, svg_box)
        """
        # real print
        page.resize(page_rect.width(), page_rect.height())
        page_pic = QPicture() # make qwidget output vectorial
        wpainter = QPainter(page_pic)
        page.render(wpainter, flags=QWidget.DrawChildren)
        wpainter.end()
        painter.drawPicture(0, 0, page_pic)

    def go():
        print("Setup pdf flags...")
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName("report.pdf")
        # printer.setFullPage(True)

        print("Parsing template")
        pages = parser.parse(open("image-preview.wrp"))

        print("Composing output pdf")
        painter = QPainter()
        painter.begin(printer)
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

