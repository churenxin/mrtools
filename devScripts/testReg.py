#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  1 18:37:59 2020

@author: cjm
"""

import os
import dicom2nifti
import ants
import scipy

dataFolder="/home/cjm/Projects/mrtools/sampleData/images/ACR_Phantom_3D/"

#%% Convert Reference 3D Datset to nifti

dicom2nifti.convert_directory(os.path.join(dataFolder,"dicom"), os.path.join(dataFolder,"nifti") , compression=True, reorient="RAI")

#%% Read Reference Series
# Read reference dataset in as an ants image
refSeries=ants.image_read(os.path.join(dataFolder,"nifti","19_t1_space_sag_p2_iso.nii.gz"), dimension=3, pixeltype='float', reorient="RAI")


#%% Create reference cylinder
import numpy as np
# Matrix Parameters
nn=256
fov=256 # mm

ll=np.linspace(-fov/2,fov/2,nn)

xx,yy,zz=np.meshgrid(ll,ll,ll,sparse=False)

# Cylinder Parameters
diameter=190
length=148

refCylinderMatrix=(np.sqrt(np.power(xx,2)+np.power(yy,2))<(diameter/2))*((np.abs(zz)<(length/2)))

#%% Slice 5 grid
gridOffsetZ=-5 #Offset in the z direction; (origin is at the superior edge of the grid insert)
gridLengthZ=10 #Size of insert in the z direction

gridSpacing=15 # Approximate distance between grid elements in the xy plane
gridLengthXY=10 # max Number of grid elments in x/y direction
gridDiameter=gridLengthXY*gridSpacing
gridWidth=5 # approx width of the grid lines in the insert

gridMask=None
grid=None
gridZ=None

# Create the mask for the grid and dilate it to catch the outside edges
gridMask=(np.sqrt(np.power(np.floor_divide(np.abs(xx),gridSpacing)+1,2)+
                  np.power(np.floor_divide(np.abs(yy),gridSpacing)+1,2))
                  <=np.sqrt(34))

dilationStructure=scipy.ndimage.generate_binary_structure(3, 3)
gridMask=scipy.ndimage.binary_dilation(gridMask,
                                        structure=dilationStructure,
                                        iterations=int(np.floor_divide(gridWidth/2,fov/nn))
                                       )

# Create the actual Grid
grid=np.logical_and(np.remainder(np.abs(xx),gridSpacing)>gridWidth/2,np.remainder(np.abs(yy),gridSpacing)>gridWidth/2)

# Create a mask for the insert in the z direction
gridZ=((np.abs(zz-gridOffsetZ)>=(gridLengthZ/2)))

# Combine everything
slice5=((grid*gridMask)+(~gridMask)+gridZ)

refCylinderMatrix=refCylinderMatrix*slice5

#%%
refCylinder=ants.from_numpy(refCylinderMatrix.astype(float),
                        spacing=(fov/nn,fov/nn,fov/nn),
                        #direction=[-1,  0,  0,  0,  1,  0, 0, 0, -1],
                        #origin=(1.0,1.0,2.0),#(-fov/2,-fov/2,-fov/2)
                        #direction=[-1,  0,  0,  0,  1,  0, 0, 0, -1]
                       )

#refCylinder.set_origin((-fov/2,-fov/2,-fov/2))
refCylinder.set_origin((-fov/2,-fov/2,-fov/2))
#refCylinder.set_direction([-1,  0,  0,  0,  1,  0, 0, 0, -1])

print(refCylinder)

refCylinder.to_file(os.path.join(dataFolder,"nifti","Ref_Phantom.nii.gz"))

#%%

refSeriesToCylinder = ants.registration(fixed=refCylinder , moving=refSeries, type_of_transform='Translation' )

ants.plot(refCylinder,axis=2,nslices=11,ncol=5,overlay=refSeries,overlay_alpha=0.5,slice_buffer=10)

ants.plot(refCylinder,axis=2,nslices=11,ncol=5,overlay=refSeriesToCylinder['warpedmovout'],overlay_alpha=0.5,slice_buffer=10)

refSeriesToCylinder['warpedmovout'].to_file(os.path.join(dataFolder,"nifti","ACR_3D_Registered.nii.gz"))

#%%

testPath="/home/cjm/Projects/slicer/storage/dicom/1.3.12.2.1107.5.2.18.41980.30000020042614071007500000001/1.3.12.2.1107.5.2.18.41980.202004261015023630201081.0.0.0/"

dicom2nifti.convert_directory(testPath, os.path.join(dataFolder,"nifti") , compression=True, reorient="RAI")

testIm=ants.image_read(os.path.join(dataFolder,"nifti","3_acr_ax_t1.nii.gz"), dimension=3, pixeltype='float', reorient="RAI")

bb=ants.resample_image_to_target(refSeriesToCylinder['warpedmovout'], testIm, interp_type='linear', imagetype=0, verbose=False)




