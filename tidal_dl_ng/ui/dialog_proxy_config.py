# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_proxy_config.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_DialogProxyConfig(object):
    def setupUi(self, DialogProxyConfig):
        if not DialogProxyConfig.objectName():
            DialogProxyConfig.setObjectName(u"DialogProxyConfig")
        DialogProxyConfig.resize(500, 400)
        DialogProxyConfig.setModal(True)
        self.verticalLayout = QVBoxLayout(DialogProxyConfig)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.l_title = QLabel(DialogProxyConfig)
        self.l_title.setObjectName(u"l_title")

        self.verticalLayout.addWidget(self.l_title)

        self.l_description = QLabel(DialogProxyConfig)
        self.l_description.setObjectName(u"l_description")
        self.l_description.setWordWrap(True)

        self.verticalLayout.addWidget(self.l_description)

        self.line = QFrame(DialogProxyConfig)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.cb_enable_proxy = QCheckBox(DialogProxyConfig)
        self.cb_enable_proxy.setObjectName(u"cb_enable_proxy")
        self.cb_enable_proxy.setChecked(False)

        self.verticalLayout.addWidget(self.cb_enable_proxy)

        self.gb_proxy_settings = QGroupBox(DialogProxyConfig)
        self.gb_proxy_settings.setObjectName(u"gb_proxy_settings")
        self.gb_proxy_settings.setEnabled(False)
        self.formLayout = QFormLayout(self.gb_proxy_settings)
        self.formLayout.setObjectName(u"formLayout")
        self.l_proxy_type = QLabel(self.gb_proxy_settings)
        self.l_proxy_type.setObjectName(u"l_proxy_type")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.l_proxy_type)

        self.cb_proxy_type = QComboBox(self.gb_proxy_settings)
        self.cb_proxy_type.addItem("")
        self.cb_proxy_type.addItem("")
        self.cb_proxy_type.addItem("")
        self.cb_proxy_type.setObjectName(u"cb_proxy_type")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.cb_proxy_type)

        self.l_proxy_host = QLabel(self.gb_proxy_settings)
        self.l_proxy_host.setObjectName(u"l_proxy_host")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.l_proxy_host)

        self.le_proxy_host = QLineEdit(self.gb_proxy_settings)
        self.le_proxy_host.setObjectName(u"le_proxy_host")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.le_proxy_host)

        self.l_proxy_port = QLabel(self.gb_proxy_settings)
        self.l_proxy_port.setObjectName(u"l_proxy_port")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.l_proxy_port)

        self.sb_proxy_port = QSpinBox(self.gb_proxy_settings)
        self.sb_proxy_port.setObjectName(u"sb_proxy_port")
        self.sb_proxy_port.setMinimum(1)
        self.sb_proxy_port.setMaximum(65535)
        self.sb_proxy_port.setValue(8080)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.sb_proxy_port)

        self.l_proxy_username = QLabel(self.gb_proxy_settings)
        self.l_proxy_username.setObjectName(u"l_proxy_username")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.l_proxy_username)

        self.le_proxy_username = QLineEdit(self.gb_proxy_settings)
        self.le_proxy_username.setObjectName(u"le_proxy_username")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.le_proxy_username)

        self.l_proxy_password = QLabel(self.gb_proxy_settings)
        self.l_proxy_password.setObjectName(u"l_proxy_password")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.l_proxy_password)

        self.le_proxy_password = QLineEdit(self.gb_proxy_settings)
        self.le_proxy_password.setObjectName(u"le_proxy_password")
        self.le_proxy_password.setEchoMode(QLineEdit.Password)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.le_proxy_password)


        self.verticalLayout.addWidget(self.gb_proxy_settings)

        self.hl_test_connection = QHBoxLayout()
        self.hl_test_connection.setObjectName(u"hl_test_connection")
        self.pb_test_connection = QPushButton(DialogProxyConfig)
        self.pb_test_connection.setObjectName(u"pb_test_connection")
        self.pb_test_connection.setEnabled(False)

        self.hl_test_connection.addWidget(self.pb_test_connection)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_test_connection.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.hl_test_connection)

        self.te_status = QTextEdit(DialogProxyConfig)
        self.te_status.setObjectName(u"te_status")
        self.te_status.setMaximumSize(QSize(16777215, 80))
        self.te_status.setReadOnly(True)

        self.verticalLayout.addWidget(self.te_status)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.line_2 = QFrame(DialogProxyConfig)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_2)

        self.hl_buttons = QHBoxLayout()
        self.hl_buttons.setObjectName(u"hl_buttons")
        self.pb_skip = QPushButton(DialogProxyConfig)
        self.pb_skip.setObjectName(u"pb_skip")

        self.hl_buttons.addWidget(self.pb_skip)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_buttons.addItem(self.horizontalSpacer_2)

        self.pb_cancel = QPushButton(DialogProxyConfig)
        self.pb_cancel.setObjectName(u"pb_cancel")

        self.hl_buttons.addWidget(self.pb_cancel)

        self.pb_save = QPushButton(DialogProxyConfig)
        self.pb_save.setObjectName(u"pb_save")

        self.hl_buttons.addWidget(self.pb_save)


        self.verticalLayout.addLayout(self.hl_buttons)


        self.retranslateUi(DialogProxyConfig)
        self.cb_enable_proxy.toggled.connect(self.gb_proxy_settings.setEnabled)
        self.cb_enable_proxy.toggled.connect(self.pb_test_connection.setEnabled)

        self.pb_save.setDefault(True)


        QMetaObject.connectSlotsByName(DialogProxyConfig)
    # setupUi

    def retranslateUi(self, DialogProxyConfig):
        DialogProxyConfig.setWindowTitle(QCoreApplication.translate("DialogProxyConfig", u"Proxy Configuration", None))
        self.l_title.setText(QCoreApplication.translate("DialogProxyConfig", u"<html><head/><body><p><span style=\" font-size:14pt; font-weight:600;\">Proxy Configuration</span></p></body></html>", None))
        self.l_description.setText(QCoreApplication.translate("DialogProxyConfig", u"Configure proxy settings for TIDAL authentication and downloads. This ensures complete location masking for all TIDAL communication.", None))
        self.cb_enable_proxy.setText(QCoreApplication.translate("DialogProxyConfig", u"Enable Proxy", None))
        self.gb_proxy_settings.setTitle(QCoreApplication.translate("DialogProxyConfig", u"Proxy Settings", None))
        self.l_proxy_type.setText(QCoreApplication.translate("DialogProxyConfig", u"Proxy Type:", None))
        self.cb_proxy_type.setItemText(0, QCoreApplication.translate("DialogProxyConfig", u"HTTP", None))
        self.cb_proxy_type.setItemText(1, QCoreApplication.translate("DialogProxyConfig", u"HTTPS", None))
        self.cb_proxy_type.setItemText(2, QCoreApplication.translate("DialogProxyConfig", u"SOCKS5", None))

        self.l_proxy_host.setText(QCoreApplication.translate("DialogProxyConfig", u"Host:", None))
        self.le_proxy_host.setPlaceholderText(QCoreApplication.translate("DialogProxyConfig", u"proxy.example.com", None))
        self.l_proxy_port.setText(QCoreApplication.translate("DialogProxyConfig", u"Port:", None))
        self.l_proxy_username.setText(QCoreApplication.translate("DialogProxyConfig", u"Username (optional):", None))
        self.le_proxy_username.setPlaceholderText(QCoreApplication.translate("DialogProxyConfig", u"Leave empty if no authentication required", None))
        self.l_proxy_password.setText(QCoreApplication.translate("DialogProxyConfig", u"Password (optional):", None))
        self.le_proxy_password.setPlaceholderText(QCoreApplication.translate("DialogProxyConfig", u"Leave empty if no authentication required", None))
        self.pb_test_connection.setText(QCoreApplication.translate("DialogProxyConfig", u"Test Connection", None))
        self.te_status.setHtml(QCoreApplication.translate("DialogProxyConfig", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#666666;\">Status information will appear here...</span></p></body></html>", None))
        self.pb_skip.setText(QCoreApplication.translate("DialogProxyConfig", u"Skip (Use Direct Connection)", None))
        self.pb_cancel.setText(QCoreApplication.translate("DialogProxyConfig", u"Cancel", None))
        self.pb_save.setText(QCoreApplication.translate("DialogProxyConfig", u"Save && Continue", None))
    # retranslateUi

