sum=0
nohup ai-test-env/bin/python3 -u zy2/src/server/trainer.py &> /data/train.log &
nohup ai-test-env/bin/python3 -u zy2/src/server/gateway.py &> /data/gateway.log &
nohup ai-test-env/bin/python3 -u zy2/src/server/gamer.py 0 &> /data/http.log &
  
for ((i=1;i<=7;i++))
do  
    ai-test-env/bin/python3 -u zy2/src/server/gamer.py $i &> /data/http1.log &  
done  
echo $sum  
