from train.linemodel import LineModel
from util.stateutil import StateUtil

if __name__ == "__main__":
    path = "/Users/sky4star/Github/zy2go/battle_logs/autobattle2.log"
    file = open(path, "r")
    model1 = LineModel(240, 48)
    lines = file.readlines()
    prestateinfo=None
    for line in lines:

        stateinfo=StateUtil.parse_state_log(line)
        if prestateinfo==None:
            {}
            #model1.remember(stateinfo)
        else:
            stateinfo=StateUtil.update_state_log(prestateinfo,stateinfo)
            #model1.remeber(stateinfo)
        prestateinfo=stateinfo
        action=model1.get_action(stateinfo, '27', '28')
        action_str = StateUtil.build_command(action)
        print(action)
