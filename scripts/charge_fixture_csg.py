"""Manifold construction of the same polygon-cylinder forming-tool definition."""
import struct
import numpy as np
import manifold3d as m


def read_stl(path):
    data=path.read_bytes();count=struct.unpack_from('<I',data,80)[0]
    if len(data)!=84+50*count:raise ValueError('Expected binary STL')
    triangles=np.array([struct.unpack_from('<12fH',data,84+i*50)[3:12] for i in range(count)],dtype=np.float32).reshape(-1,3)
    vertices,inverse=np.unique(triangles,axis=0,return_inverse=True)
    solid=m.Manifold(m.Mesh(vertices,inverse.reshape(-1,3).astype(np.uint32)))
    if solid.status()!=m.Error.NoError:raise ValueError(str(solid.status()))
    return solid


def write_stl(solid,path):
    if solid.status()!=m.Error.NoError or solid.is_empty():raise ValueError('Invalid/empty solid')
    mesh=solid.to_mesh();triangles=mesh.vert_properties[:,:3][mesh.tri_verts]
    data=bytearray(b'R19 forming tool; Manifold 3.5.4; prototype'.ljust(80,b' '))
    data+=struct.pack('<I',len(triangles))
    for tri in triangles:
        normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=np.linalg.norm(normal)
        data+=struct.pack('<12fH',*normal,*tri.ravel(),0)
    path.write_bytes(data)


def fixture(points,size,radius,label):
    cylinders=[m.Manifold.cylinder(size[2]+2-xyz[2]+radius,radius,circular_segments=24)
               .translate([xyz[0],xyz[1],xyz[2]-radius]) for xyz in points]
    segments=[m.Manifold.batch_hull([a,b]) for a,b in zip(cylinders,cylinders[1:])]
    slot=m.Manifold.batch_boolean(segments,m.OpType.Add)
    return m.Manifold.cube(size)-slot-label


def collision(a,b,name,expected_empty):
    solid=a^b
    result=dict(name=name,engine='Manifold 3.5.4',status=str(solid.status()),
                empty=solid.is_empty(),volume_mm3=solid.volume(),triangles=solid.num_tri())
    if solid.status()!=m.Error.NoError or result['empty']!=expected_empty:
        raise ValueError(str(result))
    if not expected_empty and result['volume_mm3']<=0:raise ValueError('Failed positive control')
    return result
