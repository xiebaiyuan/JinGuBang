#!/bin/bash
title="title=$1"
echo $title
desp="desp=$2"
echo $desp
curl -X POST -d "$title" -d "$desp" https://sctapi.ftqq.com/SCT37185Tt4Qv4hWxkhHqnD8yWT09TvdT.send
