import subprocess
from typing import Tuple

def config_to_command_options(cmd_config: dict, replace: dict):
    """Generates command line options based on configuration file (see config/registration_config for example)
    Replaces {token}s using the `replace` dictionary (see `get_registration_command` function in register_nifti.py)

    Args:
        cmd_config (dict): dictionary of option -> value string mappings
        replace (dict): dictionary of token -> replacement string mappings

    Returns:
        string: options of the command line command
    """
    command_options = []
    for option in cmd_config.keys():
        value = str(cmd_config[option])
        
        for token in replace.keys():
            value = value.replace('{' + token + '}', replace[token])
        
        command_options.append(f'--{option.strip()} {value.strip()}')
    return ' '.join(command_options)

def run_cmd(sys_cmd: str) -> Tuple[str, str, int]:
    """Runs a system command. Is a blocking call

    Args:
        sys_cmd (str): The command to execute

    Returns:
        Tuple[str, str, int]: The stdout and stderr of the command upon completion and the return code
    """
    p = subprocess.Popen(sys_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    return stdout.decode('utf-8'), stderr.decode('utf-8'), p.returncode

def run_cmd_async(sys_cmd: str) -> subprocess.Popen:
    """Runs a system command. Is not a blocking call

    Args:
        sys_cmd (str): The command to run

    Returns:
        subprocess.Popen: The process running the command
    """
    return subprocess.Popen(sys_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)