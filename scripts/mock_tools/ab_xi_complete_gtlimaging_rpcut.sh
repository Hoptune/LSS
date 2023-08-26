#!/bin/bash
source /global/common/software/desi/users/adematti/cosmodesi_environment.sh main
PYTHONPATH=$PYTHONPATH:$HOME/LSS/py
for (( i=$1;i<=$2;i++ ))
do
 srun -N 1 -C gpu -t 04:00:00 --gpus 4 --qos interactive --account desi_g python scripts/xirunpc.py --gpu --tracer ELG_LOP_complete_gtlimaging --region NGC SGC --corr_type smu --weight_type default --njack 0 --basedir /global/cfs/cdirs/desi/survey/catalogs/Y1/mocks/SecondGenMocks/AbacusSummit/mock$i/ --outdir /global/cfs/cdirs/desi/survey/catalogs/Y1/mocks/SecondGenMocks/AbacusSummit/mock$i/xi/ --rpcut 2.5
 srun -N 1 -C gpu -t 04:00:00 --gpus 4 --qos interactive --account desi_g python scripts/xirunpc.py --gpu --tracer LRG_complete_gtlimaging --region NGC SGC --corr_type smu --weight_type default --njack 0 --basedir /global/cfs/cdirs/desi/survey/catalogs/Y1/mocks/SecondGenMocks/AbacusSummit/mock$i/ --outdir /global/cfs/cdirs/desi/survey/catalogs/Y1/mocks/SecondGenMocks/AbacusSummit/mock$i/xi/ --rpcut 2.5
 srun -N 1 -C gpu -t 04:00:00 --gpus 4 --qos interactive --account desi_g python scripts/xirunpc.py --gpu --tracer QSO_complete_gtlimaging --region NGC SGC --corr_type smu --weight_type default --njack 0 --basedir /global/cfs/cdirs/desi/survey/catalogs/Y1/mocks/SecondGenMocks/AbacusSummit/mock$i/ --outdir /global/cfs/cdirs/desi/survey/catalogs/Y1/mocks/SecondGenMocks/AbacusSummit/mock$i/xi/ --rpcut 2.5

done

