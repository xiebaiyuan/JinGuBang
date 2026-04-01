# Net Tools

用于网络连通性基础排查与域名解析信息收集。

| 工具名 | 用途 | 使用示例 | 依赖 | 平台支持 | 风险级别 |
|---|---|---|---|---|---|
| `port_checker.html` | 浏览器端端口可达性检测 | 直接在浏览器打开 `net_tools/port_checker.html` | 浏览器 | 跨平台 | 低 |
| `port_scan_tcp.py` | 轻量 TCP 端口扫描 | `python3 net_tools/port_scan_tcp.py --host 127.0.0.1 --top-common` | Python 标准库 | 跨平台 | 中 |
| `domain_dns_report.py` | 域名 DNS 记录摘要（A/AAAA/CNAME/MX/NS） | `python3 net_tools/domain_dns_report.py -d example.com --types A,MX,NS` | Python 标准库，`dig` 可选 | 跨平台 | 低 |

## 何时使用

- 快速看本机服务端口开放状态，用 `port_scan_tcp.py`。
- 域名问题排查先跑 `domain_dns_report.py`。

## 安全说明

- 网络扫描工具仅用于你有明确授权的目标环境。

## 相关文档

- `net_tools/port_checker_readme.md`
