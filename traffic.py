
import sys
import time
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QSlider, QLabel, QTextEdit, QSpinBox, QProgressBar
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import requests
from concurrent.futures import ThreadPoolExecutor

class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = parent

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)

class RequestWorker(QThread):
    update_log = pyqtSignal(str)
    update_progress = pyqtSignal(int)

    def __init__(self, url, num_requests, num_threads, delay, proxies=None):
        super().__init__()
        self.url = url
        self.num_requests = num_requests
        self.num_threads = num_threads
        self.delay = delay
        self.proxies = proxies

    def run(self):
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(self.send_request, self.url, i + 1, self.delay, self.proxies) for i in range(self.num_requests)]
            for i, future in enumerate(futures):
                result = future.result()
                self.update_log.emit(result)
                self.update_progress.emit(int((i + 1) / self.num_requests * 100))

    def send_request(self, url, request_number, delay, proxies):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        proxy = None
        if proxies:
            proxy = {'http': proxies[request_number % len(proxies)], 'https': proxies[request_number % len(proxies)]}
        try:
            response = requests.get(url, headers=headers, proxies=proxy)
            time.sleep(delay)
            return f"{request_number} Запрос: {response.status_code} {response.reason}"
        except Exception as e:
            return f"{request_number} Запрос: Ошибка {str(e)}"

class TrafficBooster(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.setupLogging()

    def initUI(self):
        layout = QVBoxLayout()

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Введите URL (http или https)")
        layout.addWidget(self.url_input)

        self.slider_label = QLabel("Количество запросов: 1", self)
        layout.addWidget(self.slider_label)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(1)
        self.slider.setMaximum(1000000)
        self.slider.setValue(1)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.update_slider_label)
        layout.addWidget(self.slider)

        self.threads_label = QLabel("Количество потоков: 10", self)
        layout.addWidget(self.threads_label)

        self.threads_slider = QSlider(Qt.Horizontal, self)
        self.threads_slider.setMinimum(1)
        self.threads_slider.setMaximum(100)
        self.threads_slider.setValue(10)
        self.threads_slider.setTickInterval(1)
        self.threads_slider.valueChanged.connect(self.update_threads_label)
        layout.addWidget(self.threads_slider)

        self.delay_label = QLabel("Задержка между запросами (мс): 0", self)
        layout.addWidget(self.delay_label)

        self.delay_input = QSpinBox(self)
        self.delay_input.setMinimum(0)
        self.delay_input.setMaximum(10000)
        self.delay_input.setValue(0)
        layout.addWidget(self.delay_input)

        self.proxy_input = QLineEdit(self)
        self.proxy_input.setPlaceholderText("Введите прокси (опционально, разделяйте запятой)")
        layout.addWidget(self.proxy_input)

        self.start_button = QPushButton("Начать накрутку трафика", self)
        self.start_button.clicked.connect(self.start_traffic_boost)
        layout.addWidget(self.start_button)

        self.result_display = QTextEdit(self)
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.setWindowTitle('Traffic Booster')
        self.show()

    def update_slider_label(self, value):
        self.slider_label.setText(f"Количество запросов: {value}")

    def update_threads_label(self, value):
        self.threads_label.setText(f"Количество потоков: {value}")

    def setupLogging(self):
        self.logger = logging.getLogger('TrafficBooster')
        self.logger.setLevel(logging.INFO)
        handler = QTextEditLogger(self.result_display)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(handler)

        file_handler = logging.FileHandler('traffic_booster.log')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(file_handler)

    def start_traffic_boost(self):
        url = self.url_input.text()
        num_requests = self.slider.value()
        num_threads = self.threads_slider.value()
        delay = self.delay_input.value() / 1000
        self.result_display.clear()
        self.progress_bar.setValue(0)

        proxies = None
        proxy_text = self.proxy_input.text()
        if proxy_text:
            proxies = proxy_text.split(',')

        if not url.startswith("http://") and not url.startswith("https://"):
            self.result_display.append("Некорректный URL. Пожалуйста, введите URL, начинающийся с http:// или https://")
            return

        self.logger.info(f"Начало накрутки трафика на {url} с {num_requests} запросами и {num_threads} потоками, задержка {delay} секунд")

        self.worker = RequestWorker(url, num_requests, num_threads, delay, proxies)
        self.worker.update_log.connect(self.result_display.append)
        self.worker.update_progress.connect(self.progress_bar.setValue)
        self.worker.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TrafficBooster()
    sys.exit(app.exec_())
