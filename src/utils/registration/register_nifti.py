import os
import json

from .command import config_to_command_options, run_cmd

config_folder = os.path.abspath(__file__ + '/../../../../config/')



def register_nifti_to_target(subject_name: str, output_folder: str, target_nifti: str, moving_nifti: str, moving_sequence: str, target_sequence: str, config_file = 'registration_config.json') -> int:
    """Registers one nifti to another

    Args:
        session_name (str): Name of subject that the nifti belongs to
        output_folder (str): Path to output folder
        target_nifti (str): Path to target nifti
        moving_nifti (str): Path to moving nifti
        moving_sequence (str): Sequence of moving nifti
        target_sequence (str): Sequence of target nifti (e.g. T1, T2, FL, etc.)
        config_file(str): Config file located in /config folder (default is registration_config.json)
    
    Returns:
        int: Status code (0 for success, non-zero for fail)
    """
    
    print(f'Registering {moving_sequence} to {target_sequence} for subject {subject_name}', flush=True)
    
    sys_cmd = get_registration_command(subject_name, output_folder, target_nifti, moving_nifti, moving_sequence, target_sequence, config_file)
    
    _, err, code = run_cmd(sys_cmd)

    if code != 0:
        print(f'Error for {subject_name}: Registration of {moving_sequence} to {target_sequence} failed: {err}', flush=True)

    return code

def get_registration_command(subject_name: str, output_folder: str, target_nifti: str, moving_nifti: str, moving_sequence: str, target_sequence: str, config_file: str) -> str:
    """Gets registration command from config file `config/registration_config.json`

    Args:
        subject_name (str): Name of subject
        output_folder (str): Path to folder
        target_nifti (str): Path to registration target
        moving_nifti (str): Path to moving nifti
        moving_sequence (str): Sequence of moving nifti (e.g. 'T1', 'T2', 'FL')
        target_sequence (str): Sequence of target nifti (e.g. 'T1', 'T2', 'FL')
        config_file(str): Config file located in /config folder (default is registration_config.json)

    Returns:
        str: The command
    """
    
    registration_config = json.load(open(os.path.join(config_folder, config_file)))
    registered_files_prefix = os.path.join(output_folder, f'{subject_name}_{moving_sequence}_to_{target_sequence}_')

    command_replace_object = {}
    command_replace_object["prefix"] = registered_files_prefix
    command_replace_object["target_file"] = target_nifti
    command_replace_object["moving_file"] = moving_nifti
    
    options = [config_to_command_options(registration_config[key], command_replace_object) for key in registration_config.keys()]
    
    sys_cmd = "antsRegistration " +  ' '.join(options)
    
    return sys_cmd

def apply_transform(subject_name: str, file_to_transform: str, template_file: str, affine_transform_file: str, warp_transform_file: str) -> int:
    """Applies a transform to a nifti

    Args:
        subject_name (str): Name of subject
        file_to_transform (str): Path to nifti to apply transform
        template_file (str): Path to template file that the nifti is being registered to
        affine_transform_file (str): Affine transformation .mat file
        warp_transform_file (str): Warp transofrm 1Warp.nii.gz file

    Returns:
        int: Status code (0 for success, non-zero for fail)
    """
    
    output_name = file_to_transform.split('.nii.gz') + '_to_template.nii.gz'
    cmd = f'antsApplyTransforms --dimensionality 3 --float 0 --input {file_to_transform} --reference-image {template_file} --output {output_name} --transform {warp_transform_file} --transform [{affine_transform_file}]'
    
    _, err, code = run_cmd(cmd)
    
    if code != 0:
        print(f'Error for {subject_name}: Failed to apply transformation to {template_file} for {file_to_transform}: {err}')
    
    return code