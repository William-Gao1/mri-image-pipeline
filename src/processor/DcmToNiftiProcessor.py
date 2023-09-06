from .SessionProcessor import SessionProcessor, SessionInfo
from utils.base import find_sequences_for_session
from utils.registration import convert_dcm_folder_to_nifti

from typing_extensions import override
import os
import nibabel as nib
from nibabel import processing

class DcmToNiftiProcessor(SessionProcessor):
    FLE_STRING = 'FLE'

    @override
    def process_session(self, session_info: SessionInfo) -> None:
        output_folder = session_info["output_folder"]
        subject_name = session_info["subject"]
        session_folder = session_info["session_folder"]

        sequences = find_sequences_for_session(session_folder)
        # convert all dcm folders to nifti
        for sequence in sequences.keys():
            for dcm_folder in sequences[sequence]:
                # ignore t1-fle folders
                if sequence == 'T1' and 'FLE' in dcm_folder: continue

                convert_dcm_folder_to_nifti(subject_name, output_folder, dcm_folder, sequence)

        # if we have dwi and adc, reorient dwi
        dwi_nifti_files = [x for x in os.listdir(output_folder) if x.endswith('.nii.gz') and 'DWI' in x and 'BRAIN' not in x.upper() and 'OLD' not in x.upper() and '_TO_' not in x.upper()]
        for dwi_file in dwi_nifti_files:
            adc_file = dwi_file.replace('DWI', 'ADC')
            adc_full_path = os.path.join(output_folder, adc_file)
            dwi_full_path = os.path.join(output_folder, dwi_file)
            if not os.path.exists(adc_full_path):
                continue
            
            dwi = nib.funcs.squeeze_image(nib.load(dwi_full_path))

            if dwi.ndim == 4:
                dwi = nib.funcs.four_to_three(dwi)[0]

            adc = nib.load(adc_full_path)

            # orient dwi to the adc
            dwi_reorient = processing.conform(dwi, adc.shape, adc.header.get_zooms())

            # rename old dwi files
            old_dwi_files = [x for x in os.listdir(output_folder) if 'DWI' in x and 'OLD' not in x.upper() and not 'TO' in x.upper()]
            for old_dwi_file in old_dwi_files:
                full_path = os.path.join(output_folder, old_dwi_file)
                new_path = os.path.join(output_folder, old_dwi_file.replace('DWI', 'DWI_old'))
                os.rename(full_path, new_path)

            # save reoriented dwi file
            nib.save(nib.Nifti1Image(dwi_reorient.get_fdata(), adc.affine), dwi_full_path)