from abc import ABC, abstractmethod
from typing import NamedTuple


class SessionInfo(NamedTuple):
    subject: str
    session: str
    session_path: str
    output_folder: str
    
class SessionProcessor(ABC):
    @abstractmethod
    def process_session(self, session_info: SessionInfo) -> None:
        pass