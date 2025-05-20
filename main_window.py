import threading
from time import sleep

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QHBoxLayout, QHeaderView,
    QMessageBox, QAction, QMenuBar, QToolButton, QLabel,
    QDialog, QLineEdit, QDialogButtonBox, QFormLayout, QComboBox,
    QSystemTrayIcon, QMenu
)
from PyQt5.QtGui import QIcon, QCloseEvent
from PyQt5.QtCore import Qt, QSize, QTimer

import database
import monitor


class SortableFilterTable(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Блокировщик внешних устройств")
        self.setWindowIcon(QIcon("icons/main_icon.png"))
        self.resize(1000, 700)

        self.devices_columns_names = ["ID", "Name", "Permission", "Connected"]
        self.components_columns_names = ["Device ID", "IID", "Class", "Name", "Status"]
        self.sort_column = -1
        self.sort_order = Qt.AscendingOrder
        self.monitoring_active = False

        # Пропорции столбцов относительно общей ширины окна
        self.devices_column_ratios = [1, 6, 3, 3]
        self.components_column_ratios = [1, 6, 2, 5, 2]
        self.initial_width = 1600
        self.status = 0
        self.dark_theme_enabled = False
        self.show_devices = True
        self.admin_mode = "Admin"

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        # --- Панель мониторинга ---
        monitor_layout = QHBoxLayout()

        self.start_button = QToolButton()
        self.start_button.setIcon(QIcon("icons/start_monitoring.png"))
        self.start_button.setIconSize(QSize(24, 24))
        self.start_button.setToolTip("Запустить мониторинг")
        self.start_button.clicked.connect(self.start_monitoring)
        monitor_layout.addWidget(self.start_button)

        self.stop_button = QToolButton()
        self.stop_button.setIcon(QIcon("icons/stop_monitoring.png"))
        self.stop_button.setIconSize(QSize(24, 24))
        self.stop_button.setToolTip("Остановить мониторинг")
        self.stop_button.clicked.connect(self.stop_monitoring)
        monitor_layout.addWidget(self.stop_button)

        self.update_button = QToolButton()
        self.update_button.setIcon(QIcon("icons/update_table.png"))
        self.update_button.setIconSize(QSize(24, 24))
        self.update_button.setToolTip("Обновить таблицу")
        self.update_button.clicked.connect(self.update_table)
        monitor_layout.addWidget(self.update_button)

        self.status = QLabel("Статус: остановлено")
        monitor_layout.addWidget(self.status)

        monitor_layout.addStretch()
        main_layout.addLayout(monitor_layout)

        # --- Таблица ---
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #B7B7B7;
                color: white;
            }
        """)
        self.table.setMouseTracking(True)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(self.devices_columns_names)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setMouseTracking(True)
        self.table.horizontalHeader().sectionClicked.connect(self.change_sort)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.viewport().installEventFilter(self)
        self.back_button = QToolButton()
        self.back_button.setIcon(QIcon("icons/back_to_devices.png"))  # убедись, что иконка есть или замени на текст
        self.back_button.setText("Назад")
        self.back_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.back_button.setVisible(False)
        self.back_button.clicked.connect(self.return_to_devices)
        main_layout.addWidget(self.back_button)
        main_layout.addWidget(self.table)

        main_widget.setLayout(main_layout)

        QTimer.singleShot(0, self.update_table)
        self.update_monitor_buttons()

        self.create_menu()

        self.tray_icon = QSystemTrayIcon(QIcon("icons/main_icon.png"), self)
        self.tray_icon.setToolTip("Блокировщик внешних устройств")

        # --- Меню трея ---
        tray_menu = QMenu()

        restore_action = QAction("Развернуть", self)
        restore_action.triggered.connect(self.show_normal_window)
        tray_menu.addAction(restore_action)

        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_clicked)
        self.tray_icon.show()

    def create_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("Данные")
        toggle_action = QAction("Все компоненты/устройства", self)
        toggle_action.triggered.connect(self.toggle_show_devices)
        file_menu.addAction(toggle_action)
        self.log_action = QAction("Лог", self)
        self.log_action.triggered.connect(self.show_log_window)
        file_menu.addAction(self.log_action)

        view_menu = menu_bar.addMenu("Вид")
        theme_action = QAction("Переключить тему", self)
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)

        # Меню администратора
        admin_menu = menu_bar.addMenu("Админ")

        self.admin_login_action = QAction("Режим админа", self)
        self.admin_login_action.triggered.connect(self.show_admin_entrance_dialog)
        admin_menu.addAction(self.admin_login_action)

        self.reset_action = QAction("Сбросить данные", self)
        self.reset_action.triggered.connect(self.reset_table)
        admin_menu.addAction(self.reset_action)

        self.change_pass_action = QAction("Изменить пароль", self)
        self.change_pass_action.triggered.connect(self.show_change_password_dialog)
        admin_menu.addAction(self.change_pass_action)

        help_menu = menu_bar.addMenu("Помощь")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        self.update_admin_actions_visibility()

    def return_to_devices(self):
        self.show_devices = True
        self.resize(1000, 700)
        self.back_button.setVisible(False)
        self.update_table()

    def eventFilter(self, source, event):
        if source == self.table.viewport():
            if event.type() == event.MouseMove:
                index = self.table.indexAt(event.pos())
                if index.isValid():
                    self.table.selectRow(index.row())

            elif event.type() == event.MouseButtonPress:
                index = self.table.indexAt(event.pos())
                if not index.isValid():
                    return super().eventFilter(source, event)

                row = index.row()
                if event.button() == Qt.RightButton:
                    self.open_edit_device_dialog(row)
                elif event.button() == Qt.LeftButton:
                    if not self.show_devices:
                        return super().eventFilter(source, event)  # игнорируем клик, если не в режиме устройств
                    device_id = self.table.item(row, 0).text()
                    if device_id.isdigit():
                        self.show_devices = False
                        self.resize(1600, 700)
                        self.update_table_for_device(int(device_id))

        return super().eventFilter(source, event)

    def handle_row_clicked(self, row):
        if not self.show_devices or not self.admin_mode:
            return

        current_data = {}
        for col_idx, col_name in enumerate(self.devices_columns_names):
            item = self.table.item(row, col_idx)
            current_data[col_name] = item.text() if item else ""

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать компонент")
        form_layout = QFormLayout(dialog)

        input_fields = {}
        for idx, col in enumerate(self.devices_columns_names):
            if idx == 0 or idx == 3:
                label = QLabel(current_data[col])
                form_layout.addRow(col + ":", label)
                input_fields[col] = None
            elif idx == 2:
                combo = QComboBox()
                combo.addItems(["Разрешено", "Заблокировано"])
                combo.setCurrentText("Разрешено" if int(current_data[col]) == 1 else "Заблокировано")
                form_layout.addRow(col + ":", combo)
                input_fields[col] = combo
            else:
                field = QLineEdit(current_data[col])
                form_layout.addRow(col + ":", field)
                input_fields[col] = field

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        form_layout.addWidget(button_box)

        def on_accept():
            updated_data = {
                col: (
                    input_fields[col].currentText()
                    if isinstance(input_fields[col], QComboBox)
                    else input_fields[col].text()
                ) if input_fields[col] is not None else current_data[col]
                for col in self.devices_columns_names
            }

            database.edit_devices([{
                "ID": updated_data["ID"],
                "Name": updated_data["Name"],
                "Permission": 1 if updated_data["Permission"] == 'Разрешено' else 0,
                "Connected": updated_data["Connected"]
            }])
            dialog.accept()
            self.update_table()

        button_box.accepted.connect(on_accept)
        button_box.rejected.connect(dialog.reject)
        dialog.exec_()

    def open_edit_device_dialog(self, row):
        if not self.show_devices or not self.admin_mode:
            return

        current_data = {}
        for col_idx, col_name in enumerate(self.devices_columns_names):
            item = self.table.item(row, col_idx)
            current_data[col_name] = item.text() if item else ""

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать устройство")
        form_layout = QFormLayout(dialog)

        input_fields = {}
        for idx, col in enumerate(self.devices_columns_names):
            if idx == 0 or idx == 3:
                label = QLabel(current_data[col])
                form_layout.addRow(col + ":", label)
                input_fields[col] = None
            elif idx == 2:
                combo = QComboBox()
                combo.addItems(["Разрешено", "Заблокировано"])
                combo.setCurrentText("Разрешено" if int(current_data[col]) == 1 else "Заблокировано")
                form_layout.addRow(col + ":", combo)
                input_fields[col] = combo
            else:
                field = QLineEdit(current_data[col])
                form_layout.addRow(col + ":", field)
                input_fields[col] = field

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        form_layout.addWidget(button_box)

        def on_accept():
            updated_data = {
                col: (
                    input_fields[col].currentText()
                    if isinstance(input_fields[col], QComboBox)
                    else input_fields[col].text()
                ) if input_fields[col] is not None else current_data[col]
                for col in self.devices_columns_names
            }

            database.edit_devices([{
                "ID": updated_data["ID"],
                "Name": updated_data["Name"],
                "Permission": 1 if updated_data["Permission"] == 'Разрешено' else 0,
                "Connected": updated_data["Connected"]
            }])
            dialog.accept()
            self.update_table()

        button_box.accepted.connect(on_accept)
        button_box.rejected.connect(dialog.reject)
        dialog.exec_()

    def update_table_for_device(self, device_id: int):
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(self.components_columns_names)
        data = database.get_components(id=device_id)

        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

        self.adjust_column_widths()
        self.back_button.setVisible(True)

    def update_table(self):
        if self.show_devices:
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(self.devices_columns_names)
            data = database.get_devices()
        else:
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(self.components_columns_names)
            data = database.get_components()

        if self.sort_column >= 0:
            data.sort(
                key=lambda x: x[self.sort_column],
                reverse=self.sort_order == Qt.DescendingOrder
            )

        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

        # Обновляем ширину столбцов с учетом пропорций
        self.adjust_column_widths()

    def adjust_column_widths(self):
        total_width = self.table.viewport().width()
        ratios = self.devices_column_ratios if self.show_devices else self.components_column_ratios
        total_ratio = sum(ratios)

        widths = []
        accumulated = 0
        for i, ratio in enumerate(ratios):
            if i == len(ratios) - 1:
                # Последний столбец получает остаток
                width = total_width - accumulated
            else:
                width = round(total_width * (ratio / total_ratio))
                accumulated += width
            widths.append(width)

        for col_idx, width in enumerate(widths):
            self.table.setColumnWidth(col_idx, width)

    def change_sort(self, index):
        if self.sort_column == index:
            self.sort_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.sort_column = index
            self.sort_order = Qt.AscendingOrder
        self.update_table()

    def show_admin_entrance_dialog(self):
        if self.admin_mode:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Выход из режима администратора")
            msg_box.setText("Вы действительно хотите выйти из режима админа?")
            yes_button = msg_box.addButton("Да", QMessageBox.YesRole)
            no_button = msg_box.addButton("Нет", QMessageBox.NoRole)
            msg_box.exec_()

            if msg_box.clickedButton() == yes_button:
                self.admin_mode = None
                self.update_admin_actions_visibility()
                self.update_monitor_buttons()
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Вход в режим администратора")

        layout = QFormLayout(dialog)
        login_input = QLineEdit()
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Логин:", login_input)
        layout.addRow("Пароль:", password_input)

        error_label = QLabel("")
        error_label.setStyleSheet("color: red; font-size: 10pt")
        layout.addRow(error_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(button_box)

        def check_credentials():
            login = login_input.text()
            password = password_input.text()
            if database.check_password(login, password):
                self.admin_mode = login
                self.update_admin_actions_visibility()
                self.update_monitor_buttons()
                dialog.accept()
            else:
                error_label.setText("Неправильный логин или пароль")
                password_input.clear()

        button_box.accepted.connect(check_credentials)
        button_box.rejected.connect(dialog.reject)
        dialog.exec_()

    def show_change_password_dialog(self):
        if not self.admin_mode:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Изменить пароль")

        layout = QFormLayout(dialog)
        old_pass_input = QLineEdit()
        old_pass_input.setEchoMode(QLineEdit.Password)
        new_pass_input = QLineEdit()
        new_pass_input.setEchoMode(QLineEdit.Password)
        confirm_pass_input = QLineEdit()
        confirm_pass_input.setEchoMode(QLineEdit.Password)

        layout.addRow("Старый пароль:", old_pass_input)
        layout.addRow("Новый пароль:", new_pass_input)
        layout.addRow("Подтвердить пароль:", confirm_pass_input)

        error_label = QLabel("")
        error_label.setStyleSheet("color: red; font-size: 10pt")
        layout.addRow(error_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(button_box)

        def change_password():
            old = old_pass_input.text()
            new = new_pass_input.text()
            confirm = confirm_pass_input.text()
            if new != confirm:
                error_label.setText("Новый пароль не совпадает с подтверждением")
                return
            if database.change_password(self.admin_mode, old, new):
                QMessageBox.information(self, "Успех", "Пароль успешно изменён.")
                dialog.accept()
            else:
                error_label.setText("Старый пароль неверен")

        button_box.accepted.connect(change_password)
        button_box.rejected.connect(dialog.reject)
        dialog.exec_()

    def update_admin_actions_visibility(self):
        is_admin = self.admin_mode is not None
        self.reset_action.setEnabled(is_admin)
        self.change_pass_action.setEnabled(is_admin)
        self.log_action.setEnabled(is_admin)
        self.update_monitor_buttons()

    def reset_table(self):
        database.initial_devices()
        self.update_table()

    def show_about(self):
        QMessageBox.information(self, "О программе", "Программа написано непонятно кем непонятно под чем. Используйте на свой страх и риск и да прибудет с вами сила.")

    def toggle_theme(self):
        if self.dark_theme_enabled:
            # Светлая тема
            self.setStyleSheet("")
        else:
            # Тёмная тема (по умолчанию)
            self.setStyleSheet("""
                QMainWindow { background-color: #2b2b2b; color: #ffffff; }
                QMenuBar, QMenu, QLabel, QTableWidget, QToolButton {
                    background-color: #2b2b2b; color: #ffffff;
                }
                QTableWidget::item { background-color: #3b3b3b; }
                QHeaderView::section {
                    background-color: #444444;
                    color: white;
                    padding: 4px;
                }
            """)
        self.dark_theme_enabled = not self.dark_theme_enabled

    def toggle_show_devices(self):
        self.show_devices = not self.show_devices
        if self.show_devices:
            self.resize(1000, 700)
        else:
            self.resize(1600, 700)
        self.update_table()
        self.adjust_column_widths()

    def show_log_window(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Лог изменений")
        dialog.resize(700, 400)

        layout = QVBoxLayout(dialog)
        log_table = QTableWidget()
        log_table.setColumnCount(3)
        log_table.setHorizontalHeaderLabels(["Time", "Device ID", "New Status"])
        log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        log_table.setSelectionBehavior(QTableWidget.SelectRows)
        log_table.verticalHeader().setVisible(False)
        log_table.horizontalHeader().setStretchLastSection(True)

        logs = database.get_log()
        log_table.setRowCount(len(logs))
        for row_idx, row_data in enumerate(logs):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                log_table.setItem(row_idx, col_idx, item)

        layout.addWidget(log_table)
        dialog.setLayout(layout)
        dialog.exec_()

    def start_monitoring(self):
        self.monitoring_thread = threading.Thread(target=self.monitoring)
        self.monitoring_active = True
        monitor.start_monitoring_in_background(1)
        self.monitoring_thread.start()
        self.update_monitor_buttons()

    def stop_monitoring(self):
        self.monitoring_active = False
        self.update_monitor_buttons()
        monitor.stop_monitoring_in_background()
        self.monitoring_thread.join()

    def update_monitor_buttons(self):
        self.start_button.setEnabled(not self.monitoring_active)
        self.stop_button.setEnabled(self.monitoring_active and self.admin_mode is not None)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # Устанавливаем ширину столбцов на всю ширину окна при изменении размера
        new_width = self.table.viewport().width()
        if new_width != self.initial_width:
            self.initial_width = new_width
            self.adjust_column_widths()

    def monitoring(self):
        while self.monitoring_active:
            if monitor.devices_changed:
                QTimer.singleShot(0, self.update_table)
                monitor.devices_changed = False
            self.status.setText("Статус: запущено" if monitor.actual_monitoring else "Статус: остановлено")
            sleep(1)
        sleep(1) # тут задержка вроде как не нужна, но с ней спокойнее)))
        self.status.setText("Статус: остановлено")

    def show_normal_window(self):
        self.showNormal()
        self.activateWindow()

    def tray_icon_clicked(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_normal_window()

    def exit_app(self):
        if self.admin_mode is not None:
            self.tray_icon.hide()
            self.monitoring_active = False
            monitor.stop_monitoring_in_background()
            if hasattr(self, "monitoring_thread") and self.monitoring_thread.is_alive():
                self.monitoring_thread.join()
            QApplication.quit()

    def closeEvent(self, event: QCloseEvent):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Свернуто в трей",
            "Программа продолжает работать в фоне.",
            QSystemTrayIcon.Information,
            3000
        )


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SortableFilterTable()
    window.show()
    sys.exit(app.exec_())
