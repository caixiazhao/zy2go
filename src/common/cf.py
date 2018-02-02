from common.cf_default import *

# model1_path='/Users/sky4star/Github/zy2go/data/20171218/model_2017-12-14192241.120603/line_model_1_v460/model',
# model2_path='/Users/sky4star/Github/zy2go/data/20171218/model_2017-12-14192241.120603/line_model_2_v460/model',
# model1_path='/Users/sky4star/Github/zy2go/data/20171204/model_2017-12-01163333.956214/line_model_1_v430/model',
# model2_path='/Users/sky4star/Github/zy2go/data/20171204/model_2017-12-01163333.956214/line_model_2_v430/model',
# model1_path='/Users/sky4star/Github/zy2go/data/all_trained/battle_logs/trained/171127/line_model_1_v380/model',
#             '/Users/sky4star/Github/zy2go/data/20171115/model_2017-11-14183346.557007/line_model_1_v730/model',
#             '/Users/sky4star/Github/zy2go/battle_logs/model_2017-11-17123006.954281/line_model_1_v10/model',
# model2_path='/Users/sky4star/Github/zy2go/data/all_trained/battle_logs/trained/171127/line_model_2_v380/model',
#             '/Users/sky4star/Github/zy2go/data/20171121/model_2017-11-20150651.200368/line_model_2_v120/model',


PRELOAD_MODEL_DATA = False
# PRELOAD_MODEL_DATA = True
PRELOAD_MODEL_DATA_PATH = 'battle_logs/model_20180108_223551912926'
PRELOAD_MODEL_VERSION = '7260'

if PRELOAD_MODEL_DATA:
    PRELOAD_MODEL1_PATH = '/Users/Administrator/Desktop/wenjian/line_model_1_v350/model'
    PRELOAD_MODEL2_PATH = '/Users/Administrator/Desktop/wenjian/line_model_2_v400/model'
    # PRELOAD_MODEL1_PATH = os.path.join(DATA_ROOT_PATH,
    #     PRELOAD_MODEL_DATA_PATH, 'line_model_1_v' + PRELOAD_MODEL_VERSION, 'model')
    # PRELOAD_MODEL2_PATH = os.path.join(DATA_ROOT_PATH,
    #     PRELOAD_MODEL_DATA_PATH, 'line_model_2_v' + PRELOAD_MODEL_VERSION, 'model')

# ------
SAVE_BATCH = 10
TRAIN_GAME_BATCH = 6

START = 0
END = 0

generation_id = 0

LOG.update({
    'MANAGER__READ_PROCESS': False,
    'LINEMODEL__ACT_0': False,
    'LINEMODEL__ACT_1': False,
    'LINEMODEL_POLICY_ALL': False,
    'LINETRAINER_PPO': False,

    'LINEMODEL_PPO1__0': False,

    'UTIL__EQUIPUTIL': False,
    'GENERATION_UPDATE': True,
})



