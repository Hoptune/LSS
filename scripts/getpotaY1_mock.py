'''
Find all potential assignment and counts tiles for Y1 mocks
'''

import numpy as np
import os
from astropy.table import Table, join, vstack
import argparse
from fiberassign.hardware import load_hardware
from fiberassign.tiles import load_tiles
from fiberassign.targets import Targets, TargetsAvailable, LocationsAvailable, create_tagalong, load_target_file, targets_in_tiles
from fiberassign.assign import Assignment

from fiberassign.utils import Logger

from desitarget.io import read_targets_in_tiles
import desimodel.focalplane
import desimodel.footprint
trad = desimodel.focalplane.get_tile_radius_deg()*1.1 #make 10% greater just in case


import fitsio

import LSS.common_tools as common
#from LSS.imaging import get_nobsandmask
from LSS.main.cattools import count_tiles_better
from LSS.globals import main

import time
import bisect

parser = argparse.ArgumentParser()
parser.add_argument("--prog", choices=['DARK','BRIGHT'],default='DARK')
parser.add_argument("--mock", default='ab2ndgen')
parser.add_argument("--realization")
parser.add_argument("--getcoll",default='y')
parser.add_argument("--base_output", help="base directory for output",default='/global/cfs/cdirs/desi/survey/catalogs/Y1/mocks/')
parser.add_argument("--tracer", help="tracer for CutSky EZ mocks", default=None)
parser.add_argument("--base_input", help="base directory for input for EZ mocks 6Gpc", default = None)
parser.add_argument("--counttiles", default = 'n')

#desi_input_dir = '/dvs_ro/cfs/cdirs/desi'
desi_input_dir = '/global/cfs/cdirs/desi'

args = parser.parse_args()
if args.mock == 'ab2ndgen':
    #infn = args.base_output+'FirstGenMocks/AbacusSummit/forFA'+args.realization+'_matched_input_full_masknobs.fits'
    #infn = args.base_output+'SecondGenMocks/AbacusSummit/forFA'+args.realization+'.fits'
    infn = args.base_input+'SecondGenMocks/AbacusSummit/forFA'+args.realization+'.fits'
    print('Reading', infn)
    tars = fitsio.read(infn)
    tarcols = list(tars.dtype.names)
    #tileoutdir = args.base_output+'SecondGenMocks/AbacusSummit/tartiles'+args.realization+'/'
    tileoutdir = os.getenv('SCRATCH')+'/SecondGenMocks/AbacusSummit/tartiles'+args.realization+'/'
    if not os.path.exists(tileoutdir):
        os.makedirs(tileoutdir)
    paoutdir = args.base_output+'SecondGenMocks/AbacusSummit/mock'+args.realization+'/'
elif args.mock == 'ezmocks6':
#     #tr = args.tracer
#     rz = args.realization
#     print("Doing %s"%tr)

#     if  tr == "LRG":
#         infn1 = "/global/cfs/cdirs/desi/cosmosim/FirstGenMocks/EZmock/CutSky_6Gpc/LRG/z0.800/cutsky_LRG_z0.800_EZmock_B6000G1536Z0.8N216424548_b0.385d4r169c0.3_seed%s_NGC.fits"%rz
#         infn2 = "/global/cfs/cdirs/desi/cosmosim/FirstGenMocks/EZmock/CutSky_6Gpc/LRG/z0.800/cutsky_LRG_z0.800_EZmock_B6000G1536Z0.8N216424548_b0.385d4r169c0.3_seed%s_SGC.fits"%rz
#     elif tr == "ELG":
#         infn1 = "/global/cfs/cdirs/desi/cosmosim/FirstGenMocks/EZmock/CutSky_6Gpc/ELG/z1.100/cutsky_ELG_z1.100_EZmock_B6000G1536Z1.1N648012690_b0.345d1.45r40c0.05_seed%s_NGC.fits"%rz
#         infn2 = "/global/cfs/cdirs/desi/cosmosim/FirstGenMocks/EZmock/CutSky_6Gpc/ELG/z1.100/cutsky_ELG_z1.100_EZmock_B6000G1536Z1.1N648012690_b0.345d1.45r40c0.05_seed%s_SGC.fits"%rz
#     elif tr == "QSO":
#         infn1 = "/global/cfs/cdirs/desi/cosmosim/FirstGenMocks/EZmock/CutSky_6Gpc/QSO/z1.400/cutsky_QSO_z1.400_EZmock_B6000G1536Z1.4N27395172_b0.053d1.13r0c0.6_seed%s_NGC.fits"%rz
#         infn2 = "/global/cfs/cdirs/desi/cosmosim/FirstGenMocks/EZmock/CutSky_6Gpc/QSO/z1.400/cutsky_QSO_z1.400_EZmock_B6000G1536Z1.4N27395172_b0.053d1.13r0c0.6_seed%s_SGC.fits"%rz
#    # infn1 = "/global/cfs/cdirs/desi/cosmosim/FirstGenMocks/EZmock/CutSky_6Gpc/LRG/z0.800/cutsky_LRG_z0.800_EZmock_B6000G1536Z0.8N216424548_b0.385d4r169c0.3_seed1_NGC.fits"
#    # infn2 = "/global/cfs/cdirs/desi/cosmosim/FirstGenMocks/EZmock/CutSky_6Gpc/LRG/z0.800/cutsky_LRG_z0.800_EZmock_B6000G1536Z0.8N216424548_b0.385d4r169c0.3_seed1_SGC.fits"
#     tars1 = Table.read(infn1)#fitsio.read(infn1)
#     tars2 = Table.read(infn2)#fitsio.read(infn2)
#     tars1["GALCAP"] = "N"
#     tars2["GALCAP"] = "S"
#     tars = vstack([tars1, tars2])
#     tars['TARGETID'] = np.arange(len(tars))
    
    infn = args.base_input + 'EZMocks_6Gpc/EZMocks_6Gpc_' + args.realization + '.fits'
    tars = fitsio.read(infn)
    tarcols = list(tars.dtype.names)#['TARGETID','RA','DEC', 'Z','Z_COSMO','GALCAP', 'NZ', 'RAW_NZ']

    tileoutdir = args.base_output+'EZMocks_6Gpc/tartiles'+args.realization+'/'
    paoutdir = args.base_output+'EZMocks_6Gpc/EzMocks/mock'+args.realization+'/'
    if args.tracer is not None:
        tileoutdir += args.tracer+'/'
        paoutdir += args.tracer+'/'

print(tars.dtype.names)
print('Mock targets:', len(tars))
print('DEC dtype:', tars['DEC'].dtype)
print('mock type:', type(tars))

t0 = time.time()
I = np.argsort(tars['DEC'])
tars = tars[I]
t1 = time.time()
print('Sorting mocks: %.1f' % (t1-t0))

#tars_dec = tars['DEC'].copy()
#print('tars_dec dtype:', tars_dec.dtype, 'stride', tars_dec.strides)

if not os.path.exists(tileoutdir):
    os.makedirs(tileoutdir)
    print('made '+tileoutdir)
if not os.path.exists(paoutdir):
    os.makedirs(paoutdir)
    print('made '+paoutdir)


tiletab = Table.read(os.path.join(desi_input_dir, 'survey/catalogs/Y1/LSS/tiles-'+args.prog+'.fits'))

def get_tile_targ(tiles):
    t0 = time.time()
    tdec = tiles['DEC']
    decmin = tdec - trad
    decmax = tdec + trad
    #ta = time.time()
    dec = tars['DEC']
    #tb = time.time()
    #print('tars[DEC]: %.3f' % (tb-ta))
    #tc = time.time()
    #i0,i1 = np.searchsorted(dec, [decmin, decmax])
    #td = time.time()
    #j0,j1 = np.searchsorted(dec, [np.float32(decmin), np.float32(decmax)])
    #te = time.time()
    k0 = bisect.bisect_left(dec, decmin)
    k1 = bisect.bisect_left(dec, decmax, lo=k0)
    #tf = time.time()
    #m0,m1 = np.searchsorted(tars_dec, [np.float32(decmin), np.float32(decmax)])
    #tg = time.time()
    #print('searchsorted: %.3f, searchsorted(float32): %.3f, bisect: %.3f, searchsorted(copy): %.3f' % (td-tc, te-td, tf-te, tg-tf))
    #print('ijkm', i0,j0,k0,m0, '/', i1,j1,k1,m1)
    i0,i1 = k0,k1
    #wdec = (tars['DEC'] > decmin) & (tars['DEC'] < decmax)
    Idec = slice(i0, i1+1)
    #print(len(rt[wdec]))
    t1 = time.time()
    #inds = desimodel.footprint.find_points_radec(tiles['RA'], tdec,tars[wdec]['RA'], tars[wdec]['DEC'])
    inds = desimodel.footprint.find_points_radec(tiles['RA'], tdec,tars['RA'][Idec], tars['DEC'][Idec])
    t2 = time.time()
    print('got indexes')
    print('inds:', inds[:10])
    #rtw = tars[Idec][inds]
    #rtw = tars[i0 + inds]
    rtw = tars[i0 + np.array(inds)]
    print('total mock:', len(dec), 'in Dec slice:', 1+i1-i0, 'in tile:', len(rtw))
    t3 = time.time()
    rmtl = Table(rtw)
    t4 = time.time()
    print('made table')
    del rtw
    #n=len(rmtl)
    #rmtl['TARGETID'] = np.arange(1,n+1)+10*n*rannum 
    #rmtl['TARGETID'] = np.arange(len(rmtl))
    #print(len(rmtl['TARGETID'])) #checking this column is there
    if 'DESI_TARGET' not in tarcols:
        rmtl['DESI_TARGET'] = np.ones(len(rmtl),dtype=int)*2
    if 'NUMOBS_INIT' not in tarcols:
        rmtl['NUMOBS_INIT'] = np.zeros(len(rmtl),dtype=int)
    if 'NUMOBS_MORE' not in tarcols:
        rmtl['NUMOBS_MORE'] = np.ones(len(rmtl),dtype=int)
    if 'PRIORITY' not in tarcols:
        rmtl['PRIORITY'] = np.ones(len(rmtl),dtype=int)*3400
    #if 'OBSCONDITIONS' not in tarcols:
    rmtl['OBSCONDITIONS'] = np.ones(len(rmtl),dtype=int)*516#forcing it to match value assumed below
    if 'SUBPRIORITY' not in tarcols:
        rmtl['SUBPRIORITY'] = np.random.random(len(rmtl))
    t5 = time.time()
    return rmtl, dict(zip(['t_dec', 't_find_points', 't_rtw', 't_rmtl', 't_rmtl_add'],
                          np.diff([t0,t1,t2,t3,t4,t5])))

def write_tile_targ(inds ):
    t0 = time.time()
    tiles = tiletab[inds]
    #for i in range(0,len(tiles)):
    fname = tileoutdir+'/tilenofa-'+str(tiles['TILEID'])+'.fits'
    print('creating '+fname)
    t1 = time.time()
    rmtl, tiletimes = get_tile_targ(tiles)
    t2 = time.time()
    print('added columns for '+fname)
    rmtl.write(fname,format='fits', overwrite=True)
    del rmtl
    print('added columns, wrote to '+fname)
    t3 = time.time()
    #nd += 1
    #print(str(nd),len(tiles))
    #return np.append(np.array([ (t3-t2)+(t1-t0), t2-t1 ]), tiletimes)
    t = dict(t_write=(t3-t2)+(t1-t0))
    t.update(tiletimes)
    return t
    
margins = dict(pos=0.05,
                   petal=0.4,
                   gfa=0.4)


log = Logger.get()
rann = 0
n = 0


def getpa(ind):
    t0 = time.time()
    #tile = 1230
    tile = tiletab[ind]['TILEID']
    ts = '%06i' % tile
    
    fbah = fitsio.read_header(os.path.join(desi_input_dir, 'target/fiberassign/tiles/trunk/'+ts[:3]+'/fiberassign-'+ts+'.fits.gz'))
    dt = fbah['RUNDATE']#[:19]
    pr = args.prog
    t = Table(tiletab[ind])
    t['OBSCONDITIONS'] = 516
    t['IN_DESI'] = 1
    t['MTLTIME'] = fbah['MTLTIME']
    t['FA_RUN'] = fbah['FA_RUN']
    t['PROGRAM'] = pr
    obsha = fbah['FA_HA']
    obstheta = fbah['FIELDROT']

    t1 = time.time()
    
    hw = load_hardware(rundate=dt, add_margins=margins)

    t2 = time.time()
    
    t.write(os.environ['SCRATCH']+'/rantiles/'+str(tile)+'-'+str(rann)+'-tiles.fits', overwrite=True)
    
    t3 = time.time()

    tiles = load_tiles(
        tiles_file=os.environ['SCRATCH']+'/rantiles/'+str(tile)+'-'+str(rann)+'-tiles.fits',obsha=obsha,obstheta=obstheta,
        select=[tile])

    t4 = time.time()
    
    tids = tiles.id
    print('Tile ids:', tids)
    I = np.flatnonzero(np.array(tids) == tile)
    assert(len(I) == 1)
    i = I[0]
    tile_ra  = tiles.ra[i]
    tile_dec = tiles.dec[i]

    # Create empty target list
    tgs = Targets()
    # Create structure for carrying along auxiliary target data not needed by C++.
    plate_radec=True
    tagalong = create_tagalong(plate_radec=plate_radec)
    
    print(tile)
    # Load target files...
    t5 = time.time()
    load_target_file(tgs, tagalong, tileoutdir+'/tilenofa-%i.fits' % tile)
    t6 = time.time()
    #loading it again straight to table format because I can't quickly figure out exactly where targetid,ra,dec gets stored
    tar_tab = fitsio.read(tileoutdir+'/tilenofa-%i.fits' % tile,columns =tarcols)
    t7 = time.time()

    # Find targets within tiles, and project their RA,Dec positions
    # into focal-plane coordinates.
    tile_targetids, tile_x, tile_y, tile_xy_cs5 = targets_in_tiles(hw, tgs, tiles, tagalong)
    # Compute the targets available to each fiber for each tile.
    tgsavail = TargetsAvailable(hw, tiles, tile_targetids, tile_x, tile_y)
    # Compute the fibers on all tiles available for each target and sky
    favail = LocationsAvailable(tgsavail)

    # FAKE stucksky
    stucksky = {}

    # Create assignment object
    asgn = Assignment(tgs, tgsavail, favail, stucksky)
    tgsavail = asgn.targets_avail()
    avail = tgsavail.tile_data(tile)
    navail = np.sum([len(avail[x]) for x in avail.keys()])
    fibers = dict(hw.loc_fiber)
    fdata = Table()
    fdata['LOCATION'] = np.zeros(navail,dtype=int)
    fdata['FIBER'] = np.zeros(navail,dtype=int)
    fdata['TARGETID'] = np.zeros(navail,dtype=int)
    
    off = 0
    # The "FAVAIL" (available targets) HDU is sorted first by LOCATION,
    # then by TARGETID.
    for lid in sorted(avail.keys()):
        # lid (location id) is a scalar, tg (target ids) is an array
        tg = avail[lid]
        fdata['LOCATION'][off:off+len(tg)] = lid
        fdata['FIBER']   [off:off+len(tg)] = fibers[lid]
        fdata['TARGETID'][off:off+len(tg)] = sorted(tg)
        off += len(tg)
    fdata = join(fdata,tar_tab,keys=['TARGETID'],join_type='left')
    if args.getcoll == 'y':
        coll = asgn.check_avail_collisions(tile)
        kl = np.array(list(coll.keys())).transpose()
        locs = kl[0]
        ids = kl[1]
        locids = ids*10000+locs
        print('N collisions:', len(coll))
        locidsin = np.isin(fdata['LOCATION']+10000*fdata['TARGETID'],locids)
        print('N collisions original:',np.sum(locidsin),len(fdata))
        fdata['COLLISION'] = locidsin
    #colltab = Table(forig[locidsin])
    fdata['TILEID'] = tile
    t8 = time.time()
    tt = dict(zip(['t_readfa', 't_loadhw', 't_write_tile', 't_load_tile',
                   't_setup', 't_load_targets', 't_read_nofa', 't_assign'],
                  np.diff([t0,t1,t2,t3,t4,t5,t6,t7,t8])))
    tt['rundate'] = dt
    return fdata, tt

def run_one_tile(ind):
    T1 = write_tile_targ(ind)
    res,T2 = getpa(ind)
    T1.update(T2)
    return res, T1

def main():
    from multiprocessing import Pool
    tls = list(tiletab['TILEID'])#[:10])
    #inds = np.flatnonzero(np.array(tls) == 1230)
    #inds = np.arange(len(tls))
    #write_tile_targ(inds[0])
    inds = np.arange(256)
    
    # with Pool(processes=128) as pool:
    #     res = pool.map(write_tile_targ, inds)
    # with Pool(processes=128) as pool:
    #     res = pool.map(getpa, inds)

    # with Pool(processes=128) as pool:
    #     res = pool.map(run_one_tile, inds)

    #res = [run_one_tile(i) for i in inds]
    # res = []
    # tt = []
    # for i in inds:
    #     r, t = run_one_tile(i)
    #     res.append(r)
    #     tt.append(t)

    res = []
    tt = []
    with Pool(processes=128) as pool:
        R = pool.map(run_one_tile, inds)
        for r,t in R:
            res.append(r)
            tt.append(t)
    
    colltot = np.concatenate(res)
    if args.getcoll == 'y':
        print(len(colltot),np.sum(colltot['COLLISION']))
    
    common.write_LSS(colltot,paoutdir+'/pota-'+args.prog+'.fits')

    #allkeys = set()
    #for t in tt:
    #    allkeys.update(t.keys())
    #print('All keys:', allkeys)
    # Assume all keys are the same
    allkeys = tt[0].keys()

    times = Table()
    for k in allkeys:
        v = []
        for t in tt:
            v.append(t[k])
        times[k] = v
    # tt = np.vstack(tt)
    # names = ['t_write_nofa', 't_get_tile',
    #          # within get_tile_targ:
    #          't_get_dec', 't_find_points', 't_rtw', 't_mtl', 't_mtl_add',
    #          #'t_find_points',
    #          't_readfa', # 0-1
    #          't_loadhw',
    #          't_write_tile',
    #          't_load_tile',
    #          't_setup',
    #          't_load_targets',
    #          't_read_nofa',
    #          't_assign',
    #          ]
    # r,c = tt.shape
    # assert(len(names) == c)
    # 
    # for i,name in enumerate(names):
    #     times[name] = tt[:,i]
    times.write('times.fits', format='fits', overwrite=True)
    
if __name__ == '__main__':
    main()
