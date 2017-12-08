# -*- coding: utf8 -*-


class TreeNode:

    def __init__(self, state_info, hero_action, weight):
        self.state_info = state_info
        self.hero_action = hero_action
        self.rival_hero_action = None
        self.weight = weight
        self.next_state_info = None
        self.score = None

    def set_rivai_hero_action(self, rivai_hero_action):
        self.rival_hero_action = rivai_hero_action

    def set_next_state_info(self, next_state_info):
        self.next_state_info = next_state_info

    def set_score(self, score):
        self.score = score
