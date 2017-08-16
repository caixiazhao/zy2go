from model.skillcfginfo import SkillCfgInfo


class SkillUtil:
    skill_info = [
        SkillCfgInfo(101, 1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 8, 0),
        SkillCfgInfo(101, 2, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 2.5, 6, 0),
        SkillCfgInfo(101, 3, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 3.5, 3.5, 2),
        SkillCfgInfo(102, 1, 4, 4, 0, 0, 0, 0, 0, 4, 0, 5, 0, 0, 3, 8, 0),
        SkillCfgInfo(102, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 4, 0, 5, 0),
        SkillCfgInfo(102, 3, 2, 10, 5, 7, 0, 0, 0, 0, 0, 0, 0, 0, 6, 6, 2),
        SkillCfgInfo(103, 1, 4, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 5, 0),
        SkillCfgInfo(103, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 0, 3, 7, 0),
        SkillCfgInfo(103, 3, 0, 0, 0, 10, 5, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0),
        SkillCfgInfo(104, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 5, 3, 0, 0),
        SkillCfgInfo(104, 2, 4, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 3, 0, 0),
        SkillCfgInfo(104, 3, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0),
        SkillCfgInfo(105, 1, 1, 5, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 3, 0, 0),
        SkillCfgInfo(105, 2, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0),
        SkillCfgInfo(105, 3, 3, 7, 0, 5, 0, 0, 0, 0, 0, 10, 5, 0, 3, 0, 0)]

    @staticmethod
    def get_skill_info(hero_cfg_id, skill_id):
        for info in SkillUtil.skill_info:
            if info.hero_id == int(hero_cfg_id) and info.skill_id == int(skill_id):
                return info
        return None

