from .SessionProcessor import SessionProcessor, SessionInfo
from utils.registration import generate_brain_mask_using_3d_model, run_cmd

from typing_extensions import override
import os

class BrainMaskProcessor(SessionProcessor):

    @override 
    def process_session(self, session_info: SessionInfo) -> None:
        output_folder = session_info["output_folder"]
        subject_name = session_info["subject"]
        session_folder = session_info["session_folder"]

        nifti_prefix = os.path.join(session_folder, subject_name)

        t1 = f'{nifti_prefix}_AX_T1.nii.gz'
        t2 = f'{nifti_prefix}_AX_T2.nii.gz'
        fl = f'{nifti_prefix}_AX_FL.nii.gz'

        has_t1 = os.path.isfile(t1)
        has_t2 = os.path.isfile(t2)
        has_fl = os.path.isfile(fl)

        # figure out which file and sequence to create brain mask for
        register_to_seq = None
        register_to_file = None
        if has_t1:
            register_to_seq = 'T1'
            register_to_file = t1
        elif has_t2:
            register_to_seq = 'T2'
            register_to_file = t2
        elif has_fl:
            register_to_seq = 'FL'
            register_to_file = fl
        
        if register_to_seq is not None:
            code = generate_brain_mask_using_3d_model(subject_name, register_to_seq, register_to_file, output_folder)
            
            if code != 0:
                return
    
            # extract brain
            # first, find mask
            
            masks = [os.path.join(output_folder, x) for x in os.listdir(output_folder) if 'mask' in x.lower() and register_to_seq in x.upper()]
            if len(masks) > 1:
                print(f'Warning for {subject_name} found multiple brain masks: {masks}\n\tusing {masks[0]}')

            _, err, code = run_cmd(f'fslmaths {register_to_file} -mul {masks[0]} {f"{nifti_prefix}_AX_{register_to_seq}_brain.nii.gz"}')
            
            if code != 0:
                print(f'Error for {subject_name}: could not extract brain using mask for {register_to_file}:\n{err}')

        else:
            print(f'Warning for {subject_name}: Subject has no T1 or T2 or FL to create brain mask for')

        
        