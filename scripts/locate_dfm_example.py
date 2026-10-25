#!/usr/bin/env python3
"""Locate the report's coordinate-free thumbnail in rendered board copper.

Image correlation is only candidate localization. Confirm coordinates against
actual Gerber/KiCad geometry before accepting any electrical conclusion.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.signal import fftconvolve
from scipy.ndimage import uniform_filter

ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/jlc-dfm-20261024-r2'
report=Image.open(E/'page-2.png').convert('RGB').crop((614,939,788,1113))
arr=np.asarray(report);template=((arr[:,:,0]>50)&(arr[:,:,1]<70)).astype('float32')
results=[]
for side in ['bottom','top']:
    im=Image.open(E/f'{side}-nodrill.png').convert('RGBA')
    white=Image.alpha_composite(Image.new('RGBA',im.size,'white'),im).convert('L')
    copper=(np.asarray(white)<128).astype('float32')
    for scale in np.arange(.65,1.001,.025):
        size=round(template.shape[0]*scale)
        base=np.asarray(Image.fromarray((template*255).astype('uint8')).resize((size,size),Image.Resampling.BILINEAR),dtype='float32')/255
        # Standard normalized correlation over every candidate board window.
        means=uniform_filter(copper,size=size,mode='constant')
        seconds=uniform_filter(copper*copper,size=size,mode='constant')
        den=np.sqrt(np.maximum(seconds-means*means,1e-8))
        for mirror in [False,True]:
            for rotation in range(4):
                t=np.rot90(np.fliplr(base) if mirror else base,rotation).copy();t-=t.mean()
                score=fftconvolve(copper,t[::-1,::-1],mode='same')/(size*size*max(float(t.std()),1e-8)*den)
                score[:size,:]=score[-size:,:]=score[:,:size]=score[:,-size:]=-2
                iy,ix=np.unravel_index(score.argmax(),score.shape)
                results.append({'side':side,'scale':float(scale),'mirror':mirror,'rotation':rotation,'x_px':int(ix),'y_px':int(iy),'score':float(score[iy,ix]),'x_mm':100+ix/80,'y_mm':100+iy/80,'size_px':size})
    print(side,sorted([r for r in results if r['side']==side],key=lambda r:-r['score'])[:3],flush=True)
results.sort(key=lambda r:-r['score']);(E/'thumbnail-match.json').write_text(json.dumps(results[:20],indent=2)+'\n')
for i,r in enumerate(results[:5]):
    im=Image.open(E/f"{r['side']}-nodrill.png").convert('RGBA')
    im=Image.alpha_composite(Image.new('RGBA',im.size,'white'),im).convert('RGB')
    n=r['size_px'];x=r['x_px'];y=r['y_px'];im.crop((x-n//2,y-n//2,x+(n+1)//2,y+(n+1)//2)).resize((600,600)).save(E/f'candidate-{i}.png')
print(json.dumps(results[:5],indent=2))
