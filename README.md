## 训练分离启动方式

首先启动trainer. 然后启动gateway, 最后启动多个gamer

```
  python3 -m server.trainer --g=2010
  python3 -m server.gateway
  python3 -m server.gamer --port=9000 --slot=8 --base=0
  python3 -m server.gamer --port=9001 --slot=8 --base=8
  python3 -m server.gamer --port=9002 --slot=8 --base=16
```

**Note:** 目前端口配置是写死的,不能随意调整.

## 启动方式

```
source ai-test-env/bin/activate
python3 src/setup.py install
nohup ai-test-env/bin/python3 -u zy2/src/server/httpserver.py &> http.log &
```

## 调试的启动方式


```
source ai-test-env/bin/activate
export PYTHONPATH=zy2/src
cd zy2/src
python3 zy2/src/server/httpserver.py
```
建议在`screen`/`tumx`环境下

