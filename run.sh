#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate ds
python "$@" 