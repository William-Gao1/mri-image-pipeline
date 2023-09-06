from .SessionProcessor import SessionProcessor, SessionInfo
from utils.registration import extract_brain_for_files_and_register_to_target

from typing_extensions import override
import os

class DwiCoregProcessor(SessionProcessor):
    DWI_STRINGS = ['DWI', 'ADC', 'eADC', 'b1000', 'b0', 'b2600']
    
    @override
    def process_session(self, session_info: SessionInfo) -> None:
        output_folder = session_info["output_folder"]
        subject_name = session_info["subject"]
        session_folder = session_info["session_folder"]
        
        files_in_session_folder = os.listdir(session_folder)
        
        target_sequence = None
        
        registered_files = list(filter(lambda s: '_to_' in s, files_in_session_folder))
        file_prefix = os.path.join(session_folder, subject_name)
        
        if len(registered_files) > 1:
            target_sequence = registered_files[0].split('_')[3]
        else:
            # search for T1, or T2, or Fl
            if os.path.isfile(f'{file_prefix}_T1.nii.gz'):
                target_sequence = 'T1'
            elif os.path.isfile(f'{file_prefix}_T2.nii.gz'):
                target_sequence = 'T2'
            elif os.path.isfile(f'{file_prefix}_FL.nii.gz'):
                target_sequence = 'FL'
        
        target_file = file_prefix + '_' + target_sequence + '.nii.gz' if target_sequence is not None else None
        
        # if no target, print error and exit
        
        if target_sequence is None:
            print(f'Error for {subject_name}: No T1 or T2 or FL to register to for dwi coreg')
            return
        
        # create dwi folder
        dwi_coreg_folder = os.path.join(output_folder, 'dwiCoreg')
        os.makedirs(dwi_coreg_folder, exist_ok=True)
        
        # for each diffusion file, check if it's 4d, extract brain, then register to skull stripped target
        is_raw_sequence_nifti = lambda file, sequence: file.endswith('.nii.gz') and sequence in file and not '_to_' in file
        
        all_dwi = []
        for file in files_in_session_folder:
            for sequence in self.DWI_STRINGS:
                if is_raw_sequence_nifti(file, sequence):
                    file_path = os.path.join(session_folder, file)
                    
                    all_dwi.append(file_path)
                    
        extract_brain_for_files_and_register_to_target(subject_name, all_dwi, dwi_coreg_folder, target_file, target_sequence)

                    
                    

        
        
        
        