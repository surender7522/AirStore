#!/bin/bash
for i in {1..9}
do
   rm -f test_env/$i/*
   echo "Clearing folder $i"
done
