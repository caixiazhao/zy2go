# -*- coding: utf8 -*-

# 根据当前状态，英雄的选择，英雄对对方行为的猜测，
# 根据类似蒙特卡洛树搜索的方式，
# 预测后续短时间内双方的状态变化，评估相应的分数，
# 从而选择出英雄当前最应该选择的行为
from engine.playengine import PlayEngine
from model.cmdaction import CmdAction
from train.linemodel import LineModel
from treesearch.stateevaluator import StateEvaluator
from treesearch.treenode import TreeNode

#TODO 考虑剪枝
class TreeSearch:

    # 根据状态信息，根据英雄行为选择，得到下一刻的状态，和当期每个行为的得分
    @staticmethod
    def choose_action(state_info, hero_name, rival_hero_name, line_trainer, cal_level=3):
        root = TreeNode(None, None, None, None)
        root.set_next_state_info(state_info)

        second_layer = TreeSearch.build_layer([root], hero_name, rival_hero_name, line_trainer)
        if isinstance(second_layer, CmdAction):
            return second_layer
        third_layer = TreeSearch.build_layer(second_layer, hero_name, rival_hero_name, line_trainer)
        if isinstance(third_layer, CmdAction):
            return third_layer

        # 更新分数，选择得分最高的行为
        TreeSearch.update_scores(root)
        max_leaf = None
        for leaf in root.leaves:
            if max_leaf is None or max_leaf.score < leaf.score:
                max_leaf = leaf
        return leaf

    # 为了提高模型计算效率，逐层计算
    # 所以需要拿到当前层所有叶子节点的状态，统一去计算后续行为，逐个叶子节点的挑选
    @staticmethod
    def build_layer(parent_tree_nodes, hero_name, rival_hero_name, line_trainer):
        # 针对每个父节点，同时计算自身行为，猜测对方行为
        state_infos = [pt.next_state_info for pt in parent_tree_nodes]
        masked_actions_list, vpreds = line_trainer.get_actions(state_infos, hero_name, rival_hero_name)

        # 特殊情况，返回了一个训练完成的信号
        if isinstance(masked_actions_list, CmdAction):
            return masked_actions_list

        # 将结果添加到各个叶子节点上
        all_leaves = []
        for i in range(len(parent_tree_nodes)):
            parent_node = parent_tree_nodes[i]
            state_info = parent_node.next_state_info
            action_ratios_masked = masked_actions_list[i*2]
            rival_action_ratios_masked = masked_actions_list[i*2+1]

            # 选择n个最高优先级的行为
            actions = TreeSearch.select_top_n_actions(action_ratios_masked, state_info, hero_name, rival_hero_name, 3)
            rival_actions = TreeSearch.select_top_n_actions(rival_action_ratios_masked, state_info, rival_hero_name, hero_name, 3)

            # 选择下一层的分支
            # 这里首先实现一个最简单的方案，一一合并
            leaves = TreeSearch.gen_leaves(parent_node, state_info, actions, rival_actions)
            all_leaves.append(leaves)

        return all_leaves

    @staticmethod
    def select_top_n_actions(acts, state_info, hero_name, rival_hero_name, n):
        hero_info = state_info.get_hero(hero_name)
        results = []
        for i in range(n):
            maxQ = max(acts)
            selected = acts.index(maxQ)

            if maxQ > -1:
                ratio = acts[selected]
                action = LineModel.get_action(selected, state_info, hero_info, hero_name, rival_hero_name)
                results.append(action)
        return results

    @staticmethod
    def gen_leaves(parent_tree_node, state_info, actions, rival_actions):
        # 最简单的方式，一一合并
        leaf_nodes = []
        for i in range(len(actions)):
            action = actions[i]
            for j in range(len(rival_actions)):
                rival_action = rival_actions[j]
                leaf_node = TreeNode(state_info, action, rival_action, None)

                # 计算后续状态
                next_state_info = PlayEngine.play_step(leaf_node.state_info, leaf_node.get_names(), leaf_node.get_actions())
                leaf_node.set_next_state_info(next_state_info)
                leaf_nodes.append(leaf_node)

        # 更新父节点的叶子
        parent_tree_node.leaves = leaf_nodes

        return leaf_nodes

    # 自底向上的更新所有分数。更新规则为，叶子节点的均分为自己的分数
    @staticmethod
    def update_scores(parent):
        if parent.leaves is not None:
            for leaf in parent.leaves:
                TreeSearch.update_scores(leaf)
            parent.score = sum([l.score for l in parent.leaves]) / len(parent.leaves)

        else:
            parent.cal_score()
