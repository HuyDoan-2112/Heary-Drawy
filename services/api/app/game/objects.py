"""Demo catalog of secret pictures. Server-only: clients receive a picture only when authorized.

Flat stand-ins in the approved art style until Feature 04 brings real 3D models.
"""

from dataclasses import dataclass

_INK = 'stroke="#1B2B4B" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"'


@dataclass(frozen=True)
class SecretObject:
    object_id: str
    display_name: str
    svg: str
    # Visual features the AI checks in the Speaker's words and the drawing (Feature 07).
    features: tuple[str, ...] = ()


def _svg(body: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">{body}</svg>'


CATALOG: tuple[SecretObject, ...] = (
    SecretObject(
        "apple",
        "Apple",
        _svg(
            f'<path d="M100 56C78 38 36 48 32 98c-4 52 32 90 54 86 8-2 10-5 14-5s6 3 14 5c22 4 58-34 54-86-4-50-46-60-68-42z" fill="#E5483D" {_INK}/>'
            '<path d="M100 56c0-14 4-26 12-36" fill="none" stroke="#8B5A2B" stroke-width="7" stroke-linecap="round"/>'
            f'<path d="M112 34c10-14 30-16 42-8-6 14-26 22-42 8z" fill="#35B26B" {_INK}/>'
        ),
        features=("red", "round body", "stem on top", "green leaf"),
    ),
    SecretObject(
        "ball",
        "Ball",
        _svg(
            f'<circle cx="100" cy="100" r="70" fill="#2F80ED" {_INK}/>'
            f'<path d="M30 100h140M100 30c-30 30-30 110 0 140M100 30c30 30 30 110 0 140" fill="none" {_INK}/>'
        ),
        features=("blue", "round", "lines across it"),
    ),
    SecretObject(
        "house",
        "House",
        _svg(
            f'<rect x="50" y="96" width="100" height="74" fill="#7CC8FF" {_INK}/>'
            f'<path d="M36 100 L100 44 L164 100 Z" fill="#FF6F59" {_INK}/>'
            f'<rect x="88" y="124" width="24" height="46" fill="#8B5A2B" {_INK}/>'
            f'<rect x="62" y="110" width="18" height="18" fill="#fff" {_INK}/>'
            f'<rect x="120" y="110" width="18" height="18" fill="#fff" {_INK}/>'
        ),
        features=("square walls", "triangle roof", "door", "two windows"),
    ),
    SecretObject(
        "sun",
        "Sun",
        _svg(
            f'<circle cx="100" cy="100" r="44" fill="#FFC83D" {_INK}/>'
            f'<path d="M100 20v24M100 156v24M20 100h24M156 100h24M43 43l17 17M140 140l17 17M157 43l-17 17M60 140l-17 17" fill="none" {_INK}/>'
        ),
        features=("yellow", "round middle", "rays all around"),
    ),
    SecretObject(
        "fish",
        "Fish",
        _svg(
            f'<path d="M30 100c30-46 90-50 120 0-30 50-90 46-120 0z" fill="#FF9F43" {_INK}/>'
            f'<path d="M150 100l30-30v60z" fill="#FF9F43" {_INK}/>'
            '<circle cx="66" cy="94" r="7" fill="#1B2B4B"/>'
        ),
        features=("orange", "oval body", "triangle tail", "eye"),
    ),
    SecretObject(
        "tree",
        "Tree",
        _svg(
            f'<rect x="88" y="120" width="24" height="56" fill="#8B5A2B" {_INK}/>'
            f'<circle cx="100" cy="84" r="54" fill="#35B26B" {_INK}/>'
        ),
        features=("brown trunk", "green round top"),
    ),
)

BY_ID = {item.object_id: item for item in CATALOG}
