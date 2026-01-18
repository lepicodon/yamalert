# seed_templates.py
"""
Prometheus alert templates with metadata extraction utilities.
Handles template generation and database seeding on first startup.
"""

import yaml
from typing import Dict, Any
from models import Template


# =============================================================================
# METADATA EXTRACTION UTILITIES
# =============================================================================

def get_template_metadata_dict(content: str) -> Dict[str, Any]:
    """
    Extract metadata fields from the first alert rule in template content.
    
    Metadata fields (linux_playbook, windows_playbook, value) are stored
    at the rule level alongside labels and annotations.
    
    Returns:
        Dictionary with keys: linux_playbook, windows_playbook, value
    """
    try:
        doc = yaml.safe_load(content)
        
        if isinstance(doc, dict) and "groups" in doc:
            for group in doc.get("groups", []):
                if isinstance(group, dict):
                    for rule in group.get("rules", []):
                        if isinstance(rule, dict) and "alert" in rule:
                            return {
                                "linux_playbook": rule.get("linux_playbook", ""),
                                "windows_playbook": rule.get("windows_playbook", ""),
                                "value": rule.get("value", ""),
                            }
        
        return {}
    except Exception:
        return {}


# =============================================================================
# TEMPLATE GENERATION HELPERS
# =============================================================================

def _dump_yaml(data):
    """Human‑readable YAML dump."""
    return yaml.dump(data, sort_keys=False, default_flow_style=False)


def _group_rule(name, rules):
    """Wrap a list of rule dicts into a Prometheus rule group."""
    return {
        "groups": [
            {
                "name": name,
                "rules": rules,
            }
        ]
    }


def _alert(name, expr, for_="5m", labels=None, annotations=None, linux_playbook="", windows_playbook="", value=""):
    """Helper to build an alerting rule dict with runbook/playbook info."""
    rule = {
        "alert": name,
        "expr": expr,
        "for": for_,
        "labels": labels or {},
        "annotations": annotations or {},
    }
    
    # Add playbook and value fields if provided
    if linux_playbook:
        rule["linux_playbook"] = linux_playbook
    if windows_playbook:
        rule["windows_playbook"] = windows_playbook
    if value:
        rule["value"] = value
    
    return rule


def _create_template(
    name,
    type_,
    job_category,
    sensor_type,
    description,
    rules,
    group_name="",
):
    """
    Helper to create a template with metadata embedded in the alert rules.
    
    The metadata fields (linux_playbook, windows_playbook, value) are already
    embedded in each rule at the same level as labels and annotations.
    """
    yaml_content = _dump_yaml(_group_rule(group_name, rules))
    
    return Template(
        name=name,
        type=type_,
        job_category=job_category,
        sensor_type=sensor_type,
        description=description,
        content=yaml_content,
    )


def _recording(name, expr, labels=None):
    """Helper to build a recording rule dict."""
    return {
        "record": name,
        "expr": expr,
        "labels": labels or {},
    }


def generate_default_templates():
    """Return a list of Template objects that will be inserted on first run."""

    templates = []

    # ========================================================================
    # 1️⃣  TELEGRAF RULES (Up/Down, CPU, Memory, Disk, Network, Uptime)
    # ========================================================================
    templates.extend(
        [
            # Up/Down Alert
            _create_template(
                name="Telegraf Host Up/Down",
                type_="rule",
                job_category="Telegraf",
                sensor_type="Availability",
                description="Alert when Telegraf agent is down for more than 2 minutes.",
                rules=[
                    _alert(
                        "TelegrafHostDown",
                        'up{job="telegraf"} == 0',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Telegraf agent down on {{ $labels.instance }}",
                            "description": "Telegraf is not reporting metrics from {{ $labels.instance }}.",
                        },
                        linux_playbook="Check service: systemctl status telegraf, Check logs: journalctl -u telegraf -n 50",
                        windows_playbook="Check service: Get-Service telegraf, Check logs: Get-EventLog -LogName Application -Source telegraf -Newest 50",
                        value="{{ $value }}",
                    )
                ],
                group_name="telegraf_updown",
            ),

            # CPU Alert
            _create_template(
                name="Telegraf CPU High",
                type_="rule",
                job_category="Telegraf",
                sensor_type="CPU",
                description="Alert when CPU usage exceeds 80% for 5 minutes.",
                rules=[
                    _alert(
                        "CPUHigh",
                        '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80',
                        for_="5m",
                        labels={"severity": "warning"},
                        annotations={
                            "summary": "High CPU usage on {{ $labels.instance }}",
                            "description": "CPU usage is above 80% (current: {{ $value }}%)",
                        },
                        linux_playbook="Check processes: top -b -n1 | head -20, Check load: uptime, Check cores: nproc",
                        windows_playbook="Check processes: Get-Process | Sort-Object CPU -Descending | Select-Object -First 10, Check load: Get-WmiObject win32_processor -Property LoadPercentage",
                        value="{{ $value }}",
                    ),
                    _alert(
                        "CPUCritical",
                        '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 95',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Critical CPU usage on {{ $labels.instance }}",
                            "description": "CPU usage is above 95% (current: {{ $value }}%)",
                        },
                        linux_playbook="Check processes: top -b -n1 | head -20, Check load: uptime, Check cores: nproc",
                        windows_playbook="Check processes: Get-Process | Sort-Object CPU -Descending | Select-Object -First 10, Check load: Get-WmiObject win32_processor -Property LoadPercentage",
                        value="{{ $value }}",
                    ),
                ],
                group_name="telegraf_cpu_high",
            ),

            # Memory Alert
            _create_template(
                name="Telegraf Memory High",
                type_="rule",
                job_category="Telegraf",
                sensor_type="Memory",
                description="Alert when memory usage exceeds 85% for 5 minutes.",
                rules=[
                    _alert(
                        "MemoryHigh",
                        '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85',
                        for_="5m",
                        labels={"severity": "warning"},
                        annotations={
                            "summary": "High memory usage on {{ $labels.instance }}",
                            "description": "Memory usage is above 85% (current: {{ $value }}%)",
                        },
                        linux_playbook="Check memory: free -h, Check swap: swapon --show, Check top memory users: top -b -n1 | grep -E 'Mem|VIRT|RES'",
                        windows_playbook="Check memory: Get-WmiObject win32_logicalmemoryconfigurations, Check memory: Get-Process | Sort-Object WS -Descending | Select-Object -First 10",
                        value="{{ $value }}",
                    ),
                    _alert(
                        "MemoryCritical",
                        '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 95',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Critical memory usage on {{ $labels.instance }}",
                            "description": "Memory usage is above 95% (current: {{ $value }}%)",
                        },
                        linux_playbook="Check memory: free -h, Check swap: swapon --show, Check top memory users: top -b -n1 | grep -E 'Mem|VIRT|RES'",
                        windows_playbook="Check memory: Get-WmiObject win32_logicalmemoryconfigurations, Check memory: Get-Process | Sort-Object WS -Descending | Select-Object -First 10",
                        value="{{ $value }}",
                    ),
                ],
                group_name="telegraf_mem_high",
            ),

            # Disk Alert
            _create_template(
                name="Telegraf Disk Space Low",
                type_="rule",
                job_category="Telegraf",
                sensor_type="Disk",
                description="Alert when disk usage exceeds 90% for 5 minutes.",
                rules=[
                    _alert(
                        "DiskSpaceWarning",
                        '(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 85',
                        for_="5m",
                        labels={"severity": "warning"},
                        annotations={
                            "summary": "Low free space on {{ $labels.instance }} ({{ $labels.mountpoint }})",
                            "description": "Disk usage above 85% (current: {{ $value }}%)",
                        },
                        linux_playbook="Check disk usage: df -h, Check inode usage: df -i, Check largest directories: du -sh /*",
                        windows_playbook="Check disk usage: Get-Volume, Check C: drive: Get-Volume | Where-Object {$_.DriveLetter -eq 'C'}, Check largest dirs: Get-ChildItem C:\\ -Recurse -ErrorAction SilentlyContinue | Sort-Object Length -Descending | Select-Object -First 20",
                        value="{{ $value }}",
                    ),
                    _alert(
                        "DiskSpaceCritical",
                        '(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 95',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Critical: Disk full on {{ $labels.instance }} ({{ $labels.mountpoint }})",
                            "description": "Disk usage above 95% (current: {{ $value }}%)",
                        },
                        linux_playbook="Check disk usage: df -h, Check inode usage: df -i, Check largest directories: du -sh /*",
                        windows_playbook="Check disk usage: Get-Volume, Check C: drive: Get-Volume | Where-Object {$_.DriveLetter -eq 'C'}, Check largest dirs: Get-ChildItem C:\\ -Recurse -ErrorAction SilentlyContinue | Sort-Object Length -Descending | Select-Object -First 20",
                        value="{{ $value }}",
                    ),
                ],
                group_name="telegraf_disk_low",
            ),

            # Network Alert (Status)
            _create_template(
                name="Telegraf Network Interface Down",
                type_="rule",
                job_category="Telegraf",
                sensor_type="Network",
                description="Alert when network interface becomes down or errors increase rapidly.",
                rules=[
                    _alert(
                        "NetworkInterfaceDown",
                        'node_network_up{device!~"lo"} == 0',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Network interface {{ $labels.device }} down on {{ $labels.instance }}",
                            "description": "Interface {{ $labels.device }} is not up",
                        },
                        linux_playbook="Check interfaces: ip link show, Check status: ethtool {{ interface }}, Check errors: ip -s link, Check network stack: cat /proc/net/dev",
                        windows_playbook="Check interfaces: Get-NetAdapter, Check status: Get-NetAdapterStatistics, Check errors: netstat -e",
                        value="{{ $value }}",
                    ),
                    _alert(
                        "NetworkErrorsHigh",
                        'rate(node_network_receive_errs_total[5m]) + rate(node_network_transmit_errs_total[5m]) > 10',
                        for_="5m",
                        labels={"severity": "warning"},
                        annotations={
                            "summary": "High network errors on {{ $labels.instance }} ({{ $labels.device }})",
                            "description": "Network errors detected: {{ $value }} errors/sec",
                        },
                        linux_playbook="Check interfaces: ip link show, Check status: ethtool {{ interface }}, Check errors: ip -s link, Check network stack: cat /proc/net/dev",
                        windows_playbook="Check interfaces: Get-NetAdapter, Check status: Get-NetAdapterStatistics, Check errors: netstat -e",
                        value="{{ $value }}",
                    ),
                ],
                group_name="telegraf_network",
            ),

            # Uptime Alert
            _create_template(
                name="Telegraf Host Uptime Low",
                type_="rule",
                job_category="Telegraf",
                sensor_type="Uptime",
                description="Alert when host uptime is less than 1 hour (indicates recent reboot).",
                rules=[
                    _alert(
                        "HostRecentlyRebooted",
                        'node_boot_time_seconds > (time() - 3600)',
                        for_="0m",
                        labels={"severity": "info"},
                        annotations={
                            "summary": "Host {{ $labels.instance }} was recently rebooted",
                            "description": "Host has been up for less than 1 hour",
                        },
                        linux_playbook="Check uptime: uptime, Check last reboot: last reboot, Check systemd journals: journalctl --since '1 hour ago'",
                        windows_playbook="Check uptime: systeminfo | find 'System Boot Time', Check event logs: Get-EventLog -LogName System -InstanceId 6005 -Newest 1",
                        value="{{ $value }}",
                    )
                ],
                group_name="telegraf_uptime",
            ),
        ]
    )

    # ========================================================================
    # 2️⃣  PING RULES (Up/Down, Latency)
    # ========================================================================
    templates.extend(
        [
            # Ping Up/Down
            _create_template(
                name="Ping Host Down",
                type_="rule",
                job_category="Ping",
                sensor_type="Availability",
                description="Alert when ping probe fails for more than 2 minutes.",
                rules=[
                    _alert(
                        "PingHostDown",
                        'probe_success{job="ping"} == 0',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Host {{ $labels.instance }} is unreachable",
                            "description": "Ping probe failing for host {{ $labels.instance }}",
                        },
                        linux_playbook="Ping host: ping -c 5 {{ host }}, Check route: traceroute {{ host }}, Check firewall: sudo iptables -L -n | grep ICMP",
                        windows_playbook="Ping host: ping {{ host }}, Tracert: tracert {{ host }}, Check firewall: netsh advfirewall show allprofiles",
                        value="{{ $value }}",
                    )
                ],
                group_name="ping_updown",
            ),

            # Ping Latency
            _create_template(
                name="Ping Latency High",
                type_="rule",
                job_category="Ping",
                sensor_type="Latency",
                description="Alert when average ping latency exceeds 200ms for 5 minutes.",
                rules=[
                    _alert(
                        "PingLatencyWarning",
                        'probe_duration_seconds{job="ping"} > 0.1',
                        for_="5m",
                        labels={"severity": "warning"},
                        annotations={
                            "summary": "High latency to {{ $labels.instance }}",
                            "description": "Ping latency above 100ms (current: {{ $value | humanizeDuration }})",
                        },
                        linux_playbook="Ping with timing: ping -c 10 {{ host }}, Check route latency: traceroute -w 1 {{ host }}, Check network stats: ss -i",
                        windows_playbook="Ping with timing: ping -n 10 {{ host }}, Check network stats: netstat -ano | findstr ESTABLISHED",
                        value="{{ $value }}",
                    ),
                    _alert(
                        "PingLatencyCritical",
                        'probe_duration_seconds{job="ping"} > 0.5',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Critical latency to {{ $labels.instance }}",
                            "description": "Ping latency above 500ms (current: {{ $value | humanizeDuration }})",
                        },
                        linux_playbook="Ping with timing: ping -c 10 {{ host }}, Check route latency: traceroute -w 1 {{ host }}, Check network stats: ss -i",
                        windows_playbook="Ping with timing: ping -n 10 {{ host }}, Check network stats: netstat -ano | findstr ESTABLISHED",
                        value="{{ $value }}",
                    ),
                ],
                group_name="ping_latency_high",
            ),
        ]
    )

    # ========================================================================
    # 3️⃣  VMWARE RULES (VM CPU/Memory, Host CPU/Memory, Datastores)
    # ========================================================================
    templates.extend(
        [
            # VM CPU
            _create_template(
                name="VMware VM CPU High",
                type_="rule",
                job_category="VMware",
                sensor_type="CPU",
                description="Alert when VM CPU usage exceeds 80% for 5 minutes.",
                rules=[
                    _alert(
                        "VMCPUHigh",
                        'vmware_vm_cpu_usage_percent > 80',
                        for_="5m",
                        labels={"severity": "warning"},
                        annotations={
                            "summary": "High CPU on VM {{ $labels.vm_name }} ({{ $labels.host }})",
                            "description": "VM CPU usage above 80% (current: {{ $value }}%)",
                        },
                        linux_playbook="SSH to VM: ssh {{ vm_ip }}, Check CPU: top -b -n1 | head -20",
                        windows_playbook="RDP to VM, Check CPU: Get-Process | Sort-Object CPU -Descending | Select-Object -First 10",
                        value="{{ $value }}",
                    ),
                    _alert(
                        "VMCPUCritical",
                        'vmware_vm_cpu_usage_percent > 95',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Critical CPU on VM {{ $labels.vm_name }} ({{ $labels.host }})",
                            "description": "VM CPU usage above 95% (current: {{ $value }}%)",
                        },
                        linux_playbook="SSH to VM: ssh {{ vm_ip }}, Check CPU: top -b -n1 | head -20",
                        windows_playbook="RDP to VM, Check CPU: Get-Process | Sort-Object CPU -Descending | Select-Object -First 10",
                        value="{{ $value }}",
                    ),
                ],
                group_name="vmware_vm_cpu_high",
            ),

            # VM Memory
            _create_template(
                name="VMware VM Memory High",
                type_="rule",
                job_category="VMware",
                sensor_type="Memory",
                description="Alert when VM memory usage exceeds 85% for 5 minutes.",
                rules=[
                    _alert(
                        "VMMemoryHigh",
                        'vmware_vm_memory_usage_percent > 85',
                        for_="5m",
                        labels={"severity": "warning"},
                        annotations={
                            "summary": "High memory on VM {{ $labels.vm_name }} ({{ $labels.host }})",
                            "description": "VM memory usage above 85% (current: {{ $value }}%)",
                        },
                        linux_playbook="SSH to VM: ssh {{ vm_ip }}, Check memory: free -h, Check top memory users: top -b -n1 | grep -E 'Mem|RES'",
                        windows_playbook="RDP to VM, Check memory: Get-WmiObject win32_logicalmemoryconfigurations, Check processes: Get-Process | Sort-Object WS -Descending | Select-Object -First 10",
                        value="{{ $value }}",
                    ),
                    _alert(
                        "VMMemoryCritical",
                        'vmware_vm_memory_usage_percent > 95',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Critical memory on VM {{ $labels.vm_name }} ({{ $labels.host }})",
                            "description": "VM memory usage above 95% (current: {{ $value }}%)",
                        },
                        linux_playbook="SSH to VM: ssh {{ vm_ip }}, Check memory: free -h, Check top memory users: top -b -n1 | grep -E 'Mem|RES'",
                        windows_playbook="RDP to VM, Check memory: Get-WmiObject win32_logicalmemoryconfigurations, Check processes: Get-Process | Sort-Object WS -Descending | Select-Object -First 10",
                        value="{{ $value }}",
                    ),
                ],
                group_name="vmware_vm_mem_high",
            ),

            # Host CPU
            _create_template(
                name="VMware Host CPU High",
                type_="rule",
                job_category="VMware",
                sensor_type="CPU",
                description="Alert when ESX host CPU usage exceeds 80% for 5 minutes.",
                rules=[
                    _alert(
                        "HostCPUHigh",
                        'vmware_host_cpu_usage_percent > 80',
                        for_="5m",
                        labels={"severity": "warning"},
                        annotations={
                            "summary": "High CPU on ESX host {{ $labels.host_name }}",
                            "description": "Host CPU usage above 80% (current: {{ $value }}%)",
                        },
                        linux_playbook="SSH to ESX: ssh root@{{ host }}, Check CPU: esxcli hardware cpu global get, Check processes: esxtop",
                        windows_playbook="N/A - ESX hosts are Linux-based",
                        value="{{ $value }}",
                    ),
                    _alert(
                        "HostCPUCritical",
                        'vmware_host_cpu_usage_percent > 90',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Critical CPU on ESX host {{ $labels.host_name }}",
                            "description": "Host CPU usage above 90% (current: {{ $value }}%)",
                        },
                        linux_playbook="SSH to ESX: ssh root@{{ host }}, Check CPU: esxcli hardware cpu global get, Check processes: esxtop",
                        windows_playbook="N/A - ESX hosts are Linux-based",
                        value="{{ $value }}",
                    ),
                ],
                group_name="vmware_host_cpu_high",
            ),

            # Host Memory
            _create_template(
                name="VMware Host Memory High",
                type_="rule",
                job_category="VMware",
                sensor_type="Memory",
                description="Alert when ESX host memory usage exceeds 85% for 5 minutes.",
                rules=[
                    _alert(
                        "HostMemoryHigh",
                        'vmware_host_memory_usage_percent > 85',
                        for_="5m",
                        labels={"severity": "warning"},
                        annotations={
                            "summary": "High memory on ESX host {{ $labels.host_name }}",
                            "description": "Host memory usage above 85% (current: {{ $value }}%)",
                        },
                        linux_playbook="SSH to ESX: ssh root@{{ host }}, Check memory: esxcli hardware memory get, Check free memory: esxtop",
                        windows_playbook="N/A - ESX hosts are Linux-based",
                        value="{{ $value }}",
                    ),
                    _alert(
                        "HostMemoryCritical",
                        'vmware_host_memory_usage_percent > 95',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Critical memory on ESX host {{ $labels.host_name }}",
                            "description": "Host memory usage above 95% (current: {{ $value }}%)",
                        },
                        linux_playbook="SSH to ESX: ssh root@{{ host }}, Check memory: esxcli hardware memory get, Check free memory: esxtop",
                        windows_playbook="N/A - ESX hosts are Linux-based",
                        value="{{ $value }}",
                    ),
                ],
                group_name="vmware_host_mem_high",
            ),

            # Datastore
            _create_template(
                name="VMware Datastore Space Low",
                type_="rule",
                job_category="VMware",
                sensor_type="Storage",
                description="Alert when datastore usage exceeds 85% for 5 minutes.",
                rules=[
                    _alert(
                        "DatastoreWarning",
                        'vmware_datastore_capacity_percent > 85',
                        for_="5m",
                        labels={"severity": "warning"},
                        annotations={
                            "summary": "Low free space on datastore {{ $labels.datastore }} ({{ $labels.cluster }})",
                            "description": "Datastore usage above 85% (current: {{ $value }}%)",
                        },
                        linux_playbook="SSH to vCenter: ssh root@{{ vcenter }}, Check datastores: esxcli storage filesystem list, Check space: vim-cmd hostsvc/datastore/info",
                        windows_playbook="Use vSphere Client, Navigate to Storage > Datastores, Check free space and capacity",
                        value="{{ $value }}",
                    ),
                    _alert(
                        "DatastoreCritical",
                        'vmware_datastore_capacity_percent > 95',
                        for_="2m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "Critical: Datastore {{ $labels.datastore }} almost full ({{ $labels.cluster }})",
                            "description": "Datastore usage above 95% (current: {{ $value }}%)",
                        },
                        linux_playbook="SSH to vCenter: ssh root@{{ vcenter }}, Check datastores: esxcli storage filesystem list, Check space: vim-cmd hostsvc/datastore/info",
                        windows_playbook="Use vSphere Client, Navigate to Storage > Datastores, Check free space and capacity",
                        value="{{ $value }}",
                    ),
                ],
                group_name="vmware_datastore_low",
            ),
        ]
    )

    # ========================================================================
    # 4️⃣  SSL/TLS RULES (Expiring Soon, Expired)
    # ========================================================================
    templates.extend(
        [
            # SSL Expiring Soon (15 days)
            _create_template(
                name="SSL Certificate Expiring Soon (15 days)",
                type_="rule",
                job_category="SSL",
                sensor_type="Certificate",
                description="Alert when SSL certificate expires within 15 days.",
                rules=[
                    _alert(
                        "SSLCertExpiring15d",
                        'probe_ssl_earliest_cert_expiry - time() < 15 * 24 * 3600',
                        for_="1h",
                        labels={"severity": "warning"},
                        annotations={
                            "summary": "SSL certificate expiring soon: {{ $labels.instance }}",
                            "description": "Certificate expires in {{ $value | humanizeDuration }}",
                        },
                        linux_playbook="Check cert: openssl s_client -connect {{ domain }}:443 -showcerts, Check expiry: openssl x509 -in {{ cert_file }} -noout -dates",
                        windows_playbook="Check cert: certlm.msc (Local Machine > Personal > Certificates), Check expiry: Get-ChildItem Cert:\\LocalMachine\\My | Where-Object { $_.NotAfter -lt (Get-Date).AddDays(15) }",
                        value="{{ $value }}",
                    )
                ],
                group_name="ssl_cert_expiring_15d",
            ),

            # SSL Expired
            _create_template(
                name="SSL Certificate Expired",
                type_="rule",
                job_category="SSL",
                sensor_type="Certificate",
                description="Alert when SSL certificate has expired.",
                rules=[
                    _alert(
                        "SSLCertExpired",
                        'probe_ssl_earliest_cert_expiry - time() <= 0',
                        for_="0m",
                        labels={"severity": "critical"},
                        annotations={
                            "summary": "SSL certificate EXPIRED: {{ $labels.instance }}",
                            "description": "Certificate expired {{ $value | humanizeDuration }} ago",
                        },
                        linux_playbook="Renew cert: certbot renew, Check cert: openssl x509 -in {{ cert_file }} -noout -dates, Restart service: systemctl restart nginx/apache2",
                        windows_playbook="Renew cert: Use Let's Encrypt ACME client or manual renewal, Replace cert: iisreset, Import cert: certlm.msc",
                        value="{{ $value }}",
                    )
                ],
                group_name="ssl_cert_expired",
            ),
        ]
    )

    return templates


def seed_default_templates():
    """Insert the default templates if the table is empty."""
    from app import SessionLocal
    db = SessionLocal()
    try:
        # Check if any templates already exist (skip seeding)
        if db.query(Template).count() > 0:
            return
        for tpl in generate_default_templates():
            db.add(tpl)
        db.commit()
    finally:
        db.close()
