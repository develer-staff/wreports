#ifndef REPORTPREVIEW_H
#define REPORTPREVIEW_H

#include <QWidget>

namespace Ui {
class ReportPreview;
}

class ReportPreview : public QWidget
{
    Q_OBJECT

public:
    explicit ReportPreview(QWidget *parent = 0);
    ~ReportPreview();

private:
    Ui::ReportPreview *ui;
};

#endif // REPORTPREVIEW_H
