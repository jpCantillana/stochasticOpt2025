import sys
import random
# from constants import *

num_custs=int(sys.argv[1])
num_scens=int(sys.argv[2])
num_sampl=int(sys.argv[3])

sfname=str(num_custs) + '_custs_' + str(num_scens) + '_sampleM_' + str(num_sampl) + '_scens_cust_demand_rec_cost_scens.txt'
prb=(1/(1.0*num_scens))
sf=open("jp_instances" + '/' + sfname,'w')
h='Probability,'
for i in range(0,num_custs):
    h = h + 'Customer ' + str(i) + ' demand,'
for i in range(0,num_custs):
    h = h + 'Customer ' + str(i) + ' per-unit-recourse dedicated cost,'

sf.write(h + '\n')

for s in range(0,num_scens):
    l=str(prb)
    for i in range(0,num_custs):
        dm=random.triangular(1.0957,7.2870,4.3214)
        l = l + ',' + str(dm)
    for i in range(0,num_custs):
        rc=random.randint(100,140)
        l = l + ',' + str(rc)
    sf.write(l + '\n')
sf.close()
