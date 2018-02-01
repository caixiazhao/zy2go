#!/usr/bin/env python
# -*- coding: utf-8 -*-
from model.cmdaction import CmdAction
from model.equipcfginfo import EquipCfgInfo
from train.cmdactionenum import CmdActionEnum


class EquipUtil:

    # 从dll中读取的装备信息，但是dll比较旧，有些没有更新，价格其实也不确定是否有过更新
    equip_infos = [
        EquipCfgInfo(11101, 180, 162, "铁剑", "攻击力　+10"),
        EquipCfgInfo(11201, 230, 207, "索瓦剑", ""),
        EquipCfgInfo(11301, 160, 144, "虎刺拳套", "暴击几率　+6%"),
        EquipCfgInfo(12101, 550, 495, "切割斧", "攻击力　+20 被动　+10护甲穿透"),
        EquipCfgInfo(12102, 500, 450, "汲取镰刀", ""),
        EquipCfgInfo(12103, 780, 702, "大木槌", "生命值　+200 攻击力　+20"),
        EquipCfgInfo(12104, 650, 585, "裂创之剑", ""),
        EquipCfgInfo(12201, 820, 738, "石中剑", "攻击力　+45"),
        EquipCfgInfo(12202, 625, 562, "魔法剑", "攻击速度　+40% 被动　+10%冷却缩减"),
        EquipCfgInfo(12203, 450, 405, "白银枪", "攻击力　+25"),
        EquipCfgInfo(12301, 365, 328, "轻灵披风", "暴击几率　+15%"),
        EquipCfgInfo(12302, 200, 180, "短弓", "攻击速度　+10%"),
        EquipCfgInfo(12303, 600, 540, "急速弓", ""),
        # (12304, 'None')
        # (12305, 'None')
        # (12306, 'None')
        # (12307, 'None')
        EquipCfgInfo(13101, 800, 720, "斩马刀", "攻击力　+35"),
        EquipCfgInfo(13102, 1700, 1530, "收获者之镰", ""),
        EquipCfgInfo(13103, 1750, 1575, "众神之锋", ""),
        EquipCfgInfo(13104, 1550, 1395, "狂战双斧", ""),
        EquipCfgInfo(13105, 1600, 1440, "炎龙之息", ""),
        EquipCfgInfo(13106, 1700, 1530, "重创焰爪", ""),
        EquipCfgInfo(13107, 1600, 1440, "救赎圣剑", ""),
        EquipCfgInfo(13201, 1900, 1710, "正宗", ""),
        EquipCfgInfo(13202, 1450, 1305, "奥术圣剑", ""),
        EquipCfgInfo(13203, 1600, 1440, "绯暮破甲斧", ""),
        EquipCfgInfo(13301, 1150, 1035, "藏剑盾", "护甲　+36 暴击几率　+15% 被动　增加相当于你最大生命值2.5%的攻击力"),
        EquipCfgInfo(13302, 1550, 1395, "闪电之刃", ""),
        EquipCfgInfo(13303, 1500, 1350, "逐日之弓", ""),
        EquipCfgInfo(13305, 1800, 1620, "潜行者匕首", ""),
        EquipCfgInfo(13306, 1750, 1575, "残废之刃", ""),
        EquipCfgInfo(21101, 300, 270, "红魔晶", "生命值　+100"),
        EquipCfgInfo(21201, 230, 207, "索瓦盾", "护甲　+8 生命值　+60 生命恢复　+6/5秒"),
        EquipCfgInfo(21301, 150, 135, "斥候布甲", "护甲　+10"),
        EquipCfgInfo(22101, 450, 405, "冰霜魔石", ""),
        EquipCfgInfo(22102, 650, 585, "征章腰带", ""),
        EquipCfgInfo(22103, 500, 450, "骑士战靴", "护甲　+35 唯一被动 移动速度　+65"),
        # (22104, 'None')
        # (22105, 'None')
        # (22106, 'None')
        # (22107, 'None')
        EquipCfgInfo(22201, 700, 630, "菱法披风", "生命值　+200 法术防御　+20 物理防御　+35"),
        EquipCfgInfo(22202, 250, 225, "聚能披风", "法术防御　+20"),
        EquipCfgInfo(22203, 650, 585, "凌冷之靴", ""),
        EquipCfgInfo(22301, 600, 540, "斥候锁铠", "护甲　+35 被动　被普通攻击击中时，减少攻击者15%的攻击速度，持续1秒。"),
        EquipCfgInfo(22302, 550, 495, "秘法护盾", ""),
        EquipCfgInfo(22303, 400, 360, "骑士大铠", "护甲　+30"),
        EquipCfgInfo(23101, 1500, 1350, "精灵铠甲", ""),
        EquipCfgInfo(23102, 1700, 1530, "魔龙之心", "生命值　+1000 每五秒生命恢复 +30 被动　每3秒恢复1%的最大生命值。"),
        EquipCfgInfo(23103, 1650, 1485, "寒冰之锤", "生命值　+470 攻击力　+30 被动　普通攻击将降低目标40%的移动速度，持续1.5秒。"),
        EquipCfgInfo(23201, 1500, 1350, "魔法护盾", ""),
        EquipCfgInfo(23301, 1600, 1440, "黑石刃铠", "护甲　+70 生命　+300被动　在被普通攻击命中时，会将普通攻击伤害的45%转为魔法伤害回敬给攻击者。"),
        EquipCfgInfo(23302, 1500, 1350, "石化之盾", "生命值+400  护甲　+ 60 冷却缩减　+15% 魔法值　+400 被动　降低附近敌方单位15%的攻击速度。"),
        EquipCfgInfo(23303, 1550, 1395, "烈焰战甲", "护甲　+45 生命值　+450 每五秒生命恢复+15 被动　对周围敌方造成每秒60点魔法伤害。"),
        EquipCfgInfo(23304, 1550, 1395, "光辉之翼", ""),
        EquipCfgInfo(23305, 1650, 1485, "狂战之盔", ""),
        EquipCfgInfo(23306, 1500, 1350, "骑士盾", ""),
        EquipCfgInfo(23307, 650, 585, "坚毅吊坠", ""),
        EquipCfgInfo(23308, 1600, 1440, "军团守护者", ""),
        EquipCfgInfo(31101, 200, 180, "智慧法书", ""),
        EquipCfgInfo(31201, 220, 198, "索瓦戒", ""),
        EquipCfgInfo(31301, 250, 225, "蓝魔晶", ""),
        EquipCfgInfo(31401, 100, 90, "紫魔晶", ""),
        EquipCfgInfo(32101, 500, 450, "苦难面罩", ""),
        EquipCfgInfo(32103, 750, 675, "蓄能之剑", ""),
        EquipCfgInfo(32202, 430, 387, "贤者法杖", ""),
        EquipCfgInfo(32203, 800, 720, "魔能长杖", ""),
        EquipCfgInfo(32301, 450, 405, "能量宝石", ""),
        EquipCfgInfo(32302, 440, 396, "法力图腾", "魔法恢复　+7/5s 魔法抗性　+25 魔法源泉　每损失1%的魔法值会提高你1%的魔法恢复速度。"),
        EquipCfgInfo(32303, 500, 450, "恐惧魔杖", ""),
        EquipCfgInfo(33101, 1550, 1395, "永生假面", ""),
        EquipCfgInfo(33102, 1150, 1035, "禁术密卷", "冷却缩减　+10% 法术强度　+80 被动　+20%法术吸取（无属性）"),
        EquipCfgInfo(33103, 1500, 1350, "妖祸法刃", ""),
        EquipCfgInfo(33201, 1700, 1530, "法师护手", ""),
        EquipCfgInfo(33202, 1700, 1530, "湮灭之帽", ""),
        EquipCfgInfo(33203, 1900, 1710, "魔龙之角", ""),
        EquipCfgInfo(33301, 1650, 1485, "圣神使之柱", ""),
        EquipCfgInfo(33302, 1300, 1170, "先祖图腾",
                     "冷却缩减　+20% 魔法恢复　+15/5秒 魔法抗性　+40 法术强度　+60 唯一被动　在消灭或助攻后，恢复你50%的最大魔法值。 魔法源泉　每损失1%的魔法值会提高你1%的魔法恢复速度。"),
        EquipCfgInfo(33303, 1600, 1440, "冰灵之心", ""),
        EquipCfgInfo(33304, 1700, 1530, "断罪残章", ""),
        EquipCfgInfo(33305, 1650, 1485, "破魔法戒", ""),
        EquipCfgInfo(33306, 1200, 1080, "胜者勋章", ""),
        EquipCfgInfo(33307, 1750, 1575, "巫术权杖", ""),
        EquipCfgInfo(33308, 1600, 1440, "蛇行权杖", ""),
        EquipCfgInfo(41101, 1700, 1530, "皇家守卫", ""),
        EquipCfgInfo(41201, 200, 180, "魔抗披风", "魔法抗性　+10"),
        EquipCfgInfo(41301, 240, 216, "远行军靴", ""),
        EquipCfgInfo(42101, 600, 540, "巫语皮靴", ""),
        EquipCfgInfo(42102, 600, 540, "急速靴", ""),
        EquipCfgInfo(42103, 700, 630, "精灵战靴", ""),
        EquipCfgInfo(42201, 750, 675, "轻甲战靴", ""),
        EquipCfgInfo(43101, 200, 180, "小猎刀", ""),
        EquipCfgInfo(43201, 600, 540, "狩猎弯刀", ""),
        EquipCfgInfo(43202, 600, 540, "狩猎皮甲", ""),
        EquipCfgInfo(43203, 600, 540, "狩猎护符", ""),
        EquipCfgInfo(43301, 1500, 1350, "狂野猎刀", ""),
        EquipCfgInfo(43302, 1400, 1260, "灼热皮甲", ""),
        EquipCfgInfo(43303, 1450, 1305, "巫妖护符", "")
    ]

    equip_plans = {'101': [41301, 11101, 12102, 42102, 11101, 12203, 13105, 12201, 13102, 12201, 13201],
                   #查尔斯：远行军靴, 铁剑, 汲取镰刀, 急速靴, 铁剑，白银枪，炎龙之息, 石中剑, 收获者之镰, 石中剑, 正宗
                   '102': [41301, 12302, 11301, 12303, 42103, 11101, 12102, 12201, 13102],
                   #盖娅：远行军靴, 短弓，虎刺拳套，急速弓，精灵战靴, 铁剑, 汲取镰刀, 石中剑, 收获者之镰
                   '103': [41301, 11101, 12102, 42201, 11101, 12203, 13105, 13306, 22301, 22102, 41101],
                   #德古拉：远行军靴, 铁剑, 汲取镰刀，轻甲战靴，铁剑，白银枪，炎龙之息, 残废之刃, 斥候锁铠, 征章腰带，皇家守卫
                   '104': [41301, 11101, 12102, 42103, 22202, 21101, 22201, 22102, 23303, 12201, 13201],
                   #洛克：远行军靴, 铁剑, 汲取镰刀，精灵战靴, 聚能披风, 红魔晶, 菱法披风, 征章腰带, 烈焰战甲, 石中剑, 正宗
                   '106': [41301, 22203, 33303, 23101, 23304, 23102]
                   #蕾娜斯：远行军靴, 凌冷之靴, 冰灵之心, 精灵铠甲, 光辉之翼, 魔龙之心
                  }


    @staticmethod
    def buy_equip(state_info, hero_name):
        hero = state_info.get_hero(hero_name)
        if hero.cfg_id in EquipUtil.equip_plans:
            plan = EquipUtil.equip_plans[hero.cfg_id]

            # 按顺序查找玩家还不具有的装备
            owned_equips = [int(item.id) for item in hero.equips]
            for equip_id in plan:
                if equip_id not in owned_equips:
                    equip_info = EquipUtil.get_equip_info(equip_id)
                    if equip_info.buy_price <= hero.gold:
                        print(state_info.battleid, hero_name, '购买道具', equip_id, '当前拥有', ','.join(str(e) for e in owned_equips),
                              '金币', hero.gold, '价格', equip_info.buy_price, '名称', equip_info.name)
                        return CmdAction(hero_name, CmdActionEnum.BUY, None, None, None, None, equip_id, None, None)
                    else:
                        # 如果钱不够直接返回空，而不是购买下一件商品
                        return None
        return None

    @staticmethod
    def get_equip_info(id):
        for equip_info in EquipUtil.equip_infos:
            if equip_info.cfg_id == id:
                return equip_info
        return None