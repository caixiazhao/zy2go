
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
