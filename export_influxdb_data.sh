#!/bin/bash

#author: Luc Gerrits

INFLUX_URL=xxxxxxxxx
INFLUX_USER=xxxxxxxxx
INFLUX_PWD=xxxxxxxxx
INFLUX_DB=metrics
DATA_PATH=datas

echo "Start"

rm -rf $DATA_PATH
mkdir -p $DATA_PATH

NOW=$(date +%s%N | cut -b1-13)
START_TS=$1 
END_TS=$2 
GROUP_BY_TIME="10s" #in seconds
timeFilter="time >= ${START_TS}ms and time <= ${END_TS}ms "

#Note:
# Use allways "as mean" alias to make python script later simple to find the data column for each table
#

####
field="sawtooth_validator.chain.ChainController.block_num"
name="block_num_tot"
QUERY="SELECT mean(\"value\") as mean FROM \"$field\" WHERE $timeFilter GROUP BY time($GROUP_BY_TIME) fill(none)" #, \"host\"
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.chain.ChainController.block_num"
name="block_num_rate"
QUERY="SELECT (non_negative_derivative(mean(\"value\"), 10s) /10) as mean FROM \"$field\" WHERE $timeFilter GROUP BY time($GROUP_BY_TIME) fill(none)" #, \"host\"
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.chain.ChainController.committed_transactions_gauge"
name="commits_tot"
QUERY="SELECT mean(\"value\") as mean FROM \"$field\" WHERE $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.chain.ChainController.committed_transactions_gauge"
name="commits_rate"
QUERY="SELECT (non_negative_derivative(mean(\"value\"), 10s) /10) as mean FROM \"$field\" WHERE $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.executor.TransactionExecutorThread.tp_process_response_count"
name="tx_exec_rate"
QUERY="SELECT (moving_average(non_negative_derivative(mean(\"count\"), 10s),2) /10) as mean FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.executor.TransactionExecutorThread.in_process_transactions_count"
name="tx_in_process_rate"
QUERY="SELECT (non_negative_derivative(sum(\"count\"), 10s) /10) as mean FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.publisher.BlockPublisher.pending_batch_gauge"
name="pending_tx_tot"
QUERY="SELECT mean(\"value\") FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.publisher.BlockPublisher.pending_batch_gauge"
name="pending_tx_rate"
QUERY="SELECT (non_negative_derivative(mean(\"value\"), 10s) /10) as mean FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.chain.ChainController.blocks_considered_count"
name="blocks_count"
QUERY="SELECT mean(\"count\") as mean FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.back_pressure_handlers.ClientBatchSubmitBackpressureHandler.backpressure_batches_rejected_gauge"
name="reject_tot"
QUERY="SELECT mean(\"value\") as mean FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.back_pressure_handlers.ClientBatchSubmitBackpressureHandler.backpressure_batches_rejected_gauge"
name="reject_rate"
QUERY="SELECT (non_negative_derivative(sum(\"value\"), 10s) /10) as mean FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_rest_api.post_batches_count"
name="rest_api_batch_rate"
# QUERY="SELECT (non_negative_derivative(sum(\"count\"), 10s) /10) as mean FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
QUERY="SELECT ( non_negative_derivative(moving_average(sum(\"count\"), 10), 10s) /10) as mean FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
#unsure here:
# field="sawtooth_rest_api.post_batches_validator_time"
# name="batches_time"
# QUERY="SELECT (non_negative_derivative(mean(\"sum\"), 10s) /10) as mean FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
# curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.interconnect.Interconnect.send_response_time"
name="msg_sent_rate"
QUERY="SELECT (non_negative_derivative(sum(\"count\"), 10s) /10) as mean FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####
field="sawtooth_validator.interconnect._SendReceive.received_message_count"
name="msg_receive_rate"
QUERY="SELECT (non_negative_derivative(sum(\"count\"), 10s) /10) as mean FROM \"$field\" WHERE  $timeFilter GROUP BY time($GROUP_BY_TIME) fill(null)" #, \"host\"  (\"response_type\" = 'OK') AND
curl -sS --insecure -u $INFLUX_USER:$INFLUX_PWD -XPOST "$INFLUX_URL/query" --data-urlencode "db=$INFLUX_DB" --data-urlencode "q=$QUERY" -H "Accept: application/csv" > "$DATA_PATH/$name.csv"
####

echo "*******"
echo "Done"