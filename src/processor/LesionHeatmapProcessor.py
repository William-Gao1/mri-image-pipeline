from .SessionProcessor import SessionProcessor, SessionInfo
from utils.registration import run_cmd
from utils.filelock import LockedFile

from typing_extensions import override
import os
from datetime import date

class LesionHeatmapProcessor(SessionProcessor):
    @override
    def process_session(self, session_info: SessionInfo) -> None:
        output_folder = session_info["output_root"]
        subject_name = session_info["subject"]
        session_folder = session_info["session_folder"]
        
        lesion_files = list(filter(lambda s: ('seg' in s.lower() or 'lesion' in s.lower() or 'stroke' in s.lower()) and '_to_template' in s.lower(), os.listdir(session_folder)))

        # if has no lesion file, then nothing to do
        if len(lesion_files) == 0:
            print(f'Error for subject {subject_name}: Cannot find lesion file')
            return
        
        
        lesion_file_path = os.path.join(session_folder, lesion_files[0])
        
        # has lesion file
        heatmap_file = f'lesion_heatmap_{date.today().strftime("%y-%m-%d")}'
        names_file_path = os.path.join(output_folder, f'{heatmap_file}_names.txt')
        heatmap_file_path = os.path.join(output_folder, heatmap_file + '.nii.gz')


        with LockedFile(names_file_path):
            with open(names_file_path, 'a+') as locked_name_file:
                # if there's no heatmap, then we are the first subject
                is_first_subject = not os.path.isfile(heatmap_file_path)
            
                if is_first_subject:
                    print(f'Subject {subject_name} is the first segmentation, creating lesion map')
                    locked_name_file.truncate(0)
                    
                    # copy seg file as lesion file
                    out, err, status = run_cmd(f'cp {lesion_file_path} {heatmap_file_path}')
                    print(out, err)
                else:
                    run_cmd(f'fslmaths {heatmap_file_path} -add {lesion_file_path} {heatmap_file_path}')

                locked_name_file.write(f'{subject_name} added to heatmap: {heatmap_file_path}\n')
