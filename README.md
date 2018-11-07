Rewriter
addon for mitmproxy

Setup
-----

This project contains two submodules:
https://github.com/mitmproxy/mitmproxy.git - http proxy with free license
ssh://git@dev.tightvideo.com:22222/frontendproto.git - protobuf files. Make sure that you have access to this repository!

Clone the repo. Key --recursive need to pull submodules
```
git clone --recursive ssh://git@gitlab.lfstrm.tv:2002/native-apps-team/testing/native_testing_proxy_rewriter.git
```
Run setup
---------

bash:
```
. setup.sh
```

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

powershell: (not implemented!)
```
powershell .\run_mitm.ps1
```

Update
------

git pull --recurse-submodules

then do @Run setup@ chapter
