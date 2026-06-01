from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QLabel,
    QSizePolicy, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen

from .utils import _get_fastboot_path, _run_command


class DeviceListPopup(QWidget):
    """Popup for selecting up to 4 devices."""

    def __init__(self, parent, all_devices, selected_devices, on_selection_changed):
        super().__init__(parent, Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._tip_label = QLabel("⚡ 最多可同时选择 4 台设备 (实时生效)")
        self._tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tip_label.setStyleSheet("color: #666; font-size: 12px; padding: 2px;")
        layout.addWidget(self._tip_label)

        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 12px;
                min-height: 30px;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: rgba(224, 224, 224, 200);
            }
            QListWidget::item:hover {
                background-color: rgba(224, 224, 224, 150);
            }
        """)

        self._last_valid = list(selected_devices)
        self._on_selection_changed = on_selection_changed

        for device in all_devices:
            item = QListWidgetItem(device)
            self._list_widget.addItem(item)
            if device in selected_devices:
                item.setSelected(True)

        self._list_widget.itemSelectionChanged.connect(self._handle_selection)
        layout.addWidget(self._list_widget)

        item_height = self._list_widget.sizeHintForRow(0) if self._list_widget.count() > 0 else 30
        visible_items = min(self._list_widget.count(), 5)
        self._list_widget.setFixedHeight(item_height * visible_items + 4)
        self.setMaximumHeight(400)

    def _handle_selection(self):
        selected = [item.text() for item in self._list_widget.selectedItems()]
        if len(selected) > 4:
            for i in range(self._list_widget.count()):
                item = self._list_widget.item(i)
                item.setSelected(item.text() in self._last_valid)
            self._tip_label.setText("⚠️ 最多只能选择 4 台设备！")
            self._tip_label.setStyleSheet("color: red; font-size: 12px; padding: 2px;")
            QTimer.singleShot(1500, lambda: (
                self._tip_label.setText("⚡ 最多可同时选择 4 台设备 (实时生效)"),
                self._tip_label.setStyleSheet("color: #666; font-size: 12px; padding: 2px;")
            ))
        else:
            self._last_valid = list(selected)
            self._on_selection_changed(selected)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
        painter.drawRect(self.rect())


def build_device_panels(container_layout, selected_devices, device_logs, device_log_buffers,
                        get_button_style, reboot_callback, adb_path_func):
    """Build per-device log panels with reboot buttons. Returns updated device_logs dict."""
    device_logs.clear()
    while container_layout.count():
        item = container_layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()

    fastboot = _get_fastboot_path()

    for device_sn in selected_devices:
        wrapper = QVBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.setSpacing(4)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlaceholderText(f"{device_sn} 的日志输出...")
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 140);
                border: 1px solid #39C5BB;
                color: #333;
                font-size: 12px;
                border-radius: 0px;
            }
        """)
        text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        wrapper.addWidget(text_edit, 1)
        device_logs[device_sn] = text_edit

        reboot_btn = QPushButton(f"重启 {device_sn}")
        reboot_btn.setFixedHeight(28)
        reboot_btn.setStyleSheet(get_button_style())
        reboot_btn.clicked.connect(lambda checked, sn=device_sn: reboot_callback(sn, fastboot, adb_path_func()))
        wrapper.addWidget(reboot_btn)

        wrap_widget = QWidget()
        wrap_widget.setLayout(wrapper)
        container_layout.addWidget(wrap_widget)

        if device_sn in device_log_buffers:
            for msg in device_log_buffers[device_sn]:
                text_edit.append(msg)
            del device_log_buffers[device_sn]

    return device_logs


def get_fastboot_devices():
    """Get devices currently in fastboot mode."""
    fastboot = _get_fastboot_path()
    if not fastboot:
        return []
    try:
        rc, out, err = _run_command([fastboot, 'devices'], timeout=10)
        if rc != 0:
            return []
        devices = []
        for line in out.strip().split('\n'):
            line = line.strip()
            if line and '\t' in line:
                sn = line.split('\t')[0].strip()
                if sn:
                    devices.append(sn)
        return devices
    except Exception:
        return []
