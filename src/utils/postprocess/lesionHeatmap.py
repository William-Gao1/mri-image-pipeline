from ..registration import run_cmd

import os
from datetime import date
import math


def postprocessLesionHeatmap(output_folder):
    heatmap_name = f'lesion_heatmap_{date.today().strftime("%y-%m-%d")}'
    name_file = f'{heatmap_name}_names.txt'

    name_file_path = os.path.join(output_folder, name_file)

    num_subjects = sum(1 for _ in open(name_file_path))
    
    if num_subjects == 0:
        return
    
    thresh = math.floor(num_subjects * 0.1)
    heatmap_file_path = os.path.join(output_folder, heatmap_name + '.nii.gz')
    thresh_file_path = os.path.join(output_folder, heatmap_name + '_thr.nii.gz')

    print(f'Removing voxels with less than {thresh} subjects')

    run_cmd(f'fslmaths {heatmap_file_path} -thr {thresh} {thresh_file_path}')
