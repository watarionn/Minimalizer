from __future__ import annotations
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSlider, QCheckBox, QGroupBox, QFileDialog, QScrollArea, QFrame
)


class SettingsPanel(QWidget):
    open_requested = Signal()
    run_requested = Signal()
    save_svg_requested = Signal()
    save_png_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setMaximumWidth(370)

        self.open_button = QPushButton("画像を読み込む")
        self.run_button = QPushButton("ミニマル化")
        self.save_svg_button = QPushButton("SVG保存")
        self.save_png_button = QPushButton("PNG保存")
        self.save_svg_button.setEnabled(False)
        self.save_png_button.setEnabled(False)

        self.level = QComboBox()
        for i, name in [
            (1, "1  詳細"),
            (2, "2  軽量"),
            (3, "3  標準"),
            (4, "4  ミニマル"),
            (5, "5  極限"),
        ]:
            self.level.addItem(name, i)
        self.level.setCurrentIndex(3)

        self.colors = QComboBox()
        self.colors.addItem("自動", None)
        for n in [4, 6, 8, 12, 16]:
            self.colors.addItem(str(n), n)

        self.detail = QSlider(Qt.Horizontal)
        self.detail.setRange(0, 100)
        self.detail.setValue(70)

        self.merge = QSlider(Qt.Horizontal)
        self.merge.setRange(0, 100)
        self.merge.setValue(60)

        self.lines = QComboBox()
        self.lines.addItem("なし", "none")
        self.lines.addItem("少なめ", "low")
        self.lines.addItem("標準", "standard")
        self.lines.setCurrentIndex(1)

        self.accents = QCheckBox("特徴色を残す")
        self.accents.setChecked(True)

        self.layer_composition = QCheckBox("レイヤー構図化")
        self.layer_composition.setChecked(True)

        self.macro_underlays = QCheckBox("大きな下敷きシルエット")
        self.macro_underlays.setChecked(True)

        self.composition_skeleton = QCheckBox("構図骨格・中央余白")
        self.composition_skeleton.setChecked(True)

        self.multiscale = QCheckBox("マルチスケール解析")
        self.multiscale.setChecked(True)

        self.pseudo_semantics = QCheckBox("AIなし意味推定")
        self.pseudo_semantics.setChecked(True)

        self.design_primitives = QCheckBox("デザイン図形ライブラリ")
        self.design_primitives.setChecked(True)

        self.design_palette = QCheckBox("色調和・Design Palette")
        self.design_palette.setChecked(True)

        self.patterns = QCheckBox("反復パターン整理")
        self.patterns.setChecked(True)

        self.auto_retry = QCheckBox("自動品質評価・再試行")
        self.auto_retry.setChecked(True)

        self.global_shape_value = QCheckBox("価値の低いShapeを全体評価で削る")
        self.global_shape_value.setChecked(True)
        self.global_shape_value.setToolTip("面積・重要度・色差・重複・孤立・複雑度をまとめて評価し、意味の薄いShapeだけを保守的に削除します。")

        self.global_shape_cleanup = QCheckBox("極細・微小・孤立・近接Shapeを最終整理")
        self.global_shape_cleanup.setChecked(True)
        self.global_shape_cleanup.setToolTip("ミニマル化の最終段で、極細・微小・孤立Shapeを整理し、近い同色Shapeの統合と輪郭頂点の簡略化を保守的に行います。")

        self.character_structure = QCheckBox("人物・キャラクター構造化")
        self.character_structure.setChecked(True)

        self.body_primitives = QCheckBox("胴体・腕・脚を大Shape化")
        self.body_primitives.setChecked(True)

        self.hand_analysis = QCheckBox("手の形とジェスチャーを解析")
        self.hand_analysis.setChecked(True)

        self.hand_primitives = QCheckBox("手をジェスチャー1Shapeで描く")
        self.hand_primitives.setChecked(True)

        self.hand_geometry_validation = QCheckBox("手を腕先と自然につなぐ")
        self.hand_geometry_validation.setChecked(True)

        self.hand_validation = QCheckBox("手ではない袖先・髪先を除外")
        self.hand_validation.setChecked(True)

        self.hand_quality = QCheckBox("手の意味と接続品質を評価")
        self.hand_quality.setChecked(True)

        self.limb_geometry_refine = QCheckBox("崩れた腕・脚だけ輪郭補正")
        self.limb_geometry_refine.setChecked(True)

        self.hair_body_guard = QCheckBox("髪が胴体を飲み込む誤認を抑制")
        self.hair_body_guard.setChecked(True)

        self.character_layout = QCheckBox("人物配置を自動調整")
        self.character_layout.setChecked(True)

        self.character_quality = QCheckBox("人物品質を専用評価")
        self.character_quality.setChecked(True)

        self.character_auto_retry = QCheckBox("人物品質で自動再試行")
        self.character_auto_retry.setChecked(True)

        self.face_rules = QCheckBox("顔を解析して簡略化")
        self.face_rules.setChecked(True)

        self.face_primitives = QCheckBox("顔パーツを描く（目・口・顔ベース）")
        self.face_primitives.setChecked(False)
        self.face_primitives.setToolTip("位置ずれを避けるため既定OFF。必要な時だけ専用の顔Shapeを描画します。")

        self.face_validation = QCheckBox("顔の誤認を抑制")
        self.face_validation.setChecked(True)

        self.face_geometry_quality = QCheckBox("顔形状を専用評価")
        self.face_geometry_quality.setChecked(True)

        self.face_contour_fit = QCheckBox("顔輪郭を自動フィット")
        self.face_contour_fit.setChecked(True)

        self.face_boundary_guard = QCheckBox("前髪と顔の境界を保護")
        self.face_boundary_guard.setChecked(True)

        self.face_identity_budget = QCheckBox("顔を必要最小限の特徴だけで描く")
        self.face_identity_budget.setChecked(True)

        self.face_identity_validation = QCheckBox("顔を削りすぎた時だけ特徴を1つ戻す")
        self.face_identity_validation.setChecked(True)

        self.hair_rules = QCheckBox("髪の流れを保持")
        self.hair_rules.setChecked(True)

        self.outfit_rules = QCheckBox("衣装構造を優先")
        self.outfit_rules.setChecked(True)

        self.prop_rules = QCheckBox("小物・武器を独立")
        self.prop_rules.setChecked(True)

        self.adaptive_character_budget = QCheckBox("人物Shape予算を識別性で再配分")
        self.adaptive_character_budget.setChecked(True)

        self.outfit_structure_quality = QCheckBox("衣装シルエットを仕上げ評価")
        self.outfit_structure_quality.setChecked(True)

        self.prop_symbol_quality = QCheckBox("小物の記号化品質を評価")
        self.prop_symbol_quality.setChecked(True)

        self.character_wide_identity = QCheckBox("全身の識別性を総合評価")
        self.character_wide_identity.setChecked(True)

        self.background = QComboBox()
        self.background.addItem("元画像由来", "source")
        self.background.addItem("白", "white")
        self.background.addItem("透明", "transparent")

        # The default surface only exposes controls that most users need.
        basic_form = QVBoxLayout()
        basic_form.addWidget(QLabel("抽象度"))
        basic_form.addWidget(self.level)
        basic_form.addWidget(QLabel("色数"))
        basic_form.addWidget(self.colors)
        basic_form.addWidget(QLabel("ディテール除去"))
        basic_form.addWidget(self.detail)
        basic_form.addWidget(QLabel("形状統合"))
        basic_form.addWidget(self.merge)
        basic_form.addWidget(QLabel("線"))
        basic_form.addWidget(self.lines)
        basic_form.addWidget(QLabel("背景"))
        basic_form.addWidget(self.background)

        basic_group = QGroupBox("ミニマル化")
        basic_group.setLayout(basic_form)

        # Engine/detail switches remain available, but stay out of the normal
        # image -> minimalize -> save flow until the user explicitly opens them.
        cleanup_form = QVBoxLayout()
        for widget in [
            self.accents, self.layer_composition, self.macro_underlays,
            self.composition_skeleton, self.multiscale, self.pseudo_semantics,
            self.design_primitives, self.design_palette, self.patterns,
            self.auto_retry, self.global_shape_value, self.global_shape_cleanup,
        ]:
            cleanup_form.addWidget(widget)
        cleanup_group = QGroupBox("全体・仕上げ")
        cleanup_group.setLayout(cleanup_form)

        character_form = QVBoxLayout()
        for widget in [
            self.character_structure, self.body_primitives,
            self.hand_analysis, self.hand_primitives,
            self.hand_geometry_validation, self.hand_validation,
            self.hand_quality, self.limb_geometry_refine,
            self.hair_body_guard, self.character_layout,
            self.character_quality, self.character_auto_retry,
            self.hair_rules, self.outfit_rules, self.prop_rules,
            self.adaptive_character_budget, self.outfit_structure_quality,
            self.prop_symbol_quality, self.character_wide_identity,
        ]:
            character_form.addWidget(widget)
        character_group = QGroupBox("人物・キャラクター")
        character_group.setLayout(character_form)

        face_form = QVBoxLayout()
        for widget in [
            self.face_rules, self.face_primitives, self.face_validation,
            self.face_geometry_quality, self.face_contour_fit,
            self.face_boundary_guard, self.face_identity_budget,
            self.face_identity_validation,
        ]:
            face_form.addWidget(widget)
        face_group = QGroupBox("顔")
        face_group.setLayout(face_form)

        self.advanced_widget = QWidget()
        advanced_layout = QVBoxLayout(self.advanced_widget)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.addWidget(cleanup_group)
        advanced_layout.addWidget(character_group)
        advanced_layout.addWidget(face_group)
        self.advanced_widget.setVisible(False)

        self.advanced_button = QPushButton("詳細設定を表示")
        self.advanced_button.setCheckable(True)
        self.advanced_button.setToolTip("通常は変更不要です。内部機能や人物・顔関連の設定を表示します。")
        self.advanced_button.toggled.connect(self._set_advanced_visible)

        save_row = QHBoxLayout()
        save_row.addWidget(self.save_svg_button)
        save_row.addWidget(self.save_png_button)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(self.open_button)
        content_layout.addWidget(basic_group)
        content_layout.addWidget(self.advanced_button)
        content_layout.addWidget(self.advanced_widget)
        content_layout.addWidget(self.run_button)
        content_layout.addLayout(save_row)
        content_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.open_button.clicked.connect(self.open_requested)
        self.run_button.clicked.connect(self.run_requested)
        self.save_svg_button.clicked.connect(self.save_svg_requested)
        self.save_png_button.clicked.connect(self.save_png_requested)

    def _set_advanced_visible(self, visible: bool):
        self.advanced_widget.setVisible(visible)
        self.advanced_button.setText("詳細設定を隠す" if visible else "詳細設定を表示")

    def values(self):
        return {
            "level": self.level.currentData(),
            "colors": self.colors.currentData(),
            "detail": self.detail.value() / 100.0,
            "merge": self.merge.value() / 100.0,
            "line_mode": self.lines.currentData(),
            "preserve_accents": self.accents.isChecked(),
            "enable_layer_composition": self.layer_composition.isChecked(),
            "enable_macro_underlays": self.macro_underlays.isChecked(),
            "enable_composition_skeleton": self.composition_skeleton.isChecked(),
            "enable_multiscale_analysis": self.multiscale.isChecked(),
            "enable_pseudo_semantics": self.pseudo_semantics.isChecked(),
            "enable_design_primitives": self.design_primitives.isChecked(),
            "enable_design_palette": self.design_palette.isChecked(),
            "enable_pattern_recognition": self.patterns.isChecked(),
            "enable_auto_retry": self.auto_retry.isChecked(),
            "enable_global_shape_value": self.global_shape_value.isChecked(),
            "enable_global_shape_cleanup": self.global_shape_cleanup.isChecked(),
            "enable_character_structure": self.character_structure.isChecked(),
            "enable_body_primitives": self.body_primitives.isChecked(),
            "enable_hand_analysis": self.hand_analysis.isChecked(),
            "enable_hand_primitives": self.hand_primitives.isChecked(),
            "enable_hand_geometry_validation": self.hand_geometry_validation.isChecked(),
            "enable_hand_validation": self.hand_validation.isChecked(),
            "enable_hand_quality": self.hand_quality.isChecked(),
            "enable_limb_geometry_refine": self.limb_geometry_refine.isChecked(),
            "enable_hair_body_guard": self.hair_body_guard.isChecked(),
            "enable_character_layout": self.character_layout.isChecked(),
            "enable_character_quality": self.character_quality.isChecked(),
            "enable_character_auto_retry": self.character_auto_retry.isChecked(),
            "enable_face_rules": self.face_rules.isChecked(),
            "enable_face_primitives": self.face_primitives.isChecked(),
            "enable_face_validation": self.face_validation.isChecked(),
            "enable_face_geometry_quality": self.face_geometry_quality.isChecked(),
            "enable_face_contour_fit": self.face_contour_fit.isChecked(),
            "enable_face_boundary_guard": self.face_boundary_guard.isChecked(),
            "enable_face_identity_budget": self.face_identity_budget.isChecked(),
            "enable_face_identity_validation": self.face_identity_validation.isChecked(),
            "enable_hair_rules": self.hair_rules.isChecked(),
            "enable_outfit_rules": self.outfit_rules.isChecked(),
            "enable_prop_rules": self.prop_rules.isChecked(),
            "enable_adaptive_character_budget": self.adaptive_character_budget.isChecked(),
            "enable_outfit_structure_quality": self.outfit_structure_quality.isChecked(),
            "enable_prop_symbol_quality": self.prop_symbol_quality.isChecked(),
            "enable_character_wide_identity": self.character_wide_identity.isChecked(),
            "background_mode": self.background.currentData(),
        }

    def set_busy(self, busy: bool):
        self.run_button.setEnabled(not busy)
        self.open_button.setEnabled(not busy)
        self.run_button.setText("処理中…" if busy else "ミニマル化")

    def set_result_available(self, available: bool):
        self.save_svg_button.setEnabled(available)
        self.save_png_button.setEnabled(available)
