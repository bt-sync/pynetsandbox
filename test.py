#!/usr/bin/python3

import unittest
import logging

from netsandbox import NetworkSandbox, LocalNetworkSandbox

logging.basicConfig(level=logging.DEBUG)


class NAT(unittest.TestCase):
    def test_namespace(self):
        with NetworkSandbox() as ns:
            for a in ["10.1.0.1", "10.1.0.2", "10.0.0.2", "127.0.0.1"]:
                p, _ = ns.spawn("ping {} -c 3".format(a))
                if p.wait(timeout=10) != 0:
                    raise OSError('destination %s is unreachable' % a)


class CustomNAT(unittest.TestCase):
    def test_net_1(self):
        with NetworkSandbox('172.99.56.0/24') as ns:
            for a in ["172.99.56.1", "172.99.56.2", "10.0.0.2", "127.0.0.1"]:
                p, _ = ns.Popen(["ping", a, "-c", "3"])
                if p.wait(timeout=10) != 0:
                    raise OSError('destination %s is unreachable' % a)


#class PortMapping(unittest.TestCase):
    # def test_mappings(self):
    #     import subprocess
    #     import time
    #     with NetworkSandbox() as ns:
    #         mapping = {'tcp': {8000: 8000}}
    #         p = ns.spawn("python3 -m http.server 8000", mapping)
    #         subprocess.call("wget http://10.1.0.2:8000 -O -", shell=True)
    #         p.kill()
    #         p.wait(timeout=3)


class WAN(unittest.TestCase):
    def test_namespace(self):
        with NetworkSandbox(simulate_wan=True) as ns:
            for a in ["10.1.0.1", "10.1.0.2", "10.0.0.2", "127.0.0.1"]:
                p, _ = ns.spawn("ping {} -c 5".format(a))
                if p.wait(timeout=30) != 0:
                    raise OSError('destination %s is unreachable' % a)


class LAN(unittest.TestCase):
    def test_namespace(self):
        with LocalNetworkSandbox() as ns:
            for a in ["10.1.0.2", "10.1.0.1"]:
                p, _ = ns.spawn("ping {} -c 3".format(a))
                if p.wait(timeout=10) != 0:
                    raise OSError('destination %s is unreachable' % a)

    def test_namespace2(self):
        with LocalNetworkSandbox() as ns:
            for p, _ in [ns.spawn("ping 10.1.0.3 -c 10"), ns.spawn("ping 10.1.0.2 -c 10")]:
                if p.wait(timeout=30) != 0:
                    raise OSError('destination is unreachable')


if __name__ == '__main__':
    unittest.main()
