# -*- coding: utf8 -*-


class TreeNode:

    def __init__(self, parent, hero_action, weight):
        self.parent = parent
        self.state_info = None
        self.hero_action = None
        self.rival_hero_action = None
        self.weight = None
        self.next_state_info = None
        self.score = None

    def set_hero_action(self, hero_action, weight):
        self.hero_action = hero_action
        self.weight = weight

    def set_rivai_hero_action(self, rivai_hero_action, rival_weight):
        self.rival_hero_action = rivai_hero_action
        self.rival_weight = rival_weight

    def set_next_state_info(self, next_state_info):
        self.next_state_info = next_state_info

    def set_score(self, score):
        self.score = score
