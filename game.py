#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
from typing import Optional, Dict, List, Tuple

import pygame
from game.game_constants import (
    GAME_TITLE, GAME_FONT, FPS, WIDTH, HEIGHT, GAMEICON, SCALE, SHEET_SIZE, TILE_SIZE,
    GAME_MAPS, EVENTS_DATA, TILESET, OBJECTSET, SPRITESHEET, HEROSET, SAVE_FILE,
)
from game.game_class import IState, Player

from game.gamestate_menu      import MenuState
from game.gamestate_help      import HelpState
from game.gamestate_map       import MapState
from game.gamestate_inventory import InventoryState
from game.gamestate_shop      import ShopState
from game.gamestate_battle    import BattleState

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def app_base_dir(save_path: bool = False) -> str:
    if hasattr(sys, '_MEIPASS') and not save_path:
        return os.path.join(sys._MEIPASS)
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def init_assets() -> str:
    base = app_base_dir()
    assets_dir = os.path.join(base, "assets")
    if os.path.isdir(assets_dir) and any(os.scandir(assets_dir)):
        return assets_dir
    return assets_dir

# ---------------------------------------------------------------------------
# Assets Manager
# ---------------------------------------------------------------------------
class AssetManager:
    def __init__(self, root: str):
        self.root = root
        self.images: Dict[str, pygame.Surface] = {}
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.texts: Dict[str, str] = {}

    def _full(self, rel_path: str) -> str:
        return os.path.join(self.root, rel_path)

    def load_font(self, rel_path: str) -> str:
        return os.path.join(self.root, rel_path)
    
    def load_maps(self, rel_path: str) -> str:
        return load_maps_file(os.path.join(self.root, rel_path))
    
    def load_events(self, rel_path: str):
        return load_events_file(os.path.join(self.root, rel_path))
    
    def load_icon(self, rel_path: str):
        return pygame.image.load(os.path.join(self.root, rel_path))
    
    def load_spritesheet(self, rel_path: str):
        spritesheet_img = self.load_image(os.path.join(self.root, rel_path))
        return load_spritesheet(spritesheet_img)
    
    def load_tileset(self, rel_path: str):
        tileset_img = self.load_image(os.path.join(self.root, rel_path))
        return load_tileset(tileset_img)
    
    def load_objectset(self, rel_path: str):
        objectset_img = self.load_image(os.path.join(self.root, rel_path))
        return load_tileset(objectset_img)
    
    def load_heroset(self, rel_path: str):
        heroset_img = self.load_image(os.path.join(self.root, rel_path))
        return load_tileset(heroset_img)
    
    def load_image(self, rel_path: str) -> Optional[pygame.Surface]:
        key = rel_path.replace('\\', '/').lower()
        if key in self.images:
            return self.images[key]
        try:
            surf = pygame.image.load(self._full(rel_path))
            surf = surf.convert_alpha() if surf.get_alpha() else surf.convert()
            self.images[key] = surf
            return surf
        except Exception as e:
            print(f"[WARN] Image not loaded '{rel_path}': {e}")
            return None

    def load_text(self, rel_path: str, encoding: str = 'utf-8') -> str:
        key = rel_path.replace('\\', '/').lower()
        if key in self.texts:
            return self.texts[key]
        try:
            with open(self._full(rel_path), 'r', encoding=encoding) as f:
                data = f.read()
            self.texts[key] = data
            return data
        except Exception as e:
            print(f"[WARN] text not loaded '{rel_path}': {e}")
            return ""
    
    def save_path(self, rel_path: str) -> str:
        return os.path.join(app_base_dir(True), rel_path)

def load_maps_file(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = [ln.rstrip("\n") for ln in f]
    
    lines = [ln.strip() for ln in raw if ln.strip() and not ln.strip().startswith("#")]
    maps = {}
    
    i = 0
    while i < len(lines):
        map_name = lines[i]
        if not map_name.lower().startswith("map"):
            raise ValueError(f"Expected a map name (e.g., 'MapD1') at line {i+1}, got: {map_name}")
        i += 1
        
        if i >= len(lines) or not lines[i].lower().startswith("size:"):
            raise ValueError(f"Missing 'size: W,H' after {map_name}")
        try:
            _, size_str = lines[i].split(":", 1)
            w_str, h_str = [p.strip() for p in size_str.split(",")]
            w, h = int(w_str), int(h_str)
        except Exception as e:
            raise ValueError(f"Invalid size header in {path}: {lines[i]}") from e
        i += 1
        
        grid = [[0]*h for _ in range(w)]
        for row in range(h):
            if i >= len(lines):
                raise ValueError(f"Unexpected EOF while reading {map_name}, row {row}")
            row_line = lines[i]
            cells = [c.strip() for c in row_line.split(",")]
            for col in range(w):
                try:
                    parts = cells[col].split(":")
                except (ValueError, IndexError):
                    parts = 99, 99, 0
                if len(parts) != 3:
                    parts = 99, 99, 0
                try:
                    tile_id = int(parts[0])
                    obj_id  = int(parts[1])
                    ev_id   = int(parts[2])
                except Exception as e:
                    tile_id, obj_id, ev_id = 99, 99, 0
                grid[col][row] = tile_id, obj_id, ev_id
            i += 1
        
        maps[map_name] = (w, h, grid)
    return maps

def load_events_file(path):
    events = {}
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split("@", 2)
            if len(parts) == 2:
                parts.append("")
            if len(parts) != 3:
                continue
            try:
                ev_id   = int(parts[0])
                ev_type = parts[1]
                ev_data = parts[2]
                events[ev_id] = (ev_type, ev_data)
            except:
                pass
    return events

def load_tileset(sheet, tile_size = TILE_SIZE, scale = SCALE):
    w, h = sheet.get_size()
    cols = w // tile_size
    rows = h // tile_size
    
    tiles = []
    for j in range(rows):
        for k in range(cols):
            rect = pygame.Rect(k * tile_size, j * tile_size, tile_size, tile_size)
            tile = sheet.subsurface(rect).copy()
            tile = pygame.transform.scale_by(tile, scale)
            tiles.append(tile)
    return tiles

def load_spritesheet(sheet, sheet_size = SHEET_SIZE, scale = SCALE):
    w, h = sheet.get_size()
    cols = w // SHEET_SIZE
    rows = h // SHEET_SIZE
    
    sprites = []
    for j in range(rows):
        for k in range(cols):
            rect = pygame.Rect(k * SHEET_SIZE, j * SHEET_SIZE, SHEET_SIZE, SHEET_SIZE)
            sprite = sheet.subsurface(rect).copy()
            sprite = pygame.transform.scale_by(sprite, scale)
            sprites.append(sprite)
    return sprites

# ---------------------------------------------------------------------------
# Game Main Class
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        
        pygame.display.set_caption(GAME_TITLE)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        assets_dir = init_assets()
        self.assets = AssetManager(assets_dir)
        
        icon = self.assets.load_icon(GAMEICON)
        pygame.display.set_icon(icon)
        
        self.save_path = self.assets.save_path(SAVE_FILE)
        self.maps = self.assets.load_maps(GAME_MAPS)
        self.events = self.assets.load_events(EVENTS_DATA)
        self.sprites = self.assets.load_spritesheet(SPRITESHEET)
        self.tiles = self.assets.load_tileset(TILESET)
        self.objects = self.assets.load_objectset(OBJECTSET)
        self.heroset = self.assets.load_heroset(HEROSET)
        self.map_flags = {}
        
        self.player = Player(self)
        self.player.create()
        
        self.states: Dict[str, IState] = {}
        self.register_states()
        
        self.state: IState = self.states["menu"]
        self.state.enter()
        
        self.load_map_flag = True
        self._toast: Optional[Tuple[str, float]] = None
        self._font_cache: Dict[int, pygame.font.Font] = {}
    
    def register_states(self):
        menu_state = MenuState(self)
        help_state = HelpState(self, return_to = menu_state)
        map_state  = MapState(self)
        
        inventory_state = InventoryState(self, return_to = map_state)
        shop_state      = ShopState(self, return_to = map_state)
        battle_state    = BattleState(self, return_to = map_state)
        
        self.states = {
            "menu":      menu_state,
            "help":      help_state,
            "map":       map_state,
            "inventory": inventory_state,
            "shop":      shop_state,
            "battle":    battle_state,
        }
    
    def _get_font(self, size: int) -> pygame.font.Font:
        if size not in self._font_cache:
            font_path = self.assets.load_font(GAME_FONT)
            self._font_cache[size] = pygame.font.Font(font_path, size)
        return self._font_cache[size]
    
    def draw_text_center(self, text: str, x: int, y: int, *, size: int = 20, color=(220, 220, 220)):
        font = self._get_font(size)
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(x, y))
        self.screen.blit(surf, rect)
    
    def toast(self, text: str, duration: float = 2):
        self._toast = (text, time.time() + duration)
    
    def change_state(self, new_state: IState):
        if self.state:
            self.state.exit()
        self.state = new_state
        self.state.enter()
    
    def run(self):
        while self.running:
            delta_time = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.state.handle_event(event)
            
            self.state.update(delta_time)
            self.state.render(self.screen)
            
            if self._toast is not None:
                msg, until = self._toast
                if time.time() < until:
                    font = self._get_font(18)
                    surf = font.render(msg, True, (255, 250, 210))
                    rect = surf.get_rect(center=(WIDTH//2, HEIGHT - 40))
                    pad = 8
                    bg = pygame.Surface((rect.width + pad*2, rect.height + pad*2), pygame.SRCALPHA)
                    bg.fill((0,0,0,160))
                    bg_rect = bg.get_rect(center=rect.center)
                    self.screen.blit(bg, bg_rect)
                    self.screen.blit(surf, rect)
                else:
                    self._toast = None
            
            pygame.display.flip()
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
