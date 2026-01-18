# seed_templates.py
import yaml
from sqlalchemy.orm import Session
from models import Template


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


def _alert(name, expr, for_="5m", labels=None, annotations=None):
    """Helper to build an alerting rule dict."""
    return {
        "alert": name,
        "expr": expr,
        "for": for_,
        "labels": labels or {},
        "annotations": annotations or {},
    }


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
    # 1️⃣  TELEGRAPH RULES (CPU, Memory, Disk, Network, Process)
    # ========================================================================
    templates.extend(
        [
            # Alerting rules
            Template(
                name="Telegraf CPU High",
                type="rule",
                job_category="Telegraf",
                sensor_type="CPU",
                description="Alert when CPU usage stays above 80 % for 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "telegraf_cpu_high",
                        [
                            _alert(
                                "CPUHigh",
                                '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "High CPU usage on {{ $labels.instance }}",
                                    "description": "CPU > 80 % for > 5 min.",
                                },
                            )
                        ],
                    )
                ),
            ),
            Template(
                name="Telegraf Memory High",
                type="rule",
                job_category="Telegraf",
                sensor_type="Memory",
                description="Memory usage > 85 % for 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "telegraf_mem_high",
                        [
                            _alert(
                                "MemoryHigh",
                                '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "High memory usage on {{ $labels.instance }}",
                                    "description": "Memory > 85 % for > 5 min.",
                                },
                            )
                        ],
                    )
                ),
            ),
            Template(
                name="Telegraf Disk Space Low",
                type="rule",
                job_category="Telegraf",
                sensor_type="Disk",
                description="Disk usage > 90 % for 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "telegraf_disk_low",
                        [
                            _alert(
                                "DiskSpaceLow",
                                '(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 90',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "Low free space on {{ $labels.instance }}",
                                    "description": "Usage > 90 % on {{ $labels.mountpoint }}.",
                                },
                            )
                        ],
                    )
                ),
            ),

            # Recording rules - CPU
            Template(
                name="CPU Usage Recording (5m rate)",
                type="rule",
                job_category="Telegraf",
                sensor_type="CPU",
                description="Recording rule for CPU usage percentage with 5-minute rate.",
                content=_dump_yaml(
                    _group_rule(
                        "cpu_recording_5m",
                        [
                            _recording(
                                "instance:cpu_usage:rate5m",
                                '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
                                labels={"record": "instance:cpu_usage:rate5m"}
                            )
                        ]
                    )
                ),
            ),
            Template(
                name="CPU Usage Recording (1m rate)",
                type="rule",
                job_category="Telegraf",
                sensor_type="CPU",
                description="Recording rule for CPU usage percentage with 1-minute rate.",
                content=_dump_yaml(
                    _group_rule(
                        "cpu_recording_1m",
                        [
                            _recording(
                                "instance:cpu_usage:rate1m",
                                '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)',
                                labels={"record": "instance:cpu_usage:rate1m"}
                            )
                        ]
                    )
                ),
            ),
            Template(
                name="CPU Usage by Mode Recording",
                type="rule",
                job_category="Telegraf",
                sensor_type="CPU",
                description="Recording rule for CPU usage broken down by CPU mode.",
                content=_dump_yaml(
                    _group_rule(
                        "cpu_by_mode_recording",
                        [
                            _recording(
                                "instance:cpu_mode:rate5m",
                                '100 * (rate(node_cpu_seconds_total[5m]))',
                                labels={"record": "instance:cpu_mode:rate5m"}
                            )
                        ]
                    )
                ),
            ),

            # Recording rules - Memory
            Template(
                name="Memory Usage Recording",
                type="rule",
                job_category="Telegraf",
                sensor_type="Memory",
                description="Recording rule for memory usage percentage.",
                content=_dump_yaml(
                    _group_rule(
                        "memory_recording",
                        [
                            _recording(
                                "instance:memory_usage:percent",
                                '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
                                labels={"record": "instance:memory_usage:percent"}
                            )
                        ]
                    )
                ),
            ),
            Template(
                name="Memory Usage by Type Recording",
                type="rule",
                job_category="Telegraf",
                sensor_type="Memory",
                description="Recording rule for memory usage by memory type.",
                content=_dump_yaml(
                    _group_rule(
                        "memory_by_type_recording",
                        [
                            _recording(
                                "instance:memory:bytes",
                                'node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes',
                                labels={"record": "instance:memory:bytes"}
                            )
                        ]
                    )
                ),
            ),

            # Recording rules - Disk
            Template(
                name="Disk Usage Recording",
                type="rule",
                job_category="Telegraf",
                sensor_type="Disk",
                description="Recording rule for disk usage percentage by mountpoint.",
                content=_dump_yaml(
                    _group_rule(
                        "disk_recording",
                        [
                            _recording(
                                "instance:disk_usage:percent",
                                '(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100',
                                labels={"record": "instance:disk_usage:percent"}
                            )
                        ]
                    )
                ),
            ),
            Template(
                name="Disk I/O Rate Recording",
                type="rule",
                job_category="Telegraf",
                sensor_type="Disk",
                description="Recording rule for disk I/O operations per second.",
                content=_dump_yaml(
                    _group_rule(
                        "disk_io_recording",
                        [
                            _recording(
                                "instance:disk_io:reads:rate5m",
                                'rate(node_disk_reads_completed_total[5m])',
                                labels={"record": "instance:disk_io:reads:rate5m"}
                            ),
                            _recording(
                                "instance:disk_io:writes:rate5m",
                                'rate(node_disk_writes_completed_total[5m])',
                                labels={"record": "instance:disk_io:writes:rate5m"}
                            )
                        ]
                    )
                ),
            ),

            # Recording rules - Network
            Template(
                name="Network Rate Recording",
                type="rule",
                job_category="Telegraf",
                sensor_type="Network",
                description="Recording rule for network traffic rates.",
                content=_dump_yaml(
                    _group_rule(
                        "network_recording",
                        [
                            _recording(
                                "instance:network:bytes:rate5m",
                                'rate(node_network_receive_bytes_total[5m]) + rate(node_network_transmit_bytes_total[5m])',
                                labels={"record": "instance:network:bytes:rate5m"}
                            )
                        ]
                    )
                ),
            ),
        ]
    )

    # ========================================================================
    # 2️⃣  PING / ICMP RULES
    # ========================================================================
    templates.extend(
        [
            # Alerting rules
            Template(
                name="Ping Latency High",
                type="rule",
                job_category="Ping",
                sensor_type="Latency",
                description="Average ping latency > 200 ms for 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "ping_latency_high",
                        [
                            _alert(
                                "PingLatencyHigh",
                                'avg_over_time(ping_duration_seconds[5m]) > 0.2',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "High ping latency to {{ $labels.instance }}",
                                    "description": "Average ping > 200 ms for > 5 min.",
                                },
                            )
                        ],
                    )
                ),
            ),
            Template(
                name="Ping Packet Loss",
                type="rule",
                job_category="Ping",
                sensor_type="Loss",
                description="Packet loss > 2 % over 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "ping_packet_loss",
                        [
                            _alert(
                                "PingPacketLoss",
                                'rate(ping_packets_received_total[5m]) / rate(ping_packets_sent_total[5m]) < 0.98',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "Packet loss to {{ $labels.instance }}",
                                    "description": "Loss > 2 % for > 5 min.",
                                },
                            )
                        ],
                    )
                ),
            ),

            # Recording rules
            Template(
                name="Ping Latency Recording",
                type="rule",
                job_category="Ping",
                sensor_type="Latency",
                description="Recording rule for ping latency average.",
                content=_dump_yaml(
                    _group_rule(
                        "ping_latency_recording",
                        [
                            _recording(
                                "instance:ping_latency:avg5m",
                                'avg_over_time(ping_duration_seconds[5m])',
                                labels={"record": "instance:ping_latency:avg5m"}
                            )
                        ]
                    )
                ),
            ),
            Template(
                name="Ping Loss Rate Recording",
                type="rule",
                job_category="Ping",
                sensor_type="Loss",
                description="Recording rule for packet loss percentage.",
                content=_dump_yaml(
                    _group_rule(
                        "ping_loss_recording",
                        [
                            _recording(
                                "instance:ping_loss:percent5m",
                                '(1 - (rate(ping_packets_received_total[5m]) / rate(ping_packets_sent_total[5m]))) * 100',
                                labels={"record": "instance:ping_loss:percent5m"}
                            )
                        ]
                    )
                ),
            ),
        ]
    )

    # ========================================================================
    # 3️⃣  SSL / TLS CERT EXPIRY
    # ========================================================================
    templates.extend(
        [
            Template(
                name="SSL Cert Expiry (15 days)",
                type="rule",
                job_category="SSL",
                sensor_type="Certificate",
                description="Certificate expires within 15 days.",
                content=_dump_yaml(
                    _group_rule(
                        "ssl_cert_expiry_15d",
                        [
                            _alert(
                                "SSLCertExpiringSoon",
                                'probe_ssl_earliest_cert_expiry - time() < 15 * 24 * 3600',
                                for_="1h",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "SSL cert for {{ $labels.instance }} expires in < 15 days",
                                },
                            )
                        ],
                    )
                ),
            ),
            Template(
                name="SSL Cert Expiry (30 days)",
                type="rule",
                job_category="SSL",
                sensor_type="Certificate",
                description="Certificate expires within 30 days.",
                content=_dump_yaml(
                    _group_rule(
                        "ssl_cert_expiry_30d",
                        [
                            _alert(
                                "SSLCertExpiring",
                                'probe_ssl_earliest_cert_expiry - time() < 30 * 24 * 3600',
                                for_="1h",
                                labels={"severity": "info"},
                                annotations={
                                    "summary": "SSL cert for {{ $labels.instance }} expires in < 30 days",
                                },
                            )
                        ],
                    )
                ),
            ),
        ]
    )

    # ========================================================================
    # 4️⃣  VMWARE RULES (VMs, ESX, DATASTORES)
    # ========================================================================
    templates.extend(
        [
            # VM alerts
            Template(
                name="VMware VM CPU High",
                type="rule",
                job_category="VMware",
                sensor_type="CPU",
                description="VMware VM CPU usage > 80 % for 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "vmware_vm_cpu_high",
                        [
                            _alert(
                                "VMwareVMCPUHigh",
                                'vmware_vm_cpu_usage_percent > 80',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "High CPU usage on VM {{ $labels.vm }} ({{ $labels.instance }})",
                                },
                            )
                        ],
                    )
                ),
            ),
            Template(
                name="VMware VM Memory High",
                type="rule",
                job_category="VMware",
                sensor_type="Memory",
                description="VMware VM memory usage > 85 % for 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "vmware_vm_mem_high",
                        [
                            _alert(
                                "VMwareVMMemHigh",
                                'vmware_vm_memory_usage_percent > 85',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "High memory usage on VM {{ $labels.vm }} ({{ $labels.instance }})",
                                },
                            )
                        ],
                    )
                ),
            ),
            Template(
                name="VMware VMDatastore Usage High",
                type="rule",
                job_category="VMware",
                sensor_type="Storage",
                description="Datastore usage > 85 % for 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "vmware_datastore_usage_high",
                        [
                            _alert(
                                "VMwareDatastoreUsageHigh",
                                'vmware_datastore_capacity_percent > 85',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "High usage on datastore {{ $labels.datastore }} ({{ $labels.instance }})",
                                },
                            )
                        ],
                    )
                ),
            ),

            # VMware recording rules
            Template(
                name="VMware VM CPU Usage Recording",
                type="rule",
                job_category="VMware",
                sensor_type="CPU",
                description="Recording rule for VMware VM CPU usage percentage.",
                content=_dump_yaml(
                    _group_rule(
                        "vmware_vm_cpu_recording",
                        [
                            _recording(
                                "vm:cpu_usage:percent",
                                'vmware_vm_cpu_usage_percent',
                                labels={"record": "vm:cpu_usage:percent"}
                            )
                        ]
                    )
                ),
            ),
            Template(
                name="VMware VM Memory Usage Recording",
                type="rule",
                job_category="VMware",
                sensor_type="Memory",
                description="Recording rule for VMware VM memory usage percentage.",
                content=_dump_yaml(
                    _group_rule(
                        "vmware_vm_memory_recording",
                        [
                            _recording(
                                "vm:memory_usage:percent",
                                'vmware_vm_memory_usage_percent',
                                labels={"record": "vm:memory_usage:percent"}
                            )
                        ]
                    )
                ),
            ),
            Template(
                name="VMware Datastore Usage Recording",
                type="rule",
                job_category="VMware",
                sensor_type="Storage",
                description="Recording rule for VMware datastore usage percentage.",
                content=_dump_yaml(
                    _group_rule(
                        "vmware_datastore_recording",
                        [
                            _recording(
                                "datastore:usage:percent",
                                'vmware_datastore_capacity_percent',
                                labels={"record": "datastore:usage:percent"}
                            )
                        ]
                    )
                ),
            ),
        ]
    )

    # ========================================================================
    # 5️⃣  KUBERNETES RULES
    # ========================================================================
    templates.extend(
        [
            # Alerting rules
            Template(
                name="Kubernetes API Server Error Rate",
                type="rule",
                job_category="Kubernetes",
                sensor_type="API",
                description="APIServer 5xx error rate > 1 % for 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "k8s_api_error_rate",
                        [
                            _alert(
                                "K8SAPIServerErrorRate",
                                'rate(apiserver_request_total{code=~"5.."}[5m]) / rate(apiserver_request_total[5m]) > 0.01',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "API server high 5xx rate on cluster {{ $labels.cluster }}",
                                },
                            )
                        ],
                    )
                ),
            ),
            Template(
                name="Kubernetes Node Not Ready",
                type="rule",
                job_category="Kubernetes",
                sensor_type="Node",
                description="Node becomes NotReady for > 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "k8s_node_not_ready",
                        [
                            _alert(
                                "K8SNodeNotReady",
                                'kube_node_status_condition{condition="Ready",status="true"} == 0',
                                for_="5m",
                                labels={"severity": "critical"},
                                annotations={
                                    "summary": "Node {{ $labels.node }} is not ready",
                                },
                            )
                        ],
                    )
                ),
            ),

            # Recording rules
            Template(
                name="Kubernetes API Request Rate Recording",
                type="rule",
                job_category="Kubernetes",
                sensor_type="API",
                description="Recording rule for K8s API request rates by verb.",
                content=_dump_yaml(
                    _group_rule(
                        "k8s_api_recording",
                        [
                            _recording(
                                "cluster:apiserver_request_rate:5m",
                                'sum(rate(apiserver_request_total[5m])) by (verb, cluster)',
                                labels={"record": "cluster:apiserver_request_rate:5m"}
                            )
                        ]
                    )
                ),
            ),
            Template(
                name="Kubernetes Pod CPU Usage Recording",
                type="rule",
                job_category="Kubernetes",
                sensor_type="CPU",
                description="Recording rule for pod CPU usage.",
                content=_dump_yaml(
                    _group_rule(
                        "k8s_pod_cpu_recording",
                        [
                            _recording(
                                "namespace:pod_cpu_usage:rate5m",
                                'sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (namespace, pod)',
                                labels={"record": "namespace:pod_cpu_usage:rate5m"}
                            )
                        ]
                    )
                ),
            ),
            Template(
                name="Kubernetes Pod Memory Usage Recording",
                type="rule",
                job_category="Kubernetes",
                sensor_type="Memory",
                description="Recording rule for pod memory usage.",
                content=_dump_yaml(
                    _group_rule(
                        "k8s_pod_memory_recording",
                        [
                            _recording(
                                "namespace:pod_memory_usage:bytes",
                                'sum(container_memory_working_set_bytes{container!=""}) by (namespace, pod)',
                                labels={"record": "namespace:pod_memory_usage:bytes"}
                            )
                        ]
                    )
                ),
            ),
        ]
    )

    # ========================================================================
    # 6️⃣  DATABASE RULES (MySQL, Redis, etc.)
    # ========================================================================
    templates.extend(
        [
            # MySQL
            Template(
                name="MySQL Replication Lag",
                type="rule",
                job_category="MySQL",
                sensor_type="Replication",
                description="Slave lag > 30 s for 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "mysql_repl_lag",
                        [
                            _alert(
                                "MySQLReplicationLag",
                                'mysql_slave_lag_seconds > 30',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "MySQL replication lag on {{ $labels.instance }}",
                                },
                            )
                        ],
                    )
                ),
            ),
            Template(
                name="MySQL Query Rate Recording",
                type="rule",
                job_category="MySQL",
                sensor_type="Queries",
                description="Recording rule for MySQL query rates.",
                content=_dump_yaml(
                    _group_rule(
                        "mysql_queries_recording",
                        [
                            _recording(
                                "instance:mysql_queries:rate5m",
                                'rate(mysql_global_status_questions[5m])',
                                labels={"record": "instance:mysql_queries:rate5m"}
                            )
                        ]
                    )
                ),
            ),

            # Redis
            Template(
                name="Redis Memory High",
                type="rule",
                job_category="Redis",
                sensor_type="Memory",
                description="Redis memory usage > 90 % for 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "redis_mem_high",
                        [
                            _alert(
                                "RedisMemoryHigh",
                                'redis_memory_used_bytes / redis_memory_max_bytes > 0.9',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "Redis memory high on {{ $labels.instance }}",
                                },
                            )
                        ],
                    )
                ),
            ),
            Template(
                name="Redis Memory Usage Recording",
                type="rule",
                job_category="Redis",
                sensor_type="Memory",
                description="Recording rule for Redis memory usage percentage.",
                content=_dump_yaml(
                    _group_rule(
                        "redis_memory_recording",
                        [
                            _recording(
                                "instance:redis_memory:percent",
                                'redis_memory_used_bytes / redis_memory_max_bytes * 100',
                                labels={"record": "instance:redis_memory:percent"}
                            )
                        ]
                    )
                ),
            ),
        ]
    )

    # ========================================================================
    # 7️⃣  WEB SERVER RULES (Nginx, Apache)
    # ========================================================================
    templates.extend(
        [
            # Nginx
            Template(
                name="Nginx 5xx Error Rate",
                type="rule",
                job_category="Nginx",
                sensor_type="HTTP",
                description="Nginx 5xx error rate > 1 % for 5 min.",
                content=_dump_yaml(
                    _group_rule(
                        "nginx_5xx_rate",
                        [
                            _alert(
                                "Nginx5xxErrorRate",
                                'rate(nginx_http_requests_total{status=~"5.."}[5m]) / rate(nginx_http_requests_total[5m]) > 0.01',
                                for_="5m",
                                labels={"severity": "warning"},
                                annotations={
                                    "summary": "High 5xx error rate on {{ $labels.instance }}",
                                },
                            )
                        ],
                    )
                ),
            ),
            Template(
                name="Nginx Request Rate Recording",
                type="rule",
                job_category="Nginx",
                sensor_type="HTTP",
                description="Recording rule for Nginx request rates by status code.",
                content=_dump_yaml(
                    _group_rule(
                        "nginx_requests_recording",
                        [
                            _recording(
                                "instance:nginx_requests:rate5m",
                                'sum(rate(nginx_http_requests_total[5m])) by (instance, status)',
                                labels={"record": "instance:nginx_requests:rate5m"}
                            )
                        ]
                    )
                ),
            ),
        ]
    )

    # ========================================================================
    # 8️⃣  ALERTMANAGER TEMPLATES (Updated with email + webhook)
    # ========================================================================
    templates.extend(
        [
            # Default route
            Template(
                name="Default Alertmanager Route",
                type="alertmanager",
                job_category="General",
                sensor_type="N/A",
                description="Default route grouping by alertname, cluster, service.",
                content=_dump_yaml(
                    {
                        "global": {
                            "smtp_smarthost": "localhost:587",
                            "smtp_from": "alerts@example.com",
                        },
                        "route": {
                            "group_by": ["alertname", "cluster", "service"],
                            "group_wait": "10s",
                            "group_interval": "10s",
                            "repeat_interval": "1h",
                            "receiver": "default",
                        },
                        "receivers": [
                            {"name": "default"},
                            {"name": "ops-team-email", "email_configs": [{"to": "ops@example.com"}]},
                        ],
                        "inhibit_rules": [
                            {
                                "source_match": {"severity": "critical"},
                                "target_match": {"severity": "warning"},
                                "equal": ["alertname", "instance"],
                            }
                        ],
                    }
                ),
            ),

            # Email + Webhook route
            Template(
                name="Email + Webhook Route",
                type="alertmanager",
                job_category="General",
                sensor_type="N/A",
                description="Send critical to webhook, warnings/info to email.",
                content=_dump_yaml(
                    {
                        "route": {
                            "receiver": "default",
                            "routes": [
                                {"matchers": ["severity=~'critical|error'"], "receiver": "webhook"},
                                {"matchers": ["severity=~'warning|info'"], "receiver": "email"},
                            ],
                        },
                        "receivers": [
                            {
                                "name": "webhook",
                                "webhook_configs": [
                                    {
                                        "url": "https://your-webhook-endpoint.com/alert",
                                        "title": "Alert: {{ .GroupLabels.alertname }}",
                                        "text": "{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}",
                                    }
                                ],
                            },
                            {
                                "name": "email",
                                "email_configs": [{"to": "ops@example.com"}],
                            },
                            {"name": "default"},
                        ],
                    }
                ),
            ),

            # All alerts to webhook
            Template(
                name="All Alerts to Webhook",
                type="alertmanager",
                job_category="General",
                sensor_type="N/A",
                description="Send all alerts to a webhook endpoint.",
                content=_dump_yaml(
                    {
                        "route": {
                            "receiver": "webhook",
                            "group_by": ["alertname", "instance"],
                            "group_wait": "10s",
                            "group_interval": "10s",
                            "repeat_interval": "1h",
                        },
                        "receivers": [
                            {
                                "name": "webhook",
                                "webhook_configs": [
                                    {
                                        "url": "https://your-webhook-endpoint.com/alert",
                                        "send_resolved": True,
                                        "title": "Alert: {{ .GroupLabels.alertname }}",
                                        "text": "{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}",
                                    }
                                ],
                            },
                        ],
                    }
                ),
            ),

            # Multi-receiver with different alert types
            Template(
                name="Multi-Receiver with Escalation",
                type="alertmanager",
                job_category="General",
                sensor_type="N/A",
                description="Critical to webhook immediately, warnings to email, resolved to webhook.",
                content=_dump_yaml(
                    {
                        "route": {
                            "receiver": "default",
                            "routes": [
                                {
                                    "matchers": ["severity=~'critical'"],
                                    "receiver": "webhook",
                                    "group_wait": "0s",
                                },
                                {
                                    "matchers": ["severity=~'warning'"],
                                    "receiver": "email",
                                    "group_wait": "30s",
                                },
                                {
                                    "matchers": ["alertstate=~'resolved'"],
                                    "receiver": "webhook",
                                },
                            ],
                        },
                        "receivers": [
                            {
                                "name": "webhook",
                                "webhook_configs": [
                                    {
                                        "url": "https://your-webhook-endpoint.com/alert",
                                        "send_resolved": True,
                                        "title": "Alert: {{ .GroupLabels.alertname }}",
                                        "text": "{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}",
                                    }
                                ],
                            },
                            {
                                "name": "email",
                                "email_configs": [{"to": "ops@example.com"}],
                            },
                            {"name": "default"},
                        ],
                    }
                ),
            ),
        ]
    )

    # ========================================================================
    # 9️⃣  MIXED ALERTING + RECORDING RULE GROUPS (Examples of combining both)
    # ========================================================================
    templates.extend(
        [
            # Combined CPU group with recording and alerting rules
            Template(
                name="Complete CPU Monitoring",
                type="rule",
                job_category="Telegraf",
                sensor_type="CPU",
                description="Group with recording rules and alerts for comprehensive CPU monitoring.",
                content=_dump_yaml(
                    {
                        "groups": [
                            {
                                "name": "complete_cpu_monitoring",
                                "rules": [
                                    # Recording rules
                                    _recording(
                                        "instance:cpu_usage:rate5m",
                                        '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
                                        labels={"record": "instance:cpu_usage:rate5m"}
                                    ),
                                    _recording(
                                        "instance:cpu_usage:rate1m",
                                        '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)',
                                        labels={"record": "instance:cpu_usage:rate1m"}
                                    ),
                                    # Alerting rules using the recording rules
                                    _alert(
                                        "CPUHigh",
                                        'instance:cpu_usage:rate5m > 80',
                                        for_="5m",
                                        labels={"severity": "warning"},
                                        annotations={
                                            "summary": "High CPU usage on {{ $labels.instance }}",
                                            "description": "CPU usage is above 80% for more than 5 minutes.",
                                        },
                                    ),
                                    _alert(
                                        "CPUCritical",
                                        'instance:cpu_usage:rate5m > 95',
                                        for_="2m",
                                        labels={"severity": "critical"},
                                        annotations={
                                            "summary": "Critical CPU usage on {{ $labels.instance }}",
                                            "description": "CPU usage is above 95% for more than 2 minutes.",
                                        },
                                    ),
                                ],
                            }
                        ]
                    }
                ),
            ),

            # Combined Memory group with recording and alerting rules
            Template(
                name="Complete Memory Monitoring",
                type="rule",
                job_category="Telegraf",
                sensor_type="Memory",
                description="Group with recording rules and alerts for comprehensive memory monitoring.",
                content=_dump_yaml(
                    {
                        "groups": [
                            {
                                "name": "complete_memory_monitoring",
                                "rules": [
                                    # Recording rules
                                    _recording(
                                        "instance:memory_usage:percent",
                                        '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
                                        labels={"record": "instance:memory_usage:percent"}
                                    ),
                                    _recording(
                                        "instance:swap_usage:percent",
                                        '(node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes) / node_memory_SwapTotal_bytes * 100',
                                        labels={"record": "instance:swap_usage:percent"}
                                    ),
                                    # Alerting rules
                                    _alert(
                                        "MemoryHigh",
                                        'instance:memory_usage:percent > 85',
                                        for_="5m",
                                        labels={"severity": "warning"},
                                        annotations={
                                            "summary": "High memory usage on {{ $labels.instance }}",
                                            "description": "Memory usage is above 85% for more than 5 minutes.",
                                        },
                                    ),
                                    _alert(
                                        "SwapHigh",
                                        'instance:swap_usage:percent > 20',
                                        for_="5m",
                                        labels={"severity": "warning"},
                                        annotations={
                                            "summary": "High swap usage on {{ $labels.instance }}",
                                            "description": "Swap usage is above 20% for more than 5 minutes.",
                                        },
                                    ),
                                ],
                            }
                        ]
                    }
                ),
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
