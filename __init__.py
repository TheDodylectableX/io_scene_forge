# -----------------------------------------------------

# --------
# IMPORTS
# --------

import bpy, random
from typing import cast
import math
import os

from .readers import Reader
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
    "version": (0, 0, 1),
    "location": "File > Import-Export",
    "support": "COMMUNITY",
    "category": "Import-Export"
}

# -----------------------------------------------------

class ImportForgeMesh(Operator, ImportHelper):
    bl_idname = "import_forge.mesh"
    bl_label = "Forge Mesh (.forgemesh)"

    filename_ext = ".forgemesh"

    filter_glob: StringProperty(
        default="*.forgemesh",
        options={'HIDDEN'},
        maxlen=255,
    ) # type: ignore

    def execute(self, context):
        return import_forge(context, self.filepath)
    
class ImportForgeSkel(Operator, ImportHelper):
    bl_idname = "import_forge.skel"
    bl_label = "Forge Skeleton (.skel_pc/ps4)"

    filename_ext = ".skel_pc"

    filter_glob: StringProperty(
        default="*.skel_pc",
        options={'HIDDEN'},
        maxlen=255,
    ) # type: ignore

    def execute(self, context):
        return import_skel(context, self.filepath)

def menu_func_import(self, context):
    self.layout.operator(ImportForgeMesh.bl_idname, text="Forge Mesh (.forgemesh)")
#    self.layout.operator(ImportForgeSkel.bl_idname, text="Forge Skeleton (.skel_pc/ps4)")

def register():
    bpy.utils.register_class(ImportForgeMesh)
#    bpy.utils.register_class(ImportForgeSkel)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportForgeMesh)
#    bpy.utils.unregister_class(ImportForgeSkel)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    # --------------------------------------------------------------------------------------------------------

# -------
# MODELS
# -------

def import_forge(context, filepath):
    """Import a Forge Model."""

    print(f"\nIMPORTING MODEL: {filepath}...\n")

    reader = Reader(open(filepath, "rb").read())

    # -------
    # HEADER
    # -------

    magic = reader.read_string(8)
    print(f"Magic: {magic}")

    endianness = reader.uint32()
    if endianness == 1:
        reader.LE = True
        print("Endianness: Little")
    elif endianness == 0:
        reader.LE = False
        print("Endianness: Big")
    else:
        print("ERROR: Unable to determine endianness!")
        return 0

    version = reader.uint32()
    print(f"Model Version: {version}")

    vertexType = reader.uint32()
    if vertexType == 0:
        print("Vertex Type: Color")
    elif vertexType == 2:
        print("Vertex Type: ColorTex")
    elif vertexType == 3:
        print("Vertex Type: Unskinned")
    elif vertexType == 4:
        print("Vertex Type: Skinned")
    elif vertexType == 5:
        print("Vertex Type: Position Only")
    elif vertexType == 6:
        print("Vertex Type: Particle")
    elif vertexType == 7:
        print("Vertex Type: Unskinned Compressed")
    elif vertexType == 8:
        print("Vertex Type: Skinned Compressed")
    else:
        print("ERROR: Invalid vertex type!")
        return 0

    vertexCount = reader.uint32()
    print(f"Vertex Count: {vertexCount}")
    faceCount = reader.uint32()
    print(f"Face Count: {faceCount}")

    # - BOOLEANS
    header_boolA = reader.ubyte()
    header_boolB = reader.ubyte()
    header_boolC = reader.ubyte()
    header_boolD = reader.ubyte()

    keepMeshData = reader.ubyte()
    print(f"Keep Mesh Data? {keepMeshData}")
    vertexUsageFlags = reader.uint32()
    print(f"Vertex Usage Flags: {vertexUsageFlags}")
    faceUsageFlags = reader.uint32()
    print(f"Face Usage Flags: {faceUsageFlags}")

    header_unk = reader.uint32()
    header_floats = reader.vec4f() # Bounding Box XYZW?
    print(f"Header Floats: {header_floats}")

    # --------------------------------------------------------------------------------------------------------

    # ------------
    # VERTEX DATA
    # ------------

    vertices = []
    uv1 = []
    uv2 = []
    for (_) in (range(vertexCount)):
        vertices.append(reader.vec3f())

        vertex_unk_charA = reader.ubyte()
        vertex_unk_float = reader.float32()
        vertex_unk_charB = reader.ubyte()
        vertex_unk_hfloat = reader.hfloat16()

        vertex_unk_intA = reader.uint32()
        vertex_unk_intB = reader.uint32()
        vertex_unk_intC = reader.uint32()

        vertex_unk_hfloatA = reader.hfloat16()
        vertex_unk_hfloatB = reader.hfloat16()
        vertex_unk_hfloatC = reader.hfloat16()
        vertex_unk_hfloatD = reader.hfloat16()
        vertex_unk_hfloatE = reader.hfloat16()
        vertex_unk_hfloatF = reader.hfloat16()

        uvA = reader.vec2hf()
        uvA = (uvA[0], 1 - uvA[1])
        uvB = reader.vec2hf()
        uvB = (uvB[0], 1 - uvB[1])

        uv1.append(uvA)
        uv2.append(uvB)

        if vertexType == 2:
            vertex_unk_colortex = reader.read_bytes(80 - 52)
        elif vertexType == 7:
            vertex_unk_unskinnedcompressedA = reader.ushort()
            vertex_unk_unskinnedcompressedB = reader.ushort()
            vertex_unk_unskinnedcompressedC = reader.uint32()
            vertex_unk_unskinnedcompressedD = reader.uint32()
        else:
            print("Invalid vertex data!")
            return 0

    # --------------------------------------------------------------------------------------------------------

    # ------
    # FACES
    # ------

    faces = []
    for (_) in (range(faceCount)):
        i1, i2, i3 = reader.vec3i()
        faces.append([i3, i2, i1]) # Invert the order so it renders properly

    # --------------------------------------------------------------------------------------------------------

    # ----------------
    # BUILD THE MODEL
    # ----------------

    print("\nBUILDING MODEL...")

    filename = os.path.splitext(os.path.basename(filepath))[0]

    mesh_name = filename

    mesh = bpy.data.meshes.new(name = mesh_name)
    obj = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Rotate the model 90 degrees upwards
    obj.rotation_euler[0] += math.radians(90)

    # Calculate normals since we aren't parsing the model's
    shade_flat = False

    # Assemble the model
    mesh.from_pydata(vertices, [], faces, shade_flat)

    # Parse the UVs
    uv_layer_1 = mesh.uv_layers.new(name="UV_01")
    uv_layer_2 = mesh.uv_layers.new(name="UV_02")

    for loop in mesh.loops:
        uvA = uv1[loop.vertex_index]
        uv_layer_1.data[loop.index].uv = (uvA[0], uvA[1])

        uvB = uv2[loop.vertex_index]
        uv_layer_2.data[loop.index].uv = (uvB[0], uvB[1])

    # Calculate tangents since we aren't parsing the model's
    mesh.calc_tangents()

    # Update the model in the scene
    mesh.update()

    print("\nMODEL CREATED!")

    print("\nIMPORT COMPLETE!\n")

    return {'FINISHED'}

    # --------------------------------------------------------------------------------------------------------

# ----------------------
# SKELETONS
# Obviously incomplete
# ----------------------


def import_skel(context, filepath):
    """Import a Forge Skeleton."""

    print(f"\nIMPORTING SKELETON {filepath}...\n")

    reader = Reader(open(filepath, "rb").read())

    version = reader.uint32()
    print(f"Skeleton Version: {version}")

    source_file_name_length = reader.uint32()
    source_file_name = reader.read_string(source_file_name_length)
    print(f"Source File Name: {source_file_name}")

    return {'FINISHED'}

    # --------------------------------------------------------------------------------------------------------