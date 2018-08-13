import ipaddress

import curio

from ibd import *

# FIXME
VERSION = b'\xf9\xbe\xb4\xd9version\x00\x00\x00\x00\x00j\x00\x00\x00\x9b"\x8b\x9e\x7f\x11\x01\x00\x0f\x04\x00\x00\x00\x00\x00\x00\x93AU[\x00\x00\x00\x00\x0f\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0f\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00rV\xc5C\x9b:\xea\x89\x14/some-cool-software/\x01\x00\x00\x00\x01'

TIMEOUT = 3

connected_to = []


async def loop(sock, a):
    while True:
        try:
            pkt = await Packet.async_from_socket(sock)
            print(f"received {pkt.command} from {a}")
            if pkt.command == b"version":
                msg = VersionMessage.from_bytes(pkt.payload)
                # TODO send verack
                res = Packet(command=b"verack", payload=b"")
                await sock.send(res.to_bytes())
            elif pkt.command == b"verack":
                msg = VerackMessage.from_bytes(pkt.payload)
                await curio.sleep(.5)
                getaddr = Packet(command=b"getaddr", payload=b"")
                await sock.send(getaddr.to_bytes())
            elif pkt.command == b"addr":
                msg = AddrMessage.from_bytes(pkt.payload)

                for address in msg.address_list[:3]:
                    tup = (address.ip.compressed, address.port)
                    print("connecting to", tup)
                    try:
                        await curio.spawn(connect_async, tup)
                    except Exception as e:
                        print(e)
                        print("failed connecting to", tup)
        except RuntimeError as e:
            print(e)
            continue
        except Exception as e:
            print("Unhandled exception:", e)
            break


async def connect_async(address):
    ipv4 = ip_address(address[0]).version == 4
    param = curio.socket.AF_INET if ipv4 else curio.socket.AF_INET6
    sock = curio.socket.socket(param)
    # curio.timeout_after(sock.connect, addr)
    await sock.connect(address)
    await sock.send(VERSION)
    connected_to.append(address)
    await loop(sock, address)
    connected_to.remove(address)  # FIXME: this won't happen if there's an exception
    await sock.close()


async def main(address):
    await curio.spawn(connect_async, address)


if __name__ == "__main__":
    address = ("46.226.18.135", 8333)
    curio.run(connect_async, address)