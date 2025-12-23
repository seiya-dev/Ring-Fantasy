#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame
from .game_constants import TILE_SIZE, SCALE, ITEMS, MAX_ITEMS_COUNT

def get_item_type_ids(item_type):
    return [item_id for item_id, data in ITEMS.items() if data["type"] == item_type]

class IState:
    def enter(self):
        pass

    def exit(self):
        pass

    def handle_event(self, event: pygame.event.Event):
        pass

    def update(self, delta_time: float):
        pass

    def render(self, screen: pygame.Surface):
        pass

class Player:
    _PER_LEVEL_EXP = 600
    _LEVEL_EXPONENT = 200
    
    _HP_PER_LEVEL = 4
    _MP_PER_LEVEL = 2
    
    _MULT_HP_MP = 8
    _MULT_STR = 2
    
    _DEFAULT_HP = 20
    _DEFAULT_EX = 10
    
    _MAX_LEVEL = 990
    _MAX_EXP = 98_306_600
    _MAX_GOLD = 999_999_900
    _MAX_4DIGIT = 9999
    _MAX_3DIGIT = 999
    
    def __init__(self, game: "Game"):
        self.game = game
        
    def create(self, name = "Eric"):
        self.name = name
        
        start_pos = self.game.events.get(0)[1]
        parts = [p.strip() for p in start_pos.split(",")]
        
        if len(parts) == 4:
            map_name, sx, sy, dir_code = parts[0], int(parts[1]), int(parts[2]), int(parts[3])
        else:
            raise Exception("Bad Map Value!")
        
        self.map_name = map_name
        self.x = sx
        self.y = sy
        self.facing = dir_code
        
        self.hp = self._DEFAULT_HP
        self.mp = self._DEFAULT_EX
        self.exp = 0
        
        self.gold = 0
        self.power = 0
        
        self.mult_hp = 0
        self.mult_mp = 0
        self.mult_str = 0
        
        self.inventory = {}
        self.equip = {"sword":0,"armor":0,"ring":0,}
        self.spells = list()
        
        self.score = 10000
        self.bonus_code = 0
    
    def change_name(self, name):
        self.name = name
    
    def get_hero_level(self):
        cur_exp = self.exp
        if cur_exp >= self._MAX_EXP:
            return self._MAX_LEVEL
        level = 1
        
        per_level_exp = self._PER_LEVEL_EXP
        while cur_exp >= per_level_exp:
            level += 1
            cur_exp -= per_level_exp
            per_level_exp += self._LEVEL_EXPONENT
        
        return level
    
    def next_level_exp(self):
        cur_exp = self.exp
        if cur_exp >= self._MAX_EXP:
            return 0
        level = 1
        
        per_level_exp = self._PER_LEVEL_EXP
        while cur_exp >= per_level_exp:
            level += 1
            cur_exp -= per_level_exp
            per_level_exp += self._LEVEL_EXPONENT
        
        return per_level_exp - cur_exp
    
    def get_hero_max_hp(self):
        # LV1 HP 20, +4 HP per level
        max_hp = self._DEFAULT_HP + (self.get_hero_level() - 1) * self._HP_PER_LEVEL + self._MULT_HP_MP * self.mult_hp
        return self._MAX_4DIGIT if max_hp > self._MAX_4DIGIT else max_hp
    
    def get_hero_max_mp(self):
        # LV1 MP 10, +2 MP per level
        max_mp = self._DEFAULT_EX + (self.get_hero_level() - 1) * self._MP_PER_LEVEL + self._MULT_HP_MP * self.mult_mp
        return self._MAX_4DIGIT if max_mp > self._MAX_4DIGIT else max_mp
    
    def get_hero_str(self):
        # LV1 STR 10, +1 STR per level
        # self.mult_str - Soul Stone STR+2, Blood Stone STR+4 (+1, +2)
        c_str = self._DEFAULT_EX + (self.get_hero_level() - 1) + self._MULT_STR * self.mult_str
        
        # "Phoenix Ring"
        if self.equip["ring"] in get_item_type_ids("ring") and self.equip["ring"] % 300 == 5:
            c_str += self.get_hero_level()
        
        return self._MAX_3DIGIT if c_str > self._MAX_3DIGIT else c_str
    
    def get_hero_atk(self):
        # Same as STR + Sword ATK + Odin ATK
        c_atk = self.get_hero_str()
        
        if self.equip["sword"] in get_item_type_ids("sword"):
            c_atk += ITEMS.get(self.equip["sword"])["value"] or 0
        
        # "Odin Ring"
        if self.equip["ring"] in get_item_type_ids("ring") and self.equip["ring"] % 300 == 4:
            c_atk += self.get_hero_level()
        
        return self._MAX_3DIGIT if c_atk > self._MAX_3DIGIT else c_atk
    
    def get_hero_def(self):
        # Same as STR + Armor DEF + Titan DEF
        c_def = self.get_hero_str()
        
        if self.equip["armor"] in get_item_type_ids("armor"):
            c_def += ITEMS.get(self.equip["armor"])["value"] or 0
        
        # "Titan Ring"
        if self.equip["ring"] in get_item_type_ids("ring") and self.equip["ring"] % 300 == 3:
            c_def += self.get_hero_level()
        
        return self._MAX_3DIGIT if c_def > self._MAX_3DIGIT else c_def
    
    def add_exp(self, count=50):
        self.exp += count
        if self.exp > self._MAX_EXP:
            self.exp = self._MAX_EXP
    
    def add_gold(self, count=50):
        self.gold += count
        if self.gold > self._MAX_GOLD:
            self.gold = self._MAX_GOLD
    
    def add_item(self, iid, count=1):
        current = self.inventory.get(iid, 0)
        self.inventory[iid] = min(MAX_ITEMS_COUNT, current + max(1, int(count)))
    
    def has_item(self, iid):
        return self.inventory.get(iid, 0)
    
    def consume_item(self, iid, count=1):
        if self.has_item(iid) > 0:
            self.inventory[iid] -= count
            if self.inventory[iid] <= 0:
                del self.inventory[iid]
            return True
        return False
    
    def _use_item(self, iid: int):
        max_hp, max_mp = getattr(self, "get_hero_max_hp", lambda: 0)(), getattr(self, "get_hero_max_mp", lambda: 0)()
        
        item = ITEMS.get(iid)
        if self.consume_item(iid, 1):
            if iid in (1,4):
                self.hp = min(max_hp, self.hp + item['value'])
            if iid in (2,):
                self.mp = min(max_mp, self.mp + item['value'])
            if iid in (3,):
                self.power += 1
            if iid in (5,):
                self.hp = max_hp
                self.mp = max_mp
            return f"{self.name} uses {item['name']}."
    
    def move(self, dx, dy):
        self.x = dx
        self.y = dy
        
        self.score -= 1
        
        if self.score < 0:
            self.score = 0
    
    def draw(self, surface, cam_x, cam_y):
        frames = [3*12, 1*12, 2*12, 0]
        frame_id = frames[self.facing] or 0
        sprite = self.game.heroset[frame_id]
        sx = self.x * TILE_SIZE * SCALE - cam_x
        sy = self.y * TILE_SIZE * SCALE - cam_y
        surface.blit(sprite, (sx, sy))
