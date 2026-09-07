from pathlib import Path


def _settings_source():
    root=Path(__file__).parents[1]
    return (root/"gui/settings_panel.py").read_text(encoding="utf-8")


def test_advanced_settings_are_hidden_by_default_in_source():
    text=_settings_source()
    assert "self.advanced_widget.setVisible(False)" in text
    assert 'self.advanced_button = QPushButton("詳細設定を表示")' in text
    assert "self.advanced_button.setCheckable(True)" in text


def test_face_primitives_remain_default_off():
    text=_settings_source()
    marker='self.face_primitives = QCheckBox("顔パーツを描く（目・口・顔ベース）")'
    i=text.index(marker)
    window=text[i:i+500]
    assert "self.face_primitives.setChecked(False)" in window


def test_primary_controls_stay_on_basic_surface():
    text=_settings_source()
    required=[
        "basic_form.addWidget(self.level)",
        "basic_form.addWidget(self.colors)",
        "basic_form.addWidget(self.detail)",
        "basic_form.addWidget(self.merge)",
        "basic_form.addWidget(self.lines)",
        "basic_form.addWidget(self.background)",
    ]
    for marker in required:
        assert marker in text


def test_rc12_version_is_user_visible_and_engine_visible():
    root=Path(__file__).parents[1]
    main=(root/"gui/main_window.py").read_text(encoding="utf-8")
    pipeline=(root/"minimalize_engine/pipeline.py").read_text(encoding="utf-8")
    assert "Minimalizer v0.3.0" in main
    assert '"engine_version":"0.3.0"' in pipeline
