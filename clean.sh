#!/bin/bash

slurmFiles=$(ls | grep "slurm-[0-9]\+\.out$")

rm $slurmFiles