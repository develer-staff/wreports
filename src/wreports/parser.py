#!/usr/bin/env python2
# encoding: utf-8
from __future__ import print_function, absolute_import, division

import xml.parsers.expat
import types
import textwrap

import mistune
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
                horizontal=None,
                vertical=None,
                size=None,
                **kwargs):
    if layout is not None:
        layout.addWidget(widget)
    if (horizontal, vertical) is not (None, None):
        policy = widget.sizePolicy()
        if horizontal is not None:
            policy.setHorizontalPolicy(getattr(QSizePolicy, horizontal))
        if vertical is not None:
            policy.setVerticalPolicy(getattr(QSizePolicy, vertical))
        widget.setSizePolicy(policy)
    if size is not None:
        qsize = QSize(*size)
        print("Setting sizeHint to %s" % qsize)
        widget.sizeHint = lambda: qsize
        widget.setMinimumSize(qsize)
        widget.setMaximumSize(qsize)
    widget.updateGeometry()
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
    default layout (see special handling in `parse` function).
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


def _label(widget=None,
           layout=None,
           horizontal="Ignored",
           vertical="Maximum",
           name=None,
           **kwargs):
    """
    Single line text in the layout
    """
    label = QLabel()
    _set_widget(label,
                layout=layout,
                parent=widget,
                horizontal=horizontal,
                vertical=vertical,
                name=name,
                **kwargs)
    return label


class TextViewer(QWidget):
    def __init__(self, *args, **kwargs):
        super(TextViewer, self).__init__(*args, **kwargs)
        self._document = QTextDocument(self)
        self._document.setUseDesignMetrics(True)
    def document(self):
        return self._document
    def setHtml(self, html):
        self._document.setHtml(html)
    def resizeEvent(self, resize_event):
        size = resize_event.size()
        self._document.setPageSize(QSizeF(size.width(), size.height()))
        self.setMaximumHeight(self._document.size().height())
    def paintEvent(self, paint_event):
        print("size = %s" % self._document.size())
        print("lines = %s" % self._document.lineCount())
        painter = QPainter(self)
        size = self._document.pageSize()
        self._document.drawContents(painter, QRectF(0, 0, size.width(), size.height()))

def _text(widget=None,
          layout=None,
          horizontal="MinimumExpanding",
          vertical="Maximum",
          name=None,
          **kwargs):
    """
    Multiline markdown formatted text in the layout
    """
    text = TextViewer()
    _set_widget(text,
                layout=layout,
                parent=widget,
                horizontal=horizontal,
                vertical=vertical,
                name=name,
                **kwargs)
    return text


def _hline(color="black",
           widget=None,
           layout=None,
           line_width=1,
           name=None,
           **kwargs):
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
                horizontal="Minimum",
                vertical="Fixed",
                name=name,
                **kwargs)
    return line


def _vline(color="black",
           widget=None,
           layout=None,
           line_width=1,
           name=None,
           **kwargs):
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
                horizontal="Fixed",
                vertical="Minimum",
                name=name,
                **kwargs)
    return line


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
         horizontal="Preferred",
         vertical="MinimumExpanding",
         name=None,
         **kwargs):
    """
    Svg tag, provide a pointer to a valid svg file
    """
    svg = AspectRatioSvgWidget(src)
    _set_widget(svg,
                layout=layout,
                parent=widget,
                horizontal=horizontal,
                vertical=vertical,
                name=name,
                **kwargs)
    # svg.setStyleSheet("SvgPlaceholder { background: yellow }")
    return svg


def _image(src,
           widget=None,
           layout=None,
           horizontal="Preferred",
           vertical="MinimumExpanding",
           name=None,
           **kwargs):
    """
    Image tag, provide a pointer to a valid image file
    """
    pixmap = QPixmap(src)
    image = QLabel()
    image.setPixmap(pixmap)
    _set_widget(image,
                layout=layout,
                parent=widget,
                horizontal=horizontal,
                vertical=vertical,
                name=name,
                **kwargs)
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

# Markdown helpers

class EvenOddRendered(mistune.Renderer):
    def __init__(self, *args, **kwargs):
        super(EvenOddRendered, self).__init__(*args, **kwargs)
        self._even_odd = False
    def table(self, header, body):
        out = super(EvenOddRendered, self).table(header, body)
        return out.replace("<table>", '<table width="100%">', 1)
    def table_row(self, content):
        out = super(EvenOddRendered, self).table_row(content)
        if content.strip().startswith("<th>"):
            cls = 'class="header"'
        else:
            cls = 'class="even"' if self._even_odd else 'class="odd"'
            self._even_odd = not self._even_odd
        out = out.replace("<tr>", "<tr %s>" % cls, 1)
        return out

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
    buffers = {"text": [], "label": []}

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
        if tag == "text":
            if buffers["text"]:
                widget = widgets[-1] if widgets else None
                if isinstance(widget, TextViewer):
                    css = textwrap.dedent("""
                    <style type="text/css">
                        tr.header {background: #BBB}
                        tr.even {background: #CCC}
                        tr.odd {background: #FFF}
                    </style>
                    """).strip()
                    text = "".join(buffers["text"])
                    code = textwrap.dedent(text).strip()
                    html = mistune.Markdown(EvenOddRendered())(code)
                    print("setHtml <- %s" % html)
                    widget.setHtml("%s\n%s" % (css, html))
            buffers["text"] = []
        elif tag == "label":
            if buffers["label"]:
                widget = widgets[-1] if widgets else None
                if isinstance(widget, QLabel):
                    text = "".join(buffers["label"])
                    widget.setText(text.strip())
            buffers["label"] = []

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
        if tag in ("label", "text"):
            buffers[tag] += [data]

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
