#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List

import json
import pygame
from .game_constants import GAME_TITLE, WIDTH, HEIGHT
from .game_class import IState

class MenuState(IState):
    def __init__(self, game: "Game", return_to: Optional[IState] = None):
        self.game = game
        self.return_to = return_to
        self.items: List[str] = []
        self.index = 0
        self.bg = (20, 22, 28)
        self.panel = pygame.Surface((WIDTH - 40, HEIGHT - 50), pygame.SRCALPHA)
        self.panel.fill((0, 0, 0, 160))
        self.title_logo: Optional[pygame.Surface] = None
    
    def get_prev_state(self):
        return self.return_to.__class__.__name__
    
    def enter(self):
        self.prev_state = self.get_prev_state()
        self.items = []
        
        if self.prev_state in ("MapState",):
            self.items.append("Resume Game")
        
        self.items.append("New Game")
        self.items.append("Load Game")
        
        if self.prev_state in ("MapState",):
            if self.game.player.map_name != "MapD4":
                self.items.append("Save Game")
        
        self.items.append("Help")
        self.items.append("Close Game")
        
        self.index = 0
    
    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        
        if event.key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(self.items)
        if event.key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(self.items)
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.activate(self.items[self.index])
        if self.prev_state in ("MapState",) and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.game.change_state(self.return_to)
    
    def activate(self, item: str):
        if item == "Resume Game" and self.get_prev_state() != "NoneType":
            self.game.change_state(self.return_to)
        if item == "New Game":
            self.game.player.create()
            self.game.map_flags = {}
            self.game.load_map_flag = True
            self.game.change_state(self.game.states["map"])
        if item == "Load Game":
            try:
                with open(self.game.save_path, "r", encoding="utf-8") as f:
                    save_data = json.load(f)
            except Exception as e:
                self.game.toast("No save file found!")
                return
            
            self.game.player.create()
            self.game.player.name = save_data.get("name", self.game.player.name)
            
            self.game.player.map_name = save_data.get("map", self.game.player.map_name)
            self.game.player.x        = int(save_data.get("x", self.game.player.x))
            self.game.player.y        = int(save_data.get("y", self.game.player.y))
            self.game.player.facing   = int(save_data.get("z", self.game.player.facing))
            
            self.game.player.hp   = int(save_data.get("hp", self.game.player.hp))
            self.game.player.mp   = int(save_data.get("mp", self.game.player.mp))
            self.game.player.exp  = int(save_data.get("exp", self.game.player.exp))
            
            self.game.player.gold  = int(save_data.get("gold", self.game.player.gold))
            self.game.player.power = int(save_data.get("power", self.game.player.power))
            
            self.game.player.mult_hp  = int(save_data.get("mult_hp", self.game.player.mult_hp))
            self.game.player.mult_mp  = int(save_data.get("mult_mp", self.game.player.mult_mp))
            self.game.player.mult_str = int(save_data.get("mult_str", self.game.player.mult_str))
            
            self.game.player.inventory = dict(sorted({int(k): int(v) for k, v in save_data.get("inventory", self.game.player.inventory).items()}.items()))
            self.game.player.equip     = {str(k): int(v) for k, v in save_data.get("equip", self.game.player.equip).items()}
            self.game.player.spells    = sorted([int(s) for s in save_data.get("spells", self.game.player.spells)])
            
            self.game.player.score      = int(save_data.get("score", self.game.player.score))
            self.game.player.bonus_code = int(save_data.get("bonus_code", self.game.player.bonus_code))
            self.game.map_flags         = dict(sorted(save_data.get("map_flags", {}).items()))
            
            self.game.toast("Game loaded.")
            self.game.load_map_flag = True
            self.game.change_state(self.game.states["map"])
        if item == "Save Game":
            save_data = {
                "name": self.game.player.name,
                
                "map": self.game.player.map_name,
                "x":   self.game.player.x,
                "y":   self.game.player.y,
                "z":   self.game.player.facing,
                
                "hp":  self.game.player.hp,
                "mp":  self.game.player.mp,
                "exp": self.game.player.exp,
                
                "gold":  self.game.player.gold,
                "power": self.game.player.power,
                
                "mult_hp":  self.game.player.mult_hp,
                "mult_mp":  self.game.player.mult_mp,
                "mult_str": self.game.player.mult_str,
                
                "inventory": dict(sorted(self.game.player.inventory.items())),
                "equip":     self.game.player.equip,
                "spells":    sorted(self.game.player.spells),
                
                "score":       self.game.player.score,
                "bonus_code":  self.game.player.bonus_code,
                "map_flags":   dict(sorted(self.game.map_flags.items())),
            }
            try:
                with open(self.game.save_path, "w", encoding="utf-8") as f:
                    json.dump(save_data, f, indent=4)
                    self.game.toast("Game saved.")
                    self.game.change_state(self.return_to)
            except Exception as e:
                self.game.toast(f"Save failed: {e}")
        if item == "Help":
            self.game.change_state(self.game.states["help"])
        if item == "Close Game":
            self.game.running = False
    
    def update(self, delta_time: float):
        pass
    
    def render(self, screen: pygame.Surface):
        screen.fill(self.bg)
        screen.blit(self.panel, (20, 30))
        y = 50
        
        TITLE = GAME_TITLE if self.get_prev_state() == 'NoneType' else 'PAUSE'
        self.game.draw_text_center(TITLE, WIDTH//2, y, size=28)
        y += 40
        
        for i, item in enumerate(self.items):
            sel = (i == self.index)
            color = (255, 240, 200) if sel else (210, 210, 220)
            marker = "•" if sel else ""
            self.game.draw_text_center(f"{marker} {item} {marker}", WIDTH//2, y + 28*i, size=22, color=color)
        self.game.draw_text_center("↑/↓/w/s — Navigate • Enter/Space — Select", WIDTH//2, HEIGHT - 12, size=14, color=(170,170,180))
