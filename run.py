import argparse
import os
import subprocess
import json
import pathlib

from src.utils.base import find_all_sessions_for_subjects, get_all_subjects

rpi_script_location = os.path.join(os.path.dirname(__file__), 'src', 'utils', 'registration', 'scripts', 'toRPI.sh')
os.chmod(rpi_script_location, 0o755)


parser = argparse.ArgumentParser(
    prog='Image Preprocessor',
    description='Preprocessing Toolkit for MRI processing'
)

parser.add_argument('-r', '--root', required=True)
parser.add_argument('-s', '--step', required=True)
parser.add_argument('-o', '--output-dir')
parser.add_argument('-e', '--email')
parser.add_argument('-f', '--subject-file')

args = parser.parse_args()

if not args.output_dir:
    args.output_dir = args.root


def get_sbatch_script(session_info_list, step, email, output_root_folder):
    run_step_script_location = os.path.join(pathlib.Path(__file__).parent.resolve(), 'src')
    return f"""#!/bin/bash

#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=4G
#SBATCH --mail-type=ALL
#SBATCH --ntasks={len(session_info_list)}
{('#SBATCH --mail-user=' + email) if email else ''}

module load python/3.8.0
module load dcm2niix
module load ANTs/2.3.2
module load fsl/5.0.10
module load afni/20191017
module load openmpi/2.1.1
module load libpng/1.2.59
module load gsl
export LD_PRELOAD=/usr/lib64/libfreetype.so
source $FSLDIR/etc/fslconf/fsl.sh

cd {run_step_script_location}

export PYTHONPATH=/hpf/projects/ndlamini/scratch/wgao/python3.8.0/
export TF_CPP_MIN_LOG_LEVEL=3

python preprocess.py {step} {output_root_folder}

{' & '.join([f"srun --ntasks 1 --nodes 1 -c 4 --quiet --job-name={session_info['session']} python3 run_step_for_subject.py '{json.dumps(session_info)}' {step}" for session_info in session_info_list])}

wait

python postprocess.py {step} {output_root_folder}

echo Done!
"""

subjects = get_all_subjects(args.root, args.subject_file)
subject_sessions = find_all_sessions_for_subjects(args.root, subjects)
session_info_list = []
for subject in subject_sessions.keys():
    for session_folder in subject_sessions[subject]:
        session_name = session_folder.split(os.sep)[-1]
        session_info = {}
        session_info["subject"] = subject
        session_info["session"] = session_name
        session_info["session_folder"] = session_folder
        session_info["output_folder"] = os.path.join(args.output_dir, subject) if subject == session_name else os.path.join(args.output_dir, subject, session_name)
        session_info["output_root"] = args.output_dir
        
        os.makedirs(session_info["output_folder"], exist_ok=True)
        session_info_list.append(session_info)
        
        

p = subprocess.Popen(['sbatch'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, text=True)
out, err = p.communicate(input=get_sbatch_script(session_info_list, args.step, args.email, args.output_dir))
print(out, err)

#print(get_sbatch_script(session_info_list, args.step, args.email, subjects, args.output_dir))
        
        

