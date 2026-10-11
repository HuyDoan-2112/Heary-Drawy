"""Demo catalog of secret objects. Server-only: clients receive an object only when authorized.

Low-poly food models from Kenney's Food Kit 2.0 (CC0, https://kenney.nl/assets/food-kit), with
textures embedded so each is one GLB file. The PNG beside each model is a render of it, shown
while the 3D model loads and if 3D fails.
"""

from dataclasses import dataclass
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"


@dataclass(frozen=True)
class SecretObject:
    object_id: str
    display_name: str
    # Visual features the AI checks in the Speaker's words and the drawing (Feature 07).
    features: tuple[str, ...]

    @property
    def model_path(self) -> Path:
        return ASSETS / f"{self.object_id}.glb"

    @property
    def image_path(self) -> Path:
        return ASSETS / f"{self.object_id}.png"


CATALOG: tuple[SecretObject, ...] = (
    SecretObject("apple", "Apple", ("red", "round body", "stem on top", "green leaf")),
    SecretObject("banana", "Banana", ("yellow", "long curved shape", "brown tips at the ends")),
    SecretObject("carrot", "Carrot", ("orange", "long pointy shape", "green leaves on top")),
    SecretObject("strawberry", "Strawberry", ("red", "wide top and pointy bottom", "green leaves on top")),
    SecretObject("watermelon", "Watermelon", ("green", "big round shape", "darker green stripes")),
    SecretObject("cupcake", "Cupcake", ("paper cup at the bottom", "brown top", "cherry on top")),
    SecretObject("pizza", "Pizza", ("flat circle", "crust around the edge", "red dots on top")),
    SecretObject("ice_cream", "Ice cream", ("cone at the bottom", "pink scoop on top", "pointy cone tip")),
)

BY_ID = {item.object_id: item for item in CATALOG}
