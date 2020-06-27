SHELL_FOLDER=$(cd "$(dirname "$0")";pwd)
conf_path=$SHELL_FOLDER/../conf/port-map
cat $conf_path | while read line
do
	array=($line)
	port=${array[0]}
	addr=${array[1]}
	inner_addr=${array[2]}
	inner_port=${array[3]}

  # remove the known host
  ssh-keygen -R [localhost]:$port
	ssh -Nf -L $port:$inner_addr:$inner_port $addr
done
ps aux | grep 'ssh -Nf -L'
