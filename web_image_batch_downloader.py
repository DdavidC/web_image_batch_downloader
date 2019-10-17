import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QHeaderView
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
import PIL.Image

from ui_web_image_batch_downloader import Ui_MainWindow
import pyddavid.web_image


def imshow(img_path, title = None):
    img = PIL.Image.open(img_path)
    img.show()


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
                task_stat = "可用"
            else:
                task_stat = "無效"
            self.process_task_updated.emit(i, 0, task_stat)

        self.process_message_updated.emit("網址測試全部完成。")


class SaveImageThread(QThread):
    process_task_updated = pyqtSignal(int, int, "QString")
    process_message_updated = pyqtSignal("QString")


    def __init__(self, indexs, urls, output_paths, root):
        QThread.__init__(self)
        self.indexs = indexs
        self.urls = urls
        self.output_paths = output_paths
        self.root = root
    
    
    def __del__(self):
        self.wait()
    
    
    def run(self):
        n_urls = len(self.urls)

        for i in range(n_urls):
            output_dir, output_filename = pyddavid.web_image.split_path_to_dir_and_filename(self.output_paths[i])
            self.process_message_updated.emit(str(i + 1) + "/" + str(n_urls) + " 檔案下載中……")
            if pyddavid.web_image.save_img_from_url(
                self.urls[i],
                output_dir,
                output_filename):
                task_stat = "成功"
            else:
                task_stat = "失敗"

            self.process_task_updated.emit(self.indexs[i], 0, task_stat)

        self.process_message_updated.emit("下載全部完成。")


class WebImageBatchDownloader(QMainWindow, Ui_MainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._init_task_list()


    def _init_task_list(self):
        self.model_task_list = QStandardItemModel(1, 3, self.ui.tableView_Tasks)
        self.model_task_list.setHorizontalHeaderLabels(["狀態", "網址", "本機儲存目錄"])
        self.model_task_list.removeRow(0)

        self.ui.tableView_Tasks.setModel(self.model_task_list)
        self.ui.tableView_Tasks.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.ui.tableView_Tasks.horizontalHeader().setDefaultSectionSize(60)
        self.ui.tableView_Tasks.horizontalHeader().resizeSection(0, 60)
        self.ui.tableView_Tasks.horizontalHeader().resizeSection(1, 600)
        self.ui.tableView_Tasks.horizontalHeader().resizeSection(2, 250)
        self.ui.tableView_Tasks.verticalHeader().setDefaultSectionSize(20)


    def _model_setItem(self, row, col, data):
        self.model_task_list.setItem(row, col, QStandardItem(data))

    
    def add_batch_url(self):
        self.ui.comboBox_batch_urls.addItem(self.ui.plainTextEdit_BatchUrl.text().rstrip())
        self.ui.comboBox_batch_urls.setCurrentIndex(self.ui.comboBox_batch_urls.count() - 1)

        urls = self._analysis_batch_urls()
        self._update_tasks(urls)
        self._update_output_paths()
    

    def _analysis_batch_urls(self):
        url_interprer = pyddavid.web_image.UrlToComponentsInterpreter()
        batch_urls = [self.ui.comboBox_batch_urls.itemText(i) for i in range(self.ui.comboBox_batch_urls.count())]
        for batch_url in batch_urls:
            url_interprer.add_urls_from_url_batch(batch_url)
        urls = url_interprer.get_urls()

        return urls


    def _update_tasks(self, urls):
        self.model_task_list.removeRows(0, self.model_task_list.rowCount())
        
        for url in urls:
            current_row = self.model_task_list.rowCount()
            self.model_task_list.insertRow(current_row)
            self._model_setItem(current_row, 0, "未知")
            self._model_setItem(current_row, 1, url)
    

    def _adjust_root(self):
        root = self.ui.plainTextEdit_SaveDir.text().replace("\\", "/")
        self.ui.plainTextEdit_SaveDir.setText(root)


    def _update_output_paths(self):
        n_tasks = self.model_task_list.rowCount()

        root = self._get_root()
        level = self._get_level()

        for r in range(n_tasks):
            output_path = pyddavid.web_image.path_from_url_and_root(
                self.model_task_list.item(r, 1).text(),
                root,
                level
            )
            self._model_setItem(r, 2, output_path)

        self.ui.tableView_Tasks.setColumnWidth(2, 280)


    def remove_current_batch_url(self):
        if self.ui.comboBox_batch_urls.count() >= 0:
            self.ui.comboBox_batch_urls.removeItem(
                self.ui.comboBox_batch_urls.currentIndex()
            )
        
        urls = self._analysis_batch_urls()
        self._update_tasks(urls)
        self._update_output_paths()
    

    def choose_output_dir(self):
        self.ui.plainTextEdit_SaveDir.setText(QFileDialog.getExistingDirectory(self, "選擇存檔目錄", self.ui.plainTextEdit_SaveDir.text(), QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks))

        self._update_output_paths()
    

    def _get_root(self):
        root = self.ui.plainTextEdit_SaveDir.text()
        if root == "":
            root = "."
        
        return root


    def _get_level(self):
        level = int(self.ui.lineEdit_Level.text())

        return level


    def save_img(self, index):
        url = self.model_task_list.item(index.row(), 1).text()
        output_path = self.model_task_list.item(index.row(), 2).text()

        output_dir, output_filename = pyddavid.web_image.split_path_to_dir_and_filename(output_path)
        if pyddavid.web_image.save_img_from_url(
                url,
                output_dir,
                output_filename):
            self._update_process_message("下載完成。")
            imshow(output_path, output_filename)
        else:
            self._update_process_message("下載失敗。")


    def test_urls(self):
        urls = [self.model_task_list.item(r, 1).text() for r in range(self.model_task_list.rowCount())]

        self.thread_test_urls = TestUrlsThread(urls)
        self.thread_test_urls.start()
        self.thread_test_urls.process_message_updated.connect(self._update_process_message)
        self.thread_test_urls.process_task_updated.connect(self._model_setItem)


    def _update_process_message(self, message):
        self.ui.label_ProcessMessage.setText(message)


    def download_imgs(self):
        indexs = []
        urls = []
        output_paths = []
        for r in range(self.model_task_list.rowCount()):
            if (self.model_task_list.item(r, 0).text() == "未知" or
                    self.model_task_list.item(r, 0).text() == "可用"):
                indexs.append(r)
                urls.append(self.model_task_list.item(r, 1).text())
                output_paths.append(self.model_task_list.item(r, 2).text())

        root = self._get_root()

        self.save_image_thread = SaveImageThread(
            indexs,
            urls,
            output_paths,
            root,
        )
        self.save_image_thread.start()
        self.save_image_thread.process_message_updated.connect(self._update_process_message)
        self.save_image_thread.process_task_updated.connect(self._model_setItem)


    def reset_all(self):
        self.ui.comboBox_batch_urls.clear()
        self.model_task_list.removeRows(0, self.model_task_list.rowCount())


def main():
    app = QApplication(sys.argv)
    ui = WebImageBatchDownloader()
    ui.show()
    app.exec()


if __name__ == "__main__":
    main()
