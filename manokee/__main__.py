import eventlet.wsgi
from ipaddress import ip_address
from manokee.web.app import app
from netifaces import interfaces, ifaddresses, AF_INET


def ipv4_addresses():
    result = []
    for interface in interfaces():
        links = ifaddresses(interface).get(AF_INET, [])
        for link in links:
            addr = ip_address(link['addr'])
            if not addr.is_loopback:
                result.append(addr)
    return result


if __name__ == '__main__':
    port = 5000
    addresses = ipv4_addresses()
    assert len(addresses) > 0
    if len(addresses) == 1:
        print(f"OPEN MANOKEE IN A BROWSER AT http://{addresses[0]}:{port}/")
    else:
        print("OPEN MANOKEE IN A BROWSER AT:")
        for address in addresses:
            print(f"http://{address}:{port}/")
    eventlet.wsgi.server(eventlet.listen(('', port)), app)
