#include "reportpreview.h"
#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    ReportPreview w;
    w.show();

    return a.exec();
}
