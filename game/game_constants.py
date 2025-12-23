#!/usr/bin/env python3
# -*- coding: utf-8 -*-

GAME_TITLE = "Ring Fantasy"
GAME_FONT = "./fonts/NotoSansMono.ttf"

BASE_WIDTH = 320
BASE_HEIGHT = 240
WIN_SCALE = 2
SCALE = 1
FPS = 60

WIDTH = BASE_WIDTH * WIN_SCALE
HEIGHT = BASE_HEIGHT * WIN_SCALE
SHEET_SIZE = 64
TILE_SIZE = 32

GAME_MAPS   = "./data/maps.txt"
EVENTS_DATA = "./data/events.txt"
HELP_TEXT   = "./data/help.txt"
TILESET     = "./tileset_tiles.png"
OBJECTSET   = "./tileset_objects.png"
SPRITESHEET = "./sprites.png"
HEROSET     = "./hero.png"
GAMEICON    = "./icon.png"
SAVE_FILE   = "./savegame.json"

MAX_ITEMS_COUNT = 99

ITEMS = {
    # consumable
      1: { "name": "Potion",      "type": "consumable", "price":  100, "value":  20, "description": "Restore 20 HP."          },
      2: { "name": "Magic Vial",  "type": "consumable", "price":  200, "value":  20, "description": "Restore 20 MP."          },
      3: { "name": "Rainbow Oil", "type": "consumable", "price":  300, "value":   1, "description": "Temporary improve ATK."  },
      4: { "name": "Full Potion", "type": "consumable", "price":  500, "value": 100, "description": "Restore 100 HP."         },
      5: { "name": "Elixir",      "type": "consumable", "price": 1000, "value":   0, "description": "Full restore HP and MP." },
    
    # special
      6: { "name": "Soul Stone",     "type": "special", "price": 0, "value": 1, "description": "STR +2."                          },
      7: { "name": "Blood Stone",    "type": "special", "price": 0, "value": 2, "description": "STR +4."                          },
      8: { "name": "Life Stone",     "type": "special", "price": 0, "value": 1, "description": "HP +8."                           },
      9: { "name": "Magic Stone",    "type": "special", "price": 0, "value": 1, "description": "MP +8."                           },
     10: { "name": "Key",            "type": "special", "price": 0, "value": 1, "description": "Opens locked doors."              },
     11: { "name": "Treasure Radar", "type": "special", "price": 0, "value": 1, "description": "Shows where treasure is located." },
     12: { "name": "Shadow's Cloak", "type": "special", "price": 0, "value": 1, "description": "Allows to pass through walls"     },
    
    # swords
    100: { "name": "",             "type": "sword", "price":    0, "value":  0, "description": ""                                 },
    101: { "name": "Short Sword",  "type": "sword", "price":  100, "value":  2, "description": "ATK +2. A basic blade."           },
    102: { "name": "Sword",        "type": "sword", "price":  500, "value":  5, "description": "ATK +5. Sturdy steel sword."      },
    103: { "name": "Sabre",        "type": "sword", "price": 1000, "value":  8, "description": "ATK +8. Curved light blade."      },
    104: { "name": "Board Sword",  "type": "sword", "price": 2000, "value": 12, "description": "ATK +12. Heavy broad blade."      },
    105: { "name": "Claymore",     "type": "sword", "price": 4000, "value": 16, "description": "ATK +16. Two-handed greatsword.", },
    106: { "name": "Falchion",     "type": "sword", "price": 8000, "value": 20, "description": "ATK +20. Wide, heavy blade.",     },
    107: { "name": "Knight Sword", "type": "sword", "price":    0, "value": 24, "description": "ATK +24. Knightly heirloom.",     },
    108: { "name": "Hero Sword",   "type": "sword", "price":    0, "value": 28, "description": "ATK +28. Blade of a true hero.",  },
    109: { "name": "Sun Sword",    "type": "sword", "price":    0, "value": 32, "description": "ATK +32. Holy radiance within.",  },
    
    # armors
    200: { "name": "",              "type": "armor", "price":    0, "value":  0, "description": "",                               },
    201: { "name": "Leather Armor", "type": "armor", "price":  100, "value":  2, "description": "DEF +2. Light leather suit.",    },
    202: { "name": "Quilted Armor", "type": "armor", "price":  500, "value":  5, "description": "DEF +5. Padded protection.",     },
    203: { "name": "Ring Mail",     "type": "armor", "price": 1000, "value":  8, "description": "DEF +8. Linked ring shirt.",     },
    204: { "name": "Scale Mail",    "type": "armor", "price": 2000, "value": 12, "description": "DEF +12. Overlapping scales.",   },
    205: { "name": "Chain Mail",    "type": "armor", "price": 4000, "value": 16, "description": "DEF +16. Interlinked chains.",   },
    206: { "name": "Plate Mail",    "type": "armor", "price": 8000, "value": 20, "description": "DEF +20. Rigid plate armor.",    },
    207: { "name": "Knight Armor",  "type": "armor", "price":    0, "value": 24, "description": "DEF +24. Honored knight plate.", },
    208: { "name": "Hero Armor",    "type": "armor", "price":    0, "value": 28, "description": "DEF +28. Legendary protection.", },
    209: { "name": "Sun Armor",     "type": "armor", "price":    0, "value": 32, "description": "DEF +32. Armor blessed by sun.", },
    
    # rings
    300: { "name": "",             "type": "ring", "price": 0, "value": 0, "description": "",                                    },
    301: { "name": "Shiva Ring",   "type": "ring", "price": 0, "value": 0, "description": "Increases the power of ice spells.",  },
    302: { "name": "Ifrit Ring",   "type": "ring", "price": 0, "value": 0, "description": "Increases the power of fire spells.", },
    303: { "name": "Titan Ring",   "type": "ring", "price": 0, "value": 0, "description": "Increases the defense.",              },
    304: { "name": "Odin Ring",    "type": "ring", "price": 0, "value": 0, "description": "Increases the attack power.",         },
    305: { "name": "Phoenix Ring", "type": "ring", "price": 0, "value": 0, "description": "Legendary ring.",                     },
}

SPELLS = {
    1: { "name": "Ice Arrow",      "type": "ice",    "price":  600, "mp_cost":  3, "power":  6, "description": "Launches a shard of ice — a basic frost spell.",     },
    2: { "name": "Ice Lance",      "type": "ice",    "price": 1200, "mp_cost":  6, "power": 12, "description": "Pierces the target with a mid-power ice spear.",     },
    3: { "name": "Ice Storm",      "type": "ice",    "price": 2400, "mp_cost":  9, "power": 18, "description": "Summons a freezing storm that deals heavy damage.",  },
    4: { "name": "Ice Meteor",     "type": "ice",    "price": 4800, "mp_cost": 12, "power": 24, "description": "Drops an ice meteor — devastating frost magic.",     },
    5: { "name": "Fire Arrow",     "type": "fire",   "price":  600, "mp_cost":  3, "power":  6, "description": "Fires a small bolt of flame — a basic fire spell.",  },
    6: { "name": "Fire Ring",      "type": "fire",   "price": 1200, "mp_cost":  6, "power": 12, "description": "Envelops the target in a ring of fire.",             },
    7: { "name": "Fire Blast",     "type": "fire",   "price": 2400, "mp_cost":  9, "power": 18, "description": "A powerful burst of flame that scorches foes.",      },
    8: { "name": "Fire Meteor",    "type": "fire",   "price": 4800, "mp_cost": 12, "power": 24, "description": "Calls down a blazing meteor — searing devastation.", },
}

SUMMONS = {
    1: { "name": "Summon Shiva",   "type": "summon", "price": 0, "mp_cost": 12, "power":  0, "description": "", },
    2: { "name": "Summon Ifrit",   "type": "summon", "price": 0, "mp_cost": 12, "power":  0, "description": "", },
    3: { "name": "Summon Titan",   "type": "summon", "price": 0, "mp_cost": 12, "power":  0, "description": "", },
    4: { "name": "Summon Odin",    "type": "summon", "price": 0, "mp_cost": 12, "power":  0, "description": "", },
    5: { "name": "Summon Phoenix", "type": "summon", "price": 0, "mp_cost": 12, "power":  0, "description": "", },
}

ENEMIES = {
     1: { "name": "Bat",          "hp":  12, "atk":  8, "def":  8, "res_fire": 100, "res_ice": 100, "crit_chance": 20, "exp":   50, "gold":   50, },
     2: { "name": "Slime",        "hp":  16, "atk": 12, "def": 12, "res_fire":  80, "res_ice": 120, "crit_chance": 20, "exp":   50, "gold":   50, },
     3: { "name": "Scorpion",     "hp":  20, "atk": 16, "def": 16, "res_fire":  80, "res_ice": 120, "crit_chance": 20, "exp":  100, "gold":   50, },
     4: { "name": "Wolf",         "hp":  30, "atk": 20, "def": 20, "res_fire": 100, "res_ice": 100, "crit_chance": 20, "exp":  100, "gold":   50, },
     5: { "name": "Skeleton",     "hp":  40, "atk": 24, "def": 24, "res_fire": 100, "res_ice": 100, "crit_chance": 20, "exp":  100, "gold":  100, },
     6: { "name": "Fire Fox",     "hp":  50, "atk": 28, "def": 28, "res_fire": 120, "res_ice":  80, "crit_chance": 40, "exp":  200, "gold":  200, },
     7: { "name": "Orc",          "hp":  60, "atk": 32, "def": 32, "res_fire": 100, "res_ice": 100, "crit_chance": 20, "exp":  200, "gold":  100, },
     8: { "name": "Minotaur",     "hp":  70, "atk": 36, "def": 36, "res_fire": 100, "res_ice": 100, "crit_chance": 20, "exp":  300, "gold":  100, },
     9: { "name": "Gargoyle",     "hp":  80, "atk": 40, "def": 40, "res_fire": 120, "res_ice":  80, "crit_chance": 20, "exp":  400, "gold":  100, },
    10: { "name": "Hydra",        "hp":  90, "atk": 44, "def": 44, "res_fire":  80, "res_ice": 120, "crit_chance": 40, "exp":  500, "gold":  500, },
    11: { "name": "Green Dragon", "hp": 100, "atk": 48, "def": 48, "res_fire":  80, "res_ice": 120, "crit_chance": 20, "exp": 1000, "gold": 1000, },
    12: { "name": "Fire Dragon",  "hp": 120, "atk": 56, "def": 48, "res_fire": 120, "res_ice":  80, "crit_chance": 20, "exp": 2000, "gold": 2000, },
    13: { "name": "Earth Dragon", "hp": 140, "atk": 56, "def": 56, "res_fire": 100, "res_ice": 100, "crit_chance": 20, "exp": 3000, "gold": 3000, },
    14: { "name": "Robot",        "hp": 160, "atk": 56, "def": 56, "res_fire":  80, "res_ice":  80, "crit_chance": 40, "exp": 5000, "gold": 5000, },
    15: { "name": "Dark King",    "hp": 240, "atk": 64, "def": 64, "res_fire": 100, "res_ice": 100, "crit_chance": 40, "exp":    0, "gold":    0, },
}
