import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel

from ui_web_image_batch_downloader import Ui_MainWindow
import pyddavid.web_image


class TestUrlsThread(QThread):
    process_task_updated = pyqtSignal(int, int, "QString")
    process_message_updated = pyqtSignal("QString")


    def __init__(self, urls):
        QThread.__init__(self)
        self.urls = urls
    
    
    def __del__(self):
        self.wait()
    
    
    def run(self):
        n_urls = len(self.urls)

        for i in range(n_urls):
            self.process_message_updated.emit(str(i + 1) + "/" + str(n_urls) + " 網址測試中……")
            if pyddavid.web_image.test_img_url(self.urls[i]):
                self.url_list_updated.emit(self.urls[i])
        self.process_message_updated.emit("網址測試全部完成。")


class SaveImageThread(QThread):
    process_task_updated = pyqtSignal(int, int, "QString")
    process_message_updated = pyqtSignal("QString")


    def __init__(self, urls, root, level):
        QThread.__init__(self)
        self.urls = urls
        self.root = root
        self.level = level
    
    
    def __del__(self):
        self.wait()
    
    
    def run(self):
        n_urls = len(self.urls)

        for i in range(n_urls):
            output_path = pyddavid.web_image.path_from_url_and_root(
                self.urls[i],
                self.root,
                self.level
            )
            output_dir, output_filename = pyddavid.web_image.split_path_to_dir_and_filename(output_path)
            pyddavid.web_image.save_img_from_url(
                self.urls[i],
                output_dir,
                output_filename
            )
            self.process_message_updated.emit(str(i + 1) + "/" + str(n_urls) + " 檔案下載中……")
        self.process_message_updated.emit("下載全部完成。")


class WebImageBatchDownloader(QMainWindow, Ui_MainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._init_task_list()


    def _init_task_list(self):
        self.model_task_list = QStandardItemModel(1, 3)
        self.model_task_list.setHorizontalHeaderLabels(["狀態", "網址", "本機儲存目錄"])
        self.model_task_list.removeRow(0)

        self.ui.tableView_Tasks.setModel(self.model_task_list)
        self.ui.tableView_Tasks.setColumnWidth(0, 50)
        self.ui.tableView_Tasks.setColumnWidth(1, 600)
        self.ui.tableView_Tasks.setColumnWidth(2, 280)
        self.ui.tableView_Tasks.verticalHeader().setDefaultSectionSize(20)


    def _model_setItem(self, row, col, data):
        self.model_task_list.setItem(row, col, QStandardItem(data))

    
    def add_batch_url(self):
        self.ui.comboBox_batch_urls.addItem(self.ui.plainTextEdit_BatchUrl.text())

        urls = self._analysis_batch_urls()
        self._update_urls(urls)
    

    def _analysis_batch_urls(self):
        url_interprer = pyddavid.web_image.UrlToComponentsInterpreter()
        batch_urls = [self.ui.comboBox_batch_urls.itemText(i) for i in range(self.ui.comboBox_batch_urls.count())]
        for batch_url in batch_urls:
            url_interprer.add_urls_from_url_batch(batch_url)
        urls = url_interprer.get_urls()

        return urls


    def _update_urls(self, urls):
        for url in urls:
            current_row = self.model_task_list.rowCount()
            self.model_task_list.insertRow(current_row)
            self._model_setItem(current_row, 0, "未測試")
            self._model_setItem(current_row, 1, url)
            self._model_setItem(current_row, 2, "")


    def remove_current_batch_url(self):
        if self.ui.comboBox_batch_urls.count() >= 0:
            self.ui.comboBox_batch_urls.removeItem(
                self.ui.comboBox_batch_urls.currentIndex()
            )
        
        urls = self._analysis_batch_urls()
        self._update_urls(urls)
    

    def choose_output_dir(self):
        self.ui.plainTextEdit_SaveDir.setText(QFileDialog.getExistingDirectory(self, "選擇存檔目錄", self.ui.plainTextEdit_SaveDir.text(), QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks))
    

    def save_img(self, index):
        # 需要修改
        root = self.ui.plainTextEdit_SaveDir.text()
        if root == "":
            root = "."

        url = self.ui.listWidget_Urls.item(index.row()).text()
        output_path = pyddavid.web_image.path_from_url_and_root(
            url,
            root
        )
        output_dir, output_filename = pyddavid.web_image.split_path_to_dir_and_filename(output_path)
        pyddavid.web_image.save_img_from_url(
            url,
            output_dir,
            output_filename
        )
        self.update_process_message("下載完成。")


    def test_urls(self):
        # 需要修改
        self.thread_test_urls = TestUrlsThread(urls)
        self.thread_test_urls.start()
        self.thread_test_urls.process_message_updated.connect(self._update_process_message)
        self.thread_test_urls.process_task_updated.connect(self._model_setItem)
    

    def _update_process_message(self, message):
        self.ui.label_ProcessMessage.setText(message)


    def download_imgs(self):
        # 需要修改
        urls = [self.ui.listWidget_Urls.item(i).text() for i in range(self.ui.listWidget_Urls.count())]
        root = self.ui.plainTextEdit_SaveDir.text()
        if root == "":
            root = "."
        level = int(self.ui.lineEdit_Level.text())

        self.save_image_thread = SaveImageThread(
            urls,
            root,
            level
        )
        self.save_image_thread.start()
        self.save_image_thread.process_message_updated.connect(self.update_process_message)


    def reset_all(self):
        self.ui.comboBox_batch_urls.clear()
        self.model_task_list.removeColumns(
            0,
            self.model_task_list.columnCount()
        )


def main():
    app = QApplication(sys.argv)
    ui = WebImageBatchDownloader()
    ui.show()
    app.exec()


if __name__ == "__main__":
    main()
