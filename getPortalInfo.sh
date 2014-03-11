#!/usr/bin/bash

rsync -r -v --progress -e ssh hirsh@charlie.oxigen.pw:/home/hirsh/portalInfo.txt .

