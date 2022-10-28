#!/usr/bin/env python2
# encoding: utf-8
from __future__ import print_function, absolute_import, division

import xml.parsers.expat
import sys
import os
import textwrap

import bbcode
import mistune

try:
    from PyQt5.Qt import Qt
    from PyQt5.QtCore import (QSize, QSizeF, QByteArray, QRectF)
    from PyQt5.QtGui import (QPixmap, QPainter, QColor, QTextDocument)
    from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QLabel, QFrame,
                             QSizePolicy, QApplication)
    from PyQt5.QtSvg import QSvgWidget
except ImportError:
    from PyQt4.Qt import Qt
    from PyQt4.QtCore import (QSize, QSizeF, QByteArray, QRectF)
    from PyQt4.QtGui import (QVBoxLayout, QHBoxLayout, QSizePolicy, QPixmap, QPainter,
                             QColor, QApplication, QWidget, QLabel, QTextDocument, QFrame)
    from PyQt4.QtSvg import QSvgWidget

from . import errors

PY3 = sys.version_info.major == 3
if PY3:
    string_types = (str, bytes)
else:
    from types import StringTypes as string_types

__all__ = ["parse"]

def formatError(d):
    error =""
    for k,v in d.items():
        error+=" %s=%s" % (k,v)
    return error

# Helper functions to apply attributes to qwidgets
def _set_object(obj, line, parent=None, name=None, env=None, **kwargs):
    if __debug__:
        if kwargs:
            error = formatError(kwargs)
            raise errors.ParseError("unknown attributes%s at line %d in <%s>" % (error, line, name))
    if parent is not None:
        obj.setParent(parent)
    if name is not None:
        obj.setObjectName(name)


def _set_layout(layout,
                widget=None,
                spacing=None,
                margins=None,
                parent_layout=None,
                alignment=None,
                stretch=10,
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
        parent_layout.setStretchFactor(layout, int(stretch))
    if alignment is not None:
        layout.setAlignment(getattr(Qt, alignment))
    _set_object(layout, **kwargs)
    return layout


def _set_widget(widget,
                layout=None,
                horizontal=None,
                vertical=None,
                size=None,
                alignment=None,
                hstretch=10,
                vstretch=10,
                style=None,
                **kwargs):
    if style is not None:
        widget.setStyleSheet("* {%s}" % style)
    if layout is not None:
        alignment = getattr(Qt, alignment) if alignment else Qt.Alignment(0)
        layout.addWidget(widget, alignment=alignment)
    if (horizontal, vertical, hstretch, vstretch) is not (None, None, None, None):
        policy = widget.sizePolicy()
        if horizontal is not None:
            policy.setHorizontalPolicy(getattr(QSizePolicy, horizontal))
        if hstretch is not None:
            policy.setHorizontalStretch(int(hstretch))
        if vstretch is not None:
            policy.setVerticalStretch(int(vstretch))
        if vertical is not None:
            policy.setVerticalPolicy(getattr(QSizePolicy, vertical))
        widget.setSizePolicy(policy)
    if size is not None:
        qsize = QSize(*size)
        if __debug__:
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
    try:
       return kwargs["version"]
    except KeyError:
        raise errors.TagError("missing version number in <report>")


def _section(spacing=0,
          margins=(0,0,0,0),
          name=None,
          child_layout="col",
          style="font-size: 10pt",
          metadata=None,
          **kwargs):
    """
    Section is a container of contents of the same context, a section contains
    a default layout (see special handling in `parse` function).
    Section start in a new page and continue until all contents are written.
    """
    section = QWidget()
    section.setStyleSheet("* {%s}" % style)
    col_name = name+"_layout" if name is not None else None
    layouts = {"col": _col, "row": _row}
    section.metadata = metadata
    try:
        _layout = layouts[child_layout]
    except KeyError:
        msg = "Invalid value %r for `child_layout` at line %s, use %s"
        raise errors.TagError(msg % (child_layout,  kwargs['line'], "|".join(layouts.keys())))
    _layout(spacing=spacing, margins=margins, name=col_name, widget=section, **kwargs)
    return section


def _col(spacing=0,
         margins=(0,0,0,0),
         name="col",
         widget=None,
         layout=None,
         **kwargs):
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
                parent_layout=layout,
                **kwargs)
    return vlayout


def _row(spacing=0,
         margins=(0,0,0,0),
         name="row",
         widget=None,
         layout=None,
         **kwargs):
    """
    Horizontal layout, see _col for details
    """
    hlayout = QHBoxLayout()
    _set_layout(hlayout,
                widget=widget,
                spacing=spacing,
                margins=margins,
                name=name,
                parent_layout=layout,
                **kwargs)
    return hlayout


def _label(widget=None,
           layout=None,
           horizontal="Ignored",
           vertical="Maximum",
           word_wrap="False",
           name="label",
           **kwargs):
    """
    Single line text in the layout
    """
    label = QLabel()
    word_wrap = word_wrap == "True"
    label.setWordWrap(word_wrap)
    _set_widget(label,
                layout=layout,
                parent=widget,
                horizontal=horizontal,
                vertical=vertical,
                name=name,
                **kwargs)
    return label


class TextViewer(QWidget):
    def __init__(self, page, *args, **kwargs):
        self.page = page

        super(TextViewer, self).__init__(*args, **kwargs)
        self._document = QTextDocument(self)
        self._document.setUseDesignMetrics(True)
        self._page_number = 0
        self.__offset_top = 0
    def document(self):
        return self._document
    def setHtml(self, html):
        self._html = html
        self._updateHtml()
    def _offset_top(self):
        # FIXME the top offset is only on the first page, but this is ugly
        if self._page_number == 0:
            self.__offset_top = self.page.height() - self.height()
        return self.__offset_top
    def _updateHtml(self):
        css = textwrap.dedent("""
        <style type="text/css">
            tr.header {background: #BBB}
            tr.even {background: #CCC}
            tr.odd {background: #FFF}
            div.markdown {margin-top: %(margin)dpx}
        </style>
        """).strip()
        # make room for the "header" widgets
        css = css % {"margin": self._offset_top()}
        # print("css = %s" % css)
        html = '%s\n<div class="markdown">%s<span>' % (css, self._html)
        # print("setHtml <- %s" % html)
        self._document.setDefaultFont(self.font())
        self._document.setHtml(html)
    def resizeEvent(self, resize_event):
        size = self.page.size()
        #print("setPageSize <- %s" % size)
        #old_size = self._document.pageSize()
        new_size = QSizeF(size.width(), size.height())
        self._document.setPageSize(new_size)
        #print("self.size = %s" % self.size())
        self._updateHtml()
    def paintEvent(self, paint_event):
        painter = QPainter(self)
        if self._page_number == 0:
            painter.setClipRect(QRectF(0, 0, self.page.width(), self.page.height()-self._offset_top()))
            painter.translate(0, -self._offset_top())
        else:
            painter.setClipRect(QRectF(0, 0, self.page.width(), self.page.height()))
            height = self.page.height()
            painter.translate(0, -self._page_number*height)
        self._document.drawContents(painter)
    def pageCount(self):
        return self._document.pageCount()
    def setPageNumber(self, num):
        print("setPageNumber <- %s" % num)
        self._page_number = num
        self.update()
    def pageNumber(self):
        return self._page_number


def _text(widget=None,
          layout=None,
          horizontal="MinimumExpanding",
          vertical="Maximum",
          name="text",
          **kwargs):
    """
    Multiline markdown formatted text in the layout
    """
    text = TextViewer(widget)
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
           name="hline",
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
           name="vline",
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
    def __init__(self, src, env, line, *args, **kwargs):
        super(AspectRatioSvgWidget, self).__init__(*args, **kwargs)
        policy = self.sizePolicy()
        self.setSizePolicy(policy)
        if src.startswith("data://"):
            if env is None:
                raise errors.TagError("Cannot use data:// without `env`")
            multikey = src[len("data://"):]
            keys = multikey.split(":")
            # data://preview:ID -> env["preview"][ID]
            data = env
            for key in keys:
                try:
                    data = data[key]
                except KeyError as err:
                    raise errors.ParseError("%s: parsing %s at line %s" % (err, src, line))
            self.load(QByteArray(data))
        else:
            self.load(src)
        if not self.renderer().isValid():
            raise errors.TagError("Invalid svg in src='%s' at line %s" % (src, line))

    def paintEvent(self, paint_event):
        painter = QPainter(self)
        view_box = self.renderer().viewBox()

        default_width, default_height = view_box.width(), view_box.height()
        if default_width == 0 or default_height == 0:
            print("WARNING: 0x0 image")
            return

        svg_width, svg_height = view_box.width(), view_box.height()
        widget_size = self.size()
        widget_width, widget_height = widget_size.width(), widget_size.height()
        ratio_x = widget_width / svg_width
        ratio_y = widget_height / svg_height
        new_top = 0
        new_left = 0
        new_width = widget_width
        new_height = widget_height
        if ratio_x < ratio_y:
            new_height = widget_width * svg_height / svg_width
            new_top = (widget_height - new_height) / 2
        else:
            new_width = widget_height * svg_width / svg_height
            new_left = (widget_width - new_width) / 2
        new_rect = QRectF(new_left, new_top, new_width, new_height)
        self.renderer().render(painter, new_rect)


def _svg(src="",
         widget=None,
         layout=None,
         horizontal="Preferred",
         vertical="Preferred",
         name="svg",
         **kwargs):
    """
    Svg tag, provide a pointer to a valid svg file
    """
    try:
        svg = AspectRatioSvgWidget(src, kwargs["env"], kwargs['line'])
    except (errors.TagError, errors.ParseError):
        error_svg = b"""
                    <svg>
                    <rect width="100%" height="100%" fill='white' stroke="red" stroke-width="1"/>
                    <text fill="red" font-size="8" font-family="Verdana" x="30%" y="45%">
                    Error: Missing svg
                    </text>
                    </svg>"""
        svg = QSvgWidget()
        svg.load(QByteArray(error_svg))

    _set_widget(svg,
                layout=layout,
                parent=widget,
                horizontal=horizontal,
                vertical=vertical,
                name=name,
                **kwargs)
    # svg.setStyleSheet("SvgPlaceholder { background: yellow }")
    return svg


def _image(src="",
           widget=None,
           layout=None,
           width=None,
           height=None,
           horizontal="Preferred",
           vertical="MinimumExpanding",
           name="image",
           **kwargs):
    """
    Image tag, provide a pointer to a valid image file
    """
    pixmap = QPixmap(src)
    if width is not None and height is not None:
        pixmap = pixmap.scaled(int(width), int(height), transformMode=Qt.SmoothTransformation)
    elif width is not None:
        pixmap = pixmap.scaledToWidth(int(width), mode=Qt.SmoothTransformation)
    elif height is not None:
        pixmap = pixmap.scaledToHeight(int(height), mode=Qt.SmoothTransformation)

    image = QLabel()
    if pixmap.isNull():
        import os
        if os.path.exists(src):
            image.setText(os.path.basename(src))
        else:
            image.setText("")
    else:
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

def _parse_spacing(value, line):
    try:
        return int(value)
    except:
        raise errors.ParseError("Invalid value %r for `spacing` at line %s, provide a valid number" % (value, line))

def _parse_margins(value, line):
    try:
        return tuple(int(v.strip()) for v in value.strip("()").split(","))
    except:
        raise errors.ParseError("Invalid value %r for `margins` at line %s, provide 4 comma separated numbers, es. (3,3,4,4)" % (value, line))

def _parse_size(value, line):
    try:
        return tuple(int(v.strip()) for v in value.strip("()").split(","))
    except:
        raise errors.ParseError("Invalid value %r for `size` at line %s, provide 2 comma separated numbers, es. (300,400)" % (value, line))

def _parse_line_width(value, line):
    try:
        return int(value.strip())
    except:
        raise errors.ParseError("Invalid value %r for `line_width` at line %s, provide a valid numbers" % (value, line))

def _parse_color(value, line):
    try:
        return QColor(value)
    except:
        raise errors.ParseError("Invalid color %r at line %s, provide a valid QColor" % (value, line))

if __debug__:
    def _parse_src(value, line):
        if value.startswith("data://"):
            # postpone check, needs `env`
            # FIXME: spostare il check qua invece che in AspectRatioSvgWidget?
            # se lo converto qua in QByteArray nella classe faccio sempre solo la load
            pass
        else:
            import os
            if not os.path.exists(value):
                print("'%s' at line %s does not exist" % (value, line))
        return value

# Markdown helpers

class QTextEditRenderer(mistune.Renderer):
    """
    QTextEdit targetted renderer with:

    - full width tables
    - odd / even rows
    - use cell `align` attribute instead of `style`
    """
    def __init__(self, *args, **kwargs):
        super(QTextEditRenderer, self).__init__(*args, **kwargs)
        self._even_odd = False
    def table(self, header, body):
        out = super(QTextEditRenderer, self).table(header, body)
        return out.replace("<table>", '<table width="100%">', 1)
    def table_row(self, content):
        out = super(QTextEditRenderer, self).table_row(content)
        if content.strip().startswith("<th>"):
            cls = 'class="header"'
        else:
            cls = 'class="even"' if self._even_odd else 'class="odd"'
            self._even_odd = not self._even_odd
        out = out.replace("<tr>", "<tr %s>" % cls, 1)
        return out
    def table_cell(self, content, **flags):
        if flags['header']:
            tag = 'th'
        else:
            tag = 'td'
        align = flags['align']
        if not align:
            return '<%s>%s</%s>\n' % (tag, content, tag)
        return '<%s align="%s">%s</%s>\n' % (tag, align, content, tag)

# Entrypoint

def parse(source, env=None):
    p = xml.parsers.expat.ParserCreate()
    if isinstance(source, string_types):
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
                    try:
                        kwargs[attr] = parsers[attr](kwargs[attr], line=p.ErrorLineNumber)
                    except ValueError as v:
                        raise errors.ParseError("error parsing %s: %s" % (attr, v))

            if widgets:
                kwargs["widget"] = widgets[-1]
            if layouts:
                kwargs["layout"] = layouts[-1]

            if tag == "svg":
                kwargs["env"] = env

            # def nfw(w):
            #     if isinstance(w, QObject):
            #         return "<name=%s>" % w.objectName()
            #     else:
            #         return w
            # named_args = tuple(nfw(a) for a in args)
            # named_kwargs = {k: nfw(kwargs[k]) for k in kwargs}
            # print("%s %s %s)" % ("  "*len(tags), named_args, named_kwargs))

            # print("_%s(*%r, **%r)" % (tag, args, kwargs))
            obj = hook(line=p.ErrorLineNumber, *args, **kwargs)
            if tag == "report":
                if __debug__:
                    print("this template use version %s" % obj)
            elif tag in ("col", "row"):
                layouts.append(obj)
            else:
                if tag == "section":
                    pages.append(obj)
                    layouts.append(obj.layout())
                widgets.append(obj)
        return f

    def start_element(tag, attrs):
        tags.append(tag)
        # print("%s<%s>" % ("  "*len(tags), tag))
        x(tag)(**attrs)

    def end_element(tag):
        if tag == "text":
            if buffers["text"]:
                widget = widgets[-1] if widgets else None
                if isinstance(widget, TextViewer):
                    text = textwrap.dedent("".join(buffers["text"])).strip()
                    # default bbcode parser change \n with <br> we force it to \n to avoid changes
                    # 'raplace_cosmetic' change symbols into ascii code for html and we don't want that too
                    bbcode.g_parser = bbcode.Parser(newline='\n', replace_cosmetic=False)
                    code = bbcode.render_html(text)
                    html = mistune.Markdown(QTextEditRenderer())(code)
                    widget.setHtml(html)
            buffers["text"] = []
        elif tag == "label":
            if buffers["label"]:
                widget = widgets[-1] if widgets else None
                if isinstance(widget, QLabel):
                    text = "".join(buffers["label"]).strip()
                    text = mistune.markdown(text)
                    widget.setText(text.strip())
            buffers["label"] = []

        if tag == "report":
            pass
        elif tag in ("col", "row"):
            layouts.pop()
        else:
            if tag == "section":
                layouts.pop()
            widgets.pop()
        # print("%s</%s>" % ("  "*len(tags), tag))
        popped_name = tags.pop()
        assert popped_name == tag, (popped_name, tag)

    def char_data(data):
        tag = tags[-1] if tags else None
        if tag in buffers:
            buffers[tag] += [data]

    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data

    _parse(source)

    return pages


# Command line

def demo(template):
    from os.path import dirname, basename

    app = QApplication([])

    template_dir = dirname(template)
    os.chdir(template_dir)
    pages = parse(open(basename(template)))
    page = pages[0]

    page.show()

    return app.exec_()


if __name__ == '__main__':
    import sys
    if sys.argv[1:] and os.path.exists(sys.argv[1]):
        template = os.path.abspath(sys.argv[1])
        print("Parsing template %s" % template)
        demo(template)
    else:
        print("Provide a wreport template")
