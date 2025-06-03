import random
import math
import sys

rev_range=[1,5] #inst 3
rev_range=[1,10] #inst 1
rev_range=[1,20] #inst 2 
#pct_cap=[.05,.15]
sze_range=[1,10]


nitems=int(sys.argv[1])
cap=int(sys.argv[2])
nscen=int(sys.argv[3])

#mode=int((cap*1.0)/(nitems))
#left=mode-mode*left_offset
#if left < 0:
    #left=0
#right=mode+mode*left_offset

print('Number items,' + str(nitems))
print('Number scenarios,' + str(nscen))
print('Capacity,' + str(cap))
print('Item,Revenue')
for i in range(0,nitems):
	print(str(i) + ',' + str(random.randrange(rev_range[0],rev_range[1])))

s='Scenario,probability,'
for i in range(0,nitems):
	s = s + 'Item ' + str(i) + ' weight,'

#lrange=avg - offset*cap #int(pct_cap[0]*cap)
#if lrange < minp:
	#lrange=minp
#hrange=avg + int(offset*cap)

print(s)
prob=(1.0/nscen)
for p in range(0,nscen):
	s=str(p) + ',' + str(prob) + ','
	for i in range(0,nitems):
		sz=0
		#while sz <= 0:
		#sz=random.randrange(lrange,hrange)
		#sz=math.ceil(random.triangular(left,mode,right))
		#sz=math.ceil(random.randrange(math.ceil(left),math.ceil(right)))
		sz=math.ceil(random.uniform(sze_range[0],sze_range[1]))
		s = s + str(sz) + ','	
	print(s)
