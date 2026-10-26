#!/usr/bin/env python3
"""Search fixed-length internal routes; retain failed candidates without accepting them.

The two worker processes perform local numerical calculations, not agent tasks.
Run the independent geometry and CAD checks before using any resulting route.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
import argparse,concurrent.futures,hashlib,json,sys,time
from pathlib import Path
import numpy as np
from scipy.interpolate import BSpline
from scipy.optimize import minimize
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from internal_harness_geometry import evaluate
from thermal_cable_geometry import spline

spec=json.loads((ROOT/'assembly/internal-charge-r02/harness.json').read_text())
nom=np.array([w['controls_mm'] for w in spec['wires']]);n=len(nom[0]);spans=n-3
cases=json.loads((ROOT/'mechanical/swim-r11-thermal-fit/retention-checks.json').read_text())['cable_motion']['cases']
parts=[p for p in json.loads((ROOT/'mechanical/swim-r11-thermal-fit/antenna-fit.json').read_text())['scenarios'][2]['parts'] if p['ref']!='J3']
low=np.array([[*p['envelope_xy_bounds_mm'][:2],p['envelope_z_mm'][0]] for p in parts]);high=np.array([[*p['envelope_xy_bounds_mm'][2:],p['envelope_z_mm'][1]] for p in parts])
k=np.r_[np.zeros(4),np.arange(1,spans)/spans,np.ones(4)];bs=BSpline(k,np.eye(n),3);tt=np.linspace(0,1,401)
B=bs(tt);D=bs(tt,1);A=bs(tt,2)
g,w=np.polynomial.legendre.leggauss(20);qt=np.concatenate([(g+1)/2/spans+i/spans for i in range(spans)]);qw=np.tile(w/2/spans,spans);QD=bs(qt,1)
def lengths(c):return np.array([np.sum(np.linalg.norm(QD@wire,axis=1)*qw) for wire in c])
target=lengths(nom)
seeds=json.loads((ROOT/'assembly/internal-charge-r02/motion-seeds.json').read_text())['poses']
weights=np.array([0,0,.5,.8,1,1,1,1])[:,None]

def solve(index):
 case=cases[index];shift=np.array(case['pcb_pose_mm'])-np.array([0,0,spec['pcb_nominal_top_mm']])
 initial=nom+weights*shift;initial[:,-2:]=nom[:,-2:]+shift
 initial[:,2:-2]=np.array(seeds[index]['controls_mm'])[:,2:-2]
 lo,hi=low+shift,high+shift
 rf=[spline(c['control_points_mm'],1501) for c in case['cables']];trees=[cKDTree(c[0]) for c in rf]
 def unpack(v):
  c=initial.copy();c[:,2:-2]=np.array(v[:-4]).reshape(2,n-4,3)
  scale=np.array(v[-4:]).reshape(2,2)
  c[:,1]=c[:,0]+scale[:,0,None]*(initial[:,1]-initial[:,0])
  c[:,-2]=c[:,-1]+scale[:,1,None]*(initial[:,-2]-initial[:,-1]);return c
 def scores(v,full=False):
  c=unpack(v);xyz=np.array([B@wire for wire in c]);v1=np.array([D@wire for wire in c]);v2=np.array([A@wire for wire in c]);speed=np.linalg.norm(v1,axis=2);cross=np.linalg.norm(np.cross(v1,v2),axis=2)
  radius=speed**3/np.maximum(cross,1e-12)
  arc=np.concatenate([np.zeros((2,1)),np.cumsum(np.linalg.norm(np.diff(xyz,axis=1),axis=2),axis=1)],axis=1);remain=arc[:,-1,None]-arc
  stripped=np.minimum((arc-1.0)/.49,(remain-1.6)/.49)
  rad=.17+.15+.06+np.clip(stripped,0,1)*(.3302-.17)
  obstacles=np.linalg.norm(np.maximum(0,np.maximum(lo[:,None,None,:]-xyz[None,:,:,:],xyz[None,:,:,:]-hi[:,None,None,:])),axis=3).min(axis=0)-rad
  rf_gap=np.array([np.min(np.array([tree.query(p)[0]-.715-data[3]/2 for tree,data in zip(trees,rf)]),axis=0) for p in xyz])-rad
  pair=cKDTree(xyz[0]).query(xyz[1])[0]-2*(.3302+.15+.06)
  roof=17.85-xyz[:,:,2]-rad;side=17.1-np.abs(xyz[:,:,1])-rad
  wall=20.7-np.abs(xyz[:,:,0])-rad;wall[:,:35]=1
  boardgap=xyz[:,:,2]-case['pcb_pose_mm'][2]-(.3302+.15+.06);boardgap[:,-13:]=1;boardgap[xyz[:,:,0]>20.2]=1
  margins=[(radius-6.85)/2,obstacles-.26,rf_gap-.26,pair[None,:]-.25,roof,side,wall,boardgap]
  penalty=sum(float(np.sum(np.minimum(m,0)**2)) for m in margins)
  if full:return dict(penalty=penalty,parts=obstacles.min(1).tolist(),RF=rf_gap.min(1).tolist(),pair=float(pair.min()),radius=radius.min(1).tolist(),roof=roof.min(1).tolist(),length_errors_mm=(lengths(c)-target).tolist(),controls=c.tolist())
  return penalty
 x=np.r_[initial[:,2:-2].ravel(),np.ones(4)];bounds=[]
 for p in x[:-4].reshape(-1,3):
  bounds += [(max(-21,p[0]-4),min(21,p[0]+4)),(max(-22,p[1]-4),min(22,p[1]+4)),(max(9,p[2]-4),min(22,p[2]+4))]
 bounds += [(.35,1.8)]*4
 start=time.time()
 r=minimize(scores,x,method='SLSQP',bounds=bounds,constraints={'type':'eq','fun':lambda v:lengths(unpack(v))-target},options={'maxiter':400,'ftol':1e-10})
 result=scores(r.x,True);result.update(pose_index=index,pcb_pose_mm=case['pcb_pose_mm'],optimizer_message=r.message,elapsed_s=time.time()-start,physical_qualification=False,validation_status='SEARCH_ONLY_REQUIRES_INDEPENDENT_DENSE_AND_CAD_CHECKS')
 return result

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args()
 print('Fixed lengths',target.tolist(),flush=True)
 rows=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for result in pool.map(solve,range(len(cases))):
   rows.append(result)
   print(json.dumps({k:result[k] for k in ['pose_index','penalty','length_errors_mm','elapsed_s','optimizer_message']}),flush=True)
 paths=[ROOT/'assembly/internal-charge-r02/harness.json',ROOT/'assembly/internal-charge-r02/motion-seeds.json',ROOT/'mechanical/swim-r11-thermal-fit/retention-checks.json',ROOT/'mechanical/swim-r11-thermal-fit/antenna-fit.json',ROOT/'scripts/thermal_cable_geometry.py',Path(__file__)]
 report=dict(result='SEARCH_ONLY_NOT_ACCEPTANCE',inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
             fixed_lengths_mm=target.tolist(),poses=rows,
             zero_penalty_candidates=sum(r['penalty']<=1e-10 and max(abs(e) for e in r['length_errors_mm'])<=.001 for r in rows),
             physical_qualification=False,manufacturing_release=False,
             limits=['Sampled optimization objective is not the independent continuous geometry check.',
                     'No full body, native pad bond, joint, frame, self-clearance, thermal length or service/flex acceptance.',
                     'All end positions and tangent directions remain fixed to their owning parts; tangent magnitudes can vary.',
                     'A positive local minimum does not prove routing is impossible.'])
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(report,indent=2)+'\n')
 print('Zero-penalty candidates',report['zero_penalty_candidates'],'of',len(rows),flush=True)
