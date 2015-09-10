#include "reportpreview.h"
#include "ui_reportpreview.h"

ReportPreview::ReportPreview(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::ReportPreview)
{
    ui->setupUi(this);
}

ReportPreview::~ReportPreview()
{
    delete ui;
}
