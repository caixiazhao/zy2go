from src.util.replayer import Replayer as rp
from src.util.stateutil import StateUtil
from util.jsonencoder import ComplexEncoder
import json as JSON
if __name__ == "__main__":
    path = "C:/Users/Administrator/Desktop/zy2go/battle_logs/forguessAction.log"
    #path = "/Users/sky4star/Github/zy2go/battle_logs/autobattle3.log"
    #todo: change the path
    file = open(path, "r")
    lines = file.readlines()

    # for line in lines:
    #     bd_json = json.loads(line)
    #     battle_detail = BattleRoundDetail.decode(bd_json)
    #     model.remember(battle_detail)
    state_logs = []
    prev_state = None
    #replayer = Replayer()

    #model = LineModel(240,48)
    #model.load('C:/Users/Administrator/Desktop/zy2go/src/server/line_model_.model')
    # model.load('/Users/sky4star/Github/zy2go/src/server/line_model_2017-08-07 17:06:40.404176.model')

   #line_trainer = LineTrainer()
    for line in lines:
        if prev_state is not None and int(prev_state.tick) > 173504:
            i = 1

        cur_state = StateUtil.parse_state_log(line)

        if cur_state.tick == StateUtil.TICK_PER_STATE:
            print("clear")
            prev_state = None
        # elif prev_state is not None and prev_state.tick + StateUtil.TICK_PER_STATE > cur_state.tick:
        #     print ("clear")
        #     prev_state = None

        state_info = StateUtil.update_state_log(prev_state, cur_state)
        if prev_state != None:
             player_action=rp.guess_player_action(prev_state,state_info,"27")
             action_str = StateUtil.build_command(player_action)
             print(action_str)
             prev_state.actions.append(player_action)


        state_logs.append(state_info)

        #rsp_str = line_trainer.build_response(state_info, prev_state, model)
        #print(rsp_str)

        state_json = JSON.dumps(state_info,cls=ComplexEncoder)
        print(state_json)
        print(state_info.tick)

        prev_state = state_info

    # model.save('line_model_' + str(datetime.now()).replace(' ', '') + '.model')
    print(len(state_logs))