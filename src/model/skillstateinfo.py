# -*- coding: utf8 -*-


class SkillStateInfo(object):
    def __init__(self, skill_name, skill_id, max_cd, cd, cost, canuse, up):
        self.skill_name = skill_name
        self.skill_id = skill_id
        self.max_cd = max_cd
        self.cd = cd
        self.cost = cost
        self.canuse = canuse
        self.up = up

    def merge(self, delta):
        skill_name = delta.skill_name if delta.skill_name is not None else self.skill_name
        skill_id = delta.skill_id if delta.skill_id is not None else self.skill_id
        max_cd = delta.max_cd if delta.max_cd is not None else self.max_cd
        cd = delta.cd   # CD不做合并了，delta中没有就是为零，为零表示可以使用
        cost = delta.cost if delta.cost is not None else self.cost
        canuse = delta.canuse if delta.canuse is not None else self.canuse
        up = delta.up if delta.up is not None else self.up
        return SkillStateInfo(skill_name, skill_id, max_cd, cd, cost, canuse, up)

    @staticmethod
    def decode(obj, name):
        skill_name = name
        skill_id = obj['ID']
        max_cd = obj['MaxCD'] if 'MaxCD' in obj else None
        cd = obj['CD'] if 'CD' in obj else 0        # CD默认值为零
        cost = obj['Cost'] if 'Cost' in obj else None
        canuse = obj['canuse'] if 'canuse' in obj else None
        up = obj['up'] if 'up' in obj else None
        return SkillStateInfo(skill_name, skill_id, max_cd, cd, cost, canuse, up)
