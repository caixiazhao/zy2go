python -u httpserver.py &> httpserver.log &


nohup ai-test-env/bin/python3 -u zy2/src/server/httpserver.py &> /data/http.log &


nohup ai-test-env/bin/python3 -u zy2/src/server/nonblockserver.py 40 &> /data/http.log &

