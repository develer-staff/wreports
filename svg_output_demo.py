#!/usr/bin/env python
# encoding: utf-8

from __future__ import division, print_function, absolute_import

import sys

from PyQt4.Qt import *


def main():
    app = QApplication(sys.argv)


    def go():
        print("creating pdf...")
        svg_path = "piece1.svg"

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat);
        printer.setOutputFileName("report.pdf");
        paper_size = printer.paperSize(QPrinter.DevicePixel)
        print("printer page = %s" % paper_size)

        svg = QSvgRenderer(svg_path)
        print("svg size = %s box = %s" % (svg.defaultSize(), svg.viewBox()))
        svg_box = svg.viewBoxF()
        svg_size = svg_box.size()
        svg_size.scale(paper_size/3, Qt.KeepAspectRatio)
        svg_box.setSize(svg_size)
        print("svg_box = %s" % svg_box)

        img = QImage(svg_path)
        print("img size = %s" % img.size())

        painter = QPainter()
        painter.begin(printer)

        svg.render(painter, svg_box)

        printer.newPage()

        painter.drawImage(QPoint(0,0), img)

        painter.end()
        print("done!")
        app.quit()

    timer = QTimer()
    timer.singleShot(100, go)
    timer.start()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

