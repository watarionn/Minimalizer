from __future__ import annotations
import traceback
from PySide6.QtCore import QObject, Signal, Slot
from minimalize_engine import minimalize


class MinimalizeWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, image_path, config):
        super().__init__()
        self.image_path = image_path
        self.config = config

    @Slot()
    def run(self):
        try:
            scene = minimalize(self.image_path, self.config)
            self.finished.emit(scene)
        except Exception:
            self.failed.emit(traceback.format_exc())
