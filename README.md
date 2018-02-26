source ai-test-env/bin/activate
python3 src/setup.py install


bash a.sh

nohup ai-test-env/bin/python3 -u zy2/src/server/trainer.py &> train.log &
nohup ai-test-env/bin/python3 -u zy2/src/server/gateway.py &> gateway.log &
nohup ai-test-env/bin/python3 -u zy2/src/server/gamer.py 0 &> http.log &

for ((i=1;i<=7;i++))
do
    ai-test-env/bin/python3 -u zy2/src/server/gamer.py $i &> http1.log &
done
 
