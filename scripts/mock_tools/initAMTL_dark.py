import os
import errno
def test_dir(value):
    if not os.path.exists(value):
        try:
            os.makedirs(value, 0o755)
            print('made ' + value)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

path = '/global/cfs/cdirs/desi/survey/catalogs/Y1/mocks/SecondGenMocks/AbacusSummit_v4_1'
for i in range(1,25):
    print(i) 
    test_dir('%s/altmtl%d/Univ000'%(path,i))
    os.system('cp -Rf %s/altmtl%d/initled/main %s/altmtl%d/Univ000/.' %(path, i, path, i))
    os.system('cp %s/altmtl0/Univ000/*.ecsv %s/altmtl%d/Univ000/.' %(path, path, i))
