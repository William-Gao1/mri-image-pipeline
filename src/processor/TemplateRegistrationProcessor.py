from .SessionProcessor import SessionProcessor, SessionInfo
from utils.registration import register_nifti_to_target, apply_linear_transform

from typing_extensions import override
import os
import nibabel as nib
from nibabel import processing
import numpy as np

template_t1_file = '/hpf/projects/ndlamini/scratch/kwalker/templates/dHCP_40weeks/template_t1.nii.gz'
template_t2_file = '/hpf/projects/ndlamini/scratch/kwalker/templates/dHCP_40weeks/template_t2.nii.gz'

class TemplateRegistrationProcessor(SessionProcessor):
    @override
    def process_session(self, session_info: SessionInfo) -> None:
        output_folder = session_info["output_folder"]
        subject_name = session_info["subject"]
        session_folder = session_info["session_folder"]
        
        files = sorted(os.listdir(session_folder), key=lambda s: -os.path.getmtime(os.path.join(session_folder, s)))
        
        nifti_files = list(filter(lambda s: s.endswith('.nii.gz'), files))
        
        brain_files = list(filter(lambda s: 'BRAIN' in s.upper() and not 'RESAMPLED' in s.upper(), nifti_files))
        
        registered_files = list(filter(lambda s: '_TO_' in s.upper() and not 'TEMPLATE' in s.upper(), nifti_files))

        registered_brain_files = list(filter(lambda s: 'BRAIN' in s.upper(), registered_files))
        
        # figure out the target sequence of the registered files
        nifti_prefix = os.path.join(output_folder, subject_name)
        target = None
        if len(registered_files) > 0:
            target = registered_files[0].split('_to_')[1].split('_')[0]
        else:
            t1 = f'{nifti_prefix}_AX_T1.nii.gz'
            t2 = f'{nifti_prefix}_AX_T2.nii.gz'
            fl = f'{nifti_prefix}_AX_FL.nii.gz'
            
            has_t1 = os.path.isfile(t1)
            has_t2 = os.path.isfile(t2)
            has_fl = os.path.isfile(fl)

            if has_t1:
                target = 'T1'
            elif has_t2:
                target = 'T2'
            elif has_fl:
                target = 'FL'
        
        if target is None:
            print(f'Error for subject {subject_name}: Could not find file to register to template. Stopping...')
            return
        
        # find the corresponding target brain
        target_brain_files = list(filter(lambda s: target in s.upper() and not '_TO_' in s.upper(), brain_files))
        
        if len(target_brain_files) > 1:
            print(f'Warning for subject {subject_name}: more than one brain file for target {target}, picking {target_brain_files[0]}')
        if len(target_brain_files) == 0:
            print(f'Error for subject {subject_name}: No brain file found for target {target}, did you run the brain extraction step? Stopping...')
            return
        
        moving_brain = os.path.join(session_folder, target_brain_files[0])
        
        # figure out which template brain to register to
        template_brain = template_t2_file
        if target == 'T1':
            template_brain = template_t1_file
            
        img = nib.load(moving_brain)
        template = nib.load(template_brain)
        
        # resize image to dimensions of template file
        img = processing.conform(img, template.shape)
        
        # save this image with the affine transform of template file (hopefully the two files should be almost in same space now)
        resampled_img = nib.Nifti1Image(img.get_fdata(), template.affine)
        
        # save the resized and transformed file
        moving_brain_file_resampled_name = moving_brain.split('.nii.gz')[0] + '_resampled.nii.gz'
        nib.save(resampled_img, moving_brain_file_resampled_name)
        
        # do the registration of resized and transformed file to target file
        code = register_nifti_to_target(subject_name, output_folder, template_brain, moving_brain_file_resampled_name, target, 'template')
        if code != 0:
            # registration failed
            return

        # use the registered file to register all other files
        segmentation_files = list(filter(lambda s: ("STROKE" in s.upper() or "SEG" in s.upper() or "LESION" in s.upper()) and '_TO_' in s.upper(), nifti_files))
        all_files_to_register_to_template = registered_brain_files + segmentation_files

        # get the affine transform matrix from registered to template file
        files = sorted(os.listdir(session_folder), key=lambda s: -os.path.getmtime(os.path.join(session_folder, s)))
        registered_to_template_transform_files = list(filter(lambda s: s.endswith('.mat') and '_TO_TEMPLATE' in s.upper() and target in s.upper() and 'GenericAffine' in s, files))

        if len(registered_to_template_transform_files) > 1:
            print(f'Warning for {subject_name}: Multiple affine transform files for {target} to template. Using {registered_to_template_transform_files[0]}...')
        elif len(registered_to_template_transform_files) == 0:
            print(f'Error for {subject_name}: Could not find affine transform file for {target} to template. Stopping...')
            return
        
        register_to_template_transform = registered_to_template_transform_files[0]

        for file in all_files_to_register_to_template:
            print(f'Registering {file} to template')
            full_path = os.path.join(session_folder, file)
            img = nib.load(full_path)

            if file in segmentation_files:
                img = processing.conform(img, template.shape, order=1)
                registered_img = nib.Nifti1Image(np.round(img.get_fdata()), template.affine)
            else:
                img = processing.conform(img, template.shape)
                registered_img = nib.Nifti1Image(img.get_fdata(), template.affine)
            registered_file_name = file.split('.nii.gz')[0].split('_to_')[0]
            registered_file_path = os.path.join(output_folder, f'{registered_file_name}_to_template_Warped.nii.gz')
            nib.save(registered_img, registered_file_path)
            
            apply_linear_transform(subject_name, registered_file_path, os.path.join(output_folder, register_to_template_transform), template_brain, registered_file_path)

            