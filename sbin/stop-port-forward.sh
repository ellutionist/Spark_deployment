ps aux | grep 'ssh -Nf -L' | while read line
do
  array=($line)
  pid=${array[1]}
  kill -9 $pid
done