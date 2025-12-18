# VS1984_Dashboard
用 Python 实现的 VS1984 简易控制台演示

[English](README.md) | [中文](README.zh-CN.md)

## VS1984的安装

访问并[下载DEB文件](https://github.com/YangV77/VS1984/releases/latest)

``` base
# install vs1984
sudo dpkg -i vs1984.deb

# To start VS1984 per-user daemon
systemctl --user daemon-reload
systemctl --user enable --now vs1984d.service

# To check status:
systemctl --user status vs1984d.service

```

## 配置打开daemon
编辑配置文件, 默认路径 ~/.local/share/vs1984/cnf/config.xbc

添加: "daemon": {"startup": true, "token": "123123"},
"startup": true 会打开daemon以允许 dashboard 访问
"token": "<user_set_DAEMONSVC_TOKEN>" 会设置 dashboard 访问VS1984主程序的token

## VS1984_Dashboard 设置 DAEMONSVC_TOKEN
xbcpy/config.py中:
    token = os.getenv("DAEMONSVC_TOKEN") or "<user_set_DAEMONSVC_TOKEN>"
设置 DAEMONSVC_TOKEN

## 安装和配置依赖

```bash
pip install -e .
pip install -e ".[dashboard]"
```

## 启动 Dashboard 服务

```bash
export XBCPY_ADMIN_TOKEN="your-strong-browser-access-token"
uvicorn dashboard.app:app --host 0.0.0.0 --port 18080
```

## 浏览器访问

浏览器从其他机器访问：
http://<这台机器IP>:18080/?t=your-strong-browser-access-token

## [命令手册](https://vs1984.com/zh/docs/manual/)
