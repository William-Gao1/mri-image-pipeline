import os
import keras
import cv2
import numpy as np
import nibabel as nib
from nibabel import processing

IMG_SIZE = 128
def segment_stroke(subject_name: str, dwi_or_b1000: str, adc: str, output_dir: str, segment_on_dwi = False) -> int:
    """Generates a stroke segmentation from the dwi and adc using a trained CNN

    Args:
        subject_name (str): Name of subject
        dwi_or_b1000 (str): Path to b1000 or dwi
        adc (str): Path to adc
        output_dir (str): Directory to output segmentation
        registered_to (str): Name of sequence that dwi and adc are registered to
        segment_on_dwi(bool): True if we are segmenting on dwi false if segmenting on b1000. Default false
        
    Returns:
        int: Success code (0 for success, non-zero for fail)
    """
    # load the model
    path_to_model = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', 'models', '2d', f'stroke_segmentation_{"dwi" if segment_on_dwi else "b1000"}.keras'))
    model = keras.models.load_model(path_to_model, compile=False)
    
    # read the dwi and adc and prep input to model
    adc_img = nib.load(adc)
    dwi_or_b1000_img = nib.load(dwi_or_b1000)

    # if dwi is 3d, take first volume
    if dwi_or_b1000_img.ndim == 4:
        dwi_or_b1000_img = nib.funcs.four_to_three(dwi_or_b1000_img)[0]

    # make sure adc is the same dimensions as dwi
    adc_img = processing.conform(adc_img, dwi_or_b1000_img.shape, dwi_or_b1000_img.header.get_zooms())
    
    num_slices = dwi_or_b1000_img.shape[2]
    X = np.empty((num_slices, IMG_SIZE, IMG_SIZE, 2))
    
    adc_voxels = adc_img.get_fdata()
    dwi_voxels = dwi_or_b1000_img.get_fdata()

    assert adc_voxels.shape[2] == dwi_voxels.shape[2], (adc, adc_voxels.shape, dwi_voxels.shape)
    
    # resize input data to conform to model expectations
    for i in range(num_slices):
        X[i,:,:,0] = cv2.resize(dwi_voxels[:,:,i], (IMG_SIZE,IMG_SIZE))
        X[i,:,:,1] = cv2.resize(adc_voxels[:,:,i], (IMG_SIZE,IMG_SIZE))

    # normalize
    max_voxel = np.max(X)
    
    if max_voxel == 0:
        print(f"Error for subject {subject_name}: both {dwi_or_b1000_img} and {adc} are empty images. Skipping stroke segmentation...")
        return 1
    
    print(f"Generating stroke segmentation for {subject_name} using {dwi_or_b1000_img}, {adc}...")

    # predict
    prediction = model.predict(X/max_voxel, verbose=0)
    
    # convert to axial
    prediction = np.moveaxis(prediction[:, :, :, 1], 0, 2)
    
    # resize predictions back to the size of input nifti
    resized_prediction = np.zeros(dwi_or_b1000_img.shape)
    
    for slice in range(prediction.shape[2]):
        # round the predictions to get a binary mask
        resized_prediction[:, :, slice] = cv2.resize(prediction[:, :, slice], (dwi_or_b1000_img.shape[0], dwi_or_b1000_img.shape[1]))

    # only take high probability predictions
    resized_prediction = np.where(resized_prediction > 0.7, 1.0, 0.0).astype(int)

    # save predictions
    prediction_nifti = nib.Nifti1Image(resized_prediction.astype(float), dwi_or_b1000_img.affine)
    
    nib.save(prediction_nifti, os.path.join(output_dir, f'{subject_name}_stroke_segmentation.nii.gz'))
    
    return 0