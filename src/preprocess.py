from utils.preprocess import preprocessLesionHeatmap

from sys import argv

step = argv[1]
output_folder = argv[2]

if step == 'lesionHeatmap' or step == 'map':
    preprocessLesionHeatmap(output_folder)