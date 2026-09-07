from __future__ import annotations

from enum import StrEnum
from typing import Literal


class CharacterPartType(StrEnum):
    SUBJECT = "subject"
    HEAD = "head"
    FACE = "face"
    HAIR = "hair"
    BANGS = "bangs"
    SIDE_HAIR_LEFT = "side_hair_left"
    SIDE_HAIR_RIGHT = "side_hair_right"
    BACK_HAIR = "back_hair"
    HAIR_FEATURE = "hair_feature"
    TORSO = "torso"
    OUTFIT = "outfit"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"
    LEFT_SHOE = "left_shoe"
    RIGHT_SHOE = "right_shoe"
    PROP = "prop"
    ACCESSORY = "accessory"
    UNKNOWN = "unknown"


SideHint = Literal["left", "right", "center", "unknown"]
CharacterPreset = Literal["auto", "portrait", "upper_body", "full_body", "chibi"]


PART_PRIORITY: dict[CharacterPartType, float] = {
    CharacterPartType.SUBJECT: 0.5,
    CharacterPartType.HEAD: 1.20,
    CharacterPartType.FACE: 1.35,
    CharacterPartType.HAIR: 1.20,
    CharacterPartType.BANGS: 1.15,
    CharacterPartType.SIDE_HAIR_LEFT: 1.05,
    CharacterPartType.SIDE_HAIR_RIGHT: 1.05,
    CharacterPartType.BACK_HAIR: 0.95,
    CharacterPartType.HAIR_FEATURE: 1.10,
    CharacterPartType.TORSO: 1.10,
    CharacterPartType.OUTFIT: 0.95,
    CharacterPartType.LEFT_ARM: 0.92,
    CharacterPartType.RIGHT_ARM: 0.92,
    CharacterPartType.LEFT_LEG: 0.88,
    CharacterPartType.RIGHT_LEG: 0.88,
    CharacterPartType.LEFT_SHOE: 0.75,
    CharacterPartType.RIGHT_SHOE: 0.75,
    CharacterPartType.PROP: 1.12,
    CharacterPartType.ACCESSORY: 0.82,
    CharacterPartType.UNKNOWN: 0.55,
}


PART_DEFAULT_BUDGET: dict[CharacterPartType, int] = {
    CharacterPartType.FACE: 4,
    CharacterPartType.HAIR: 6,
    CharacterPartType.TORSO: 5,
    CharacterPartType.LEFT_ARM: 2,
    CharacterPartType.RIGHT_ARM: 2,
    CharacterPartType.LEFT_LEG: 2,
    CharacterPartType.RIGHT_LEG: 2,
    CharacterPartType.OUTFIT: 3,
    CharacterPartType.PROP: 2,
    CharacterPartType.ACCESSORY: 2,
}


PART_DEFAULT_ABSTRACTION: dict[CharacterPartType, float] = {
    CharacterPartType.FACE: 0.65,
    CharacterPartType.HAIR: 0.75,
    CharacterPartType.HEAD: 0.72,
    CharacterPartType.TORSO: 0.85,
    CharacterPartType.OUTFIT: 0.95,
    CharacterPartType.LEFT_ARM: 0.95,
    CharacterPartType.RIGHT_ARM: 0.95,
    CharacterPartType.LEFT_LEG: 1.00,
    CharacterPartType.RIGHT_LEG: 1.00,
    CharacterPartType.PROP: 0.85,
    CharacterPartType.ACCESSORY: 1.15,
    CharacterPartType.UNKNOWN: 1.00,
}
