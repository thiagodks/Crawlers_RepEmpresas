import sys
import urllib.request
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl

app = QApplication(sys.argv)

class Page(QWebEnginePage):
	def __init__(self, url):
		self.app = app
		QWebEnginePage.__init__(self)
		self.html = ''
		self.loadFinished.connect(self._on_load_finished)
		self.load(QUrl(url))
		self.app.exec_()

	def _on_load_finished(self):
		self.html = self.toHtml(self.Callable)
		print('Load finished')

	def Callable(self, html_str):
		self.html = html_str
		self.app.quit()
		QApplication.quit()
