from .SessionProcessor import SessionProcessor, SessionInfo
from utils.registration import segment_stroke, apply_linear_transform

from typing_extensions import override
import os
import nilearn.image
import nibabel as nib
import numpy as np

class StrokeSegmentationProcessor(SessionProcessor):
    @override
    def process_session(self, session_info: SessionInfo) -> None:
        output_folder = session_info["output_folder"]
        subject_name = session_info["subject"]
        session_folder = session_info["session_folder"]
        
        nifti_prefix = os.path.join(session_folder, subject_name)

        # segment on non-registered adc and dwi
        adc = f'{nifti_prefix}_AX_ADC.nii.gz'
        b1000 = f'{nifti_prefix}_AX_b1000.nii.gz'
        dwi = f'{nifti_prefix}_AX_DWI.nii.gz'

        has_adc = os.path.isfile(adc)
        has_b1000 = os.path.isfile(b1000)
        has_dwi = os.path.isfile(dwi)

        # if we dont have adc or if we dont have either the dwi or b1000, then cannot segment
        if not has_adc or not (has_b1000 or has_dwi):
            print(f'Warning for {subject_name}: subject does not have the required files to perform automatic stroke segmentation')
            return

        # use b1000 if we have that, otherwise use dwi
        if has_b1000:
            code = segment_stroke(subject_name, b1000, adc, output_folder)
        elif has_dwi:
            code = segment_stroke(subject_name, dwi, adc, output_folder, True)
        
        if code == 0:
            t1 = f'{nifti_prefix}_AX_T1.nii.gz'
            t2 = f'{nifti_prefix}_AX_T2.nii.gz'
            fl = f'{nifti_prefix}_AX_FL.nii.gz'
            
            has_t1 = os.path.isfile(t1)
            has_t2 = os.path.isfile(t2)
            has_fl = os.path.isfile(fl)

            target = None
            if has_t1:
                target = 'T1'
            elif has_t2:
                target = 'T2'
            elif has_fl:
                target = 'FL'

            if target is None:
                print(f'Warning for {subject_name}: no target to register stroke segmentation to')

            stroke_segmentation_path = os.path.join(output_folder, f'{subject_name}_stroke_segmentation.nii.gz')
            registered_segmentation_output_path = os.path.join(output_folder, f'{subject_name}_stroke_segmentation_to_{target}_Warped.nii.gz')
            
            dwi_b1000_str = 'b1000' if has_b1000 else 'DWI'
            
            transform_path = os.path.join(output_folder, f'{subject_name}_{dwi_b1000_str}_to_{target}_0GenericAffine.mat')
            registered_dwi_path = os.path.join(output_folder, f'{subject_name}_{dwi_b1000_str}_to_{target}_Warped.nii.gz')
            if not os.path.exists(stroke_segmentation_path) or not os.path.exists(transform_path) or not os.path.exists(registered_dwi_path):
                print(f'Error for {subject_name}: Tried to register {stroke_segmentation_path} using {transform_path} and {registered_dwi_path} butat least one of these files do not exist')
                return
            
            apply_linear_transform(subject_name, stroke_segmentation_path, transform_path, b1000 if has_b1000 else dwi, registered_segmentation_output_path)
            
            # resize registered segmentation file to dwi
            seg = nib.load(registered_segmentation_output_path)
            dwi_or_b1000 = nib.load(registered_dwi_path)
            
            seg_resampled = nilearn.image.resample_img(seg, dwi_or_b1000.affine, dwi_or_b1000.shape, interpolation='nearest')
            seg_resampled = nib.Nifti1Image(np.round(seg_resampled.get_fdata()), seg_resampled.affine)
            nib.save(seg_resampled, registered_segmentation_output_path)