# Contributing a Script to Image Preprocessing

This guide will give you an overview of the contribution workflow of how to add a script to this repository.

## New contributor guide

To get an overview of the project, read the [README](readme.md). Here are some resources to help you get started with the git flow required to add to this repositiory.

- [Git flow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow)
- [Collaborating with pull requests](https://docs.github.com/en/github/collaborating-with-pull-requests)

You must never push directly to `main`. Always check you are on the correct branch by running `git branch` in your terminal. If you are unsure, consult the "Git flow" link above.

## Code structure

This section will walk you through the high level details of what happens when a user runs `./run.sh`. First, `run.sh` will open a termial on HPC, load python3.8.0 and pass all command line arguments to a call to `run.py` which is where the main logic begins.

`run.py` takes the root folder passed by `--root/-r` and the subject file passed by `--subject-file/-f` and finds all the session folders for each subject. Then, it will create a JSON object with the session folder path, session name, subject name, and output path (passed by `--output-dir/-o`) for each session. For illustration, it will look something like this:

```json
{
  "subject": "IPSS_011_22808",
  "session": "IPSS_011_22808_01_SE01_MR",
  "session_folder": "/hpf/projects/ndlamini/images/MM_ADC/IPSS_011_22808/IPSS_011_22808_01_SE01_MR",
  "output_folder": "/hpf/projects/ndlamini/scratch/jowsmith/subjects_preprocessed/"
}
```

Then, `run.py` will submit a bash script that creates one Slurm task per session. This is how each session is processed concurrently. Each slurm task calls `src/run_step_for_subject.py` with the JSON session info object described above and the step passed by `--step/-s`.

`run_step_for_subject.py` will then call the appropriate script with the JSON session info object. It is up to the script to process this session.

## Adding a Script

This section will walk you through how to add a script that users can call from `./run.sh`. Your script will be responsible for processing one session only. You are not responsible for finding the session folders or figuring out which subjects need to be processed.

1. Copy the template file `src/processor/__TemplateProcessor.py` into the same directory and give it an appropriate file name. Remember to rename the class as well.
2. The class must override the `process_session` method. This is the entrypoint to your script that `run_step_for_subject.py` will call. You will receive the `session_info` parameter that contains the subject name, session name, path to session folder, path to output folder. See **Code Structure** section for more details.
3. When you are done writing code, modify the `get_processor_for_step` function in the  `src/processor/__init__.py` file. Add an additional `elif step === <STEP_NAME>` with an appropriate step name for your script and return your processor.
4. That's it! Document your step in the [README](readme.md) file under the **Steps** section and make a pull request.

## Post and Pre Processing

There are instances where you may want to run code before or after the script runs for any subject. In that case, you can add pre/post processing code to `preprocess.py` or `postprocess.py`. These two files run before and after subjects are processed. The files will be called with the step name, and the output folder as command line arguments

## Locks

Since each subject is processed simultaneously, there may be intances where you only want one subject doing a particular thing at a time. For example, when generating a heatmap, you may only want one subject to be writing to the heatmap at a time. This is a classic use case for a lock. However, since each subject is running in a separate process, the traditional `multithreading.Lock()` will not work. This repository has a custom lock that makes use of files. In short, the idea is, if a certain file exists, then that indicates another process is currently doing the mutually exclusive action and the current process should wait until the file is deleted.

To use the lock, import the `FileLock` class from `utils/filelock`. Then, in your code:

```python
with FileLock('/some/path/where/you/would/like/the/lockfile/created/'):
    # you now have the lock, do whatever you need

# the lock is automatically released when the `with` statement ends
```
