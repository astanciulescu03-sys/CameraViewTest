import concurrent.futures
import ipaddress
import socket


def get_local_subnet():
    """Best-effort detection of the local /24 subnet based on the primary outbound IP."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()
    network = ipaddress.ip_network(local_ip + "/24", strict=False)
    return local_ip, network


def discover_onvif(timeout=4):
    """Discover ONVIF devices via WS-Discovery multicast.

    Returns [] instead of raising if the optional WSDiscovery dependency
    is missing, so the app still works via the RTSP port-scan fallback.
    """
    results = []
    try:
        from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
    except Exception:
        return results

    wsd = WSDiscovery()
    wsd.start()
    try:
        services = wsd.searchServices(timeout=timeout)
        for service in services:
            xaddrs = service.getXAddrs()
            if not xaddrs:
                continue
            results.append(
                {
                    "xaddr": xaddrs[0],
                    "types": [str(t) for t in service.getTypes()],
                    "scopes": [str(sc) for sc in service.getScopes()],
                }
            )
    finally:
        wsd.stop()
    return results


def scan_port(ip, port, timeout=0.3):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((str(ip), port)) == 0
    except Exception:
        return False


def scan_subnet_for_rtsp(network=None, port=554, max_workers=100, progress_cb=None):
    """Probe every host in a /24 subnet for an open RTSP port."""
    if network is None:
        _, network = get_local_subnet()

    hosts = list(network.hosts())
    found = []

    def check(ip):
        return str(ip) if scan_port(ip, port) else None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check, ip): ip for ip in hosts}
        done = 0
        for future in concurrent.futures.as_completed(futures):
            done += 1
            if progress_cb:
                progress_cb(done, len(hosts))
            result = future.result()
            if result:
                found.append(result)

    return sorted(found, key=lambda ip: tuple(int(p) for p in ip.split(".")))
