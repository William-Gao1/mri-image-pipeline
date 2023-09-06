from .SessionProcessor import SessionProcessor, SessionInfo
from utils.registration import generate_brain_mask

from typing_extensions import override
import os

# Remember to add this processor to src/processor/__init__.py when you're done
class __TemplateProcessor(SessionProcessor):
    @override
    def process_session(self, session_info: SessionInfo) -> None:
        output_folder = session_info["output_folder"]
        subject_name = session_info["subject"]
        session_folder = session_info["session_folder"]
        session_name = session_info["session"]
        
        # process session code here
        
        pass