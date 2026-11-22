"""Trace every number the 2.1.4 script says to final_table.md. Run: python3 scripts/check_numbers.py"""
import re
D={}
sf=None
for l in open("results/final_table.md"):
    m=re.match(r"### SF(\d+)",l)
    if m: sf=int(m.group(1)); continue
    if l.startswith("|") and sf and not l.startswith("|---") and not l.startswith("| Config"):
        c=[x.strip() for x in l.strip().strip("|").split("|")]
        if c[7]=="-": continue
        n=float
        D[(sf,c[0])]=dict(fi=n(c[1]),fr=n(c[2]),ft=n(c[3]),fc=n(c[4])+n(c[5]),di=n(c[6]),dr=n(c[7]),dt=n(c[8]),dc=n(c[9])+n(c[10]),six=n(c[11]))
def R(sf,c):
    d=D[(sf,c)];idle=d['fi']+6*d['di'];run=d['fr']+6*d['dr'];return dict(idle=idle,run=run,tot=idle+run,cost=d['fc']+d['six'])
ok=True
def chk(name,val,lo,hi):
    global ok
    p=lo<=val<=hi; ok&=p
    print(("PASS" if p else "FAIL"),name,round(val,2),f"(want {lo} to {hi})")
# hook
chk("hook warehouse SF1000 $",R(1000,"wh_large")['cost'],8.95,9.10)
chk("hook standard SF1000 $",R(1000,"srv_standard")['cost'],1.58,1.66)
chk("hook standard idle min of 48",R(1000,"srv_standard")['idle'],19,21)
chk("hook standard total min",R(1000,"srv_standard")['tot'],47.5,48.5)
# verdict
for sf,v in ((100,0.75),(1000,1.62),(10000,7.52)): chk(f"standard SF{sf} $",R(sf,"srv_standard")['cost'],v-0.03,v+0.03)
chk("best classic job SF1000 (xlarge) $",R(1000,"jc_xlarge")['cost'],1.57,1.63)
chk("spot SF10000 $",R(10000,"jc_2xlarge_spot")['cost'],4.6,4.66)
chk("2xl on demand SF10000 $",R(10000,"jc_2xlarge")['cost'],6.6,6.66)
# serverless
chk("optimized SF1000 min",R(1000,"srv_optimized")['tot'],25,27)
chk("optimized SF1000 $",R(1000,"srv_optimized")['cost'],5.4,5.46)
chk("optimized/standard price ratio SF1000",R(1000,"srv_optimized")['cost']/R(1000,"srv_standard")['cost'],3.3,3.6)
chk("optimized/standard speed ratio SF1000",R(1000,"srv_standard")['tot']/R(1000,"srv_optimized")['tot'],1.8,2.0)
chk("optimized SF10000 $",R(10000,"srv_optimized")['cost'],14.05,14.15)
chk("medium cap SF10000 min",R(10000,"srv_medium")['tot'],40,41.5)
chk("medium cap SF10000 $",R(10000,"srv_medium")['cost'],11.1,11.2)
chk("optimized SF10000 min",R(10000,"srv_optimized")['tot'],56.5,57.5)
for sf in (100,1000):
    chk(f"small cap vs optimized speed SF{sf}",R(sf,"srv_small")['tot']/R(sf,"srv_optimized")['tot'],0.95,1.1)
    chk(f"small cap vs optimized cost SF{sf}",R(sf,"srv_small")['cost']/R(sf,"srv_optimized")['cost'],0.9,1.1)
# classic
for sf in (100,1000,10000):
    sp,od=R(sf,"jc_2xlarge_spot"),R(sf,"jc_2xlarge")
    chk(f"spot cost saving % SF{sf}",100*(1-sp['cost']/od['cost']),15,32)
    chk(f"spot extra time % SF{sf}",100*(sp['tot']/od['tot']-1),3,15)
chk("photon off cost SF100 cheaper (ratio)",R(100,"jc_2xlarge_nophoton")['cost']/R(100,"jc_2xlarge")['cost'],0.8,0.95)
chk("photon off cost % more SF1000",100*(R(1000,"jc_2xlarge_nophoton")['cost']/R(1000,"jc_2xlarge")['cost']-1),12,16)
chk("photon off time % longer SF1000",100*(R(1000,"jc_2xlarge_nophoton")['tot']/R(1000,"jc_2xlarge")['tot']-1),43,47)
chk("photon off cost x SF10000",R(10000,"jc_2xlarge_nophoton")['cost']/R(10000,"jc_2xlarge")['cost'],2.5,2.7)
chk("photon off time x SF10000",R(10000,"jc_2xlarge_nophoton")['tot']/R(10000,"jc_2xlarge")['tot'],2.4,2.6)
chk("min2 idle SF1000 (20 to 14)",R(1000,"jc_2xlarge_min2")['idle'],13,14.5)
chk("2xl idle SF1000",R(1000,"jc_2xlarge")['idle'],20,21)
chk("min2 cost % more SF1000",100*(R(1000,"jc_2xlarge_min2")['cost']/R(1000,"jc_2xlarge")['cost']-1),16,20)
for sf in (100,1000,10000):
    chk(f"all-purpose vs 2xl cost x SF{sf}",R(sf,"ap_2xlarge")['cost']/R(sf,"jc_2xlarge")['cost'],1.9,2.2)
for sf in (100,1000):
    r=R(sf,"jc_2xlarge");chk(f"classic idle share % SF{sf}",100*r['idle']/r['tot'],40,60)
chk("8xl slower/dearer than optimized SF1000 (cost x)",R(1000,"jc_8xlarge")['cost']/R(1000,"srv_optimized")['cost'],1.3,1.4)
# warehouse
for sf,m in ((100,17),(1000,18),(10000,31)): chk(f"warehouse SF{sf} min",R(sf,"wh_large")['tot'],m-0.6,m+0.6)
chk("warehouse SF100 $",R(100,"wh_large")['cost'],11.2,11.3)
chk("warehouse/standard SF100 x (15x)",R(100,"wh_large")['cost']/R(100,"srv_standard")['cost'],14.5,15.5)
chk("warehouse SF1000 $ and highest",R(1000,"wh_large")['cost'],8.95,9.1)
print("warehouse highest at SF1000:",max(D,key=lambda k:R(*k)['cost'] if k[0]==1000 else 0)[1])
chk("warehouse SF10000 $",R(10000,"wh_large")['cost'],13.4,13.5)
print("\nALL PASS" if ok else "\nSOME FAIL")
