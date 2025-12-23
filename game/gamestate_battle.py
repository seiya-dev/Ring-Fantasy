#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List
import random

import pygame
from .game_constants import WIDTH, HEIGHT, SCALE, SHEET_SIZE, FPS, ENEMIES, ITEMS, SPELLS, SUMMONS
from .game_class import IState

SHEET_SIZE_SCALED = SHEET_SIZE * SCALE
WHITE = (255,255,255)
BLACK = (0,0,0)
GREEN = (0,160,0)
RED   = (220,40,40)
BLUE  = (60,60,220)
GRAY  = (40,40,40)
MAX_DMG = 999

def randomInt() -> int:
    return random.randrange(100)

class BattleState(IState):
    def __init__(self, game: "Game", return_to: IState):
        self.game = game
        self.return_to = return_to
        self.mon_id = -1
        
        # fields: event_pos_x, event_pos_y, win_lose_flag
        self.result = None
        
        # cursor/menu
        self.menu_index = 0
        self.menu_items = ["Attack", "Item", "Cast", "Flee"]
        self.submenu = None  # None / "cast" / "item"
        self.sub_index = 0
    
    def game_delay(self, time = int(FPS * 3)):
        pygame.time.delay(time)
    
    def enter(self):
        # init data
        self.mc = self.game.player
        self.mo = dict(ENEMIES.get(self.mon_id))
        self.mo["max_hp"] = self.mo["hp"]
        self.buffs = 0
        
        self.game_delay()
        self.menu_index = 0
        self.submenu = None
        self.sub_index = 0
        self.wait_end = 0
        
        # states
        self.state = "player" # "action", "player", "monster"
        self.ready = f"{self.mc.name} is ready for the command."
        
        self.messages = []
        self.messages.append((self.ready, BLUE))
    
    def hero_attack(self):
        dmg = self.mc.get_hero_atk() - self.mo["def"]
        if dmg < 1:
            dmg = 1
        
        if self.mc.equip.get("ring") in (304, 305) and self.buffs > 0:
            dmg += self.mc.get_hero_level() * self.buffs * randomInt() // 99
        
        ext_dmg = dmg * randomInt() // 99
        if ext_dmg < 1:
            ext_dmg = 1
        
        dmg += ext_dmg
        if dmg % 2 > 0:
            dmg += 1
        
        is_crit = False
        crit_chance = 20 * (self.mc.power + 1)
        if randomInt() < crit_chance:
            is_crit = True
            dmg += self.mc.power * 2
        else:
            dmg //= 2
        
        dmg = MAX_DMG if dmg > MAX_DMG else round(dmg)
        self.mo["hp"] -= dmg
        if self.mo["hp"] < 0:
            self.mo["hp"] = 0
        
        deadly = " deadly" if is_crit else ""
        return f"{self.mc.name}{deadly} attacks: deals {dmg} dmg."
    
    def cast_magic(self, magic_id):
        self.submenu = None
        self.menu_index = 0
        self.sub_index = 0
        
        if magic_id == 0:
            summon = SUMMONS[self.mc.equip.get("ring") % 300]
            self.mc.mp -= summon["mp_cost"]
            self.buffs += 1
            return f"{self.mc.name} cast {summon["name"]} to power up."
        
        spell = SPELLS[magic_id]
        self.mc.mp -= spell["mp_cost"]
        mdmg = self.mc.get_hero_str() + spell["power"]
        
        if self.mc.equip.get("ring") == 301 and magic_id in (1,2,3,4):
            mdmg += self.mc.get_hero_level() * (1 + self.buffs)
        
        if self.mc.equip.get("ring") == 302 and magic_id in (5,6,7,8):
            mdmg += self.mc.get_hero_level() * (1 + self.buffs)
        
        mo_mdef = self.mo["def"]
        if magic_id in (1,2,3,4):
            mo_mdef = mo_mdef * self.mo["res_ice"] / 100;
        if magic_id in (5,6,7,8):
            mo_mdef = mo_mdef * self.mo["res_fire"] / 100;
        
        mdmg = mdmg - mo_mdef
        if mdmg < 1:
            mdmg = 1
        
        mdmg = MAX_DMG if mdmg > MAX_DMG else round(mdmg)
        self.mo["hp"] -= mdmg
        if self.mo["hp"] < 0:
            self.mo["hp"] = 0
        
        return f"{self.mc.name} cast {spell["name"]}: deals {mdmg} dmg."
    
    def mon_attack(self):
        mo_dmg = self.mo["atk"] - self.mc.get_hero_def()
        
        if self.mc.equip.get("ring") in (303, 305) and self.buffs > 0:
            mo_dmg -= self.mc.get_hero_level() * self.buffs * randomInt() // 99
        
        if mo_dmg < 1:
            mo_dmg = 1
        
        mo_ext_dmg = mo_dmg * randomInt() // 99
        if mo_ext_dmg < 1:
            mo_ext_dmg = 1
        
        mo_dmg += mo_ext_dmg
        if mo_dmg % 2 > 0:
            mo_dmg += 1
        
        is_crit = False
        if randomInt() < self.mo["crit_chance"]:
            is_crit = True
        else:
            mo_dmg //= 2
        
        mo_dmg = MAX_DMG if mo_dmg > MAX_DMG else round(mo_dmg)
        self.mc.hp -= mo_dmg
        if self.mc.hp < 0:
            self.mc.hp = 0
        
        deadly = " deadly" if is_crit else ""
        return f"{self.mo["name"]}{deadly} attacks: deals {mo_dmg} dmg."
    
    def _use_item(self, iid: int):
        self.submenu = None
        self.menu_index = 0
        self.sub_index = 0
        
        p = self.game.player
        return p._use_item(iid)
    
    def available_items(self):
        return [iid for iid in range(1, 6) if self.mc.inventory.get(iid, 0) > 0]
    
    def available_spells(self):
        entries = [sid for sid in self.mc.spells if sid in SPELLS]
        if self.mc.equip.get("ring") and self.mc.equip.get("ring") % 300 in SUMMONS:
            entries.append(0) # 0 means summon special row
        return entries
    
    def submenu_len(self):
        if self.submenu == "cast":
            return len(self.available_spells())
        if self.submenu == "item":
            return len(self.available_items())
        return 0
    
    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        
        if self.state != "player":
            return
        
        # get screen
        screen = pygame.display.get_surface()
        
        if self.submenu is None:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.menu_index = (self.menu_index-1) % 4
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.menu_index = (self.menu_index+1) % 4
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.menu_index = (self.menu_index-2) % 4
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.menu_index = (self.menu_index+2) % 4
            
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                choice = self.menu_items[self.menu_index]
                
                if choice == "Attack":
                    self.state = "action"
                    self.messages.append((self.hero_attack(), BLUE))
                    self.render(screen)
                    pygame.display.flip()
                    is_win = self.check_win()
                    if not is_win:
                        self.state = "monster"
                
                if choice == "Item":
                    if len(self.available_items()) == 0:
                        self.game.toast("No items can be used.")
                        return
                    
                    self.submenu = "item"
                    self.sub_index = 0
                
                if choice == "Cast":
                    if len(self.available_spells()) == 0:
                        self.game.toast("No spells can be cast.")
                        return
                    
                    self.submenu = "cast"
                    self.sub_index = 0
                
                if choice == "Flee":
                    self.state = "action"
                    self.mc.power = 0
                    self.score_penalty()
                    self.result.append(None)
                    self.state = "end_"
                    self.game.change_state(self.game.states["map"])
        else:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.submenu = None
                self.sub_index = 0
            
            if event.key in (pygame.K_UP, pygame.K_w):
                self.sub_index = (self.sub_index-1) % self.submenu_len()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.sub_index = (self.sub_index+1) % self.submenu_len()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.submenu == "cast":
                    entries = self.available_spells()
                    if self.sub_index < len(entries):
                        sid = entries[self.sub_index]
                        if sid == 0:
                            summon = SUMMONS[self.mc.equip.get("ring") % 300]
                            if self.mc.mp < summon["mp_cost"]:
                                self.game.toast("Not enough MP.")
                                self.game_delay()
                                return
                            self.state = "action"
                            self.messages.append((self.cast_magic(sid), BLUE))
                            self.render(screen)
                            pygame.display.flip()
                            
                            self.state = "monster"
                        else:
                            magic = SPELLS[sid]
                            if self.mc.mp < magic["mp_cost"]:
                                self.game.toast("Not enough MP.")
                                self.game_delay()
                                return
                            self.state = "action"
                            self.messages.append((self.cast_magic(sid), BLUE))
                            self.render(screen)
                            pygame.display.flip()
                            is_win = self.check_win()
                            if not is_win:
                                self.state = "monster"
                if self.submenu == "item":
                    entries = self.available_items()
                    if entries:
                        self.state = "action"
                        iid = entries[self.sub_index]
                        self.messages.append((self._use_item(iid), BLUE))
                        self.render(screen)
                        pygame.display.flip()
                        self.state = "monster"
    
    def update(self, delta_time: float):
        if self.state == "end":
            self.wait_end += delta_time
            if self.wait_end >= 3:
                self.state = "end_"
                self.game.change_state(self.game.states["map"])
        
        if self.state == "monster":
            self.state = "action"
            self.messages.append((self.mon_attack(), RED))
            screen = pygame.display.get_surface()
            self.render(screen)
            pygame.display.flip()
            is_lose = self.check_lose()
            if not is_lose:
                self.messages.append((self.ready, BLUE))
                self.state = "player"
    
    def check_win(self):
        if self.mo["hp"] < 1:
            self.mc.power = 0
            self.result.append(True)
            self.state = "end"
            return True
        return False
    
    def check_lose(self):
        if self.mc.hp < 1:
            self.mc.power = 0
            self.score_penalty()
            self.result.append(False)
            self.state = "end"
            return True
        return False
    
    def score_penalty(self):
        self.mc.score -= 200
        if self.mc.score < 0:
            self.mc.score = 0
    
    def render(self, screen: pygame.Surface):
        screen.fill(BLACK)
        
        self.percent_bar(screen, 12, 12, WIDTH - 12 * 3 - SHEET_SIZE_SCALED, 20, self.mo["hp"], self.mo["max_hp"])
        en_text = self.game._get_font(16).render(f'HP {self.mo["hp"]:03}/{self.mo["max_hp"]:03}', True, WHITE)
        screen.blit(en_text, (WIDTH - 12 * 10.25 - SHEET_SIZE_SCALED, 40))
        
        mon_sprite = self.game.sprites[self.mon_id - 1]
        screen.blit(mon_sprite, (WIDTH - SHEET_SIZE * SCALE - 12, 12))
        
        self.percent_bar(screen, SHEET_SIZE_SCALED + 24, 104, WIDTH - 12 * 3 - SHEET_SIZE_SCALED, 20, self.mc.hp, self.mc.get_hero_max_hp())
        hero_txt = f"HP {self.mc.hp:04}/{self.mc.get_hero_max_hp():04} • MP {self.mc.mp:04}/{self.mc.get_hero_max_mp():04}"
        hero_txt = self.game._get_font(16).render(hero_txt, True, WHITE)
        screen.blit(hero_txt, (SHEET_SIZE_SCALED + 24, 72))
        
        hero = self.game.sprites[15]
        screen.blit(hero, (12, 60))
        
        ym = 140
        for msg, color in self.messages[-10:]:
            status = self.game._get_font(16).render(msg, True, color)
            screen.blit(status, (20, ym))
            ym += 20
        
        if self.state == "player":
            if self.submenu is None:
                
                menu_x = 220
                menu_y = HEIGHT-120
                options = [(self.menu_items[0], 0, 0), (self.menu_items[1], 150, 0), (self.menu_items[2], 0, 40), (self.menu_items[3], 150, 40)]
                
                for label, dx, dy in options:
                    text = self.game._get_font(16).render(label, True, WHITE)
                    screen.blit(text, (menu_x + dx, menu_y + dy))
                
                ptr_pos = {
                    0:(menu_x-20,  menu_y +6),
                    1:(menu_x+130, menu_y +6),
                    2:(menu_x-20,  menu_y+46),
                    3:(menu_x+130, menu_y+46)
                }[self.menu_index]
                
                pygame.draw.polygon(screen, BLUE, [(ptr_pos[0], ptr_pos[1]), (ptr_pos[0]+8, ptr_pos[1]+6), (ptr_pos[0], ptr_pos[1]+12)])
            
            if self.submenu == "cast":
                rect = pygame.Rect(200, 200, 240, 200)
                pygame.draw.rect(screen, BLACK, rect)
                entries = self.available_spells()
                for i, e in enumerate(entries):
                    if e == 0:
                        summon = SUMMONS[self.mc.equip.get("ring") % 300]
                        label = f"{summon['name']:<14} (MP{summon['mp_cost']:02})"
                    else:
                        spell = SPELLS[e]
                        label = f"{spell["name"]:<14} (MP{spell['mp_cost']:02})"
                    text = self.game._get_font(14).render(label, True, WHITE)
                    screen.blit(text, (rect.x + 18, rect.y + 5 + i * 28))
                
                cx = rect.x + 2
                cy = rect.y + 8 + self.sub_index*28
                pygame.draw.polygon(screen, BLUE, [(cx,cy), (cx + 8, cy + 6), (cx, cy + 12)])
            
            if self.submenu == "item":
                rect = pygame.Rect(200, 200, 240, 200)
                pygame.draw.rect(screen, BLACK, rect)
                entries = self.available_items()
                for i, e in enumerate(entries):
                    item = ITEMS.get(e)["name"]
                    qty = self.mc.inventory.get(e, 0)
                    
                    text = self.game._get_font(14).render(f"{item:<14}  x{qty:02}", True, WHITE)
                    screen.blit(text, (rect.x + 18, rect.y + 5 + i * 28))
                
                cx = rect.x + 2
                cy = rect.y + 8 + self.sub_index*28
                pygame.draw.polygon(screen, BLUE, [(cx,cy), (cx + 8, cy + 6), (cx, cy + 12)])
    
    def clamp(self, v, a, b):
        return a if v<a else (b if v>b else v)
    
    def percent_bar(self, surface, x, y, w, h, value, maxv, back_color=RED, fill_color=GREEN):
        pygame.draw.rect(surface, back_color, pygame.Rect(x,y,w,h))
        if maxv <= 0:
            return
        fill_w = int(w * self.clamp(value, 0, maxv) / maxv)
        if fill_w > 0:
            pygame.draw.rect(surface, fill_color, pygame.Rect(x,y,fill_w,h))
