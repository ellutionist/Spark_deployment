CURDIR=`dirname $0`
cd $CURDIR
pid=$(cat ./logs/pid)
kill -SIGTERM $pid
