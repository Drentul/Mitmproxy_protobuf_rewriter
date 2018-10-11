Rewriter
addon for mitmproxy

Setup
-----

This project contains two submodules:
https://github.com/mitmproxy/mitmproxy.git - http proxy with free license
ssh://git@dev.tightvideo.com:22222/frontendproto.git - protobuf files. Make sure that you have access to this repository!

Clone the repo. Key -r need to pull submodules
git clone -r ssh://git@dev.tightvideo.com:22222/native-testing-proxy-rewriter.git

Run setup
---------

bash:
. setup.sh

powershell:
powershell .\dev.ps1 (on Windows)

Run proxy
---------

bash:
. run_mitm.sh

powershell:
powershell .\run_mitm.ps1 (on Windows)

Update
------

Pull changes with git (or sit submodules) then do @Run setup@ chapter
