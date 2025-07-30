# 示例：使用 v2ray_util 库解析（需安装 pip install v2ray_util）
from v2ray_util import GeoSite, GeoIP

# 解析 geosite.dat
geosite = GeoSite.load("geosite.dat")
print(geosite.get_domains("cn"))  # 输出中国大陆域名列表

# 解析 geoip.dat
geoip = GeoIP.load("geoip.dat")
print(geoip.get_ips("CN"))  # 输出中国IP段
