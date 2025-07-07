#!/usr/bin/env bash

echo ">>> Uninstalling existing line-bot-sdk..."
pip uninstall -y line-bot-sdk

echo ">>> Installing line-bot-sdk version 3.7.0..."
pip install line-bot-sdk==3.7.0



#Add .render-build.sh to force correct SDK version
