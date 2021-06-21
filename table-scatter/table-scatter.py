#!/usr/bin/env python3
#!coding:utf-8

import argparse
import subprocess
import json
import os, sys, stat
import requests

def parse_args():
    parser = argparse.ArgumentParser(description="Show leader distribution of a TiDB table.")
    parser.add_argument("--host", dest="host", help="tidb-server address, default: 127.0.0.1", default="127.0.0.1")
    parser.add_argument("--port", dest="port", help="tidb-server status port, default: 10080", default="10080")
    parser.add_argument("--database", help="database name")
    parser.add_argument("--table",    help="table name")
    parser.add_argument("--file",     help="The table regions JSON file")
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    if args.file:
        region_info = json.load(open(args.file))
    else:
        tidb_http_API = "http://{}:{}/tables/{}/{}/regions".format(args.host, args.port, args.database, args.table)
        print(tidb_http_API)
        response = requests.get(tidb_http_API)
        region_info = response.json()
        fdw = open(f"{args.database}-{args.table}.json", "w")
        fdw.write(json.dumps(region_info, indent=2))
        fdw.close()

    # Find target store
    target_store_id = find_target_store(region_info["record_regions"])
    print(f"Target store id: {target_store_id}")


    # Parse regions
    parse_regions(target_store_id, region_info["record_regions"])

def find_target_store(regions):
    stores = {}
    for region in regions:
        stores.setdefault(region["leader"]["store_id"], []).append(region["leader"]["id"])

    sorted_stores = sorted(stores.items(), key=lambda item: len(item[1]), reverse=True)

    for store in sorted_stores:
        percent = 100 * len(store[1]) / len(regions)
        store_id_str = f"store-{store[0]}"
        print(f"{store_id_str:>20}: {len(store[1])} ({round(percent, 2)} %)")

    return sorted_stores[0][0]

def parse_regions(target_store_id, regions):
    idx = 0
    store_id_list = []
    region_id_list = []
    f = open("./command.sh", 'w+')
    os.chmod("./command.sh", stat.S_IRWXU|stat.S_IRGRP|stat.S_IROTH)
    for region in regions:
        if region["leader"]["store_id"] != None:
            if len(store_id_list) == 5:
                start_key, end_key = get_start_end_keys(region_id_list[0], region_id_list[-1])
                if start_key and end_key:
                    f.write(f"pd-ctl scheduler add scatter-range --format=hex {start_key} {end_key} {target_store_id}-{region_id_list[0]}-{region_id_list[-1]}\n")
         
                store_id_list.clear()
                region_id_list.clear()
                idx += 1
            store_id = region["leader"]["store_id"]
            region_id = region["region_id"]
            if (store_id == target_store_id):
                store_id_list.append(store_id)
                region_id_list.append(region_id)                
            else:
                store_id_list.clear()
                region_id_list.clear()


def get_start_end_keys(start_region_id, end_region_id):
    pd_base_uri = f"http://{os.environ.get('PD_ADDR', '127.0.0.1:2379')}/pd/api/v1/region/id"

    start_key = None
    end_key = None
    print(f"{pd_base_uri}/{start_region_id}")
    response = requests.get(f"{pd_base_uri}/{start_region_id}")
    if response.ok:
        start_key = response.json()["start_key"]
    response = requests.get(f"{pd_base_uri}/{end_region_id}")
    if response.ok:
        end_key = response.json()["end_key"]

    return start_key, end_key


if __name__ == "__main__":
    main()
