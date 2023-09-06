from .SessionProcessor import SessionProcessor, SessionInfo
from utils.registration import register_nifti_to_target


from typing_extensions import override
import os

class AdcRegistrationProcessor(SessionProcessor):
    @override
    def process_session(self, session_info: SessionInfo) -> None:
        output_folder = session_info["output_folder"]
        subject_name = session_info["subject"]
        session_folder = session_info["session_folder"]

        nifti_prefix = os.path.join(output_folder, subject_name)

        t1 = f'{nifti_prefix}_T1.nii.gz'
        t2 = f'{nifti_prefix}_T2.nii.gz'
        fl = f'{nifti_prefix}_FL.nii.gz'

        has_t1 = os.path.isfile(t1)
        has_t2 = os.path.isfile(t2)
        has_fl = os.path.isfile(fl)

        files_in_session_folder = os.listdir(session_folder)

        # now, register all the adc sequences
        adc_sequences = ['ADC', 'eADC']

        # figure out which file and sequence to register to
        register_to_seq = None
        register_to_file = None
        if has_t2:
            register_to_seq = 'T2'
            register_to_file = t2
        elif has_t1:
            register_to_seq = 'T1'
            register_to_file = t1
        elif has_fl:
            register_to_seq = 'FL'
            register_to_file = fl

        if register_to_seq is not None:
            for file in files_in_session_folder:
                for sequence in adc_sequences:
                    if sequence in file.split('_')[-1] and file.endswith('.nii.gz'):
                        output_file = os.path.join(output_folder, file)
                        moving_sequence = file.split('_')[-1].split('.')[0]
                        register_nifti_to_target(subject_name, output_folder, register_to_file, output_file, moving_sequence, register_to_seq)
        else:
            print(f'Warning for {subject_name}: Subject has no T1 or T2 or FL to register adc')