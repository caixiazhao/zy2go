#!/usr/bin/env python
# -*- coding: utf-8 -*-

import clr

clr.AddReference("/Users/sky4star/Github/zy2go/lib/GaeaAI/GaeaAI")
clr.AddReference("/Users/sky4star/Github/zy2go/lib/GaeaAI/CommonLibs")
clr.AddReference("/Users/sky4star/Github/zy2go/lib/GaeaAI/Pathfinding.ClipperLib.dll")
clr.AddReference("/Users/sky4star/Github/zy2go/lib/GaeaAI/Pathfinding.Ionic.Zip.Reduced.dll")
clr.AddReference("/Users/sky4star/Github/zy2go/lib/GaeaAI/Pathfinding.JsonFx.dll")
clr.AddReference("/Users/sky4star/Github/zy2go/lib/GaeaAI/Pathfinding.Poly2Tri.dll")

import GaeaAI
from GaeaAI import ExportInterface
from GaeaAI import *
import MobaGo.FlatBuffer
import Pathfinding
import System


SWF = clr.AddReference("System.Windows.Forms")
print (SWF.Location)


GaeaAI.ExportInterface.InitialData("/Users/sky4star/Github/zy2go/lib/GaeaAI/")

GaeaAI.ExportInterface.InitialScene(GaeaAI.ExportInterface.eBattleScene.eBattleScene_5v5)

start = clr.VecInt3(-4600, 0, 0)
end = clr.VecInt3(4600, 0, 0)
path = GaeaAI.ExportInterface.SearchPath(start, end)


heroinfo = ExportInterface.GetHeroCfgInfo(101)
herolvinfo = ExportInterface.GetHeroLvUpInfo(112)
monster = ExportInterface.GetMonsterDataCfgInfo(914)
obelisk = ExportInterface.GetObeliskCfgInfo(964)
mapinfo = ExportInterface.GetMapSize()
skillinfo = ExportInterface.GetSkillCfgInfo(10200)
skillinfo2 = ExportInterface.GetSkillCfgInfo(10210)
skillinfo3 = ExportInterface.GetSkillCfgInfo(10220)
skillinfo4 = ExportInterface.GetSkillCfgInfo(10230)
equipinfo = ExportInterface.GetEquipInBattleInfo(11101)
print('%s %s %s' % (skillinfo.szSkillDesc, skillinfo.iMaxAttackDistance, skillinfo.dwRangeAppointType))
print('%s %s %s' % (skillinfo2.szSkillDesc, skillinfo2.iMaxAttackDistance, skillinfo2.dwRangeAppointType))
print('%s %s %s' % (skillinfo3.szSkillDesc, skillinfo3.iMaxAttackDistance, skillinfo3.dwRangeAppointType))
print('%s %s %s' % (skillinfo4.szSkillDesc, skillinfo4.iMaxAttackDistance, skillinfo4.dwRangeAppointType))

item_list = [11101,11201,11301,12101,12102,12103,12104,12201,12202,12203,12301,12302,12303,12304,12305,12306,12307,13101,13102,13103,13104,13105,13106,13107,13201,13202,13203,13301,13302,13303,13305,13306,21101,21201,21301,22101,22102,22103,22104,22105,22106,22107,22201,22202,22203,22301,22302,22303,23101,23102,23103,23201,23301,23302,23303,23304,23305,23306,23307,23308,31101,31201,31301,31401,32101,32103,32202,32203,32301,32302,32303,33101,33102,33103,33201,33202,33203,33301,33302,33303,33304,33305,33306,33307,33308,41101,41201,41301,42101,42102,42103,42201,43101,43201,43202,43203,43301,43302,43303]
for item in item_list:
    equipinfo = ExportInterface.GetEquipInBattleInfo(item)
    if equipinfo is not None:
        print('EquipCfgInfo({}, {}, {}, "{}", "{}")'.format(equipinfo.WID, equipinfo.DwBuyPrice, equipinfo.DwSalePrice, equipinfo.SzName.encode('utf-8'), equipinfo.SzDesc.encode('utf-8') if equipinfo.SzDesc is not None else ''))
    else:
        print(item, 'None')

print(heroinfo)
print(herolvinfo)

ExportInterface.GetSkillCfgInfo(923)
tower = ExportInterface.GetObeliskCfgInfo(900)
