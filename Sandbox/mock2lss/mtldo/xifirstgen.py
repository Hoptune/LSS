import os
import argparse
import logging
import numpy as np
from astropy.table import Table, vstack
from matplotlib import pyplot as plt
from desitarget.sv3 import sv3_targetmask
import itertools
import random
from pycorr import TwoPointCorrelationFunction, utils, project_to_multipoles, project_to_wp, setup_logging
from LSS.tabulated_cosmo import TabulatedDESI
cosmo = TabulatedDESI()
distance = cosmo.comoving_radial_distance

parser = argparse.ArgumentParser()
parser.add_argument("--type", help="tracer type to be selected")
parser.add_argument("--basedir", help="where to find catalogs",default='/global/cscratch1/sd/acarnero')
parser.add_argument("--version", help="catalog version",default='test')
parser.add_argument("--verspec",help="version for redshifts",default='mock')
parser.add_argument("--survey",help="e.g., SV3 or main",default='SV3')
parser.add_argument("--nran",help="number of random files to combine together (1-18 available)",default=10)
parser.add_argument("--weight_type",help="types of weights to use; use angular_bitwise for PIP; default just uses WEIGHT column",default='default')
parser.add_argument("--bintype",help="log or lin",default='lin')
parser.add_argument("--nthreads",help="number of threads for parallel comp",default=32,type=int)
parser.add_argument("--vis",help="set to y to plot each xi ",default='n')
parser.add_argument("--id",help="id of mock ",default=0)

#parser.add_argument("--idran",help="id of mock ",default=0)

#only relevant for reconstruction
parser.add_argument("--rectype",help="IFT or MG supported so far",default='IFT')
parser.add_argument("--convention",help="recsym or reciso supported so far",default='reciso')


args = parser.parse_args()

ttype = args.type
basedir = args.basedir
version = args.version
specrel = args.verspec
survey = args.survey
nran = int(args.nran)
weight_type = args.weight_type
id_ = "%03d"%int(args.id)

if args.bintype == 'log':
    bine = np.logspace(-1.5, 2.2, 80)
if args.bintype == 'lin':
    bine = np.linspace(1e-4, 200, 40)

dirxi = os.path.join(os.environ['CSCRATCH'],survey+'xi')

if not os.path.exists(dirxi):
    os.mkdir(dirxi)
    print('made '+dirxi) 

datafile = os.path.join(os.environ['CSCRATCH'], survey, 'mockTargets_{ID}_FirstGen_CutSky_alltracers_sv3bits.fits'.format(ID=id_))

ran_ids = np.linspace(100,5000,50)
ran_ids = random.sample(list(ran_ids), nran)
random_data = os.path.join(os.environ['CSCRATCH'], survey, 'mockRandom_{RANID}_FirstGen_CutSky_alltracers_sv3bits.fits') #.format(RANID=int(ran_ids[ii])))



zmask = ['']
minn = 0

subt = None

if ttype[:3] == 'LRG':
    zl = [0.4,0.6,0.8,1.1]


if ttype[:3] == 'ELG':# or type == 'ELG_HIP':
    #minn = 5
    zl = [0.8,1.1,1.5]

if ttype == 'QSO':
    zl = [0.8,1.1,1.5,2.1]

if ttype == 'QSOh':
    zl = [2.1,3.5]
    ttype = 'QSO'
    #zmin = 1.
    #zmax = 2.1

   

if ttype[:3] == 'BGS':
    #minn = 2
    zl = [0.1,0.3,0.5]
    #zmin = 0.1
    #zmax = 0.5 

if ttype[:3] == 'BGS' and ttype[-1] == 'l':
    #minn = 2
    zl = [0.1,0.3]
    ttype = ttype[:-1]
    #zmin = 0.1
    #zmax = 0.5 

if ttype[:3] == 'BGS' and ttype[-1] == 'h':
    #minn = 2
    zl = [0.3,0.5]
    ttype = ttype[:-1]
    #zmin = 0.1
    #zmax = 0.5 


wa = ''
if survey == 'main':
    wa = 'zdone'

#bit = sv3_targetmask.desi_mask[type]

#wtype = ((dz['SV3_DESI_TARGET'] & bit) > 0)


def compute_correlation_function(mode, edges, tracer='LRG', region='_N', nrandoms=4, zlim=(0., np.inf), weight_type=None, nthreads=8, dtype='f8', wang=None):
    if ttype == 'ELGrec' or ttype == 'LRGrec':
        data_fn = os.path.join(dirname, tracer+wa+ region+'_clustering_'+args.rectype+args.convention+'.dat.fits')
        data = Table.read(data_fn)

        randoms_fn = os.path.join(dirname, tracer+wa+ region+'_clustering_'+args.rectype+args.convention+'.ran.fits') 
        randoms = Table.read(randoms_fn) 
    else:
        data_fn = datafile #os.path.join(dirname, '{}{}_clustering_{}.dat.fits'.format(tracer+wa, region, id_))
        data = Table.read(data_fn)

        bit = sv3_targetmask.desi_mask[ttype]
        wtype = ((data['SV3_DESI_TARGET'] & bit) > 0)
        data = data[wtype]


        randoms_fn = [random_data.format(RANID=int(ran_ids[iran])) for iran in range(nrandoms)]
        randoms = vstack([Table.read(fn) for fn in randoms_fn])

        wtype = ((randoms['SV3_DESI_TARGET'] & bit) > 0)
        randoms = randoms[wtype]

    corrmode = mode
    if mode == 'wp':
        corrmode = 'rppi'
    if mode == 'multi':
        corrmode = 'smu'
    if corrmode == 'smu':
        edges = (edges, np.linspace(0., 1., 101))
    if corrmode == 'rppi':
        edges = (edges, np.linspace(0., 40., 41))
    
    def get_positions_weights(catalog, name='data', zname='Z'):
        mask = (catalog[zname] >= zlim[0]) & (catalog[zname] < zlim[1])
        positions = [catalog['RA'][mask], catalog['DEC'][mask], distance(catalog[zname][mask])]
        #if weight_type is None:
        #    weights = None
        #else:
        weights = np.ones_like(positions[0])
        if name == 'data':
            if 'photometric' in weight_type:
                rfweight = RFWeight(tracer=tracer)
                weights *= rfweight(positions[0], positions[1])
            if 'zfail' in weight_type:
                weights *= catalog['WEIGHT_ZFAIL'][mask]
            if 'default' in weight_type:
                weights *= catalog['WEIGHT'][mask]
            if 'completeness' in weight_type:
                weights *= catalog['WEIGHT'][mask]/catalog['WEIGHT_ZFAIL'][mask]
            elif 'bitwise' in weight_type:
                weights = list(catalog['BITWEIGHTS'][mask].T) + [weights]
        return positions, weights
    
    data_positions, data_weights = get_positions_weights(data, name='firstgen', zname='RSDZ')
    print('using '+str(len(data_positions[0]))+ ' rows for data')
    randoms_positions, randoms_weights = get_positions_weights(randoms, name='randoms', zname='RSDZ') #'TRUEZ'
    print('using '+str(len(randoms_positions[0]))+ ' rows for random')

    kwargs = {}
    if 'angular' in weight_type and wang is None:
        
        data_fn = os.path.join(dirname, '{}_full_{}.dat.fits'.format(tracer, id_))
        randoms_fn = os.path.join(dirname, '{}_full_{}.ran.fits'.format(tracer, id_))
        parent_data = Table.read(data_fn)
        parent_randoms = Table.read(randoms_fn)
        
        def get_positions_weights(catalog, fibered=False):
            mask = np.ones(len(catalog),dtype='bool')
            if reg != '':
                mask &= catalog['PHOTSYS'] == region.strip('_')
            if fibered: mask &= catalog['LOCATION_ASSIGNED']
            positions = [catalog['RA'][mask], catalog['DEC'][mask], catalog['DEC'][mask]]
            if fibered: weights = list(catalog['BITWEIGHTS'][mask].T)
            else: weights = np.ones_like(positions[0])
            return positions, weights
    
        fibered_data_positions, fibered_data_weights = get_positions_weights(parent_data, fibered=True)
        print(len(fibered_data_weights),len(fibered_data_positions[0]),len(parent_data))
        parent_data_positions, parent_data_weights = get_positions_weights(parent_data)
        parent_randoms_positions, parent_randoms_weights = get_positions_weights(parent_randoms)
        
        tedges = np.logspace(-3.5, 0.5, 31)
        # First D1D2_parent/D1D2_PIP angular weight
        wangD1D2 = TwoPointCorrelationFunction('theta', tedges, data_positions1=fibered_data_positions, data_weights1=fibered_data_weights,
                                               randoms_positions1=parent_data_positions, randoms_weights1=parent_data_weights,
                                               estimator='weight', engine='corrfunc', position_type='rdd', nthreads=nthreads, dtype=dtype)

        # First D1R2_parent/D1R2_IIP angular weight
        # Input bitwise weights are automatically turned into IIP
        wangD1R2 = TwoPointCorrelationFunction('theta', tedges, data_positions1=fibered_data_positions, data_weights1=fibered_data_weights,
                                               data_positions2=parent_randoms_positions, data_weights2=parent_randoms_weights,
                                               randoms_positions1=parent_data_positions, randoms_weights1=parent_data_weights,
                                               randoms_positions2=parent_randoms_positions, randoms_weights2=parent_randoms_weights,
                                               estimator='weight', engine='corrfunc', position_type='rdd', nthreads=nthreads, dtype=dtype)
        wang = {}
        wang['D1D2_twopoint_weights'] = wangD1D2
        wang['D1R2_twopoint_weights'] = wangD1R2
    
    kwargs.update(wang or {})

    result = TwoPointCorrelationFunction(corrmode, edges, data_positions1=data_positions, data_weights1=data_weights,
                                         randoms_positions1=randoms_positions, randoms_weights1=randoms_weights,
                                         engine='corrfunc', position_type='rdd', nthreads=nthreads, dtype=dtype, **kwargs)
    if mode == 'multi':
        return project_to_multipoles(result), wang
    if mode == 'wp':
        return project_to_wp(result), wang
    return result.sep, result.corr, wang    

ranwt1=False

regl = ['']
#regl = ['_N','_S','']

tcorr = ttype
tw = ttype
if survey == 'main':
    regl = ['_DN','_DS','_N','_S','']
    if ttype == 'LRGrec':
        regl = ['_DN','_N']
        tcorr = 'LRG'
        tw = 'LRG'+args.rectype+args.convention
    if ttype == 'ELGrec':
        regl = ['_DN','_N']
        tcorr = 'ELG'
        tw = 'ELG'+args.rectype+args.convention
        
zlimits_comb = list(itertools.combinations(zl, 2))
for zlims in zlimits_comb:
    zmin = zlims[0]
    zmax = zlims[1]
    print(zmin,zmax)
    for reg in regl:
        print(reg)
        (sep, xiell), wang = compute_correlation_function(mode='multi', edges=bine, tracer=tcorr, region=reg, zlim=(zmin,zmax), weight_type=weight_type,nthreads=args.nthreads, nrandoms=nran)
        outfile = os.path.join(dirxi, 'FirstGen_xi024'+tw+survey+reg+'_'+str(zmin)+str(zmax)+version+'_'+weight_type+args.bintype+'_'+id_+'_numran'+str(nran)+'.dat')
        fo = open(outfile, 'w')
        for i in range(0,len(sep)):
            fo.write(str(sep[i])+' '+str(xiell[0][i])+' '+str(xiell[1][i])+' '+str(xiell[2][i])+'\n')
        fo.close()
        if args.vis == 'y':
            if args.bintype == 'log':
                plt.loglog(sep,xiell[0])
            if args.bintype == 'lin':
                plt.plot(sep,sep**2.*xiell[0])
            plt.title(ttype+' '+str(zmin)+'<z<'+str(zmax)+' in '+reg)
            plt.show()    
