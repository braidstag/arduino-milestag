#!/bin/bash

cp testFile.orig testFile
./client.py -s testFile

cp testFile.orig testFile
./client.py -s testFile -t 1 -p 2

cp testFile.orig testFile
./client.py -s testFile -t 2 -p 1
