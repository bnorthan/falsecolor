"""
DataObject for H&E False coloring

Robert Serafin
9/11/2019

"""

import os
import tifffile as tf
import skimage.morphology as morph
import skimage.filters as filt
import numpy
import scipy.ndimage as nd
import skimage.feature as feat
from pathos.multiprocessing import ProcessingPool
from functools import partial
import glob
import time
import h5py as hp
import FalseColor.Color as fc

class DataObject(object):
    def __init__(self, directory, imageSet = None,
                 setupPool = False, ncpus = 2):
        """
        Object to store image data in a convienient way for batch processing
        
        Attributes
        ----------
        
        directory : string or pathlike
            Base directory where image data is stored
            
        imageSet : 3d numpy array
            images for processing
        
        setupPool : bool
            setup processing pool
        
        """
        
        # object base directory
        self.directory = directory
        
        self.imageSet = imageSet
        
        if setupPool:
            self.setupProcessing(ncpus = ncpus)
        else:
            self.unloadPool()
                
    
    def loadTifImages(self,file_list):            
        try:
            file_list = sorted(file_list)
            file_names = []
            images = []

            for i in range(len(file_list)):
                images.append(tf.imread(file_list[i]))
                file_names.append(z.split(os.sep)[-1])

            return np.asarray(images)
        
        except AssertionError:
            print('Image_size must be tuple of form (m,n) where m and n are integers')
            
    def loadH5(self,folder,image_size = None,return_as_property=False):
        
        data_name = [os.path.join(folder,f) for f in os.listdir(folder) if f.endswith('h5')]
        
        H5_dataset = hp.File(data_name[0],'r')

        print(list(H5_dataset.keys()))

        if return_as_property:
            self.H5_dataset = H5_dataset

        else:
            return H5_dataset
        
    def setupH5data(self,folder=None,dataID = 0,channelIDs = None):

        if channelIDs is None:
            channelIDs = ['s00','s01']

        if folder:
            dataset = self.loadH5(folder)

        else:
            dataset = self.loadH5(self.directory)

        #Create imageSet as a 4D array, from the loaded dataset
        imageData = numpy.stack((dataset['t00000'][channelIDs[0]][str(dataID)]['cells'],
            dataset['t00000'][channelIDs[1]][str(dataID)]['cells']),axis=-1)
        
        print(self.imageSet.shape)
        imageData = None
    
    def setupProcessing(self,ncpus):
        self.pool = ProcessingPool(ncpus=ncpus)
        
    def unloadPool(self):
        self.pool = None
    
    def processImages(self,runnable_dict, imageSet, dtype = None):
            """
            Purpose
            -------
            Method to batch process multiple images simultaneously. Can process multiple 
            channels or one at a time. Method acts on Image data within data object. 
            
            Attributes
            ----------
            
            runnable_dict : dict
                Currently should have one key 'runnable' which is mapped to a method to be run
                the other key 'kwargs' are the inputs to the method which are different than
                the method's default parameters
            
            """
            if self.pool is None:
                self.setupProcessing(ncpus=4)
            
            func,kwargs = runnable_dict['runnable'],runnable_dict['kwargs']
            print(func,kwargs,imageSet.shape)
 
            processed_images = []
            # method = partial(runnable,**kwargs)

            if type(kwargs) == dict:
                processed_images.append(self.pool.map(func,imageSet,**kwargs))
            
            else:
                processed_images.append(self.pool.map(func,imageSet))

            if dtype is None:
                return numpy.asarray(processed_images)
            
            else:
                return numpy.asarray(processed_images,dtype = dtype)