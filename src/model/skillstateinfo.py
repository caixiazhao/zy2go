# -*- coding: utf8 -*-

class SkillStateInfo(object):
    def __init__(self, skill_name, skill_id, max_cd, cd, cost):
        self.skill_name = skill_name
        self.skill_id = skill_id
        self.max_cd = max_cd
        self.cd = cd
        self.cost = cost

    def merge(self, delta):
        self.skill_name = delta.skill_name if delta.skill_name is not None else self.skill_name
        self.skill_id = delta.skill_id if delta.skill_id is not None else self.skill_id
        self.max_cd = delta.max_cd if delta.max_cd is not None else self.max_cd
        self.cd = delta.cd if delta.cd is not None else self.cd
        self.cost = delta.cost if delta.cost is not None else self.cost

    @staticmethod
    def decode(obj, name):
        skill_name = name
        skill_id = obj['ID']
        # maxcd有可能是0，表示被动技能？
        max_cd = obj['MaxCD'] if 'MaxCD' in obj else None
        # 如果没有cd时间信息，和上一帧一样
        cd = obj['CD'] if 'CD' in obj else None
        cost = obj['Cost'] if 'Cost' in obj else 0
        return SkillStateInfo(skill_name, skill_id, max_cd, cd, cost)
