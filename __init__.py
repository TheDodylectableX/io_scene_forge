# -----------------------------------------------------

# --------
# IMPORTS
# --------

import bpy, random
from typing import cast

from .readers import Reader
from .model_importer import import_model
# from .texture_importer import import_texture
# from .skeleton_importer import import_skeleton
from .bpy_util_funcs import *

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

# -----------------------------------------------------

# Plugin Information/Metadata
bl_info = {
    "name": "Forge Engine Modding Plugin",
    "description": "Import models from Harmonix' Forge Engine",
    "author": "Dodylectable",
    "blender": (4, 0, 0),
    "version": (1, 0, 1),
    "location": "File > Import-Export",
    "support": "COMMUNITY",
    "category": "Import-Export"
}

# -----------------------------------------------------

class ImportForgeMesh(Operator, ImportHelper):
    bl_idname = "import_forge.mesh"
    bl_label = "Import Forge Mesh (.forgemesh)"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".forgemesh"

    filter_glob: StringProperty(
        default="*.forgemesh",
        options={'HIDDEN'},
        maxlen=1024,
    ) # type: ignore

    custom_normals: BoolProperty(
        name="Custom Normals",
        description="Rather than using the original normals, re-calculate them when the meshes are created. (Looks smoother)",
        default=True,
    ) # type: ignore

    assign_material_colors: BoolProperty(
        name="Assign Material Colors",
        description="Assign random colors to the model's materials to help with distingushing submeshes",
        default=True,
    ) # type: ignore

    def execute(self, context):
       return import_model(self.filepath, self.custom_normals, self.assign_material_colors)
    
# class ImportForgeSkel(Operator, ImportHelper):
#     bl_idname = "import_forge.skel"
#     bl_label = "Import Forge Skeleton (.skel_pc/ps4)"
#     bl_options = {'REGISTER', 'UNDO'}

#     filename_ext = ".skel_pc"

#     filter_glob: StringProperty(
#         default="*.skel_pc;*.skel_ps4",
#         options={'HIDDEN'},
#         maxlen=1024,
#     ) # type: ignore

#     def execute(self, context):
#         return import_skeleton(context, self.filepath)

# class ImportForgeTex(Operator, ImportHelper):
#     bl_idname = "import_forge.tex"
#     bl_label = "Import Forge Texture (.bmp_pc/ps4 | .png_pc/ps4)"
#     bl_options = {'REGISTER', 'UNDO'}

#     filename_ext = ".bmp_pc"

#     filter_glob: StringProperty(
#         default="*.bmp_pc;*.bmp_ps4;*.png_pc;*.png_ps4",
#         options={'HIDDEN'},
#         maxlen=1024,
#     ) # type: ignore

#     def execute(self, context):
#         return import_texture(context, self.filepath)
        
def menu_func_import(self, context):
    self.layout.operator(ImportForgeMesh.bl_idname, text="Forge Mesh (.forgemesh)")
#    self.layout.operator(ImportForgeTex.bl_idname, text="Forge Texture (.bmp_pc/ps4 | .png_pc/ps4)")
#    self.layout.operator(ImportForgeSkel.bl_idname, text="Forge Skeleton (.skel_pc/ps4)")

def register():
    bpy.utils.register_class(ImportForgeMesh)
#    bpy.utils.register_class(ImportForgeTex)
#    bpy.utils.register_class(ImportForgeSkel)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportForgeMesh)
#    bpy.utils.unregister_class(ImportForgeTex)
#    bpy.utils.unregister_class(ImportForgeSkel)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    # --------------------------------------------------------------------------------------------------------