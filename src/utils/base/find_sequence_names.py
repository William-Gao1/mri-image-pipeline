import json
import os

path_to_sequence_string_lists = os.path.abspath(__file__ + '/../../../../config/sequence_string_lists.json')
sequence_lists = json.load(open(path_to_sequence_string_lists))

def find_strings_with_sequence(strings, seq_string):
    """Find the strings in a list of strings that contains a particular sequence string

    Args:
        strings (list[string]): List of strings
        seq_string (string): Sequence string to search for

    Returns:
        list[String]: Returns the strings that contains seq_string
    """
    result = []
    for string in strings:
        if seq_string.lower() in string.lower():
            result.append(string)
        
    return result

def find_sequences_for_session(session_path):
    """Finds sequences of interest for a session

    Args:
        session_path (string): Path to the session

    Returns:
        dict: A sequence to filename mapping, sorted by importance as defined in config/sequence_string_lists.json
    """
    result = {}
    objects_in_session_folder = os.listdir(session_path)

    for sequence in sequence_lists.keys():
        result[sequence] = []
        for sequence_str in sequence_lists[sequence]:
            folder_with_seq_string = find_strings_with_sequence(objects_in_session_folder, sequence_str)

            for folder in folder_with_seq_string:
                objects_in_session_folder.remove(folder)
                result[sequence].append(os.path.join(session_path, folder))
    
    return result

