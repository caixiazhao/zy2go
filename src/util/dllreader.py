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
monster = ExportInterface.GetMonsterDataCfgInfo(911)
print monster.szName
obelisk = ExportInterface.GetObeliskCfgInfo(964)
mapinfo = ExportInterface.GetMapSize()
skillinfo = ExportInterface.GetSkillCfgInfo(10200)
skillinfo2 = ExportInterface.GetSkillCfgInfo(10210)
skillinfo3 = ExportInterface.GetSkillCfgInfo(10220)
skillinfo4 = ExportInterface.GetSkillCfgInfo(10230)
equipinfo = ExportInterface.GetEquipInBattleInfo(11101)
print '%s %s %s' % (skillinfo.szSkillDesc, skillinfo.iMaxAttackDistance, skillinfo.dwRangeAppointType)
print '%s %s %s' % (skillinfo2.szSkillDesc, skillinfo2.iMaxAttackDistance, skillinfo2.dwRangeAppointType)
print '%s %s %s' % (skillinfo3.szSkillDesc, skillinfo3.iMaxAttackDistance, skillinfo3.dwRangeAppointType)
print '%s %s %s' % (skillinfo4.szSkillDesc, skillinfo4.iMaxAttackDistance, skillinfo4.dwRangeAppointType)

print heroinfo
print herolvinfo

ExportInterface.GetSkillCfgInfo(923)
tower = ExportInterface.GetObeliskCfgInfo(900)
