#!/usr/bin/env python2
# encoding: utf-8
from __future__ import print_function, absolute_import, division

import xml.parsers.expat
import types

from PyQt4.Qt import *


__all__ = ["parse"]

# Helper functions to apply attributes to qwidgets

def _set_object(obj, parent=None, name=None):
    if parent is not None:
        obj.setParent(parent)
    if name is not None:
        obj.setObjectName(name)

def _set_layout(layout,
                widget=None,
                spacing=None,
                margins=None,
                parent_layout=None,
                **kwargs):
    if widget is not None:
        if widget.layout() is None:
            widget.setLayout(layout)
    if margins is not None:
        layout.setContentsMargins(*margins)
    if spacing is not None:
        layout.setSpacing(spacing)
    if parent_layout is not None:
        parent_layout.addLayout(layout)
    _set_object(layout, **kwargs)
    return layout

def _set_widget(widget,
                layout=None,
                width=None,
                height=None,
                **kwargs):
    if layout is not None:
        layout.addWidget(widget)
    if (width, height) is not (None, None):
        policy = QSizePolicy()
        if width is not None:
            horizontal = getattr(QSizePolicy, width)
            policy.setHorizontalPolicy(horizontal)
        if height is not None:
            vertical = getattr(QSizePolicy, height)
            policy.setVerticalPolicy(vertical)
        widget.setSizePolicy(policy)
    _set_object(widget, **kwargs)

# Tag function, called for each _<tag> found

def _report(*args, **kwargs):
    """
    Document root, simply a container of pages
    <report>
      ...
    </report>
    """
    pass


def _page(spacing=0,
          margins=(0,0,0,0),
          name=None,
          child_layout="col"):
    """
    The page is the container of all the page contents, a page contains a
    default layout
    """
    page = QWidget()
    col_name = name+"_layout" if name is not None else None
    layouts = {"col": _col, "row": _row}
    try:
        _layout = layouts[child_layout]
    except KeyError:
        msg = "Invalid value %r for `child_layout`, use %s"
        raise ValueError(msg % (child_layout, "|".join(layouts.keys())))
    _layout(spacing=spacing, margins=margins, name=col_name, widget=page)
    return page


def _col(spacing=0,
         margins=(0,0,0,0),
         name=None,
         widget=None,
         layout=None):
    """
    Vertical layout, with some defaults better suited to printed output.
    There are no tables (yet) in this markup, so nest more col|row layouts to
    build one.

    <row>
      <col>
        ...
      </col>
      <col>
        ...
      </col>
    </row>
    """
    vlayout = QVBoxLayout()
    _set_layout(vlayout,
                widget=widget,
                spacing=spacing,
                margins=margins,
                name=name,
                parent_layout=layout)
    return vlayout


def _row(spacing=0,
         margins=(0,0,0,0),
         name=None,
         widget=None,
         layout=None):
    """
    Horizontal layout, see _col for details
    """
    hlayout = QHBoxLayout()
    _set_layout(hlayout,
                widget=widget,
                spacing=spacing,
                margins=margins,
                name=name,
                parent_layout=layout)
    return hlayout


def _text(widget=None,
          layout=None,
          width="Ignored",
          height="Maximum",
          name=None):
    """
    Text in the layout
    """
    label = QLabel()
    _set_widget(label,
                layout=layout,
                parent=widget,
                width=width,
                height=height,
                name=name)
    return label


def _hline(color="black",
           widget=None,
           layout=None,
           line_width=1,
           name=None):
    """
    Horizontal line
    """
    line = QFrame()
    line.setFrameShadow(QFrame.Plain)
    line.setFrameShape(QFrame.HLine)
    line.setLineWidth(line_width)
    _set_widget(line,
                layout=layout,
                parent=widget,
                width="Minimum",
                height="Fixed",
                name=name)
    return line


def _vline(color="black",
           widget=None,
           layout=None,
           line_width=1,
           name=None):
    """
    Vertical line
    """
    line = QFrame()
    line.setFrameShadow(QFrame.Plain)
    line.setFrameShape(QFrame.VLine)
    line.setLineWidth(line_width)
    _set_widget(line,
                layout=layout,
                parent=widget,
                width="Fixed",
                height="Minimum",
                name=name)
    return line

# Image rendering is done in two steps, the first run we detect the size of the
# image in the document, in the second step we render the image correctly scaled
# into the reserved place (vectorial svn render).

class AspectRatioSvgWidget(QSvgWidget):
    def paintEvent(self, paint_event):
        painter = QPainter(self)
        view_box = self.renderer().viewBox()
        default_width, default_height = view_box.width(), view_box.height()
        widget_size = self.size()
        widget_width, widget_height = widget_size.width(), widget_size.height()
        ratio_x = widget_width / default_width
        ratio_y = widget_height / default_height
        if ratio_x < ratio_y:
            new_width = widget_width
            new_height = widget_width * default_height / default_width
            new_left = 0
            new_top = (widget_height - new_height) / 2
        else:
            new_width = widget_height * default_width / default_height
            new_height = widget_height
            new_left = (widget_width - new_width) / 2
            new_top = 0
        new_rect = QRectF(new_left, new_top, new_width, new_height)
        self.renderer().render(painter, new_rect)

def _svg(src,
         widget=None,
         layout=None,
         width="Preferred",
         height="MinimumExpanding",
         name=None):
    """
    Svg tag, provide a pointer to a valid svg file
    """
    svg = AspectRatioSvgWidget(src)
    _set_widget(svg,
                layout=layout,
                parent=widget,
                width=width,
                height=height,
                name=name)
    # svg.setStyleSheet("SvgPlaceholder { background: yellow }")
    return svg


def _image(src,
           widget=None,
           layout=None,
           width="Preferred",
           height="MinimumExpanding",
           name=None):
    """
    image tag, provide a pointer to a valid image file
    """
    pixmap = QPixmap(src)
    image = QLabel()
    image.setPixmap(pixmap)
    _set_widget(image,
                layout=layout,
                parent=widget,
                width=width,
                height=height,
                name=name)
    return image


# Attributes parsers

def _parse_spacing(value):
    try:
        return float(value)
    except:
        raise ValueError("Invalid value %r for `spacing`, provide a valid number" % value)

def _parse_margins(value):
    try:
        return tuple(float(v.strip()) for v in value.strip("()").split(","))
    except:
        raise ValueError("Invalid value %r for `margins`, provide 4 comma separated numbers, es. (3,3,4,4)" % value)

def _parse_size(value):
    try:
        return tuple(float(v.strip()) for v in value.strip("()").split(","))
    except:
        raise ValueError("Invalid value %r for `size`, provide 2 comma separated numbers, es. (300,400)" % value)

def _parse_line_width(value):
    try:
        return float(value.strip())
    except:
        raise ValueError("Invalid value %r for `line_width`, provide a valid numbers" % value)

def _parse_color(value):
    try:
        return QColor(value)
    except:
        raise ValueError("Invalid color %r, provide a valid QColor" % value)


# Entrypoint

def parse(source):
    p = xml.parsers.expat.ParserCreate()
    if isinstance(source, types.StringTypes):
        _parse = p.Parse
    else:
        _parse = p.ParseFile

    tags = []
    widgets = []
    layouts = []
    pages = []

    parsers = {}
    for parser_name in globals():
        if parser_name.startswith("_parse_"):
            attr = parser_name[len("_parse_"):]
            parsers[attr] = globals()[parser_name]

    def x(tag):
        hook = globals()["_"+tag]
        def f(*args, **kwargs):
            # parse non string arguments
            for attr in kwargs:
                if attr in parsers:
                    kwargs[attr] = parsers[attr](kwargs[attr])

            if widgets:
                kwargs["widget"] = widgets[-1]
            if layouts:
                kwargs["layout"] = layouts[-1]

            # def nfw(w):
            #     if isinstance(w, QObject):
            #         return "<name=%s>" % w.objectName()
            #     else:
            #         return w
            # named_args = tuple(nfw(a) for a in args)
            # named_kwargs = {k: nfw(kwargs[k]) for k in kwargs}
            # print("%s %s %s)" % ("  "*len(tags), named_args, named_kwargs))

            # print("_%s(*%r, **%r)" % (tag, args, kwargs))
            obj = hook(*args, **kwargs)
            if tag == "report":
                pass
            elif tag in ("col", "row"):
                layouts.append(obj)
            else:
                if tag == "page":
                    pages.append(obj)
                    layouts.append(obj.layout())
                widgets.append(obj)
        return f

    def start_element(tag, attrs):
        tags.append(tag)
        # print("%s<%s>" % ("  "*len(tags), tag))
        obj = x(tag)(**attrs)
    def end_element(tag):
        if tag == "report":
            pass
        elif tag in ("col", "row"):
            layouts.pop()
        else:
            if tag == "page":
                layouts.pop()
            widgets.pop()
        # print("%s</%s>" % ("  "*len(tags), tag))
        popped_name = tags.pop()
        assert popped_name == tag, (popped_name, tag)
    def char_data(data):
        tag = tags[-1] if tags else None
        if tag == "text":
            widget = widgets[-1] if widgets else None
            if isinstance(widget, QLabel):
                widget.setText(data.strip())

    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data

    _parse(source)

    return pages


# Command line

def demo(template):
    import os
    from os.path import dirname, basename

    app = QApplication([])

    template_dir = dirname(template)
    os.chdir(template_dir)
    pages = parse(open(basename(template)))
    page = pages[0]

    page.show()

    return app.exec_()


if __name__ == '__main__':
    import os
    import sys
    if sys.argv[1:] and os.path.exists(sys.argv[1]):
        template = sys.argv[1]
        print("Parsing template %s" % template)
        demo(template)
    else:
        print("Provide a wreport template")
