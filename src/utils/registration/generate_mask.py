import sys
sys.path.insert(0, '/hpf/projects/ndlamini/scratch/wgao/python3.8.0/')

import os
import keras
import cv2
import numpy as np
import nibabel as nib
from nibabel import processing
import scipy
from skimage import morphology
from typing_extensions import deprecated
import nilearn.image
import albumentations as A
import skimage.transform

from .command import run_cmd_async, run_cmd

TEMPLATE_DIR = '/hpf/projects/ndlamini/scratch/kwalker/templates/NKI10AndUnder'

@deprecated("Deprecated in favour of using neural networks to generate masks, use generate_brain_mask_using_model() instead")
def generate_brain_mask(subject_name: str, sequence: str, target_file: str, output_dir: str) -> int:
    """Generates a concensus brain mask using `3dSkullStrip`, `bet`, and `antsBrainExtraction`

    Args:
        subject_name (str): Name of subject
        sequence (str): Name of sequence (e.g. 'T1', 'T2', 'FL')
        target_file (str): Path to file to extract brain for
        output_dir (str): Path to output folder

    Returns:
        int: Return code of concensus mask creation (0 for success, non-zero for fail)
    """
    output_file_prefix = os.path.join(output_dir, f'{subject_name}_{sequence}')

    # AFNI skull strip
    afni_skullstrip_cmd = f'3dSkullStrip -input {target_file} -prefix {output_file_prefix}_mask_3dss.nii.gz -mask_vol'
    afni_fsl_cmd = f'fslmaths {output_file_prefix}_mask_3dss.nii.gz -thr 2 -bin {output_file_prefix}_mask_3dss_thresh.nii.gz -odt char'

    afni_process = run_cmd_async(f"{afni_skullstrip_cmd} && {afni_fsl_cmd}")

    # FSL bet
    bet_cmd = f'bet {target_file} {output_file_prefix}_bet -m -n -R -S -B'
    bet_fsl_cmd = f'fslmaths {output_file_prefix}_bet_mask.nii.gz -bin {output_file_prefix}_bet_mask.nii.gz -odt char'

    bet_process = run_cmd_async(f'{bet_cmd} && {bet_fsl_cmd}')

    # ANTs brain extraction
    ants_cmd = f'antsBrainExtraction.sh -d 3 -a {target_file} -e {TEMPLATE_DIR}/T_template0.nii.gz -m {TEMPLATE_DIR}/T_template0_BrainCerebellumProbabilityMask.nii.gz -o {output_file_prefix}_mask_abe -s nii.gz -q 1'
    ants_fsl_cmd = f'fslmaths {output_file_prefix}_mask_abeBrainExtractionMask.nii.gz -bin {output_file_prefix}_mask_abeMask.nii.gz -odt char'

    ants_process = run_cmd_async(f'{ants_cmd} && {ants_fsl_cmd}')

    for process in [afni_process, bet_process, ants_process]:
        _, err = process.communicate()

        if process.returncode != 0:
            print(f'Error for {subject_name}: Creation of mask failed, concensus creation will be skipped. \n\tCommand {process.args} failed: \n\t{err}')
            return process.returncode
        
    # generate concensus mask
    concensus_cmd = f'fslmaths {output_file_prefix}_mask_3dss_thresh.nii.gz -add {output_file_prefix}_bet_mask.nii.gz -add {output_file_prefix}_mask_abeMask.nii.gz {output_file_prefix}_concensusMask.nii.gz -odt float'
    concensus_fsl_cmd = f'fslmaths {output_file_prefix}_concensusMask.nii.gz -thr 2 -bin {output_file_prefix}_mask.nii.gz -odt char'
    _, err, code = run_cmd(f'{concensus_cmd} && {concensus_fsl_cmd}')

    if code != 0:
        print(f'Error for {subject_name}: All masks created but concensus mask creation failed: {err}')
    return code

IMG_SIZE = 128
def generate_brain_mask_using_model(subject_name: str, sequence: str, target_file: str, output_dir: str) -> int:
    """Generates a brain mask using a trained CNN for T1s

    Args:
        subject_name (str): Name of subject
        sequence (str): Sequence of file to generate mask for (Currently has to be 'T1')
        target_file (str): Path to file to generate mask for
        output_dir (str): Directory to output mask

    Returns:
        int: Success code (0 for success, non-zero for fail)
    """
    
    # load the model
    path_to_model = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', 'models', '2d', f'{sequence.lower()}_brain_extraction.keras'))
    model = keras.models.load_model(path_to_model, compile=False)
    
    # read the nifti and prep input to model
    nifti = nib.load(target_file)
    nifti_resampled = processing.conform(nifti)

    num_slices = nifti_resampled.shape[2]
    X = np.empty((num_slices, IMG_SIZE, IMG_SIZE, 1))
    nifti_voxels = nifti_resampled.get_fdata()
    
    # resize input data to conform to model expectations
    for i in range(num_slices):
        X[i,:,:,0] = cv2.resize(nifti_voxels[:,:,i], (IMG_SIZE,IMG_SIZE))

    # normalize
    max_voxel = np.max(X)
    
    if max_voxel == 0:
        print(f"Error for subject {subject_name}: {target_file} is an empty image. Skipping mask generation...")
        return 1
    
    print(f"Generating mask for {subject_name}, {target_file}...")

    # predict
    prediction = model.predict(X/max_voxel, verbose=0)
    
    # convert to axial
    prediction = np.moveaxis(prediction[:, :, :, 1], 0, 2)
    
    # apply a gaussian blur
    prediction = scipy.ndimage.gaussian_filter(prediction, sigma=(1, 3, 3), order=0)

    # resize predictions back to the size of resampled input nifti
    resized_prediction = np.zeros(nifti_resampled.shape)
    
    for slice in range(prediction.shape[2]):
        # round the predictions to get a binary mask
        resized_prediction[:, :, slice] = np.round(cv2.resize(prediction[:, :, slice], (nifti_resampled.shape[0], nifti_resampled.shape[1]))).astype(int)

        # post processing, fill in any holes in mask
        resized_prediction[:, :, slice] = scipy.ndimage.binary_fill_holes(resized_prediction[:, :, slice])
        
        # post processing, remove any stray artifacts
        resized_prediction[:,:, slice] = morphology.remove_small_objects(resized_prediction[:,:, slice].astype(bool), IMG_SIZE*IMG_SIZE*0.01).astype(int)

    for slice in range(resized_prediction.shape[0]):
        # post processing, fill in any holes in mask
        resized_prediction[slice, :, :] = scipy.ndimage.binary_fill_holes(resized_prediction[slice, :, :])
        
        # post processing, remove any stray artifacts
        resized_prediction[slice, :, :] = morphology.remove_small_objects(resized_prediction[slice, :, :].astype(bool), IMG_SIZE*IMG_SIZE*0.01).astype(int)
    
    for slice in range(resized_prediction.shape[1]):
        # post processing, fill in any holes in mask
        resized_prediction[:, slice, :] = scipy.ndimage.binary_fill_holes(resized_prediction[:, slice, :])
        
        # post processing, remove any stray artifacts
        resized_prediction[:, slice, :] = morphology.remove_small_objects(resized_prediction[:, slice, :].astype(bool), IMG_SIZE*IMG_SIZE*0.01).astype(int)

    # save predictions
    prediction_nifti = nib.Nifti1Image(resized_prediction, nifti_resampled.affine, dtype=np.uint16)
    prediction_nifti = nilearn.image.resample_img(prediction_nifti, nifti.affine, nifti.shape, "nearest")
    nib.save(prediction_nifti, os.path.join(output_dir, f'{subject_name}_AX_{sequence}_mask.nii.gz'))
    
    return 0

IMG_SIZE = 128
def generate_brain_mask_using_3d_model(subject_name: str, sequence: str, target_file: str, output_dir: str) -> int:
    """Generates a brain mask using a trained 3D CNN for T1s

    Args:
        subject_name (str): Name of subject
        sequence (str): Sequence of file to generate mask for (Currently has to be 'T1')
        target_file (str): Path to file to generate mask for
        output_dir (str): Directory to output mask

    Returns:
        int: Success code (0 for success, non-zero for fail)
    """
    
    # load the model
    path_to_model = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', 'models', '3d', f'{sequence.lower()}_brain_extraction.keras'))
    model = keras.models.load_model(path_to_model, compile=False)
    
    # read the nifti and prep input to model
    nifti = nib.load(target_file)
    nifti_resampled = processing.conform(nifti)

    X = np.empty((1, IMG_SIZE, IMG_SIZE, IMG_SIZE, 1))
    nifti_voxels = nifti_resampled.get_fdata()
    
    # resize input data to conform to model expectations
    X[0, :, :, :, 0] = A.resize(nifti_voxels, 128, 128)[:, :, ::2]
    
    # normalize
    max_voxel = np.max(X)
    
    if max_voxel == 0:
        print(f"Error for subject {subject_name}: {target_file} is an empty image. Skipping mask generation...")
        return 1
    
    print(f"Generating mask for {subject_name}, {target_file}...")

    # predict
    prediction = model.predict(X/max_voxel, verbose=0)[0, :, :, :, 1]
    
    # apply a gaussian blur
    prediction = scipy.ndimage.gaussian_filter(prediction, sigma=(3, 3, 3), order=0)

    # resize predictions back to the size of resampled input nifti
    resized_prediction = skimage.transform.resize(np.where(prediction > 0.6, 1.0, 0.0), nifti_resampled.shape, order=0)
    
    for slice in range(resized_prediction.shape[2]):
        # post processing, fill in any holes in mask
        resized_prediction[:, :, slice] = scipy.ndimage.binary_fill_holes(resized_prediction[:, :, slice])
        
        # post processing, remove any stray artifacts
        resized_prediction[:,:, slice] = morphology.remove_small_objects(resized_prediction[:,:, slice].astype(bool), IMG_SIZE*IMG_SIZE*0.01).astype(int)

    for slice in range(resized_prediction.shape[0]):
        # post processing, fill in any holes in mask
        resized_prediction[slice, :, :] = scipy.ndimage.binary_fill_holes(resized_prediction[slice, :, :])
        
        # post processing, remove any stray artifacts
        resized_prediction[slice, :, :] = morphology.remove_small_objects(resized_prediction[slice, :, :].astype(bool), IMG_SIZE*IMG_SIZE*0.01).astype(int)
    
    for slice in range(resized_prediction.shape[1]):
        # post processing, fill in any holes in mask
        resized_prediction[:, slice, :] = scipy.ndimage.binary_fill_holes(resized_prediction[:, slice, :])
        
        # post processing, remove any stray artifacts
        resized_prediction[:, slice, :] = morphology.remove_small_objects(resized_prediction[:, slice, :].astype(bool), IMG_SIZE*IMG_SIZE*0.01).astype(int)

    # save predictions
    prediction_nifti = nib.Nifti1Image(resized_prediction, nifti_resampled.affine, dtype=np.uint16)
    prediction_nifti = processing.conform(prediction_nifti, nifti.shape, nifti.header.get_zooms(), order=0)
    nib.save(prediction_nifti, os.path.join(output_dir, f'{subject_name}_AX_{sequence}_mask.nii.gz'))
    
    return 0