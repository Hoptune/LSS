#!/bin/bash

set -e

source /global/common/software/desi/desi_environment.sh main
export LSSCODE=$HOME
PYTHONPATH=$PYTHONPATH:$LSSCODE/LSS/py


srun -N 1 -C cpu -t 04:00:00 --qos interactive --account desi python scripts/main/mkCat_main.py --type BGS_BRIGHT-21.5 --fulld n --survey Y1 --verspec iron --version $1 --clusd y --clusran y --splitGC y --nz y --par y --imsys_colname WEIGHT_IMLIN --basedir /global/cfs/cdirs/desi/survey/catalogs/ --compmd altmtl

