# -*- coding: utf8 -*-

# 根据当前状态，英雄的选择，英雄对对方行为的猜测，
# 根据类似蒙特卡洛树搜索的方式，
# 预测后续短时间内双方的状态变化，评估相应的分数，
# 从而选择出英雄当前最应该选择的行为
from train.linemodel import LineModel
from treesearch.treenode import TreeNode


class TreeSearch:

    # 根据状态信息，根据英雄行为选择，得到下一刻的状态，和当期每个行为的得分
    @staticmethod
    def choose_action(parent_tree_node, hero_name, rival_hero_name, line_trainer):
        state_info = parent_tree_node.next_state_info

        # 对方行为的预测方式为，使用自己的模型，预测对方的行为（需要翻转输入）。这里有个限制条件就是双方的阵容（不管1v1还是5v5），都必须是一样的
        _, explorer_ratio, action_ratios_masked = line_trainer.get_action(state_info, hero_name, rival_hero_name)
        _, rival_explorer_ratio, rival_action_ratios_masked = line_trainer.get_action(state_info, rival_hero_name, hero_name)

        # 选择n个最高优先级的行为
        tree_nodes = TreeSearch.select_top_n_actions(parent_tree_node, action_ratios_masked, hero_name, rival_hero_name, False, 3)
        rival_tree_nodes = TreeSearch.select_top_n_actions(parent_tree_node, rival_action_ratios_masked, rival_hero_name, hero_name, True, 3)

        # 选择下一层的分支
        # 这里首先实现一个最简单的方案，一一合并
        leaves


    @staticmethod
    def select_top_n_actions(parent_tree_node, acts, hero_name, rival_hero_name, revert, n):
        tree_nodes = []
        state_info = parent_tree_node.next_state_info
        hero_info = state_info.get_hero(hero_name)
        for i in range(n):
            maxQ = max(acts)
            selected = acts.index(maxQ)

            if ratio < len(acts):
                ratio = acts[selected]
                action = LineModel.get_action(selected, state_info, hero_info, hero_name, rival_hero_name, revert)
                tree_node = TreeNode(parent_tree_node)
                tree_node.set_hero_action(action, ratio)
                tree_nodes.append(tree_node)
        return tree_nodes

    @staticmethod
    def gen_leaves(state_info, tree_nodes, rival_tree_nodes):
        # 最简单的方式，一一合并
        leaf_nodes = []
        for i in range(len(tree_nodes)):
            node_i = tree_nodes[i]
            for j in range(len(rival_tree_nodes)):
                node_j = rival_tree_nodes[j]
                leaf_node = TreeNode(state_info, node_i.hero_action, node_i.weight)
                leaf_node.rival_hero_action = node_j.hero_action
                leaf_node.rival_weight = node_j.weight
                leaf_nodes.append(leaf_node)
        return leaf_nodes
