class StrategyRecords:
    def __init__(self, battleid, strategy_lists):
        self.battleid = battleid
        self.strategy_lists = strategy_lists

    def find_hero_info(self, hero_name):
        for hs in self.strategy_lists:
            if hs.hero_name == hero_name:
                return hs
        return None

    def add_hero_action(self, hero_action):
        for hs in self.strategy_lists:
            if hs.hero_name == hero_action.hero_name:
                hs.strategy_list.append(hero_action)
