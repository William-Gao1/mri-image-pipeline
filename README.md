# Image Preprocessing

## Getting started

This repository contains the scripts to preprocess DICOM and Nifti images. There is only one basic command you need to invoke all of these scripts. That is the `./run.sh` command. You must run this on HPC.

Before using `./run.sh`, you will need to give execute permissions to `run.sh` by running `chmod +x run.sh` in your terminal.

Before beggining, it is recommended that you read this README file in its entirety. Please pay particular attention to the [Using run.sh](#using-runsh) and [Workflow](#workflow) sections.

## Using `run.sh`

You will need to specify options to the command such as where your images are located and which script you want to execute on those images. The options available are:

| Long flag      | Short flag | Description                                                                                  |
| -------------- | ---------- | -------------------------------------------------------------------------------------------- |
| --root         | -r         | The folder containing your sessions see the[Root Folder](#root-folder) Section                  |
| --step         | -s         | Which step you want to be executed see the[Steps](#steps) section                               |
| --output-dir   | -o         | The folder where the resulting images/files should be outputed (defaults to the root folder) |
| --subject-file | -f         | A text file with one subject per line. See the[Subjects File](#subjects-file) section           |
| --email        | -e         | Your email address to be notified when the script is complete                                |

### Root Folder

The root folder is the folder where all your subject folders are contained

```
├── root
    ├── subject1
    ├── subject2
    ├── subject3
    ├── ...
```

Each subject folder can be single session or multisession

**Single session subject folder**

```
├── subject1
    ├── nifti.nii.gz
    ├── something.json
    ├── something.bvec
    ├── ...
```

**Multi session subject folder**

```
├── subject2
    ├── subject2_01_SE01_MR
        ├── nifti.nii.gz
        ├── something.json
        ├── ...
    ├── subject2_01_SE02_MR
        ├── ...
    ├── ...
```

**Warning: Subject folders MUST end in a number (e.g IPSS_100 but not IPSS_subject)**

### Steps

Here are the current list of scripts can be specified to the `--step/-s` option in `run.sh`

* `dcm2nii`
  * Converts dicom folders to nifti files. Only converts the files with the substrings specified in `/config/sequence_string_lists.json`
* `registration`
  * Registers T1s, T2s, FLAIRs, DWIs, ADCs, eADCs, B0s, and B1000s to the T1 or T2 or FLAIR depending on which one is available
* `registerToTemplate`
  * Registers the T1 or T2 or FLAIR (depending on which one was used in `registration`) to a template file, then register all other files and segmentations to the template
* `mask`
  * Generates a brain mask for the T1 or T2 or FLAIR depending on which one is avilable
* `brainExtraction`
  * Extracts brain for all registered files using `_mask_edit.nii.gz` file or if that doesn't exist, use `_mask.nii.gz` file
* `lesionHeatmap`
  * Creates a heatmap from all lesion files and thresholds voxels with less than 10% of subjects
* `adcRegistration`
  * Registers all ADC files to either the T2, T1, or FL, whichever is available
* `segmentStroke`
  * Automatically segments stroke from the B1000 or DWI and ADC depending on what is available. Currently being tested so results may vary.
* `base`
  * Runs the `dcm2nii`, then `mask`, and finally `registration` step for each subject. Together, these are the base preprocessing steps needed for any image analysis
* `all`
  * Runs `dcm2nii`, `mask`, `registration`, `brainExtraction`, `segmentStroke`. These are all the pipeline steps that can be reliably run without manual intervention
* `map`
  * Runs `registerToTemplate` and `lesionHeatmap`. Run this after you have segmented the stroke for each subject
* `fixMask`
  * Runs `registration` , `brainExtraction`, then `segmentStroke`. Use this after fixing a bad brain mask.

### Subjects file

If you only want to run the scripts for a subset of the subjects in the root folder, you can optionally provide a text file with the names (not file paths) of the subjects that you would like to be processed. Each name must be on a separate file and must match the name of a folder in the root folder.

## Workflow

The usual workflow is as follows. First, run the `all` step:

```
./run.sh -r <path_to_dicom_folders> -o <path_to_output_folder> -s all
```

Next, we need to segment the stroke for each subject. If the stroke has a DWI/b1000, an ADC, and either a T1, T2, or FLAIR, then you should see an automatically generated `_stroke_segmentation_to_T1/T2/FL_Warped.nii.gz` file. This is a first attempt at automatically segmenting the stroke, but it is unreliable especially for unclear/small stroke lesions. You should edit this segmentation in 3D slicer to properly reflect the stroke lesion. For reference, you **must** segment against the `DWI/b1000_to_T1/T2/FL.nii.gz` and `ADC_to_T1/T2/FL.nii.gz` files (i.e. the DWI/b1000 and ADC files that have been registered to the subject's T1/T2/FL).

If you're subject is **missing** a T1 or T2 or FLAIR, but **has** a DWI/b1000 and an ADC, then you should see a `_stroke_segmentation.nii.gz` file. You should again edit this segmentation to reflect the stroke but this time use the `_AX_DWI/b1000.nii.gz` and `_AX_ADC.nii.gz` files. Note that registration of these files is not possible since the subject is missing a T1/T2/FL and the pipeline for this subject will not continue.

If you're subject has a DWI/b1000 but not an ADC or vice-versa, then automatic stroke segmentation will not work and you will not see a stroke segmentation file. It is possible to still manually segment against only the DWI/b1000 or ADC. In this case, you must segment against the `DWI/b1000_to_T1/T2/FL.nii.gz` or `ADC_to_T1/T2/FL.nii.gz` file (i.e. the DWI/b1000 and ADC files that have been registered to the subject's T1/T2/FL) is possible and name your segmentation `<id>_stroke_segmentation_to_T1/T2/FL_Warped.nii.gz`. If there are no registered files (i.e. your subject does not have a T1/T2/FL), then you can still segment against the DWI/b1000 or ADC, but registration is not possible and so the pipeline for this subject will not continue.

After you are happy with all the stroke segmentations, run the `map` step:

```
./run.sh -r <path_to_folder_with_subjects> -s map
```

This will register all files and the stroke segmentation to the template and generate a heatmap of all lesions. Double check to make sure the `stroke_segmentation_to_template_Warped.nii.gz` files for each subject are properly aligned with the `DWI/b1000_to_template_Warped.nii.gz` and `ADC_to_template_Warped.nii.gz` files.

![Pipeline](./Image%20Preprocessing%20Pipeline.svg)

## Troubleshooting brain mask generation

If you have run `all` but find that you are unhappy with the brain mask generated, you can edit the brain mask as desired and run the `maskFix` step to run the remaining steps with your new brain mask.

## Viewing the state of a running script

Once you run `./run.sh`, you should see a single line printed informing you of the job id. It will look like:

`Submitted batch job <JOB_ID>`

This is the job id that will be referenced in this section

You can view high level information about a current job (e.g. Elapsed time) by running `squeue --me` and looking for the job id of your job.

The script processes each subject in parallel. You can view information about the state of processing on a subject by subject basis by running `sacct --format="JobID,JobName%30,State" -j <JOB_ID>`

## Examples

To run the `dwicoreg` step for subjects in the folder `/hpf/projects/ndlamini/images/MM_ADC` and to be emailed when completed:

```
./run.sh -r /hpf/projects/ndlamini/images/MM_ADC -s dwicoreg -e <yourname>.sickkids.ca
```

To run the `dcm2nii` step for subjects in `/hpf/projects/ndlamini/scratch/joesmith/subjects.txt` in the root folder `/hpf/projects/ndlamini/images/MM_ADC` and output results in `/hpf/projects/ndlamini/scratch/joesmith/preprocess` folder:

```
./run.sh -r /hpf/projects/ndlamini/images/MM_ADC -o /hpf/projects/ndlamini/scratch/joesmith/preprocess -s dcm2nii -f /hpf/projects/ndlamini/scratch/joesmith/subjects.txt
```

## Altering Registration Parameters

If you would like to alter image registration parameters that are used in the call to `antsRegistration`, the parameter values can be altered in `/config/registration_config.json`

Note: the string `{prefix}` will be replaced with the string `<SUBJECT_NAME>_<SEQUENCE_NAME>_to_<TARGET_SEQUENCE_NAME>_` (e.g. `IPSS_011_92037526_DWI_to_T1_`) at runtime

Furthermore, the strings `{target_file}` and `{moving_file}` will be replaced with the paths to the target and moving files respectively at runtime

## Cleaning Slurm Output Files

If you would like to remove all slurm output files quickly, a helper script is provided and can be called using `./clean.sh`
