#!/bin/bash

rm testFile > /dev/null
mkfifo testFile
(sleep 3; cat testFile.orig; sleep 2) > testFile &
./client.py -s testFile
