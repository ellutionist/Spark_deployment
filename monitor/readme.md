# Monitor

This is a special module that should be installed on every node of the cluster.

The shell script sbin/start-setup.sh will take the installation job.

If you want to modify the source code, make sure to compress the directory monitor/ into the file lib/monitor.tar.

For example,

    cd Spark_deployment/
    tar -cf lib/monitor.tar monitor/

For more configuration, please refer to

    conf/server.ini