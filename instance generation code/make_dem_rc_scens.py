import sys
import random
from constants import *

num_custs=int(sys.argv[1])
num_scens=int(sys.argv[2])

sfname=str(num_custs) + '_custs_' + str(num_scens) + '_scens_cust_demand_rec_cost_scens.txt'
prb=(1/(1.0*num_scens))
sf=open(DATA_DIR + '/' + sfname,'w')
h='Probability,'
for i in range(0,num_custs):
    h = h + 'Customer ' + str(i) + ' demand,'
for i in range(0,num_custs):
    h = h + 'Customer ' + str(i) + ' per-unit-recourse dedicated cost,'

sf.write(h + '\n')

for s in range(0,num_scens):
    l=str(prb)
    for i in range(0,num_custs):
        dm=random.triangular(dem_tri_low,dem_tri_high,dem_tri_mode)
        l = l + ',' + str(dm)
    for i in range(0,num_custs):
        rc=random.randint(rc_low,rc_high)
        l = l + ',' + str(rc)
    sf.write(l + '\n')
sf.close()
