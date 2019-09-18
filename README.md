# Blender Annotation Tool
Tools for annotating and using 3D models for synthetic data generation.

Although this can be used in many ways, the initial reason for creating this project is to label
the parts of [ShapeNet](www.shapenet.org) car models so that the doors and trunks can be deformed
in a data generation pipeline for RGB images and semantic segmentation images.


# Project Layout

### [annotation_tools](https://github.com/mpeven/Blender-Annotation-Tool/tree/master/annotation_tools)
The tools used with [Blender](https://www.blender.org) to annotate models.

### [automatic_annotation](https://github.com/mpeven/Blender-Annotation-Tool/tree/master/automatic_annotation)
Automatic transfer of annotations to un-annotated models.

This uses and unsupervised clustering method based on shape descriptors to find similar models to
the source model (the hand-annotated model) and transfers the vertices belonging to the
annotated parts of this source model by locating the vertices in a 3D bounding box of a target
model (the un-annotated models in the same cluster).

### [export_tools](https://github.com/mpeven/Blender-Annotation-Tool/tree/master/export_tools)
For exporting the annotations in various ways.

1. Contains a script for creating .obj files from the annotations.
2. Contains a script for loading the created .obj files into Unreal Engine.


# Getting Started
You will need to have Blender 2.79 installed.

To use annotation_tools/annotate.py, you will need to install pandas into Blender's python:
```
cd /path/to/blender/python
rm -rf ./lib/python3.7/site-packages/numpy
./python -m ensurepip
./python -m pip install pandas
```

Then, you can run this tool from the commandline like so:
```
blender --python annotation_tools/annotate.py -- -m <shapenet model id> -o <object mode> -a <annotate mode>
```

# TODO

1. Add Unreal import scripts
2. Switch to Blender 2.8
