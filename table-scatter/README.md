# Table Scatter
If a TiDB table has too many adjacent region leaders concentrating on a TiKV node, this tool helps scatter those region leaders.

## How it works
The script `table-scatter.py` gets all regions of the target table, picks adjacent region leaders in a specified TiKV store id, and then generates `pd-ctl` commands to help scatter those adjacent region leaders. The generated commands are saved in the `command.sh` file. You need to execute this file to add `scatter-range` schedulers to PD.

Besides, the script `table-scatter.py` also generates a `distribution.txt` file consisting of two columns `REGION_ID` and `LEADER_STORE_ID`. Where `LEADER_STORE_ID` is the TiKV store id in which the region leader stays. You can open this file and check the distribution of regions of the TiDB table.

## Usage
```bash
# Login the control node
$(fop login)

# Create a ssh tunnel to a TiDB server
screen -S tidb-ssh-tunnel
ssh -L 10080:localhost:10080 <TIDB_IP_ADDR>

# Set PD_ADDR environment variable
export PD_ADDR=<PD_IP_ADDR>:2379

# Generate scatter-range schedulers
python3 table-scatter.py --database <DB_NAME> --table <TABLE_NAME> --store-id <STORE_ID>

# If total generated schedulers are too large (greater than 5),
# you should adjust REGION_ADJACENT_SIZE and then re-execute table-scatter.py with --file option
export REGION_ADJACENT_SIZE=10 # or 15 or 20 or 25 ...
python3 table-scatter.py --file=<DB_NAME>-<TABLE_NAME>.json

# Scatter table
./command.sh
```

# Credits
Great thanks to https://github.com/niezefeng for telling me the main idea!