#!/bin/bash

chmod +x ./submit.sh ./clean.sh
srun submit.sh "$@"