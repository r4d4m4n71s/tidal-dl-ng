import datetime
import os.path
import shutil
import webbrowser
from enum import Enum, StrEnum
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
from tidalapi import Quality as QualityAudio

from tidal_dl_ng import __version__
from tidal_dl_ng.config import Settings
from tidal_dl_ng.constants import CoverDimensions, QualityVideo
from tidal_dl_ng.model.cfg import HelpSettings
from tidal_dl_ng.model.cfg import Settings as ModelSettings
from tidal_dl_ng.model.meta import ReleaseLatest
from tidal_dl_ng.ui.dialog_login import Ui_DialogLogin
from tidal_dl_ng.ui.dialog_proxy_config import Ui_DialogProxyConfig
from tidal_dl_ng.ui.dialog_settings import Ui_DialogSettings
from tidal_dl_ng.ui.dialog_version import Ui_DialogVersion


class DialogVersion(QtWidgets.QDialog):
    """Version dialog."""

    ui: Ui_DialogVersion

    def __init__(
        self, parent=None, update_check: bool = False, update_available: bool = False, update_info: ReleaseLatest = None
    ):
        super().__init__(parent)

        # Create an instance of the GUI
        self.ui = Ui_DialogVersion()

        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        # Set the version.
        self.ui.l_version.setText("v" + __version__)

        if not update_check:
            self.update_info_hide()
            self.error_hide()
        else:
            self.update_info(update_available, update_info)

        # Show
        self.exec()

    def update_info(self, update_available: bool, update_info: ReleaseLatest):
        if not update_available and update_info.version == "v0.0.0":
            self.update_info_hide()
            self.ui.l_error_details.setText(
                "Cannot retrieve update information. Maybe something is wrong with your internet connection."
            )
        else:
            self.error_hide()

            if not update_available:
                self.ui.l_h_version_new.setText("Latest available version:")
                self.changelog_hide()
            else:
                self.ui.l_changelog_details.setText(update_info.release_info)
                self.ui.pb_download.clicked.connect(lambda: webbrowser.open(update_info.url))

            self.ui.l_version_new.setText(update_info.version)

    def error_hide(self):
        self.ui.l_error.setHidden(True)
        self.ui.l_error_details.setHidden(True)

    def update_info_hide(self):
        self.ui.l_h_version_new.setHidden(True)
        self.ui.l_version_new.setHidden(True)
        self.changelog_hide()

    def changelog_hide(self):
        self.ui.l_changelog.setHidden(True)
        self.ui.l_changelog_details.setHidden(True)
        self.ui.pb_download.setHidden(True)


class DialogLogin(QtWidgets.QDialog):
    """Version dialog."""

    ui: Ui_DialogLogin
    url_redirect: str

    def __init__(self, url_login: str, hint: str, expires_in: int, parent=None):
        super().__init__(parent)

        datetime_current: datetime.datetime = datetime.datetime.now()
        datetime_expires: datetime.datetime = datetime_current + datetime.timedelta(0, expires_in)

        # Create an instance of the GUI
        self.ui = Ui_DialogLogin()

        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        # Set data.
        self.ui.tb_url_login.setText(f'<a href="https://{url_login}">https://{url_login}</a>')
        self.ui.l_hint.setText(hint)
        self.ui.l_expires_date_time.setText(datetime_expires.strftime("%Y-%m-%d %H:%M"))
        # Show
        self.return_code = self.exec()


class DialogPreferences(QtWidgets.QDialog):
    """Preferences dialog."""

    ui: Ui_DialogSettings
    settings: Settings
    data: ModelSettings
    s_settings_save: QtCore.Signal
    icon: QtGui.QIcon
    help_settings: HelpSettings
    parameters_checkboxes: [str]
    parameters_combo: [(str, StrEnum)]
    parameters_line_edit: [str]
    parameters_spin_box: [str]
    prefix_checkbox: str = "cb_"
    prefix_label: str = "l_"
    prefix_icon: str = "icon_"
    prefix_line_edit: str = "le_"
    prefix_combo: str = "c_"
    prefix_spin_box: str = "sb_"

    def __init__(self, settings: Settings, settings_save: QtCore.Signal, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.data = settings.data
        self.s_settings_save = settings_save
        self.help_settings = HelpSettings()
        pixmapi: QtWidgets.QStyle.StandardPixmap = QtWidgets.QStyle.SP_MessageBoxQuestion
        self.icon = self.style().standardIcon(pixmapi)

        self._init_checkboxes()
        self._init_comboboxes()
        self._init_line_edit()
        self._init_spin_box()

        # Create an instance of the GUI
        self.ui = Ui_DialogSettings()

        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        # Set data.
        self.gui_populate()
        # Post setup

        self.exec()

    def _init_line_edit(self):
        self.parameters_line_edit = [
            "download_base_path",
            "format_album",
            "format_playlist",
            "format_mix",
            "format_track",
            "format_video",
            "path_binary_ffmpeg",
        ]

    def _init_spin_box(self):
        self.parameters_spin_box = ["album_track_num_pad_min", "downloads_concurrent_max"]

    def _init_comboboxes(self):
        self.parameters_combo = [
            ("quality_audio", QualityAudio),
            ("quality_video", QualityVideo),
            ("metadata_cover_dimension", CoverDimensions),
        ]

    def _init_checkboxes(self):
        self.parameters_checkboxes = [
            "lyrics_embed",
            "lyrics_file",
            "video_download",
            "download_delay",
            "video_convert_mp4",
            "extract_flac",
            "metadata_cover_embed",
            "cover_album_file",
            "skip_existing",
            "symlink_to_track",
            "playlist_create",
        ]

    def gui_populate(self):
        self.populate_checkboxes()
        self.populate_combo()
        self.populate_line_edit()
        self.populate_spin_box()

    def dialog_chose_file(
        self,
        obj_line_edit: QtWidgets.QLineEdit,
        file_mode: QtWidgets.QFileDialog | QtWidgets.QFileDialog.FileMode = QtWidgets.QFileDialog.Directory,
        path_default: str = None,
    ):
        # If a path is set, use it otherwise the users home directory.
        path_settings: str = os.path.expanduser(obj_line_edit.text()) if obj_line_edit.text() else ""
        # Check if obj_line_edit is empty but path_default can be usd instead
        path_settings = (
            path_settings if path_settings else os.path.expanduser(path_default) if path_default else path_settings
        )
        dir_current: str = path_settings if path_settings and os.path.exists(path_settings) else str(Path.home())
        dialog: QtWidgets.QFileDialog = QtWidgets.QFileDialog()

        # Set to directory mode only but show files.
        dialog.setFileMode(file_mode)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, False)
        dialog.setOption(QtWidgets.QFileDialog.DontResolveSymlinks, True)

        # There is a bug in the PyQt implementation, which hides files in Directory mode.
        # Thus, we need to use the PyQt dialog instead of the native dialog.
        if os.name == "nt" and file_mode == QtWidgets.QFileDialog.Directory:
            dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)

        dialog.setDirectory(dir_current)

        # Execute dialog and set path is something is choosen.
        if dialog.exec():
            dir_name: str = dialog.selectedFiles()[0]
            path: Path = Path(dir_name)
            obj_line_edit.setText(str(path))

    def populate_line_edit(self):
        for pn in self.parameters_line_edit:
            label_icon: QtWidgets.QLabel = getattr(self.ui, self.prefix_label + self.prefix_icon + pn)
            label: QtWidgets.QLabel = getattr(self.ui, self.prefix_label + pn)
            line_edit: QtWidgets.QLineEdit = getattr(self.ui, self.prefix_line_edit + pn)

            label_icon.setPixmap(QtGui.QPixmap(self.icon.pixmap(QtCore.QSize(16, 16))))
            label_icon.setToolTip(getattr(self.help_settings, pn))
            label.setText(pn)
            line_edit.setText(str(getattr(self.data, pn)))

        # Base Path File Dialog
        self.ui.pb_download_base_path.clicked.connect(lambda x: self.dialog_chose_file(self.ui.le_download_base_path))
        self.ui.pb_path_binary_ffmpeg.clicked.connect(
            lambda x: self.dialog_chose_file(
                self.ui.le_path_binary_ffmpeg,
                file_mode=QtWidgets.QFileDialog.FileMode.ExistingFiles,
                path_default=shutil.which("ffmpeg"),
            )
        )

    def populate_combo(self):
        for p in self.parameters_combo:
            pn: str = p[0]
            values: Enum = p[1]
            label_icon: QtWidgets.QLabel = getattr(self.ui, self.prefix_label + self.prefix_icon + pn)
            label: QtWidgets.QLabel = getattr(self.ui, self.prefix_label + pn)
            combo: QtWidgets.QComboBox = getattr(self.ui, self.prefix_combo + pn)
            setting_current = getattr(self.data, pn)

            label_icon.setPixmap(QtGui.QPixmap(self.icon.pixmap(QtCore.QSize(16, 16))))
            label_icon.setToolTip(getattr(self.help_settings, pn))
            label.setText(pn)

            for index, v in enumerate(values):
                combo.addItem(v.name, v)

                if v == setting_current:
                    combo.setCurrentIndex(index)

    def populate_checkboxes(self):
        for pn in self.parameters_checkboxes:
            checkbox: QtWidgets.QCheckBox = getattr(self.ui, self.prefix_checkbox + pn)

            checkbox.setText(pn)
            checkbox.setToolTip(getattr(self.help_settings, pn))
            checkbox.setIcon(self.icon)
            checkbox.setChecked(getattr(self.data, pn))

    def populate_spin_box(self):
        for pn in self.parameters_spin_box:
            label_icon: QtWidgets.QLabel = getattr(self.ui, self.prefix_label + self.prefix_icon + pn)
            label: QtWidgets.QLabel = getattr(self.ui, self.prefix_label + pn)
            spin_box: QtWidgets.QSpinBox = getattr(self.ui, self.prefix_spin_box + pn)

            label_icon.setPixmap(QtGui.QPixmap(self.icon.pixmap(QtCore.QSize(16, 16))))
            label_icon.setToolTip(getattr(self.help_settings, pn))
            label.setText(pn)
            spin_box.setValue(getattr(self.data, pn))

    def accept(self):
        # Get settings.
        self.to_settings()
        self.done(1)

    def to_settings(self):
        for item in self.parameters_checkboxes:
            setattr(self.settings.data, item, getattr(self.ui, self.prefix_checkbox + item).isChecked())

        for item in self.parameters_line_edit:
            setattr(self.settings.data, item, getattr(self.ui, self.prefix_line_edit + item).text())

        for item in self.parameters_combo:
            setattr(self.settings.data, item[0], getattr(self.ui, self.prefix_combo + item[0]).currentData())

        for item in self.parameters_spin_box:
            setattr(self.settings.data, item, getattr(self.ui, self.prefix_spin_box + item).value())

        self.s_settings_save.emit()


class DialogProxyConfig(QtWidgets.QDialog):
    """Proxy configuration dialog."""

    ui: Ui_DialogProxyConfig
    settings: Settings
    result_skip_proxy: bool = False
    result_configured: bool = False

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)

        self.settings = settings
        
        # Create an instance of the GUI
        self.ui = Ui_DialogProxyConfig()

        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        
        # Initialize UI state
        self._init_ui()
        self._connect_signals()
        
        # Load existing proxy settings if any
        self._load_existing_settings()
        
        # Show the dialog
        self.exec()

    def _init_ui(self):
        """Initialize UI state and styling."""
        # Set default proxy type to HTTPS
        self.ui.cb_proxy_type.setCurrentIndex(1)  # HTTPS
        
        # Set initial status message
        self._update_status("Ready to configure proxy settings.", "info")

    def _connect_signals(self):
        """Connect UI signals to handlers."""
        self.ui.pb_test_connection.clicked.connect(self._test_connection)
        self.ui.pb_skip.clicked.connect(self._skip_proxy)
        self.ui.pb_cancel.clicked.connect(self._cancel)
        self.ui.pb_save.clicked.connect(self._save_and_continue)
        
        # Enable/disable form validation on input changes
        self.ui.le_proxy_host.textChanged.connect(self._validate_form)
        self.ui.sb_proxy_port.valueChanged.connect(self._validate_form)
        self.ui.cb_enable_proxy.toggled.connect(self._validate_form)

    def _load_existing_settings(self):
        """Load existing proxy settings into the form."""
        proxy_settings = self.settings.data.proxy_settings
        
        if proxy_settings.enabled and proxy_settings.proxies:
            # Load the first proxy configuration
            proxy = proxy_settings.proxies[0]
            
            self.ui.cb_enable_proxy.setChecked(True)
            self.ui.le_proxy_host.setText(proxy.host)
            self.ui.sb_proxy_port.setValue(proxy.port)
            
            # Set proxy type
            proxy_types = {"http": 0, "https": 1, "socks5": 2}
            if proxy.proxy_type.lower() in proxy_types:
                self.ui.cb_proxy_type.setCurrentIndex(proxy_types[proxy.proxy_type.lower()])
            
            # Set authentication if available
            if proxy.username:
                self.ui.le_proxy_username.setText(proxy.username)
            if proxy.password:
                self.ui.le_proxy_password.setText(proxy.password)

    def _validate_form(self):
        """Validate form inputs and enable/disable buttons accordingly."""
        if not self.ui.cb_enable_proxy.isChecked():
            self.ui.pb_save.setEnabled(True)
            return
        
        host = self.ui.le_proxy_host.text().strip()
        port = self.ui.sb_proxy_port.value()
        
        is_valid = bool(host) and 1 <= port <= 65535
        
        self.ui.pb_save.setEnabled(is_valid)
        self.ui.pb_test_connection.setEnabled(is_valid)

    def _test_connection(self):
        """Test the proxy connection."""
        if not self.ui.cb_enable_proxy.isChecked():
            self._update_status("Proxy is not enabled.", "warning")
            return
        
        # Disable test button during testing
        self.ui.pb_test_connection.setEnabled(False)
        self.ui.pb_test_connection.setText("Testing...")
        
        try:
            # Create proxy configuration from form data
            proxy_config = self._create_proxy_config()
            
            self._update_status("Testing proxy connection...", "info")
            
            # Test the connection
            success, latency, error = proxy_config.test_connection(timeout=10)
            
            if success:
                self._update_status(
                    f"✓ Proxy connection successful! Latency: {latency:.2f}ms", 
                    "success"
                )
            else:
                self._update_status(
                    f"✗ Proxy connection failed: {error}", 
                    "error"
                )
                
        except Exception as e:
            self._update_status(f"✗ Error testing proxy: {str(e)}", "error")
        
        finally:
            # Re-enable test button
            self.ui.pb_test_connection.setEnabled(True)
            self.ui.pb_test_connection.setText("Test Connection")

    def _create_proxy_config(self):
        """Create ProxyConfig from form data."""
        from tidal_dl_ng.proxy import ProxyConfig
        
        proxy_type = self.ui.cb_proxy_type.currentText().lower()
        host = self.ui.le_proxy_host.text().strip()
        port = self.ui.sb_proxy_port.value()
        username = self.ui.le_proxy_username.text().strip() or None
        password = self.ui.le_proxy_password.text().strip() or None
        
        return ProxyConfig(
            name="User Proxy",
            host=host,
            port=port,
            proxy_type=proxy_type,
            username=username,
            password=password,
            protocols=["http", "https"],
            enabled=True,
            priority=1
        )

    def _update_status(self, message: str, status_type: str = "info"):
        """Update the status display with colored message."""
        colors = {
            "info": "#0066cc",
            "success": "#008000", 
            "warning": "#ff8800",
            "error": "#cc0000"
        }
        
        color = colors.get(status_type, colors["info"])
        
        html = f"""
        <html><body style="margin:0; padding:4px;">
        <p style="margin:0; color:{color}; font-weight:bold;">
        {message}
        </p></body></html>
        """
        
        self.ui.te_status.setHtml(html)

    def _skip_proxy(self):
        """Handle skip proxy button click."""
        self.result_skip_proxy = True
        self.result_configured = False
        self._update_status("Skipping proxy configuration. Using direct connection.", "info")
        self.accept()

    def _cancel(self):
        """Handle cancel button click."""
        self.result_skip_proxy = False
        self.result_configured = False
        self.reject()

    def _save_and_continue(self):
        """Handle save and continue button click."""
        try:
            if self.ui.cb_enable_proxy.isChecked():
                # Validate form
                if not self._validate_proxy_settings():
                    return
                
                # Create and save proxy configuration
                proxy_config = self._create_proxy_config()
                
                # Update settings
                self.settings.data.proxy_settings.enabled = True
                self.settings.data.proxy_settings.proxies = [proxy_config]
                
                # Save settings
                self.settings.save()
                
                self.result_configured = True
                self._update_status("✓ Proxy configuration saved successfully!", "success")
            else:
                # User disabled proxy
                self.settings.data.proxy_settings.enabled = False
                self.settings.data.proxy_settings.proxies = []
                self.settings.save()
                
                self.result_skip_proxy = True
                self._update_status("Proxy disabled. Using direct connection.", "info")
            
            self.result_skip_proxy = not self.ui.cb_enable_proxy.isChecked()
            self.accept()
            
        except Exception as e:
            self._update_status(f"✗ Error saving configuration: {str(e)}", "error")

    def _validate_proxy_settings(self) -> bool:
        """Validate proxy settings before saving."""
        host = self.ui.le_proxy_host.text().strip()
        port = self.ui.sb_proxy_port.value()
        
        if not host:
            self._update_status("✗ Proxy host is required.", "error")
            self.ui.le_proxy_host.setFocus()
            return False
        
        if not (1 <= port <= 65535):
            self._update_status("✗ Proxy port must be between 1 and 65535.", "error")
            self.ui.sb_proxy_port.setFocus()
            return False
        
        # Check if username is provided but password is missing (or vice versa)
        username = self.ui.le_proxy_username.text().strip()
        password = self.ui.le_proxy_password.text().strip()
        
        if username and not password:
            self._update_status("✗ Password is required when username is provided.", "error")
            self.ui.le_proxy_password.setFocus()
            return False
        
        if password and not username:
            self._update_status("✗ Username is required when password is provided.", "error")
            self.ui.le_proxy_username.setFocus()
            return False
        
        return True
