from distutils.core import setup

setup(
    name='zy2go',
    version='',
    packages=[
        '', 'common', 'test', 'util', 'model', 'train', 'server', 'baselines', 'baselines.a2c', 'baselines.ddpg',
        'baselines.ppo1', 'baselines.acktr', 'baselines.bench', 'baselines.deepq', 'baselines.deepq.experiments',
        'baselines.deepq.experiments.atari', 'baselines.common', 'baselines.common.vec_env', 'baselines.trpo_mpi',
        'hero_strategy'],
    package_dir={'': 'src'},
    url='',
    license='',
    author='sky4star',
    author_email='',
    description=''
)
