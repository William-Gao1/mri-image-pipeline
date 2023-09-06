from .DcmToNiftiProcessor import DcmToNiftiProcessor
from .RegistrationProcessor import RegistrationProcessor
from .BrainMaskProcessor import BrainMaskProcessor
from .DwiCoregProcessor import DwiCoregProcessor
from .LesionHeatmapProcessor import LesionHeatmapProcessor
from .BrainExtractionProcessor import BrainExtractionProcessor
from .AdcRegistrationProcessor import AdcRegistrationProcessor
from .TemplateRegistrationProcessor import TemplateRegistrationProcessor
from .StrokeSegmentationProcessor import StrokeSegmentationProcessor

# remember to add your step to the README.md file!
def get_processor_for_step(step):
    if step == 'dcm2nii':
        return DcmToNiftiProcessor()
    elif step == 'registration':
        return RegistrationProcessor()
    elif step == 'mask':
        return BrainMaskProcessor()
    elif step == 'dwicoreg':
        return DwiCoregProcessor()
    elif step == 'lesionHeatmap':
        return LesionHeatmapProcessor()
    elif step == 'brainExtraction':
        return BrainExtractionProcessor()
    elif step == 'adcRegistration':
        return AdcRegistrationProcessor()
    elif step == 'registerToTemplate':
        return TemplateRegistrationProcessor()
    elif step == 'segmentStroke':
        return StrokeSegmentationProcessor()
