#!/usr/bin/env bash

## This script will go to the Nexus and will get exist version
version=$(curl -sS -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET 'http://nexus.fuchicorp.com/service/rest/beta/components?repository=fscoding' | grep version | sed 's/ //g' | cut -c 12-20| sed 's/",//g' | tail -n1)
echo $version
