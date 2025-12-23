#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List, Tuple
import string

import pygame
from .game_constants import WIDTH, HEIGHT, ITEMS, MAX_ITEMS_COUNT, SPELLS
from .game_bonus import give_bonus
from .game_class import IState

PAGE_SIZE = 14
ALLOWED_CHARS = set(string.ascii_letters + " '")

def is_sword(iid: int) -> bool:
    return 101 <= iid <= 199

def is_armor(iid: int) -> bool:
    return 201 <= iid <= 299

def is_ring(iid: int) -> bool:
    return 301 <= iid <= 399

class InventoryState(IState):
    def _get_count(self, iid: int) -> int:
        return int((self.game.player.inventory or {}).get(iid, 0))
    
    def _get_item_info(self, iid: int):
        it = ITEMS.get(iid, {})
        return (it.get("type", f"Item #{iid}").capitalize(), it.get("description", ""))
    
    def _would_overflow(self, iid: int, delta: int = 1) -> bool:
        return self._get_count(iid) + delta > MAX_ITEMS_COUNT
    
    def __init__(self, game: "Game", return_to: Optional[IState] = None):
        self.game = game
        self.return_to = return_to
        self.menu_items = ["Stats", "Spells", "Inventory", "Equipment", "Change Name", "Enter Bonus Code", "Back"]
        self.slots = ["Sword", "Armor", "Ring"]
    
    # --- IState hooks ---
    def enter(self):
        self.mode = "root"
        
        self.index = 0
        self.slot = 0
        self.scroll = 0
        
        self.sel_slot = False
        self.selected = False
        
        self.entries = []
        
        self.confirm_text = ""
        self.description_text = ""
        
        self.input_text = ""
        
        self.buttons = []
        self.button_i = 0
    
    def exit(self):
        pass
    
    # --- Data builders ---
    def _build_all_inventory(self):
        inv = self.game.player.inventory or {}
        self.entries = sorted([(iid, cnt) for iid, cnt in inv.items() if cnt > 0], key=lambda t: t[0])
        self.index = min(self.index, max(0, len(self.entries)-1))
        self.scroll = 0
    
    def _build_equip_list(self):
        inv = self.game.player.inventory or {}
        if self.slot == 0:
            allow = is_sword
        if self.slot == 1:
            allow = is_armor
        if self.slot == 2:
            allow = is_ring
        self.entries = [(iid, cnt) for iid, cnt in sorted(inv.items()) if allow(iid) and cnt > 0]
        
        equip_slot = self.slots[self.slot].lower()
        equip_id = self.game.player.equip[equip_slot]
        
        if equip_id > 0:
            self.entries.append((equip_id * -1, 0))
        
        self.index = min(0, max(0, len(self.entries)-1))
    
    def _get_item_name(self, iid: int) -> str:
        return ITEMS.get(iid, {}).get("name", f"#{iid}")
    
    def _get_item_desc(self, iid: int) -> Tuple[str,str]:
        t = ITEMS.get(iid, {}).get("type", "")
        d = ITEMS.get(iid, {}).get("description", "")
        return t or "", d or ""
    
    # --- Event handling ---
    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        
        if self.mode == "stats":
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.mode = "root"
            return
        
        if self.mode == "spells":
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.mode = "root"
            return
        
        if self.mode == "root":
            if event.key in (pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % len(self.menu_items)
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % len(self.menu_items)
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                choice = self.menu_items[self.index]
                if choice == "Stats":
                    self.mode = "stats"
                if choice == "Spells":
                    self.mode = "spells"
                if choice == "Inventory":
                    self.index = 0
                    self._build_all_inventory()
                    self.mode = "inventory"
                if choice == "Equipment":
                    self.index = 0
                    self.slot = 0
                    self.mode = "equip"
                if choice == "Change Name":
                    self.mode = "change_name"
                    self.input_text = self.game.player.name
                if choice == "Enter Bonus Code":
                    if getattr(self.game.player, "bonus_code", 0) != 0:
                        self.game.toast("Bonus already claimed.")
                    else:
                        self.mode = "bonus_code"
                        self.input_text = ""
                if choice == "Back":
                    self.game.change_state(self.return_to)
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.game.change_state(self.return_to)
            return
        
        if self.mode == "inventory" and not self.selected:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.selected = False
                self.mode = "root"
                self.index = 2
                return
            if len(self.entries) > 0:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.index = max(0, self.index - 1)
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.index = min(max(0, len(self.entries)-1), self.index + 1)
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.index = max(0, self.index - PAGE_SIZE)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.index = min(max(0, len(self.entries)-1), self.index + PAGE_SIZE)
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if len(self.entries) < 1:
                    self.game.toast("Nothing here.")
                    return
                
                item_type = self._get_item_info(self.entries[self.index][0])[0]
                if item_type == "Special":
                    self.game.toast("Might be useful later.")
                    return
                
                self._open_confirm_for_current()
                self.selected = True
            return
        
        if self.mode == "equip" and not self.sel_slot:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.selected = False
                self.mode = "root"
                self.index = 3
            if event.key in (pygame.K_UP, pygame.K_w):
                self.slot = max(0, self.slot - 1)
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.slot = min(max(0, len(self.slots) - 1), self.slot + 1)
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._build_equip_list()
                self.sel_slot = True
                self.index = 0
            return
        
        if self.mode == "equip" and self.sel_slot and not self.selected:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.mode = "equip"
                self.sel_slot = False
            if len(self.entries) > 0:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.index = max(0, self.index - 1)
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.index = min(max(0, len(self.entries)-1), self.index + 1)
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.index = max(0, self.index - PAGE_SIZE)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.index = min(max(0, len(self.entries)-1), self.index + PAGE_SIZE)
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if len(self.entries) < 1:
                    self.game.toast("Nothing here.")
                    return
                
                self._open_confirm_for_current()
                self.selected = True
            return
        
        if self.selected:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.selected = False
            if self.mode == "equip" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    iid, _ = self.entries[self.index]
                    
                    if iid > 0:
                        equip_slot_s = self.slots[self.slot].lower()
                        eid = self.game.player.equip[equip_slot_s]
                        if eid == iid:
                            self.game.toast("Already equipped.")
                            self.selected = False
                        else:
                            if eid != 0 and self.game.player.has_item(eid) > MAX_ITEMS_COUNT-1:
                                self.game.toast(f"Can't unequip previous {equip_slot_s}.")
                                self.selected = False
                            else:
                                if eid != 0:
                                    self.game.player.add_item(eid)
                                self.game.player.consume_item(iid)
                                self.game.player.equip[equip_slot_s] = iid
                                self.game.toast(f"Equipped {ITEMS.get(iid, {}).get('name', equip_slot_s)}.")
                                self.selected = False
                                self.sel_slot = False
                    if iid < 0:
                        equip_slot_s = self.slots[self.slot].lower()
                        eid = self.game.player.equip[equip_slot_s]
                        if eid != 0 and self.game.player.has_item(eid) > MAX_ITEMS_COUNT-1:
                            self.game.toast(f"Can't unequip {ITEMS.get(eid, {}).get('name', equip_slot_s)}.")
                            self.selected = False
                        else:
                            self.game.player.add_item(eid)
                            self.game.player.equip[equip_slot_s] = 0
                            self.game.toast(f"Unequipped {ITEMS.get(eid, {}).get('name', equip_slot_s)}.")
                            self.selected = False
                            self.sel_slot = False
            
            if self.mode == "inventory":
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.button_i = max(0, self.button_i - 1)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.button_i = min(max(0, len(self.buttons)-1), self.button_i + 1)
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    iid, _ = self.entries[self.index]
                    if self.buttons[self.button_i] == "Use":
                        self.game.player._use_item(iid)
                        self.game.toast("Used item.")
                    if self.buttons[self.button_i] == "Equip":
                        equip_slot_i = round(iid / 100) - 1
                        equip_slot_s = self.slots[equip_slot_i].lower()
                        eid = self.game.player.equip[equip_slot_s]
                        if eid == iid:
                            self.game.toast("Already equipped.")
                        else:
                            if eid != 0 and self.game.player.has_item(eid) > MAX_ITEMS_COUNT-1:
                                self.game.toast(f"Can't unequip previous {equip_slot_s}.")
                            else:
                                if eid != 0:
                                    self.game.player.add_item(eid)
                                self.game.player.consume_item(iid)
                                self.game.player.equip[equip_slot_s] = iid
                                self.game.toast(f"Equipped {ITEMS.get(iid, {}).get('name', equip_slot_s)}.")
                    if self.buttons[self.button_i] == "Drop":
                        self.game.player.consume_item(iid)
                        self.game.toast("Dropped 1 item.")
                    self._build_all_inventory()
                    self.selected = False
            return
        
        if self.mode == "change_name":
            if event.key in (pygame.K_ESCAPE,):
                self.mode = "root"
                return
            
            if event.key == pygame.K_RETURN:
                self.game.player.name = self.input_text.strip() or self.game.player.name
                self.mode = "root"
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                if event.unicode in ALLOWED_CHARS and len(self.input_text) < 16:  # 16 char limit
                    self.input_text += event.unicode
            
            return
        
        if self.mode == "bonus_code":
            if event.key in (pygame.K_ESCAPE,):
                self.mode = "root"
                return
            
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # Require exactly 5 digits
                if len(self.input_text) != 5:
                    self.game.toast("Enter a 5-digit code.")
                    return
                # Validate via dry-run
                code_int = int(self.input_text)
                if not give_bonus(self.game.player, code_int, True):
                    self.game.toast("Invalid code.")
                    return
                # Apply for real
                give_bonus(self.game.player, code_int, False)
                self.game.toast("Bonus unlocked!")
                self.mode = "root"
            elif event.key in (pygame.K_BACKSPACE,):
                self.input_text = self.input_text[:-1]
            else:
                # Only digits, length <= 5
                if event.unicode.isdigit() and len(self.input_text) < 5:
                    self.input_text += event.unicode
            
            return
    
    def _open_confirm_for_current(self):
        if len(self.entries) == 0:
            self.game.toast("Nothing here.")
            return
        
        name = ""
        item_type = ""
        item_description = ""
        
        self.confirm_text = ""
        self.buttons = ()
        
        iid, _ = self.entries[self.index]
        if iid > 0:
            name = ITEMS.get(iid, {}).get("name", f"Item {iid}")
            item_type, item_description = self._get_item_info(iid)
        if iid < 0:
            name = ITEMS.get(iid*-1, {}).get("name", f"Item {iid}")
            item_type, item_description = self._get_item_info(iid*-1)
        
        self.button_i = 0
        self.buttons = None
        if item_type == "Consumable":
            self.confirm_text = f"Action for {name}:"
            self.buttons = ("Use", "Drop")
        
        if item_type in ("Sword", "Armor", "Ring") and self.mode == "inventory":
            self.description_text = ""
            self.confirm_text = f"Action for {name}:"
            self.buttons = ("Equip", "Drop")
        
        if iid > 0 and item_type in ("Sword", "Armor", "Ring") and self.mode == "equip":
            self.description_text = f"{item_type} • {item_description}"
            self.confirm_text = f"Equip {name}?"
            self.buttons = ("Equip",)
        
        if iid < 0 and self.mode == "equip":
            self.description_text = f"{item_type} • {item_description}"
            self.confirm_text = f"Unequip {name}?"
            self.buttons = ("Unequip",)
    
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
        font = self.game._get_font(size)
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(x, y))
        screen.blit(surf, rect)
        if underline:
            uy = rect.bottom + 2
            pygame.draw.line(screen, (80,150,255), (rect.left, uy), (rect.right, uy), 2)
    
    def _draw_panel(self, screen: pygame.Surface, rect: pygame.Rect, title: str):
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg.fill((0,0,0,160))
        screen.blit(bg, rect)
        self.game.draw_text_center(title, rect.centerx, rect.top + 14, size=18, color=(255,240,220))
    
    def _draw_modal(self, screen):
        self.game.draw_text_center(self.confirm_text, WIDTH//2, HEIGHT//2 - 18, size=20, color=(255,230,210))
        
        if self.buttons and len(self.buttons) > 1:
            iid, _ = self.entries[self.index]
            if iid > 0 and iid <= 5:
                p = self.game.player
                max_hp = getattr(p, 'get_hero_max_hp', lambda: 0)()
                hp = f"{getattr(p, 'hp', 0):04}/{max_hp:04}"
                max_mp = getattr(p, 'get_hero_max_mp', lambda: 0)()
                mp = f"{getattr(p, 'mp', 0):04}/{max_mp:04}"
                
                self.game.draw_text_center(f"HP: {hp}", WIDTH - 90, HEIGHT - 78, size=12, color=(170,170,180))
                self.game.draw_text_center(f"MP: {mp}", WIDTH - 90, HEIGHT - 60, size=12, color=(170,170,180))
        
        if self.buttons and len(self.buttons) > 1:
            # otherwise draw buttons + hint as before
            btn_font = self.game._get_font(16)
            spacing = 20
            sizes = [btn_font.size(lbl) for lbl in self.buttons]
            total_w = sum(w for (w, h) in sizes) + spacing*(len(self.buttons)-1)
            start_x = (WIDTH - total_w) // 2
            baseline_y = HEIGHT//2 + 18
            
            for i, lbl in enumerate(self.buttons):
                w, h = sizes[i]
                surf = btn_font.render(lbl, True, (255, 255, 255))
                pos = (start_x, baseline_y - h)
                screen.blit(surf, pos)
                
                if i == self.button_i:
                    underline_y = baseline_y - 2
                    pygame.draw.line(screen, (0, 128, 255), (start_x, underline_y), (start_x + w, underline_y), 2)
                
                start_x += w + spacing
        
        if self.buttons and len(self.buttons) > 1:
            self.game.draw_text_center("←/→/a/d - move • Enter/Space - select • Esc/Backspace - cancel", WIDTH//2, HEIGHT - 18, size=14, color=(170,170,180))
        else:
            self.game.draw_text_center("Enter/Space - Yes • Esc/Backspace - No", WIDTH//2, HEIGHT//2 + 18, size=16, color=(180,180,190))
            self.game.draw_text_center(self.description_text, WIDTH//2, HEIGHT - 18, size=14, color=(170,170,180))
    
    def render(self, screen: pygame.Surface):
        screen.fill((24,20,28))
        
        if self.mode == "root":
            rect = pygame.Rect(24, 24, WIDTH-48, HEIGHT-58)
            self._draw_panel(screen, rect, f"- {self.game.player.name} -")
            
            y0 = rect.top + 42
            for i, label in enumerate(self.menu_items):
                y = y0 + i*28
                color = (255,220,120) if i == self.index else (200,200,210)
                mark = "•" if i == self.index else ""
                self.game.draw_text_center(f"{mark} {label} {mark}", rect.centerx, y, size=18, color=color)
            
            hint = "↑/↓/w/s - move • Enter/Space - select • Esc/Backspace - back"
            self.game.draw_text_center(hint, WIDTH//2, HEIGHT - 18, size=14, color=(170,170,180))
            return
        
        if self.mode == "stats":
            rect = pygame.Rect(24, 24, WIDTH-48, HEIGHT-58)
            self._draw_panel(screen, rect, "Stats")
            
            p = self.game.player
            max_hp = getattr(p, 'get_hero_max_hp', lambda: 0)()
            hp = f"{getattr(p, 'hp', 0):04}/{max_hp:04}"
            max_mp = getattr(p, 'get_hero_max_mp', lambda: 0)()
            mp = f"{getattr(p, 'mp', 0):04}/{max_mp:04}"
            
            lines = [
                f"Level: {p.get_hero_level():>18}",
                f"Next Level Exp: {p.next_level_exp():>9}",
                f"HP:    {hp:>18}",
                f"MP:    {mp:>18}",
                f"STR:   {p.get_hero_str():>18}",
                f"ATK:   {p.get_hero_atk():>18}",
                f"DEF:   {p.get_hero_def():>18}",
                f"Gold:  {p.gold:>18}",
                f"Keys:  {p.has_item(10):>18}",
            ]
            
            y0 = rect.top + 42
            for i, label in enumerate(lines):
                y = y0 + i*24
                color = (200,200,210)
                self.game.draw_text_center(f"{label}", rect.centerx, y, size=18, color=color)
            
            hint = "Esc/Backspace - back"
            self.game.draw_text_center(hint, WIDTH//2, HEIGHT - 18, size=14, color=(170,170,180))
            return
        
        if self.mode == "spells":
            rect = pygame.Rect(24, 24, WIDTH-48, HEIGHT-58)
            self._draw_panel(screen, rect, "Spells")
            
            spls = self.game.player.spells
            
            y0 = rect.top + 42
            for i, sid in enumerate(spls):
                y = y0 + i*24
                color = (200,200,210)
                sp_name = SPELLS.get(sid).get("name")
                sp_cost = SPELLS.get(sid).get("mp_cost")
                sp_power = SPELLS.get(sid).get("power")
                self.game.draw_text_center(f"{sp_name:<15} MP {sp_cost:02} PWR {sp_power:02}", rect.centerx, y, size=18, color=color)
            
            if len(spls) == 0:
                self.game.draw_text_center(f"(no known spells)", WIDTH//2, HEIGHT//2 - 9, size=18, color=(210,210,220))
            
            hint = "Esc/Backspace - back"
            self.game.draw_text_center(hint, WIDTH//2, HEIGHT - 18, size=14, color=(170,170,180))
            return
        
        if (self.mode == "inventory" or self.mode == "equip" and self.sel_slot) and not self.selected:
            rect = pygame.Rect(24, 24, WIDTH-48, HEIGHT-85)
            self._draw_panel(screen, rect, self.mode.capitalize())
            
            y0 = rect.top + 40
            if len(self.entries) > 0:
                rows = self.entries[self.scroll:self.scroll+PAGE_SIZE]
                for i, (iid, _) in enumerate(rows):
                    idx = self.scroll + i
                    sel = (idx == self.index)
                    y = y0 + i*24
                    
                    name = self._get_item_name(iid) if iid > 0 else "(unequip)"
                    have = int(self.game.player.inventory.get(iid, 0) or 0)
                    have = f" x{have:02}" if iid > 0 else '    '
                    line = f"{name:<30}{have}"
                    self._draw_text_center_underline(screen, line, rect.centerx, y, size=16, color=(255,220,120) if sel else (210,210,220), underline=sel)
                
                sel_item_id = self.entries[self.index][0]
                sel_item_id = sel_item_id if sel_item_id > 0 else sel_item_id * -1
                desc = self._get_item_info(sel_item_id)
                self.game.draw_text_center(f"{desc[0]} • {desc[1]}", WIDTH//2, HEIGHT - 50, size=14,  color=(170,170,180))
                
                hintb = f"Item - {self.index+1:02}/{len(self.entries):02} • "
                hintb += "↑/↓/←/→/w/s/a/d - move"
                self.game.draw_text_center(hintb, WIDTH//2, HEIGHT - 31, size=14, color=(170,170,180))
            else:
                self._draw_text_center_underline(screen, '(No items)', rect.centerx, HEIGHT//2 - 16, size=16, color=(210,210,220), underline=False)
            
            select_text = "Enter/Space - select • " if len(self.entries) > 0 else ""
            self.game.draw_text_center(f"{select_text}Esc/Backspace - back", WIDTH//2, HEIGHT - 12, size=14, color=(170,170,180))
            return
        
        if self.mode == "equip" and not self.sel_slot:
            rect = pygame.Rect(24, 24, WIDTH-48, HEIGHT-68)
            self._draw_panel(screen, rect, self.mode.capitalize())
            
            y0 = rect.top + 40
            for idx, slot_name in enumerate(self.slots):
                sel = (idx == self.slot)
                y = y0 + idx*24
                
                slot_contain = self.game.player.equip[slot_name.lower()]
                item_name = "(empty)" if slot_contain == 0 else self._get_item_name(slot_contain)
                line = f"{slot_name:<5}: {item_name:<28}"
                self._draw_text_center_underline(screen, line, rect.centerx, y, size=16, color=(255,220,120) if sel else (210,210,220), underline=sel)
            
            equip_slot_s = self.slots[self.slot]
            eid = self.game.player.equip[equip_slot_s.lower()]
            equip_desc = self._get_item_info(eid) if eid > 0 else (equip_slot_s, "Empty Slot")
            self.game.draw_text_center(f"{equip_desc[0]} • {equip_desc[1]}", WIDTH//2, HEIGHT - 31, size=14, color=(170,170,180))
            self.game.draw_text_center("↑/↓/w/s - move • Enter/Space - select • Esc/Backspace - back", WIDTH//2, HEIGHT - 12, size=14, color=(170,170,180))
        
        if self.selected:
            screen.fill((24,20,28))
            rect = pygame.Rect(24, 24, WIDTH-48, HEIGHT-58)
            self._draw_panel(screen, rect, "Action")
            self._draw_modal(screen)
        
        if self.mode == "change_name":
            rect = pygame.Rect(24, 24, WIDTH-48, HEIGHT-58)
            self._draw_panel(screen, rect, "Change Name")
            
            # Draw input box
            font = self.game._get_font(20)
            txt_surface = font.render(self.input_text, True, (255, 255, 255))
            
            box_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 20, 200, 40)
            pygame.draw.rect(screen, (50, 50, 70), box_rect)
            pygame.draw.rect(screen, (200, 200, 240), box_rect, 2)
            screen.blit(txt_surface, (box_rect.x + 5, box_rect.y + 5))
            
            self.game.draw_text_center("Only A–Z, a–z, apostrophe, and space allowed", WIDTH//2, HEIGHT//2 + 40, size=14, color=(200,170,170))
            self.game.draw_text_center("Type new name • Enter = confirm • Esc = cancel", WIDTH//2, HEIGHT - 18, size=14, color=(170,170,180))
            return
        
        if self.mode == "bonus_code":
            rect = pygame.Rect(24, 24, WIDTH-48, HEIGHT-58)
            self._draw_panel(screen, rect, "Enter Bonus Code")
            
            # Input box
            font = self.game._get_font(20)
            
            # Pad with minus for missing digits
            display_text = self.input_text.ljust(5, "-")
            
            txt_surface = font.render(display_text, True, (255, 255, 255))
            
            box_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 20, 200, 40)
            pygame.draw.rect(screen, (50, 50, 70), box_rect)
            pygame.draw.rect(screen, (200, 200, 240), box_rect, 2)
            
            # Center inside the box
            txt_rect = txt_surface.get_rect(center=box_rect.center)
            screen.blit(txt_surface, txt_rect)
            
            # Note + controls
            self.game.draw_text_center("Enter a 5-digit code (0–9 only).", WIDTH//2, HEIGHT//2 + 40, size=14, color=(200,170,170))
            self.game.draw_text_center("Only one code can be redeemed per save.", WIDTH//2, HEIGHT//2 + 58, size=14, color=(200,170,170))
            self.game.draw_text_center("Type code • Enter = confirm • Esc = cancel", WIDTH//2, HEIGHT - 18, size=14, color=(170,170,180))
            return
