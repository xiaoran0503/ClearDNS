# 分流资源文件

本目录下的脚本用于拉取合并上游数据，生成以下对应的资源文件：

+ `gfwlist.txt` ：常见的被墙域名

+ `chinalist.txt` ：服务器在国内的常见域名

+ `china-ip.txt` ：国内 IP 段数据（CIDR 格式）

## 运行说明

在运行前，请检查 `netaddr` 模块是否安装，若无则执行以下命令：

```bash
pip3 install netaddr
```

> 由于 Python 的性能问题，脚本对 CIDR 的合并效率偏低，获取国内 IP 段可能花费较长时间。

```bash
$ ./gfwlist.py
$ ./china-ip.py
$ ./chinalist.py
$ ls
china-ip.txt  chinalist.txt  gfwlist.txt  ...
```

## 上游信息

### gfwlist

```yaml
https://github.com/gfwlist/gfwlist/raw/master/gfwlist.txt

https://github.com/hq450/fancyss/raw/master/rules/gfwlist.conf

https://github.com/Loukky/gfwlist-by-loukky/raw/master/gfwlist.txt

https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/gfw.txt
```

### china-ip

```yaml
https://gaoyifan.github.io/china-operator-ip/

https://github.com/misakaio/chnroutes2/raw/master/chnroutes.txt

https://github.com/17mon/china_ip_list/raw/master/china_ip_list.txt

https://github.com/metowolf/iplist/raw/master/data/special/china.txt
```

### chinalist

```yaml
https://github.com/hq450/fancyss/raw/master/rules/WhiteList_new.txt'

https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/direct-list.txt'

https://github.com/felixonmars/dnsmasq-china-list/raw/master/accelerated-domains.china.conf'
```

## 下发地址（GitHub Actions 自动维护）

> 纯文本资源由本仓库 GitHub Actions 每日自动生成，可随时拉取最新数据。

文本下载链接（GitHub 直连）：

+ `gfwlist.txt` ：`https://raw.githubusercontent.com/xiaoran0503/ClearDNS/master/assets/gfwlist.txt`
+ `china-ip.txt` ：`https://raw.githubusercontent.com/xiaoran0503/ClearDNS/master/assets/china-ip.txt`
+ `chinalist.txt` ：`https://raw.githubusercontent.com/xiaoran0503/ClearDNS/master/assets/chinalist.txt`

> 如果下载工具不支持压缩，可以使用以下预压缩文件，加快下载速度。

压缩资源链接（`ghfast.top` 镜像加速）：

+ `gfwlist.txt` ：`https://ghfast.top/https://raw.githubusercontent.com/xiaoran0503/ClearDNS/master/assets/gfwlist.txt.xz`
+ `china-ip.txt` ：`https://ghfast.top/https://raw.githubusercontent.com/xiaoran0503/ClearDNS/master/assets/china-ip.txt.xz`
+ `chinalist.txt` ：`https://ghfast.top/https://raw.githubusercontent.com/xiaoran0503/ClearDNS/master/assets/chinalist.txt.xz`

> 资源文件由本仓库 GitHub Actions 每日自动生成并提交（含 `.txt` 与 `.txt.xz` 双份），构建期与运行期均从本仓库拉取。
