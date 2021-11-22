'''
python functions to do various useful date processing/manipulation
'''
import numpy as np
from scipy.special import erf
import fitsio
import glob
import os
import astropy.io.fits as fits
from astropy.table import Table,join,unique,vstack
from matplotlib import pyplot as plt
import desimodel.footprint
import desimodel.focalplane
from random import random
from desitarget.io import read_targets_in_tiles
from desitarget.sv3 import sv3_targetmask

from LSS.Cosmo import distance

def find_znotposs(dz):

    dz.sort('TARGETID')
    tidnoz = []
    tids = np.unique(dz['TARGETID'])
    ti = 0
    i = 0
    
    print('finding targetids that were not observed')
    while i < len(dz):
        za = 0
    
        while dz[i]['TARGETID'] == tids[ti]:
            if dz[i]['ZWARN'] != 999999:
                za = 1
                #break
            i += 1
            if i == len(dz):
                break
        if za == 0:
            tidnoz.append(tids[ti])
      
        if ti%30000 == 0:
            print(ti)
        ti += 1 

    
    selnoz = np.isin(dz['TARGETID'],tidnoz)
    tidsb = np.unique(dz[selnoz]['TILELOCID'])
    #dz = dz[selnoz]
    dz.sort('TILELOCID')
    tids = np.unique(dz['TILELOCID'])
    print('number of targetids with no obs '+str(len(tidnoz)))
    tlidnoz = []
    lznposs = []
    
    ti = 0
    i = 0
    
    while i < len(dz):
        za = 0
    
        while dz[i]['TILELOCID'] == tids[ti]:
            if dz[i]['ZWARN'] != 999999:
                za = 1
                #break
            i += 1
            if i == len(dz):
                break
        if za == 0:
            tlidnoz.append(tids[ti])
            #if np.isin(tids[ti],tidsb):
            #    lznposs.append(tids[ti])
      
        if ti%30000 == 0:
            print(ti,len(tids))
        ti += 1 
    #the ones to veto are now the join of the two
    wtbtlid = np.isin(tlidnoz,tidsb)
    tlidnoz = np.array(tlidnoz)
    lznposs = tlidnoz[wtbtlid]
    print('number of locations where assignment was not possible because of priorities '+str(len(lznposs)))
    return lznposs

def tile2rosette(tile):
    if tile < 433:
        return (tile-1)//27
    else:
        if tile >= 433 and tile < 436:
            return 13
        if tile >= 436 and tile < 439:
            return 14
        if tile >= 439 and tile < 442:
            return 15
        if tile >= 442 and tile <=480:
            return (tile-442)//3

        if tile > 480:
            return tile//30
    return 999999 #shouldn't be any more?

def calc_rosr(rosn,ra,dec):
    #given rosetter number and ra,dec, calculate distance from center
    roscen = {0:(150.100,2.182),1:(179.6,0),2:(183.1,0),3:(189.9,61.8),4:(194.75,28.2)\
    ,5:(210.0,5.0),6:(215.5,52.5),7:(217.8,34.4),8:(216.3,-0.6),9:(219.8,-0.6)\
    ,10:(218.05,2.43),11:(242.75,54.98),12:(241.05,43.45),13:(245.88,43.45),14:(252.5,34.5)\
    ,15:(269.73,66.02),16:(194.75,24.7),17:(212.8,-0.6),18:(269.73,62.52),19:(236.1,43.45)}
    ra = ra*np.pi/180.
    dec = dec*np.pi/180.
    rac,decc = roscen[rosn]
    rac = rac*np.pi/180.
    decc = decc*np.pi/180.
    cd = np.sin(dec)*np.sin(decc)+np.cos(dec)*np.cos(decc)*np.cos(rac-ra)
    ad = np.arccos(cd)*180./np.pi
    if ad > 2.5:
        print(rosn,ra,dec,rac,decc)
    return ad

#Reading the target file, create a file per tile, with duplicates of the targets
def randomtiles_allSV3(tiles, mytargets, directory_output='.'):
#AURE def randomtiles_allSV3(tiles,dirout='/global/cfs/cdirs/desi/survey/catalogs/SV3/LSS/random',imin=0,imax=18):
    '''
    tiles should be a table containing the relevant info
    '''
    trad = desimodel.focalplane.get_tile_radius_deg()*1.1 #make 10% greater just in case
    print(trad)
#AURE    for ii in range(imin,imax):
    rt = fitsio.read(mytargets)
    #rt = fitsio.read(minisvdir+'random/random_mtl.fits')
    print('loaded random file')
    tot = 0
    for i in range(0,len(tiles)):

        #print('length of tile file is (expected to be 1):'+str(len(tiles)))
        tile = tiles['TILEID'][i]
        fname = os.path.join(directory_output, 'tilenofa-'+str(tile)+'.fits')
        if os.path.isfile(fname):
            print(fname +' already exists')
        else:
            tdec = tiles['DEC'][i]
            decmin = tdec - trad
            decmax = tdec + trad
            wdec = (rt['DEC'] > decmin) & (rt['DEC'] < decmax)
            print(len(rt[wdec]))
            inds = desimodel.footprint.find_points_radec(tiles['RA'][i], tdec,rt[wdec]['RA'], rt[wdec]['DEC'])
            print('got indexes')
            rtw = rt[wdec][inds]
            rmtl = Table(rtw)
            tot += len(rmtl['TARGETID'])
            #rmtl['TARGETID'] = np.arange(len(rmtl))
            print(len(rmtl['TARGETID'])) #checking this column is there
            '''
            rmtl['DESI_TARGET'] = np.ones(len(rmtl),dtype=int)*2
            rmtl['SV3_DESI_TARGET'] = np.ones(len(rmtl),dtype=int)*2
            rmtl['NUMOBS_INIT'] = np.zeros(len(rmtl),dtype=int)
            rmtl['NUMOBS_MORE'] = np.ones(len(rmtl),dtype=int)
            rmtl['PRIORITY'] = np.ones(len(rmtl),dtype=int)*3400
            rmtl['OBSCONDITIONS'] = np.ones(len(rmtl),dtype=int)*516#tiles['OBSCONDITIONS'][i]
            rmtl['SUBPRIORITY'] = np.random.random(len(rmtl))
            '''

            if 'ZWARN' in rmtl.keys():
                del rmtl['ZWARN']
            if 'TRUEZ' in rmtl.keys():
                del rmtl['TRUEZ']

            rmtl.write(fname,format='fits', overwrite=True)
            print('added columns, wrote to '+fname)


def combtiles_wdup(tiles, mltTargets, fbaRun, fout='', tarcol=['RA','DEC','TARGETID','SV3_DESI_TARGET','SV3_BGS_TARGET','SV3_MWS_TARGET','SUBPRIORITY','PRIORITY_INIT','TARGET_STATE','TIMESTAMP','ZWARN','PRIORITY']):
    s = 0
    n = 0
    tmask = np.ones(len(tiles)).astype('bool')

    for tile in tiles[tmask]['TILEID']:
        ts = str(tile).zfill(3)
        faf = os.path.join(fbaRun[0], fbaRun[1].format(TILE=ts))
        #'/global/cfs/cdirs/desi/target/fiberassign/tiles/trunk/'+ts[:3]+'/fiberassign-'+ts+'.fits.gz'
        fht = fitsio.read_header(faf)
        wt = tiles['TILEID'] == tile

        tars = os.path.join(mltTargets[0], mltTargets[1].format(TILE=tile))
        tars = Table.read(tars)

        tt = Table.read(faf,hdu='FAVAIL')
        #tt = Table.read(faf,hdu='POTENTIAL_ASSIGNMENTS')
        tars = join(tars,tt,keys=['TARGETID'])
        tars['TILEID'] = tile
        #tars['ZWARN'].name = 'ZWARN_MTL'
        if s == 0:
            tarsn = tars
            s = 1
        else:
            tarsn = vstack([tarsn,tars],metadata_conflicts='silent')
        tarsn.sort('TARGETID')
        n += 1
        print(tile,n,len(tiles[tmask]),len(tarsn))
    tarsn.write(fout,format='fits', overwrite=True)

#combtile_specmock(ta, ['./fiberassigment', 'aure000{TILE}.fits'], target_file, outf)
def combtile_specmock(tiles, fbaRun, masterTarget, fout=''):
    print('Entering my combtile_specmock')
    s = 0
    n = 0
    tmask = np.ones(len(tiles)).astype('bool')

    tars = Table.read(masterTarget)

    for tile in tiles[tmask]['TILEID']:
        print(tile)
        ts = str(tile).zfill(3)
        faf = os.path.join(fbaRun[0], fbaRun[1].format(TILE=ts))
#        fht = fitsio.read_header(faf)
        wt = tiles['TILEID'] == tile
        tt = Table.read(faf,hdu='FASSIGN')
        tt['TILEID'] = tile
        tt = join(tt, tars, keys=['TARGETID'])

        if s == 0:
            ttn = tt
            s = 1
        else:
            ttn = vstack([ttn,tt], metadata_conflicts = 'silent')
        ttn.sort('TARGETID')
        n += 1
    ttn.write(fout,format='fits', overwrite=True)



#count_tiles_better(specf, 'mock', pdir)

def count_tiles_better(fs, somefile, fibcol='ZWARN'):
    '''
    from files with duplicates that have already been sorted by targetid, quickly go 
    through and get the multi-tile information
    dr is either 'dat' or 'ran'
    returns file with TARGETID,NTILE,TILES,TILELOCIDS
    '''
    
    #fs = fitsio.read('/global/cfs/cdirs/desi/survey/catalogs/SV3/LSS/'+specrel+'/datcomb_'+pd+'_specwdup_Alltiles.fits')
    #wf = fs['FIBERSTATUS'] == 0
    wf = fs[fibcol] == 0
    stlid = 10000*fs['TILEID'] +fs['LOCATION']
    gtl = np.unique(stlid[wf])
    
    fj = fitsio.read(somefile)
        #outf = '/global/cfs/cdirs/desi/survey/catalogs/SV3/LSS/datcomb_'+pd+'ntileinfo.fits' 
#    if dr == 'ran':
#        fj = fitsio.read('/global/cfs/cdirs/desi/survey/catalogs/SV3/LSS/'+specrel+'/rancomb_'+str(rann)+pd+'wdupspec_Alltiles.fits')
        #outf = '/global/cfs/cdirs/desi/survey/catalogs/SV3/LSS/random'+str(rann)+'/rancomb_'+pd+'ntileinfo.fits'
    wg = np.isin(fj['TILELOCID'],gtl)  
    fjg = fj[wg]  

    tids = np.unique(fjg['TARGETID'])
    nloc = []#np.zeros(len(np.unique(f['TARGETID'])))
    nt = []
    tl = []
    tli = []
    ti = 0
    i = 0
    while i < len(fjg):
        tls  = []
        tlis = []
        nli = 0
    
        while fjg[i]['TARGETID'] == tids[ti]:
            nli += 1
            tls.append(fjg[i]['TILEID'])
            tlis.append(fjg[i]['TILELOCID'])
            i += 1
            if i == len(fjg):
                break
        nloc.append(nli)
        tlsu = np.unique(tls)
        tlisu = np.unique(tlis)
        nt.append(len(tlsu))
        tl.append("-".join(tlsu.astype(str)))
        tli.append("-".join(tlisu.astype(str)))
      
        if ti%100000 == 0:
            print(ti)
        ti += 1 
    tc = Table()
    tc['TARGETID'] = tids
    tc['NTILE'] = nt
    tc['TILES'] = tl
    tc['TILELOCIDS'] = tli
    
    return tc
#specf,dz,imbits,type,bit,os.path.join(dirout,type+notqso+'_full_noveto.dat.fits'),os.path.join(ldirspec, 'Alltiles_dark_tilelocs.dat.fits'), azf=azf, desitarg=desitarg,specver=specrel,notqso=notqso
def mkfulldat(fs,zf,imbits,tp,bit,outf,ftiles,azf='',desitarg='SV3_DESI_TARGET',specver='daily',notqso='',qsobit=4,bitweightfile=None):
    '''
    fs is the spec sample
    zf is the name of the file containing all of the combined spec and target info compiled already
    imbits is the list of imaging mask bits to mask out
    tdir is the directory for the targets
    tp is the target type
    bit is the SV3_{type}_MASK bit to use for select the correct target type
    outf is the full path + name for the output file
    ftiles is the name of the file containing information on, e.g., how many tiles each target was available on
    azf is the file name for OII flux info (relevant for ELGs only)
    desitarg is the column to use for the target type cut (all use SV3_DESI_TARGET except BGS_BRIGHT)
    specver is the version of the pipeline used for the redshift info; only 'daily' exists for now
    '''


    #from desitarget.mtl import inflate_ledger
    if tp[:3] == 'BGS' or tp[:3] == 'MWS':
        pd = 'bright'
        tscol = 'TSNR2_BGS'
    else:
        pd = 'dark'
        tscol = 'TSNR2_ELG'
    #load in the appropriate dark/bright combined spec file and use to denote the tileid + location that had good observations:
    #fs = fitsio.read('/global/cfs/cdirs/desi/survey/catalogs/SV3/LSS/'+specver+'/datcomb_'+pd+'_specwdup_Alltiles.fits')
    if specver == 'daily':
        fbcol = 'FIBERSTATUS'
    elif specver == 'everest':
        fbcol = 'COADD_FIBERSTATUS'
    else:
        fbcol = 'FIBERSTATUS'

    wf = fs[fbcol] == 0
    stlid = 10000*fs['TILEID'] +fs['LOCATION']
    gtl = np.unique(stlid[wf])
    #gtl now contains the list of 'good' tilelocid

    #read in the big combined data file
    dz = Table.read(zf)
    #find the rows that satisfy the target type
    wtype = ((dz[desitarg] & bit) > 0)
    if notqso == 'notqso':
        print('removing QSO targets')
        wtype &= ((dz[desitarg] & qsobit) == 0)
    #find the rows that are 'good' tilelocid
    wg = np.isin(dz['TILELOCID'],gtl)
    print(len(dz[wtype]))
    print(len(dz[wg]))
    #down-select to target type of interest and good tilelocid
    dz = dz[wtype&wg]
    print('length after selecting type and fiberstatus == 0 '+str(len(dz)))
    print('length of unique targetid after selecting type and fiberstatus == 0 '+str(len(np.unique(dz['TARGETID']))))
    #find targets that were never available at the same location as a target of the same type that got assigned to a good location
    #those that were never available are assumed to have 0 probability of assignment so we want to veto this location
    lznp = find_znotposs(dz)
    wk = ~np.isin(dz['TILELOCID'],lznp)#dz['ZPOSS'] == 1
    dz = dz[wk] #0 probability locations now vetoed
    print('length after priority veto '+str(len(dz)))
    '''
    print('joining to full imaging')
    ftar = Table.read('/global/cfs/cdirs/desi/survey/catalogs/SV3/LSS/'+pd+'_targets.fits')
    ftar.keep_columns(['TARGETID','EBV','FLUX_G','FLUX_R','FLUX_Z','FLUX_IVAR_G','FLUX_IVAR_R','FLUX_IVAR_Z','MW_TRANSMISSION_G','MW_TRANSMISSION_R',\
            'MW_TRANSMISSION_Z','FRACFLUX_G','FRACFLUX_R','FRACFLUX_Z','FRACMASKED_G','FRACMASKED_R','FRACMASKED_Z','FRACIN_G','FRACIN_R',\
            'FRACIN_Z','NOBS_G','NOBS_R','NOBS_Z','PSFDEPTH_G','PSFDEPTH_R','PSFDEPTH_Z','GALDEPTH_G','GALDEPTH_R','GALDEPTH_Z','FLUX_W1',\
            'FLUX_W2','FLUX_IVAR_W1','FLUX_IVAR_W2','MW_TRANSMISSION_W1','MW_TRANSMISSION_W2','ALLMASK_G','ALLMASK_R','ALLMASK_Z','FIBERFLUX_G',\
            'FIBERFLUX_R','FIBERFLUX_Z','FIBERTOTFLUX_G','FIBERTOTFLUX_R','FIBERTOTFLUX_Z','WISEMASK_W1','WISEMASK_W2','MASKBITS',\
            'RELEASE','BRICKID','BRICKNAME','BRICK_OBJID','MORPHTYPE','PHOTSYS'])
    dz = join(dz,ftar,keys=['TARGETID'])
    print('length after join to full targets (should be same) '+str(len(dz)))
    
    #apply imaging veto mask
    dz = cutphotmask(dz,imbits)
    '''

    #load in file with information about where repeats occurred and join it
    dtl = Table.read(ftiles)
    dtl.keep_columns(['TARGETID','NTILE','TILES','TILELOCIDS'])
    dz = join(dz,dtl,keys='TARGETID')

    #find the rows where we have spectroscopic observations
    wz = dz['ZWARN'] != 999999 #this is what the null column becomes
    wz &= dz['ZWARN']*0 == 0 #just in case of nans
    #mark them as having LOCATION_ASSIGNED
    dz['LOCATION_ASSIGNED'] = np.zeros(len(dz)).astype('bool')
    dz['LOCATION_ASSIGNED'][wz] = 1
    #find the TILELOCID that were assigned and mark them as so
    tlids = np.unique(dz['TILELOCID'][wz])
    wtl = np.isin(dz['TILELOCID'],tlids)
    dz['TILELOCID_ASSIGNED'] = 0
    dz['TILELOCID_ASSIGNED'][wtl] = 1
    print('number of unique targets at assigned tilelocid:')
    print(len(np.unique(dz[wtl]['TARGETID'])))

    #get OII flux info for ELGs
    if tp == 'ELG' or tp == 'ELG_HIP':
        if azf != '':
            arz = fitsio.read(azf,columns=[fbcol,'TARGETID','LOCATION','TILEID','OII_FLUX','OII_FLUX_IVAR','SUBSET','DELTACHI2'])
            st = []
            for i in range(0,len(arz)):
                st.append(arz['SUBSET'][i][:4])
            st = np.array(st)
            wg = arz[fbcol] == 0
            wg &= st == "thru"
            arz = arz[wg]
            o2c = np.log10(arz['OII_FLUX'] * np.sqrt(arz['OII_FLUX_IVAR']))+0.2*np.log10(arz['DELTACHI2'])
            w = (o2c*0) != 0
            w |= arz['OII_FLUX'] < 0
            o2c[w] = -20
            #arz.keep_columns(['TARGETID','LOCATION','TILEID','o2c','OII_FLUX','OII_SIGMA'])#,'Z','ZWARN','TSNR2_ELG'])
            arz = Table(arz)
            arz['o2c'] = o2c
            dz = join(dz,arz,keys=['TARGETID','LOCATION','TILEID'],join_type='left',uniq_col_name='{col_name}{table_name}',table_names=['', '_OII'])

            dz.remove_columns(['SUBSET','DELTACHI2_OII',fbcol+'_OII'])
            print('check length after merge with OII strength file:' +str(len(dz)))

    if tp[:3] == 'QSO':
        if azf != '':
            arz = Table.read(azf)
            arz.keep_columns(['TARGETID','LOCATION','TILEID','Z','ZERR','Z_QN'])
            print(arz.dtype.names)
            #arz['TILE'].name = 'TILEID'
            dz = join(dz,arz,keys=['TARGETID','TILEID','LOCATION'],join_type='left',uniq_col_name='{col_name}{table_name}',table_names=['','_QF'])
            dz['Z'].name = 'Z_RR' #rename the original redrock redshifts
            dz['Z_QF'].name = 'Z' #the redshifts from the quasar file should be used instead

#CHECK HERE
    #sort and then cut to unique targetid; sort prioritizes observed targets and then TSNR2
    dz['sort'] = dz['LOCATION_ASSIGNED']
    #dz['sort'] = dz['TILELOCID_ASSIGNED']
    #dz['sort'] = dz['LOCATION_ASSIGNED']*dz[tscol]+dz['TILELOCID_ASSIGNED']
    dz.sort('sort')
    dz = unique(dz, keys=['TARGETID'],keep='last')
    if tp == 'ELG' or tp == 'ELG_HIP':
        print('number of masked oII row (hopefully matches number not assigned) '+ str(np.sum(dz['o2c'].mask)))
    if tp == 'QSO':
        print('number of good z according to qso file '+str(len(dz)-np.sum(dz['Z'].mask)))
    print('length after cutting to unique targetid '+str(len(dz)))
    print('LOCATION_ASSIGNED numbers')
    print(np.unique(dz['LOCATION_ASSIGNED'],return_counts=True))

    print('TILELOCID_ASSIGNED numbers')
    print(np.unique(dz['TILELOCID_ASSIGNED'],return_counts=True))

    probl = np.zeros(len(dz))
    #get completeness based on unique sets of tiles
    compa = []
    tll = []
    ti = 0
    print('getting completenes')
    #sorting by tiles makes things quicker with while statements below
    dz.sort('TILES')
    nts = len(np.unique(dz['TILES']))
    tlsl = dz['TILES']
    tlslu = np.unique(tlsl)
    laa = dz['LOCATION_ASSIGNED']

    i = 0
    while i < len(dz):
        tls  = []
        tlis = []
        nli = 0
        nai = 0

        while tlsl[i] == tlslu[ti]:
            nli += 1 #counting unique targetids within the given TILES value
            nai += laa[i] #counting the number assigned
            i += 1
            if i == len(dz):
                break

        if ti%1000 == 0:
            print('at tiles '+str(ti)+' of '+str(nts))
        cp = nai/nli #completeness is number assigned over number total
        compa.append(cp)
        tll.append(tlslu[ti])
        ti += 1
    #turn the above into a dictionary and apply it
    comp_dicta = dict(zip(tll, compa))
    fcompa = []
    for tl in dz['TILES']:
        fcompa.append(comp_dicta[tl])
    dz['COMP_TILE'] = np.array(fcompa)
    wc0 = dz['COMP_TILE'] == 0
    print('number of targets in 0 completeness regions '+str(len(dz[wc0])))

    #get counts at unique TILELOCID
    locl,nlocl = np.unique(dz['TILELOCID'],return_counts=True)
    #do same after cutting to only the data with location_assigned
    wz = dz['LOCATION_ASSIGNED'] == 1
    dzz = dz[wz]
    loclz,nloclz = np.unique(dzz['TILELOCID'],return_counts=True)
    natloc = ~np.isin(dz['TILELOCID'],loclz)
    print('number of unique targets left around unassigned locations is '+str(np.sum(natloc)))
    locs = np.copy(dz['TILELOCID'])
#
#
    print('reassigning TILELOCID for duplicates and finding rosette')
    #re-assigning "naked" targets; if we gave a targetid a tilelocid that was not assigned
    #by the same target was available at a location that was assigned, we re-assign its tilelocid
    nch = 0
    nbl = 0
    tlids = dz['TILELOCIDS']
    ros = np.zeros(len(dz))
    rosr = np.zeros(len(dz))
    for ii in range(0,len(dz['TILEID'])): #not sure why, but this only works when using loop for Table.read but array option works for fitsio.read
        ti = dz[ii]['TILEID']
        rosn = tile2rosette(ti) #get rosette id
        rosr[ii] = calc_rosr(rosn,dz[ii]['RA'],dz[ii]['DEC']) #calculates distance in degrees from rosette center
        ros[ii] = rosn
        if natloc[ii]:# == False:
            nbl += 1
            s = 0
            tids = tlids[ii].split('-')
            if s == 0:
                for tl in tids:
                    ttlocid  = int(tl)
                    if np.isin(ttlocid,loclz):
                        locs[ii] = ttlocid
                        nch += 1
                        s = 1
                        break
        if ii%10000 == 0:
            print(ii,len(dz['TILEID']),ti,ros[ii],nch,nbl)

    dz['TILELOCID'] = locs
    #get numbers again after the re-assignment
    locl,nlocl = np.unique(dz['TILELOCID'],return_counts=True)
    loclz,nloclz = np.unique(dzz['TILELOCID'],return_counts=True)

    dz['rosette_number'] = ros
    dz['rosette_r'] = rosr
    print('rosette number and the number on each rosette')
    print(np.unique(dz['rosette_number'],return_counts=True))
    print('getting fraction assigned for each tilelocid')
    #should be one (sometimes zero, though) assigned target at each tilelocid and we are now counting how many targets there are per tilelocid
    #probability of assignment is then estimated as 1/n_tilelocid
    nm = 0
    nmt =0
    pd = []
    for i in range(0,len(locl)):
        if i%10000 == 0:
            print('at row '+str(i))
        nt = nlocl[i]
        loc = locl[i]
        w = loclz == loc
        nz = 0
        if len(loclz[w]) == 1:
            nz = nloclz[w] #these are supposed all be 1...
        else:
            nm += 1.
            nmt += nt
        if len(loclz[w]) > 1:
            print('why is len(loclz[w]) > 1?') #this should never happen
        pd.append((loc,nz/nt))
    pd = dict(pd)
    for i in range(0,len(dz)):
        probl[i] = pd[dz['TILELOCID'][i]]
    print('number of fibers with no observation, number targets on those fibers')
    print(nm,nmt)

    dz['FRACZ_TILELOCID'] = probl
    print('sum of 1/FRACZ_TILELOCID, 1/COMP_TILE, and length of input; dont quite match because some tilelocid still have 0 assigned')
    print(np.sum(1./dz[wz]['FRACZ_TILELOCID']),np.sum(1./dz[wz]['COMP_TILE']),len(dz),len(dz[wz]))
    #dz['WEIGHT_ZFAIL'] = np.ones(len(dz))
    oct = np.copy(dz['COMP_TILE'])
    if bitweightfile is not None:
        fb = fitsio.read(bitweightfile)
        dz = join(dz,fb,keys=['TARGETID'])
    wz = dz['LOCATION_ASSIGNED'] == 1 #join re-ordered array, reget mask for assigned locations and check comp_tile
    print('length after join with bitweight file and sum of 1/comp_tile',len(dz),np.sum(1./dz[wz]['COMP_TILE']),len(dz[wz]))
    #print('check comp_tile array',np.array_equal(oct,dz['COMP_TILE']))


    #for debugging writeout
    for col in dz.dtype.names:
        to = Table()
        to[col] = dz[col]
        #print(col)
        try:
            to.write('temp.fits',format='fits', overwrite=True)
        except:
            print(col+' failed!')

    dz.write(outf,format='fits', overwrite=True)


def mkclusdat(fl,weightmd='tileloc',zmask=False,tp='',dchi2=9,tsnrcut=80,rcut=None,ntilecut=0,ccut=None,ebits=None,nreal=128):
    '''
    fl is the input file
    weighttileloc determines whether to include 1/FRACZ_TILELOCID as a completeness weight
    zmask determines whether to apply a mask at some given redshift
    tp is the target type
    dchi2 is the threshold for keeping as a good redshift
    tnsrcut determines where to mask based on the tsnr2 value (defined below per tracer)
    '''    
    ff = Table.read(fl)

    zcolumn = 'TRUEZ'
    rootname = fl.split('full_noveto')[0]

    if ebits is not None:
        print('number before imaging mask '+str(len(ff)))
        ff = cutphotmask(ff,ebits)
        print('number after imaging mask '+str(len(ff)))

    ff.write(rootname + 'full.dat.fits', overwrite=True, format='fits')

    wzm = ''
    if zmask:
        wzm = 'zmask_'
    if rcut is not None:
        wzm += 'rmin'+str(rcut[0])+'rmax'+str(rcut[1])+'_'
    if ntilecut > 0:
        wzm += 'ntileg'+str(ntilecut)+'_'    
    if ccut is not None:
        wzm += ccut+'_' #you could change this to however you want the file names to turn out

    if ccut == 'main':
        if tp != 'LRG':
            print('this is only defined for LRGs!' )
        else:
            lrgmaintar = fitsio.read('/global/cfs/cdirs/desi/survey/catalogs/main/LSS/LRGtargetsDR9v1.1.1.fits',columns=['TARGETID'])
            sel = np.isin(ff['TARGETID'],lrgmaintar['TARGETID'])
            print('numbers before/after cut:')
            print(len(ff),len(ff[sel]))
            ff = ff[sel]   
            ff.write(fl+wzm+'full.dat.fits',format='fits',overwrite='True')
    
    '''
    This is where redshift failure weights go
    '''

    ff['WEIGHT_ZFAIL'] = np.ones(len(ff))
    '''
    #The LRGs just have this fairly ad hoc model that AJR fit in the notebook, definitely needs refinement/automation
    if tp == 'LRG':
        fibfluxz = ff['FIBERFLUX_Z']/ff['MW_TRANSMISSION_Z']
        coeff = [117.46,-60.91,11.49,-0.513] #from polyfit, 3rd to zeroth order in 1/fiberflu
        efs = coeff[-1]+coeff[-2]*(1/fibfluxz)+coeff[-3]*(1/fibfluxz)**2.+coeff[-4]*(1/fibfluxz)**3.
        ems = erf((ff['TSNR2_LRG']-13.2)/39.7)*.9855
        ff['WEIGHT_ZFAIL'] = 1./(1. -(1.-ems)*efs)
    '''
    '''
    One could plug in imaging systematic weights here
    Probably better to put it here so that full file only gets written out once and includes
    all of the weights
    '''


    outf = rootname + wzm + 'clustering.dat.fits'
    wz = ff['ZWARN'] == 0
    print('length before cutting to objects with redshifts '+str(len(ff)))
    print('length after cutting to zwarn == 0 '+str(len(ff[wz])))
    
    if tp == 'QSO':
        #good redshifts are currently just the ones that should have been defined in the QSO file when merged in full
        wz = ff[zcolumn]*0 == 0
        wz &= ff[zcolumn] != 999999
        wz &= ff[zcolumn] != 1.e20
        wz &= ff['ZWARN'] != 999999
        wz &= ff['TSNR2_QSO'] > tsnrcut
    
    if tp == 'ELG' or tp == 'ELG_HIP':
        wz = ff['o2c'] > dchi2
        wz &= ff['ZWARN']*0 == 0
        wz &= ff['ZWARN'] != 999999
        print('length after oII cut '+str(len(ff[wz])))
        wz &= ff['LOCATION_ASSIGNED'] == 1
        print('length after also making sure location assigned '+str(len(ff[wz])))
        wz &= ff['TSNR2_ELG'] > tsnrcut
        print('length after tsnrcut '+str(len(ff[wz])))
    if tp == 'LRG':
        print('applying extra cut for LRGs')
        # Custom DELTACHI2 vs z cut from Rongpu
#        drz = (10**(3 - 3.5*ff[zcolumn]))
#        print(drz)
#        mask_bad = (drz>30) #& (ff['DELTACHI2']<30)
#        mask_bad |= (drz<30) & (ff['DELTACHI2']<drz)
#        mask_bad |= (ff['DELTACHI2']<10)
        wz &= ff[zcolumn]<1.4
#        wz &= (~mask_bad)

        #wz &= ff['DELTACHI2'] > dchi2
        print('length after Rongpu cut '+str(len(ff[wz])))
#        wz &= ff['TSNR2_ELG'] > tsnrcut
#        print('length after tsnrcut '+str(len(ff[wz])))

    if tp[:3] == 'BGS':
        print('applying extra cut for BGS')
        wz &= ff['DELTACHI2'] > dchi2
        print('length after dchi2 cut '+str(len(ff[wz])))
        wz &= ff['TSNR2_BGS'] > tsnrcut
        print('length after tsnrcut '+str(len(ff[wz])))


    
    ff = ff[wz]
    print('length after cutting to good z '+str(len(ff)))
    print('minimum,maximum Z',min(ff[zcolumn]),max(ff[zcolumn]))
    ff['WEIGHT'] = ff['WEIGHT_ZFAIL']
    if weightmd == 'tileloc':
        ff['WEIGHT'] *= 1./ff['FRACZ_TILELOCID']
    if weightmd == 'probobs' :         
        nassign = nreal*ff['PROB_OBS']+1 #assignment in actual observation counts
        ff['WEIGHT'] *= (nreal+1)/nassign#1./ff['PROB_OBS']
        print(np.min(ff['WEIGHT']),np.max(ff['WEIGHT']))
        #wzer = ff['PROB_OBS'] == 0
        #ff['WEIGHT'][wzer] = 0
        #print(str(len(ff[wzer]))+' galaxies with PROB_OBS 0 getting assigned weight of 0 (should not happen, at minimum adjust weights to reflect 1 real realization happened)')
    if zmask:
        whz = ff['Z'] < 1.6
        ff = ff[whz]

        fzm = fitsio.read('/global/homes/m/mjwilson/desi/DX2DROPOUT/radial_mask.fits')
        zma = []
        for z in ff['Z']:
            zind = int(z/1e-6)
            zma.append(fzm[zind]['RADIAL_MASK'])        
        zma = np.array(zma)
        wm = zma == 0
        ff = ff[wm]    
    #apply any cut on rosette radius
    if rcut is not None:
        wr = ff['rosette_r'] > rcut[0]
        wr &= ff['rosette_r'] <  rcut[1]
        print('length before rosette radius cut '+str(len(ff)))
        ff = ff[wr]
        print('length after rosette radius cut '+str(len(ff)))
    #apply cut on ntile
    if ntilecut > 0:
        print('length before ntile cut '+str(len(ff)))
        wt = ff['NTILE'] > ntilecut
        ff = ff[wt]
        print('length after ntile cut '+str(len(ff)))    
    if ccut == 'notQSO':
        wc = (ff['SV3_DESI_TARGET'] & sv3_targetmask.desi_mask['QSO']) ==  0
        print('length before cutting to not QSO '+str(len(ff)))
        ff = ff[wc]
        print('length after cutting to not QSO '+str(len(ff)))
    if ccut == 'zQSO':
        wc = ff['SPECTYPE'] ==  'QSO'
        print('length before cutting to spectype QSO '+str(len(ff)))
        ff = ff[wc]
        print('length after cutting to spectype QSO '+str(len(ff)))

    #select down to specific columns below and then also split N/S

#    wn = ff['PHOTSYS'] == 'N'
    #if tp[:3] == 'BGS':
    #    kl = ['RA','DEC','Z','WEIGHT','TARGETID','NTILE','rosette_number','rosette_r','TILES','WEIGHT_ZFAIL','FRACZ_TILELOCID']
    #else:
    ff['Z'] = ff[zcolumn]
    kl = ['RA','DEC','Z','WEIGHT','TARGETID','NTILE','rosette_number','rosette_r','TILES','WEIGHT_ZFAIL','FRACZ_TILELOCID']#,'BITWEIGHTS']   # 'PROB_OBS',
    if tp[:3] == 'BGS':
        ff['flux_r_dered'] = ff['FLUX_R']/ff['MW_TRANSMISSION_R']
        kl.append('flux_r_dered')
        print(kl)

    ff.keep_columns(kl)#,'PROB_OBS'
    print('minimum,maximum weight')
    print(np.min(ff['WEIGHT']),np.max(ff['WEIGHT']))
    ff.write(outf,format='fits', overwrite=True)

#    outfn = fl+wzm+'N_clustering.dat.fits'
#    ff[wn].write(outfn,format='fits', overwrite=True)
#    outfn = fl+wzm+'S_clustering.dat.fits'
#    ff[~wn].write(outfn,format='fits', overwrite=True)
