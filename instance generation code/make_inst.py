import random
from constants import *

legs={}
customers={}

f=open(DATA_DIR + '/consol_points.txt','w')
f.write('Consolidation point\n')
for o in orig_consol_points:
    f.write(o + '\n')

for d in dest_consol_points:
    f.write(d + '\n')
f.close()

f=open(DATA_DIR + '/legs.txt','w')
f.write('Leg origin,Leg destination,travel time in days\n')
for o in orig_consol_points:
    for d in dest_consol_points:
        lg=(o,d)
        ttime=random.randint(lh_leg_day_range[0],lh_leg_day_range[1])
        f.write(o + ',' + d + ',' + str(ttime) + '\n')
        legs[lg]=ttime
f.close()

f=open(DATA_DIR + '/customers.txt','w')
f.write('Customer index,Pickup day,Service,Per-unit revenue,Dedicated jet per-unit cost\n')
fd=days[0]
ld=days[-1]-1
custs={}
for i in range(0,num_custs):
    pd=random.randint(fd,ld)
    svc=min_svc + random.randint(svc_buffer[0],svc_buffer[1])
    rev=random.randint(per_unit_rev_range[0],per_unit_rev_range[1])
    ded_cost=random.randint(per_unit_ded_lh_cost[0],per_unit_ded_lh_cost[1])
    custs[i]=[pd,svc,rev]
    f.write(str(i) + ',' + str(pd) + ',' + str(svc) + ',' + str(rev) + ',' + str(ded_cost) + '\n')

f=open(DATA_DIR + '/cust_consol_moves.txt','w')
f.write('Customer index,Origin consolidation point,travel time from customer origin (in days),per-unit cost\n')
for i in range(0,num_custs):
    for o in orig_consol_points:
        ttime=random.randint(sh_leg_day_range[0],sh_leg_day_range[1])
        pucost=random.randint(per_unit_sh_cost_range[0],per_unit_sh_cost_range[1])
        s=str(i) + ',' + o + ',' + str(ttime) + ',' + str(pucost)
        f.write(s + '\n')
f.close()

f=open(DATA_DIR + '/consol_cust_moves.txt','w')
f.write('Customer index,Dest consolidation point,travel time to customer destination (in days),per-unit cost\n')
for i in range(0,num_custs):
    for d in dest_consol_points:
        ttime=random.randint(sh_leg_day_range[0],sh_leg_day_range[1])
        pucost=random.randint(per_unit_sh_cost_range[0],per_unit_sh_cost_range[1])
        s=str(i) + ',' + d + ',' + str(ttime) + ',' + str(pucost)
        f.write(s + '\n')
f.close()

f=open(DATA_DIR + '/passenger_cargo_legs.txt','w')
f.write('Origin consol point,Destination consol point,Day,fixed cost per block,capacity per block,maximum # blocks\n')
for dy in days:
    for ((o,d),ttime) in legs.items():
        fc=ttime*conv_lh_ttime_cost    
        f.write(o + ',' + d + ',' + str(dy) + ',' + str(fc) + ',' + str(cap_lh_cap_block) + ',' + str(max_lh_cap_blocks_day) + '\n')


