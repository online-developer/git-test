#!/bin/bash

export PYTHONIOENCODING=utf8

prog=$(basename $0)
pwd=$(dirname $0)
master="local[1]"
deploy_mode="client"
memory="2g"
prog=${prog%%.*}
packages="com.databricks:spark-csv_2.11:1.5.0"

if [[ -e "$pwd/conf/log4j.properties" ]]; then
   export SPARK_CONF_DIR="$pwd/conf/log4j.properties"
fi

#spark-submit --master $master --deploy-mode $deploy_mode wordcount.py ../data/wordcount.txt 2
spark-submit \
	--packages $packages \
	--master $master \
	--deploy-mode $deploy_mode \
	--executor-memory $memory \
	--name $prog \
	--conf "spark.app.id=$prog" \
	"$@"
