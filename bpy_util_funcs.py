# ----------------------------------------
#   BLENDER PYTHON UTILITY FUNCTIONS
#       Various utility scripts for the
#       Blender Python (bpy) module to
#       allow for ease of implementing
#       other various features!
# ----------------------------------------
"""Module with various utility scripts for the Blender Python (`bpy`) module to allow for ease of implementing other various features!"""

import bpy, random
from typing import cast

# ------------------------

# -------------------------------------------------------
# DETERMINE BLENDER VERSION TO HANDLE THINGS DIFFERENTLY
# Credit: REDxEYE
# -------------------------------------------------------

# Blender 3.6
def is_blender_3_6():
    return bpy.app.version >= (3, 6, 0)

# Blender 4.0
def is_blender_4():
    return bpy.app.version >= (4, 0, 0)

# Blender 4.1
def is_blender_4_1():
    return bpy.app.version >= (4, 1, 0)

# --------------------------------------------

# ------------------------------
# DATA CONVERSIONS / INVERSIONS
# ------------------------------

# UV Map inverter for import and export purposes.
def invert_uv_map(uv_set: tuple[float, float]) -> tuple[float, float]:
    """Invert the V component of a UV Map."""
    return (uv_set[0], 1 - uv_set[1])

# Reverse an n-point vector's values. Used for flipping faces' indices ordering.
def reverse_vector(vector: list | tuple) -> tuple:
    """Reverse an n-point vector's values."""
    return tuple(reversed(vector))

# Take the XYZ of a mesh's normals (or tangents) and divide them by 127. (Their maximum range)
def convert_vertex_normal(nx: int, ny: int, nz: int) -> tuple[float, float, float]:
    """Takes the XYZ of the normals and divides them by 127 to convert them from signed bytes to floats so Blender can parse them."""
    nx_conv = nx / 127
    ny_conv = ny / 127
    nz_conv = nz / 127

    return (nx_conv, ny_conv, nz_conv)

# Take the RGBA values of a mesh's vertex colors and divide them by 255.
def convert_vertex_color(r: int, g: int, b: int, a: int) -> list[float, float, float, float]:
    """Takes the RGBA of the vertex colors and divides them by 255 to convert them from signed bytes to floats so Blender can parse them."""
    r_conv = r / 255
    g_conv = g / 255
    b_conv = b / 255
    a_conv = a / 255

    return [r_conv, g_conv, b_conv, a_conv]

# Converter for single color channels from Linear to sRGB Color Space.
def linear_to_srgb(value: float) -> float:
    """Convert a single color channel from Linear to sRGB Color Space."""
    if value <= 0.0031308:
        return value * 12.92
    else:
        return 1.055 * pow(value, 1.0 / 2.4) - 0.055

# -------------------------------------------------------------------------------------------------------------------------------------------------

# ----------
# MATERIALS
# ----------

# Create a material that can be placed on an object. Credit: REDxEYE, Modified by Dodylectable
def create_material(material_name: str, assign_material_colors: bool = True) -> bpy.types.Material:
    """Create a material that can be placed on an object."""
    mat = bpy.data.materials.get(material_name, None)
    if mat is None:
        mat = bpy.data.materials.new(material_name)

        # Assign a random color on per material to help with distinguishing submeshes
        if assign_material_colors:
            mat.diffuse_color = [random.uniform(.4, 1) for (_) in range(3)] + [1.0]
    return mat

# Quickly add a material to a Blender object. Credit: REDxEYE
def add_material(mat: bpy.types.Material, model_obj: bpy.types.Object) -> int:
    """Quickly add a material to a Blender mesh object."""
    model_data: bpy.types.Mesh = cast(bpy.types.Mesh, model_obj.data)
    if model_data.materials.get(mat.name, None) is not None:
        return list(model_data.materials).index(mat)
    else:
        model_data.materials.append(mat)
        return len(model_data.materials) - 1

# ---------------------------------------------------------------------------------------------

# -------------------------
# VERTEX GROUPS NAME STUFF
# -------------------------

# Mass rename vertex groups' bone indexes to bone names.
def rename_vertex_groups_to_bone_names(obj: bpy.types.Object, bone_map: dict) -> None:
    """Mass rename vertex groups' bone indexes to bone names based on the skeleton's bone map."""

    for group in obj.vertex_groups:
        try:
            # Extract the bone index from the vertex group name (assumes "bone_<index>" format)
            bone_index = int(group.name.replace("bone_", ""))

            # Use the bone_map to find the corresponding bone name by its 'id'
            bone_name = bone_map.get(bone_index)

            if bone_name:
                # Rename the vertex group to the corresponding bone name
                group.name = bone_name
                print(f"Renamed vertex group '{group.name}' to '{bone_name}'")
            else:
                # If no matching bone name, print a warning
                print(f"No matching bone found for vertex group '{group.name}' with index {bone_index}")
        except ValueError:
            # Skip if the group name doesn't match the expected format
            print(f"Skipping vertex group '{group.name}' (non-standard format).")

# Just the function above but in reverse.
def rename_vertex_groups_to_bone_indexes(obj: bpy.types.Object, bone_map: dict) -> None:
    """Mass rename vertex groups' bone names to bone indexes based on the skeleton's bone map."""

    for group in obj.vertex_groups:
        # If the vertex group name matches a bone name in the bone_map
        if group.name in bone_map:
            bone_index = bone_map[group.name]  # Get the bone index from the bone_map
            group.name = f"bone_{bone_index}"  # Rename the vertex group to "bone_<index>"
            print(f"Renamed vertex group '{group.name}' to 'bone_{bone_index}'")

# Handle vertex group name switching! - This one renames indexes to names
def handle_vertex_group_rename_to_names() -> None:
    """Handles vertex group name switching to names."""
    objects = bpy.context.selected_objects

    for obj in objects:
        # Only apply to mesh objects
        if obj.type == 'MESH':

            # Get the attached armature, if there is one
            arm = get_attached_skeleton(obj)

            # If no armature is attached, raise an error
            if not arm:
                raise Exception("Model has no skeleton to draw bone names from!")

            # Get the armature's data
            arm_data = arm.data

            # Create the bone_map based on the bone['id'] attribute (use this index instead)
            bone_map = {bone['id']: bone.name for bone in arm_data.bones if 'id' in bone}

            # Debug print the bone map to verify it
            print(f"Bone map: {bone_map}")

            # Call the renaming function, passing the bone_map
            rename_vertex_groups_to_bone_names(obj, bone_map)

# And this one renames from names to indexes
def handle_vertex_group_rename_to_indexes() -> None:
    """Handles vertex group name switching back to indexes."""
    objects = bpy.context.selected_objects

    for obj in objects:
        # Only on meshes (for now)
        if obj.type == 'MESH':
            
            # Get the attached armature, if there is one
            arm = get_attached_skeleton(obj)

            # If there was no skeleton attached, throw an error
            if not arm:
                raise Exception("Model has no skeleton to draw bone names from!")
            
            # Get the armature's data
            arm_data = arm.data

            # Create a mapping of bone names to their respective indices (bone['id'])
            bone_map = {bone.name: bone['id'] for bone in arm_data.bones if 'id' in bone}

            # Debug print the bone map to verify it
            print(f"Bone map: {bone_map}")

            # Call the renaming function, passing the bone_map
            rename_vertex_groups_to_bone_indexes(obj, bone_map)

# Get an attached skeleton object.
def get_attached_skeleton(obj: bpy.types.Object) -> bpy.types.Object | None:
    """ Return the object instance of an attached skeleton to an object, if it exists. If no object was found or the type of the object is not a skeleton, returns `None`. """
    # The provided object is a skeleton already.
    if (obj.type == 'ARMATURE'):
        return obj
    
    # Check through the modifiers, see if there was a skeleton set.
    for (modifier) in (obj.modifiers):
        if (str(modifier.type) == 'ARMATURE') and (modifier.object):
            return modifier.object
        
    # Is this parented to an armature?
    if (obj.parent):
        if (obj.parent.type == 'ARMATURE'):
            return obj.parent
        
    # No armature found, bruh - Just return None in that case, we'll handle this ourselves
    return None

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
