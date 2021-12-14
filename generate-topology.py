import sys
import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--cluster', '-c', required=True, help="The TiDB cluster name")
args = parser.parse_args()
cluster = args.cluster
print(f"Cluster: {cluster}")

pipe = subprocess.Popen(f'fop cluster {cluster} show | grep --color=none "ap-northeast-1" | grep -v aws | sort -V', stdout=subprocess.PIPE, shell=True)
results = pipe.stdout.readlines()
pipe.wait()

def format_tikv_host(ip, az, host, zone):
  h = """  - host: {}
    config:
      server.labels: {{ az: "{}", host: "{}", zone: "{}"}}""".format(ip, az, host, zone)
  return h

drainer_hosts = []
pd_hosts = []
prometheus_hosts = []
pump_hosts = []
tidb_hosts = []
tikv_hosts = {}
tikv_i = {}

for line in results:
  line = line.decode('utf-8')
  if 'Load Balancers:' in line:
    break
  if 'Drainer' in line:
    drainer_hosts.append(line.split()[2])
  if 'PD' in line:
    pd_hosts.append(line.split()[2])
  elif 'Prometheus' in line:
    prometheus_hosts.append(line.split()[2])
  elif 'Pump' in line:
    pump_hosts.append(line.split()[2])
  elif 'TiDB' in line:
    tidb_hosts.append(line.split()[2])
  elif 'TiKV' in line:
    columns = line.split()
    ip = columns[2]
    az = columns[3]
    if az in tikv_i:
      tikv_i[az] += 1
    else:
      tikv_i[az] = 1
    host = f"{az.split('-')[2]}-{tikv_i[az]}"

    if az in tikv_hosts:
      tikv_hosts[az].append({"ip": ip, "host": host})
    else:
      tikv_hosts[az] = []
      tikv_hosts[az].append({"ip": ip, "host": host})


print("pd_servers:")
for h in pd_hosts:
  print(f"  - host: {h}")

print("tidb_servers:")
for h in tidb_hosts:
  print(f"  - host: {h}")

print("tikv_servers:")
az = "ap-northeast-1a"
for h in tikv_hosts[az]:
  print(format_tikv_host(h["ip"], az, h["host"], "zone1"))

az = "ap-northeast-1c"
for i in range(len(tikv_hosts[az])):
  h = tikv_hosts[az][i]
  if i < (len(tikv_hosts[az])//2 + 1):
    print(format_tikv_host(h["ip"], az, h["host"], "zone2"))
  else:
    print(format_tikv_host(h["ip"], az, h["host"], "zone3"))

az = "ap-northeast-1d"
for i in range(len(tikv_hosts[az])):
  h = tikv_hosts[az][i]
  if i < (len(tikv_hosts[az])//2 + 1):
    print(format_tikv_host(h["ip"], az, h["host"], "zone4"))
  else:
    print(format_tikv_host(h["ip"], az, h["host"], "zone5"))

print("pump_servers:")
for h in pump_hosts:
  print(f"  - host: {h}")

print("drainer_servers:")
for h in drainer_hosts:
  print(f"  - host: {h}")

print("monitoring_servers:")
for h in prometheus_hosts:
  print(f"  - host: {h}")
