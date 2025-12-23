#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List, Tuple

import pygame
from .game_constants import WIDTH, HEIGHT, ITEMS, SPELLS, MAX_ITEMS_COUNT
from .game_class import IState

PAGE_SIZE = 14  # rows per page for shop lists

# Category helpers (align with inventory)
def is_consumable(iid: int) -> bool:
    return 1 <= iid <= 99
def is_sword(iid: int) -> bool:
    return 100 <= iid <= 199
def is_armor(iid: int) -> bool:
    return 200 <= iid <= 299

BUY_PAGES = [
    ("Consumables", is_consumable),
    ("Swords",      is_sword),
    ("Armor",       is_armor),
]

class ShopState(IState):
    def __init__(self, game: "Game", return_to: Optional[IState] = None):
        self.game = game
        self.return_to = return_to
        
        self.mode = "root"     # "root" | "buy" | "sell" | "confirm"
        self.menu_items: List[str] = ["Buy", "Sell", "Learn Spell", "Exit"]
        self.index = 0         # index for root menu OR list selection
        
        # buy pages
        self.page_no = 0       # 0..len(BUY_PAGES)-1
        self.entries: List[Tuple[int,int]] = []  # list of (iid, price) for buy; or (iid, half_price) for sell
        self.scroll = 0
        self.confirm_text = ""
        self._pending_action = None  # callable to run on confirm
    
    # --- IState lifecycle ---
    def enter(self):
        self.mode = "root"
        self.index = 0
        self.page_no = 0
        self.scroll = 0
        self.entries = []
        self.confirm_text = ""
        self._pending_action = None
    
    def exit(self):
        pass
    
    def _build_buy_list(self):
        name, pred = BUY_PAGES[self.page_no]
        items = []
        for iid, meta in sorted(ITEMS.items()):
            price = int(meta.get("price", 0) or 0)
            if price <= 0:
                continue  # not for sale
            if pred(iid):
                items.append((iid, price))
        self.entries = items
        self.index = 0 if not self.entries else min(self.index, len(self.entries)-1)
        self.scroll = 0
    
    def _build_sell_list(self):
        # Only items with price > 0 and count > 0 can be sold
        items = []
        inv = self.game.player.inventory or {}
        for iid, cnt in sorted(inv.items()):
            if cnt <= 0:
                continue
            meta = ITEMS.get(iid, {})
            price = int(meta.get("price", 0) or 0)
            if price > 0:
                items.append((iid, price // 2))
        self.entries = items
        self.index = 0 if not self.entries else min(self.index, len(self.entries)-1)
        self.scroll = 0
    
    def _build_learn_list(self):
        # list of spells that cost > 0 and not yet learned
        learned = set(self.game.player.spells or [])
        items = []
        for sid, meta in sorted(SPELLS.items()):
            price = int(meta.get("price", 0) or 0)
            if price <= 0:
                continue
            if sid in learned:
                continue
            items.append((sid, price))
        self.entries = items
        self.index = 0 if not self.entries else min(self.index, len(self.entries)-1)
        self.scroll = 0
    
    def _would_overflow(self, iid: int, add: int = 1) -> bool:
        cur = int(self.game.player.inventory.get(iid, 0) or 0)
        return cur + add > MAX_ITEMS_COUNT
    
    def _buy_item(self, iid: int, price: int):
        p = self.game.player
        if self._would_overflow(iid, 1):
            self.game.toast(f"Max {MAX_ITEMS_COUNT} per item.")
            return
        if p.gold < price:
            self.game.toast("Not enough gold.")
            return
        # confirm
        name = ITEMS.get(iid, {}).get("name", f"#{iid}")
        self.confirm_text = f"Buy {name} for {price}G? (Y/N)"
        def action():
            p.gold -= price
            p.add_item(iid, 1)
            self.game.toast("Purchased.")
            # refresh lists
            if self.mode == "buy":
                self._build_buy_list()
        self._pending_action = action
        self.mode = "confirm"
    
    def _sell_item(self, iid: int, half_price: int):
        p = self.game.player
        if p.has_item(iid) <= 0:
            self.game.toast("You don't have this item.")
            return
        name = ITEMS.get(iid, {}).get("name", f"#{iid}")
        self.confirm_text = f"Sell {name} for {half_price}G? (Y/N)"
        def action():
            if p.consume_item(iid, 1):
                p.add_gold(half_price)
                self.game.toast("Sold.")
                self._build_sell_list()
        self._pending_action = action
        self.mode = "confirm"
    
    def _learn_spell(self, sid: int, price: int):
        p = self.game.player
        if sid in (p.spells or []):
            self.game.toast("Already learned.")
            return
        if p.gold < price:
            self.game.toast("Not enough gold.")
            return
        name = SPELLS.get(sid, {}).get("name", f"Spell #{sid}")
        self.confirm_text = f"Learn {name} for {price}G? (Y/N)"
        def action():
            p.gold -= price
            p.spells = sorted(list(set((p.spells or []) + [sid])))
            self.game.toast("Learned spell.")
            self._build_learn_list()
        self._pending_action = action
        self.mode = "confirm"

    # --- Event handling ---
    
    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        
        # Confirm dialog
        if self.mode == "confirm":
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self._pending_action:
                    self._pending_action()
                self.mode = "buy" if self.confirm_text.startswith("Buy") else ("sell" if self.confirm_text.startswith("Sell") else "learn")
                self._pending_action = None
                self.confirm_text = ""
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.mode = "buy" if self.confirm_text.startswith("Buy") else ("sell" if self.confirm_text.startswith("Sell") else "learn")
                self._pending_action = None
                self.confirm_text = ""
            return
        
        # Root menu
        if self.mode == "root":
            if event.key in (pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % len(self.menu_items)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % len(self.menu_items)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                choice = self.menu_items[self.index]
                if choice == "Buy":
                    self.mode = "buy"
                    self.page_no = 0
                    self.index = 0
                    self._build_buy_list()
                elif choice == "Sell":
                    self.mode = "sell"
                    self.index = 0
                    self._build_sell_list()
                elif choice == "Learn Spell":
                    self.mode = "learn"
                    self.index = 0
                    self._build_learn_list()
                elif choice == "Exit":
                    self.game.change_state(self.return_to or self.game.states.get("menu", None) or self)
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.game.change_state(self.return_to or self.game.states.get("menu", None) or self)
            return
        
        # Buy / Sell / Learn lists
        if self.mode in ("buy", "sell", "learn"):
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                # back to root
                self.mode = "root"
                self.index = 0
                return
            if event.key in (pygame.K_UP, pygame.K_w):
                self.index = max(0, self.index - 1)
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = min(max(0, len(self.entries)-1), self.index + 1)
            if self.mode == "buy" and event.key in (pygame.K_LEFT, pygame.K_a):
                self.page_no = (self.page_no - 1) % len(BUY_PAGES)
                self.index = 0
                self.scroll = 0
                self._build_buy_list()
            if self.mode == "buy" and event.key in (pygame.K_RIGHT, pygame.K_d):
                self.page_no = (self.page_no + 1) % len(BUY_PAGES)
                self.index = 0
                self.scroll = 0
                self._build_buy_list()
            if self.mode == "sell" and event.key in (pygame.K_LEFT, pygame.K_a):
                self.index = max(0, self.index - PAGE_SIZE)
            if self.mode == "sell" and event.key in (pygame.K_RIGHT, pygame.K_d):
                self.index = min(max(0, len(self.entries)-1), self.index + PAGE_SIZE)
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if not self.entries:
                    self.game.toast("Nothing here.")
                    return
                iid, price = self.entries[self.index]
                if self.mode == "buy":
                    self._buy_item(iid, price)
                elif self.mode == "sell":
                    self._sell_item(iid, price)
                else:
                    self._learn_spell(iid, price)

    def update(self, delta_time: float):
        # keep scroll in sync
        top = self.scroll
        bot = self.scroll + PAGE_SIZE - 1
        if self.index < top:
            self.scroll = self.index
        elif self.index > bot:
            self.scroll = self.index - (PAGE_SIZE - 1)
        self.scroll = max(0, min(self.scroll, max(0, len(self.entries) - PAGE_SIZE)))
    
    def _draw_text_center_underline(self, screen: pygame.Surface, text: str, x: int, y: int, *, size: int = 18, color=(220,220,220), underline: bool = False):
        # Render text centered at (x, y). If underline, draw a blue underline below.
        font = self.game._get_font(size)
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(x, y))
        screen.blit(surf, rect)
        if underline:
            # Blue underline slightly below the text
            uy = rect.bottom + 2
            pygame.draw.line(screen, (80,150,255), (rect.left, uy), (rect.right, uy), 2)
    
    def _draw_panel(self, screen: pygame.Surface, rect: pygame.Rect, title: str):
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg.fill((0,0,0,160))
        screen.blit(bg, rect)
        # title
        self.game.draw_text_center(title, rect.centerx, rect.top + 14, size=18, color=(255,240,220))
    
    def _draw_money(self, screen: pygame.Surface):
        text = f"Gold: {self.game.player.gold:>9} G"
        self.game.draw_text_center(text, WIDTH - 118, 20, size=18, color=(255,240,180))
    
    def _get_item_name(self, iid: int) -> str:
        return ITEMS.get(iid, {}).get("name", f"#{iid}")
    
    def _get_item_desc(self, iid: int) -> Tuple[str,str]:
        t = ITEMS.get(iid, {}).get("type", "")
        d = ITEMS.get(iid, {}).get("description", "")
        return t or "", d or ""
    
    def _get_spell_name(self, sid: int) -> str:
        return SPELLS.get(sid, {}).get("name", f"Spell #{sid}")
    
    def _get_spell_desc(self, sid: int):
        meta = SPELLS.get(sid, {}) or {}
        t = meta.get("type", "")
        d = meta.get("description", "")
        mp = int(meta.get("mp_cost", 0) or 0)
        pwr = int(meta.get("power", 0) or 0)
        return (t or ""), (d or ""), mp, pwr
    
    def render(self, screen: pygame.Surface):
        screen.fill((24,20,28))
        
        # header
        self._draw_money(screen)
        
        if self.mode == "root":
            rect = pygame.Rect(24, 40, WIDTH-48, HEIGHT-70)
            self._draw_panel(screen, rect, "Shop")
            
            # menu list
            y0 = rect.top + 42
            for i, label in enumerate(self.menu_items):
                y = y0 + i*28
                color = (255,220,120) if i == self.index else (200,200,210)
                mark = "•" if i == self.index else ""
                self.game.draw_text_center(f"{mark} {label} {mark}", rect.centerx, y, size=18, color=color)
            
            # hints
            hint = "↑/↓ - move • Enter/Space - select • Esc/Backspace - back"
            self.game.draw_text_center(hint, WIDTH//2, HEIGHT - 18, size=14, color=(170,170,180))
            return
        
        if self.mode in ("buy", "sell", "learn"):
            title = "Buy" if self.mode == "buy" else ("Sell" if self.mode == "sell" else "Learn Spell")
            if self.mode == "buy":
                title = f"{title:<12}"
                title += f"  -{self.page_no+1}/{len(BUY_PAGES)}-  "
                title += f"{BUY_PAGES[self.page_no][0]:>12}"
            rect = pygame.Rect(24, 40, WIDTH-48, HEIGHT-100)
            self._draw_panel(screen, rect, title)
            
            # draw columns: Name | Price | Have
            y0 = rect.top + 40
            rows = self.entries[self.scroll:self.scroll+PAGE_SIZE]
            for i, (iid, price) in enumerate(rows):
                idx = self.scroll + i
                sel = (idx == self.index)
                y = y0 + i*24
                
                name = self._get_spell_name(iid) if self.mode == "learn" else self._get_item_name(iid)
                if self.mode == "learn":
                    mp = int(SPELLS.get(iid, {}).get("mp_cost", 0) or 0)
                    line = f"{name:<25} {price:>4}G (MP{mp:02})"
                else:
                    have = int(self.game.player.inventory.get(iid, 0) or 0)
                    line = f"{name:<25} {price:>4}G ({have:02})"
                self._draw_text_center_underline(screen, line, rect.centerx, y, size=16, color=(255,220,120) if sel else (210,210,220), underline=sel)
            
            if not rows:
                self.game.draw_text_center("(No items)", rect.centerx, rect.centery, size=16, color=(200,200,210))
            
            # bottom hint: show type + description of selected
            hint0 = ""
            if self.entries:
                sel_iid = self.entries[self.index][0]
                if self.mode == "learn":
                    t, d, mp, pwr = self._get_spell_desc(sel_iid)
                    extra = f" • MP {mp}" if mp else ""
                    hint0 = f"{t.title()}{extra} • {d}" if (t or d) else f"MP {mp}"
                else:
                    t, d = self._get_item_desc(sel_iid)
                    hint0 = f"{t.capitalize()} • {d}"
            if hint0:
                self.game.draw_text_center(hint0, WIDTH//2, HEIGHT - 50, size=14, color=(170,170,180))
            
            # control hints
            if self.mode == "buy":
                hint1 = "←/→/a/d - pages • ↑/↓/w/s - move"
            if self.mode == "sell":
                hint1 = f"Item - {self.index+1:02}/{len(self.entries):02} • "
                hint1 += "↑/↓/←/→/w/s/a/d - move"
            if self.mode == "learn":
                hint1 = "↑/↓ - move"
            self.game.draw_text_center(hint1, WIDTH//2, HEIGHT - 31, size=14, color=(170,170,180))
            self.game.draw_text_center("Enter/Space - select • Esc/Backspace - back", WIDTH//2, HEIGHT - 12, size=14, color=(170,170,180))
            return
        
        if self.mode == "confirm":
            self.game.draw_text_center(self.confirm_text or "Are you sure? (Y/N)", WIDTH//2, HEIGHT//2 - 6, size=20, color=(255,230,210))
            self.game.draw_text_center("Enter/Space - Yes • Esc/Backspace - No", WIDTH//2, HEIGHT//2 + 18, size=16, color=(180,180,190))
