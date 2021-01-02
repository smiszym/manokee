import eventlet.wsgi
from ipaddress import ip_address
import logging
from manokee.web.app import app
from netifaces import interfaces, ifaddresses, AF_INET
import qrcode


def ipv4_addresses():
    result = []
    for interface in interfaces():
        links = ifaddresses(interface).get(AF_INET, [])
        for link in links:
            addr = ip_address(link["addr"])
            if not addr.is_loopback:
                result.append(addr)
    return result


if __name__ == "__main__":
    port = 5000
    addresses = ipv4_addresses()
    assert len(addresses) > 0
    print("OPEN MANOKEE IN A BROWSER AT:")
    for address in addresses:
        url = f"http://{address}:{port}/"
        print(url)
        qr = qrcode.QRCode()
        qr.add_data(url)
        qr.print_ascii()
    eventlet.wsgi.server(
        eventlet.listen(("", port)), app, log=logging.getLogger("webserver")
    )
