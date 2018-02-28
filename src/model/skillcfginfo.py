# -*- coding: utf8 -*-


# 记录技能的各种属性，方便模型来决策选择技能
# 瞬间伤害, 后续伤害, 回复, 防御加强, 攻击加强, 回复加强, 移动加强, 防御削弱, 攻击削弱, 减速, 控制, 位移, 伤害范围, 施法距离, 最大施法时间, 施法对象
class SkillCfgInfo:
    def __init__(self, hero_id, skill_id, instant_dmg, sustained_dmg, restore, defend_bonus, attack_bonus, restore_bonus,
                 move_bonus, defend_weaken, attack_weaken, move_weaken, stun, blink, dmg_range, cast_distance,
                 max_cast_duration, cast_target):
        self.hero_id = hero_id
        self.skill_id = skill_id
        self.instant_dmg = instant_dmg
        self.sustained_dmg = sustained_dmg
        self.restore = restore
        self.defend_bonus = defend_bonus
        self.attack_bonus = attack_bonus
        self.restore_bonus = restore_bonus
        self.move_bonus = move_bonus
        self.defend_weaken = defend_weaken
        self.attack_weaken = attack_weaken
        self.move_weaken = move_weaken
        self.stun = stun
        self.blink = blink
        self.dmg_range = dmg_range
        self.cast_distance = cast_distance
        self.max_cast_duration = max_cast_duration
        self.cast_target = cast_target


class SkillTargetEnum:
        def __init__(self):
            pass

        rival = 0
        self = 1
        both = 2
        buff = 3
