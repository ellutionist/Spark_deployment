stop-port-forward.sh

cat ./conf/port-map | while read line
do
	array=($line)
	port=${array[0]}
	addr=${array[1]}
	echo $port

  # remove the known host
  ssh-keygen -R [localhost]:$port
	ssh -Nf -L $port:localhost:22 -i ./keys/spark spark@$addr
done
