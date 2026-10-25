#!/usr/bin/env python3
"""Inspect actual binary STL topology; extracted from the preserved r11 exporter."""
import collections
import hashlib
import math
import struct
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def inspect(path, allow_separate=False):
    data=path.read_bytes();n=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*n,'Expected binary STL'
    points={};faces=[];bounds=[[math.inf]*3,[-math.inf]*3];volume=0.;degenerate=0
    for i in range(n):
        record=struct.unpack_from('<12fH',data,84+50*i)
        xyz=[record[3+j*3:6+j*3] for j in range(3)];face=[]
        for v in xyz:
            assert all(math.isfinite(x) for x in v)
            q=tuple(round(x,5) for x in v)
            if q not in points:points[q]=len(points)
            face.append(points[q])
            for axis in range(3):bounds[0][axis]=min(bounds[0][axis],v[axis]);bounds[1][axis]=max(bounds[1][axis],v[axis])
        if len(set(face))<3:degenerate+=1
        faces.append(face)
        a,b,c=xyz
        volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    edges=collections.defaultdict(list);parent=list(range(n))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,f in enumerate(faces):
        for a,b in zip(f,f[1:]+f[:1]):edges[tuple(sorted([a,b]))].append((i,1 if a<b else -1))
    for items in edges.values():
        for i,_ in items[1:]:parent[find(i)]=find(items[0][0])
    bad=sum(len(x)!=2 or sum(v for _,v in x)!=0 for x in edges.values())
    components=len({find(i) for i in range(n)})
    result=dict(file=path.name,sha256=sha(path),triangles=n,vertices=len(points),bounds_mm=bounds,
                dimensions_mm=[bounds[1][i]-bounds[0][i] for i in range(3)],signed_volume_mm3=volume,
                bad_edge_count=bad,collapsed_faces_at_1e_5mm=degenerate,connected_surfaces=components,
                closed_oriented_manifold=bad==0 and degenerate==0 and (components==1 or allow_separate) and volume>0)
    assert result['closed_oriented_manifold'],result
    return result
