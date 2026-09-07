from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QFileDialog, QMessageBox, QStatusBar
)
from minimalize_engine import MinimalizeConfig
from minimalize_engine.io.svg_exporter import export_svg
from minimalize_engine.io.image_exporter import export_png, render_scene
from .preview_widget import PreviewWidget
from .settings_panel import SettingsPanel
from .workers import MinimalizeWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimalizer v0.3.0")
        self.resize(1280, 800)

        self.settings = SettingsPanel()
        self.preview = PreviewWidget()

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.addWidget(self.settings)
        layout.addWidget(self.preview, 1)
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

        self.image_path: str | None = None
        self.scene = None
        self.thread = None
        self.worker = None

        self.settings.open_requested.connect(self.open_image)
        self.settings.run_requested.connect(self.run_minimalize)
        self.settings.save_svg_requested.connect(self.save_svg)
        self.settings.save_png_requested.connect(self.save_png)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "画像を選択",
            "",
            "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if not path:
            return
        self.image_path = path
        self.scene = None
        self.preview.set_source_path(path)
        self.preview.result.clear()
        self.settings.set_result_available(False)
        self.statusBar().showMessage(Path(path).name)

    def build_config(self):
        v = self.settings.values()
        overrides = {
            "pre_smoothing": v["detail"],
            "merge_distance_ratio": 0.025 * v["merge"],
            "line_mode": v["line_mode"],
            "preserve_accents": v["preserve_accents"],
            "enable_layer_composition": v["enable_layer_composition"],
            "enable_macro_underlays": v["enable_macro_underlays"],
            "enable_composition_skeleton": v["enable_composition_skeleton"],
            "enable_multiscale_analysis": v["enable_multiscale_analysis"],
            "enable_pseudo_semantics": v["enable_pseudo_semantics"],
            "enable_design_primitives": v["enable_design_primitives"],
            "enable_design_palette": v["enable_design_palette"],
            "enable_pattern_recognition": v["enable_pattern_recognition"],
            "enable_auto_retry": v["enable_auto_retry"],
            "enable_global_shape_value": v["enable_global_shape_value"],
            "enable_global_shape_cleanup": v["enable_global_shape_cleanup"],
            "enable_character_structure": v["enable_character_structure"],
            "enable_body_primitives": v["enable_body_primitives"],
            "enable_hand_analysis": v["enable_hand_analysis"],
            "enable_hand_primitives": v["enable_hand_primitives"],
            "enable_hand_geometry_validation": v["enable_hand_geometry_validation"],
            "enable_hand_validation": v["enable_hand_validation"],
            "enable_hand_quality": v["enable_hand_quality"],
            "enable_limb_geometry_refine": v["enable_limb_geometry_refine"],
            "enable_hair_body_guard": v["enable_hair_body_guard"],
            "enable_character_layout": v["enable_character_layout"],
            "enable_character_quality": v["enable_character_quality"],
            "enable_character_auto_retry": v["enable_character_auto_retry"],
            "enable_face_rules": v["enable_face_rules"],
            "enable_face_primitives": v["enable_face_primitives"],
            "enable_face_validation": v["enable_face_validation"],
            "enable_face_geometry_quality": v["enable_face_geometry_quality"],
            "enable_face_contour_fit": v["enable_face_contour_fit"],
            "enable_face_boundary_guard": v["enable_face_boundary_guard"],
            "enable_face_identity_budget": v["enable_face_identity_budget"],
            "enable_face_identity_validation": v["enable_face_identity_validation"],
            "enable_hair_rules": v["enable_hair_rules"],
            "enable_outfit_rules": v["enable_outfit_rules"],
            "enable_prop_rules": v["enable_prop_rules"],
            "enable_adaptive_character_budget": v["enable_adaptive_character_budget"],
            "enable_outfit_structure_quality": v["enable_outfit_structure_quality"],
            "enable_prop_symbol_quality": v["enable_prop_symbol_quality"],
            "enable_character_wide_identity": v["enable_character_wide_identity"],
            "background_mode": v["background_mode"],
        }
        if v["colors"] is not None:
            overrides["palette_colors"] = int(v["colors"])
        return MinimalizeConfig.from_level(int(v["level"]), **overrides)

    def run_minimalize(self):
        if not self.image_path:
            QMessageBox.information(self, "Minimalizer", "先に画像を読み込んでください。")
            return

        config = self.build_config()
        self.settings.set_busy(True)
        self.settings.set_result_available(False)
        self.statusBar().showMessage("ミニマル化しています…")

        self.thread = QThread(self)
        self.worker = MinimalizeWorker(self.image_path, config)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_finished(self, scene):
        self.scene = scene
        self.preview.set_result(render_scene(scene, scale=1))
        self.settings.set_busy(False)
        self.settings.set_result_available(True)
        quality = scene.metadata.get("quality", {}).get("score")
        quality_text = f" / quality {quality:.3f}" if isinstance(quality, (int, float)) else ""

        character_quality = scene.metadata.get("character_quality", {}).get("score")
        character_quality_text = (
            f" / character {character_quality:.3f}"
            if isinstance(character_quality, (int, float))
            else ""
        )

        retry = scene.metadata.get("auto_retry_attempts", 0)
        character_retry = scene.metadata.get("character_retry_attempts", 0)
        face_retry = scene.metadata.get("face_retry_attempts", 0)
        retry_text = ""
        if retry or character_retry or face_retry:
            retry_text = f" / retry g{retry}:c{character_retry}:f{face_retry}"

        self.statusBar().showMessage(
            f"完了: {scene.metadata.get('shape_count', len(scene.shapes))} shapes"
            f"{quality_text}{character_quality_text}{retry_text}"
        )

    def on_failed(self, message: str):
        self.settings.set_busy(False)
        self.statusBar().showMessage("エラー")
        QMessageBox.critical(self, "Minimalizer", message)

    def save_svg(self):
        if self.scene is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "SVG保存", "minimalized.svg", "SVG (*.svg)")
        if path:
            export_svg(self.scene, path)
            self.statusBar().showMessage(f"保存しました: {path}")

    def save_png(self):
        if self.scene is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "PNG保存", "minimalized.png", "PNG (*.png)")
        if path:
            export_png(self.scene, path)
            self.statusBar().showMessage(f"保存しました: {path}")
