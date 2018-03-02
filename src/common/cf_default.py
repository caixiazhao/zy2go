import os

DATA_ROOT_PATH = os.path.join(os.environ['HOME'], 'data')


TRAIN_CPUS = 16

NAME_MODEL_1 = 'model_1'
NAME_MODEL_2 = 'model_2'

PARAMS = {}
GLOBAL = {}

LOG = {
    'LINEMODEL__ACT_0': True,
    'LINEMODEL__ACT_1': True,
    'MANAGER__READ_PROCESS': True,
    'LINEMODE__POLICY_ALL': True,
    'LINETRAINER_PPO': True,

    'LINEMODEL_PPO1__0': True,

    'UTIL__EQUIPUTIL': True,
    'GENERATION_UPDATE': True,
}

LOG__MANAGER_READ_PROCESSOR = True

PRELOAD_MODEL1_PATH = None
PRELOAD_MODEL2_PATH = None

# game worker 进程数量
GAME_WORKERS = 1

# 每个game worker为几个game.exe提供服务
GAME_WORKER_SLOTS = 1

# game worker的起始端口
GAME_BASE_PORT = 9000

# 训练worker的端口
TRAINER_PORT = 8889
GATEWAY_PORT = 8780

# Gamer机器
GAME_WORKER_HOSTS = ['127.0.0.1']

RUN_MODE_GATEWAY = 'gateway'
RUN_MODE_PREDICT = 'predict'
RUN_MODE_TRAIN = 'train'

id1 =0

# ----
def set_worker_name(s):
    if os.environ.get('TMUX') is not None:
        os.system("tmux rename-window '%s'" % s)


def set_run_mode(mode):
    GLOBAL['run_mode'] = mode

def get_run_mode():
    return GLOBAL['run_mode']


def get_total_battle_num():
    return len(GAME_WORKER_HOSTS) * GAME_WORKERS * GAME_WORKER_SLOTS


# ----
REVISION_GAMER = 'r5'
REVISION_GATEWAY = 'r0'
REVISION_TRAINER = 'r2'


