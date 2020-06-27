SHELL_FOLDER=$(cd "$(dirname "$0")";pwd)
script_path=$SHELL_FOLDER/../scripts/stop_monitor.py

export PYTHONPATH=$PYTHONPATH:$SHELL_FOLDER/..
cd $SHELL_FOLDER/../ && python3 $script_path