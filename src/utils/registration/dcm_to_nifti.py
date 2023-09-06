import os
import pydicom as dcm
import numpy as np
import dicom2nifti
import dicom2nifti.settings as settings

settings.disable_validate_slice_increment()
settings.disable_validate_instance_number()

from .command import run_cmd

AXIAL_ORIENTATION = [1, 0, 0, 0, 1, 0]
CORONAL_ORIENTATION = [1, 0, 0, 0, 0, -1]
SAGITTAL_ORIENTATION = [0, 1, 0, 0, 0, -1]

def get_view(dicom_folder: str) -> str:
    """Given a dicom folder, determine the view (axial, sagittal, coronal)

    Args:
        dicom_folder (str): Path to dicom folder

    Returns:
        str: the view, returns UK if unknown
    """
    files = os.listdir(dicom_folder)

    if len(files) == 0:
        return 'UK'
    
    dcm_file = dcm.read_file(os.path.join(dicom_folder, files[0]))

    try:
        orientation = np.round(dcm_file.ImageOrientationPatient).astype(int)
    
        if np.array_equal(orientation, AXIAL_ORIENTATION):
            return 'AX'
        elif np.array_equal(orientation, SAGITTAL_ORIENTATION):
            return 'SAG'
        elif np.array_equal(orientation, CORONAL_ORIENTATION):
            return 'COR'
    except:
        pass

    return 'UK'

# def convert_dcm_folder_to_nifti(subject_name: str, output_folder: str, dcm_folder: str, sequence_name: str) -> None:
#     """Converts a dicom folder to nifti image

#     Args:
#         subject_name (str): Name of subject
#         output_folder (str): Path to output folder
#         dcm_folder (str): Path to dicom folder
#         sequence_name (str): Name of sequence being converted (e.g. 'T1', 'T2', 'FL')
#     """

#     view = get_view(dcm_folder)

#     dcm2nii_cmd = f'dcm2niix -z y -f {subject_name}_{view}_{sequence_name} -o {output_folder} {dcm_folder}'


#     out, err, code = run_cmd(dcm2nii_cmd)

#     if code != 0:
#         print(f'Error for {subject_name}: Dcm to nifti failed for sequence {dcm_folder}: {err} {out}')

#     #ensure nifti in RPI
#     rpi_script_location = os.path.join(os.path.dirname(__file__), 'scripts', 'toRPI.sh')

#     _, err, code = run_cmd(f'{rpi_script_location} {os.path.join(output_folder, f"{subject_name}_{view}_{sequence_name}.nii.gz")}')

#     if err:
#         print(f'Error for {subject_name}: RPI failed: {err}')

def convert_dcm_folder_to_nifti(subject_name: str, output_folder: str, dcm_folder: str, sequence_name: str) -> None:
    """Converts a dicom folder to nifti image

    Args:
        subject_name (str): Name of subject
        output_folder (str): Path to output folder
        dcm_folder (str): Path to dicom folder
        sequence_name (str): Name of sequence being converted (e.g. 'T1', 'T2', 'FL')
    """

    view = get_view(dcm_folder)

    try:
        output_nifti = os.path.join(output_folder, f'{subject_name}_{view}_{sequence_name}.nii.gz')
        
        if os.path.exists(output_nifti):
            count = 1
            output_nifti = os.path.join(output_folder, f'{subject_name}_{view}_{sequence_name}_{count}.nii.gz')
            while os.path.exists(output_nifti):
                count += 1
                output_nifti = os.path.join(output_folder, f'{subject_name}_{view}_{sequence_name}_{count}.nii.gz')

        dicom2nifti.dicom_series_to_nifti(dcm_folder, output_nifti)
    
        # ensure nifti in RPI
        rpi_script_location = os.path.join(os.path.dirname(__file__), 'scripts', 'toRPI.sh')

        _, err, _ = run_cmd(f'{rpi_script_location} {output_nifti}')

        if err:
            print(f'Error for {subject_name}: RPI failed: {err}')
    except Exception as e:
        print(f'Error for {subject_name}: could not convert dicom folder {dcm_folder} to nifti: {e}')