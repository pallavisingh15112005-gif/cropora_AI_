"""Cropora Mandi — commodity and mandi catalog.

Every entry is tied to the real Agmarknet master data:

* ``commodity.agmarknet_id`` is the commodity id used by the
  ``api.agmarknet.gov.in/v1`` report endpoints.
* ``market.market_id`` / ``market.state_id`` are the default APMC ids. Agmarknet
  lists the same mandi under different ids for different crops, so
  :mod:`trading.agmarknet` keeps a per-commodity directory and prefers the id
  that actually reports each crop.
"""

from __future__ import annotations

from dataclasses import dataclass

UNIT = "quintal"


@dataclass(frozen=True)
class Commodity:
    key: str
    name: str
    local_name: str
    category: str
    agmarknet_id: int
    icon: str = ":material/eco:"


@dataclass(frozen=True)
class Market:
    key: str
    name: str
    state: str
    market_id: int
    state_id: int
    known_for: str
    matchers: tuple[str, ...] = ()


COMMODITIES: tuple[Commodity, ...] = (
    # Vegetables
    Commodity("tomato", "Tomato", "Tamatar", "Vegetables", 65, ":material/nutrition:"),
    Commodity("onion", "Onion", "Pyaz", "Vegetables", 23, ":material/nutrition:"),
    Commodity("potato", "Potato", "Aloo", "Vegetables", 24, ":material/nutrition:"),
    Commodity("cauliflower", "Cauliflower", "Phool gobhi", "Vegetables", 31, ":material/nutrition:"),
    Commodity("cabbage", "Cabbage", "Patta gobhi", "Vegetables", 126, ":material/nutrition:"),
    Commodity("green_chilli", "Green chilli", "Hari mirch", "Vegetables", 73, ":material/nutrition:"),
    Commodity("garlic", "Garlic", "Lehsun", "Vegetables", 25, ":material/nutrition:"),
    Commodity("ginger", "Ginger", "Adrak", "Vegetables", 87, ":material/nutrition:"),
    # Fruits
    Commodity("apple", "Apple", "Seb", "Fruits", 17, ":material/nutrition:"),
    Commodity("banana", "Banana", "Kela", "Fruits", 19, ":material/nutrition:"),
    Commodity("mango", "Mango", "Aam", "Fruits", 20, ":material/nutrition:"),
    Commodity("pomegranate", "Pomegranate", "Anar", "Fruits", 160, ":material/nutrition:"),
    Commodity("grapes", "Grapes", "Angoor", "Fruits", 22, ":material/nutrition:"),
    # Cereals
    Commodity("wheat", "Wheat", "Gehun", "Cereals", 1, ":material/grain:"),
    Commodity("paddy", "Paddy", "Dhan", "Cereals", 2, ":material/grain:"),
    Commodity("basmati", "Basmati rice", "Basmati chawal", "Cereals", 569, ":material/grain:"),
    Commodity("rice", "Rice", "Chawal", "Cereals", 3, ":material/grain:"),
    Commodity("maize", "Maize", "Makka", "Cereals", 4, ":material/grain:"),
    # Pulses and oilseeds
    Commodity("soybean", "Soybean", "Soyabean", "Pulses & oilseeds", 13, ":material/spa:"),
    Commodity("gram", "Gram", "Chana", "Pulses & oilseeds", 6, ":material/spa:"),
    Commodity("mustard", "Mustard seed", "Sarson", "Pulses & oilseeds", 12, ":material/spa:"),
    # Cash crops
    Commodity("cotton", "Cotton", "Kapas", "Cash crops", 15, ":material/apparel:"),
)

MARKETS: tuple[Market, ...] = (
    Market(
        "azadpur", "Azadpur mandi", "Delhi", 3445, 25, "fruits & vegetables",
        (r"^apmc azadpur$",),
    ),
    Market(
        "vashi", "Mumbai APMC (Vashi)", "Maharashtra", 154, 20, "fruits & vegetables",
        (r"^apmc mumbai$", r"^mumbai- fruit", r"^mumbai.*onion"),
    ),
    Market(
        "bengaluru", "Binny Mill APMC", "Karnataka", 100, 16, "fruits & vegetables",
        (r"^binny mill", r"^bengaluru", r"^bangalore"),
    ),
    Market(
        "kolar", "Kolar APMC", "Karnataka", 112, 16, "vegetables",
        (r"^kolar apmc$",),
    ),
    Market(
        "indore", "Indore mandi", "Madhya Pradesh", 3046, 19, "soybean & grains",
        (r"^indore apmc$", r"^indore"),
    ),
    Market(
        "ludhiana", "Ludhiana mandi", "Punjab", 1443, 28, "wheat & paddy",
        (r"^ludhiana apmc$", r"^ludhiana"),
    ),
    Market(
        "lasalgaon", "Lasalgaon APMC", "Maharashtra", 161, 20, "onion",
        (r"^apmc lasalgaon$", r"^lasalgaon"),
    ),
    Market(
        "bowenpally", "Bowenpally mandi", "Telangana", 1868, 32, "vegetables",
        (r"^bowenpally apmc$", r"^bowenpally"),
    ),
)

COMMODITY_BY_KEY: dict[str, Commodity] = {item.key: item for item in COMMODITIES}
MARKET_BY_KEY: dict[str, Market] = {item.key: item for item in MARKETS}

CATEGORIES: tuple[str, ...] = (
    "Vegetables",
    "Fruits",
    "Cereals",
    "Pulses & oilseeds",
    "Cash crops",
)

# What each APMC actually reports, so we only ask Agmarknet for relevant crops.
MARKET_COMMODITIES: dict[str, tuple[str, ...]] = {
    "azadpur": (
        "tomato", "onion", "potato", "cauliflower", "cabbage", "green_chilli",
        "garlic", "ginger", "apple", "banana", "mango", "pomegranate", "grapes",
    ),
    "vashi": (
        "tomato", "onion", "potato", "cauliflower", "cabbage", "green_chilli",
        "ginger", "apple", "banana", "mango", "pomegranate", "grapes",
        "gram", "mustard", "soybean", "cotton",
    ),
    "bengaluru": (
        "tomato", "onion", "potato", "cauliflower", "cabbage", "green_chilli",
        "ginger", "apple", "banana", "mango", "pomegranate", "grapes",
        "gram", "mustard", "soybean",
    ),
    "kolar": (
        "tomato", "onion", "potato", "cauliflower", "cabbage", "green_chilli",
        "ginger", "banana", "mango", "grapes", "gram",
    ),
    "indore": (
        "wheat", "paddy", "maize", "gram", "soybean", "mustard",
        "garlic", "onion", "apple", "grapes", "pomegranate",
    ),
    "ludhiana": (
        "wheat", "paddy", "basmati", "rice", "maize", "cotton",
        "apple", "grapes", "mango", "pomegranate", "potato", "onion",
    ),
    "lasalgaon": (
        "onion", "potato", "garlic", "tomato", "pomegranate", "grapes",
        "gram", "soybean", "mustard", "cotton",
    ),
    "bowenpally": (
        "tomato", "onion", "potato", "cauliflower", "cabbage", "green_chilli",
        "ginger", "banana", "apple", "mango", "grapes", "gram",
    ),
}


def commodities_for_market(market_key: str) -> list[str]:
    keys = MARKET_COMMODITIES.get(market_key, tuple(item.key for item in COMMODITIES))
    return list(keys)


def starter_commodities(market_key: str, limit: int = 6) -> list[str]:
    """Small, popular basket used for the first automatic sync of a mandi.

    A full mandi sync can take several minutes because Agmarknet is slow, so the
    app fetches these first and lets the user pull the rest with Refresh.
    """
    return commodities_for_market(market_key)[:limit]


def get_commodity(key: str) -> Commodity:
    return COMMODITY_BY_KEY[key]


def get_market(key: str) -> Market:
    return MARKET_BY_KEY[key]


def commodity_label(key: str) -> str:
    commodity = COMMODITY_BY_KEY[key]
    return f"{commodity.name} ({commodity.local_name})"


def market_label(key: str) -> str:
    market = MARKET_BY_KEY[key]
    return f"{market.name}, {market.state}"


def commodities_in(category: str | None = None) -> list[Commodity]:
    if not category or category == "All":
        return list(COMMODITIES)
    return [item for item in COMMODITIES if item.category == category]
