from .command import run_cmd_async
from .check_4d import check_4d
from .register_nifti import get_registration_command

import os

from typing import List

def extract_brain_for_files_and_register_to_target(subject_name: str, file_paths: List[str], output_folder: str, target_file: str, target_sequence: str) -> None:
    """Extracts brain using `bet` then registers file to target

    Args:
        subject_name (str): Name of subject
        file_paths (list[str]): Files to extract brain for
        output_folder (str): Path to output folder
        target_file (str): Path to registration target nifti
        target_sequence (str): Target sequence name (e.g. 'T1', 'T2', 'FL')
    """
    
    processes = []
    
    for file_path in file_paths:
        is_4d = check_4d(file_path, output_folder)
        
        if is_4d is None:
            continue
        
        file_name = file_path.split(os.sep)[-1]
        file_prefix = file_name.split('.')[0]
        
        output_brain_file_path = os.path.join(output_folder, f'{file_prefix}_brain.nii.gz')
        input_brain_file_path = file_prefix + '_first_vol.nii.gz' if is_4d else file_path
        
        sys_cmd = f'bet {input_brain_file_path} {output_brain_file_path} -m -f 0.3'
        
        if target_file is not None:
            moving_sequence = os.path.split(input_brain_file_path)[1].split('_')[-1].split('.')[0]
            
            reg_cmd = get_registration_command(subject_name, output_folder, target_file, output_brain_file_path, moving_sequence, target_sequence)
            sys_cmd += f' && {reg_cmd}'
        
        processes.append(run_cmd_async(sys_cmd))
    
    for process in processes:
        _, err = process.communicate()
        code = process.returncode
        
        if code != 0:
            print(f'Error for {subject_name}: Could not extract and register dwi: {err}')
        
        