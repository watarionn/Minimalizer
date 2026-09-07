from __future__ import annotations
from pathlib import Path
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QScrollArea


def pil_to_pixmap(image: Image.Image) -> QPixmap:
    rgba = image.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qimg = QImage(
        data,
        rgba.width,
        rgba.height,
        rgba.width * 4,
        QImage.Format_RGBA8888,
    ).copy()
    return QPixmap.fromImage(qimg)


class ImagePane(QWidget):
    def __init__(self, title: str):
        super().__init__()
        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignCenter)
        self.image = QLabel("画像なし")
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setMinimumSize(240, 180)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.image)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(scroll, 1)

    def set_pil(self, image: Image.Image):
        pixmap = pil_to_pixmap(image)
        self.image.setPixmap(pixmap)
        self.image.resize(pixmap.size())

    def clear(self):
        self.image.setPixmap(QPixmap())
        self.image.setText("画像なし")


class PreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.source = ImagePane("元画像")
        self.result = ImagePane("ミニマル化結果")

        layout = QHBoxLayout(self)
        layout.addWidget(self.source, 1)
        layout.addWidget(self.result, 1)

    def set_source_path(self, path: str | Path):
        image = Image.open(path).convert("RGB")
        self.source.set_pil(image)

    def set_result(self, image: Image.Image):
        self.result.set_pil(image)
