"""
common_kp.py file

File limitations
blender compatability tools
"""

# from ast import excepthandler
# from msilib.schema import Class
# from typing import Tuple
import bpy
import struct
from timeit import default_timer as timer
# import bmesh
from mathutils import Vector
from collections import namedtuple
from math import exp, radians
from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty,
    CollectionProperty,
    BoolProperty
)


# BL_VER = (1, 2, 7)

# store data from md2 file in object(used for smooth tool)
DATA_V_BYTE = "frame_vert_grid_idx"
DATA_F_SCALE = "frame_scale"
DATA_F_COUNT = "num_frames"
DATA_V_COUNT = "num_vertex"

SK_MODE_VERT = "SK_VERTEX"
SK_MODE_REL = "SK_REL"
SK_MODE_ABS = "SK_ABS"

UI_OBJ_SINGLE = "MDX_OBJ_NONE"
UI_OBJ_SKINS = "MDX_OBJ_SKINS"
UI_OBJ_OBJECTS = "MDX_OBJ_OBJECTS"

MDX5_MAX_TRIANGLES = 8192
MDX5_MAX_VERTS = 4096
MDX5_VERSION = 5

MDX_IDENT = b"IDPX"
MDX_VERSION = 4

MD2_IDENT = b"IDP2"
MD2_VERSION = 8

MD2_MAX_TRIANGLES = 4096
MD2_MAX_VERTS = 2048
MD2_MAX_FRAMES = 1024  # 512 - 1024 is an UFO:AI extension.
MD2_MAX_SKINS = 32
MD2_MAX_SKINNAME = 64
MD2_VN = (
    (-0.525731, 0.000000, 0.850651),
    (-0.442863, 0.238856, 0.864188),
    (-0.295242, 0.000000, 0.955423),
    (-0.309017, 0.500000, 0.809017),
    (-0.162460, 0.262866, 0.951056),
    (0.000000, 0.000000, 1.000000),
    (0.000000, 0.850651, 0.525731),
    (-0.147621, 0.716567, 0.681718),
    (0.147621, 0.716567, 0.681718),
    (0.000000, 0.525731, 0.850651),
    (0.309017, 0.500000, 0.809017),
    (0.525731, 0.000000, 0.850651),
    (0.295242, 0.000000, 0.955423),
    (0.442863, 0.238856, 0.864188),
    (0.162460, 0.262866, 0.951056),
    (-0.681718, 0.147621, 0.716567),
    (-0.809017, 0.309017, 0.500000),
    (-0.587785, 0.425325, 0.688191),
    (-0.850651, 0.525731, 0.000000),
    (-0.864188, 0.442863, 0.238856),
    (-0.716567, 0.681718, 0.147621),
    (-0.688191, 0.587785, 0.425325),
    (-0.500000, 0.809017, 0.309017),
    (-0.238856, 0.864188, 0.442863),
    (-0.425325, 0.688191, 0.587785),
    (-0.716567, 0.681718, -0.147621),
    (-0.500000, 0.809017, -0.309017),
    (-0.525731, 0.850651, 0.000000),
    (0.000000, 0.850651, -0.525731),
    (-0.238856, 0.864188, -0.442863),
    (0.000000, 0.955423, -0.295242),
    (-0.262866, 0.951056, -0.162460),
    (0.000000, 1.000000, 0.000000),
    (0.000000, 0.955423, 0.295242),
    (-0.262866, 0.951056, 0.162460),
    (0.238856, 0.864188, 0.442863),
    (0.262866, 0.951056, 0.162460),
    (0.500000, 0.809017, 0.309017),
    (0.238856, 0.864188, -0.442863),
    (0.262866, 0.951056, -0.162460),
    (0.500000, 0.809017, -0.309017),
    (0.850651, 0.525731, 0.000000),
    (0.716567, 0.681718, 0.147621),
    (0.716567, 0.681718, -0.147621),
    (0.525731, 0.850651, 0.000000),
    (0.425325, 0.688191, 0.587785),
    (0.864188, 0.442863, 0.238856),
    (0.688191, 0.587785, 0.425325),
    (0.809017, 0.309017, 0.500000),
    (0.681718, 0.147621, 0.716567),
    (0.587785, 0.425325, 0.688191),
    (0.955423, 0.295242, 0.000000),
    (1.000000, 0.000000, 0.000000),
    (0.951056, 0.162460, 0.262866),
    (0.850651, -0.525731, 0.000000),
    (0.955423, -0.295242, 0.000000),
    (0.864188, -0.442863, 0.238856),
    (0.951056, -0.162460, 0.262866),
    (0.809017, -0.309017, 0.500000),
    (0.681718, -0.147621, 0.716567),
    (0.850651, 0.000000, 0.525731),
    (0.864188, 0.442863, -0.238856),
    (0.809017, 0.309017, -0.500000),
    (0.951056, 0.162460, -0.262866),
    (0.525731, 0.000000, -0.850651),
    (0.681718, 0.147621, -0.716567),
    (0.681718, -0.147621, -0.716567),
    (0.850651, 0.000000, -0.525731),
    (0.809017, -0.309017, -0.500000),
    (0.864188, -0.442863, -0.238856),
    (0.951056, -0.162460, -0.262866),
    (0.147621, 0.716567, -0.681718),
    (0.309017, 0.500000, -0.809017),
    (0.425325, 0.688191, -0.587785),
    (0.442863, 0.238856, -0.864188),
    (0.587785, 0.425325, -0.688191),
    (0.688191, 0.587785, -0.425325),
    (-0.147621, 0.716567, -0.681718),
    (-0.309017, 0.500000, -0.809017),
    (0.000000, 0.525731, -0.850651),
    (-0.525731, 0.000000, -0.850651),
    (-0.442863, 0.238856, -0.864188),
    (-0.295242, 0.000000, -0.955423),
    (-0.162460, 0.262866, -0.951056),
    (0.000000, 0.000000, -1.000000),
    (0.295242, 0.000000, -0.955423),
    (0.162460, 0.262866, -0.951056),
    (-0.442863, -0.238856, -0.864188),
    (-0.309017, -0.500000, -0.809017),
    (-0.162460, -0.262866, -0.951056),
    (0.000000, -0.850651, -0.525731),
    (-0.147621, -0.716567, -0.681718),
    (0.147621, -0.716567, -0.681718),
    (0.000000, -0.525731, -0.850651),
    (0.309017, -0.500000, -0.809017),
    (0.442863, -0.238856, -0.864188),
    (0.162460, -0.262866, -0.951056),
    (0.238856, -0.864188, -0.442863),
    (0.500000, -0.809017, -0.309017),
    (0.425325, -0.688191, -0.587785),
    (0.716567, -0.681718, -0.147621),
    (0.688191, -0.587785, -0.425325),
    (0.587785, -0.425325, -0.688191),
    (0.000000, -0.955423, -0.295242),
    (0.000000, -1.000000, 0.000000),
    (0.262866, -0.951056, -0.162460),
    (0.000000, -0.850651, 0.525731),
    (0.000000, -0.955423, 0.295242),
    (0.238856, -0.864188, 0.442863),
    (0.262866, -0.951056, 0.162460),
    (0.500000, -0.809017, 0.309017),
    (0.716567, -0.681718, 0.147621),
    (0.525731, -0.850651, 0.000000),
    (-0.238856, -0.864188, -0.442863),
    (-0.500000, -0.809017, -0.309017),
    (-0.262866, -0.951056, -0.162460),
    (-0.850651, -0.525731, 0.000000),
    (-0.716567, -0.681718, -0.147621),
    (-0.716567, -0.681718, 0.147621),
    (-0.525731, -0.850651, 0.000000),
    (-0.500000, -0.809017, 0.309017),
    (-0.238856, -0.864188, 0.442863),
    (-0.262866, -0.951056, 0.162460),
    (-0.864188, -0.442863, 0.238856),
    (-0.809017, -0.309017, 0.500000),
    (-0.688191, -0.587785, 0.425325),
    (-0.681718, -0.147621, 0.716567),
    (-0.442863, -0.238856, 0.864188),
    (-0.587785, -0.425325, 0.688191),
    (-0.309017, -0.500000, 0.809017),
    (-0.147621, -0.716567, 0.681718),
    (-0.425325, -0.688191, 0.587785),
    (-0.162460, -0.262866, 0.951056),
    (0.442863, -0.238856, 0.864188),
    (0.162460, -0.262866, 0.951056),
    (0.309017, -0.500000, 0.809017),
    (0.147621, -0.716567, 0.681718),
    (0.000000, -0.525731, 0.850651),
    (0.425325, -0.688191, 0.587785),
    (0.587785, -0.425325, 0.688191),
    (0.688191, -0.587785, 0.425325),
    (-0.955423, 0.295242, 0.000000),
    (-0.951056, 0.162460, 0.262866),
    (-1.000000, 0.000000, 0.000000),
    (-0.850651, 0.000000, 0.525731),
    (-0.955423, -0.295242, 0.000000),
    (-0.951056, -0.162460, 0.262866),
    (-0.864188, 0.442863, -0.238856),
    (-0.951056, 0.162460, -0.262866),
    (-0.809017, 0.309017, -0.500000),
    (-0.864188, -0.442863, -0.238856),
    (-0.951056, -0.162460, -0.262866),
    (-0.809017, -0.309017, -0.500000),
    (-0.681718, 0.147621, -0.716567),
    (-0.681718, -0.147621, -0.716567),
    (-0.850651, 0.000000, -0.525731),
    (-0.688191, 0.587785, -0.425325),
    (-0.587785, 0.425325, -0.688191),
    (-0.425325, 0.688191, -0.587785),
    (-0.425325, -0.688191, -0.587785),
    (-0.587785, -0.425325, -0.688191),
    (-0.688191, -0.587785, -0.425325)
)


class mdx_hdr:
    """ mdx header """
    def __init__(self, inFile):
        buff = inFile.read(struct.calcsize("<23i"))
        data = struct.unpack("<23i", buff)

        if data[0] != struct.unpack('<I', MDX_IDENT)[0]:
            raise RuntimeError("Invalid MDX file (id)")
        if data[1] != MDX_VERSION:
            raise RuntimeError("Invalid MDX file(version)")

        self.id = data[0]
        self.version = data[1]
        self.skinWidth = max(1, data[2])
        self.skinHeight = max(1, data[3])
        self.framesize = data[4]
        self.numSkins = data[5]
        self.numVerts = data[6]
        self.numTris = data[7]
        self.numGLCmds = data[8]
        self.numFrames = data[9]
        self.numSfxDefines = data[10]
        self.numSfxEntries = data[11]
        self.numSubObjects = data[12]
        self.ofsSkins = data[13]
        self.ofsTris = data[14]
        self.ofsFrames = data[15]
        self.ofsGLCmds = data[16]
        self.ofsGLCmds_end = data[17]  # dupe. get lump size
        # not used
        self.offsetVertexInfo = data[17]
        self.offsetSfxDefines = data[18]
        self.offsetSfxEntries = data[19]
        self.offsetBBoxFrames = data[20]
        self.offsetDummyEnd = data[21]
        self.offsetEnd = data[22]


class md2_hdr:
    """ md2 header """

    def __init__(self, inFile):
        buff = inFile.read(struct.calcsize("<17i"))
        data = struct.unpack("<17i", buff)

        if data[0] != struct.unpack('<I', MD2_IDENT)[0]:
            raise RuntimeError("Invalid MD2 file (id)")
        if data[1] != MD2_VERSION:
            raise RuntimeError("Invalid MD2 file(version)")

        # fill header details
        self.id = data[0]
        self.version = data[1]
        self.skinWidth = max(1, data[2])
        self.skinHeight = max(1, data[3])
        self.framesize = data[4]
        self.numSkins = data[5]
        self.numVerts = data[6]
        self.numUV = data[7]
        self.numTris = data[8]
        self.numGLCmds = data[9]
        self.numFrames = data[10]
        self.ofsSkins = data[11]
        self.ofsUV = data[12]
        self.ofsTris = data[13]
        self.ofsFrames = data[14]
        self.ofsGLCmds = data[15]
        self.ofsGLCmds_end = data[16]  # dupe. get lump size
        # not used
        self.offsetEnd = data[16]


class mdx_hdr_export:
    ''' _ '''
    _fields = (
        "ident","version","skinWidth","skinHeight","frameSize","numSkins","numVerts",
        "numTris","numGLCmds","numFrames","numSfxDefines","numSfxEntries","numSubObjects",
        "ofsSkins","ofsTris","ofsFrames","ofsGLCmds","ofsVertexInfo","ofsSfxDefines",
        "ofsSfxEntries","ofsBBoxFrames","ofsDummyEnd","ofsEnd")

    def calculateHitBox_fn(self):
        ''' _ '''

    def get_numUV(self):
        ''' _ '''

    def pack_header(self):
        # Collect all attributes specified for packing
        values = [getattr(self, f, 0) for f in self._fields]
        return struct.pack("<23i", *values)

    def __init__(self, mdl, cfg):
        self.ident = struct.unpack('<I', MDX_IDENT)[0] # 1481655369
        self.version = 4
        self.skinWidth = mdl.skinWidth
        self.skinHeight = mdl.skinHeight
        self.frameSize = mdl.frameSize
        self.numSkins = mdl.numSkins
        self.numVerts = mdl.numVerts
        self.numTris = mdl.numTris
        self.numGLCmds = mdl.numGLCmds
        self.numFrames = mdl.numFrames
        self.numSfxDefines = 0
        self.numSfxEntries = 0
        self.numSubObjects = mdl.numSubObjects
        # self.numSubObjects = 1 if not cfg.ui_opt_use_hitbox else len(mdl.mdl_objs)
        # offsets
        self.ofsSkins = struct.calcsize("<23i")
        self.ofsTris = self.ofsSkins + struct.calcsize("<64s") * self.numSkins
        self.ofsFrames = self.ofsTris + struct.calcsize("<6H") * self.numTris
        self.ofsGLCmds = self.ofsFrames + self.frameSize * self.numFrames
        self.ofsVertexInfo = self.ofsGLCmds + struct.calcsize("<i") * self.numGLCmds
        self.ofsSfxDefines = self.ofsVertexInfo + struct.calcsize("<i") * (self.numVerts)
        self.ofsSfxEntries = self.ofsSfxDefines
        self.ofsBBoxFrames = self.ofsSfxEntries
        self.ofsDummyEnd = self.ofsBBoxFrames + \
            struct.calcsize("<6i") * (self.numFrames * self.numSubObjects)
        self.ofsEnd = self.ofsDummyEnd


class md2_hdr_export:
    ''' _ '''
    _fields = (
        "ident","version","skinWidth","skinHeight","frameSize",
        "numSkins","numVerts","numUV","numTris","numGLCmds","numFrames",
        "ofsSkins","ofsUV","ofsTris","ofsFrames","ofsGLCmds","ofsEnd")

    def pack_header(self):
        values = [getattr(self, f, 0) for f in self._fields]
        return struct.pack("<17i", *values)

    def __init__(self, mdl, numUV):
        self.ident = struct.unpack('<I', MD2_IDENT)[0] #844121161
        self.version = 8
        self.skinWidth = mdl.skinWidth
        self.skinHeight = mdl.skinHeight
        self.frameSize = mdl.frameSize
        self.numSkins = mdl.numSkins
        self.numVerts = mdl.numVerts
        self.numUV = numUV # md2 only
        self.numTris = mdl.numTris
        self.numGLCmds = mdl.numGLCmds
        self.numFrames = mdl.numFrames

        # offsets
        self.ofsSkins = struct.calcsize("<17i")
        self.ofsUV = self.ofsSkins + struct.calcsize("<64s") * self.numSkins
        self.ofsTris = self.ofsUV + struct.calcsize("<2h") * self.numUV
        self.ofsFrames = self.ofsTris + struct.calcsize("<6H") * self.numTris
        self.ofsGLCmds = self.ofsFrames + self.frameSize * self.numFrames
        self.ofsEnd = self.ofsGLCmds + struct.calcsize("<i") * self.numGLCmds


class mdl_export:
    ''' _ '''
    def __init__(self, objs, isPlayer: bool, meshName: str):
        self.valid = True # set false on fail
        self.obj_array = []
        self.frMeData = []
        self.frMeData_BBox = []
        self.hitbox = []  # mdx hitbox
        # self.vertCounter = []
        self.glCmdList = []
        self.vNormData = []
        self.vertices = -1
        self.faces = 0
        self.status = ("", "")

        self.numFrames = 0

        self.skinWidth = 0
        self.skinHeight = 0
        self.skins = []
        self.numSkins = 0
        self.skin_print = ""

        self.frameNames = []

        self.bbox_min = []
        self.bbox_max = []

        self.vNormData = []
        self.numVerts = 0
        self.numTris = 0

        self.numGLCmds = 0
        self.frameSize = 0

        self.numSubObjects = 0 #mdx

        self.hdr = None #mdl_hdr_export(None)

        self.save_name = meshName
        self.isPlayer = isPlayer
        if isPlayer:
            self.mdl_objs = []
            self.mdl_objs_player = objs
            for o in objs:
                if o.name[:len(meshName)].lower() == meshName:
                    self.mdl_objs.append(o)
        else:
            self.mdl_objs = objs
            self.mdl_objs_player = []
            if len(objs) == 0:
                self.valid = False


class export_cfg:
    ''' _ '''
    def __init__(self, fpath_, fname_, fext_, isMdx):
        self.f_path = fpath_
        self.f_name = fname_
        self.f_ext = fext_  # includes dot (".mdx")
        self.isMdx = bool(isMdx)

        ui_export_ = bpy.context.window_manager.kp_export_
        mode = ui_export_.ui_opt_export_mode

        self.ui_opt_animated = ui_export_.ui_opt_animated
        self.ui_opt_exp_selected = mode == "EXP_MERGED"
        self.ui_opt_is_player = mode in ("MDX_PLAYER_ONLY", "EXP_PLAYER_WEPS")
        self.ui_opt_exp_weps = mode in ("EXP_PLAYER_WEPS", "EXP_ADDON_ONLY")
        self.ui_opt_exp_all = mode == "EXP_ALL_ITEMS"
        self.ui_opt_use_hitbox = ui_export_.ui_opt_use_hitbox
        self.ui_opt_tex_name = ui_export_.ui_opt_tex_name
        self.ui_opt_fr_start = ui_export_.ui_opt_fr_start
        self.ui_opt_fr_end = ui_export_.ui_opt_fr_end
        self.ui_opt_apply_modify = True  # ui_export_.ui_opt_apply_modify
        self.ui_opt_is_hd = ui_export_.ui_opt_is_hd
        self.ui_opt_cust_vn = ui_export_.ui_opt_cust_vn

        # obj/hitbox mode. use dropdown
        self.ui_opt_mat_hitbox = False  # UI_OBJ_SINGLE
        self.ui_opt_use_hitbox = False
        if ui_export_.ui_opt_export_mdx_obj == UI_OBJ_OBJECTS:
            self.ui_opt_use_hitbox = True
        elif ui_export_.ui_opt_export_mdx_obj == UI_OBJ_SKINS:
            self.ui_opt_use_hitbox = True
            self.ui_opt_mat_hitbox = True

        if self.ui_opt_apply_modify is False:
            self.ui_opt_cust_vn = False


MeshData = namedtuple("MeshData", [
    "md_idc_vert",
    "md_idc_uv",
    "md_xyz_vert",
    "md_xyz_norm",
    "md_xy_uv",
    "md_face_count",
    "md_vert_count",
    "md_uv_count",
    "md_face_mat",
    "md_mat_count"
])


def string_to_bytes(s: str, count) -> bytes:
    """ null terminate string """
    b = s.encode('latin-1')
    if len(b) >= count:
        b = b[:count -1]  # truncate, leave room for null
    return b.ljust(count, b'\0')  # pad with nulls to fill 64

def string_from_bytes(src: bytes) -> str:
    """ search first hex null """
    return src.split(b'\x00', 1)[0].decode('latin-1')


def forceMinMaxRange(value, min_, max_):
    ''' _ '''
    if value < min_:
        return min_
    if value > max_:
        return max_
    return value


def check_version(major, minor, _):
    """
    check_version(2, 80, 0) < 0:
    source 3.2.1 magic_uv/utils/compatibility.py
    Check blender version
    return:
    0: same version
    1: newer version
    -1:older version
    """
    ver_id = tuple(bpy.app.version)
    cur_major, cur_minor = ver_id[0], ver_id[1]

    # matching major version
    if cur_major == major:
        if cur_minor == minor:  # minor version identical
            return 0
        if cur_minor > minor:  # minor version newer
            return 1
    # newer major ver
    if cur_major > major:
        return 1
    # older version
    return -1


def set_ui_panel_string():
    """
    bl_region_type = set_ui_panel_string()
    old blender used differnt name for panel location
    2.80: <"UI">
    2.79: <"TOOLS">
    """
    if check_version(2, 80, 0) < 0:
        return "TOOLS"
    return "UI"


class KINGPIN_FileSelect_md2_Params:
    """ common file select dialog paramaters
        2.79/2.80
    """
    filter_glob = StringProperty(
        default="*.md2;*.mdx",
        options={"HIDDEN"}
    )
    files = CollectionProperty(
        type=PropertyGroup
    )
    filepath = StringProperty(
        maxlen=1024,
        subtype="FILE_PATH",
        options={"HIDDEN", "SKIP_SAVE"}
    )


class KINGPIN_FileSelect_q3cfg_Params:
    """ common file select dialog paramaters
        2.79/2.80
    """
    filter_glob = StringProperty(
        default="*.cfg",
        options={"HIDDEN"},  # TODO
    )
    files = CollectionProperty(
        type=PropertyGroup
    )
    filepath = StringProperty(
        maxlen=1024,
        subtype="FILE_NAME",  # "FILE_PATH",
        options={"HIDDEN", "SKIP_SAVE"}
    )


class KINGPIN_FileSelect_folder_Params:
    """ common folder select dialog paramaters
        2.79/2.80
    """
    directory = StringProperty(
        name="Outdir Path",
        description="Folder to save models."
    )  # subtype="DIR_PATH"
    filter_folder = BoolProperty(
        default=True,
        options={"HIDDEN"}
    )


class KINGPIN_FileSelect_file_Params_tga:
    """ common folder select dialog paramaters
        2.79/2.80
    """
    directory = StringProperty(
        name="Outdir Path",
        description="Folder to save models."
    )  # subtype="DIR_PATH"
    filter_folder = BoolProperty(
        default=False,
        options={"HIDDEN"}
    )
    filter_glob = StringProperty(
        default="*.tga",
        options={'HIDDEN'},
        maxlen=255,
    )


class TexturePacker:
    """ Manages 2D space allocation for the texture atlas """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Track available spaces as [x, y, width, height]
        self.free_rects = [[0, 0, width, height]]

    def pack(self, img_w, img_h):
        """ Finds the best empty slot, places the image, and splits the remaining space """
        for i, rect in enumerate(self.free_rects):
            rx, ry, rw, rh = rect

            # Check if the texture fits in this free slot
            if img_w <= rw and img_h <= rh:
                self.free_rects.pop(i)

                # Guillotine split method
                rem_w = rw - img_w
                rem_h = rh - img_h

                if rem_w > 0: # Create a free column to the right
                    self.free_rects.append([rx + img_w, ry, rem_w, img_h])
                if rem_h > 0: # Create a free row above
                    self.free_rects.append([rx, ry + img_h, rw, rem_h])

                return rx, ry

        return None # Out of space


#########
# print #
def printStart_fn():
    """
    get current time
    start_time = printStart_fn()
    """
    return timer()


def printProgress_fn(current, max_count, prefix):
    """ Display the progress status in console
    input: <frame><total><prefix>  """
    progress = float(current / max_count) * 100
    print("%-25s %6.2f%%\r" % (prefix + ":", progress), end="")


def printDone_fn(st_time, prefix):
    """ Display the progress status in console """
    print("%-25s 100%% Done. (%.2f sec)" % (prefix + ":", timer() - st_time))


def get_preferences(context=None):
    """
    2.80: <context.preferences>
    2.79: <context.user_preferences>
    Multi version compatibility for getting preferences
    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-7
    """
    if not context:
        context = bpy.context
    if hasattr(context, "user_preferences"):  # B2.7
        return context.user_preferences
    if hasattr(context, "preferences"):   # B2.8
        return context.preferences

    raise ValueError("Could not fetch user preferences")


def get_addon_preferences():
    """
    2.80: <context.preferences.addons.get>
    2.79: <context.user_preferences.addons.get>
    Multi version compatibility for getting preferences
    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-7
    """
    context = bpy.context
    prefs = None
    if hasattr(context, "user_preferences"):  # B2.7
        prefs = context.user_preferences.addons.get(__package__, None)
    elif hasattr(context, "preferences"):
        prefs = context.preferences.addons.get(__package__, None)

    if prefs and prefs.preferences:
        return prefs.preferences
    raise ValueError("Could not fetch user addon preferences")


# todo fix this
def get_collection(context):
    """
    2.80: <context.collection.objects>
    2.79: <context.scene.groups>
    """
    if hasattr(context, "collection"):
        return context.collection.objects  # B2.8
    return context.scene.groups


# ui input for colections
def get_ui_collection(context):
    """
    2.80: <bpy.types.Collection>
    2.79: <bpy.types.Scene>
    """
    if hasattr(context, "Collection"):
        # https://docs.blender.org/api/current/bpy.types.Collection.html#bpy.types.Collection
        return bpy.types.Collection
    # else:
    # return bpy.types.Group
    # https://docs.blender.org/api/blender_python_api_current/bpy.types.Group.html
    return bpy.types.Scene
    # https://docs.blender.org/api/blender_python_api_current/bpy.types.Scene.html


def get_objects_all(context):
    """
    2.80: <context.view_layer.objects>
    2.79: <context.scene.objects>
    """
    if hasattr(context, "view_layer"):
        return context.view_layer.objects  # B2.8
    # else:
    return context.scene.objects


def get_objects_active(context):
    """
    2.80: <context.view_layer.objects.active>
    2.79: <context.scene.objects.active>
    """
    if hasattr(context, "view_layer"):
        return context.view_layer.objects.active  # B2.8
    return context.scene.objects.active


def set_objects_active(context, obj):
    """
    2.80: <context.view_layer.objects.active>
    2.79: <context.scene.objects.active>
    """
    if hasattr(context, "view_layer"):
        context.view_layer.objects.active = obj  # B2.8
    else:
        context.scene.objects.active = obj


def get_objects_selected(context):
    """
    2.80: <context.view_layer.objects.selected>
    2.79: <context.selected_objects>
    """
    # .selected:  # bpy.data.objects:
    if hasattr(context, "view_layer"):
        return context.view_layer.objects.selected  # B2.8
    return context.selected_objects


def get_layers(context):
    """
    2.80: <context.view_layer>
    2.79: <context.scene>
    """
    if hasattr(context, "view_layer"):
        return context.view_layer  # B2.8
    return context.scene


# TODO rename to scene...
def set_layer_update(context):
    """
    2.80: <context.view_layer>
    2.79: <context.scene>
    """
    if hasattr(context, "view_layer"):
        context.view_layer.update()  # B2.8
    else:
        context.scene.update()


def get_menu_import():
    """
    0: <TOPBAR_MT_file_import>
    1: <INFO_MT_file_import>
     """
    if hasattr(bpy.types, "TOPBAR_MT_file_import"):
        return bpy.types.TOPBAR_MT_file_import
    elif hasattr(bpy.types, "INFO_MT_file_import"):
        return bpy.types.INFO_MT_file_import
    # failed
    raise ValueError("Could not fetch menu")


def get_menu_export():
    """
    2.80: <>
    2.79: <>
    """
    if hasattr(bpy.types, "TOPBAR_MT_file_export"):
        return bpy.types.TOPBAR_MT_file_export
    elif hasattr(bpy.types, "INFO_MT_file_export"):
        return bpy.types.INFO_MT_file_export
    else:
        raise ValueError("Could not fetch menu")


def get_groups():
    """
    2.80: <bpy.data.collections.get("MyGroup")>
    2.79: <bpy.data.groups.get("MyGroup")>
    """
    if hasattr(bpy.data, "collections"):
        return bpy.data.collections.get("MyGroup")
    # else:
    return bpy.data.groups.get("MyGroup")


def get_uv_data_new(me_data, uv_name=""):
    """
    2.80: <me_data.uv_layers.new()>
    2.79: <me_data.uv_textures.new()>
    """
    uv_type = 0
    uv_data = None
    if hasattr(me_data, "uv_textures"):
        # tessface_uv_textures
        uv_data = me_data.uv_textures.new(name=uv_name)
        me_data.uv_textures.active = uv_data
    else: # B2.8
        uv_type = 1
        uv_data = me_data.uv_layers.new(name=uv_name)
        me_data.uv_layers.active = uv_data
    return (uv_type, uv_data)


def get_uv_data(context):
    """
    2.80: <context.uv_textures>
    2.79: <context.uv_layers>
    """
    if hasattr(context, "uv_textures"):
        return context.uv_textures
    # else:
    return context.uv_layers  # B2.8


def get_hide(context):
    """
    2.80: <context.hide_viewport>
    2.79: <context.hide>
    """
    if hasattr(context, "hide_viewport"):
        return context.hide_viewport  # B2.8
    return context.hide


def set_empty_draw_type(context, e_type):
    """
    2.80: <context.empty_draw_type>
    2.79: <context.empty_display_type>
     """
    if hasattr(context, "empty_draw_type"):
        context.empty_draw_type = e_type  # B3.0
    else:
        context.empty_display_type = e_type


def set_mode_get_obj(context):
    """set object mode=OBJECT, get active.object and selected.objects
    : return(
        : current object mode,
        : active object
        : selected objects (array)
    )
    """
    edit_mode = context.mode
    if edit_mode == "EDIT_MESH":
        edit_mode = "EDIT"
    # TODO add extra modes

    act_obj = get_objects_active(context)
    if edit_mode != "OBJECT":
        sel_obj = [act_obj]
        bpy.ops.object.mode_set(mode="OBJECT")
    else:
        # bpy.context.selected_objects
        sel_obj = get_objects_selected(context)[:]

    return edit_mode, act_obj, sel_obj


def is_selected_mesh(self, objs):
    """ selection is all mesh objects """
    if len(objs) == 0:
        print("No objects selected")
        self.report(type={"WARNING"}, message="Nothing Selected")
        return False

    for obj in objs:
        if obj.type != "MESH":
            print("Selection does not contain a valid mesh")
            self.report(type={"WARNING"}, message="Select a valid mesh")
            return False
    return True


def set_select_state(obj, opt):
    """
    2.80: <context.select_set(state=opt)>
    2.79: <context.select = opt>

    Multi version compatibility for setting object selection
    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-11
    """
    if hasattr(obj, "select_set"):
        obj.select_set(state=opt)  # B2.8
    else:
        obj.select = opt


def set_mode_state(context, opt):
    """
    2.80: <>
    2.79: <>

    Multi version compatibility for setting object selection
    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-11
    """
    if hasattr(context, "mode_set"):
        context.mode_set(state=opt)  # B2.8
    else:
        context.mode = opt


# def set_uv_array(context, index, x, y):
#        return context


def set_uv_data_active(context, obj):
    """
    2.80: <context.uv_layers.active = obj>
    2.79: <context.tessface_uv_textures.active = obj>
    """
    if hasattr(context, "uv_layers"):
        context.uv_layers.active = obj  # B2.8
    else:
        context.tessface_uv_textures.active = obj


def set_object_link(context, obj):
    """
    2.80: <context.collection.objects.link(obj)>
    2.79: <context.scene.objects.link(obj)>
    """
    if hasattr(context, "collection"):
        context.collection.objects.link(obj)  # B2.8
    else:
        context.scene.objects.link(obj)


def set_obj_draw_type(obj, draw_type):
    """
    2.80: <obj.display_typev>
    2.79: <obj.draw_type>
    """
    if hasattr(obj, "draw_type"):
        obj.draw_type = draw_type
    else:
        obj.display_type = draw_type


def update_matrices(obj):
    """
    https://stackoverflow.com/a/57485640
    """
    if obj.parent is None:
        obj.matrix_world = obj.matrix_basis
    else:  # TODO @
        obj.matrix_world = obj.parent.matrix_world * \
            obj.matrix_parent_inverse * \
            obj.matrix_basis


def make_annotations(cls):
    """Add annotation attribute to fields to avoid Blender 2.8+ warnings
    https://github.com/OpenNaja/cobra-tools/blob/master/addon_updater_ops.py"""
    if not hasattr(bpy.app, "version") or check_version(2, 80, 0) < 0:
        return cls
    if check_version(2, 93, 0) < 0:
        bl_props = {k: v for k, v in cls.__dict__.items()
                    if isinstance(v, tuple)}
    else:
        bl_props = {k: v for k, v in cls.__dict__.items()
                    if isinstance(v, bpy.props._PropertyDeferred)}
    if bl_props:
        if "__annotations__" not in cls.__dict__:
            setattr(cls, "__annotations__", {})
        annotations = cls.__dict__["__annotations__"]
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls


# B44+ by SaintBaron

# =====================================================================
# Slotted Actions compatibility (Blender 4.4+ / 5.0+)
# =====================================================================
# In Blender 5.0+, action.fcurves.new() was removed. F-Curves now live
# on a channelbag inside an action's keyframe strip, addressed via a slot.
# These helpers paper over the difference so the same call site works on
# old (2.8-4.3) and new (4.4+) Blender.

def _ensure_channelbag_for_action(action, slot_id_type='OBJECT', slot_name=""):
    """Ensure a channelbag exists for the given action's first compatible slot.
    Returns:
        - (action, None)              on Blender < 4.4 (legacy API works as-is)
        - (action, channelbag)        on Blender >= 4.4 (new slotted API)
    """
    # bpy.app.version is a tuple; 4.4 is the cut-over.
    if bpy.app.version < (4, 4, 0):
        return action, None

    # New API: slots + layers + strips + channelbag.
    # Reuse an existing compatible slot if one is already present.
    slot = None
    for s in action.slots:
        # target_id_type 'UNSPECIFIED' is treated as compatible.
        if s.target_id_type in (slot_id_type, 'UNSPECIFIED'):
            slot = s
            break
    if slot is None:
        slot = action.slots.new(id_type=slot_id_type, name=slot_name or "Slot")

    # Ensure layer + keyframe strip exist.
    if len(action.layers) == 0:
        layer = action.layers.new("Layer")
    else:
        layer = action.layers[0]

    if len(layer.strips) == 0:
        strip = layer.strips.new(type='KEYFRAME')
    else:
        strip = layer.strips[0]

    channelbag = strip.channelbag(slot, ensure=True)
    return action, channelbag


def assign_action_with_slot(animated_id, action, slot_id_type='OBJECT'):
    """Assign an action to a data-block and (on 4.4+) auto-bind a slot.
    `animated_id` must already have animation_data (call
    animation_data_create() first).
    """
    anim_data = animated_id.animation_data
    anim_data.action = action

    if bpy.app.version >= (4, 4, 0):
        # Try Blender's auto-assign first.
        if anim_data.action_slot is None:
            # Find or create a compatible slot.
            slot = None
            for s in action.slots:
                if s.target_id_type in (slot_id_type, 'UNSPECIFIED'):
                    slot = s
                    break
            if slot is None:
                slot = action.slots.new(id_type=slot_id_type, name=animated_id.name)
            anim_data.action_slot = slot


def fcurves_new(action, data_path, index=0, group_name="",
                slot_id_type='OBJECT'):
    """Create an F-Curve on `action`, compatible with both legacy and
    slotted-action APIs.
    On Blender < 4.4: uses action.fcurves.new(...).
    On Blender >= 4.4: uses channelbag.fcurves.new(...).
    """
    if bpy.app.version < (4, 4, 0):
        # Legacy API still has the `action_group` kw.
        if group_name:
            return action.fcurves.new(data_path, index=index,
                                      action_group=group_name)
        return action.fcurves.new(data_path, index=index)

    _, channelbag = _ensure_channelbag_for_action(
        action, slot_id_type=slot_id_type)
    if group_name:
        return channelbag.fcurves.new(data_path, index=index,
                                      group_name=group_name)
    return channelbag.fcurves.new(data_path, index=index)


def fcurves_iter(action):
    """Iterate the F-Curves of an action across Blender versions.
    On Blender < 5.0: action.fcurves works directly (it's a real
    collection on <4.4, and a legacy proxy on 4.4-4.5).
    On Blender >= 5.0: action.fcurves is gone; F-Curves are gathered
    from each slot's channelbag inside the first keyframe strip.
    """
    # Fast path for <5.0: action.fcurves exists (native or proxy).
    fcurves = getattr(action, "fcurves", None)
    if fcurves is not None:
        for fcu in fcurves:
            yield fcu
        return
    # 5.0+: walk layers/strips/slots/channelbags.
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                try:
                    cb = strip.channelbag(slot)
                except Exception:
                    cb = None
                if cb is None:
                    continue
                for fcu in cb.fcurves:
                    yield fcu


def fcurves_get(action):
    """Return the action's F-Curves as a list (indexable) across versions.
    Blender 5.0 removed the action.fcurves legacy proxy. Callers that
    indexed into action.fcurves[i] need a real sequence instead.
    """
    # Fast path: legacy proxy or pre-4.4 collection.
    fcurves = getattr(action, "fcurves", None)
    if fcurves is not None:
        try:
            return list(fcurves)
        except Exception:
            pass

    # New API: gather from every slot's channelbag.
    out = []
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                try:
                    cb = strip.channelbag(slot)
                except Exception:
                    cb = None
                if cb is None:
                    continue
                out.extend(cb.fcurves)
    return out
# end B44+


def set_obj_group(obj, new_group=None):
    """
    2.80: <bpy.data.collections>
    2.79: <bpy.data.scenes>

    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-4
    """
    if not new_group:
        raise ValueError("cant assign object to group")

    if hasattr(obj, "layers"):  # B 2.7x
        for layer in bpy.data.scenes:
            # remove object from layer if present
            if obj not in layer.objects[:]:
                continue
            layer.objects.unlink(obj)
        new_group.objects.link(obj)
    else:  # B2.8
        # remove object from sub-colection if present
        for layer in bpy.data.collections:
            if obj in layer.objects[:]:
                layer.objects.unlink(obj)
        # remove object from master collection if present
        # for layer in bpy.data.scenes[0].collection:
        #     if object in layer.objects[:]:
        #         layer.objects.unlink(object)
        if obj in bpy.context.scene.collection.objects[:]:
            bpy.context.scene.collection.objects.unlink(obj)
        # assign object to collection
        new_group.objects.link(obj)


def set_layout_separator(ui_element, factor=1.0):
    """ _ """
    if check_version(2, 80, 0) < 0:
        ui_element.separator()
    else:
        ui_element.separator(factor=factor)


def get_mesh_objects(array):
    """ discard non mesh """
    out = []
    for o in array:
        if o is None:
            continue
        if o.type == "MESH":
            out.append(o)
    return out


def get_shapekey_name_str():
    return "Frame_%03d"


def sync_shapekey_to_frame(obj, sk_data):
    """ _ """
    if sk_data is None:
        return

    if sk_data.use_relative:  # shape key relative
        for i, sk in enumerate(sk_data.key_blocks):
            if sk.value == 1.0:  # find if shape key matches active frame
                obj.active_shape_key_index = i
                break
    else : # sk absolute
        eval_time = sk_data.eval_time
        frame_min = eval_time - 0.01  # find close float
        frame_max = eval_time + 0.01  #
        for i, sk in enumerate(sk_data.key_blocks):
            sk_time = sk.frame
            if (sk_time > frame_min and sk_time < frame_max):
                obj.active_shape_key_index = i
                break


def get_shapekey_data(obj):
    if hasattr(obj.data, "shape_keys") \
        and obj.data.shape_keys is not None:
        return obj.data.shape_keys
    return None


def get_shapekey_anim_data(obj_dat, relative):
    if relative:
        if check_version(2, 80, 0) < 0:
            return obj_dat.animation_data
        return obj_dat.shape_keys.animation_data
    else:
        return obj_dat.shape_keys.animation_data


def get_anim_fdata_vert():
    """ vertex names for action fcurve """
    # "vertices[%d].co"
    if check_version(2, 80, 0) < 0:
        return "data.verts[%d].co" #<2.8
    return "data.vertices[%d].co"


def set_auto_smooth(mesh, angle):
    """ _ """
    if hasattr(mesh, "use_auto_smooth"):
        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = radians(angle)
    # else: auto_smooth_angle


def readChunkToList(file, data_str: str, read_len: int):
    """ _ """
    chunk_size = struct.calcsize(data_str)
    total_size = read_len * chunk_size
    buff = file.read(chunk_size * read_len)
    return [struct.unpack(data_str, buff[i:i + chunk_size])
        for i in range(0, total_size, chunk_size)]


def readChunk(file, data_str: str, read_len: int):
    """ _ """
    chunk_size = struct.calcsize(data_str)
    return file.read(chunk_size * read_len)


def getChunk(data, data_str: str, start_idx: int):
    """ _ """
    chunk_size = struct.calcsize(data_str)
    end_idx = start_idx + chunk_size
    return struct.unpack(data_str, data[start_idx:end_idx]), end_idx


def getDepsgraph():
    if check_version(2, 80, 0) >= 0:
        return bpy.context.evaluated_depsgraph_get()
    # B2.79
    return None


def getVertexNormalsFromMesh_faceWeight(me):
    """
    used to keep polygon weight(1 face) to weight normal
    better than trianglated, where 2 faces could add edge to normal.
    TODO add as option?
    """
    me_verts = me.vertices
    vert_count = len(me_verts)
    accum_normals = [[0.0, 0.0, 0.0] for _ in range(vert_count)]
    for poly in me.polygons:
        pn = poly.normal
        for v_idx in poly.vertices:
            accum_normals[v_idx][0] += pn[0]
            accum_normals[v_idx][1] += pn[1]
            accum_normals[v_idx][2] += pn[2]
    return accum_normals


def getVertexNormalsFromMesh(me, custom_vn=False):
    """
    get local cords of vetex normals

    note: model is not split at vertex.
            set mesh to smoothed and detatch faces at hard edge
            or use "edge split" modifier with hard edges marked
    """
    me_verts = me.vertices
    vert_count = len(me.vertices)

    if not custom_vn:
        return [list(v.normal) for v in me_verts]

    ret_normals = [Vector((0.0, 0.0, 0.0)) for _ in range(vert_count)]
    has_custom = False

    if hasattr(me, "corner_normals"):
        # ---- Blender 4.1+ ----
        if me.corner_normals:
            has_custom = True
            for loop in me.loops:
                v_idx = loop.vertex_index
                ret_normals[v_idx] += me.corner_normals[loop.index].vector
    elif hasattr(me, "calc_normals_split"):
        # ---- Blender 2.7x to 4.0 ----
        me.calc_normals_split()
        has_custom = True
        for loop in me.loops:
            v_idx = loop.vertex_index
            ret_normals[v_idx] += loop.normal

    if has_custom:
        return [list(n) for n in ret_normals]
    return [list(v.normal) for v in me_verts]


def getEvaluatedMesh(obj, depsgraph, apply_modifyer=True):
    """
    get evaluated mesh
    return none of failed
    """
    me = None
    eval_obj = None
    if check_version(2, 80, 0) >= 0:  # B2.8
        eval_obj = obj.evaluated_get(depsgraph)
        try:
            if apply_modifyer:
                me = eval_obj.to_mesh()
            else:
                me = eval_obj.original.to_mesh()
                eval_obj = eval_obj.original #use correct mesh
        except RuntimeError:
            eval_obj.to_mesh_clear()
            return None, None
    else:  # B2.79
        try:
            me = obj.to_mesh(
                bpy.context.scene,
                apply_modifyer,
                calc_tessface=False,
                settings="PREVIEW")  # "RENDER" "PREVIEW")
        except RuntimeError:
            # bpy.data.meshes.remove(me)
            return None, None  # return None

    return me, eval_obj


# kpc.getMehWorldCords_fn()
def getMeshWorldCords_fn(obj, depsgraph, apply_modifyer=True):
    """ Get real world position of each vertex (post-deform) """
    if check_version(2, 80, 0) >= 0:
        me, eval_obj = getEvaluatedMesh(obj, depsgraph, apply_modifyer)
        if me is None:
            return []
        try:
            mw = eval_obj.matrix_world
            return [mw @ v.co for v in me.vertices]
        finally:
            eval_obj.to_mesh_clear() #cleanup

    # B2.79
    me, _ = getEvaluatedMesh(obj, None, apply_modifyer)
    try:
        mw = obj.matrix_world
        return [mw * v.co for v in me.vertices]
    finally:
        bpy.data.meshes.remove(me) #cleanup


#kpc.setMeshLocalCords_fn
def setMeshLocalCords_fn(obj, world_positions):
    """ position vert relative to existing transforms """
    if len(world_positions) != len(obj.data.vertices):
        raise ValueError(
            "Source evaluated vertex count does not match destination mesh"
        )

    inv = obj.matrix_world.inverted()
    if check_version(2, 80, 0) >= 0:
        return [inv @ p for p in world_positions]
    # B2.79
    return [inv * p for p in world_positions]


def isMatrix_identity(obj):
    """
    Check if matrix is identity or empty safely across 2.79 up to 4.x
    """
    mw = obj.matrix_world
    # Standard identity check: diagonals are 1.0, everything else is 0.0
    if abs(mw[0][0]-1) + abs(mw[1][1]-1) + abs(mw[2][2]-1) + abs(mw[3][3]-1) < 0.0001:
        return True
    return False


def transformMesh(obj, me, global_cords):
    """ get vertex pos in global cords """
    if not global_cords or isMatrix_identity(obj):
        return

    mw = obj.matrix_world
    me.transform(mw)

   # 2. Extract determinant safely based on Blender Version API differences
    if check_version(2, 80, 0) < 0:
        det = mw.determinant()
        me.calc_normals_split()
    else:
        det = mw.determinant if not hasattr(mw.determinant, "__call__") else mw.determinant()

    if det < 0.0:
        me.flip_normals()
        print("Note: object transform is negative, flipping face normals")
    # done transformMesh()
    # #####################


def transformNormals(obj, vn_data, global_cords):

    if global_cords and not isMatrix_identity(obj):
        return vn_data # Safely return raw data; they are already in world space!

    # Fallback/Skip condition if no transformation happened at all
    if not global_cords or isMatrix_identity(obj):
        return vn_data

    mat = obj.matrix_world.inverted().transposed().to_3x3()
    if check_version(2, 80, 0) >= 0:
        return [list((mat @ Vector(n)).normalized()) for n in vn_data]
    # B2.79
    return [list((mat * Vector(n)).normalized()) for n in vn_data]


def computeTriangleData(me):
    """ run this before any object transformation """
    if hasattr(me, "calc_loop_triangles"):
        # Blender 2.80+
        me.calc_loop_triangles()
    else:
        # Legacy Blender 2.79
        me.calc_tessface()


# get mesh data at current frame
def getMeshArrays_fn(obj_group=None,
                     getUV=False,
                     apply_modifyer=True,
                     custom_vn=False,
                     global_cords=True):
    """Return collapsed mesh data at current frame.

    :param obj_group: The object data to load.
    :type object:     object array.
    :param getUV:     get uv data.
    :type getUV:      bool
    :param apply_modifyer: apply modifier
    :type apply_modifyer:  bool
    :param custom_vn:      use custom normals
    :type custom_vn:       bool

    :rtype: array
    :return: obj_array(
        : md_idc_vert    # indices (vert)
        : md_idc_uv      # indices (vert uv)
        : md_xyz_vert    # xyz (pos vert)
        : md_xyz_norm    # xyz (pos vert normal)
        : md_xy_uv       # XY (pos UV)
        : md_face_count  # COUNT (face)
        : md_vert_count  # COUNT (vertex)
        : md_uv_count    # COUNT (UV)
    )
    """
    def get_triangle_data(me, faceuv):
        """
        Returns (vert_indices, uvs)
        Each is a flat list of length tri_count * 3
        """
        vert_indices = []
        uvs = []
        mat_indices = []
        uv_data = None

        if hasattr(me, "loop_triangles"):
            # 2.80+
            # me.calc_loop_triangles()
            if faceuv:
                uv_data = me.uv_layers.active.data
            for tri in me.loop_triangles:
                mat_indices.append(tri.material_index) # material
                vert_indices.extend(tri.vertices)
                if uv_data:
                    for l_idx in tri.loops:
                        uvs.append(tuple(uv_data[l_idx].uv))
        else:
            # 2.79: UVs from tessface_uv_textures, normals from split_normals
            # me.calc_tessface()
            if faceuv:
                uv_data = me.tessface_uv_textures.active.data
            for face in me.tessfaces:
                v = face.vertices
                if len(v) == 3:
                    mat_indices.append(face.material_index) # material
                    vert_indices.extend([v[0], v[1], v[2]])
                    if uv_data:
                        uv_face = uv_data[face.index]
                        uvs.extend([
                            tuple(uv_face.uv1), tuple(uv_face.uv2),tuple(uv_face.uv3)])
                else:
                    mat_indices.extend([face.material_index, face.material_index])
                    vert_indices.extend([v[0], v[1], v[2], v[0], v[2], v[3]])
                    if uv_data:
                        uv_face = uv_data[face.index]
                        uvs.extend([
                            tuple(uv_face.uv1), tuple(uv_face.uv2), tuple(uv_face.uv3), # Tri 1
                            tuple(uv_face.uv1), tuple(uv_face.uv3), tuple(uv_face.uv4)  # Tri 2
                        ])

        return vert_indices, uvs, mat_indices #, normals

    def fillMeshArrays(me, faceuv, custom_vn):
        """ generate arrays """
        me_verts = me.vertices
        ret_vert_count = len(me_verts)
        ret_count_mat = max(len(me.materials), 1)
        tmp_idc_uv = []
        tmp_XY_uv = []

        # --- Vertex position ---
        tmp_XYZ_vert = [v.co[:] for v in me_verts]

        # --- Vertex normals ---
        tmp_XYZ_norm = getVertexNormalsFromMesh(me, custom_vn)

        # --- face indices ---
        tmp_idc_vert, uvs, tmp_face_matid = get_triangle_data(me, faceuv)

        # --- UV cords ---
        uv_unique_count = 0
        if faceuv:
            uv_dict = {}
            uv_get = uv_dict.get
            for i, v_idx in enumerate(tmp_idc_vert):
                uv = uvs[i]
                uv_key = (v_idx, uv)
                uv_val = uv_get(uv_key)
                if uv_val is None:
                    uv_val = uv_dict[uv_key] = uv_unique_count
                    tmp_XY_uv.append(uv)
                    uv_unique_count += 1
                tmp_idc_uv.append(uv_val)

        face_count = len(tmp_idc_vert) // 3 # face= 3verts

        return MeshData(
            md_idc_vert=tmp_idc_vert,  # indices
            md_idc_uv=tmp_idc_uv,      # indices
            md_xyz_vert=tmp_XYZ_vert,  # xyz
            md_xyz_norm=tmp_XYZ_norm,  # xyz
            md_xy_uv=tmp_XY_uv,        # XY
            md_face_count=face_count,     # COUNT
            md_vert_count=ret_vert_count, # COUNT
            md_uv_count=uv_unique_count,  # COUNT
            md_face_mat=tmp_face_matid,
            md_mat_count=ret_count_mat)   # COUNT
    # done fillMeshArrays()
    # #####################

    ret_ob_data = []

    if obj_group is None or len(obj_group) == 0:
        raise ValueError("No mesh in array")

    if check_version(2, 80, 0) >= 0:  # B2.80
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for obj in obj_group:
            obj = bpy.data.objects[obj.name].evaluated_get(depsgraph)
            me, depMesh = getEvaluatedMesh(obj, depsgraph, apply_modifyer)
            if not me:
                continue

            faceuv = False
            if getUV:
                faceuv = bool(len(me.uv_layers) > 0)
                if not faceuv:
                    me.uv_layers.new()  # add uv map
                    faceuv = True
            computeTriangleData(me)
            transformMesh(obj, me, global_cords)
            m_data = fillMeshArrays(me, faceuv, custom_vn)
            normals = transformNormals(obj, m_data.md_xyz_norm, global_cords)
            m_data = m_data._replace(md_xyz_norm=normals) # repack
            ret_ob_data.append(m_data)
            # clean up
            depMesh.to_mesh_clear()
    else:  # B2.79
        for obj in obj_group:
            me, _ = getEvaluatedMesh(obj, None, apply_modifyer)
            if not me:
                continue

            faceuv = False
            if getUV:
                faceuv = len(me.uv_textures) > 0
                if not faceuv:
                    me.uv_textures.new()  # add uv map
                    faceuv = True
            computeTriangleData(me)
            transformMesh(obj, me, global_cords)
            m_data = fillMeshArrays(me, faceuv, custom_vn)
            normals = transformNormals(obj, m_data.md_xyz_norm, global_cords)
            m_data = m_data._replace(md_xyz_norm=normals) # repack
            ret_ob_data.append(m_data)
            # clean up
            bpy.data.meshes.remove(me)

    if len(ret_ob_data) == 0:
        raise ValueError("No mesh in array")

    return ret_ob_data
# end getMeshArrays_fn


# Utility functions
def refresh_ui_keyframes():
    """ use after a scrip update of annimation data """
    try:
        for area in bpy.context.screen.areas:
            if area.type in ("TIMELINE", "GRAPH_EDITOR", "DOPESHEET_EDITOR"):
                area.tag_redraw()
    except Exception:
        print("ERROR: refresh_ui_keyframes")


################################
# Grok generted smooth function
def bilateral_filter_circular(data, sigma_space=1.5, sigma_range=5.0):
    """
    Pure Python 1D circular bilateral filter (no numpy/matplotlib)

    data         : list or tuple of floats
    sigma_space  : how far to look (1.5-3.0)
    sigma_range  : edge preservation threshold (25-50 for 0-255 data)

    Returns: list of smoothed values
    """
    print("bilateral_filter_circular")
    data = list(data)          # make sure it's a list
    len_array = len(data)
    result = [0.0] * len_array
    radius = int(3.0 * sigma_space + 0.5)   # 3-sigma rule

    # Precompute spatial Gaussian weights
    spatial = []
    sum_spatial = 0.0
    for k in range(-radius, radius + 1):
        w = exp(- (k * k) / (2.0 * sigma_space * sigma_space))
        spatial.append(w)
        sum_spatial += w
    # normalize
    spatial = [w / sum_spatial for w in spatial]

    for i in range(len_array):
        weighted_sum = 0.0
        total_weight = 0.0

        for k in range(-radius, radius + 1):
            j = (i + k) % len_array         # circular wrap
            diff = data[i] - data[j]
            range_weight = exp(- (diff * diff) /
                               (2.0 * sigma_range * sigma_range))
            weight = spatial[k + radius] * range_weight

            weighted_sum += data[j] * weight
            total_weight += weight

        result[i] = weighted_sum / \
            total_weight if total_weight > 1e-8 else data[i]

    return result

################


def fast_threshold_bilateral_init(data_vert, data_scale, data_bytes, print_z):
    """ handle scale
        sent 1byte data array. do compare/smoothing.
        then use scale to get game/blender size.
    """
    len_array = len(data_vert)
    result = [0.0] * len_array

    # use byte data to get differnce
    out_data = fast_threshold_bilateral(data_bytes)

    # convert back to blender unit
    for fr, new_pos in enumerate(out_data):
        if print_z and fr == 10:
            print("(%3i %3i %3i) (%-4.2f %-4.2f %-4.2f) (%-4.2f)" %
                  (data_bytes[fr - 1], data_bytes[fr], data_bytes[fr + 1],
                   data_vert[fr - 1], data_vert[fr], data_vert[fr + 1], new_pos))
        result[fr] = new_pos * data_scale[fr] + data_vert[fr]

    return result


def mod_hd_setup_weight():
    """ _ """
    # mod_hd_setup_weight_width() # build lookup tables
    # mod_hd_setup_weight_height()


#############
# frames/width
HD_RANGE_WIDTH = 2  # search -2 frames, frame0 and +2 frames
# MOD_HD_WEIGHTS_WIDTH = [0.25, 0.5, 1.0, 0.5, 0.25]

#############
# height
# HD_RANGE_HEIGHT = 2
# WEIGHTS_HEIGHT_LOOKUP = [0.25, 1.0, 1.0, 1.0, 0.25]  # Only 5 values needed
# MOD_HD_WEIGHTS_HEIGHT = None
# def mod_hd_setup_weight_height():
#     global MOD_HD_WEIGHTS_HEIGHT
#     if MOD_HD_WEIGHTS_HEIGHT is not None:
#         return

#     # Zero-fill
#     MOD_HD_WEIGHTS_HEIGHT = [[0.0] * 256 for _ in range(256)]

#     for center in range(256):
#         for radius in range(-HD_RANGE_HEIGHT, HD_RANGE_HEIGHT + 1):
#             neighbor = (center + radius) & 255  # Fast wrap
#             weight = WEIGHTS_HEIGHT_LOOKUP[radius + HD_RANGE_HEIGHT] # Fast lookup
#             MOD_HD_WEIGHTS_HEIGHT[center][neighbor] = weight


# grok. faster smooth
def fast_threshold_bilateral(data):
    """
    Temporal bilateral filter for vertex height streams.
    Preserves edges, kills 1-bit noise, stays stable on fast motion.
    """
    if not data:
        return data
    ##############

    sigma_t=2.0
    sigma_r=1.5
    rng = 2
    rangeMin = -rng
    rangeMax = rng+1

    n = len(data)
    result = [0.0] * n

    for i in range(n):
        smoothed = 0.0
        w_total = 0.0

        for offset in range(rangeMin, rangeMax):  # ±5 frames
            j = (i + offset) % n
            dt = (offset) ** 2 / (2 * sigma_t ** 2)
            dr = (data[j] - data[i]) ** 2 / (2 * sigma_r ** 2)
            w = exp(-dt - dr)

            smoothed += w * data[j]
            w_total += w

        if w_total > 0:
            smoothed /= w_total
            result[i] = smoothed - data[i]

    return result



    # n = len(data)
    # result = [0.0] * n
    # window = 2 * HD_RANGE_WIDTH + 1

    # for i in range(n):
    #     total = 0.0
    #     for offset in range(-HD_RANGE_WIDTH, HD_RANGE_WIDTH + 1):
    #         j = (i + offset) % n
    #         total += data[j]

    #     avg = total / window
    #     result[i] = (avg - data[i]) / 64          # raw delta in byte units (-128..+127 range max)

    # return result
# end grok

def fast_threshold_bilateral_mh(data):
    """
    Temporal bilateral filter for vertex height streams.
    Preserves edges, kills 1-bit noise, stays stable on fast motion.
    """
    if not data:
        return data

    len_array = len(data)
    result = [0.0] * len_array
    search_total = (2 * HD_RANGE_WIDTH) + 1

    for fr in range(len_array):
        center_vert = data[fr]  # read current vertex position byte
        sum_val = 0.0

        for fr_ofset in range(-HD_RANGE_WIDTH, HD_RANGE_WIDTH + 1):
            j = (fr + fr_ofset) % len_array
            # read near frame vertex position. wrap, byte
            neighbour_vert = data[j]

            if neighbour_vert > center_vert:
                sum_val += 1.0
            elif neighbour_vert < center_vert:
                sum_val -= 1.0
        result[fr] = sum_val / float(search_total)  # (center_vert +

    return result


def __fast_threshold_bilateral(data):
    """
    Temporal bilateral filter for vertex height streams.
    Preserves edges, kills 1-bit noise, stays stable on fast motion.
    """
    if not data:
        return data

    len_array = len(data)
    result = [0.0] * len_array

    for fr in range(len_array):
        center_vert = data[fr]  # read current vertex position byte
        sum_val = 0.0
        sum_weight = 0.0

        for fr_ofset in range(-HD_RANGE_WIDTH, HD_RANGE_WIDTH + 1):
            j = (fr + fr_ofset) % len_array
            # read near frame vertex position. wrap, byte
            neighbour_vert = data[j]

            # Value similarity (range weight)
            height_weight = MOD_HD_WEIGHTS_HEIGHT[center_vert][neighbour_vert]
            # Temporal proximity (spatial weight)
            width_weight = MOD_HD_WEIGHTS_WIDTH[fr_ofset + HD_RANGE_WIDTH]

            w = height_weight * width_weight
            if w > 0.0:  # skip zero-weight
                sum_val += w * neighbour_vert
                sum_weight += w
        if sum_weight > 0.01:
            result[fr] = sum_val / sum_weight
        else:
            result[fr] =  float(center_vert)

    return result
# end grok

# grok. faster smooth


def _fast_threshold_bilateral(data, threshold=3.0, radius=2):
    """
    Super-fast circular threshold bilateral filter (no math.exp!)

    Perfect for 8-bit quantized 3D model vertices / animation cleanup
    Used in AAA games (Unreal, Unity, Frostbite, etc.)

    Parameters:
        data           : list[float] or tuple
        threshold      : max difference to consider "similar" (5.0–7.0 best for 8-bit)
        radius         : how many neighbors to look at (2 = 5-tap, very fast)

    Returns: list of smoothed values
    """
    data = list(data)
    len_array = len(data)
    result = [0.0] * len_array

    for fr in range(len_array):
        center = data[fr]
        sum_val = 0.0
        sum_weight = 0.0

        for k in range(-radius, radius + 1):
            j = (fr + k) % len_array
            diff = float(abs(center - data[j]))

            if diff <= threshold:
                weight = 1.0 - diff / threshold          # smooth ramp
                sum_val += data[j] * weight
                sum_weight += weight

        result[fr] = sum_val / sum_weight if sum_weight > 0.01 else center

    return result
# end grok


# grok
def smooth_gauss_fast(v_pos, v_scale, isLoop):
    len_array = len(v_pos)
    ret = [0.0] * len_array

    # Precompute exp(-0.5 * x²) for x = 0..5 (distances are small)
    exp_table = [exp(-0.5 * d*d) for d in range(6)]

    for fr in range(len_array):
        sum_w = 0.0
        sum_p = 0.0
        center = v_pos[fr]

        for j in range(-2, 3):
            fr2 = (fr + j) % len_array if isLoop else fr + j
            if not isLoop and (fr2 < 0 or fr2 >= len_array):
                continue

            diff = abs(v_pos[fr2] - center)
            scale = abs(v_scale[fr2] * 2.5)

            # Approximate: find closest integer distance bucket
            idx = min(int(diff / scale + 0.5), 5)
            w = exp_table[idx] if scale > 0 else 0.0

            sum_w += w
            sum_p += w * v_pos[fr2]

        ret[fr] = sum_p / sum_w if sum_w > 0 else center

    return ret

def smooth_better(v_pos, v_scale, isLoop, range_mult=2.8):
    n = len(v_pos)
    ret = [0.0] * n

    for i in range(n):
        sum_p = 0.0
        sum_w = 0.0
        center = v_pos[i]

        for j in range(-2, 3):
            idx = i + j
            if not isLoop:
                if idx < 0 or idx >= n:
                    continue
            else:
                idx %= n

            diff = abs(v_pos[idx] - center)
            sigma = abs(v_scale[idx]) * range_mult   # 2.5–3.2 usually best

            if sigma > 0:
                w = exp(-0.5 * (diff / sigma) ** 2)
            else:
                w = 1.0 if diff == 0 else 0.0

            sum_w += w
            sum_p += w * v_pos[idx]

        ret[i] = sum_p / sum_w if sum_w > 0 else center

    return ret
# end grok
