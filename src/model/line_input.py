# -*- coding: utf8 -*-
import numpy as np


class Line_input:
    def __init__(self, stateInformation,team):
        self.stateInformation = stateInformation
        self.team=team

    def gen_input(self):
        state=[]
        for hero in self.stateInformation.heros:
            hero_input=self.gen_input_hero(hero)
            state=state+hero_input
            #todo:仅对1v1模型有效，第一个英雄为当前操作英雄
         for

    def gen_input_hero(self,hero):

    def gen_input_skill(self,skill):

    def gen_input_building(self,building):

    def gen_input_creep(self,creep):