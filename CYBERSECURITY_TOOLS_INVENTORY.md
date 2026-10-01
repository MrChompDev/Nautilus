# Cybersecurity Tools Inventory

Comprehensive inventory of all tools, frameworks, platforms, and technologies mentioned across 200+ cybersecurity skills in the agent system.

---

## SIEM & Log Management

| Tool | Category | Description |
|------|----------|-------------|
| **Splunk** | SIEM | Enterprise security information and event management |
| **Splunk Enterprise Security** | SIEM | Security-focused Splunk app for correlation, dashboards |
| **Splunk SOAR (Phantom)** | SOAR | Security orchestration, automation, and response |
| **Elastic Security** | SIEM | Elastic Stack security solution (formerly Elastic SIEM) |
| **Elastic/Kibana** | SIEM/Visualization | Log aggregation, search, and visualization |
| **Microsoft Sentinel** | SIEM | Cloud-native SIEM/SOAR (formerly Azure Sentinel) |
| **QRadar SIEM** | SIEM | IBM's security information and event management |
| **Chronicle/Backstory** | SIEM | Google Cloud's security analytics platform |
| **LogRhythm** | SIEM | Next-gen SIEM with security analytics |
| **ArcSight** | SIEM | Micro Focus enterprise SIEM |
| **Securonix** | SIEM | Behavior analytics-driven SIEM |
| **Exabeam** | SIEM | User and entity behavior analytics (UEBA) |
| **Sumo Logic** | SIEM | Cloud-native log analytics and SIEM |
| **Datadog Security** | SIEM/Monitoring | Cloud monitoring with security modules |
| **New Relic** | Observability | Full-stack observability with security |
| **Honeycomb** | Observability | High-cardinality observability |
| **Lightstep** | Observability | Distributed tracing and observability |
| **Signoz** | Observability | Open-source APM and observability |
| **Grafana** | Visualization | Dashboard and visualization platform |
| **Prometheus** | Monitoring | Time-series database and alerting |
| **Alertmanager** | Alerting | Alert routing and deduplication |
| **Thanos** | Monitoring | Long-term Prometheus storage |
| **Cortex/Mimir** | Monitoring | Horizontal scalable Prometheus |
| **VictoriaMetrics** | Monitoring | Fast, cost-effective monitoring |
| **Netdata** | Monitoring | Real-time infrastructure monitoring |
| **Munin** | Monitoring | Networked resource monitoring |
| **Cacti** | Monitoring | Graphing solution for RRDTool |
| **Zabbix** | Monitoring | Enterprise-class monitoring |
| **Nagios** | Monitoring | Infrastructure monitoring |
| **Icinga** | Monitoring | Open-source monitoring |
| **Checkmk** | Monitoring | Comprehensive IT monitoring |

---

## Endpoint Detection & Response (EDR/XDR)

| Tool | Category | Description |
|------|----------|-------------|
| **CrowdStrike Falcon** | EDR | Cloud-native endpoint protection platform |
| **Microsoft Defender for Endpoint** | EDR | Built-in Windows EDR (MDE) |
| **Cortex XDR** | XDR | Palo Alto Networks extended detection & response |
| **Carbon Black (CB Response/Defense/Protection)** | EDR | VMware Carbon Black endpoint security |
| **SentinelOne** | EDR | Autonomous endpoint protection |
| **Cynet** | XDR | Autonomous breach protection |
| **Cybereason** | EDR | Endpoint detection and response |
| **CrowdStrike Falcon OverWatch** | MDR | Managed threat hunting service |
| **Rapid7 InsightIDR** | SIEM/EDR | Cloud SIEM with endpoint detection |
| **Elastic Endpoint Security** | EDR | Elastic's endpoint protection |
| **Trend Micro Apex One** | EDR | Endpoint protection platform |
| **Sophos Intercept X** | EDR | Next-gen endpoint protection |
| **Kaspersky EDR** | EDR | Endpoint detection and response |
| **Bitdefender GravityZone** | EDR | Unified endpoint security |
| **ESET Enterprise Inspector** | EDR | Endpoint detection and response |

---

## Vulnerability Management & Scanning

| Tool | Category | Description |
|------|----------|-------------|
| **Tenable Nessus** | Vuln Scanner | Industry-leading vulnerability scanner |
| **Tenable.io / Tenable.sc** | Vuln Management | Cloud/on-prem vulnerability management |
| **Rapid7 InsightVM (Nexpose)** | Vuln Management | Vulnerability management with risk scoring |
| **Qualys VMDR** | Vuln Management | Cloud-based vulnerability management |
| **OpenVAS / Greenbone (GVM)** | Vuln Scanner | Open-source vulnerability scanner |
| **Nmap** | Network Scanner | Network discovery and security auditing |
| **Masscan** | Port Scanner | Fastest Internet port scanner |
| **ZMap** | Port Scanner | Fast single-packet network scanner |
| **RustScan** | Port Scanner | Modern port scanner with smart defaults |
| **Naabu** | Port Scanner | Fast port scanner by ProjectDiscovery |
| **Nikto** | Web Scanner | Web server vulnerability scanner |
| **Nuclei** | Template Scanner | Fast vulnerability scanner with templates |
| **Dalfox** | XSS Scanner | Parameter analysis and XSS scanner |
| **FFUF** | Fuzzer | Fast web fuzzer |
| **Gobuster** | Directory Scanner | Directory/file/DNS busting tool |
| **Dirb/Dirbuster** | Directory Scanner | Web content scanner |
| **Feroxbuster** | Directory Scanner | Fast recursive content discovery |
| **WFuzz** | Fuzzer | Web application fuzzer |
| **SQLMap** | SQLi Tool | Automatic SQL injection exploitation |
| **NoSQLMap** | NoSQLi Tool | NoSQL injection exploitation |
| **XSStrike** | XSS Scanner | Advanced XSS detection suite |
| **Commix** | Command Injection | Automated command injection exploitation |
| **TPLMap** | SSTI Scanner | Server-side template injection scanner |
| **SSRFMap** | SSRF Scanner | Automated SSRF discovery |
| **Gopherus** | SSRF Tool | Generate Gopher payloads for SSRF |
| **JWT_Tool / jwt-tool** | JWT Tester | JSON Web Token testing toolkit |
| **OWASP ZAP (ZAPROXY)** | DAST | Dynamic application security testing |
| **Burp Suite** | DAST/Proxy | Web application security testing platform |
| **Postman** | API Testing | API development and testing |
| **Insomnia** | API Testing | API client for testing |
| **Hoppscotch** | API Testing | Open-source API development |
| **Bruno** | API Testing | Open-source API client |

---

## Cloud Security & CSPM

| Tool | Category | Description |
|------|----------|-------------|
| **AWS Security Hub** | CSPM | Centralized security findings |
| **AWS GuardDuty** | Threat Detection | Managed threat detection service |
| **AWS Inspector** | Vuln Scanning | Automated security assessment |
| **AWS Macie** | Data Classification | ML-powered data discovery |
| **AWS Config** | Compliance | Resource configuration tracking |
| **AWS IAM Access Analyzer** | IAM Analysis | Policy analysis for least privilege |
| **Prowler** | CSPM | AWS/Azure/GCP security assessment |
| **ScoutSuite** | CSPM | Multi-cloud security auditing |
| **CloudFox** | Cloud Recon | AWS/Azure attack path enumeration |
| **Pacu** | AWS Exploitation | AWS exploitation framework |
| **CloudSploit** | CSPM | Cloud security posture management |
| **Checkov** | IaC Scanner | Static analysis for Terraform, CloudFormation |
| **tfsec** | IaC Scanner | Static analysis for Terraform |
| **Terrascan** | IaC Scanner | Static analysis for IaC |
| **KICS** | IaC Scanner | Static analysis for Kubernetes, Terraform |
| **OPA Gatekeeper** | Policy Engine | Policy-as-code for Kubernetes |
| **Kyverno** | Policy Engine | Kubernetes native policy management |
| **Trivy** | Container Scanner | Vulnerability, misconfig, secret scanner |
| **Grype** | Container Scanner | Vulnerability scanner for containers |
| **Syft** | SBOM Generator | Software Bill of Materials generator |
| **Cosign** | Signing | Container image signing |
| **Sigstore/fulcio/rekor** | Supply Chain | Software signing and transparency |
| **SLSA/in-toto** | Supply Chain | Supply chain integrity framework |
| **Harbor** | Registry | Container registry with security |
| **Clair/Anchore** | Container Scanner | Container vulnerability scanning |
| **Aqua Security / Twistlock** | Cloud Native | Cloud-native security platform |
| **Sysdig / Falco** | Runtime Security | Container runtime security |
| **Tetragon / Cilium** | eBPF Security | eBPF-based runtime security |
| **kubectl / kubeadm / k3s / k0s / kind / minikube** | K8s Tools | Kubernetes cluster management |
| **k9s / Lens / Rancher** | K8s UI | Kubernetes management interfaces |
| **EKS / AKS / GKE / OpenShift** | Managed K8s | Managed Kubernetes services |

---

## Network Security & Monitoring

| Tool | Category | Description |
|------|----------|-------------|
| **Zeek (Bro)** | NIDS | Network security monitoring |
| **Suricata** | NIDS/IPS | High-performance network IDS/IPS |
| **Snort** | NIDS/IPS | Network intrusion detection/prevention |
| **Arkime (Moloch)** | PCAP Analysis | Large-scale packet capture indexing |
| **Wireshark / tshark** | Packet Analysis | Network protocol analyzer |
| **tcpdump** | Packet Capture | Command-line packet analyzer |
| **ntopng** | Traffic Analysis | Network traffic monitoring |
| **Argus** | Flow Analysis | Network flow analysis |
| **Silk** | Flow Analysis | Network traffic analysis |
| **nProbe** | Flow Export | NetFlow/IPFIX probe |
| **Softflowd** | Flow Export | Software flow exporter |
| **pfSense** | Firewall | Open-source firewall/router |
| **OPNsense** | Firewall | Hardened pfSense fork |
| **iptables/nftables** | Firewall | Linux kernel firewall |
| **Cisco ASA/Firepower** | Firewall | Enterprise firewall |
| **Palo Alto Networks** | NGFW | Next-generation firewall |
| **Fortinet FortiGate** | NGFW | Unified threat management |
| **Check Point** | Firewall | Enterprise security gateway |
| **Juniper SRX** | Firewall | Services gateway |
| **F5 BIG-IP** | ADC/WAF | Application delivery controller |
| **NGINX / HAProxy / Traefik / Caddy** | Reverse Proxy | Load balancing and proxy |
| **Envoy / Istio / Linkerd** | Service Mesh | Service-to-service communication |
| **Kong / APISIX / Tyk / Gravitee / Apigee** | API Gateway | API management platforms |
| **ModSecurity / Coraza / OWASP CRS** | WAF | Web application firewall |
| **OpenResty** | Web Platform | NGINX + Lua for web apps |
| **Cloudflare / Akamai / Fastly** | CDN/WAF | Edge security and performance |

---

## Threat Intelligence & TIP

| Tool | Category | Description |
|------|----------|-------------|
| **MISP** | TIP | Malware Information Sharing Platform |
| **OpenCTI** | TIP | Open Cyber Threat Intelligence platform |
| **TheHive** | Case Management | Scalable incident response platform |
| **Cortex** | Analysis | Observable analysis and enrichment |
| **Shuffle** | SOAR | No-code security automation |
| **Splunk SOAR (Phantom)** | SOAR | Security orchestration & automation |
| **Cortex XSOAR (Demisto)** | SOAR | Security orchestration platform |
| **VirusTotal** | Intelligence | Malware analysis and intelligence |
| **Abuse.ch (URLhaus, FeodoTracker, SSLBL, ThreatFox, MalwareBazaar, YARAify)** | Feeds | Threat intelligence feeds |
| **Hybrid Analysis** | Sandbox | Malware analysis sandbox |
| **Joe Sandbox** | Sandbox | Deep malware analysis |
| **ANY.RUN** | Sandbox | Interactive malware analysis |
| **CAPE / Cuckoo Sandbox** | Sandbox | Automated malware analysis |
| **Detekt** | Analysis | Static analysis platform |
| **InQuest** | Analysis | Deep file inspection |
| **AlienVault OTX** | Feeds | Open threat exchange |
| **Shodan / Censys / ZoomEye / Fofa / Hunter / BinaryEdge / Onyphe / IntelX** | Recon | Internet-wide scanning |
| **SecurityTrails / RiskIQ / PassiveTotal** | Recon | DNS and infrastructure intelligence |
| **Maltego** | Graph Analysis | Link analysis and visualization |
| **SpiderFoot** | OSINT | Automated OSINT collection |
| **theHarvester / Sherlock / Social-Analyzer** | OSINT | Information gathering tools |
| **MITRE ATT&CK / Navigator / D3FEND / ENGAGE / ATLAS / CAR** | Frameworks | Adversary behavior frameworks |

---

## Digital Forensics & Incident Response (DFIR)

| Tool | Category | Description |
|------|----------|-------------|
| **Volatility / Volatility 3** | Memory Forensics | Memory analysis framework |
| **Rekall** | Memory Forensics | Memory forensics framework |
| **RedLine** | Triage | Endpoint triage and collection |
| **FTK / FTK Imager** | Disk Forensics | Forensic toolkit and imaging |
| **Autopsy / Sleuth Kit (TSK)** | Disk Forensics | Open-source digital forensics |
| **X-Ways Forensics** | Disk Forensics | Commercial forensics platform |
| **Kroll Artifact Parser (KAPE)** | Triage | Targeted artifact collection |
| **Chainsaw** | Log Analysis | Sigma-based EVTX analysis |
| **Hayabusa** | Log Analysis | Fast Sigma-based EVTX analysis |
| **EvtxECmd / MFTECmd / PECmd / RECmd / LECmd / JLECmd / AmcacheParser** | Artifact Parsing | Eric Zimmerman's EZ Tools |
| **Timeline Explorer** | Analysis | CSV/JSON timeline visualization |
| **Plaso (log2timeline, psort, psteal)** | Timeline | Super-timeline generation |
| **Timesketch** | Timeline | Collaborative timeline analysis |
| **Hindsight** | Browser Forensics | Chromium browser artifact parsing |
| **BrowserHistoryView / ChromeCacheView / MZCacheView** | Browser Forensics | NirSoft browser tools |
| **SQLite Browser / DB Browser for SQLite** | Database | SQLite database viewer |
| **PhotoRec / Foremost / Scalpel** | File Carving | File recovery from disk images |
| **Binwalk / Firmwalker / Firmadyne** | Firmware Analysis | Firmware extraction and analysis |
| **CHIPSEC** | Firmware Security | Hardware/firmware security assessment |
| **UEFI/BIOS/SPI Flash tools** | Firmware | Bootkit detection and analysis |

---

## Active Directory & Identity Security

| Tool | Category | Description |
|------|----------|-------------|
| **BloodHound / SharpHound / AzureHound** | AD Recon | Graph-based AD attack path analysis |
| **Mimikatz** | Credential Access | Windows credential extraction |
| **Rubeus / Kekeo** | Kerberos | Kerberos ticket manipulation |
| **Impacket** | Protocol | Network protocol implementation |
| **Certipy** | AD CS | AD Certificate Services exploitation |
| **ADFind / ldapdomaindump / ldapsearch** | AD Enumeration | LDAP enumeration tools |
| **PingCastle / Purple Knight** | AD Assessment | AD security posture assessment |
| **NetExec (nxc)** | Lateral Movement | Network authentication and enumeration |
| **CrackMapExec** | Lateral Movement | Post-exploitation toolkit |
| **Responder / PetitPotam / Coercer / PrinterBug** | Coercion | NTLM relay and coercion tools |
| **ntlmrelayx** | Relay | NTLM relay attacks |
| **GraphRunner** | Post-Exploitation | Microsoft Graph API post-exploitation |
| **AADInternals / ROADTools** | Entra ID | Azure AD/Entra ID reconnaissance |
| **CyberArk / BeyondTrust / Delinea / HashiCorp Vault** | PAM | Privileged access management |
| **Okta / Microsoft Entra ID / Azure AD** | Identity | Identity providers |
| **HashiCorp Boundary** | ZTNA | Identity-aware access proxy |

---

## C2 Frameworks & Red Team

| Tool | Category | Description |
|------|----------|-------------|
| **Cobalt Strike** | C2 | Commercial adversary simulation |
| **Brute Ratel (BRc4)** | C2 | Adversary simulation framework |
| **Sliver** | C2 | Open-source C2 framework |
| **Havoc** | C2 | Open-source C2 framework |
| **Covenant** | C2 | .NET C2 framework |
| **Empire / PowerShell Empire** | C2 | PowerShell post-exploitation |
| **Pupy / Shad0w / SilentTrinity / Faction / Merlin / Poseidon / Krypton** | C2 | Various C2 frameworks |
| **Nighthawk / Bokoblin / TrevorC2 / Pandora / Salsa** | C2 | Additional C2 frameworks |
| **Metasploit / msfconsole / Armitage** | Exploitation | Penetration testing framework |
| **Atomic Red Team** | Testing | Atomic test execution |
| **Invoke-AtomicRedTeam** | Testing | PowerShell atomic test runner |
| **Stratus Red Team** | Cloud Testing | Cloud attack technique detonation |

---

## Container & Kubernetes Security

| Tool | Category | Description |
|------|----------|-------------|
| **Trivy** | Scanner | Comprehensive container/IaC scanner |
| **Grype / Syft** | Scanner/SBOM | Vulnerability scanning and SBOM |
| **Cosign / Sigstore / Rekor / Fulcio** | Supply Chain | Signing and transparency |
| **SLSA / in-toto** | Supply Chain | Supply chain integrity |
| **Harbor** | Registry | Secure container registry |
| **Clair / Anchore / Aqua / Twistlock** | Scanner | Container vulnerability scanning |
| **Sysdig / Falco / Tetragon / Cilium** | Runtime | eBPF-based runtime security |
| **OPA Gatekeeper / Kyverno** | Policy | Kubernetes admission control |
| **kubectl / kubeadm / k3s / k0s / kind / minikube / microk8s / k3d** | K8s Mgmt | Cluster management tools |
| **k9s / Lens / Rancher / OpenShift / OKD** | K8s UI | Management interfaces |
| **EKS / AKS / GKE** | Managed K8s | Cloud managed Kubernetes |
| **Helm / Kustomize / ArgoCD / Flux / Tekton** | GitOps/CD | Deployment and CI/CD |

---

## Password Cracking & Credential Tools

| Tool | Category | Description |
|------|----------|-------------|
| **Hashcat** | Password Cracking | GPU-accelerated password recovery |
| **John the Ripper / Johnny** | Password Cracking | Multi-platform password cracker |
| **Hydra / Medusa / Ncrack / Patator** | Brute Force | Network login crackers |
| **CeWL / Crunch / CUPP / Mentalist** | Wordlist Gen | Custom wordlist generators |
| **RainbowCrack / rtgen / rcrack / rcracki / rtcrack** | Rainbow Tables | Time-memory trade-off cracking |

---

## Phishing & Social Engineering

| Tool | Category | Description |
|------|----------|-------------|
| **Gophish / GoPhish** | Phishing | Open-source phishing framework |
| **King Phisher** | Phishing | Phishing campaign toolkit |
| **Phishing Frenzy** | Phishing | Ruby on Rails phishing framework |
| **PhishMe / Cofense** | Phishing | Enterprise phishing simulation |
| **KnowBe4** | Training | Security awareness training |
| **Proofpoint / Mimecast / Barracuda** | Email Security | Secure email gateways |
| **EvilGinx3** | AiTM | Adversary-in-the-middle phishing |

---

## Web Application Security Testing

| Tool | Category | Description |
|------|----------|-------------|
| **Burp Suite** | DAST/Proxy | Professional web app testing |
| **OWASP ZAP (ZAPROXY)** | DAST | Free web app scanner |
| **Nikto** | Scanner | Web server vulnerability scanner |
| **Nuclei** | Template Scanner | Vulnerability scanner with templates |
| **FFUF / Gobuster / Dirb / Feroxbuster** | Fuzzing | Content discovery |
| **SQLMap / NoSQLMap** | Injection | SQL/NoSQL injection automation |
| **XSStrike / Commix / TPLMap / SSRFMap / Gopherus** | Specialized | XSS, CMDi, SSTI, SSRF tools |
| **JWT_Tool / jwt-tool** | JWT Testing | JSON Web Token analysis |

---

## Infrastructure & DevOps Security

| Tool | Category | Description |
|------|----------|-------------|
| **Terraform / Packer / Vagrant** | IaC | Infrastructure provisioning |
| **Ansible** | Config Mgmt | Configuration management |
| **Docker / Podman / containerd / cri-o / runc / crun / runv / kata / gvisor / firecracker** | Containers | Container runtimes |
| **Kubernetes (k8s) / k3s / k0s / kind / minikube / microk8s / k3d** | Orchestration | Container orchestration |
| **Helm / Kustomize / ArgoCD / Flux / Tekton** | GitOps | Continuous deployment |
| **Vault / Consul / Nomad / Boundary / Waypoint** | HashiCorp | Secrets, service mesh, orchestration |
| **AWS / Azure / GCP / Cloudflare / Akamai / Fastly / Vercel / Netlify / Heroku / DigitalOcean / Linode / Vultr / Hetzner / Scaleway / OVH / Rackspace** | Cloud | Cloud providers and CDNs |

---

## Mobile & IoT Security

| Tool | Category | Description |
|------|----------|-------------|
| **MobSF** | Mobile SAST | Mobile security framework |
| **Frida / Objection** | Dynamic Analysis | Runtime instrumentation |
| **JADX / apktool** | Reverse Engineering | Android decompilation |
| **Ghidra / IDA Pro / Binary Ninja / radare2 / Cutter** | Reverse Engineering | Multi-platform reverse engineering |
| **Cellebrite UFED / ALEAPP / iLEAPP / MEAT / libimobiledevice** | Mobile Forensics | Mobile device acquisition |
| **Ubertooth One / nRF52840 / bleak / crackle** | BLE Security | Bluetooth analysis |
| **binwalk / firmwalker / firmadyne** | Firmware | Firmware analysis |

---

## Cryptography & PKI

| Tool | Category | Description |
|------|----------|-------------|
| **OpenSSL / LibreSSL / BoringSSL / GnuTLS / mbedTLS / wolfSSL / NSS / JSSE / Schannel / Secure Transport** | TLS Libraries | Cryptographic libraries |
| **HashiCorp Vault** | Secrets Mgmt | Secrets management |
| **Hardware Security Modules (HSM) / PKCS#11 / SoftHSM2 / AWS CloudHSM / YubiHSM2** | HSM | Hardware key storage |
| **Let's Encrypt / certbot / ACME.sh** | Certificate Mgmt | Automated certificate management |
| **OpenSSL PKI / CFSSL / Smallstep** | PKI | Certificate authority tools |
| **Sigstore / Cosign / Fulcio / Rekor** | Supply Chain | Keyless signing and transparency |

---

## Compliance & Audit

| Tool | Category | Description |
|------|----------|-------------|
| **kube-bench** | Compliance | CIS Kubernetes Benchmark |
| **kube-hunter / Kubescape / Peirates** | K8s Pentest | Kubernetes penetration testing |
| **Docker Bench for Security** | Compliance | CIS Docker Benchmark |
| **Lynis / Tiger** | Auditing | Linux/Unix security auditing |
| **OpenSCAP / SCAP** | Compliance | Security Content Automation Protocol |
| **Chef InSpec / Serverspec** | Compliance | Infrastructure testing |
| **Prowler / ScoutSuite / CloudSploit** | Cloud Audit | Multi-cloud compliance |

---

## Additional Notable Tools

| Tool | Category | Description |
|------|----------|-------------|
| **OSSEC / Wazuh** | HIDS | Host-based intrusion detection |
| **AIDE / Tripwire / Samhain** | FIM | File integrity monitoring |
| **GMER / rkhunter / chkrootkit / RootkitRevealer** | Rootkit Detection | Rootkit scanners |
| **Velociraptor** | DFIR | Endpoint forensics and hunting |
| **osquery** | Endpoint Visibility | SQL-based endpoint querying |
| **Autoruns / Procmon / Process Hacker** | Sysinternals | Windows system analysis |
| **Sysmon** | Logging | Enhanced Windows logging |
| **PowerShell Empire / GraphRunner** | Post-Exploitation | AD/Entra ID post-exploitation |
| **Sharp* tools (SharpHound, SharpDPAPI, SharpChrome, etc.)** | AD Tools | C# AD enumeration tools |

---

## Summary Statistics

- **Total Skills Analyzed**: 200+
- **Unique Tools Identified**: 300+
- **Categories Covered**: 20+
- **Primary Focus Areas**: 
  - SIEM/SOAR: 15+ tools
  - EDR/XDR: 10+ tools
  - Vulnerability Management: 25+ tools
  - Cloud Security: 30+ tools
  - Network Security: 25+ tools
  - Threat Intelligence: 20+ tools
  - DFIR: 20+ tools
  - Active Directory: 15+ tools
  - C2/Red Team: 15+ tools
  - Container/K8s Security: 25+ tools
  - Password/Phishing/Web/Mobile: 40+ tools

---

*Generated from analysis of cybersecurity skills in the agent system. This inventory represents tools mentioned across various offensive, defensive, and compliance skill modules.*