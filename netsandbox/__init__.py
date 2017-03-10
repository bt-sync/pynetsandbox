import subprocess
import os
import binascii
import random
import logging
from ipaddress import IPv4Network

logger = logging.getLogger(__name__)


class NetworkNamespace(object):

    def __init__(self, name):
        self.name = name
        subprocess.check_output("ip netns add " + self.name, shell=True)

    def release(self):
        subprocess.check_output("ip netns delete " + self.name, shell=True)

    def call(self, cmds):
        for cmd in cmds:
            cmd = "ip netns exec %s %s" % (self.name, cmd)
            logger.debug(cmd)
            subprocess.check_output(cmd, shell=True)

    def spawn(self, cmd):
        cmd = "ip netns exec %s %s" % (self.name, cmd)
        logger.debug(cmd)
        return subprocess.Popen(cmd, shell=True)


class NetworkSandbox(object):

    def __init__(self, subnet='10.1.0.0/16'):
        self.token = binascii.b2a_hex(os.urandom(4)).decode()
        self.namespaces = []
        self.counter = 1
        self.subnet = IPv4Network(subnet)
        self.hosts_pool = self.subnet.hosts() 
        self.default_gw = self.get_next_address()
        
        self.patterns = {
            'token': self.token,
            'subnet': self.subnet.compressed,
            'subnet_prefix': self.subnet.prefixlen,
            'default_gw': self.default_gw,
        }

        logger.debug('Subnet: %s, default gateway: %s', self.subnet.compressed, self.default_gw)

        if not self._sanity_check():
            raise OSError('IP forwarding is not enabled in the kernel. Check https://www.kernel.org/doc/Documentation/networking/ip-sysctl.txt')

        self.setup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
        return self

    @staticmethod
    def _sanity_check():
        return open('/proc/sys/net/ipv4/ip_forward').read().strip() == '1'

    def get_next_address(self, with_prefix=False):
        return "%s" % (next(self.hosts_pool).compressed) + ('/%d' % self.subnet.prefixlen if with_prefix else '')

    def call(self, cmds, check=True):
        cmds = [i.format(**self.patterns) for i in cmds]

        if check:
            for cmd in cmds:
                logger.debug(cmd)
                subprocess.check_output(cmd, shell=True)
        else:
            for cmd in cmds:
                logger.debug(cmd)
                subprocess.call(cmd, shell=True)

    def setup(self):

        cmd = [
            "brctl addbr br-router-{token}",
            "ip link set up br-router-{token}",
            "ip addr add {default_gw}/{subnet_prefix} dev br-router-{token}",
            "iptables -A INPUT -d {default_gw} -p icmp -j ACCEPT"
        ]

        self.call(cmd)

    def release(self):
        for n in self.namespaces:
            n.release()

        self.call(["ip link del br-router-{token}"], check=False)

    def spawn(self, command):
        router_ns = NetworkNamespace(
            "%s_router%d" % (self.token, self.counter))
        process_ns = NetworkNamespace(
            "%s_process%d" % (self.token, self.counter))

        self.namespaces.append(router_ns)
        self.namespaces.append(process_ns)

        def preprocess(cmds):
            sub = {
                'router_ns': router_ns.name,
                'process_ns': process_ns.name,
                'i': self.counter,
            }
            sub.update(self.patterns)
            return [i.format(**sub) for i in cmds]

        cmd = [
            "ip link add r{i}-{token} type veth peer name wan",
            "ip link set up r{i}-{token}",
            "brctl addif br-router-{token} r{i}-{token}",
            "ip link set wan netns {router_ns}",
        ]

        self.call(preprocess(cmd))

        cmd = [
            "ip link set up lo",

            "ip link set up wan",
            "ip addr add %s  dev wan" % self.get_next_address(with_prefix=True),
            "ip route add default via {default_gw}",
            "ip link add to_process type veth peer name to_router",
            "ip link set to_router netns {process_ns}",
            "ip addr add 10.0.0.1/24 dev to_process",
            "ip link set up to_process",

            "iptables -A INPUT -p icmp -j ACCEPT",
            "iptables -P INPUT DROP",
            "iptables -t nat -A POSTROUTING -o wan -j MASQUERADE",
            "iptables -A FORWARD -o wan -j ACCEPT",
            "iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT",
        ]
        router_ns.call(preprocess(cmd))

        cmd = [
            "ip link set up lo",

            "ip addr add 10.0.0.2/24 dev to_router",
            "ip link set up to_router",
            "ip route add default via 10.0.0.1",

            "iptables -P INPUT ACCEPT",
            "iptables -P OUTPUT ACCEPT",
            "iptables -P FORWARD DROP"
        ]
        process_ns.call(preprocess(cmd))
        self.counter += 1

        return process_ns.spawn(command)
