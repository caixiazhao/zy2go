import os

DATA_ROOT_PATH = os.path.join(os.environ['HOME'], 'data')

SAVE_BATCH = 10
TRAIN_GAME_BATCH = 60

NAME_MODEL_1 = 'model_1'
NAME_MODEL_2 = 'model_2'

PARAMS = {}

LOG = {
    'LINEMODEL__ACT_0': True,
    'LINEMODEL__ACT_1': True,
    'MANAGER__READ_PROCESS': True,
    'LINEMODE__POLICY_ALL': True,
    'LINETRAINER_PPO': True,

    'LINEMODEL_PPO1__0': True,

    'UTIL__EQUIPUTIL': True,
}

LOG__MANAGER_READ_PROCESSOR = True

PRELOAD_MODEL1_PATH = None
PRELOAD_MODEL2_PATH = None

GAME_WORKERS = 20 # game worker 进程数量
GAME_WORKER_SLOTS = 8 # 每个game worker为几个game.exe提供服务
GAME_BASE_PORT = 9000 # game worker的起始端口
TRAINER_PORT = 8999 #训练worker的端口
