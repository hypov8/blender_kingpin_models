"""
##############################
convert q3 models to kingpin
##############################
"""


# from ast import ExceptHandler
from pathlib import Path  # , Try, excepthandler
import bpy
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup
)
from bpy.props import (
    BoolProperty,
    StringProperty,
    EnumProperty,
    IntProperty,
    FloatProperty
)
from collections import namedtuple
from math import radians
from mathutils import Vector, Matrix
from enum import IntEnum
from . import common_kp as kpc

# q3 anims
class Q3_Seq(IntEnum):
    #  q3 animation file indexed names

    def __str__(self):
        return str(self.value)
    #death
    BOTH_DEATH1 = 0
    BOTH_DEAD1 = 1
    BOTH_DEATH2 = 2
    BOTH_DEAD2 = 3
    BOTH_DEATH3 = 4
    BOTH_DEAD3 = 5
    #torso
    TORSO_GESTURE = 6
    TORSO_ATTACK = 7
    TORSO_ATTACK2 = 8
    TORSO_DROP = 9
    TORSO_RAISE = 10
    TORSO_STAND = 11
    TORSO_STAND2 = 12
    #legs
    LEGS_WALKCR = 13
    LEGS_WALK = 14
    LEGS_RUN = 15
    LEGS_BACK = 16
    LEGS_SWIM = 17
    LEGS_JUMPA = 18
    LEGS_LANDA = 19
    LEGS_JUMPB = 20
    LEGS_LANDB = 21
    LEGS_IDLE = 22
    LEGS_IDLECR = 23
    LEGS_TURN = 24


# kp animations
class KP_Seq(IntEnum):
    """ kingpin animation index """
    TG_RDY = 0         # tgun_rdy_       1st frame
    TG_SHOOT = 1       # tg_shoot_
    TG_TAUNT1 = 2      # tg_bird_
    TG_TAUNT2 = 3      # tg_crch_grab_
    TG_TAUNT3 = 4      # tg_chin_flip_
    P_RDY = 5          # 1pstl_rdy_ 1st frame. pist
    P_SHOOT = 6        # p_std_shoot_
    WALK = 7           # walk_gdown_
    TG_WALK_SHOOT = 8  # walk_tg_sht_
    TG_RUN_SHOOT = 9   # run_tg_sht_
    TG_RUN_RIGHT = 10  # rsd_tg_run_
    TG_RUN_LEFT = 11   # lsd_tg_run_
    P_WALK_SHOOT = 12  # p_walk_sht_   pistol
    P_RUN_SHOOT = 13   # p_run_shoot_  pistol
    P_RUN_RIGHT = 14   # p_rside_run_  *missing*
    P_RUN_LEFT = 15    # p_lside_run_  *missing*
    M_RDY = 16         # melee_rdy_    1st frame
    M_HIT1 = 17        # melee1_
    M_HIT2 = 18        # melee2_
    M_RUN = 19         # run_melee_    //check
    RUN = 20           # run_gun_dn_
    JUMP = 21          # jump_       1st frame
    LADR = 22          # clmb_loop_  *missing*
    DEATH1 = 23        # death1_    19 frames
    DEATH2 = 24        # death2_   16 frames
    DEATH3 = 25        # death3_   28 frames
    DEATH4 = 26        # death4_   13 frames
    TG_CR_RDY = 27     # tg_crch_rdy_
    TG_CR_SHOOT = 28   # crouch_shoot_
    CR_WALK = 29       # crch_walk_
    P_CR_RDY = 30      # 1p_crch_rdy_  pistol
    P_CR_SHOOT = 31    # p_crch_sht_   pistol
    P_CR_WALK = 32     # p_crch_walk_  1st frame
    CR_DEATH1 = 33     # crouch_death_ *missing*


class mdl_sec(IntEnum):
    LEGS = 0
    BODY = 1
    HEAD = 2
    WEPS = 3
    FLSH = 4


# Property DEFINITIONS
class KINGPIN_Q3toKP_props(PropertyGroup):
    #############
    # UI varables
    # stand
    ui_stand_tg_idle = BoolProperty(
        name="Idle TG",  # (Standing)",
        description=("Leg idle animations.\n" +
                     "Leg animation will be static if un-checked"),
        default=True,
    )
    ui_stand_p_idle = BoolProperty(
        name="Idle GUN",  # Pistol (Standing)",
        description=("Leg idle animations.\n" +
                     "Leg animation will be static if un-checked"),
        default=True,
    )
    ui_stand_ma_idle = BoolProperty(
        name="Idle PIPE",  # Pipe (Standing)",
        description=("Leg idle animations.\n" +
                     "Leg animation will be static if un-checked"),
        default=True,
    )
    ui_stand_taunt = BoolProperty(
        name="Taunt",
        description=("Leg idle animations.\n" +
                     "Leg animation will be static if un-checked"),
        default=False,
    )
    ui_stand_attack = BoolProperty(
        name="Attack",
        description=("Leg idle animations.\n" +
                     "Leg animation will be static if un-checked"),
        default=False,
    )
    ui_stand_ladder = BoolProperty(
        name="Ladder",
        description=("Leg idle animations.\n" +
                     "Leg animation will be static if un-checked"),
        default=True,
    )
    ui_stand_jump_anim = EnumProperty(
        name="Jump",
        description="Jump animation",
        items=[
            (str(int(Q3_Seq.LEGS_JUMPA)), "LEGS_JUMPA", "Animation to use for jump", 0), # 18
            (str(int(Q3_Seq.LEGS_JUMPB)), "LEGS_JUMPB", "Animation to use for jump", 1), # 20
        ],
        default=str(int(Q3_Seq.LEGS_JUMPA)),
    )
    ##########
    # crouch #
    ui_crouch_idle = BoolProperty(
        name="idle",
        description=("Leg idle animations.\n" +
                     "Leg animation will be static if un-checked"),
        default=True,
    )
    ui_crouch_shoot = BoolProperty(
        name="Attack",
        description=("Leg idle animations.\n" +
                     "Leg animation will be static if un-checked"),
        default=False,
    )
    ############################
    # crouch death anim
    ui_cr_death_anim = EnumProperty(
        name="Death",
        description="Crouch death animation",
        items=[
            (str(int(Q3_Seq.BOTH_DEATH1)), "BOTH_DEATH1", "Animation to use for crouch death", 0),
            (str(int(Q3_Seq.BOTH_DEATH2)), "BOTH_DEATH2", "Animation to use for crouch death", 1),
            (str(int(Q3_Seq.BOTH_DEATH3)), "BOTH_DEATH3", "Animation to use for crouch death", 2),
        ],
        default=str(int(Q3_Seq.BOTH_DEATH1)),
    )
    ############################
    # ladder anim. no equivalent
    ui_ladder_anim = EnumProperty(
        name="Ladder",
        description=("Ladder animation for legs."
                     "(No equivalent)"),
        items=[
            (str(int(Q3_Seq.LEGS_WALKCR)), "LEGS_WALKCR", "Animation to use for ladder.\nWalking Crouched.\nDefault", 0),
            (str(int(Q3_Seq.LEGS_WALK)), "LEGS_WALK", "Animation to use for ladder.\nWalking", 1),
            (str(int(Q3_Seq.LEGS_BACK)), "LEGS_BACK", "Animation to use for ladder.\nRun backwards", 2),
            (str(int(Q3_Seq.LEGS_SWIM)), "LEGS_SWIM", "Animation to use for ladder.\nSwimming", 3),
            (str(int(Q3_Seq.LEGS_JUMPA)), "LEGS_JUMPA", "Animation to use for ladder.\nJumping. Type 1", 4),
            (str(int(Q3_Seq.LEGS_LANDA)), "LEGS_LANDA", "Animation to use for ladder.\nLanding. Type 1", 5),
            (str(int(Q3_Seq.LEGS_JUMPB)), "LEGS_JUMPB", "Animation to use for ladder.\nJumping. Type 2", 6),
            (str(int(Q3_Seq.LEGS_LANDB)), "LEGS_LANDB", "Animation to use for ladder.\nLanding. Type 2", 7),
            (str(int(Q3_Seq.LEGS_IDLE)), "LEGS_IDLE", "Animation to use for ladder.\nIdling", 8),
            (str(int(Q3_Seq.LEGS_IDLECR)), "LEGS_IDLECR", "Animation to use for ladder.\nIdle Crouch", 9),
            (str(int(Q3_Seq.LEGS_TURN)), "LEGS_TURN", "Animation to use for ladder.\nTurn on spot", 10),
        ],
        default=str(int(Q3_Seq.LEGS_WALKCR)),
    )
    ############################
    # group "Run Sideways Angle"
    ui_rotate_leg_left = IntProperty(
        name="Left",
        description="Angle to rotate legs while running left",
        # subtype='ANGLE',
        min=0,
        max=120,
        default=35
    )
    ui_rotate_leg_right = IntProperty(
        name="Right",
        description="Angle to rotate legs while running right",
        min=0,
        max=120,
        default=35
    )
    #######
    # scale
    ui_scale = FloatProperty(
        name="Model Scale",
        description="Scale model to suit kingpin\nThis adds a cube at base, that can be scaled after",
        min=0.5,
        max=5,
        precision=2,
        default=1.4
    )
    ###################
    # match death anims
    ui_use_framerate_for_death = BoolProperty(
        name="Match Death FPS",
        description=(
            "Enable: Animations Speed/FPS match Q3\n" +
            "Places empty frames at end of death sequence\n" +
            "Note: disabled will fill animation timeline"
        ),
        default=True,
    )
    # add timeline names
    ui_add_timeline = BoolProperty(
        name="Add Timeline Names",
        description=(
            "Add timeline frame names\n" +
            "Note: this wipes existing frame name data"
        ),
        default=True,
    )
    ############
    # file input
    ui_path_cfg_file = StringProperty(
        name="",  # Animation.cfg",
        description="animation.cfg path",
        default="animation.cfg",
        maxlen=1024,
        options={'HIDDEN'},
        subtype='NONE'  # FILE_PATH'
    )


# GUI
class KINGPIN_PT_Q3_to_KP_GUI(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = kpc.set_ui_panel_string()
    bl_category = 'Kingpin'
    bl_label = 'QUAKE3 to KP'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        kp_tool_q3tokp = context.window_manager.kp_q3tokp_
        # context.window_manager.kp_q3tokp_
        layout = self.layout

        box1 = layout.box()
        row = box1.row(align=True)
        # STANDING
        row.alignment = 'CENTER'
        row.label(text="Leg Anims: Stand")
        row = box1.column_flow(columns=2, align=True)
        row.prop(kp_tool_q3tokp, "ui_stand_tg_idle")  # stand_tg_idle
        row.prop(kp_tool_q3tokp, "ui_stand_attack")  # tg, pipe, pistol
        row.prop(kp_tool_q3tokp, "ui_stand_p_idle")
        row.prop(kp_tool_q3tokp, "ui_stand_taunt")  # stand_taunt
        row.prop(kp_tool_q3tokp, "ui_stand_ma_idle")  # stand_ma_idle
        row.prop(kp_tool_q3tokp, "ui_stand_ladder")  # clmb_loop_
        row = box1.row()
        row.prop(kp_tool_q3tokp, "ui_stand_jump_anim")  # jump animation

        # CROUCH
        box2 = layout.box()
        row = box2.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="Leg Anims: Crouch")
        row = box2.column_flow(columns=2, align=True)
        row.prop(kp_tool_q3tokp, "ui_crouch_idle")  # crouch_idle
        row.prop(kp_tool_q3tokp, "ui_crouch_shoot")  # crouch_shoot
        row = box2.row()
        row.prop(kp_tool_q3tokp, "ui_cr_death_anim")  # death anim animation

        # RUN SIDEWAYS
        box3 = layout.box()
        row = box3.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="Legs Run Sideways: Angle")
        row = box3.column_flow(columns=2, align=True)
        row.prop(kp_tool_q3tokp, "ui_rotate_leg_left")  # left leg angle
        row.prop(kp_tool_q3tokp, "ui_rotate_leg_right")  # right leg angle

        # MISC
        box4 = layout.box()
        row = box4.column_flow(columns=1, align=True)
        row.prop(kp_tool_q3tokp, "ui_ladder_anim")  # death anim animation
        row.prop(kp_tool_q3tokp, "ui_scale")  # scale
        row.prop(kp_tool_q3tokp, "ui_use_framerate_for_death")  # Match Death FPS
        row.prop(kp_tool_q3tokp, "ui_add_timeline")  # timeline names
        # set_layout_separator(col, factor=0.3)

        row = layout.row(align=True)
        # file/folder string
        col1 = row.column()
        col1.alignment = 'EXPAND'
        col1.enabled = False  # input box (no edit)
        col1.prop(kp_tool_q3tokp, "ui_path_cfg_file")
        # folder button
        col2 = row.column()
        col2.alignment = 'RIGHT'
        col2.operator("kp.ui_btn_get_cfg_file", icon='FILE_FOLDER', text="")  # file <Animation.cfg>

        row = layout.row()
        row.scale_y = 1.2
        row.alignment = 'CENTER'
        row.operator("kp.ui_btn_do_conversion")  # Convert to Kingpin
        row = layout.row()
        row.alignment = 'CENTER'
        row.operator("kp.ui_btn_info", text="Help...")  # Info


# button CONFIG
class KINGPIN_UI_BUTTON_CFG_File(Operator, kpc.KINGPIN_FileSelect_q3cfg_Params):
    ''' convert q3 config file button '''
    bl_idname = "kp.ui_btn_get_cfg_file"
    bl_label = "Animation.cfg"
    bl_description = "Open a Quake3 animation config file.\n"
    filename_ext = "cfg"

    def execute(self, context):
        f_path = Path(self.filepath)
        if f_path.exists():
            kp_q3tokp_ = context.window_manager.kp_q3tokp_
            kp_q3tokp_.ui_path_cfg_file = self.filepath  # directory
        else:
            self.report(type={"WARNING"}, message="File not found")
        return{'FINISHED'}

    def invoke(self, context, event):
        kp_q3tokp_ = context.window_manager.kp_q3tokp_
        self.filepath = kp_q3tokp_.ui_path_cfg_file  # read existing
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class Quake3_to_Kingpin:
    """ moved from operator self """
    Frames_KP = namedtuple('Frames_KP', ['start', 'end', 'legs', 'body', 'name'])

    array_kp_Anims = [
        Frames_KP(0, 31, Q3_Seq.LEGS_IDLE, Q3_Seq.TORSO_STAND, "tgun_rdy_32"),       # 0  tgun_rdy_       1st frame
        Frames_KP(32, 36, Q3_Seq.LEGS_IDLE, Q3_Seq.TORSO_ATTACK, "tg_shoot_05"),     # tg_shoot_
        Frames_KP(37, 46, Q3_Seq.LEGS_IDLE, Q3_Seq.TORSO_GESTURE, "tg_bird_10"),    # tg_bird_
        Frames_KP(47, 62, Q3_Seq.LEGS_IDLE, Q3_Seq.TORSO_GESTURE, "tg_crch_grab_16"),    # tg_crch_grab_
        Frames_KP(63, 77, Q3_Seq.LEGS_IDLE, Q3_Seq.TORSO_GESTURE, "tg_chin_flip_15"),    # tg_chin_flip_
        Frames_KP(78, 100, Q3_Seq.LEGS_IDLE, Q3_Seq.TORSO_STAND, "1pstl_rdy_23"),     # 1pstl_rdy_ 1st frame. pist
        Frames_KP(101, 104, Q3_Seq.LEGS_IDLE, Q3_Seq.TORSO_ATTACK, "p_std_shoot_04"),   # p_std_shoot_
        Frames_KP(105, 114, Q3_Seq.LEGS_WALK, Q3_Seq.TORSO_STAND, "walk_gdown_10"),    # walk_gdown_
        Frames_KP(115, 124, Q3_Seq.LEGS_WALK, Q3_Seq.TORSO_ATTACK, "walk_tg_sht_10"),   # walk_tg_sht_
        Frames_KP(125, 130, Q3_Seq.LEGS_RUN, Q3_Seq.TORSO_ATTACK, "run_tg_sht_06"),    # run_tg_sht_
        Frames_KP(131, 136, Q3_Seq.LEGS_RUN, Q3_Seq.TORSO_STAND, "rsd_tg_run_06"),      # 10 rsd_tg_run_
        Frames_KP(137, 142, Q3_Seq.LEGS_RUN, Q3_Seq.TORSO_STAND, "lsd_tg_run_06"),      # lsd_tg_run_
        Frames_KP(143, 152, Q3_Seq.LEGS_WALK, Q3_Seq.TORSO_ATTACK, "p_walk_sht_10"),    # p_walk_sht_   pistol
        Frames_KP(153, 158, Q3_Seq.LEGS_RUN, Q3_Seq.TORSO_ATTACK, "p_run_shoot_06"),     # p_run_shoot_  pistol
        Frames_KP(159, 164, Q3_Seq.LEGS_RUN, Q3_Seq.TORSO_STAND, "p_rside_run_06"),      # p_rside_run_  *missing*
        Frames_KP(165, 170, Q3_Seq.LEGS_RUN, Q3_Seq.TORSO_STAND, "p_lside_run_06"),      # p_lside_run_  *missing*
        Frames_KP(171, 189, Q3_Seq.LEGS_IDLE, Q3_Seq.TORSO_STAND2, "melee_rdy_19"),    # melee_rdy_    1st frame
        Frames_KP(190, 196, Q3_Seq.LEGS_IDLE, Q3_Seq.TORSO_ATTACK2, "melee3_07"),   # melee1_
        Frames_KP(197, 202, Q3_Seq.LEGS_IDLE, Q3_Seq.TORSO_ATTACK2, "melee4_06"),   # melee2_
        Frames_KP(203, 208, Q3_Seq.LEGS_RUN, Q3_Seq.TORSO_ATTACK2, "run_melee_06"),    # run_melee_    //check
        Frames_KP(209, 214, Q3_Seq.LEGS_RUN, Q3_Seq.TORSO_STAND, "run_gun_dn_06"),      # 20 run_gun_dn_
        Frames_KP(215, 221, Q3_Seq.LEGS_JUMPA, Q3_Seq.TORSO_STAND, "jump_07"),    # jump_       1st frame
        Frames_KP(222, 230, Q3_Seq.LEGS_TURN, Q3_Seq.TORSO_STAND, "clmb_loop_09"),     # clmb_loop_  *missing*
        Frames_KP(231, 249, Q3_Seq.BOTH_DEATH1, Q3_Seq.BOTH_DEATH1, "death1_19"),   # death1_    19 frames
        Frames_KP(250, 265, Q3_Seq.BOTH_DEATH2, Q3_Seq.BOTH_DEATH2, "death2_16"),   # death2_   16 frames
        Frames_KP(266, 293, Q3_Seq.BOTH_DEATH3, Q3_Seq.BOTH_DEATH3, "death3_28"),   # death3_   28 frames
        Frames_KP(294, 306, Q3_Seq.BOTH_DEATH1, Q3_Seq.BOTH_DEATH1, "death4_13"),   # death4_   13 frames
        Frames_KP(307, 333, Q3_Seq.LEGS_IDLECR, Q3_Seq.TORSO_STAND, "tg_crch_rdy_27"),   # tg_crch_rdy_
        Frames_KP(334, 339, Q3_Seq.LEGS_IDLECR, Q3_Seq.TORSO_ATTACK, "crouch_shoot_06"),  # crouch_shoot_
        Frames_KP(340, 344, Q3_Seq.LEGS_WALKCR, Q3_Seq.TORSO_STAND, "crch_shuf_05"),   # crch_walk_
        Frames_KP(345, 362, Q3_Seq.LEGS_IDLECR, Q3_Seq.TORSO_STAND, "1p_crch_rdy_18"),   # 30 1p_crch_rdy_  pistol
        Frames_KP(363, 367, Q3_Seq.LEGS_IDLECR, Q3_Seq.TORSO_ATTACK, "p_crch_sht_05"),  # p_crch_sht_   pistol
        Frames_KP(368, 373, Q3_Seq.LEGS_WALKCR, Q3_Seq.TORSO_ATTACK, "p_crch_walk_06"),  # p_crch_walk_  1st frame
        Frames_KP(374, 385, Q3_Seq.BOTH_DEATH1, Q3_Seq.BOTH_DEATH1, "crouch_death_12"),   # crouch_death_ *missing*
    ]

    def __init__(self):
        self.Q3_Anims = []
        self.array_legs = []
        self.array_body = []
        self.array_head = []
        self.array_weap = []
        self.tag_body_nodeID = None
        self.tag_head_nodeID = None
        self.tag_wep_nodeID = None
        self.tag_flash_nodeID = None

        self.obj_out = []  # store new objects, regroup after conversion
        self.obj_visable = [] # bpy.context.visible_objects  # store objedcts
    # END __init__

    def add_timeline_fn(self):
        mark = bpy.context.scene.timeline_markers
        mark.clear()
        for aniset_kp in self.array_kp_Anims:
            mark.new(aniset_kp.name, frame=aniset_kp.start)
    # END add_timeline_fn():

    def addObjectsToCollection(self):
        # set scens/collection
        sceneName = "KP_combined"
        if kpc.check_version(2, 80, 0) < 0:
            collection_new = bpy.data.scenes.new(sceneName)
            bpy.context.screen.scene = collection_new
        else:
            # collection_q3 = bpy.data.collections
            collection_new = bpy.data.collections.new(sceneName)
            bpy.context.scene.collection.children.link(collection_new)
            col = bpy.context.view_layer.layer_collection.children[collection_new.name]
            bpy.context.view_layer.active_layer_collection = col

        # move to collection 'KP_combined'
        for obj in self.obj_out:
            kpc.set_obj_group(obj[0], new_group=collection_new)
        return 1 #self.var1 + self.var2
    # END addObjectsToCollection

    ##################
    #  MAIN FUNCTION
    ##################
    def doConversion_fn(self, context, key_prop):
        """ convert to kingpin """
        def moveChild_mesh_fn(grouped_md3_f, body_part_f, parent_f, snap_f):
            if parent_f is None:
                return
            for child, ob_type in grouped_md3_f:
                if ob_type != body_part_f:
                    continue
                if child.name[:7] == "KP_tag_":
                    continue
                child.parent = parent_f
                if snap_f:
                    child.location = (0, 0, 0)  # parent_f.location.copy()
                    child.rotation_quaternion = (1, 0, 0, 0)  # parent_f.rotation_quaternion.copy()
                else:
                    child.matrix_parent_inverse = parent_f.matrix_world.inverted()
        # END moveChild_mesh_fn

        def moveChild_tag_fn(child_f, parent_f, keepPos_f):
            if parent_f is None or child_f is None:
                return
            child_f.parent = parent_f
            if keepPos_f:
                child_f.matrix_parent_inverse = parent_f.matrix_world.inverted()
        # END moveChild_tag_fn

        def addScaleObj_fn():
            """ add parent, for scale """
            bpy.ops.object.empty_add(type='CUBE')
            retObj = context.selected_objects[0]
            if not retObj:
                raise ValueError("Could not get selection(cube)")
            retObj.name = "KP_scale"
            retObj.location = (0, 0, -24)
            retObj.scale = (key_prop.ui_scale, key_prop.ui_scale, key_prop.ui_scale)
            kpc.update_matrices(retObj)
            kpc.set_select_state(retObj, False)  # deselect object
            return retObj
        # END addScaleObj_fn

        # grop objects
        def setupObjectsAsGroups_fn():
            # move tags to top of array
            def move_tagToTop(array_, tag_name):
                tag_items = [item for item in array_ if item.name.startswith(tag_name)]
                mesh_items = [item for item in array_ if not item.name.startswith(tag_name)]
                # Combine them with tag items at the top
                array_ = tag_items + mesh_items
                return array_
            # end move_tagToTop

            for obj in self.obj_visable:
                if not obj.type == 'MESH' and not obj.type == 'EMPTY':
                    continue

                obj_name = obj.name  # "tag_torso.low"
                prefix = obj_name.split("_", 1)[0] + "_"
                suffix = obj_name.split(".", 1)[-1]

                # asigne each part to a group. eg.. tag_torso to group_body
                # TODO remove unused tags
                if prefix == "tag_":
                    discard = True
                    if obj_name.startswith("tag_torso"):
                        if suffix.startswith("low"):       # .low
                            self.array_legs.append(obj)
                            discard = False
                    elif obj_name.startswith("tag_head"):
                        if suffix.startswith("upp"):       # .upp
                            self.array_head.append(obj)
                            discard = False
                    elif obj_name.startswith("tag_weapon"):
                        if suffix.startswith("upp"):       # .upp
                            self.array_body.append(obj)
                            discard = False
                    elif obj_name.startswith("tag_flash"):
                        # if suffix[9:13] == ".sho":       # note only 1
                        self.array_weap.append(obj)
                        discard = False
                    if discard:
                        print("%-14s %s" % ("Discard tag:", obj_name))
                        continue
                #  end tag asigments
                elif prefix == "l_":
                    self.array_legs.append(obj)
                elif prefix == "u_":
                    self.array_body.append(obj)
                elif prefix == "h_":
                    self.array_head.append(obj)
                elif prefix == "w_":
                    self.array_weap.append(obj)
                else:
                    print("%-14s %s" % ("Discard object:", obj_name))
                    continue

                print("%-14s %s" % ("added object:", obj_name))
            #  end adding each mesh object to array

            # sort list
            self.array_head = move_tagToTop(self.array_head, "tag_head")
            self.array_legs = move_tagToTop(self.array_legs, "tag_torso")
            self.array_body = move_tagToTop(self.array_body, "tag_weapon")
            self.array_weap = move_tagToTop(self.array_weap, "tag_flash")

            print("---- Finished Grouping items -----")
        # end setupObjectsAsGroups_fn

        # adjust keyframes
        def moveModelKeys_fn(context, grouped_md3_f, body_part_f):

            # key frame XYZ legs (no parent) 'tag_'
            def set_key_tag_fn(targetObj_f, time_kp_f, time_q3_f, fCurveArray):
                anim = targetObj_f.animation_data
                for i, fcu in enumerate(kpc.fcurves_iter(anim.action)):  #b44+
                    fcu_pt = fcu.keyframe_points
                    fcu_pt.add(1)
                    fcu_pt_id = fcu_pt[-1]
                    fcu_pt_id.co = (time_kp_f, fCurveArray[i][time_q3_f])
                    fcu_pt_id.interpolation = 'LINEAR'
                    fcu.update()

            def set_key_mesh_fn(targetObj_f, time_kp_f, time_q3_f):
                obj_sk = targetObj_f.data.shape_keys
                # note: 2.7 is buggy when you press Re-Time Shape Keys (+ 10)
                off = 1 #if kpc.check_version(2,8, 0) >= 0 else 1
                obj_sk.eval_time = (time_q3_f + off) * 10  # +10. dont use base key (causes coruption)
                obj_sk.keyframe_insert(data_path='eval_time', frame=time_kp_f)

            def evalTime_pos_fn(obj, time):
                anim = obj.animation_data
                pos = [0, 0, 0]
                for i, fcu in enumerate(kpc.fcurves_iter(anim.action)):  #b44+
                    pos[i] = fcu.evaluate(time)
                    if i == 2:
                        break
                return Vector((pos[0], pos[1], pos[2]))

            def IsDeathFrame_fn(anim_idx):
                if (key_prop.ui_use_framerate_for_death and
                    anim_idx in (
                        KP_Seq.DEATH1,
                        KP_Seq.DEATH2,
                        KP_Seq.DEATH3,
                        KP_Seq.DEATH4,
                        KP_Seq.CR_DEATH1)):
                    return True
                return False

            #  stop legs moving if checkboxes un-ticked and frame id match
            def IsSingleFrame_fn(anim_idx):
                if (not key_prop.ui_stand_ladder and anim_idx == KP_Seq.LADR):
                    return True     # clmb_loop_
                if (not key_prop.ui_stand_tg_idle and anim_idx == KP_Seq.TG_RDY):
                    return True     # tgun_rdy_
                if (not key_prop.ui_stand_p_idle and anim_idx == KP_Seq.P_RDY):
                    return True     # 1pstl_rdy_
                if (not key_prop.ui_stand_ma_idle and anim_idx == KP_Seq.M_RDY):
                    return True     # melee_rdy_

                if (not key_prop.ui_stand_attack and
                    anim_idx in (
                        KP_Seq.TG_SHOOT,  # tg_shoot_
                        KP_Seq.P_SHOOT,   # p_std_shoot_
                        KP_Seq.M_HIT1,    # melee1_
                        KP_Seq.M_HIT2)):  # melee2_
                    return True

                if (not key_prop.ui_crouch_shoot and
                    anim_idx in (
                        KP_Seq.TG_CR_SHOOT,   # crouch_shoot_
                        KP_Seq.P_CR_SHOOT)):  # p_crch_sht_
                    return True

                if (not key_prop.ui_crouch_idle and
                    anim_idx in (
                        KP_Seq.TG_CR_RDY,   # tg_crch_rdy_
                        KP_Seq.P_CR_RDY)):  # 1p_crch_rdy_
                    return True

                if (not key_prop.ui_stand_taunt and
                    anim_idx in (
                        KP_Seq.TG_TAUNT1,    # tg_bird_
                        KP_Seq.TG_TAUNT2,    # tg_crch_grab_
                        KP_Seq.TG_TAUNT3)):  # tg_chin_flip_
                    return True

                return False

            def rotMatrix4(ob, tag_pos_f, angle_f):
                """ https://blender.stackexchange.com/a/194802 """
                angle = radians(angle_f)
                axis = (0, 0, 1)
                mat_loc1 = Matrix.Translation(tag_pos_f)
                mat_rot = Matrix.Rotation(angle, 4, axis)  # 'Z')
                mat_loc2 = Matrix.Translation(-tag_pos_f)
                if kpc.check_version(2, 80, 0) < 0:
                    ob.matrix_world = mat_loc1 * mat_rot * mat_loc2 * ob.matrix_world
                else:
                    ob.matrix_world = mat_loc1 @ mat_rot @ mat_loc2 @ ob.matrix_world

            # clone object. copy() is failing, linked data
            def cloneObject_fn(context, obj):
                kpc.set_select_state(obj, True)  # select object
                bpy.ops.object.duplicate(linked=False)  # clone object
                retObj = context.selected_objects[0]  # get new onject
                if not retObj:
                    raise ValueError("Could not get selection")
                kpc.set_select_state(retObj, False)  # deselect object
                if retObj.data.shape_keys:
                    retObj.active_shape_key_index = 0
                return retObj

            def tag_getName_setNodeID(tempname):
                if body_part_f == mdl_sec.LEGS:  # leg->torso
                    if srcName.startswith("tag_torso"):
                        tempname += "_InLegs"
                        self.tag_body_nodeID = targetObj
                elif body_part_f == mdl_sec.BODY:
                    if srcName.startswith("tag_weap"):  # body->weapon
                        tempname += "_InBody_"
                        self.tag_wep_nodeID = targetObj
                elif body_part_f == mdl_sec.HEAD:
                    if srcName.startswith("tag_head"):  # body->head
                        tempname += "_InBody_"
                        self.tag_head_nodeID = targetObj
                elif body_part_f == mdl_sec.WEPS:
                    if srcName.startswith("tag_flash"):  # weap->flash
                        tempname += "_InWeap_"
                        self.tag_flash_nodeID = targetObj
                return tempname

            def tag_newAction(anim, fCurveArray):
                anim.action = anim.action.copy()
                anim_fcurves = kpc.fcurves_get(anim.action)  #b44+
                for fcu in anim_fcurves: #anim.action.fcurves:
                    tmp = []
                    # store q3 keyframes
                    for kf in fcu.keyframe_points:
                        tmp.append(kf.co[1])  # (kf.co[0],
                    fCurveArray.append(tmp)
                    # wipe keyframes
                    for i in reversed(range(0, len(fcu.keyframe_points))):
                        fcu.keyframe_points.remove(fcu.keyframe_points[i], fast=True)
                    fcu.update()

            def mesh_clearShapeKeys(targetObj):
                anim = targetObj.data.shape_keys.animation_data
                if anim is not None and anim.action is not None:
                    for fcu in kpc.fcurves_iter(anim.action):  #b44+
                        for i in reversed(range(0, len(fcu.keyframe_points))):
                            fcu.keyframe_points.remove(fcu.keyframe_points[i], fast=True)
                        fcu.update()

            def rotateLegs_fn(targetObj):
                # legs mesh
                # no_twist = (130, 143, 158, 171) #0-130, 143-158, 171-385
                twistR_timer = (131, 132, 133, 134, 135, 136,  # right 131-136
                                159, 160, 161, 162, 163, 164)  # right 159-164
                twistL_timer = (137, 138, 139, 140, 141, 142,  # left 137-142
                                165, 166, 167, 168, 169, 170)  # left 165-170
                angRight = 0 - key_prop.ui_rotate_leg_right  # math.radians
                angLeft = key_prop.ui_rotate_leg_left  # math.radians
                mesh_parent_ID = self.tag_body_nodeID

                # zero all frames first.
                for keyAt in range(130, 171+1):  # stand_timer:
                    targetObj.location = (0, 0, 0)
                    targetObj.rotation_mode = 'XYZ'
                    targetObj.rotation_euler = (0, 0, 0)
                    targetObj.keyframe_insert(data_path="location", frame=keyAt, group="legPos")
                    targetObj.keyframe_insert(data_path="rotation_euler", frame=keyAt, group="legRotate")

                # run right
                for keyAt in twistR_timer:
                    bpy.context.scene.frame_set(keyAt, subframe=0.0)
                    kpc.update_matrices(mesh_parent_ID)
                    rotMatrix4(targetObj, evalTime_pos_fn(mesh_parent_ID, keyAt), angRight)
                    targetObj.keyframe_insert(data_path="location", frame=keyAt, group="legPos")
                    targetObj.keyframe_insert(data_path="rotation_euler", frame=keyAt, group="legRotate")

                # run left
                for keyAt in twistL_timer:
                    bpy.context.scene.frame_set(keyAt, subframe=0.0)
                    kpc.update_matrices(mesh_parent_ID)
                    rotMatrix4(targetObj, evalTime_pos_fn(mesh_parent_ID, keyAt), angLeft)
                    targetObj.keyframe_insert(data_path="location", frame=keyAt, group="legPos")
                    targetObj.keyframe_insert(data_path="rotation_euler", frame=keyAt, group="legRotate")
            # END rotateLegs_fn()

            def updateMeshAnimation(targetObj):
                # update to linear
                if targetObj.data.shape_keys:
                    anim = targetObj.data.shape_keys.animation_data
                    for fcu in kpc.fcurves_iter(anim.action):  #b44+
                        for pt in fcu.keyframe_points:
                            pt.interpolation = 'LINEAR'
                        fcu.update()
                    # fix for kp using non integer frame placement
                    for sk in targetObj.data.shape_keys.key_blocks:
                        sk.interpolation = 'KEY_LINEAR'
                targetObj.data.update()
            # END updateMeshAnimation()

            # TODO add collection
            printPart = ["LEGS", "BODY", "HEAD", "WEPS"]
            namePart = ["legs_", "body_", "head_", ""]
            obj_total = len(grouped_md3_f)

            # ====================================== #
            #  loop through all grouped model parts
            # ====================================== #
            for objIdx, sourceObj in enumerate(grouped_md3_f):
                targetObj = None
                obj_isTag = 0
                fCurveArray = []
                srcName = sourceObj.name
                tagname = sourceObj.name[:4]

                print("Converting %s (%i/%i) %s" %
                    (printPart[body_part_f], objIdx + 1, obj_total, srcName))

                if tagname == "tag_":
                    #############
                    # tag object
                    #############
                    obj_isTag = 1

                    # duplicate model
                    targetObj = sourceObj.copy()
                    self.obj_out.append((targetObj, body_part_f))

                    # build name for new object.
                    # add tag for parenting
                    tempname = "KP_" + sourceObj.name
                    targetObj.name = tag_getName_setNodeID(tempname) #unique?

                    # shift fcurve keyframe
                    anim = targetObj.animation_data
                    if anim is not None and anim.action is not None:
                        tag_newAction(anim, fCurveArray) # targetObj.action = sourceObj.action.copy()
                    else:
                        print("Warning: no anim in tag (%s)" % (sourceObj.name))
                        obj_isTag = 2
                        # continue  # TODO. tag flash missing
                else:
                    ##############
                    # mesh object
                    ##############
                    # duplicate model
                    targetObj = cloneObject_fn(context, sourceObj)
                    self.obj_out.append((targetObj, body_part_f))
                    targetObj.name = namePart[body_part_f] + "KP_" + sourceObj.name + "_"  # uniqueName

                    # delete keyframes
                    if targetObj.data.shape_keys:
                        mesh_clearShapeKeys(targetObj)

                # ========================================= #
                #  loop through all kp animation sequences
                # ========================================= #
                for aniset_kp_idx, aniset_kp in enumerate(self.array_kp_Anims):
                    frames_total_q3 = 1
                    frameID_start_q3 = 0
                    modelIndex_q3 = aniset_kp.legs if body_part_f == mdl_sec.LEGS else aniset_kp.body
                    frames_fps_multiply_q3 = 1
                    IsUsingDeath_FPS = False

                    if not obj_isTag:
                        if (not targetObj.data or
                                not targetObj.data.shape_keys or
                                not targetObj.data.shape_keys.animation_data):
                            break
                    elif obj_isTag == 2:
                        break  # skip tag without anims(tag_flash)

                    #############
                    #   debug   #
                    # if not aniset_kp.start == 374:
                    #     continue
                    #############

                    frame_start_kp = float(aniset_kp.start)
                    frame_end_kp = aniset_kp.end
                    frames_total_kp = aniset_kp.end - aniset_kp.start + 1

                    frames_total_q3 = self.Q3_Anims[modelIndex_q3].total_fr
                    frameID_start_q3 = self.Q3_Anims[modelIndex_q3].start

                    #  check boxes for no leg animations
                    if body_part_f == mdl_sec.LEGS:
                        if IsSingleFrame_fn(aniset_kp_idx):
                            #  no idle animation for legs
                            frames_total_q3 = 1
                            frameID_start_q3 = self.Q3_Anims[modelIndex_q3].start

                    # death animation scale
                    if IsDeathFrame_fn(aniset_kp_idx):
                        # will scale death animation speeds to match frame rate in q3 file.
                        # copy a static frame to remaining animation set
                        q3_fr_time = 10.0 / float(self.Q3_Anims[modelIndex_q3].fps)
                        total_fps_Q3 = float(q3_fr_time) * frames_total_q3
                        if frames_total_kp > total_fps_Q3:
                            IsUsingDeath_FPS = True
                            frames_fps_multiply_q3 = q3_fr_time

                    # ========================================= #
                    #  get every q3 keyframe. paste to kp frame %0.f
                    #  make sure we have a start and end frame (0-1)
                    # do first to last frame (can be a single frame)
                    q3_total = frames_total_q3 - 1
                    for q3_key in range(frames_total_q3+1):
                        time_kp = 0
                        time_q3 = 0

                        if q3_key == 0:
                            # Q3 first frame
                            time_kp = frame_start_kp
                            time_q3 = frameID_start_q3
                        elif q3_key == 1 and frames_total_q3 == 1:
                            # Q3 only has 1 frame
                            time_kp = frame_end_kp
                            time_q3 = frameID_start_q3
                        elif q3_key == frames_total_q3:
                            # 1 extra frame. for death animations
                            if not IsUsingDeath_FPS:
                                break
                            time_kp = frame_end_kp
                            time_q3 = frameID_start_q3 + q3_total
                        elif q3_key <= q3_total:
                            if IsUsingDeath_FPS:
                                tween_fr = frames_fps_multiply_q3
                            else:
                                tween_fr = float(frames_total_kp - 1) / float(q3_total)
                            tween_fr *= q3_key
                            time_kp = frame_start_kp + tween_fr
                            time_q3 = frameID_start_q3 + q3_key
                        # end q3_keys setup

                        ###########################################
                        # start copying animation for each q3 frame
                        if obj_isTag == 1:
                            # fix for wrong animation.cfg. use last frame
                            time_q3 = min(time_q3, len(fCurveArray[0]) - 1)

                            # add key to tag_
                            set_key_tag_fn(targetObj, time_kp, time_q3, fCurveArray)
                        else:
                            if targetObj.data.shape_keys:
                                # add key to mesh
                                set_key_mesh_fn(targetObj, time_kp, time_q3)
                        # ==> END vertex animated mesh objects
                    # ==> END q3 animation set loop
                    ############
                    #   debug  #
                    # break    # <-- loop through only 1 animation
                    ############
                # ==> end kp animation set
                ##########################

                # legs to run side (sidestep)
                if self.tag_body_nodeID and body_part_f == mdl_sec.LEGS and obj_isTag == 0:
                    rotateLegs_fn(targetObj)

                # update mesh->data. linear
                if targetObj and targetObj.data:
                    updateMeshAnimation(targetObj)

            #  end loop through body parts
        # end moveModelKeys_fn

        if not bpy.context.mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')  # , toggle=False)

        self.obj_visable = list(bpy.context.visible_objects)  # store objedcts

        # deselect any objects
        for ob in bpy.data.objects:
            kpc.set_select_state(ob, False)

        try:
            setupObjectsAsGroups_fn()
            # animationrange = interval 0 390 # TODO
            moveModelKeys_fn(context, self.array_legs, mdl_sec.LEGS)
            moveModelKeys_fn(context, self.array_body, mdl_sec.BODY)
            moveModelKeys_fn(context, self.array_head, mdl_sec.HEAD)
            moveModelKeys_fn(context, self.array_weap, mdl_sec.WEPS)
            #  todo: tag flash??

            # move mesh to tag/parent then link. reversed
            moveChild_mesh_fn(self.obj_out, mdl_sec.WEPS, self.tag_wep_nodeID, True)
            moveChild_mesh_fn(self.obj_out, mdl_sec.HEAD, self.tag_head_nodeID, True)
            moveChild_mesh_fn(self.obj_out, mdl_sec.BODY, self.tag_body_nodeID, True)

            # move tag to tag/parent then link
            moveChild_tag_fn(self.tag_flash_nodeID, self.tag_wep_nodeID, False)  # move tag_flash to tag_wep
            moveChild_tag_fn(self.tag_wep_nodeID, self.tag_body_nodeID, False)  # move tag_wep to tag_body
            moveChild_tag_fn(self.tag_head_nodeID, self.tag_body_nodeID, False)  # move tag_head to tag_body

            # generate a null cube, so scale can be applied
            retObj = addScaleObj_fn()

            moveChild_mesh_fn(self.obj_out, mdl_sec.LEGS, retObj, False)
            moveChild_tag_fn(self.tag_body_nodeID, retObj, True)  # move tag_wep to tag_body

            # add cube to collection
            self.obj_out.append((retObj, mdl_sec.FLSH))

        except Exception as e:
            print("error: %s" % e)
            raise RuntimeError("ERROR: ") from e
    # END doConversion_fn

    ######################
    #  get animation.cfg
    def getAnimationFile_fn(self, key_prop):
        # read file

        def set_sorted_anim(kp_idx, val, body=True):
            if body:
                self.array_kp_Anims[kp_idx] = self.array_kp_Anims[kp_idx]._replace(body=val)
            self.array_kp_Anims[kp_idx] = self.array_kp_Anims[kp_idx]._replace(legs=val)

        def sortDeathAni_ByFrames_fn():
            # UI set animations
            set_sorted_anim(KP_Seq.CR_DEATH1, int(key_prop.ui_cr_death_anim))
            set_sorted_anim(KP_Seq.LADR, int(key_prop.ui_ladder_anim), body=False)

            set_sorted_anim(KP_Seq.JUMP, int(key_prop.ui_stand_jump_anim), body=False)

            # sort death animations by length (short to longest)
            listTime = [  # get frame time
                [self.Q3_Anims[Q3_Seq.BOTH_DEATH1].total_fr / self.Q3_Anims[Q3_Seq.BOTH_DEATH1].fps, Q3_Seq.BOTH_DEATH1],
                [self.Q3_Anims[Q3_Seq.BOTH_DEATH2].total_fr / self.Q3_Anims[Q3_Seq.BOTH_DEATH2].fps, Q3_Seq.BOTH_DEATH2],
                [self.Q3_Anims[Q3_Seq.BOTH_DEATH3].total_fr / self.Q3_Anims[Q3_Seq.BOTH_DEATH3].fps, Q3_Seq.BOTH_DEATH3]]
            listTime.sort(key=lambda x: x[0])
            set_sorted_anim(KP_Seq.DEATH1, listTime[1][1])  # 19 frames
            set_sorted_anim(KP_Seq.DEATH2, listTime[0][1])  # 16 frames
            set_sorted_anim(KP_Seq.DEATH3, listTime[2][1])  # 28 frames
            set_sorted_anim(KP_Seq.DEATH4, listTime[0][1])  # 13 frames
        # END sortDeathAni_ByFrames_fn

        # TODO get previous folder if missing? or show dialog box?
        fPath = key_prop.ui_path_cfg_file
        Frame_q3 = namedtuple('Frame_q3', ['start', 'total_fr', 'fps'])

        def read_cfg_file():
            ani_Index = 0  # as integer
            lineNum = 0
            offsetLegsTime = 0  # as integer

            def _get_cfg_values(parts):
                """ get 4 int values. return None if failed """
                result = []
                for i in range(4):
                    if i < len(parts) and parts[i].isdigit():
                        result.append(int(parts[i]))
                    else:
                        return [None, None, None, None]
                return result

            with open(file=fPath, mode="r", encoding="latin-1") as file: # "rt", "errors="replace")
                for line in file:
                    lineDelim = line.split()
                    lineNum += 1

                    frameStart, frameEnd, _, frameFPS = _get_cfg_values(lineDelim)
                    if frameStart is None:
                        # print("Warning: line#%i not int" % (lineNum)) #debug
                        continue

                    if frameFPS <= 0:
                        frameFPS = 15  # cant devide by zero
                    if frameEnd < 1:
                        frameEnd = 1  # just incase its zero

                    if ani_Index == Q3_Seq.LEGS_WALKCR:
                        offsetLeg = self.Q3_Anims[Q3_Seq.TORSO_GESTURE].start
                        print("leg offset1= %i" % (offsetLeg))
                        offsetLegsTime = frameStart - offsetLeg
                        print("leg offset2= %i" % (offsetLegsTime))

                    # leg animations start at torso start frame # very odd...
                    if ani_Index >= Q3_Seq.LEGS_WALKCR:
                        frameStart -= offsetLegsTime

                    self.Q3_Anims.append(
                        Frame_q3(start=frameStart, total_fr=frameEnd, fps=frameFPS))

                    if ani_Index > Q3_Seq.LEGS_TURN:
                        print("*** File has to many animations ***")
                        break
                    ani_Index += 1
            #end with open

        try:
            read_cfg_file()
            print("Done reading animation.cfg")
        except Exception():
            print("ERROR: reading animation.cfg")
            return 0

        #debug
        # for i, li in enumerate(self.Q3_Anims):
        #     print("Anim:%i start:%i end:%i" % (i+1, li.start, li.total_fr))


        if len(self.Q3_Anims) <= Q3_Seq.LEGS_TURN:
            print("ERROR: animation count to low")
            return 0

        # arange death by frame counts
        sortDeathAni_ByFrames_fn()
        return 1
    # END getAnimationFile_fn


# button CONVERT
class KINGPIN_UI_BUTTON_GO(Operator):
    ''' convert model '''
    bl_idname = "kp.ui_btn_do_conversion"
    bl_label = "Convert to Kingpin"
    bl_options = {'REGISTER'}
    bl_description = ("Creates new objects with name KP_*\n"
                      "Will search all non hidden items with names\n"
                      "tag_* \nL_* \nH_* \nU_* \nW_* ")

    def execute(self, context):
        '''convert q3 models to kp animations'''
        key_prop = context.window_manager.kp_q3tokp_

        # animation.cfg with 25 leg/body events (structure(start,end)
        # -self.Q3_Anims = []
        q3ToKp = Quake3_to_Kingpin()

        ###############
        # begin execute
        ###############
        # -self.obj_out = []  # store new objects, regroup after conversion
        # -self.obj_visable = list(bpy.context.visible_objects)  # store objedcts
        bpy.context.scene.frame_set(0)  # todo restore

        # read animation.cfg
        if not q3ToKp.getAnimationFile_fn(key_prop):
            self.report({'INFO'}, "ERROR: animation.cfg failed.")
            return {'FINISHED'}

        # start conversion
        q3ToKp.doConversion_fn(context, key_prop) # sortDeathAni_ByFrames_fn()
        q3ToKp.addObjectsToCollection()
        if key_prop.ui_add_timeline:
            q3ToKp.add_timeline_fn()

        bpy.context.scene.frame_end = 385
        bpy.context.scene.frame_set(0)  # todo restore

        return {'FINISHED'}
        # ==>END execute
    # END class KINGPIN_UI_BUTTON_GO


# button ABOUT
class KINGPIN_UI_BUTTON_ABOUT(Operator):
    """ q3 conversion info """
    bl_label = "Designed by hypov8. For kingpin."
    bl_idname = "kp.ui_btn_info"
    bl_description = "Info on how to use the converter"

    text = bpy.props.StringProperty(
        name="Enter Name",
        default=""
    )
    about_message = bpy.props.StringProperty(
        name="message",
        description="Help",
        default=(
            "-------------\n" +
            "Using the 'Quake 3 Model (.md3)-hy-' Import script(v0.4.4.2).\n" +
            "Import lower.md3, upper.md3, head.md3 and shotgun.md3.\n" +
            "Option: Select the Leg Idle animations type(static/animated)\n" +
            "Option: Change the leg rotation angles(for running sidways)\n" +
            "Option: Change Crouch Death anim to use stand death anim 1/2/3.\n" +
            "Option: Change Scale to match a kingpin player model size.\n" +
            "Press the 'Animation.cfg' folder Button.\n" +
            "Select the .cfg file matching the imported Q3 models.\n" +
            "Hide any non Q3 scene objects.\n" +
            "Press the 'Convert to Kingpin' Button.\n" +
            "You can now export the head/body/legs models to Kingpin.\n"
            "Notes:\n" +
            "  Animation.cfg may need tweeking to get the animations correct.\n" +
            "  Death animations order are used based on time, to suit KP.\n" +
            # "BOTH_DEATH1 is also used for crouch death. This should be the shortest animation.\n" +
            "-------------"
        )
    )

    def execute(self, context):
        self.report({'INFO'}, self.about_message)
        print(self.about_message)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=520)

    def draw(self, context):
        strArray = self.about_message.split("\n")
        for s in strArray:
            self.layout.label(text=s)
        # self.layout.label(text=self.msg)


classes = (
    # KINGPIN_Q3toKP_props,  # toolbar
    KINGPIN_UI_BUTTON_CFG_File,
    KINGPIN_UI_BUTTON_GO,
    KINGPIN_UI_BUTTON_ABOUT,
    KINGPIN_PT_Q3_to_KP_GUI
)


def register():
    for cls in classes:
        kpc.make_annotations(cls)  # v1.2.2
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
