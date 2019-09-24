'''
This needs to be run from inside Unreal Engine

To do this, you will need to do the following:
1. Install "Python Editor Script Plugin"
2. Click "Window" -> "Developer Tools" -> "Output Log"
3. Click "Cmd" and switch to "Python"
4. Type in the full path of this script
'''

import unreal
import glob
import os

def main():
    # car_models_directory = '/home/mike/Projects/DIVA/car_models/car_models_auto_annotated'
    # destination_path = '/Game/ShapenetAutomatic'
    car_models_directory = '/home/mike/Projects/DIVA/car_models/car_models_hand_annotated'
    destination_path = '/Game/ShapenetManual'

    # Get all obj files
    files_to_import = get_all_obj_files(car_models_directory)

    # Create progress bar
    with unreal.ScopedSlowTask(len(files_to_import), "Importing Assets") as slow_task:
        slow_task.make_dialog(True)
        for file in files_to_import:
            # Import mesh and textures
            task = build_import_task(file, destination_path)
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

            # Update progress bar
            if slow_task.should_cancel():
                break
            slow_task.enter_progress_frame(1)


def get_all_obj_files(directory):
    return sorted(glob.glob(os.path.join(directory, '*.obj')))

def build_import_task(filename, destination):
    task = unreal.AssetImportTask()
    task.set_editor_property('automated', True)
    task.set_editor_property('filename', filename)
    task.set_editor_property('destination_path', destination)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('save', True)
    task.set_editor_property('options', build_import_options())
    return task

def build_import_options():
    options = unreal.FbxImportUI()
    # unreal.FbxImportUI
    options.set_editor_property('import_mesh', True)
    options.set_editor_property('import_textures', True)
    options.set_editor_property('import_materials', True)
    options.set_editor_property('import_as_skeletal', False)  # Static Mesh
    # unreal.FbxMeshImportData
    options.static_mesh_import_data.set_editor_property('import_translation', unreal.Vector(0.0, 0.0, 0.0))
    options.static_mesh_import_data.set_editor_property('import_rotation', unreal.Rotator(90.0, 0.0, 0.0))
    options.static_mesh_import_data.set_editor_property('import_uniform_scale', 500.0)
    # unreal.FbxStaticMeshImportData
    options.static_mesh_import_data.set_editor_property('combine_meshes', False)
    options.static_mesh_import_data.set_editor_property('generate_lightmap_u_vs', True)
    options.static_mesh_import_data.set_editor_property('auto_generate_collision', True)
    return options

if __name__ == '__main__':
    main()
