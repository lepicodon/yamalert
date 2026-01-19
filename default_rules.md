# Default Prometheus Alert Rules - Comprehensive Guide

This document provides a complete reference for all default alert rules included in the YamAlert rule repository. Each rule is designed to monitor critical infrastructure components and provide actionable alerts with platform-specific remediation guidance.

## Table of Contents

- [Telegraf Job Rules](#telegraf-job-rules)
- [Ping Job Rules](#ping-job-rules)
- [VMware Job Rules](#vmware-job-rules)
- [SSL Certificate Rules](#ssl-certificate-rules)

---

## Telegraf Job Rules

Telegraf is a metrics collection agent. These rules monitor host-level system metrics collected by Telegraf.

### 1. Telegraf Host Up/Down

**Purpose:** Detect when a Telegraf agent stops reporting metrics

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `TelegrafHostDown` | Critical | `up{job="telegraf"} == 0` | 2 minutes |

**Playbooks:**
- **Linux:** Check service status, review logs (`systemctl status telegraf`, `journalctl -u telegraf -n 50`)
- **Windows:** Check service, review event logs (`Get-Service telegraf`, `Get-EventLog -LogName Application -Source telegraf -Newest 50`)

---

### 2. Telegraf CPU High

**Purpose:** Monitor CPU utilization and alert on sustained high usage

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `CPUHigh` | Warning | CPU > 80% | 5 minutes |
| `CPUCritical` | Critical | CPU > 95% | 2 minutes |

**Calculation:** `100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`

**Playbooks:**
- **Linux:** Check top processes, system load, CPU cores (`top -b -n1`, `uptime`, `nproc`)
- **Windows:** Check processes, load percentage (`Get-Process | Sort-Object CPU -Descending | Select-Object -First 10`)

---

### 3. Telegraf Memory High

**Purpose:** Monitor memory consumption and detect memory pressure

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `MemoryHigh` | Warning | Memory > 85% | 5 minutes |
| `MemoryCritical` | Critical | Memory > 95% | 2 minutes |

**Calculation:** `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`

**Playbooks:**
- **Linux:** Check memory usage, swap, top memory consumers (`free -h`, `swapon --show`, `top -b -n1`)
- **Windows:** Check memory configuration and top processes (`Get-WmiObject win32_logicalmemoryconfigurations`, `Get-Process | Sort-Object WS -Descending`)

---

### 4. Telegraf Disk Space Low

**Purpose:** Alert when filesystem usage approaches capacity

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `DiskSpaceWarning` | Warning | Disk > 85% | 5 minutes |
| `DiskSpaceCritical` | Critical | Disk > 95% | 2 minutes |

**Calculation:** `(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100`

**Playbooks:**
- **Linux:** Check disk usage, inode usage, largest directories (`df -h`, `df -i`, `du -sh /*`)
- **Windows:** Check volumes, largest directories (`Get-Volume`, `Get-ChildItem C:\ -Recurse | Sort-Object Length -Descending`)

---

### 5. Telegraf Disk Inodes Low

**Purpose:** Monitor inode exhaustion which can prevent file creation even with free space

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `DiskInodesWarning` | Warning | Inodes > 85% | 5 minutes |
| `DiskInodesCritical` | Critical | Inodes > 95% | 2 minutes |

**Calculation:** `(1 - (node_filesystem_files_free / node_filesystem_files)) * 100`

**Playbooks:**
- **Linux:** Check inode usage, find directories with many files, clean up (`df -i`, `du --inodes -d 3 / | sort -nr`)
- **Windows:** N/A - Inode monitoring is Linux/Unix specific

---

### 6. Telegraf Disk Read-Only

**Purpose:** Detect filesystems remounted read-only due to errors

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `FilesystemReadOnly` | Critical | `node_filesystem_readonly == 1` | 1 minute |

**Note:** Excludes tmpfs and fuse filesystems

**Playbooks:**
- **Linux:** Check filesystem errors, mount status, disk health, attempt remount (`dmesg | tail -50`, `smartctl -a`)
- **Windows:** Check event logs, run disk check (`Get-EventLog -LogName System -Source Disk`, `chkdsk`)

---

### 7. Telegraf Network Interface Down

**Purpose:** Monitor network interface status and packet errors

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `NetworkInterfaceDown` | Critical | `node_network_up == 0` | 2 minutes |
| `NetworkErrorsHigh` | Warning | Errors > 10/sec | 5 minutes |

**Note:** Excludes loopback interface

**Playbooks:**
- **Linux:** Check interfaces, status, errors, network stack (`ip link show`, `ethtool`, `cat /proc/net/dev`)
- **Windows:** Check adapters, statistics (`Get-NetAdapter`, `Get-NetAdapterStatistics`, `netstat -e`)

---

### 8. Telegraf Network Bandwidth High

**Purpose:** Alert on sustained high network throughput

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `NetworkBandwidthHigh` | Warning | Bandwidth > 100 MB/s | 10 minutes |

**Calculation:** `(rate(node_network_receive_bytes_total[5m]) + rate(node_network_transmit_bytes_total[5m])) / 1024 / 1024`

**Playbooks:**
- **Linux:** Check bandwidth, connections, top users (`iftop`, `ss -tunap`, `nethogs`)
- **Windows:** Check bandwidth counters, connections (`Get-Counter '\\Network Interface(*)\\Bytes Total/sec'`)

---

### 9. Telegraf Network Packet Loss

**Purpose:** Monitor packet drops indicating network issues

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `NetworkPacketDrops` | Warning | Drops > 100/sec | 5 minutes |

**Calculation:** `rate(node_network_receive_drop_total[5m]) + rate(node_network_transmit_drop_total[5m])`

**Playbooks:**
- **Linux:** Check drops, buffer settings, errors (`ip -s link show`, `ethtool -g`, `dmesg`)
- **Windows:** Check adapter statistics (`Get-NetAdapterStatistics`, `netstat -e`)

---

### 10. Telegraf Host Uptime Low

**Purpose:** Alert on recent host reboots

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `HostRecentlyRebooted` | Info | Uptime < 1 hour | Immediate |

**Calculation:** `node_boot_time_seconds > (time() - 3600)`

**Playbooks:**
- **Linux:** Check uptime, last reboot, recent logs (`uptime`, `last reboot`, `journalctl --since '1 hour ago'`)
- **Windows:** Check uptime, system events (`systeminfo | find 'System Boot Time'`, `Get-EventLog -LogName System -InstanceId 6005`)

---

### 11. Telegraf Load Average High

**Purpose:** Track system saturation relative to CPU count

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `LoadAverageHigh` | Warning | Load > 2x CPUs | 10 minutes |
| `LoadAverageCritical` | Critical | Load > 4x CPUs | 5 minutes |

**Calculation:** `node_load15 / count(node_cpu_seconds_total{mode="idle"}) without (cpu, mode)`

**Playbooks:**
- **Linux:** Check load, processes, I/O wait, zombies (`uptime`, `ps aux`, `iostat -x 1 5`)
- **Windows:** Check CPU queue, processes (`Get-Counter '\\System\\Processor Queue Length'`)

---

### 12. Telegraf Swap Usage High

**Purpose:** Monitor swap usage indicating memory pressure

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `SwapUsageHigh` | Warning | Swap > 50% | 5 minutes |

**Calculation:** `(1 - (node_memory_SwapFree_bytes / node_memory_SwapTotal_bytes)) * 100`

**Playbooks:**
- **Linux:** Check swap usage, identify swapped processes, check OOM (`free -h`, `/proc/*/status`, `dmesg`)
- **Windows:** Check page file usage (`Get-WmiObject Win32_PageFileUsage`)

---

### 13. Telegraf Disk I/O High

**Purpose:** Detect sustained disk I/O saturation

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `DiskIOSaturated` | Warning | I/O > 80% | 10 minutes |

**Calculation:** `rate(node_disk_io_time_seconds_total[5m]) * 100`

**Playbooks:**
- **Linux:** Check I/O stats, processes, disk stats (`iostat -x 1 5`, `iotop -o -b -n 3`)
- **Windows:** Check disk performance, processes (`Get-Counter '\\PhysicalDisk(*)\\% Disk Time'`)

---

### 14. Telegraf Time Drift

**Purpose:** Detect NTP synchronization issues

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `SystemClockDrift` | Warning | Offset > 0.1 seconds | 5 minutes |

**Calculation:** `abs(node_timex_offset_seconds)`

**Playbooks:**
- **Linux:** Check NTP status, sync time, force sync (`timedatectl status`, `ntpq -p`, `ntpdate -u pool.ntp.org`)
- **Windows:** Check time service, resync (`w32tm /query /status`, `w32tm /resync`)

---

### 15. Telegraf Context Switches High

**Purpose:** Identify CPU contention through high context switching

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `ContextSwitchesHigh` | Warning | Switches > 10,000/sec | 10 minutes |

**Calculation:** `rate(node_context_switches_total[5m])`

**Playbooks:**
- **Linux:** Check context switches, processes, interrupts (`vmstat 1 5`, `ps -eo pid,tid,class,rtprio`, `cat /proc/interrupts`)
- **Windows:** Check context switches, processes (`Get-Counter '\\System\\Context Switches/sec'`)

---

## Ping Job Rules

Ping monitoring tracks network connectivity and latency to critical endpoints.

### 16. Ping Host Down

**Purpose:** Detect unreachable hosts via ICMP ping

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `PingHostDown` | Critical | `probe_success == 0` | 2 minutes |

**Playbooks:**
- **Linux:** Ping host, trace route, check firewall (`ping -c 5`, `traceroute`, `iptables -L -n`)
- **Windows:** Ping host, trace route, check firewall (`ping`, `tracert`, `netsh advfirewall show allprofiles`)

---

### 17. Ping Latency High

**Purpose:** Monitor network latency for performance degradation

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `PingLatencyWarning` | Warning | Latency > 100ms | 5 minutes |
| `PingLatencyCritical` | Critical | Latency > 500ms | 2 minutes |

**Metric:** `probe_duration_seconds`

**Playbooks:**
- **Linux:** Ping with timing, check route latency, network stats (`ping -c 10`, `traceroute -w 1`, `ss -i`)
- **Windows:** Ping with timing, check network stats (`ping -n 10`, `netstat -ano`)

---

### 18. Ping Packet Loss

**Purpose:** Monitor intermittent connectivity issues

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `PingPacketLoss` | Warning | Success rate < 95% | 5 minutes |

**Calculation:** `avg_over_time(probe_success{job="ping"}[5m])`

**Playbooks:**
- **Linux:** Ping with statistics, check route, MTU (`ping -c 100`, `traceroute`, `ip link show`)
- **Windows:** Ping with statistics, check route (`ping -n 100`, `route print`)

---

## VMware Job Rules

VMware monitoring tracks ESXi hosts, virtual machines, and vCenter infrastructure.

### 19. VMware VM CPU High

**Purpose:** Monitor virtual machine CPU utilization

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `VMCPUHigh` | Warning | CPU > 80% | 5 minutes |
| `VMCPUCritical` | Critical | CPU > 95% | 2 minutes |

**Metric:** `vmware_vm_cpu_usage_percent`

**Playbooks:**
- **Linux:** SSH to VM, check CPU usage (`ssh`, `top -b -n1`)
- **Windows:** RDP to VM, check processes (`Get-Process | Sort-Object CPU -Descending`)

---

### 20. VMware VM Memory High

**Purpose:** Monitor virtual machine memory utilization

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `VMMemoryHigh` | Warning | Memory > 85% | 5 minutes |
| `VMMemoryCritical` | Critical | Memory > 95% | 2 minutes |

**Metric:** `vmware_vm_memory_usage_percent`

**Playbooks:**
- **Linux:** SSH to VM, check memory, top users (`ssh`, `free -h`, `top -b -n1`)
- **Windows:** RDP to VM, check memory and processes (`Get-WmiObject win32_logicalmemoryconfigurations`)

---

### 21. VMware VM Disk Latency High

**Purpose:** Monitor VM storage performance

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `VMDiskLatencyHigh` | Warning | Latency > 50ms | 5 minutes |

**Metric:** `vmware_vm_disk_latency_average_milliseconds`

**Playbooks:**
- **Linux:** SSH to ESX host, check storage latency with esxtop
- **Windows:** Use vSphere Client, check VM performance tab, datastore latency

---

### 22. VMware VM Network Dropped Packets

**Purpose:** Detect virtual network issues

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `VMNetworkDroppedPackets` | Warning | Drops > 10/sec | 5 minutes |

**Calculation:** `rate(vmware_vm_network_packets_dropped_total[5m])`

**Playbooks:**
- **Linux:** Check vSwitch, port groups, physical adapters (`esxcli network vswitch standard list`)
- **Windows:** Use vSphere Client, check virtual switch configuration, port groups, NIC status

---

### 23. VMware Snapshot Age High

**Purpose:** Alert on old/forgotten VM snapshots

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `VMSnapshotOld` | Warning | Age > 7 days | 1 hour |
| `VMSnapshotVeryOld` | Critical | Age > 30 days | 1 hour |

**Calculation:** `vmware_vm_snapshot_age_seconds > (7 or 30) * 24 * 3600`

**Playbooks:**
- **Linux:** SSH to vCenter, list and remove snapshots (`vim-cmd vmsvc/snapshot.get`, `vim-cmd vmsvc/snapshot.remove`)
- **Windows:** Use vSphere Client, navigate to VM > Snapshots, review and delete old snapshots

---

### 24. VMware Host CPU High

**Purpose:** Monitor ESXi host CPU utilization

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `HostCPUHigh` | Warning | CPU > 80% | 5 minutes |
| `HostCPUCritical` | Critical | CPU > 90% | 2 minutes |

**Metric:** `vmware_host_cpu_usage_percent`

**Playbooks:**
- **Linux:** SSH to ESX, check CPU, processes (`ssh root@host`, `esxcli hardware cpu global get`, `esxtop`)
- **Windows:** N/A - ESX hosts are Linux-based

---

### 25. VMware Host Memory High

**Purpose:** Monitor ESXi host memory utilization

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `HostMemoryHigh` | Warning | Memory > 85% | 5 minutes |
| `HostMemoryCritical` | Critical | Memory > 95% | 2 minutes |

**Metric:** `vmware_host_memory_usage_percent`

**Playbooks:**
- **Linux:** SSH to ESX, check memory (`ssh root@host`, `esxcli hardware memory get`, `esxtop`)
- **Windows:** N/A - ESX hosts are Linux-based

---

### 26. VMware Datastore Space Low

**Purpose:** Monitor datastore capacity

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `DatastoreWarning` | Warning | Usage > 85% | 5 minutes |
| `DatastoreCritical` | Critical | Usage > 95% | 2 minutes |

**Metric:** `vmware_datastore_capacity_percent`

**Playbooks:**
- **Linux:** SSH to vCenter, check datastores (`esxcli storage filesystem list`, `vim-cmd hostsvc/datastore/info`)
- **Windows:** Use vSphere Client, navigate to Storage > Datastores, check free space

---

### 27. VMware Host Connection State

**Purpose:** Detect ESX hosts disconnected from vCenter

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `HostDisconnected` | Critical | Connection state = disconnected | 2 minutes |

**Metric:** `vmware_host_connection_state{state="disconnected"}`

**Playbooks:**
- **Linux:** SSH to ESX, check services, restart management (`/etc/init.d/hostd status`, `vim-cmd hostsvc/reconnect`)
- **Windows:** Use vSphere Client, right-click host > Connection > Reconnect, verify network

---

### 28. VMware VM Power State Unexpected

**Purpose:** Alert when critical VMs are powered off

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `VMPoweredOff` | Critical | Production/critical VM powered off | 5 minutes |

**Note:** Targets VMs with names containing "prod" or "critical"

**Playbooks:**
- **Linux:** Check VM state, power on (`vim-cmd vmsvc/power.getstate`, `vim-cmd vmsvc/power.on`)
- **Windows:** Use vSphere Client, check VM events and alarms, power on VM

---

## SSL Certificate Rules

SSL monitoring tracks certificate expiration and validates HTTPS endpoints.

### 29. SSL Certificate Expiring Soon (30 days)

**Purpose:** Early warning for certificate renewal planning

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `SSLCertExpiring30d` | Info | Expires in < 30 days | 6 hours |

**Calculation:** `probe_ssl_earliest_cert_expiry - time() < 30 * 24 * 3600`

**Playbooks:**
- **Linux:** Check certificate, prepare renewal, test (`openssl s_client -connect`, `certbot certificates`, `certbot renew --dry-run`)
- **Windows:** Check certificate, request new cert (`certlm.msc`, use ACME client)

---

### 30. SSL Certificate Expiring Soon (15 days)

**Purpose:** Alert when certificate expires within 15 days

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `SSLCertExpiring15d` | Warning | Expires in < 15 days | 1 hour |

**Calculation:** `probe_ssl_earliest_cert_expiry - time() < 15 * 24 * 3600`

**Playbooks:**
- **Linux:** Check certificate expiry, verify renewal process (`openssl x509 -in cert -noout -dates`)
- **Windows:** Check certificate expiry, find expiring certs (`Get-ChildItem Cert:\\LocalMachine\\My | Where-Object { $_.NotAfter -lt (Get-Date).AddDays(15) }`)

---

### 31. SSL Certificate Expiring Soon (3 days)

**Purpose:** Critical warning for immediate certificate renewal

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `SSLCertExpiring3d` | Critical | Expires in < 3 days | 30 minutes |

**Calculation:** `probe_ssl_earliest_cert_expiry - time() < 3 * 24 * 3600`

**Playbooks:**
- **Linux:** URGENT - Renew immediately, restart services (`certbot renew --force-renewal`, `systemctl restart nginx/apache2`)
- **Windows:** URGENT - Renew certificate immediately, import and bind (`certlm.msc`, `iisreset`)

---

### 32. SSL Certificate Expired

**Purpose:** Alert when certificate has already expired

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `SSLCertExpired` | Critical | Certificate expired | Immediate |

**Calculation:** `probe_ssl_earliest_cert_expiry - time() <= 0`

**Playbooks:**
- **Linux:** Renew certificate, check dates, restart service (`certbot renew`, `openssl x509 -in cert -noout -dates`, `systemctl restart`)
- **Windows:** Renew certificate, replace, restart IIS (`certlm.msc`, `iisreset`)

---

### 33. SSL Probe Failed

**Purpose:** Alert when unable to retrieve SSL certificate information

#### Rules

| Alert Name | Severity | Threshold | Duration |
|------------|----------|-----------|----------|
| `SSLProbeFailed` | Warning | `probe_success == 0` | 5 minutes |

**Playbooks:**
- **Linux:** Test connection, check DNS, firewall, service (`openssl s_client -connect`, `dig`, `telnet`, `systemctl status`)
- **Windows:** Test connection, check DNS, firewall, IIS (`Test-NetConnection -Port 443`, `nslookup`, `Get-Website`)

---

## Alert Type Definitions

### Email
Standard notification rules designed for Alertmanager's email integration. Suitable for general awareness and non-urgent alerts.

### Interlink
Rules optimized for Interlink integration with automated ServiceNow incident creation or enhanced email notifications. Ideal for alerts requiring ticket tracking.

### EDA (Event-Driven Ansible)
Rules optimized for Event-Driven Ansible automation. These alerts can trigger automated remediation playbooks for self-healing infrastructure.

---

## Severity Levels

- **Info:** Informational alerts for awareness, no immediate action required
- **Warning:** Potential issues that should be investigated but are not yet critical
- **Critical:** Serious issues requiring immediate attention and remediation

---

## Best Practices

1. **Threshold Tuning:** Adjust thresholds based on your environment's baseline performance
2. **Alert Fatigue:** Start with higher thresholds and gradually lower them to reduce noise
3. **Playbook Customization:** Adapt the remediation playbooks to match your infrastructure and processes
4. **Testing:** Validate each rule in a non-production environment before deployment
5. **Documentation:** Keep instance-specific notes for rules you modify

---

**Last Updated:** 2026-01-19  
**Total Rules:** 33  
**Rule Groups:** 28
