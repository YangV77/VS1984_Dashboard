# VS1984_Dashboard
A simple console demo of VS1984 implemented in Python

[English](README.md) | [Chinese](README.zh-CN.md)

## Installing VS1984

Visit and [download the DEB file](https://github.com/YangV77/VS1984/releases/latest)

```base

# install vs1984

sudo dpkg -i vs1984.deb

# To start VS1984 per-user daemon

systemctl --user daemon-reload

systemctl --user enable --now vs1984d.service

# To check status:

systemctl --user status vs1984d.service

```

## Configure daemon to open
Edit the configuration file, default path `~/.local/share/vs1984/cnf/config.xbc`

Add: `"daemon": {"startup": true, "token": "<user_set_DAEMONSVC_TOKEN>"},`

`"startup": true` will enable the daemon to allow dashboard access.

`"token": "<user_set_DAEMONSVC_TOKEN>"` will set the token for dashboard access to the VS1984 main program.

## Setting DAEMONSVC_TOKEN in VS1984_Dashboard

In `xbcpy/config.py`:

`token = os.getenv("DAEMONSVC_TOKEN") or "<user_set_DAEMONSVC_TOKEN>" This sets DAEMONSVC_TOKEN.`

## Installing and Configuring Dependencies

```bash
pip install -e .

pip install -e ".[dashboard]"

```

## Starting the Dashboard Service

```bash
export XBCPY_ADMIN_TOKEN="your-strong-browser-access-token"
uvicorn dashboard.app:app --host 0.0.0.0 --port 18080

```

## Browser Access

Accessing from another machine:

`http://<this machine's IP>:18080/?t=your-strong-browser-access-token`

[command manual](https://vs1984.com/en/docs/manual/)