from urllib.parse import urlparse


def xaddr_to_ip_port(xaddr):
    parsed = urlparse(xaddr)
    return parsed.hostname, parsed.port or 80


def get_stream_uri(ip, port, username, password, profile_index=0):
    """Connect to an ONVIF device and return (rtsp_url_with_credentials, device_name)."""
    from onvif import ONVIFCamera

    cam = ONVIFCamera(ip, port, username, password)
    media_service = cam.create_media_service()
    profiles = media_service.GetProfiles()
    if not profiles:
        raise RuntimeError("Camera nu a returnat niciun profil media.")
    profile = profiles[profile_index]

    request = media_service.create_type("GetStreamUri")
    request.ProfileToken = profile.token
    request.StreamSetup = {"Stream": "RTP-Unicast", "Transport": {"Protocol": "RTSP"}}
    stream_uri = media_service.GetStreamUri(request).Uri

    device_name = ip
    try:
        info = cam.devicemgmt.GetDeviceInformation()
        device_name = f"{info.Manufacturer} {info.Model}"
    except Exception:
        pass

    if username:
        parsed = urlparse(stream_uri)
        netloc = f"{username}:{password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        stream_uri = parsed._replace(netloc=netloc).geturl()

    return stream_uri, device_name
