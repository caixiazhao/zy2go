source ai-test-env/bin/activate
python3 src/setup.py install
nohup ai-test-env/bin/python3 -u zy2/src/server/httpserver.py &> http.log &