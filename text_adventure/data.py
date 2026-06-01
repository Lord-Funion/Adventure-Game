"""Shared game data.

Keeping spells, monsters, and item names here makes the story files easier to
read and avoids magic strings scattered through combat and shops.
"""


SPELLS = {
    "Fireball": {
        "damage": 10,
        "manaCost": 5,
        "effects": {"burn": 3},
        "description": "Deals 10 damage and sets the target burning.",
    },
    "Arcane Blast": {
        "damage": 0,
        "manaCost": 15,
        "effects": {"stun": 2},
        "description": "Stuns an enemy for 2 turns.",
    },
    "Thunderstorm": {
        "damage": 20,
        "manaCost": 20,
        "description": "Deals 20 damage.",
    },
    "Restoration Incantation": {
        "healing": 10,
        "manaCost": 7,
        "description": "Heals 10 health in battle.",
    },
    "Frost Nova": {
        "damage": 12,
        "manaCost": 12,
        "effects": {"stun": 1},
        "description": "Deals 12 damage and chills an enemy still for 1 turn.",
    },
    "Solar Beam": {
        "damage": 30,
        "manaCost": 25,
        "effects": {"burn": 2},
        "description": "Deals 30 damage and leaves a bright burn.",
    },
    "Life Bloom": {
        "healing": 25,
        "manaCost": 15,
        "description": "Heals 25 health in battle.",
    },
    "Lockio Reducto": {
        "description": "Unlocks sealed doors.",
    },
}


FROG_ATTACKS = {
    "Tongue Slap": {
        "damage": 8,
        "energyCost": 0,
        "description": "A free snapping smack from a very serious frog.",
    },
    "Bubble Burp": {
        "damage": 14,
        "energyCost": 6,
        "effects": {"burn": 2},
        "description": "Deals 14 damage and leaves the target covered in fizzy bubbles.",
    },
    "Royal Croak": {
        "damage": 0,
        "energyCost": 8,
        "effects": {"stun": 2},
        "description": "A royal croak that stuns an enemy for 2 turns.",
    },
    "Snack Break": {
        "healing": 20,
        "energyCost": 7,
        "description": "The frog shares emergency snacks and heals 20 health.",
    },
    "Moon Leap": {
        "damage": 22,
        "energyCost": 12,
        "effects": {"stun": 1},
        "description": "Deals 22 damage and lands with a stunning moonlit bounce.",
    },
    "Dragonfly Dive": {
        "damage": 30,
        "energyCost": 16,
        "effects": {"burn": 2},
        "description": "Deals 30 damage with a fiery dive after an imaginary dragonfly.",
    },
}


MONSTERS = {
    "goblin": {
        "health": 20,
        "damage": 5,
        "attacks": ["punch", "screech", "headbutt"],
    },
    "troll": {
        "health": 30,
        "damage": 7,
        "attacks": ["club", "slam", "bite"],
    },
    "skeleton": {
        "health": 15,
        "damage": 12,
        "attacks": ["bone club", "bone scare", "bone headbutt"],
    },
    "werewolf": {
        "health": 40,
        "damage": 15,
        "attacks": ["claw", "bite", "howl"],
    },
    "ogre": {
        "health": 50,
        "damage": 25,
        "attacks": ["big club", "super smash", "stomp"],
    },
    "witch": {
        "health": 35,
        "damage": 10,
        "attacks": ["poison", "curse", "hex"],
    },
    "vampire": {
        "health": 45,
        "damage": 17,
        "reward": 20,
        "attacks": ["transform into bat", "fangs", "suck blood"],
    },
    "ice goblin": {
        "health": 35,
        "damage": 14,
        "reward": 15,
        "attacks": ["snowball uppercut", "cold toes", "icicle bonk"],
    },
    "shadow knight": {
        "health": 60,
        "damage": 20,
        "reward": 25,
        "attacks": ["gloom blade", "helmet glare", "dramatic cape slap"],
    },
    "crystal dragon": {
        "health": 80,
        "damage": 24,
        "reward": 35,
        "attacks": ["sparkle breath", "tail sweep", "gemstone sneeze"],
    },
    "lord dreadbiscuit": {
        "health": 95,
        "damage": 26,
        "reward": 50,
        "attacks": ["cookie crumble", "royal tantrum", "butter curse"],
    },
}


LOOT_DROPS = [
    "Suspicious Gold Nugget",
    "Metal Scraps of Mystery",
    "Pointy Monster Tooth",
    "Rotten Flesh",
    "Small Health Potion",
    "Mystery Goop",
    "Strange Liquid",
    "Gnarled Toenail",
    "Moon Cheese",
    "Dragon Scale Chip",
    "Haunted Button",
]


SELLABLE_LOOT = {
    "Suspicious Gold Nugget",
    "Metal Scraps of Mystery",
    "Pointy Monster Tooth",
    "Rotten Flesh",
    "Mystery Goop",
    "Strange Liquid",
    "Gnarled Toenail",
    "Moon Cheese",
    "Dragon Scale Chip",
    "Haunted Button",
}
