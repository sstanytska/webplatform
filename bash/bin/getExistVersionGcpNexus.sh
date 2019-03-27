#!/usr/bin/env bash

## This script will go to the Nexus and will get exist version
version=$(curl -X GET "http://nexus.fuchicorp.com/service/rest/v1/components?repository=fuchicorp" -H "accept: application/json" |  grep version | sed 's/ //g' | cut -c 12-20 | sed 's/",//g' | tail -n1)
echo $version
