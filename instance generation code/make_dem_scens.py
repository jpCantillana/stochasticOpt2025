import sys
import random
from constants import *

num_custs=int(sys.argv[1])
num_scens=int(sys.argv[2])

prb=(1/(1.0*num_scens))
sfname=str(num_custs) + '_custs_' + str(num_scens) + '_scens_cust_demand_scens.txt'
sf=open(DATA_DIR + '/' + sfname,'w')
h='Probability,'
for i in range(0,num_custs):
    h = h + 'Customer ' + str(i) + ' demand,'

sf.write(h + '\n')

for s in range(0,num_scens):
    l=str(prb)
    for i in range(0,num_custs):
        dm=random.triangular(dem_tri_low,dem_tri_high,dem_tri_mode)
        l = l + ',' + str(dm)
    sf.write(l + '\n')
sf.close()
