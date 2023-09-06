import nibabel as nib
import os

from .command import run_cmd

def check_4d(dwi_path: str, output_dir: str):
    """Checks if a nifti file (dwi) is a 4d file. If it is, extract the first volume

    Args:
        dwi_path (str): path to nifti
        output_dir (str): path to output folder of 3d conversion

    Returns:
        bool | None: true if image was 4d, false if it was not 4d. Returns none if the image was 4d but conversion to 3d failed
    """
    image_dim_0 = nib.load(dwi_path).header['dim'][0]
    
    if image_dim_0 > 3:
        # dwi is 4d
        dwi_first_vol_name = os.path.split(dwi_path)[1].split('.')[0] + '_first_vol.nii.gz'
        result_path = os.path.join(output_dir, dwi_first_vol_name)
        
        _, err, code = run_cmd(f'fslroi {dwi_path} {result_path} 0 1')
    
        if code != 0:
            print(f'Error converting {dwi_path}: \n\t is 4-d but could not extract first volume: {err}')
            return None
    
        return True
    elif image_dim_0 == 3:
        return False
    else:
        # neither 3d or 4d? do nothing
        print(f'Warning for {dwi_path} \n\tImage is {image_dim_0} dimensional')
        return False