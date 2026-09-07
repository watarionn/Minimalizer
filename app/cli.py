from __future__ import annotations
import argparse
from pathlib import Path
from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.io.svg_exporter import export_svg
from minimalize_engine.io.image_exporter import export_png, export_webp


def build_parser():
    p = argparse.ArgumentParser(description="Minimalize an image into simple geometric shapes.")
    p.add_argument("input")
    p.add_argument("-o", "--output", default="minimalized.svg")
    p.add_argument("--png")
    p.add_argument("--webp")
    p.add_argument("--level", type=int, default=4, choices=range(1, 6))
    p.add_argument("--colors", type=int)
    p.add_argument("--max-shapes", type=int)
    p.add_argument("--padding", type=float)
    p.add_argument("--background", choices=["source", "white", "transparent", "custom"])
    p.add_argument("--no-lines", action="store_true")
    p.add_argument("--no-layer-composition", action="store_true")
    p.add_argument("--no-macro-underlays", action="store_true")
    p.add_argument("--no-composition-skeleton", action="store_true")
    p.add_argument("--no-multiscale", action="store_true")
    p.add_argument("--no-semantics", action="store_true")
    p.add_argument("--no-design-primitives", action="store_true")
    p.add_argument("--no-design-palette", action="store_true")
    p.add_argument("--no-patterns", action="store_true")
    p.add_argument("--no-auto-retry", action="store_true")
    p.add_argument("--ignore-alpha", action="store_true")
    p.add_argument("--quality-report", action="store_true")
    p.add_argument("--no-global-shape-value", action="store_true", help="disable global shape-value pruning")
    p.add_argument("--no-global-shape-cleanup", action="store_true", help="disable final thin/micro/isolation/merge/simplify shape cleanup")
    p.add_argument("--no-character-structure", action="store_true")
    p.add_argument("--no-body-primitives", action="store_true")
    p.add_argument("--no-hand-analysis", action="store_true")
    p.add_argument("--no-hand-primitives", action="store_true")
    p.add_argument("--no-hand-geometry-validation", action="store_true")
    p.add_argument("--no-hand-validation", action="store_true")
    p.add_argument("--no-hand-quality", action="store_true")
    p.add_argument("--no-limb-geometry-refine", action="store_true")
    p.add_argument("--no-hair-body-guard", action="store_true")
    p.add_argument("--no-character-layout", action="store_true")
    p.add_argument("--no-character-quality", action="store_true")
    p.add_argument("--no-character-auto-retry", action="store_true")
    p.add_argument("--no-pose-proxy", action="store_true")
    p.add_argument("--character-preset", choices=["auto","portrait","upper_body","full_body","chibi"])
    p.add_argument("--no-face-rules", action="store_true")
    p.add_argument("--face-primitives", action="store_true", help="draw dedicated face base/eye/mouth shapes (default: off)")
    p.add_argument("--no-face-validation", action="store_true")
    p.add_argument("--no-face-geometry-quality", action="store_true")
    p.add_argument("--no-face-contour-fit", action="store_true")
    p.add_argument("--no-face-boundary-guard", action="store_true")
    p.add_argument("--no-face-identity-budget", action="store_true")
    p.add_argument("--no-face-identity-validation", action="store_true")
    p.add_argument("--no-hair-rules", action="store_true")
    p.add_argument("--no-outfit-rules", action="store_true")
    p.add_argument("--no-prop-rules", action="store_true")
    p.add_argument("--no-adaptive-character-budget", action="store_true")
    p.add_argument("--no-outfit-structure-quality", action="store_true")
    p.add_argument("--no-prop-symbol-quality", action="store_true")
    p.add_argument("--no-character-wide-identity", action="store_true")
    p.add_argument("--debug-dir")
    return p


def main():
    args = build_parser().parse_args()
    overrides = {}
    if args.colors is not None:
        overrides["palette_colors"] = args.colors
    if args.max_shapes is not None:
        overrides["target_max_shapes"] = args.max_shapes
    if args.padding is not None:
        overrides["canvas_padding"] = args.padding
    if args.background is not None:
        overrides["background_mode"] = args.background
    if args.no_lines:
        overrides["line_mode"] = "none"
    if args.no_layer_composition:
        overrides["enable_layer_composition"] = False
    if args.no_macro_underlays:
        overrides["enable_macro_underlays"] = False
    if args.no_composition_skeleton:
        overrides["enable_composition_skeleton"] = False
    if args.no_multiscale:
        overrides["enable_multiscale_analysis"] = False
    if args.no_semantics:
        overrides["enable_pseudo_semantics"] = False
    if args.no_design_primitives:
        overrides["enable_design_primitives"] = False
    if args.no_design_palette:
        overrides["enable_design_palette"] = False
    if args.no_patterns:
        overrides["enable_pattern_recognition"] = False
    if args.no_auto_retry:
        overrides["enable_auto_retry"] = False
    if args.ignore_alpha:
        overrides["respect_source_alpha"] = False
    if args.no_global_shape_value:
        overrides["enable_global_shape_value"] = False
    if args.no_global_shape_cleanup:
        overrides["enable_global_shape_cleanup"] = False
    if args.no_character_structure:
        overrides["enable_character_structure"] = False
    if args.no_body_primitives:
        overrides["enable_body_primitives"] = False
    if args.no_hand_analysis:
        overrides["enable_hand_analysis"] = False
    if args.no_hand_primitives:
        overrides["enable_hand_primitives"] = False
    if args.no_hand_geometry_validation:
        overrides["enable_hand_geometry_validation"] = False
    if args.no_hand_validation:
        overrides["enable_hand_validation"] = False
    if args.no_hand_quality:
        overrides["enable_hand_quality"] = False
    if args.no_limb_geometry_refine:
        overrides["enable_limb_geometry_refine"] = False
    if args.no_hair_body_guard:
        overrides["enable_hair_body_guard"] = False
    if args.no_character_layout:
        overrides["enable_character_layout"] = False
    if args.no_character_quality:
        overrides["enable_character_quality"] = False
    if args.no_character_auto_retry:
        overrides["enable_character_auto_retry"] = False
    if args.no_pose_proxy:
        overrides["enable_pose_proxy"] = False
    if args.character_preset:
        overrides["character_preset"] = args.character_preset
    if args.no_face_rules:
        overrides["enable_face_rules"] = False
    if args.face_primitives:
        overrides["enable_face_primitives"] = True
    if args.no_face_validation:
        overrides["enable_face_validation"] = False
    if args.no_face_geometry_quality:
        overrides["enable_face_geometry_quality"] = False
    if args.no_face_contour_fit:
        overrides["enable_face_contour_fit"] = False
    if args.no_face_boundary_guard:
        overrides["enable_face_boundary_guard"] = False
    if args.no_face_identity_budget:
        overrides["enable_face_identity_budget"] = False
    if args.no_face_identity_validation:
        overrides["enable_face_identity_validation"] = False
    if args.no_hair_rules:
        overrides["enable_hair_rules"] = False
    if args.no_outfit_rules:
        overrides["enable_outfit_rules"] = False
    if args.no_prop_rules:
        overrides["enable_prop_rules"] = False
    if args.no_adaptive_character_budget:
        overrides["enable_adaptive_character_budget"] = False
    if args.no_outfit_structure_quality:
        overrides["enable_outfit_structure_quality"] = False
    if args.no_prop_symbol_quality:
        overrides["enable_prop_symbol_quality"] = False
    if args.no_character_wide_identity:
        overrides["enable_character_wide_identity"] = False
    if args.debug_dir:
        overrides["debug_mode"] = True
        overrides["debug_output_dir"] = args.debug_dir

    cfg = MinimalizeConfig.from_level(args.level, **overrides)
    scene = minimalize(args.input, cfg)

    export_svg(scene, args.output)
    if args.png:
        export_png(scene, args.png)
    if args.webp:
        export_webp(scene, args.webp)

    print(f"SVG: {Path(args.output).resolve()}")
    print(f"shapes: {scene.metadata['shape_count']}")
    print(f"analysis: {scene.width}x{scene.height}")
    print(f"source: {scene.metadata['source_width']}x{scene.metadata['source_height']}")
    if args.quality_report:
        print(f"quality: {scene.metadata.get('quality', {})}")
        print(f"auto_retry_attempts: {scene.metadata.get('auto_retry_attempts', 0)}")
        print(f"character_retry_attempts: {scene.metadata.get('character_retry_attempts', 0)}")
        print(f"face_retry_attempts: {scene.metadata.get('face_retry_attempts', 0)}")
        cq = scene.metadata.get("character_quality")
        if cq:
            print(f"character_quality: {cq.get('score', 0):.3f}")
            print(f"character_retry_reasons: {cq.get('retry_reasons', [])}")
        wide = scene.metadata.get("character_wide_identity")
        if wide:
            print(f"character_wide_identity: {wide.get('score', 0):.3f}")
        history = scene.metadata.get("retry_history", [])
        if history:
            print(f"retry_history: {history}")
        print(f"subject_mode: {scene.metadata.get('subject_mode', False)}")


if __name__ == "__main__":
    main()
