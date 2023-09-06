from utils.postprocess import postprocessLesionHeatmap

from sys import argv

step = argv[1]
output_folder = argv[2]

if step == 'lesionHeatmap' or step == 'map':
    postprocessLesionHeatmap(output_folder)