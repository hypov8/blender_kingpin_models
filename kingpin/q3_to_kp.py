
# from ast import excepthandler
# from inspect import getfile
# from logging import exception
# from tkinter import EXCEPTION
from ast import ExceptHandler  # , Try, excepthandler
# from distutils.log import error
# from logging import raiseExceptions
# from posixpath import split
# from xml.dom.pulldom import ErrorHandler
import bpy
from bpy.types import (
    Operator,
    Panel,
    WindowManager,
    # AddonPreferences,
)

from bpy.props import (
    BoolProperty,
    StringProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    FloatProperty
)
# from bpy.app.handlers import persistent


from collections import namedtuple
from math import radians  # , pi, cos, sin

from mathutils import Vector, Matrix  # , Quaternion, Euler
# from typing import List

from .common_kp import (
    make_annotations,
    set_select_state,
    # get_objects_all,
    set_obj_group,
    update_matrices
)


# Property DEFINITIONS
class KINGPIN_Q3_to_KP_Properties(bpy.types.PropertyGroup):
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
            ('0', "BOTH_DEATH1", "Animation to use for crouch death", 0),
            ('2', "BOTH_DEATH2", "Animation to use for crouch death", 1),
            ('4', "BOTH_DEATH3", "Animation to use for crouch death", 2),
        ],
        default='0',
    )
    ############################
    # ladder anim. no equivalent
    ui_ladder_anim = EnumProperty(
        name="Ladder",
        description=("Ladder animation for legs."
                     "(No equivalent)"),
        items=[
            ('13', "LEGS_WALKCR", "Animation to use for ladder.\nWalking Crouched.\nDefault", 0),
            ('14', "LEGS_WALK", "Animation to use for ladder.\nWalking", 1),
            ('16', "LEGS_BACK", "Animation to use for ladder.\nRun backwards", 2),
            ('17', "LEGS_SWIM", "Animation to use for ladder.\nSwimming", 3),
            ('18', "LEGS_JUMP", "Animation to use for ladder.\nJumping. Type 1", 4),
            ('19', "LEGS_LAND", "Animation to use for ladder.\nLanding. Type 1", 5),
            ('20', "LEGS_JUMPB", "Animation to use for ladder.\nJumping. Type 2", 6),
            ('21', "LEGS_LANDB", "Animation to use for ladder.\nLanding. Type 2", 7),
            ('22', "LEGS_IDLE", "Animation to use for ladder.\nIdling", 8),
            ('23', "LEGS_IDLECR", "Animation to use for ladder.\nIdle Crouch", 9),
            ('24', "LEGS_TURN", "Animation to use for ladder.\nTurn on spot", 10),
        ],
        default='13',
    )
    ''' LEGS_WALKCR = 13
        LEGS_WALK = 14
        LEGS_RUN = 15
        LEGS_BACK = 16
        LEGS_SWIM = 17
        LEGS_JUMP = 18
        LEGS_LAND = 19
        LEGS_JUMPB = 20
        LEGS_LANDB = 21
        LEGS_IDLE = 22
        LEGS_IDLECR = 23
        LEGS_TURN = 24'''
    ############################
    # group "Run Sideways Angle"
    ui_rotate_leg_left = IntProperty(
        name="Left",
        description="Angle to rotate legs while running left.",
        # subtype='ANGLE',
        min=0,
        max=120,
        default=35
    )
    ui_rotate_leg_right = IntProperty(
        name="Right",
        description="Angle to rotate legs while running right.",
        min=0,
        max=120,
        default=35
    )
    #######
    # scale
    ui_scale = FloatProperty(
        name="Model Scale",
        description="Scale model to suit kingpin.",
        min=0.5,
        max=5,
        precision=2,
        default=1.4
    )
    ###################
    # match death anims
    ui_use_framerate_for_death = BoolProperty(
        name="Match Death FPS",
        description="Enable: Animations Speed/FPS match Q3\n" +
                    "  This will place empty frames at end of death sequence\n" +
                    "Disable: Will squeeze/stretch animation to fit into kp timeline",
        default=True,
    )
    # add timeline names
    ui_add_timeline = BoolProperty(
        name="Add Timeline Names",
        description="Add timeline frame names\nNote: this wipes existing frame name data.",
        default=True,
    )
    ############
    # file input
    ui_btn_getfile = StringProperty(
        name="Animation.cfg",
        description="Get frame sequence for conversion",
        default="D:/Quake3/baseq3/models/players/bones/animation.cfg",  # todo
        maxlen=1024,
        options={'HIDDEN'},
        subtype='FILE_PATH'  # 'DIR_PATH')
    )
    filter_glob = StringProperty(
        default="*.cfg",
        options={'HIDDEN'},
    )


# GUI
class VIEW3D_PT_Q3_to_KP_GUI(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS' if bpy.app.version < (2, 80, 0) else 'UI'
    bl_category = 'Kingpin'
    bl_label = 'QUAKE3 to KP'
    bl_options = {'DEFAULT_CLOSED'}
    # bl_options = {'HEADER_LAYOUT_EXPAND'}
    #  UI

    def draw(self, context):
        kp_tool_q3tokp = context.window_manager.kp_tool_q3tokp
        # context.window_manager.kp_tool_q3tokp
        layout = self.layout
        col = layout.column(align=True)

        # group "No Leg Animation For.."
        # box = col.box()
        # row = box.row()  # align=True #
        row = col.row()
        row.alignment = 'CENTER'  # 'EXPAND'
        row.label(text="Legs Anims: Stand")
        # STANDING
        row = col.row()
        row.prop(kp_tool_q3tokp, "ui_stand_tg_idle")  # stand_tg_idle
        row.prop(kp_tool_q3tokp, "ui_stand_attack")  # tg, pipe, pistol
        row = col.row()
        row.prop(kp_tool_q3tokp, "ui_stand_p_idle")
        row.prop(kp_tool_q3tokp, "ui_stand_taunt")  # stand_taunt
        row = col.row()
        row.prop(kp_tool_q3tokp, "ui_stand_ma_idle")  # stand_ma_idle
        row.prop(kp_tool_q3tokp, "ui_stand_ladder")  # clmb_loop_

        # CROUCH
        row = col.row()
        row.alignment = 'CENTER'
        row.label(text="Legs Anims: Crouch")
        row = col.row()
        row.prop(kp_tool_q3tokp, "ui_crouch_idle")  # crouch_idle
        row.prop(kp_tool_q3tokp, "ui_crouch_shoot")  # crouch_shoot
        row = col.row()
        row.prop(kp_tool_q3tokp, "ui_cr_death_anim")  # death anim animation
        row = col.row()
        row.prop(kp_tool_q3tokp, "ui_ladder_anim")  # death anim animation

        row = col.row()
        row.alignment = 'CENTER'
        row.label(text="Run Sideways: Angle")
        row = col.row(align=False)
        row.prop(kp_tool_q3tokp, "ui_rotate_leg_left")  # left leg angle
        row.prop(kp_tool_q3tokp, "ui_rotate_leg_right")  # right leg angle

        row = col.row()
        row.prop(kp_tool_q3tokp, "ui_scale")  # scale

        row = col.row()
        row.prop(kp_tool_q3tokp, "ui_use_framerate_for_death")  # Match Death FPS
        row = col.row()
        row.prop(kp_tool_q3tokp, "ui_add_timeline")  # timeline names
        row = col.row()
        row.prop(kp_tool_q3tokp, "ui_btn_getfile", text="")  # file <Animation.cfg>
        row = col.row()
        row.scale_y = 1.2
        row.alignment = 'CENTER'
        row.operator("kp.ui_btn_do_conversion")  # Convert to Kingpin
        row = col.row()
        row.alignment = 'CENTER'
        row.operator("kp.ui_btn_info", text="Help...")  # Info


# button CONFIG
class KINGPIN_UI_BUTTON_CFG_File(Operator):
    # ui_btn_getfile             "Animation.cfg "         align:#centre     height:22 width:136 tooltip:"select file"
    bl_idname = "kp.ui_btn_getfile"
    bl_label = "Animation.cfg"
    bl_description = ("Enable: Animations Speed/FPS match Q3\nThis wil place enpty frames at end\n"
                      "Disable: Will squeeze/stretch animation to fit into kp timeline")
    filename_ext = "cfg"
    filter_glob = StringProperty(
        default="*.cfg",
        options={'HIDDEN'},  # TODO
    )

    def execute(self, context):
        key_prop = context.window_manager.kp_tool_q3tokp
        # fdir = self.properties.filepath
        # context.scene.my_addon.some_identifier = fdir
        return{'FINISHED'}


# button CONVERT
class KINGPIN_UI_BUTTON_GO(Operator):
    # UI_btn_DoConversion     "Convert to Kingpin"     align:#centre     height:22 width:136 tooltip:string_Tip_GO
    bl_idname = "kp.ui_btn_do_conversion"
    bl_label = "Convert to Kingpin"
    bl_description = ("Creates new objects with name KP_*\n"
                      "Will search all non hidden items with names\ntag_* \nL_* \nH_* \nU_* \nW_* ")

    def execute(self, context):
        '''convert q3 models to kp animations'''
        key_prop = context.window_manager.kp_tool_q3tokp
        # key_prop = WindowManager.kp_tool_q3tokp

        # animation.cfg with 25 leg/body events (structure(start,end)
        self.Q3_Anims = []
        array_legs = []
        array_body = []
        array_head = []
        array_wep = []

        #  q3 animation file indexed names
        BOTH_DEATH1 = 0
        BOTH_DEAD1 = 1
        BOTH_DEATH2 = 2
        BOTH_DEAD2 = 3
        BOTH_DEATH3 = 4
        BOTH_DEAD3 = 5
        TORSO_GESTURE = 6
        TORSO_ATTACK = 7
        TORSO_ATTACK2 = 8
        TORSO_DROP = 9
        TORSO_RAISE = 10
        TORSO_STAND = 11
        TORSO_STAND2 = 12
        LEGS_WALKCR = 13
        LEGS_WALK = 14
        LEGS_RUN = 15
        LEGS_BACK = 16
        LEGS_SWIM = 17
        LEGS_JUMP = 18  # TODO alt option
        LEGS_LAND = 19
        LEGS_JUMPB = 20
        LEGS_LANDB = 21
        LEGS_IDLE = 22
        LEGS_IDLECR = 23
        LEGS_TURN = 24
        # BOTH_DEATH4 = 25  # hypo added for crouch
        # BOTH_DEAD4 = 26  # hypo added for crouch

        #  forward the body parts group for functions
        MODEL_LEGS = 0
        MODEL_BODY = 1
        MODEL_HEAD = 2
        MODEL_WEPS = 3
        MODEL_FLSH = 4

        # tag_legs_nodeID = None
        self.tag_body_nodeID = None
        self.tag_head_nodeID = None
        self.tag_wep_nodeID = None
        self.tag_flash_nodeID = None

        Frame_q3 = namedtuple('Frame_q3', ['start', 'total_fr', 'fps'])
        Frames_KP = namedtuple('Frames_KP', ['start', 'end', 'legs', 'body'])

        self.array_kp_Anims = [
            Frames_KP(0, 31, LEGS_IDLE, TORSO_STAND),    # 0  tgun_rdy_       1st frame
            Frames_KP(32, 36, LEGS_IDLE, TORSO_ATTACK),     # tg_shoot_
            Frames_KP(37, 46, LEGS_IDLE, TORSO_GESTURE),    # tg_bird_
            Frames_KP(47, 62, LEGS_IDLE, TORSO_GESTURE),    # tg_crch_grab_
            Frames_KP(63, 77, LEGS_IDLE, TORSO_GESTURE),    # tg_chin_flip_
            Frames_KP(78, 100, LEGS_IDLE, TORSO_STAND),     # 1pstl_rdy_ 1st frame. pist
            Frames_KP(101, 104, LEGS_IDLE, TORSO_ATTACK),   # p_std_shoot_
            Frames_KP(105, 114, LEGS_WALK, TORSO_STAND),    # walk_gdown_
            Frames_KP(115, 124, LEGS_WALK, TORSO_ATTACK),   # walk_tg_sht_
            Frames_KP(125, 130, LEGS_RUN, TORSO_ATTACK),    # run_tg_sht_
            Frames_KP(131, 136, LEGS_RUN, TORSO_STAND),   # 10 rsd_tg_run_
            Frames_KP(137, 142, LEGS_RUN, TORSO_STAND),      # lsd_tg_run_
            Frames_KP(143, 152, LEGS_WALK, TORSO_ATTACK),    # p_walk_sht_   pistol
            Frames_KP(153, 158, LEGS_RUN, TORSO_ATTACK),     # p_run_shoot_  pistol
            Frames_KP(159, 164, LEGS_RUN, TORSO_STAND),      # p_rside_run_  *missing*
            Frames_KP(165, 170, LEGS_RUN, TORSO_STAND),      # p_lside_run_  *missing*
            Frames_KP(171, 189, LEGS_IDLE, TORSO_STAND2),    # melee_rdy_    1st frame
            Frames_KP(190, 196, LEGS_IDLE, TORSO_ATTACK2),   # melee1_
            Frames_KP(197, 202, LEGS_IDLE, TORSO_ATTACK2),   # melee2_
            Frames_KP(203, 208, LEGS_RUN, TORSO_ATTACK2),    # run_melee_    //check
            Frames_KP(209, 214, LEGS_RUN, TORSO_STAND),   # 20 run_gun_dn_
            Frames_KP(215, 221, LEGS_JUMP, TORSO_STAND),       # jump_       1st frame
            Frames_KP(222, 230, LEGS_TURN, TORSO_STAND),       # clmb_loop_  *missing*
            Frames_KP(231, 249, BOTH_DEATH1, BOTH_DEATH1),     # death1_    19 frames
            Frames_KP(250, 265, BOTH_DEATH2, BOTH_DEATH2),     # death2_   16 frames
            Frames_KP(266, 293, BOTH_DEATH3, BOTH_DEATH3),     # death3_   28 frames
            Frames_KP(294, 306, BOTH_DEATH1, BOTH_DEATH1),     # death4_   13 frames
            Frames_KP(307, 333, LEGS_IDLECR, TORSO_STAND),     # tg_crch_rdy_
            Frames_KP(334, 339, LEGS_IDLECR, TORSO_ATTACK),    # crouch_shoot_
            Frames_KP(340, 344, LEGS_WALKCR, TORSO_STAND),     # crch_walk_
            Frames_KP(345, 362, LEGS_IDLECR, TORSO_STAND),  # 30 1p_crch_rdy_  pistol
            Frames_KP(363, 367, LEGS_IDLECR, TORSO_ATTACK),    # p_crch_sht_   pistol
            Frames_KP(368, 373, LEGS_WALKCR, TORSO_ATTACK),    # p_crch_walk_  1st frame
            Frames_KP(374, 385, BOTH_DEATH1, BOTH_DEATH1),     # crouch_death_ *missing*
        ]

        KP_00_TG_RDY = 0         # tgun_rdy_       1st frame
        KP_01_TG_SHOOT = 1       # tg_shoot_
        KP_02_TG_TAUNT1 = 2      # tg_bird_
        KP_03_TG_TAUNT2 = 3      # tg_crch_grab_
        KP_04_TG_TAUNT3 = 4      # tg_chin_flip_
        KP_05_P_RDY = 5          # 1pstl_rdy_ 1st frame. pist
        KP_06_P_SHOOT = 6        # p_std_shoot_
        KP_07_WALK = 7           # walk_gdown_
        KP_08_TG_WALK_SHOOT = 8  # walk_tg_sht_
        KP_09_TG_RUN_SHOOT = 9   # run_tg_sht_
        KP_10_TG_RUN_RIGHT = 10  # rsd_tg_run_
        KP_11_TG_RUN_LEFT = 11   # lsd_tg_run_
        KP_12_P_WALK_SHOOT = 12  # p_walk_sht_   pistol
        KP_13_P_RUN_SHOOT = 13   # p_run_shoot_  pistol
        KP_14_P_RUN_RIGHT = 14   # p_rside_run_  *missing*
        KP_15_P_RUN_LEFT = 15    # p_lside_run_  *missing*
        KP_16_M_RDY = 16         # melee_rdy_    1st frame
        KP_17_M_HIT1 = 17        # melee1_
        KP_18_M_HIT2 = 18        # melee2_
        KP_19_M_RUN = 19         # run_melee_    //check
        KP_20_RUN = 20           # run_gun_dn_
        KP_21_JUMP = 21          # jump_       1st frame
        KP_22_LADR = 22          # clmb_loop_  *missing*
        KP_23_DEATH1 = 23        # death1_    19 frames
        KP_24_DEATH2 = 24        # death2_   16 frames
        KP_25_DEATH3 = 25        # death3_   28 frames
        KP_26_DEATH4 = 26        # death4_   13 frames
        KP_27_TG_CR_RDY = 27     # tg_crch_rdy_
        KP_28_TG_CR_SHOOT = 28   # crouch_shoot_
        KP_29_CR_WALK = 29       # crch_walk_
        KP_30_P_CR_RDY = 30      # 1p_crch_rdy_  pistol
        KP_31_P_CR_SHOOT = 31    # p_crch_sht_   pistol
        KP_32_P_CR_WALK = 32     # p_crch_walk_  1st frame
        KP_33_CR_DEATH1 = 33     # crouch_death_ *missing*

        def swap(list, val1, val2):
            # TODO fix return
            list[val1], list[val2] = list[val2], list[val1]
            return list

        ##################
        #  MAIN FUNCTION
        ##################
        def moveModelKeys_fn(self, context, grouped_md3_f, body_part_f):

            # key frame XYZ legs (no parent) 'tag_'
            def set_key_tag_fn(targetObj_f, time_kp_f, time_q3_f, fCurveArray, fcur_idx_f):
                anim = targetObj_f.animation_data
                for i, fcu in enumerate(anim.action.fcurves):
                    fcu_pt = fcu.keyframe_points
                    fcu_pt.add(1)
                    fcu_pt_id = fcu_pt[fcur_idx_f]
                    fcu_pt_id.co = (time_kp_f, fCurveArray[i][time_q3_f])
                    fcu_pt_id.interpolation = 'LINEAR'
                    fcu.update()

            def set_key_mesh_fn(targetObj_f, time_kp_f, time_q3_f):
                obj_sk = targetObj_f.data.shape_keys
                # note: 2.7 is buggy when you press Re-Time Shape Keys (+ 10)
                obj_sk.eval_time = ((time_q3_f+1) * 10)  # +10. dont use base key (causes coruption)
                obj_sk.keyframe_insert(data_path='eval_time', frame=time_kp_f)

            def evalTime_pos_fn(obj, time):
                anim = obj.animation_data
                pos = [0, 0, 0]
                for i, fcu in enumerate(anim.action.fcurves):
                    pos[i] = fcu.evaluate(time)
                    if i == 2:
                        break
                return Vector((pos[0], pos[1], pos[2]))

            def IsDeathFrame_fn(anim_idx):
                if (key_prop.ui_use_framerate_for_death and
                    (anim_idx == KP_23_DEATH1 or
                     anim_idx == KP_24_DEATH2 or
                     anim_idx == KP_25_DEATH3 or
                     anim_idx == KP_26_DEATH4 or
                     anim_idx == KP_33_CR_DEATH1)):
                    return True
                return False

            #  stop legs moving if checkboxes un-ticked and frame id match
            def IsSingleFrame_fn(anim_idx):
                if (not key_prop.ui_stand_ladder and anim_idx == KP_22_LADR):
                    return True  # clmb_loop_
                if (not key_prop.ui_stand_tg_idle and anim_idx == KP_00_TG_RDY):
                    return True     # tgun_rdy_
                if (not key_prop.ui_stand_p_idle and anim_idx == KP_05_P_RDY):
                    return True     # 1pstl_rdy_
                if (not key_prop.ui_stand_ma_idle and anim_idx == KP_16_M_RDY):
                    return True      # melee_rdy_

                if (not key_prop.ui_stand_attack and
                    (anim_idx == KP_01_TG_SHOOT or  # tg_shoot_
                     anim_idx == KP_06_P_SHOOT or   # p_std_shoot_
                     anim_idx == KP_17_M_HIT1 or    # melee1_
                     anim_idx == KP_18_M_HIT2)):    # melee2_
                    return True

                if (not key_prop.ui_crouch_shoot and
                    (anim_idx == KP_28_TG_CR_SHOOT or     # crouch_shoot_
                     anim_idx == KP_31_P_CR_SHOOT)):     # p_crch_sht_
                    return True

                if (not key_prop.ui_crouch_idle and
                    (anim_idx == KP_27_TG_CR_RDY or     # tg_crch_rdy_
                     anim_idx == KP_30_P_CR_RDY)):     # 1p_crch_rdy_
                    return True

                if (not key_prop.ui_stand_taunt and
                    (anim_idx == KP_02_TG_TAUNT1 or   # tg_bird_
                     anim_idx == KP_03_TG_TAUNT2 or   # tg_crch_grab_
                     anim_idx == KP_04_TG_TAUNT3)):    # tg_chin_flip_
                    return True

                return False

            def rotMatrix4(obj_leg, tag_pos_f, angle_f):
                '''https://blender.stackexchange.com/a/194802'''
                angle = radians(angle_f)
                axis = (0, 0, 1)
                ob = obj_leg
                mat_loc1 = Matrix.Translation(tag_pos_f)
                mat_rot = Matrix.Rotation(angle, 4, axis)  # 'Z')
                mat_loc2 = Matrix.Translation(-tag_pos_f)
                if bpy.app.version < (2, 80, 0):
                    ob.matrix_world = mat_loc1 * mat_rot * mat_loc2 * ob.matrix_world
                else:
                    ob.matrix_world = mat_loc1 @ mat_rot @ mat_loc2 @ ob.matrix_world

            # clone object. copy() is failing, linked data
            def cloneObject_fn(context, obj):
                set_select_state(context=obj, opt=True)  # select object
                bpy.ops.object.duplicate(linked=False)  # clone object
                retObj = context.selected_objects[0]  # get new onject
                if not retObj:
                    raise Exception("Could not get selection")
                set_select_state(context=retObj, opt=False)  # deselect object
                if retObj.data.shape_keys:
                    retObj.active_shape_key_index = 0
                return retObj

            # TODO add collection
            printPart = ["LEGS", "BODY", "HEAD", "WEPS"]
            objIdx = 0
            obj_total = len(grouped_md3_f)

            # ====================================== #
            #  loop through all grouped model parts
            # ====================================== #
            for sourceObj in grouped_md3_f:
                targetObj = None
                objIdx += 1
                obj_isTag = 0
                srcName = sourceObj.name
                tagname = sourceObj.name[:4]

                print("Converting %s (%i/%i) %s" %
                      (printPart[body_part_f], objIdx, obj_total, srcName))

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
                    if body_part_f == MODEL_LEGS:  # leg->torso
                        if srcName[:9] == "tag_torso":
                            tempname += "_InLegs"
                            self.tag_body_nodeID = targetObj
                    elif body_part_f == MODEL_BODY:
                        if srcName[:8] == "tag_weap":  # body->weapon
                            tempname += "_InBody_"
                            self.tag_wep_nodeID = targetObj
                    elif body_part_f == MODEL_HEAD:
                        if srcName[:8] == "tag_head":  # body->head
                            tempname += "_InBody_"
                            self.tag_head_nodeID = targetObj
                    elif body_part_f == MODEL_WEPS:
                        if (srcName[:9] == "tag_flash"):  # weap->flash
                            tempname += "_InWeap_"
                            self.tag_flash_nodeID = targetObj

                    # targetObj.action = sourceObj.action.copy()  # TODO name + check exists?
                    targetObj.name = tempname

                    # shift fcurve keyframe
                    fCurveArray = []
                    anim = targetObj.animation_data
                    if anim is not None and anim.action is not None:
                        anim.action = anim.action.copy()
                        for fcu in anim.action.fcurves:
                            tmp = []
                            # store q3 keyframes
                            for v_i, kf in enumerate(fcu.keyframe_points):
                                tmp.append(kf.co[1])  # (kf.co[0],
                            fCurveArray.append(tmp)
                            # wipe keyframes
                            for i in reversed(range(0, len(fcu.keyframe_points))):
                                fcu.keyframe_points.remove(fcu.keyframe_points[i], fast=True)
                            fcu.update()
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
                    targetObj.name = "KP_" + sourceObj.name + "_"  # uniqueName

                    # delete keyframes
                    if targetObj.data.shape_keys:
                        anim = targetObj.data.shape_keys.animation_data
                        if anim is not None and anim.action is not None:
                            for fcu in anim.action.fcurves:
                                for i in reversed(range(0, len(fcu.keyframe_points))):
                                    fcu.keyframe_points.remove(fcu.keyframe_points[i], fast=True)
                                fcu.update()

                # ========================================= #
                #  loop through all kp animation sequences
                # ========================================= #
                fcur_idx = 0
                for aniset_kp_idx, aniset_kp in enumerate(self.array_kp_Anims):
                    # frames_total_kp, frame_start_kp, frame_end_kp
                    frames_total_q3 = 1
                    frameID_start_q3 = 0
                    modelIndex_q3 = 0
                    frames_fps_multiply_q3 = 1
                    IsUsingDeath_FPS = False

                    if body_part_f == MODEL_LEGS:
                        modelIndex_q3 = aniset_kp.legs
                    else:
                        modelIndex_q3 = aniset_kp.body

                    if not obj_isTag:
                        if (not targetObj.data or
                                not targetObj.data.shape_keys or
                                not targetObj.data.shape_keys.animation_data):
                            break
                    elif obj_isTag == 2:
                        break  # skip tag without anims(tag_flash)

                    #############
                    #   debug   #
                    # if not debugFrame_fn(aniset_kp_idx):
                    #    continue
                    #############

                    frame_start_kp = float(aniset_kp.start)
                    frame_end_kp = aniset_kp.end
                    frames_total_kp = ((aniset_kp.end + 1) - aniset_kp.start)

                    frames_total_q3 = self.Q3_Anims[modelIndex_q3].total_fr
                    frameID_start_q3 = self.Q3_Anims[modelIndex_q3].start

                    #  check boxes for no leg animations
                    if (body_part_f == MODEL_LEGS):
                        if (IsSingleFrame_fn(aniset_kp_idx)) is True:
                            #  no idle animation for legs
                            frames_total_q3 = 1
                            frameID_start_q3 = self.Q3_Anims[modelIndex_q3].start

                    # death animation scale
                    if (IsDeathFrame_fn(aniset_kp_idx)) is True:
                        # will scale death animation speeds to match frame rate in q3 file.
                        # copy a static frame to remaining animation set
                        frames_fps_multiply_q3 = (10.0 / (float(self.Q3_Anims[modelIndex_q3].fps)))
                        total_fps_Q3 = (float(frames_fps_multiply_q3) * frames_total_q3)
                        if frames_total_kp >= total_fps_Q3:
                            IsUsingDeath_FPS = True

                    # ========================================= #
                    #  get every q3 keyframe. paste to kp frame %0.f
                    #  make sure we have a start and end frame (0-1)
                    for q3_key in range(frames_total_q3):  # do first to last frame (can be a single frame)
                        time_kp = 0
                        time_q3 = 0
                        time_kp_end = 0
                        q3_total = frames_total_q3 - 1

                        if (q3_key == 0):
                            # Q3 first frame
                            time_kp = frame_start_kp
                            time_q3 = (frameID_start_q3)
                        elif (q3_key == 1) and (frames_total_q3 == 1):
                            # Q3 only has 1 frame
                            time_kp = frame_end_kp
                            time_q3 = (frameID_start_q3)
                        elif (q3_key == q3_total) and (IsUsingDeath_FPS is False):
                            # last Q3 frame (using timeline)
                            time_kp = frame_end_kp
                            time_q3 = (frameID_start_q3 + q3_key)
                        elif (q3_key <= q3_total):
                            tween_fr = float((frames_total_kp - 1.0) / q3_total)
                            if IsUsingDeath_FPS:
                                tween_fr = frames_fps_multiply_q3
                            tween_fr *= q3_key
                            time_kp = (frame_start_kp + tween_fr)
                            time_q3 = (frameID_start_q3 + q3_key)
                            #  end q3 frame numbers
                        else:
                            if IsUsingDeath_FPS:  # death animations, 1 extra last frame
                                time_kp = frame_end_kp
                                time_q3 = (frameID_start_q3 + (q3_key - 1))   # as integer
                            else:  # end 1 extra frame. for death animations
                                break
                        # end q3_keys setup

                        # add null key to end OF sequence
                        if (frames_total_q3 == 1 or (q3_key == q3_total and time_kp < frame_end_kp)):
                            time_kp_end = frame_end_kp

                        ###########################################
                        # start copying animation for each q3 frame
                        if (obj_isTag == 1):
                            # fix for wrong animation.cfg. use last frame
                            if time_q3 > len(fCurveArray[0]) - 1:
                                time_q3 = len(fCurveArray[0]) - 1

                            # add key to tag_
                            set_key_tag_fn(targetObj, time_kp, time_q3, fCurveArray, fcur_idx)

                            # needs extra key
                            if time_kp_end:
                                fcur_idx += 1
                                set_key_tag_fn(targetObj, time_kp_end, time_q3, fCurveArray, fcur_idx)
                            fcur_idx += 1
                        else:
                            if targetObj.data.shape_keys:
                                # add key to mesh
                                set_key_mesh_fn(targetObj, time_kp, time_q3)

                                # needs extra key
                                if time_kp_end:
                                    set_key_mesh_fn(targetObj, time_kp_end, time_q3)
                                # update fcurve
                                anim = targetObj.data.shape_keys.animation_data
                                for fcu in anim.action.fcurves:
                                    for pt in fcu.keyframe_points:
                                        pt.interpolation = 'LINEAR'
                                    fcu.update()

                                # fix for kp using non integer frame placement
                                for sk in targetObj.data.shape_keys.key_blocks:
                                    sk.interpolation = 'KEY_LINEAR'

                        # ==> END vertex animated mesh objects
                    # ==> END q3 animation set loop
                    ############
                    #   debug  #
                    # break    # <-- loop through only 1 animation
                    ############
                # ==> end kp animation set
                ##########################

                #############################
                # legs to run side (sidestep)
                if self.tag_body_nodeID and (body_part_f == MODEL_LEGS) and (obj_isTag == 0):
                    # is legs mesh
                    twistR_timer = (131, 132, 133, 134, 135, 136,  # right 131-136
                                    159, 160, 161, 162, 163, 164)  # right 159-164
                    twistL_timer = (137, 138, 139, 140, 141, 142,   # left 137-142
                                    165, 166, 167, 168, 169, 170)  # left 165-170
                    angRight = (0 - key_prop.ui_rotate_leg_right)  # math.radians
                    angLeft = (key_prop.ui_rotate_leg_left)  # math.radians
                    mesh_parent_ID = self.tag_body_nodeID

                    for keyAt in range(130, 172):  # stand_timer:
                        targetObj.location = (0, 0, 0)
                        targetObj.rotation_mode = 'XYZ'
                        targetObj.rotation_euler = (0, 0, 0)
                        targetObj.keyframe_insert(data_path="location", frame=keyAt, group="legPos")
                        targetObj.keyframe_insert(data_path="rotation_euler", frame=keyAt, group="legRotate")

                    for i, keyAt in enumerate(twistR_timer):
                        bpy.context.scene.frame_set(keyAt, subframe=0.0)  # todo eval fcurv?
                        update_matrices(mesh_parent_ID)
                        rotMatrix4(targetObj, evalTime_pos_fn(mesh_parent_ID, keyAt), angRight)
                        targetObj.keyframe_insert(data_path="location", frame=keyAt, group="legPos")
                        targetObj.keyframe_insert(data_path="rotation_euler", frame=keyAt, group="legRotate")

                    for i, keyAt in enumerate(twistL_timer):
                        bpy.context.scene.frame_set(keyAt, subframe=0.0)
                        update_matrices(mesh_parent_ID)
                        rotMatrix4(targetObj, evalTime_pos_fn(mesh_parent_ID, keyAt), angLeft)
                        targetObj.keyframe_insert(data_path="location", frame=keyAt, group="legPos")
                        targetObj.keyframe_insert(data_path="rotation_euler", frame=keyAt, group="legRotate")
                # > end legs run side
                #####################

                if targetObj and targetObj.data:
                    targetObj.data.update()

            #  end loop through body parts
        # end function copy keys

        def setupObjectsAsGroups_fn(self):
            # move tags to top of array
            def move_tagToTop(self, array_, tag_name):
                sLen = len(tag_name)
                for x in range(0, len(array_)):
                    tmpStr = array_[x].name[:sLen]
                    if tmpStr == tag_name:
                        array_ = swap(array_, 0, x)
                        # array_[0], array_[x] = array_[x], array_[0]  # swap
                        break  # exit  # found
                return array_
            # end move_tagToTop

            for obj in self.objects:
                if not (obj.type == 'MESH') and not (obj.type == 'EMPTY'):
                    continue

                firstletter = obj.name[0:2]  # substring obj.name 1 2 as name
                tagname = obj.name[0:4]  # substring obj.name 1 4 as name
                objectsName = obj.name  # string

                # asigne each part to a group. eg.. tag_torso to group_body
                # TODO remove unused tags
                discard = True
                if (tagname == "tag_"):
                    if objectsName[:9] == "tag_torso":
                        if objectsName[9:13] == ".low":
                            array_legs.append(obj)
                            discard = False
                    elif objectsName[:8] == "tag_head":
                        if objectsName[8:12] == ".upp":
                            array_head.append(obj)
                            discard = False
                    elif objectsName[:10] == "tag_weapon":
                        if objectsName[10:14] == ".upp":
                            array_body.append(obj)
                            discard = False
                    elif objectsName[:9] == "tag_flash":
                        # if objectsName[9:13] == ".sho":  # note only 1
                        array_wep.append(obj)
                        discard = False
                    if discard:
                        print("%-14s %s" % ("Discard tag:", objectsName))
                        continue
                #  end tag asigments
                elif (firstletter == "l_"):
                    array_legs.append(obj)
                elif (firstletter == "u_"):
                    array_body.append(obj)
                elif (firstletter == "w_"):
                    array_wep.append(obj)
                elif (firstletter == "h_"):
                    array_head.append(obj)
                else:
                    print("%-14s %s" % ("Discard object:", obj.name))
                    continue

                print("%-14s %s" % ("added object:", obj.name))
            #  end adding each mesh object to array

            # sort list
            move_tagToTop(self, array_legs, "tag_torso")
            move_tagToTop(self, array_body, "tag_weapon")
            move_tagToTop(self, array_head, "tag_head")
            move_tagToTop(self, array_wep, "tag_flash")

            print("---- Finished Grouping items -----")
        # end function set model groups

        #  button get animation.cfg
        def getAnimationFile_fn(self, context):
            def strToInt(str):
                out = None
                try:
                    out = int(str)
                except ValueError:
                    out = None
                return out

            def set_sorted_anim(kp_idx, val, body=True):
                if body:
                    self.array_kp_Anims[kp_idx] = self.array_kp_Anims[kp_idx]._replace(body=val)
                self.array_kp_Anims[kp_idx] = self.array_kp_Anims[kp_idx]._replace(legs=val)

            def sortDeathAni_ByFrames_fn(self):
                # Set UI set animations
                set_sorted_anim(KP_33_CR_DEATH1, int(key_prop.ui_cr_death_anim))
                set_sorted_anim(KP_22_LADR, int(key_prop.ui_ladder_anim), body=False)

                # sort death animations by length (short to longest)
                listTime = [  # get frame time
                    [self.Q3_Anims[BOTH_DEATH1].total_fr / self.Q3_Anims[BOTH_DEATH1].fps, BOTH_DEATH1],
                    [self.Q3_Anims[BOTH_DEATH2].total_fr / self.Q3_Anims[BOTH_DEATH2].fps, BOTH_DEATH2],
                    [self.Q3_Anims[BOTH_DEATH3].total_fr / self.Q3_Anims[BOTH_DEATH3].fps, BOTH_DEATH3]]
                listTime.sort(key=lambda x: x[0])
                set_sorted_anim(KP_23_DEATH1, listTime[1][1])  # 19 frames
                set_sorted_anim(KP_24_DEATH2, listTime[0][1])  # 16 frames
                set_sorted_anim(KP_25_DEATH3, listTime[2][1])  # 28 frames
                set_sorted_anim(KP_26_DEATH4, listTime[0][1])  # 13 frames
            # END sortDeathAni_ByFrames_fn

            # TODO get previous folder if missing? or show dialog box?
            fPath = key_prop.ui_btn_getfile
            isError = False
            ani_Index = 0  # as integer
            lineNum = 0
            offsetLegsTime = 0  # as integer
            skipStr = ['//', '/', 'sex', 'footsteps', 'headoffset']

            try:
                file = open(file=fPath, mode="r")
                while(True):
                    line = file.readline()
                    if not line:
                        break
                    if (ani_Index > LEGS_TURN):
                        print("*** File has to many animations ***")
                        break

                    lineDelim = line.split()
                    lineNum += 1

                    if len(lineDelim) < 4:
                        continue

                    if (lineDelim[0] in skipStr or lineDelim[1] in skipStr or lineDelim[2] in skipStr):
                        continue

                    frameStart = strToInt(lineDelim[0])
                    frameEnd = strToInt(lineDelim[1])
                    frameFPS = strToInt(lineDelim[3])

                    if frameStart is None or frameEnd is None or frameFPS is None:
                        print("Warning: line#%i not int" % (lineNum))
                        continue

                    if not frameFPS:
                        frameFPS = 15  # cant devide by zero

                    if (ani_Index == LEGS_WALKCR):
                        offsetLeg = self.Q3_Anims[TORSO_GESTURE].start
                        print("leg offset= %i" % (offsetLeg))
                        offsetLegsTime = (frameStart - offsetLeg)

                    # leg animations start at torso start frame #
                    if (ani_Index >= LEGS_WALKCR):
                        frameStart -= offsetLegsTime

                    self.Q3_Anims.append(Frame_q3(start=frameStart, total_fr=frameEnd, fps=frameFPS))

                    ani_Index += 1

                file.close()
                print("Done reading animation.cfg")
            except Exception:
                print("ERROR: reading animation.cfg")
                self.report({'INFO'}, "ERROR: animation.cfg not found")
                isError = True

            if isError or len(self.Q3_Anims) <= LEGS_TURN:
                print("Skipping conversion")
                return 0

            # arange death by frame counts
            if (self.Q3_Anims is not None) and (len(self.Q3_Anims) > LEGS_TURN):
                sortDeathAni_ByFrames_fn(self)
                return 1
            else:
                return 0
        # ==> END getAnimationFile_fn
        #  end button pressed get animation.cfg file

        def moveChild_mesh_fn(grouped_md3_f, body_part_f, parent_f, snap_f):
            if parent_f is None:
                return

            for child, type in grouped_md3_f:
                if type != body_part_f:
                    continue
                if (child.name[:7] == "KP_tag_"):
                    continue

                child.parent = parent_f
                if snap_f:
                    child.location = (0, 0, 0)  # parent_f.location.copy()
                    child.rotation_quaternion = (1, 0, 0, 0)  # parent_f.rotation_quaternion.copy()
                else:
                    child.matrix_parent_inverse = parent_f.matrix_world.inverted()

        def moveChild_tag_fn(child_f, parent_f, keepPos_f):
            if parent_f is None or child_f is None:
                return

            child_f.parent = parent_f
            if keepPos_f:
                child_f.matrix_parent_inverse = parent_f.matrix_world.inverted()

        def addScaleObj_fn():
            bpy.ops.object.empty_add(type='CUBE')
            retObj = context.selected_objects[0]
            if not retObj:
                raise Exception("Could not get selection(cube)")
            retObj.name = "kp_scale"
            retObj.location = (0, 0, -24)
            retObj.scale = (key_prop.ui_scale, key_prop.ui_scale, key_prop.ui_scale)
            update_matrices(retObj)
            set_select_state(context=retObj, opt=False)  # deselect object
            return retObj

        def doConversion_fn(self, context):

            if not (bpy.context.mode == 'OBJECT'):
                bpy.ops.object.mode_set(mode='OBJECT')  # , toggle=False)

            # deselect any objects
            for ob in bpy.data.objects:
                set_select_state(context=ob, opt=False)

            try:
                setupObjectsAsGroups_fn(self)
                # animationrange = interval 0 390 # TODO
                moveModelKeys_fn(self, context, array_legs, MODEL_LEGS)
                moveModelKeys_fn(self, context, array_body, MODEL_BODY)
                moveModelKeys_fn(self, context, array_head, MODEL_HEAD)
                moveModelKeys_fn(self, context, array_wep, MODEL_WEPS)
                #  todo: tag flash??

                # move mesh to tag/parent then link. reversed
                moveChild_mesh_fn(self.obj_out, MODEL_WEPS, self.tag_wep_nodeID, True)
                moveChild_mesh_fn(self.obj_out, MODEL_HEAD, self.tag_head_nodeID, True)
                moveChild_mesh_fn(self.obj_out, MODEL_BODY, self.tag_body_nodeID, True)

                # move tag to tag/parent then link
                moveChild_tag_fn(self.tag_flash_nodeID, self.tag_wep_nodeID, False)  # move tag_flash to tag_wep
                moveChild_tag_fn(self.tag_wep_nodeID, self.tag_body_nodeID, False)  # move tag_wep to tag_body
                moveChild_tag_fn(self.tag_head_nodeID, self.tag_body_nodeID, False)  # move tag_head to tag_body

                # generate a cube so scale can be applied
                retObj = addScaleObj_fn()

                moveChild_mesh_fn(self.obj_out, MODEL_LEGS, retObj, False)
                moveChild_tag_fn(self.tag_body_nodeID, retObj, True)  # move tag_wep to tag_body

                # add cube to collection
                self.obj_out.append((retObj, MODEL_FLSH))

            except ExceptHandler():
                raise RuntimeError("ERROR: ")
            return
        # ==>END doConversion_fn

        def add_timeline_fn():
            timeNames = (
                ("tgun_rdy_32", 0),
                ("tg_shoot_05", 32),
                ("tg_bird_10", 37),
                ("tg_crch_grab_16", 47),
                ("tg_chin_flip_15", 63),
                ("1pstl_rdy_23", 78),
                ("p_std_shoot_04", 101),
                ("walk_gdown_10", 105),
                ("walk_tg_sht_10", 115),
                ("run_tg_sht_06", 125),
                ("rsd_tg_run_06", 131),
                ("lsd_tg_run_06", 137),
                ("p_walk_sht_10", 143),
                ("p_run_shoot_06", 153),
                ("p_rside_run_06", 159),
                ("p_lside_run_06", 165),
                ("melee_rdy_19", 171),
                ("melee3_07", 190),
                ("melee4_06", 197),
                ("run_melee_06", 203),
                ("run_gun_dn_06", 209),
                ("jump_07", 215),
                ("clmb_loop_09", 222),
                ("death1_19", 231),
                ("death2_16", 250),
                ("death3_28", 266),
                ("death4_13", 294),
                ("tg_crch_rdy_27", 307),
                ("crouch_shoot_06", 334),
                ("crch_shuf_05", 340),
                ("1p_crch_rdy_18", 345),
                ("p_crch_sht_05", 363),
                ("p_crch_walk_06", 368),
                ("crouch_death_12", 374),
            )

            if key_prop.ui_add_timeline:
                mark = bpy.context.scene.timeline_markers
                # mark = bpy.data.scenes[0].timeline_markers  # todo: scene
                mark.clear()
                for str, i in timeNames:
                    mark.new(str, frame=i)
        # END add_timeline_fn():

        ###############
        # begin execute
        ###############
        self.obj_out = []  # store new objects, regroup after conversion
        self.objects = bpy.context.visible_objects  # store objedcts
        bpy.context.scene.frame_set(0)  # todo restore

        if (getAnimationFile_fn(self, context)):  # read animation.cfg
            doConversion_fn(self, context)  # do conversion

            # set scens/collction
            sceneName = "KP_combined"
            if bpy.app.version < (2, 80, 0):
                self.collection_new = bpy.data.scenes.new(sceneName)
                bpy.context.screen.scene = self.collection_new
            else:
                self.collection_q3 = bpy.data.collections
                self.collection_new = bpy.data.collections.new(sceneName)
                bpy.context.scene.collection.children.link(self.collection_new)
                col = bpy.context.view_layer.layer_collection.children[self.collection_new.name]
                bpy.context.view_layer.active_layer_collection = col

            # move to collection 'KP_combined'
            for obj in self.obj_out:
                set_obj_group(obj[0], new_group=self.collection_new)

            add_timeline_fn()
            bpy.context.scene.frame_end = 385
            bpy.context.scene.frame_set(0)  # todo restore

        return {'FINISHED'}
        # ==>END execute
    # END class KINGPIN_UI_BUTTON_GO


# button ABOUT
class KINGPIN_UI_BUTTON_ABOUT(Operator):
    bl_label = "Designed by hypov8. For kingpin."
    bl_idname = "kp.ui_btn_info"
    '''bl_description = ("Update/Sy\n"
                      "Shape key mode:1\n"
                      "Vertex mode: 1")'''
    text = bpy.props.StringProperty(
        name="Enter Name",
        default=""
    )
    about_message = bpy.props.StringProperty(
        name="message",
        description="rtf\nghjtgj",
        default=(
            "-------------\n" +
            "Using the 'Quake 3 Model (.md3)-hy-' Import script.\n" +
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
            "Note:\n" +
            "Animation.cfg may need tweeking to get the animations correct.\n" +
            "Death animations order are used based on time, to suit KP.\n" +
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
        for str in strArray:
            self.layout.label(text=str)
        # self.layout.label(text=self.msg)


classes = [
    KINGPIN_Q3_to_KP_Properties,  # toolbar
    KINGPIN_UI_BUTTON_CFG_File,
    KINGPIN_UI_BUTTON_GO,
    KINGPIN_UI_BUTTON_ABOUT,
    VIEW3D_PT_Q3_to_KP_GUI
]


def register():
    for cls in classes:
        make_annotations(cls)  # v1.2.2
        bpy.utils.register_class(cls)
    # bpy.types.WindowManager.kp_tool_anim = PointerProperty(type=AnimallProperties_KP)
    WindowManager.kp_tool_q3tokp = PointerProperty(type=KINGPIN_Q3_to_KP_Properties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    # bpy.app.handlers.frame_change_post.remove(post_frame_change)
    # del bpy.types.WindowManager.kp_tool_anim
    del WindowManager.kp_tool_q3tokp
