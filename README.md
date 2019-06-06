Rewriter
addon for mitmproxy

Setup
-----

This project contains two submodules:
https://github.com/mitmproxy/mitmproxy.git - http proxy with free license
https://github.com/Drentul/Sample_proto.git - protobuf files. Connect your own protobuf repo instead.

```
git clone --recursive https://github.com/Drentul/Mitmproxy_protobuf_rewriter.git
```

Run setup
---------

bash:
```
. setup.sh
```
And follow the tips

powershell: (not implemented!)
```
powershell .\dev.ps1
```

Run proxy
---------

bash:
```
. run_mitm.sh
```

if you want only proxy, without rewrite addon, comment (#) this "-s rewrite.py" in *run_mitm.sh* file

powershell: (not implemented!)
```
powershell .\run_mitm.ps1
```

Controls
---------

Rewriting by addon works according configs which is in rewrite.py and rewrite_core.py files.
Changes in rewrite.py file (e.g. adding new rule or changes in it) will restart the addon automatically. Proxy does not need to be restarted.

For tips on managing proxies, see the project description https://github.com/mitmproxy/mitmproxy
