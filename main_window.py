import threading
from time import sleep

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QHBoxLayout, QHeaderView,
    QMessageBox, QAction, QMenuBar, QToolButton, QLabel
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize, QTimer

import database
import monitor


class SortableFilterTable(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Блокировщик внешних устройств")
        self.resize(1000, 700)

        self.column_name = ["ID", "Name", "Permission", "Connected"]
        self.sort_column = -1
        self.sort_order = Qt.AscendingOrder
        self.monitoring_active = False  # 🔄 состояние мониторинга

        # Пропорции столбцов относительно общей ширины окна
        self.column_ratios = [1, 2, 1, 1]
        self.initial_width = 1000  # Для хранения изначальной ширины окна
        self.status = 0
        self.dark_theme_enabled = False

        self.init_ui()

    def init_ui(self):
        self.create_menu()

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

        # --- Фильтры ---
        # filter_layout = QHBoxLayout()
        # self.filters = []
        # for _ in range(4):
        #     line_edit = QLineEdit()
        #     line_edit.setPlaceholderText("Фильтр...")
        #     line_edit.textChanged.connect(self.update_table)
        #     self.filters.append(line_edit)
        #     filter_layout.addWidget(line_edit)
        # main_layout.addLayout(filter_layout)

        # --- Таблица ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(self.column_name)
        self.table.horizontalHeader().sectionClicked.connect(self.change_sort)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.table)

        main_widget.setLayout(main_layout)

        QTimer.singleShot(0, self.update_table)
        self.update_monitor_buttons()
        self.toggle_theme()

    def create_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("Файл")
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menu_bar.addMenu("Вид")
        theme_action = QAction("Переключить тему", self)
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)

        help_menu = menu_bar.addMenu("Помощь")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def update_table(self):
        # filter_args = {
        #     "id": self.filters[0].text() or None,
        #     "name": self.filters[1].text() or None,
        #     "permission": self.filters[2].text() or None,
        #     "connected": self.filters[3].text() or None
        # }

        data = database.get_devices()

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
        total_ratio = sum(self.column_ratios)

        widths = []
        accumulated = 0
        for i, ratio in enumerate(self.column_ratios):
            if i == len(self.column_ratios) - 1:
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

    def start_monitoring(self):
        self.monitoring_thread = threading.Thread(target=self.monitoring)
        self.monitoring_active = True
        self.update_monitor_buttons()
        monitor.start_monitoring_in_background(1)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        self.monitoring_active = False
        self.update_monitor_buttons()
        monitor.stop_monitoring_in_background()
        self.monitoring_thread.join()

    def update_monitor_buttons(self):
        self.start_button.setEnabled(not self.monitoring_active)
        self.stop_button.setEnabled(self.monitoring_active)

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


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SortableFilterTable()
    window.show()
    sys.exit(app.exec_())
