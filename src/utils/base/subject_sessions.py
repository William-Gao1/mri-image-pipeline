import os

def read_subjects_from_file(root, file):
    """Reads in all subjects from text file

    Args:
        file (string): The path to the file
        root (string): The path to the root directory

    Returns:
        list[string]: List of subjects 
    """
    with open(file) as f:
        lines = [line.strip() for line in f]
    
    for subject in lines:
        subject_dir = os.path.join(root, subject)
        assert os.path.isdir(subject_dir), f'Subject {subject} provided in subject file, but folder named {subject} can not be found in {root}'
    return lines

def get_all_subjects(root_folder, subject_file=None):
    """Gets all subject names from subject file. If subject file is not provided, then take all folders ending in a number

    Args:
        root_folder (string): The root folder containing the subject folders
        subject_file (string, optional): Path to text file containing one subject per line. Defaults to None.

    Returns:
        list[string]: List of subject names
    """
    _, folders_in_root, _ = next(os.walk(root_folder))
    
    folders_in_root = list(filter(lambda folder: folder[-1].isdigit(), folders_in_root))
    
    if subject_file is not None:
        subjects_from_file = read_subjects_from_file(root_folder, subject_file)
        
        for subject in subjects_from_file:
            if not subject[-1].isdigit():
                raise Exception(f'Subject folder names must end with a number but subject {subject} provided in subject file does not')
                
            assert subject in folders_in_root, f'Subject {subject} provided in subject file, but folder named {subject} can not be found in {root_folder}'
        return subjects_from_file
    
    return folders_in_root

def is_session_folder(folder):
    """Determines if a folder is a session folder

    Args:
        folder (string): Path to folder

    Returns:
        bool: True if folder is session folder, false otherwise
    """
    _, folders, files = next(os.walk(folder))
    
    folder_has_nifti_files = any(file.endswith('.nii') or file.endswith('.nii.gz') for file in files)
    
    if folder_has_nifti_files:
        # if the folder has nifti files, then it's a session folder
        return True
    elif len(folders) > 0 and any(file.endswith('dcm') for file in os.listdir(os.path.join(folder, folders[0]))):
        # if there are no niftis and there are folders with dicom files, then it's a session folder
        return True
    
    return False


def find_sessions_for_subject(subject_folder):
    """Finds all session folders in a subject folder
    
    Args:
        subject_folder (string): Path to subject folder
    Returns:
        list[string]: A list of session folders inside the subject_folder. Note that the subject folder itself may be a session folder
    """
    if is_session_folder(subject_folder):
        return [subject_folder]
    
    _, session_folders, _ = next(os.walk(subject_folder))
    return [os.path.join(subject_folder, session) for session in session_folders]

def find_all_sessions_for_subjects(root_folder, subjects):
    """Generates a subject to session folders map. If the subject is single session, the list has one element, the subject folder itself
    For example
    {
        'subject1': [list of session folders associated with subject1],
        'subject2': [list of session folders associated with subject2],
        ...
    }

    Args:
        root_folder (string): Top level folder containing all subject folders
        subjects (list[string]): A list of all subject names (subject folders)

    Raises:
        Exception: IF a subject folder is empty

    Returns:
        dict: A map of subjects to list of sessions
    """

    result_dict = {}
    for subject in subjects:
        result_dict[subject] = find_sessions_for_subject(os.path.join(root_folder, subject))
    
    return result_dict
