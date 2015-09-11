#!/usr/bin/env python2
# encoding: utf-8


from PyQt4.Qt import *



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

def _page(name=None, size=(600, 900)):
    page = QWidget()
    _set_object(page, name=name)
    page.resize(600, 900)
    return page

def _vlayout(spacing=0,
             margins=(0,0,0,0),
             name=None,
             widget=None,
             parent_layout=None):
    layout = QVBoxLayout()
    _set_layout(layout,
                widget=widget,
                spacing=spacing,
                margins=margins,
                name=name,
                parent_layout=parent_layout)
    return layout

def _hlayout(spacing=0,
             margins=(0,0,0,0),
             name=None,
             widget=None,
             parent_layout=None):
    layout = QHBoxLayout()
    _set_layout(layout,
                widget=widget,
                spacing=spacing,
                margins=margins,
                name=name,
                parent_layout=parent_layout)
    return layout


def _label(text,
           parent=None,
           layout=None,
           width="Ignored",
           height="Maximum",
           name=None):
    label = QLabel(text)
    _set_widget(label,
                layout=layout,
                parent=parent,
                width=width,
                height=height,
                name=name)
    return label

class QImagePlaceholder(QWidget):
    def __init__(self, src, *args, **kwargs):
        self.src = src
        super(QImagePlaceholder, self).__init__(*args, **kwargs)

def _image(src,
           parent=None,
           layout=None,
           width="Preferred",
           height="MinimumExpanding",
           name=None):
    widget = QImagePlaceholder(src)
    _set_widget(widget,
                layout=layout,
                parent=parent,
                width=width,
                height=height,
                name=name)
    widget.setStyleSheet("QImagePlaceholder { background: yellow }")
    return widget

def main(args):
    app = QApplication(args)

    page = _page()
    page_layout = _vlayout(name="page_layout", widget=page)
    header_layout = _hlayout(name="header_layout", widget=page, parent_layout=page_layout)
    col1 = _label("Some text", parent=page, layout=header_layout)
    col2 = _label("Other text", parent=page, layout=header_layout)
    col3 = _label("Even other text", parent=page, layout=header_layout)
    image = _image(src="some.svg", parent=page, layout=page_layout)
    footer = _label("Footer", parent=page, layout=page_layout)

    page.show()

    return app.exec_()



if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
