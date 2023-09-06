import os
from datetime import date

def preprocessLesionHeatmap(output_folder):
    heatmap_name = os.path.join(output_folder, f'lesion_heatmap_{date.today().strftime("%y-%m-%d")}')

    try:
        os.remove(f'{heatmap_name}.nii.gz')
    except:
        pass

    try:
        os.remove(f'{heatmap_name}_thr.nii.gz')
    except:
        pass

    try:
        os.remove(f'{heatmap_name}_names.txt.lock')
    except:
        pass
    
    try:
        os.remove(f'{heatmap_name}_names.txt')
    except:
        pass