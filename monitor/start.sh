CURDIR=`dirname $0`
cd $CURDIR
nohup python3 ./monitor.py $1 >/dev/null 2>&1 &
