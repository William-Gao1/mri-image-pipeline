from processor import get_processor_for_step

import json
from sys import argv

session_info = json.loads(argv[1])
step = argv[2]

if step == 'base':
    dcm2nii_processor = get_processor_for_step('dcm2nii')
    dcm2nii_processor.process_session(session_info)
    # output folder now becomes root folder of next step
    session_info["session_folder"] = session_info["output_folder"]
    
    mask_processor = get_processor_for_step('mask')
    mask_processor.process_session(session_info)
    
    registration_processor = get_processor_for_step('registration')
    registration_processor.process_session(session_info)
    
elif step == 'all':
    dcm2nii_processor = get_processor_for_step('dcm2nii')
    dcm2nii_processor.process_session(session_info)
    # output folder now becomes root folder of next step
    session_info["session_folder"] = session_info["output_folder"]
    
    mask_processor = get_processor_for_step('mask')
    mask_processor.process_session(session_info)
    
    registration_processor = get_processor_for_step('registration')
    registration_processor.process_session(session_info)

    brain_extraction_processor = get_processor_for_step('brainExtraction')
    brain_extraction_processor.process_session(session_info)

    stroke_segmentation_processor = get_processor_for_step('segmentStroke')
    stroke_segmentation_processor.process_session(session_info)
elif step == 'fixMask':
    registration_processor = get_processor_for_step('registration')
    registration_processor.process_session(session_info)

    brain_extraction_processor = get_processor_for_step('brainExtraction')
    brain_extraction_processor.process_session(session_info)

    stroke_segmentation_processor = get_processor_for_step('segmentStroke')
    stroke_segmentation_processor.process_session(session_info)
elif step == 'map':
    register_to_template_processor = get_processor_for_step('registerToTemplate')
    register_to_template_processor.process_session(session_info)
    
    heatmap_processor = get_processor_for_step('lesionHeatmap')
    heatmap_processor.process_session(session_info)
else:
    processor = get_processor_for_step(step)
    if processor is None:
        print(f'Step {step} does not exist, aborting...')
        exit(1)
    processor.process_session(session_info)
