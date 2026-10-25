#!/usr/bin/env python3
"""Localize report thumbnails by copper correlation; candidates, not proof."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.signal import fftconvolve
from scipy.ndimage import uniform_filter
R=Path(__file__).resolve().parents[1]/'evidence/jlc-dfm-20261025-r5'
im=Image.open(R/'front-copper.png').convert('RGBA').resize((1400,1120),Image.Resampling.LANCZOS)
im=Image.alpha_composite(Image.new('RGBA',im.size,'white'),im).convert('L')
copper=(np.asarray(im)<128).astype('float32')
for name in ['mask-trace-example','negative-mask-example']:
 a=np.asarray(Image.open(R/(name+'.png')).convert('RGB'),dtype='int16')
 temp=(((a[:,:,0]>70)|(a[:,:,1]>50)) & ((a.max(axis=2)-a.min(axis=2))>25)).astype('uint8')*255
 results=[]
 for scale in np.arange(.30,.651,.025):
  base=np.asarray(Image.fromarray(temp).resize((round(temp.shape[1]*scale),round(temp.shape[0]*scale)),Image.Resampling.BILINEAR),dtype='float32')/255
  for rotation in range(4):
   t=np.rot90(base,rotation).copy();h,w=t.shape;t-=t.mean()
   mean=uniform_filter(copper,size=(h,w),mode='constant')
   variance=np.maximum(mean-mean*mean,1e-8)
   score=fftconvolve(copper,t[::-1,::-1],mode='same')/(h*w*max(float(t.std()),1e-8)*np.sqrt(variance))
   score[:h,:]=score[-h:,:]=score[:,:w]=score[:,-w:]=-2
   y,x=np.unravel_index(score.argmax(),score.shape)
   results.append({'score':float(score[y,x]),'scale':float(scale),'rotation':rotation,'x_px':int(x),'y_px':int(y),'size_px':[w,h],
                   'x_mm':100+x/40,'y_mm':100+y/40})
 results.sort(key=lambda x:-x['score'])
 (R/(name+'-locations.json')).write_text(json.dumps(results[:12],indent=2)+'\n')
 print(name,results[:3],flush=True)
 for i,r in enumerate(results[:3]):
  x,y=r['x_px'],r['y_px'];w,h=r['size_px']
  im.crop((x-w//2,y-h//2,x+(w+1)//2,y+(h+1)//2)).resize((600,600)).save(R/(name+f'-match-{i}.png'))
