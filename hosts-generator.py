#!/usr/bin/python3

import argparse
import concurrent.futures
import shutil
import subprocess
import sys
import urllib.request

# do not edit these!
HOST_CACHE_DIR = None
CONFIG_FILE = None

BLOCKLISTS = []
ALLOW_URLS = []
BLOCK_URLS = []


def read_config():
    if not CONFIG_FILE:
        raise ValueError("Config file not found!")

    config = {}
    with open(CONFIG_FILE) as f:
        current_section = None
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue  # Skip comments and empty lines
            if line.endswith("="):
                current_section = line[:-1].strip()
                config[current_section] = []
            else:
                config[current_section].append(line)

    global BLOCKLISTS, ALLOW_URLS, BLOCK_URLS
    BLOCKLISTS = config["blocklists"]
    if "allow_urls" in config:
        ALLOW_URLS = config["allow_urls"]
    if "block_urls" in config:
        BLOCK_URLS = config["block_urls"]


def url_strip(url):
    url = url.strip()
    if url.startswith("https://"):
        url = url[8:]
    if url.startswith("http://"):
        url = url[7:]
    if url.startswith("www."):
        url = url[4:]
    return url


def get_hostname():
    hostname = subprocess.check_output("hostname").strip().decode()
    return hostname


def load_url(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as conn:
        return conn.read()


def parse_hosts(text_bytes):
    result = []
    text = text_bytes.decode()
    for line in text.splitlines():
        if not line.startswith("#"):
            # elements should be separated by a single space
            line = " ".join(line.split())
            # we don't care about comments
            hostline = line.split("#")[0].strip()
            if len(hostline) == 0:
                continue
            hostline = hostline.replace("127.0.0.1", "0.0.0.0")
            result.append(hostline)
    return result


def get_host_list(urls, timeout=5):
    responses = []

    max_workers = len(urls)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(load_url, url, timeout) for url in urls]
        for future in concurrent.futures.as_completed(futures):
            data = future.result()
            responses.append(data)

    result = set()
    for r in responses:
        hosts = parse_hosts(r)
        result.update(hosts)

    return sorted(result)


def filter_allowed(hosts, alist):
    if not alist:
        return hosts

    allowed = map(url_strip, alist)
    allowed = set(allowed)
    result = []
    for h in hosts:
        url = h.split(maxsplit=1)[1]
        if url_strip(url) not in allowed:
            result.append(h)

    return result


def get_custom_urls():
    custom_urls = []

    for url in BLOCK_URLS:
        url = url_strip(url)
        if url:
            custom_urls.append(f"0.0.0.0 {url}")
            custom_urls.append(f"0.0.0.0 www.{url}")

    return custom_urls


def download():
    output = "hosts"
    if HOST_CACHE_DIR:
        output = f"{HOST_CACHE_DIR}/hosts"

    hosts = get_host_list(BLOCKLISTS)
    hosts = filter_allowed(hosts, ALLOW_URLS)
    hostname = get_hostname()

    with open(output, "w") as f:
        f.write(f"127.0.0.1 localhost {hostname}\n")
        f.write(f"127.0.1.1 {hostname}\n")
        f.write("\n")

        for entry in hosts:
            f.write(f"{entry}\n")

        custom = get_custom_urls()
        if custom:
            f.write("\n# CUSTOM URLS\n")
            for entry in custom:
                f.write(f"{entry}\n")


def copy():
    if not HOST_CACHE_DIR:
        raise ValueError("HOST_CACHE_DIR is not set!")
    hosts = f"{HOST_CACHE_DIR}/hosts"
    shutil.copy2(hosts, "/etc/hosts")


def allow(url):
    if not HOST_CACHE_DIR:
        raise ValueError("HOST_CACHE_DIR is not set!")
    allowed_url = url_strip(url)
    hosts_file = "/etc/hosts"
    blocked = []
    with open(hosts_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                # perserve empty lines
                blocked.append("")
                continue
            current_url = line.split(maxsplit=1)[1]
            current_url = url_strip(current_url)
            if current_url != allowed_url:
                # current_url should be blocked
                blocked.append(line)

    with open("/etc/hosts", "w") as f:
        for entry in blocked:
            f.write(f"{entry}\n")


def update():
    download()
    copy()


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", help="refresh cache", action="store_true")
    group.add_argument(
        "-c", help="copy cached hosts to /etc/hosts", action="store_true"
    )
    group.add_argument("-u", help="update /etc/hosts", action="store_true")
    group.add_argument("-a", "--allow", help="temporarily unblock url", dest="url")
    parser.add_argument("--config", help="custom config file")

    args = parser.parse_args()

    if args.config:
        global CONFIG_FILE
        CONFIG_FILE = args.config

    try:
        read_config()
    except ValueError as e:
        sys.stderr.write(f"Error: {e}")
        exit(1)

    if args.u:
        try:
            update()
        except ValueError as e:
            sys.stderr.write(f"Error: {e}")
            exit(1)
    elif args.r:
        download()
    elif args.c:
        try:
            copy()
        except ValueError as e:
            sys.stderr.write(f"Error: {e}")
            exit(1)
    elif args.url:
        try:
            allow(args.url)
        except ValueError as e:
            sys.stderr.write(f"Error: {e}")
            exit(1)
    else:
        parser.print_help(sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
