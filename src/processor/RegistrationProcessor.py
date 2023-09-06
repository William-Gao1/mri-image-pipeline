from .SessionProcessor import SessionProcessor, SessionInfo
from utils.registration import register_nifti_to_target, run_cmd


from typing_extensions import override
import os

class RegistrationProcessor(SessionProcessor):
    @override
    def process_session(self, session_info: SessionInfo) -> None:
        output_folder = session_info["output_folder"]
        subject_name = session_info["subject"]
        session_folder = session_info["session_folder"]

        nifti_prefix = os.path.join(output_folder, subject_name)

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
            print(f'Error for {subject_name}: Cannot find mask, stopping registration...')
            return
        
         # perform brain extraction for registration target file
        target_file = f'{nifti_prefix}_AX_{target}.nii.gz'
        target_brain = f'{nifti_prefix}_AX_{target}_brain.nii.gz'
        _, err, code = run_cmd(f'fslmaths {target_file} -mul {mask} {target_brain}')
        
        if code != 0:
            print(f'Error for subject {subject_name}: brain extraction from mask failed for {target_file}. Stopping registration: {err}')

        files_in_session_folder = os.listdir(session_folder)
        is_raw_sequence_nifti = lambda file, sequence: file.endswith('.nii.gz') and sequence.upper() in file.upper() and not '_to_' in file and '_AX_' in file and 'brain' not in file and 'resampled' not in file and 'MASK' not in file.upper() and 'OLD' not in file.upper()

        for file in files_in_session_folder:
            output_file = os.path.join(output_folder, file)
            moving_sequence = file.split('_')[-1].split('.')[0] if len(file.split('_')) >= 2 else ''
            if is_raw_sequence_nifti(file, 'T1') and not file.endswith('_T1.nii.gz') and has_t1:
                # register files like <subject>_T1b.nii.gz to t1
                register_nifti_to_target(subject_name, output_folder, target_brain, output_file, moving_sequence, 'T1')
            
            if is_raw_sequence_nifti(file, 'T2') and has_t1:
                register_nifti_to_target(subject_name, output_folder, target_brain, output_file, moving_sequence, 'T1')
            elif is_raw_sequence_nifti(file, 'T2') and not file.endswith('_T2.nii.gz') and has_t2:
                # register files like <subject>_T2b.nii.gz to t2
                register_nifti_to_target(subject_name, output_folder, target_brain, output_file, moving_sequence, 'T2')
            
            if is_raw_sequence_nifti(file, 'FL') and has_t1:
                register_nifti_to_target(subject_name, output_folder, target_brain, output_file, moving_sequence, 'T1')
            elif is_raw_sequence_nifti(file, 'FL') and has_t2:
                register_nifti_to_target(subject_name, output_folder, target_brain, output_file, moving_sequence, 'T2')
            elif is_raw_sequence_nifti(file, 'FL') and not file.endswith('_FL.nii.gz') and not file.endswith('_FLAIR.nii.gz') and has_fl:
                # register files like <subject>_FLb.nii.gz to fl
                register_nifti_to_target(subject_name, output_folder, target_brain, output_file, moving_sequence, 'FL')

        # now, register all the other sequences
        other_sequences = ['DWI', 'b0', 'b1000', 'ADC', 'eADC', 'b2600']

        if target is not None:
            for file in files_in_session_folder:
                file_name = file.split(os.sep)[-1]
                for sequence in other_sequences:
                    if is_raw_sequence_nifti(file_name, sequence):
                        output_file = os.path.join(output_folder, file)
                        moving_sequence = file.split('_')[-1].split('.')[0]
                        register_nifti_to_target(subject_name, output_folder, target_brain, output_file, moving_sequence, target)
                        break
        else:
            print(f'Warning for {subject_name}: Subject has no T1 or T2 or FL brain to register files')
