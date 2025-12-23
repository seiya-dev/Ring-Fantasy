#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import sys
import json
import copy
import pygame

from .game_class import IState, Player
from .game_constants import FPS, WIDTH, HEIGHT, TILE_SIZE, SCALE, ITEMS, SPELLS, ENEMIES, MAX_ITEMS_COUNT
from .game_bonus import code_select
TILE_SIZE_SCALED = TILE_SIZE * SCALE

ranges = [
    range(34, 38), # gold
    range(38, 43), # items #6-10
    range(43, 47), # rings #1-4
    range(47, 55), # swords and armors
    range(55, 57), # items #1-2
    range(96, 97), # ring #305
    # range(80, 81), # queen
    # range(95, 96), # princess
]

def in_ranges(n: int) -> bool:
    return any(n in r for r in ranges)

class GameMap:
    def __init__(self, game: "Game"):
        self.game = game
        self.maps = dict(game.maps)
    
    def load_map(self):
        self.name = self.game.player.map_name
        self.w, self.h, self.grid = copy.deepcopy(self.maps[self.name])
    
    def cell_components(self, x, y):
        map_values = self.grid[x][y]
        if f'{self.name},{x:02},{y:02}' in self.game.map_flags:
            map_values = tuple(map(int, self.game.map_flags[f'{self.name},{x:02},{y:02}'].split(":")))
        return map_values
    
    def set_override(self, x, y, tile_idx, obj_idx, ev_id):
        self.game.map_flags[f'{self.name},{x:02},{y:02}'] = f"{tile_idx:02}:{obj_idx:02}:{ev_id:03}"
    
    def set_event_id(self, x, y, ev_id):
        tile_idx, obj_idx, _ = self.grid[x][y]
        self.game.map_flags[f'{self.name},{x:02},{y:02}'] = f"{tile_idx:02}:{obj_idx:02}:{ev_id:03}"
    
    def set_event_id_temp(self, x, y, ev_id):
        tile_idx, obj_idx, _ = self.grid[x][y]
        self.grid[x][y] = tile_idx, obj_idx, ev_id
    
    def is_walkable(self, x, y):
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return False
        
        tile_idx, obj_idx, ev_id = self.cell_components(x, y)
        ev_type = self.game.events.get(ev_id)[0] if ev_id > 0 else None
        
        if self.game.player.has_item(12) > 0:
            return True
        
        if ev_type in ('change_map', 'unwalkable', 'door'):
            return False
        
        if ev_type in ('walkable', 'walkable_button', 'walkable_dialogue_box'):
            return True
        
        if obj_idx == 0:
            return tile_idx <= 18
        else:
            return (obj_idx <= 1) or (obj_idx == 44)
    
    def draw(self, surface, cam_x, cam_y):
        cols_visible = WIDTH // TILE_SIZE_SCALED + 2
        rows_visible = HEIGHT // TILE_SIZE_SCALED + 2
        
        start_x = max(0, cam_x // TILE_SIZE_SCALED)
        start_y = max(0, cam_y // TILE_SIZE_SCALED)
        
        end_x = min(self.w, start_x + cols_visible)
        end_y = min(self.h, start_y + rows_visible)
        
        for gx in range(start_x, end_x):
            for gy in range(start_y, end_y):
                sx = gx * TILE_SIZE_SCALED - cam_x
                sy = gy * TILE_SIZE_SCALED - cam_y
                
                tile_idx, obj_idx, ev_id = self.cell_components(gx, gy)
                
                if 0 <= tile_idx < len(self.game.tiles) and self.game.tiles[tile_idx]:
                    scaled_tile = self.game.tiles[tile_idx]
                    surface.blit(scaled_tile, (sx, sy))
                
                if obj_idx and 0 < obj_idx <= len(self.game.objects):
                    scaled_obj = self.game.objects[obj_idx-1]
                    surface.blit(scaled_obj, (sx, sy))
                
                if self.game.player.has_item(11) > 0 and ev_id > 0 and in_ranges(ev_id):
                    surface.fill((255, 0, 0), (sx, sy, 4 * SCALE, 4 * SCALE))

class MapState(IState):
    def __init__(self, game: "Game"):
        self.game = game
        self.game.cur_map = GameMap(self.game)
        
        self.cam_x = 0
        self.cam_y = 0
    
    def enter(self):
        self.repeat_delay = FPS/1000 * 3
        self.move_cooldown = 0
        self.active_event = False
        self.gossip_id = 0
        
        if self.game.load_map_flag:
            self.game.cur_map.load_map()
            self.game.load_map_flag = False
        
        if self.game.states["battle"].mon_id > 0:
            self.active_event = True
            
            mon_id = self.game.states["battle"].mon_id
            mon = ENEMIES.get(mon_id)
            
            x, y, won_flag = self.game.states["battle"].result
            self.game.states["battle"].mon_id = -1
            self.game.states["battle"].result = None
            
            if won_flag:
                tile_idx, obj_idx, ev_id = self.game.cur_map.cell_components(x, y)
                etype, data = self.game.events.get(ev_id)
                
                if etype in("battle",):
                    self.game.player.add_exp(mon["exp"])
                    self.game.player.add_gold(mon["gold"])
                    prize_text = self.game.events.get(132)[1]
                    if mon_id == 14:
                        self.game.player.mult_str += 2
                        prize_text = self.game.events.get(133)[1]
                
                    self.dialogue(prize_text.format(name=mon["name"], exp=mon["exp"], gold=mon["gold"]))
                    
                    if obj_idx in (11, 41): # tile enemies
                        self.game.cur_map.set_override(x, y, tile_idx, 0, 0)
                    else:
                        self.game.cur_map.set_event_id_temp(x, y, 0)
                
                if etype in("boss",):
                    king_talk_data = self.game.events.get(138)[1].split('@')
                    king_name = king_talk_data[0]
                    king_talk = self.game.assets.load_text(king_talk_data[1])
                    self.dialogue(king_talk, title = king_name)
                    
                    self.game.cur_map.set_override(6, 3, 8, 0, 0)
                    self.game.cur_map.set_override(6, 4, 8, 44, 139)
            
            self.game_delay()
            self.active_event = False
    
    def snap_camera_to_player(self):
        player_px = self.game.player.x * TILE_SIZE_SCALED
        player_py = self.game.player.y * TILE_SIZE_SCALED
        
        target_cx = player_px - WIDTH  // 2 + TILE_SIZE_SCALED // 2
        target_cy = player_py - HEIGHT // 2 + TILE_SIZE_SCALED // 2
        
        map_w_px = self.game.cur_map.w * TILE_SIZE_SCALED
        map_h_px = self.game.cur_map.h * TILE_SIZE_SCALED
        
        if map_w_px <= WIDTH:
            self.cam_x = - (WIDTH - map_w_px) // 2
        else:
            self.cam_x = self.clamp(target_cx, 0, map_w_px - WIDTH)
        
        if map_h_px <= HEIGHT:
            self.cam_y = - (HEIGHT - map_h_px) // 2
        else:
            self.cam_y = self.clamp(target_cy, 0, map_h_px - HEIGHT)
    
    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        
        if event.key == pygame.K_i:
            self.game.change_state(self.game.states["inventory"])
            return
        
        if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
            self.game.states["menu"].return_to = self
            self.game.change_state(self.game.states["menu"])
            return
        
        if event.key == pygame.K_c:
            char_stats = (
                f" Level: {self.game.player.get_hero_level()} \n"
                f" Next Level Exp: {self.game.player.next_level_exp()} \n"
                f" HP: {self.game.player.hp}/{self.game.player.get_hero_max_hp()} \n"
                f" MP: {self.game.player.mp}/{self.game.player.get_hero_max_mp()} \n"
                f" STR: {self.game.player.get_hero_str()} \n"
                f" ATK: {self.game.player.get_hero_atk()} \n"
                f" DEF: {self.game.player.get_hero_def()} \n"
                f" Gold: {self.game.player.gold} \n"
                f" Keys: {self.game.player.has_item(10)} \n"
            )
            
            if self.game.player.equip["sword"] > 0:
                char_stats += f" Equipped Sword: {ITEMS[self.game.player.equip["sword"]]["name"]} \n"
            
            if self.game.player.equip["armor"] > 0:
                char_stats += f" Equipped Armor: {ITEMS[self.game.player.equip["armor"]]["name"]} \n"
            
            if self.game.player.equip["ring"] > 0:
                char_stats += f" Equipped Ring:  {ITEMS[self.game.player.equip["ring"]]["name"]} \n"
            
            if len(self.game.player.spells) > 0:
                char_stats += f" Spells: \n"
                spells_fire = ""
                spells_ice = ""
                
                for spell_id in self.game.player.spells:
                    if SPELLS[spell_id]["type"] == "fire":
                        spells_fire += f" * {SPELLS[spell_id]["name"]:<10}"
                    if SPELLS[spell_id]["type"] == "ice":
                        spells_ice  += f" * {SPELLS[spell_id]["name"]:<10}"
                
                if len(spells_ice) > 0:
                    char_stats += f" {spells_ice}\n"
                
                if len(spells_fire) > 0:
                    char_stats += f" {spells_fire}\n"
            
            char_stats += f"\n Score: {self.game.player.score} \n"
            if self.game.player.bonus_code != 0:
                char_stats += f" Bonus Code: {self.game.player.bonus_code}"
            
            c_selected = self.dialogue(char_stats, title = self.game.player.name, buttons = ())
            return
    
    def update(self, delta_time: float):
        self.move_cooldown -= delta_time
        keys = pygame.key.get_pressed()
        
        if self.active_event:
            return
        
        moved = False
        turned = True
        
        move_U = keys[pygame.K_UP]    or keys[pygame.K_w]
        move_L = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        move_R = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        move_D = keys[pygame.K_DOWN]  or keys[pygame.K_s]
        
        if self.move_cooldown <= 0:
            if move_U and self.game.player.facing != 0:
                self.game.player.facing = 0
                turned = False
            if move_L and self.game.player.facing != 1:
                self.game.player.facing = 1
                turned = False
            if move_R and self.game.player.facing != 2:
                self.game.player.facing = 2
                turned = False
            if move_D and self.game.player.facing != 3:
                self.game.player.facing = 3
                turned = False
            
            if not turned:
                self.move_cooldown = self.repeat_delay
                return
            
            dx = dy = 0
            if move_U:
                dy = -1
            if move_L:
                dx = -1
            if move_R:
                dx = 1
            if move_D:
                dy = 1
            
            if dx != 0 or dy != 0:
                try_walk = self.game.player.x + dx, self.game.player.y + dy
                is_walkable = self.game.cur_map.is_walkable(try_walk[0], try_walk[1])
                
                if is_walkable:
                    self.game.player.move(try_walk[0], try_walk[1])
                    self.move_cooldown = self.repeat_delay
                
                self.active_event = True
                self.trigger_event(try_walk[0], try_walk[1])
                self.active_event = False
    
    def game_delay(self):
        pygame.time.delay(int(self.repeat_delay * 1000))
    
    def trigger_event(self, x, y):
        if x < 0 or y < 0:
            return
        if x >= self.game.cur_map.w or y >= self.game.cur_map.h:
            return
        
        tile_idx, obj_idx, ev_id = self.game.cur_map.cell_components(x, y)
        
        if ev_id == 0:
            return
        
        ev = self.game.events.get(ev_id)
        if not ev:
            return
        
        etype, data = ev
        
        if etype in ("walkable",):
            return
        
        if etype in ("walkable_button",):
            data = data.split("@")
            map_pos_x, map_pos_y = list(map(int, data[0].split(",")))
            map_new_data = [int(p.strip()) for p in data[1].split(":")]
            
            self.game.cur_map.set_override(x + map_pos_x, y + map_pos_y, map_new_data[0], map_new_data[1], map_new_data[2])
            self.game.cur_map.set_event_id(x, y, 97)
            
            return
        
        if etype in ("walkable_dialogue_box",):
            self.dialogue(data)
            self.game.cur_map.set_event_id(x, y, 97)
            
            self.game_delay()
            return
        
        if etype in ("change_map",):
            parts = [p.strip() for p in data.split(",")]
            map_name, sx, sy, dir_code = parts[0], int(parts[1]), int(parts[2]), int(parts[3])
            
            self.game.player.map_name = map_name
            self.game.player.x = sx
            self.game.player.y = sy
            self.game.player.facing = dir_code
            self.game.cur_map.load_map()
            
            self.game_delay()
            return
        
        if etype in ("door",):
            if self.game.player.has_item(10) > 0:
                ask_open_door = self.game.events.get(111)[1]
                do_open_door = self.dialogue(ask_open_door, buttons=("Yes", "No"))
                if do_open_door == "Yes":
                    self.game.cur_map.set_event_id(x, y, 0)
                    self.game.player.consume_item(10)
            else:
                no_keys_text = self.game.events.get(110)[1]
                self.dialogue(no_keys_text)
            
            self.game_delay()
            return
        
        if etype in ("sign", "dialogue_box", "one_time_dialogue_box",):
            self.dialogue(data)
            
            if etype in ("one_time_dialogue_box",):
                self.game.cur_map.set_event_id(x, y, 0)
            
            self.game_delay()
            return
        
        if etype in ("battle","boss"):
            mon_id = int(data)
            mon = ENEMIES.get(mon_id)
            
            if mon == None:
                return
            
            if self.game.player.hp == 0:
                self.game.toast("I need to rest...")
                return
            
            battle_text = self.game.events.get(131)[1]
            do_battle = self.dialogue(battle_text.format(name=mon["name"], hp=mon["hp"]), buttons=("Yes", "No"))
            
            if do_battle == "Yes":
                if etype == "boss":
                    king_talk_data = self.game.events.get(137)[1].split('@')
                    king_name = king_talk_data[0]
                    king_talk = self.game.assets.load_text(king_talk_data[1])
                    self.dialogue(king_talk, title = king_name)
                
                self.game.states["battle"].mon_id = mon_id
                self.game.states["battle"].result = [x, y]
                
                self.game.change_state(self.game.states["battle"])
                return
            
            self.game_delay()
            return
        
        if etype in ("tavern",):
            ask_gossips_text = self.game.events.get(114)[1]
            ask_gossips = self.dialogue(ask_gossips_text, buttons=("Yes", "No"))
            
            if ask_gossips == "Yes":
                self.gossip_id = 0 if self.gossip_id > 7 else self.gossip_id
                gossips_text = self.game.events.get(120 + self.gossip_id)[1]
                self.dialogue(gossips_text)
                self.gossip_id += 1
            
            self.game_delay()
            return
        
        if etype in ("queen",):
            sad_queen = self.game.events.get(112)[1]
            do_talk = self.dialogue(sad_queen, buttons=("Yes", "No"))
            
            if do_talk == "Yes":
                queen_talk_data = self.game.events.get(134)[1].split('@')
                queen_name = queen_talk_data[0]
                queen_talk = self.game.assets.load_text(queen_talk_data[1])
                self.dialogue(queen_talk, title = queen_name)
                
                accept_quest_text = self.game.events.get(115)[1]
                accept_quest = self.dialogue(accept_quest_text, buttons=("Yes", "No"))
                if accept_quest == "Yes":
                    self.game.player.add_item(10)
                    self.game.cur_map.set_event_id(x, y, 81)
                    self.trigger_event(x, y)
                    return
            
            self.game_delay()
            return
        
        if etype in ("princess",):
            ask_release_text = self.game.events.get(113)[1]
            ask_release = self.dialogue(ask_release_text, buttons=("Yes", "No"))
            
            if ask_release == "Yes":
                princess_talk_data = self.game.events.get(135)[1].split('@')
                princess_name = princess_talk_data[0]
                princess_talk = self.game.assets.load_text(princess_talk_data[1])
                self.dialogue(princess_talk, title = princess_name)
                self.game.cur_map.set_override(x, y, 22, 0, 96)
            
            self.game_delay()
            return
        
        if etype in ("shop",):
            shop_ask = self.game.events.get(109)[1]
            do_shop = self.dialogue(shop_ask, buttons=("Yes", "No"))
            
            if do_shop == "Yes":
                self.game.change_state(self.game.states["shop"])
                return
            
            self.game_delay()
            return
        
        if etype in ("gold",):
            self.game.player.add_gold(int(data))
            
            gold_text = self.game.events.get(128)[1].format(gold=int(data))
            self.dialogue(gold_text)
            self.game.cur_map.set_event_id(x, y, 0)
            
            self.game_delay()
            return
        
        if etype in ("item",):
            item_id = int(data)
            item = ITEMS.get(item_id)
            
            if item == None:
                return
            
            if self.game.player.has_item(item_id) >= MAX_ITEMS_COUNT:
                full_bag_text = self.game.events.get(129)[1]
                self.dialogue(full_bag_text.format(name=item["name"]))
            else:
                found_item_text = self.game.events.get(130)[1]
                
                if tile_idx == 22 and obj_idx == 0: # itembox
                    self.game.cur_map.set_override(x, y, tile_idx+1, 0, 0)
                else:
                    self.game.cur_map.set_event_id(x, y, 0)
                
                item_description = ""
                if item["type"] == "special" and item_id != 10:
                    if item_id == 6:
                        self.game.player.mult_str += 1
                    if item_id == 7:
                        self.game.player.mult_str += 2
                    if item_id == 8:
                        self.game.player.mult_hp += 1
                    if item_id == 9:
                        self.game.player.mult_mp += 1
                    item_description = item["description"]
                else:
                     self.game.player.add_item(item_id)
                
                self.dialogue(found_item_text.format(name=item["name"], description=item_description))
            
            self.game_delay()
            return
        
        if etype in ("inn",):
            rest_ask = self.game.events.get(108)[1]
            do_rest = self.dialogue(rest_ask, buttons=("Yes", "No"))
            
            if do_rest == "Yes" and self.game.player.gold >= 100:
                self.game.player.gold -= 100
                self.game.player.hp = self.game.player.get_hero_max_hp()
                self.game.player.mp = self.game.player.get_hero_max_mp()
                
                new_x, new_y = list(map(int, data.split(",")))
                new_x = self.game.player.x + new_x
                new_y = self.game.player.y + new_y
                
                if self.game.cur_map.is_walkable(new_x, new_y):
                    self.game.player.x = new_x
                    self.game.player.y = new_y
            
            elif do_rest == "Yes":
                rest_gold = self.game.events.get(136)[1]
                self.dialogue(rest_gold)
            
            self.game_delay()
            return
        
        if etype in ("end_screen",):
            self.render_end_screen()
            self.game_delay()
            return
        
        self.game.toast("Not Ready Yet")
        self.game_delay()
        return
    
    def clamp(self, v, lo, hi):
        return max(lo, min(v, hi))
    
    def draw_end_center_text(self, surface):
        lines = [
            "The End",
            "Your Score:",
            str(self.game.player.score),
            "Bonus Code:",
            str(code_select(self.game.player.score)),
        ]
        
        rendered_lines = [self.game._get_font(32).render(line, True, (255,255,255)) for line in lines]
        total_height = sum(r.get_height() for r in rendered_lines) + (len(lines)-1) * 5
    
        start_y = (surface.get_height() - total_height) // 2
        for r in rendered_lines:
            rect = r.get_rect(centerx=surface.get_width()//2, y=start_y)
            surface.blit(r, rect)
            start_y += r.get_height() + 5
    
    def end_draw_hint(self, surface):
        text_surf = self.game._get_font(16).render("Enter/Space - back to main screen", True, (180, 180, 180))
        rect = text_surf.get_rect(midbottom=(surface.get_width()//2, surface.get_height() - 16))
        surface.blit(text_surf, rect)
    
    def render_end_screen(self):
        clock = pygame.time.Clock()
        screen = pygame.display.get_surface()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.game.states["menu"].return_to = None
                        self.game.change_state(self.game.states["menu"])
                        return
            
            screen.fill((0,0,0))
            self.draw_end_center_text(screen)
            self.end_draw_hint(screen)
            pygame.display.flip()
            clock.tick(FPS)
    
    def dialogue(self, text: str, title="", buttons=("OK",)) -> str | bool:
        clock = pygame.time.Clock()
        screen = pygame.display.get_surface()
        
        focused = 0
        single_button = len(buttons) < 2
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if not single_button:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            focused = (focused - 1) % len(buttons)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            focused = (focused + 1) % len(buttons)
                    
                    if single_button and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                        return True
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if single_button:
                            return True
                        else:
                            return buttons[focused]
            
            self.render(screen)
            if not single_button:
                self._draw_dialogue_overlay(screen, text, buttons, focused, title)
            else:
                self._draw_dialogue_overlay(screen, text, (), -1, title)
            pygame.display.flip()
            clock.tick(FPS)
    
    def render(self, screen: pygame.Surface):
        self.snap_camera_to_player()
        
        screen.fill((0,0,0))
        self.game.cur_map.draw(screen, self.cam_x, self.cam_y)
        self.game.player.draw(screen, self.cam_x, self.cam_y)
        
        box_surface = pygame.Surface((WIDTH, 16), pygame.SRCALPHA)
        box_surface.fill((0, 0, 0, 128))
        screen.blit(box_surface, (0, 0))
        
        keys = self.game.player.has_item(10)
        
        hud = (
            f"HP {self.game.player.hp}/{self.game.player.get_hero_max_hp()} | "
            f"MP {self.game.player.mp}/{self.game.player.get_hero_max_mp()} | "
            f"Gold {self.game.player.gold} | Keys {keys}"
        )
        
        hud = self.game._get_font(10).render(hud, True, (255,255,255))
        screen.blit(hud, (5, 0))
    
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int):
        text = text.replace("\\n", "\n")
        
        lines = []
        for paragraph in text.split("\n"):
            tokens = re.findall(r'\S+|\s+', paragraph)
            
            cur = ""
            for t in tokens:
                test = cur + t
                if not cur or font.size(test)[0] <= max_width:
                    cur = test
                else:
                    lines.append(cur)
                    cur = t.lstrip()
            
            if cur:
                lines.append(cur)
            
            if paragraph == "":
                lines.append("")
        
        return lines
    
    def _draw_dialogue_overlay(self, screen: pygame.Surface, text: str, buttons, focused_idx: int, title: str = ""):
        margin, pad = 8, 8
        box_h = HEIGHT // 1 if title else HEIGHT // 4
        box_y = HEIGHT - box_h
        
        # translucent dialogue panel
        box = pygame.Surface((WIDTH - margin*2, box_h - margin*2), pygame.SRCALPHA)
        box.fill((0, 0, 0, 220))
        screen.blit(box, (margin, box_y + margin))
        
        if title:
            title_font = self.game._get_font(18)
            title_surf = title_font.render(title, True, (255, 255, 255))
            title_x = (WIDTH - title_surf.get_width()) // 2
            title_y = box_y + margin + pad
            screen.blit(title_surf, (title_x, title_y))
            text_offset_y = title_surf.get_height() + 12
        else:
            text_offset_y = 0
        
        # wrapped dialogue text
        font = self.game._get_font(14)
        max_w = WIDTH - margin*2 - pad*2
        lines = self._wrap_text(text, font, max_w)
        
        for i, line in enumerate(lines[: (box_h - pad*2 - text_offset_y) // 18]):
            surf = font.render(line, True, (255, 255, 255))
            screen.blit(surf, (margin + pad, box_y + margin + pad + text_offset_y + i*18))
        
        if buttons and len(buttons) > 1:
            # otherwise draw buttons + hint as before
            btn_font = self.game._get_font(14)
            spacing = 20
            sizes = [btn_font.size(lbl) for lbl in buttons]
            total_w = sum(w for (w, h) in sizes) + spacing*(len(buttons)-1)
            start_x = (WIDTH - total_w) // 2
            baseline_y = HEIGHT - 40
            
            for i, lbl in enumerate(buttons):
                w, h = sizes[i]
                surf = btn_font.render(lbl, True, (255, 255, 255))
                pos = (start_x, baseline_y - h)
                screen.blit(surf, pos)
                
                if i == focused_idx:
                    underline_y = baseline_y - 2
                    pygame.draw.line(screen, (0, 128, 255), (start_x, underline_y), (start_x + w, underline_y), 2)
                
                start_x += w + spacing
        
        # hint
        hint_font = self.game._get_font(11)
        hint_text = "←/→/a/d — choose • Enter/Space — confirm" if buttons else "Enter/Backspace/Space/ESC — continue"
        hint_surf = hint_font.render(hint_text, True, (180, 180, 180))
        hint_x = (WIDTH - hint_surf.get_width()) // 2
        hint_y = HEIGHT - 24
        screen.blit(hint_surf, (hint_x, hint_y))
