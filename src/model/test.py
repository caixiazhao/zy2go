from src.util.replayer import Replayer as rp
from src.model.linemodel import linemodel
from src.model.line_input import Line_input

if __name__ == "__main__":
    path = "C:/Users/Administrator/Desktop/zy2go/battle_logs/httpd.log"
    file = open(path, "r")
    model1 = linemodel(240,48,'27')
    lines = file.readlines()
    prestateinfo=None
    for line in lines:

        stateinfo=rp.parse_state_log(line)
        if prestateinfo==None:
            {}
            #model1.remember(stateinfo)
        else:
            stateinfo=rp.update_state_log(prestateinfo,stateinfo)
            #model1.remeber(stateinfo)
        prestateinfo=stateinfo
        action=model1.get_action(stateinfo)
        print(action)
