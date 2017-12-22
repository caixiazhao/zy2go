# -*- coding: utf8 -*-
from treesearch.stateevaluator import StateEvaluator


class TreeNode:

    def __init__(self, state_info, hero_action, rival_action, leaves):
        self.state_info = state_info
        self.hero_action = hero_action
        self.rival_hero_action = rival_action
        self.leaves = leaves
        self.next_state_info = None
        self.score = None

    def set_next_state_info(self, next_state_info):
        self.next_state_info = next_state_info

    def get_names(self):
        return [h.hero_name for h in [self.hero_action, self.rival_action]]

    def get_actions(self):
        return [self.hero_action, self.rival_hero_action]

    def cal_score(self):
        score, rival_score = StateEvaluator.score(self.next_state_info, self.state_info, self.hero_action.hero_name, self.rival_hero_action.hero_name)
        self.score = score - rival_score