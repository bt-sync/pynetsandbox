## About linux namespaces
http://man7.org/linux/man-pages/man7/namespaces.7.html

## Unittests
`sudo python3 test.py`

## Install

`pip3 install git+https://github.com/bt-sync/pynetsandbox`

## How to use

main.py
```
from netsandbox import NetworkSandbox

with NetworkSandbox('10.1.0.0/16') as ns:
    p = ns.spawn('ping 10.1.0.1 -c 3')
    p.wait(timeout=10)

try:
    ns = NetworkSandbox('10.2.0.0/16')
    p = ns.spawn('ping 10.2.0.1 -c 3')
    p.wait(timeout=10)
finally:
    ns.release()

```

`sudo python3 main.py`


## Before contributing

`pylint --rcfile .pylintrc *.py netsandbox`