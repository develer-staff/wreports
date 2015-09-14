#!/usr/bin/env python2
# encoding: utf-8
from __future__ import print_function, absolute_import, division

import xml.parsers.expat
import types

from PyQt4.Qt import *

__all__ = [parse, SvgPlaceholder]

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
    Document root, simply a container o pages
    <report>
      ...
    </report>
    """
    pass


def _page(name=None, size=(600, 900)):
    """
    The page is the container of all the page contents
    """
    page = QWidget()
    _set_object(page, name=name)
    page.resize(*size)
    return page


def _vlayout(spacing=0,
             margins=(0,0,0,0),
             name=None,
             widget=None,
             layout=None):
    """
    Vertical layout, with some defaults better suited to printed output.
    There are no tables (yet) in this markup, so nest more v|h layouts to build one.
    <hlayout>
      <vlayout>
        ...
      </vlayout>
      <vlayout>
        ...
      </vlayout>
    </hlayout>
    """
    vlayout = QVBoxLayout()
    _set_layout(vlayout,
                widget=widget,
                spacing=spacing,
                margins=margins,
                name=name,
                parent_layout=layout)
    return vlayout


def _hlayout(spacing=0,
             margins=(0,0,0,0),
             name=None,
             widget=None,
             layout=None):
    """
    Horizontal layout, see _vlayout for details
    """
    hlayout = QHBoxLayout()
    _set_layout(hlayout,
                widget=widget,
                spacing=spacing,
                margins=margins,
                name=name,
                parent_layout=layout)
    return hlayout


def _label(widget=None,
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
           width=1,
           name=None):
    """
    Horizontal line
    """
    line = QFrame()
    line.setFrameShadow(QFrame.Plain)
    line.setFrameShape(QFrame.HLine)
    line.setLineWidth(width)
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
           width=1,
           name=None):
    """
    Vertical line
    """
    line = QFrame()
    line.setFrameShadow(QFrame.Plain)
    line.setFrameShape(QFrame.VLine)
    line.setLineWidth(width)
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

class SvgPlaceholder(QFrame):
    def __init__(self, src, *args, **kwargs):
        super(SvgPlaceholder, self).__init__(*args, **kwargs)
        self.src = src

def _svg(src,
           widget=None,
           layout=None,
           width="Preferred",
           height="MinimumExpanding",
           name=None):
    """
    Svg tag, provide a pointer to a valid svg file
    """
    svg = SvgPlaceholder(src)
    _set_widget(svg,
                layout=layout,
                parent=widget,
                width=width,
                height=height,
                name=name)
    svg.setStyleSheet("SvgPlaceholder { background: yellow }")
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

            def nfw(w):
                if isinstance(w, QObject):
                    return "<name=%s>" % w.objectName()
                else:
                    return w
            named_args = tuple(nfw(a) for a in args)
            named_kwargs = {k: nfw(kwargs[k]) for k in kwargs}
            print("%s %s %s)" % ("  "*len(tags), named_args, named_kwargs))

            # print("_%s(*%r, **%r)" % (tag, args, kwargs))
            obj = hook(*args, **kwargs)
            if "report" in tag:
                pass
            elif "layout" in tag:
                layouts.append(obj)
            else:
                if "page" in tag:
                    pages.append(obj)
                widgets.append(obj)
        return f

    def start_element(tag, attrs):
        tags.append(tag)
        print("%s<%s>" % ("  "*len(tags), tag))
        obj = x(tag)(**attrs)
    def end_element(tag):
        if "report" in tag:
            pass
        elif "layout" in tag:
            layouts.pop()
        else:
            widgets.pop()
        print("%s</%s>" % ("  "*len(tags), tag))
        popped_name = tags.pop()
        assert popped_name == tag, (popped_name, tag)
    def char_data(data):
        tag = tags[-1] if tags else None
        if "label" in tag:
            widget = widgets[-1] if widgets else None
            if isinstance(widget, QLabel):
                widget.setText(data.strip())

    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data

    _parse(source)

    return pages


def main(args):
    app = QApplication(args)

    if "code" in args:
        page = _page()
        page_layout = _vlayout(name="page_layout", widget=page)
        header_layout = _hlayout(name="header_layout", widget=page, layout=page_layout)
        col1 = _label("Some text", widget=page, layout=header_layout)
        col2 = _label("Other text", widget=page, layout=header_layout)
        col3 = _label("Even other text", widget=page, layout=header_layout)
        svg = _svg(src="some.svg", widget=page, layout=page_layout)
        footer = _label("Footer", widget=page, layout=page_layout)
    else:
        pages = parse(open("image-preview.wrp"))
        page = pages[0]

    page.show()

    return app.exec_()



if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
