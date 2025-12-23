#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List

import pygame
from .game_constants import WIDTH, HEIGHT, HELP_TEXT
from .game_class import IState

class HelpState(IState):
    def __init__(self, game: "Game", return_to: Optional[IState] = None):
        self.game = game
        self.return_to = return_to
        self.lines: List[str] = []
        self.scroll = 0
        self.margin = 16
        self.line_height = 20
    
    def enter(self):
        text = ""
        if self.game.assets:
            text = self.game.assets.load_text(HELP_TEXT)
        if not text:
            text = "Help not found."
        
        self.lines = self.wrap_text(text, WIDTH - self.margin*2, size=18)
        self.scroll = 0
    
    def wrap_text(self, text: str, max_width: int, *, size: int) -> List[str]:
        font = self.game._get_font(size)
        wrapped: List[str] = []
        for paragraph in text.splitlines():
            if paragraph.strip() == "":
                wrapped.append("")
                continue
            words = paragraph.split(" ")
            line = ""
            for w in words:
                test = w if line == "" else line + " " + w
                if font.size(test)[0] <= max_width:
                    line = test
                else:
                    wrapped.append(line)
                    line = w
            if line:
                wrapped.append(line)
        return wrapped

    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.game.change_state(self.return_to)
        if event.key in (pygame.K_UP, pygame.K_w):
            self.scroll = max(0, self.scroll - 1)
        if event.key in (pygame.K_DOWN, pygame.K_s):
            self.scroll = min(max(0, len(self.lines) - 1), self.scroll + 1)
        if event.key in (pygame.K_PAGEUP,):
            self.scroll = max(0, self.scroll - 10)
        if event.key in (pygame.K_PAGEDOWN,):
            self.scroll = min(max(0, len(self.lines) - 1), self.scroll + 10)

    def update(self, delta_time: float):
        pass

    def render(self, screen: pygame.Surface):
        screen.fill((18, 20, 24))
        self.game.draw_text_center("HELP", WIDTH//2, 20, size=22, color=(220,220,240))
        y = 44
        font = self.game._get_font(18)
        visible_h = HEIGHT - y - 24
        max_lines = visible_h // self.line_height
        start = self.scroll
        end = min(len(self.lines), start + max_lines)
        for i in range(start, end):
            line = self.lines[i]
            surf = font.render(line, True, (220, 220, 220))
            screen.blit(surf, (self.margin, y + (i-start)*self.line_height))
        info = f"{start+1}-{end} / {len(self.lines)} • ↑/↓/w/s/PgUp/PgDn — scroll • BS/Esc — back"
        self.game.draw_text_center(info, WIDTH//2, HEIGHT - 12, size=14, color=(170,170,180))
