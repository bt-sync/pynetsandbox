## About linux namespaces
http://man7.org/linux/man-pages/man7/namespaces.7.html

## Unittests
`sudo python3 test.py`

## How to use

main.py
```
from netsandbox import NetworkSandbox

with NetworkSandbox() as ns:
    p = ns.spawn("ping 10.32.255.254 -c 3")
    p.wait(timeout=10)
```

`sudo python3 main.py`
