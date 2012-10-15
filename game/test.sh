#!/bin/bash

rm testFile > /dev/null
mkfifo testFile
(sleep 3; cat testFile.orig > testFile) &
./client.py -s testFile
