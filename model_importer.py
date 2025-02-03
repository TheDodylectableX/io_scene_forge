# ------------------------------------------------
#   MODEL IMPORTER / BUILDER
#       Takes the parsed model data and
#       builds it into Blender's scene as objects
# ------------------------------------------------
"""
Takes the parsed model data and builds it into Blender's scene as objects.
"""

import os
import bpy
import math
import os
import struct

from .model_parser import ForgeMesh
from .bpy_util_funcs import *

from itertools import chain
from collections import defaultdict

# Import the model!
def import_model(file_path: str, use_custom_normals: bool = False, assign_material_colors: bool = True):
    """Import a model and construct it in Blender."""

    print(f"\nIMPORTING MODEL: {file_path}...\n")

    # Make sure the file exists!
    if not os.path.exists(file_path):
        print(f"Cannot import model; file not found at: {file_path}")
        return {'FINISHED'}

    model = ForgeMesh(file_path, use_custom_normals, assign_material_colors)
    
    # Extract data from the parsers
    model_data = {
        "filepath": model.model_file,
        "vertices": model.mesh_data[0]["vertices"],
        "faces": model.mesh_data[0]["faces"],
        # "normals": model.mesh_data[0]["normals"],
        "uv1": model.mesh_data[0]["uv_map_1"],
        "uv2": model.mesh_data[0]["uv_map_2"],
        "bone_indices": model.mesh_data[0].get("bone_indices", []),
        "bone_weights": model.mesh_data[0].get("bone_weights", []),
    }

    # Extract the filename for mesh naming
    filename = os.path.splitext(os.path.basename(file_path))[0]
    mesh_name = filename
    print(f"\nBuilding Mesh: {mesh_name}")

    # Create a new Blender mesh and object
    mesh = bpy.data.meshes.new(name=mesh_name)
    obj = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Rotate the model 90 degrees upwards
    obj.rotation_euler[0] += math.radians(90)
    print("Rotating the model by 90 degrees upwards")

    def add_weights(obj, bone_ids, bone_weights):
        """Add vertex group weights to the object."""
        print("Adding vertex weights...")
        vertex_groups = {}

        # Loop through vertices and assign weights
        for vertex_index, (vertex_bone_ids, vertex_bone_weights) in enumerate(zip(bone_ids, bone_weights)):
            for bone_index, weight in zip(vertex_bone_ids, vertex_bone_weights):
                # Ignore zero weights
                if weight == 0:
                    continue

                group_name = f"bone_{bone_index}"

                # Create the vertex group if it doesn't exist
                if group_name not in vertex_groups:
                    vertex_groups[group_name] = obj.vertex_groups.new(name=group_name)

                # Normalize weight
                normalized_weight = weight / 65535.0
                vertex_groups[group_name].add([vertex_index], normalized_weight, 'REPLACE')
    
    def add_model_materials(obj):
        """Add materials to the model."""
        # This implementation is quite simple, It just adds a material on the model.

        new_material = create_material(filename)

        add_material(new_material, obj)
    
    add_model_materials(obj)

    # First build the mesh with vertices, faces and normals - Credit: REDxEYE for fixed/improved code with support for other Blender versions
    # if use_custom_normals is False:
    #     mesh.from_pydata(model_data["vertices"], [], model_data["faces"])
    #     mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    #     if not is_blender_4_1():    # Blender 4.1 removed "use_auto_smooth" which was used on previous versions of the program.
    #         mesh.use_auto_smooth = True
    #     mesh.normals_split_custom_set_from_vertices(model_data["normals"])
    #     print("  Parsed vertices and faces with normals from the model.")
    # else:
    shade_flat = False
    mesh.from_pydata(model_data["vertices"], [], model_data["faces"], shade_flat)
    print("  Parsed vertices and faces with custom normals.")

    # Add the UV map
    uv_map_1 = model_data["uv1"]
    uv_map_2 = model_data["uv2"]
    if uv_map_1:
        uv_layer = mesh.uv_layers.new(name="UV_01")
        for loop in mesh.loops:
            uv_layer.data[loop.index].uv = uv_map_2[loop.vertex_index]
        print("Added UV Map #1.")
    if uv_map_2:
        uv_layer = mesh.uv_layers.new(name="UV_02")
        for loop in mesh.loops:
            uv_layer.data[loop.index].uv = uv_map_2[loop.vertex_index]
        print("Added UV Map #2.")

    # Add weights
    add_weights(obj, model_data["bone_indices"], model_data["bone_weights"])

    # Finalize the mesh
    mesh.calc_tangents()
    mesh.update()

    print("\nMODEL IMPORT COMPLETE!")
    return {'FINISHED'}

    # ----------------