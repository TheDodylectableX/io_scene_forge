import bpy

from .readers import Reader
from .bpy_util_funcs import *

class ForgeMesh():
    """Forge model format class. Used for Rock Band 4 and VR models"""
    # Class constructor.
    def __init__(self, file_path: str, custom_normals: bool = False, random_material_colors: bool = True):
        """Forge model format class. Used for Rock Band 4 and VR models"""

        # Class init stuff
        super().__init__()

        # -------------------------------
        # -- CLASS MEMBERS --------------
        # -------------------------------

        # -- MODEL FILE
        self.model_file: str = file_path
        """The path to the model file."""

        # -- MASTER MESH DATA
        self.mesh_data: list[dict] = []
        """Master list of all mesh data."""

        # -- USE CUSTOM NORMALS
        self.use_custom_normals: bool = custom_normals
        """When the model is created, this will re-calculate the normals instead of using the original ones."""

        # -- ASSIGN MATERIAL COLORS
        self.assign_material_colors: bool = random_material_colors
        """This determines if the user wants random material colors on the model's generated materials or not."""

        # -------------------------------
        # -- PARSE THE DATA -------------
        # -------------------------------

        # Parse our model file here!
        self.parse_model_file()
        
    # Main model parser!
    def parse_model_file(self):
        """ Parse the model file itself! """
        print(f"Parsing model data...\n")

        # -------------------------------
        # Initialize the reader
        reader = Reader(open(self.model_file, "rb").read())
        # -------------------------------

        # -------------------------------
        # Data list dictionary
        master_data_list: list[dict] = []
        # -------------------------------

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
            raise ValueError("Unable to determine endianness for the model's data!")

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
            raise ValueError("Invalid vertex type for the model's data!")

        # -- COUNTS
        vertexCount = reader.uint32()
        print(f"Vertex Count: {vertexCount}")
        faceCount = reader.uint32()
        print(f"Face Count: {faceCount}")

        # -- BOOLEANS
        header_boolA = reader.ubyte()
        header_boolB = reader.ubyte()
        header_boolC = reader.ubyte()
        header_boolD = reader.ubyte()

        # -- FLAGS
        keepMeshData = reader.ubyte()
        print(f"Keep Mesh Data? {keepMeshData}")
        vertexUsageFlags = reader.uint32()
        print(f"Vertex Usage Flags: {vertexUsageFlags}")
        faceUsageFlags = reader.uint32()
        print(f"Face Usage Flags: {faceUsageFlags}")

        header_unk = reader.uint32()
        header_floats = reader.vec4f()    # Could be the model's bounding box?
        print(f"Header Floats: {header_floats}")

        # --------------------------------------------------------------------------------------------------------

        # ------------
        # VERTEX DATA
        # ------------

        vertices = []
        uv1 = []
        uv2 = []
        bone_indices = []
        bone_weights = []

        for (_) in (range(vertexCount)):
            vertices.append(reader.vec3f())

            vertex_pad = reader.ushort()
            
            vertex_data_A1 = reader.ubyte()
            vertex_data_A2 = reader.ubyte()
            vertex_data_A3 = reader.ubyte()
            vertex_data_A4 = reader.ubyte()

            vertex_pad2 = reader.ushort()

            vertex_data_B1 = reader.ubyte()
            vertex_data_B2 = reader.ubyte()
            vertex_data_B3 = reader.ubyte()
            vertex_data_B4 = reader.ubyte()

            vertex_pad3 = reader.int32()

            vertex_pad4 = reader.byte()
            vertex_pad5 = reader.byte()

            vertex_data_C1 = reader.ubyte()
            vertex_data_C2 = reader.ubyte()
            vertex_data_C3 = reader.ubyte()

            vertex_interesting_int = reader.int32()
            vertex_interesting_short = reader.short()

            vertex_pad4 = reader.ushort()
            vertex_pad5 = reader.ushort()
            vertex_pad4 = reader.byte()

            uv_primary = invert_uv_map(reader.vec2hf())
            uv_secondary = invert_uv_map(reader.vec2hf())

            uv1.append(uv_primary)
            uv2.append(uv_secondary)

            if vertexType == 2:      # ColorTex
                vertex_unk_ColorTex = reader.read_bytes(80 - 52)
            elif vertexType == 7:    # UnskinnedCompressed
                weights = [reader.ushort() for (_) in range(4)]
                ids = [reader.ubyte() for (_) in range(4)]

                bone_weights.append(weights)
                bone_indices.append(ids)

        # --------------------------------------------------------------------------------------------------------

        # ------
        # FACES
        # ------

        faces = []
        for (_) in (range(faceCount)):
            faces.append(reader.vec3i())

        # -------------------------------------------

        mesh_data_dict = {
            "magic": magic,
            "vertex_type": vertexType,
            "vertex_count": vertexCount,
            "face_count": faceCount,
            "vertices": vertices,
            "uv_map_1": uv1,
            "uv_map_2": uv2,
            "faces": faces,
            "bone_indices": bone_indices,
            "bone_weights": bone_weights,
        }

        master_data_list.append(mesh_data_dict)

        self.mesh_data = master_data_list

        print(f"\nMODEL PARSING COMPLETE!")

        # -------------------------------------------