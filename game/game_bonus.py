#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def code_select(score: int) -> int:
    if score > 6000:
        return 95009
    if score > 5000:
        return 88268
    if score > 4000:
        return 78751
    if score > 3000:
        return 61021
    if score > 2500:
        return 50578
    if score > 2000:
        return 45620
    if score > 1500:
        return 33086
    if score > 1000:
        return 29591
    return 11911

def give_bonus(mc, code, test):
    if code == 13168:
        if test:
            return True
        mc.add_exp(1000000)
        mc.add_gold(1000000)
        mc.mult_hp += 1250
        mc.mult_mp += 1250
        mc.mult_str += 1250
        mc.add_item(10, 5)
        mc.add_item(11, 1)
        mc.add_item(12, 1)
        mc.bonus_code = 13168
    
    if code == 11911:
        if test:
            return True
        mc.add_gold(1000)
        mc.bonus_code = 11911
    
    if code == 29591:
        if test:
            return True
        mc.add_gold(1000)
        mc.mult_str += 1
        mc.bonus_code = 29591
    
    if code == 33086:
        if test:
            return True
        mc.add_gold(1000)
        mc.mult_str += 1
        mc.add_item(10, 1)
        mc.bonus_code = 33086
    
    if code == 45620:
        if test:
            return True
        mc.add_gold(1000)
        mc.mult_hp += 1
        mc.mult_str += 1
        mc.add_item(10, 1)
        mc.bonus_code = 45620
    
    if code == 50578:
        if test:
            return True
        mc.add_gold(1000)
        mc.mult_hp += 1
        mc.mult_str += 2
        mc.add_item(10, 1)
        mc.bonus_code = 50578
    
    if code == 61021:
        if test:
            return True
        mc.add_gold(1000)
        mc.mult_hp += 1
        mc.mult_mp += 1
        mc.mult_str += 2
        mc.add_item(10, 1)
        mc.bonus_code = 61021
    
    if code == 78751:
        if test:
            return True
        mc.add_gold(10000)
        mc.mult_hp += 1
        mc.mult_mp += 1
        mc.mult_str += 2
        mc.add_item(10, 1)
        mc.bonus_code = 78751
    
    if code == 88268:
        if test:
            return True
        mc.add_exp(10000)
        mc.add_gold(10000)
        mc.mult_hp += 1
        mc.mult_mp += 1
        mc.mult_str += 2
        mc.add_item(10, 1)
        mc.bonus_code = 88268
    
    if code == 95009:
        if test:
            return True
        mc.add_exp(10000)
        mc.add_gold(10000)
        mc.mult_hp += 1
        mc.mult_mp += 1
        mc.mult_str += 2
        mc.add_item(10, 1)
        mc.add_item(11, 1)
        mc.bonus_code = 95009
    
    return False
