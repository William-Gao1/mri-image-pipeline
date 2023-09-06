from .SessionProcessor import SessionProcessor, SessionInfo
from utils.registration import run_cmd

from typing_extensions import override
import os

# Remember to add this processor to src/processor/__init__.py when you're done
class BrainExtractionProcessor(SessionProcessor):
    @override
    def process_session(self, session_info: SessionInfo) -> None:
        output_folder = session_info["output_folder"]
        subject_name = session_info["subject"]
        session_folder = session_info["session_folder"]
        
        # find registered files:
        registered_files = list(filter(lambda s: s.endswith('.nii.gz') and '_to_' in s and 'brain' not in s and 'template' not in s and 'SEG' not in s.upper() and 'STROKE' not in s.upper() and 'LESION' not in s.upper(), os.listdir(output_folder)))
        
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
            print(f'Error for {subject_name}: Cannot find target registration sequence. Subject has no T1, T2, FL')
            return
        
        # first, find the mask
        possible_masks = list(filter(lambda s: 'mask' in s and target in s, os.listdir(output_folder)))
        
        # see if there is edit mask:
        edit_masks = list(filter(lambda s: 'mask_edit' in s, possible_masks))
        concensus_masks = list(filter(lambda s: s.endswith('_mask.nii.gz'), possible_masks))
        
        mask = None
        
        if len(edit_masks) > 0:
            mask = edit_masks[0]
        elif len(concensus_masks) > 0:
            mask = concensus_masks[0]
            
        if mask is None:
            print(f'Error for {subject_name}: Cannot find mask, skipping brain extraction')
            return
        
        # perform brain extraction for all registered files
        mask = os.path.join(session_folder, mask)
        for registered_file in registered_files:
            registered_file = os.path.join(session_folder, registered_file)
            registered_brain = registered_file.split('.')[0] + '_brain.nii.gz'
            _, err, code = run_cmd(f'fslmaths {registered_file} -mul {mask} {registered_brain}')
            
            if code != 0:
                print(f'Warning for subject {subject_name}: brain extraction from mask failed for {registered_file}: {err}')

        # perform brain extraction for registration target file
        target_file = f'{nifti_prefix}_AX_{target}.nii.gz'
        target_brain = f'{nifti_prefix}_AX_{target}_brain.nii.gz'
        _, err, code = run_cmd(f'fslmaths {target_file} -mul {mask} {target_brain}')
        
        if code != 0:
            print(f'Warning for subject {subject_name}: brain extraction from mask failed for {target_file}: {err}')