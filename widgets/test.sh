#!/bin/bash

source pcds_conda
export EPICS_HOST_ARCH="rhel7-x86_64" # fix for env var overwritten by pcds_conda

export MYDIR=`dirname $(readlink -f $0)` # gets script working dir

SCRIPT=$(basename "$0")
SCRIPT=${SCRIPT%%.*}

echo "Launching ${SCRIPT}.ui"
pydm --hide-nav-bar $MYDIR/$SCRIPT.ui
