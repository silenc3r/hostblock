# Hostblock

**Automatically generate and manage an /etc/hosts file to block known ads, malware, and other unwanted domains.**

Hostblock downloads hosts files from specified URLs, merges them
into single file (while removing duplicates) and saves them to
`/etc/hosts`.

Repository includes a systemd service and timer file to keep the blocklist up to date automatically.

## Installation
```
git clone https://github.com/silenc3r/hostblock
make
sudo make install
sudo systemctl enable --now hostblock-update.timer
```

## Usage
```
usage: hostblock [-h] [-r | -c | -u | -a URL] [--config CONFIG]

options:
  -h, --help           show this help message and exit
  -r                   refresh cache
  -c                   copy cached hosts to /etc/hosts
  -u                   update /etc/hosts
  -a URL, --allow URL  temporarily unblock url
  --config CONFIG      custom config file
```

Use `hostblock -u` to download the blockilsts and create new `/etc/hosts` file. It is equivalent to running `hostblock -r` followed by `hostblock -c`.

`hostblock -r` downloads all the blocklists without updating hosts file.

`hostblock -c` is useful for blocking temporarily allowed domains
without having to re-download all the hostlists.

## Configuration
All configuration is done inside `/etc/hostblock.conf` file (or custom file when invoked with `hostblock --config=<custom-config-file>`).

There are 3 configurable variables:
- `blocklists` - a list of blocklist providers
- `allow_urls` - a list of url's that should not be blocked
- `block_urls` - a list of additional urls that should be blocked

All urls in configuration file should reside in separate line.

Note: `block_urls` overrides `allow_urls`.