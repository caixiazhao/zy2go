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
herolvinfo = ExportInterface.GetHeroLvUpInfo(923)
monster = ExportInterface.GetMonsterDataCfgInfo(902)
mapinfo = ExportInterface.GetMapSize()
skillinfo = ExportInterface.GetSkillCfgInfo(11402)
print heroinfo
print herolvinfo

ExportInterface.GetSkillCfgInfo(923)
ExportInterface.GetObeliskCfgInfo(923);
            # ExportInterface.GetSkillCombineInfo(923);
            # ExportInterface.GetHeroLvUpInfo(923);
            # ExportInterface.GetLevelCfgInfo(923);
            # ExportInterface.GetSkillMarkInfo(923);
            # ExportInterface.GetMonsterObeliskLevelDynamicInfo(923);
            # ExportInterface.GetEquipInBattleInfo(923);