"""
SPDX-License-Identifier: GPL-2.0-or-later
"Daniel Salazar <zanqdo@gmail.com>"

#############
hypov8
using animall plugin tool bar with only vertex/ShapeKey enabled

added:
- key to update frame data

Note: Use full "AnimAll" plugin if you want full control.
      This light version is only suitable for an imported mesh via the kingpin script
#############
"""

import bpy
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup
)
from bpy.props import (
    BoolProperty,
    EnumProperty,
)
from bpy.app.handlers import persistent
from mathutils import Vector
# from math import isclose
from . common_kp import (
    set_ui_panel_string,
    set_select_state,
    getMeshArrays_fn,
    set_mode_get_obj,
    is_selected_mesh,
    get_mesh_objects,
    IDX_XYZ_V
)
from . import common_kp as kpc


@persistent
def post_frame_change(*args):
    """ bpy.ops.object.mode_set(mode=mode) """
    bpy_context = bpy.context
    if bpy_context.mode != "OBJECT":
        try:
            mode = bpy_context.object.mode
            act_obj = kpc.get_objects_active(bpy_context)
            bpy.ops.object.mode_set(mode="OBJECT")
            kpc.set_objects_active(bpy_context, act_obj)
            bpy.ops.object.mode_set(mode=mode)
            print("post_frame_change1")
        except Exception as e:
            print("post_frame_change error: %s" % e)


@persistent
def pre_frame_change(*args):
    """ bpy.context.active_object.update_from_editmode() """
    bpy_context = bpy.context
    if bpy_context.mode != "OBJECT":
        try:
            act_obj = kpc.get_objects_active(bpy_context)
            bpy_context.active_object.update_from_editmode()
            kpc.set_objects_active(bpy_context, act_obj)
            print("pre_frame_change1")
        except Exception as e:
            print("pre_frame_change error: %s" % e)


# Property Definitions
class KINGPIN_Anim_props(PropertyGroup):
    """ auto update frame change """

    def chkBox_autoUpdateFrame(self, _):
        """ _ """
        if self.key_frame:
            bpy.app.handlers.frame_change_pre.append(pre_frame_change)
            bpy.app.handlers.frame_change_post.append(post_frame_change)
            print("Enable class: frame change")
        else:
            bpy.app.handlers.frame_change_pre.remove(pre_frame_change)
            bpy.app.handlers.frame_change_post.remove(post_frame_change)
            print("Disable class: frame change")

    type_list = [
        ("NONE", "-----", "Use Default interpolation", 0),
        ("CONSTANT", "Constant",
            "No interpolation, value of A gets held until B is encountered",
            "IPO_CONSTANT", 1),
        ("LINEAR", "Linear",
            "Straight-line interpolation between A and B (i.e. no ease in/out).",
            "IPO_LINEAR", 2),
        ("BEZIER", "Bezier",
            "Smooth interpolation between A and B, with some control over curve shape.",
            "IPO_BEZIER", 3),
        ("SINE", "Sinusoidal",
            "Sinusoidal easing (weakest, almost linear but with a slight curvature).",
            "IPO_SINE", 4),
        ("QUAD", "Quadratic",
            "Quadratic easing", "IPO_QUAD", 5),
        ("CUBIC", "Cubic",
            "Cubic easing", "IPO_CUBIC", 6),
        ("QUART", "Quartic",
            "Quartic easing", "IPO_QUART", 7),
        ("QUINT", "Quintic",
            "Quintic easing", "IPO_QUINT", 8),
        ("EXPO", "Exponential",
            "Exponential easing (dramatic)", "IPO_EXPO", 9),
        ("CIRC", "Circular",
            "Circular easing (strongest and most dynamic)", "IPO_CIRC", 10),
        ("BACK", "Back",
            "Cubic easing with overshoot and settle", "IPO_BACK", 11),
        ("BOUNCE", "Bounce",
            "Exponentially decaying parabolic bounce, like when objects collide.",
            "IPO_BOUNCE", 12),
        ("ELASTIC", "Elastic",
            "Exponentially decaying sine wave, like an elastic band.",
            "IPO_ELASTIC", 13)]
    key_keytype_in = EnumProperty(
        name="Type",
        description="interpolation for keyframe F-Curve",
        items=type_list,
        default="NONE",
    )

    mode_list = [
        ("AUTO", "Automatic", "Easing type is chosen automatically based on what the type of interpolation", 0),
        ("EASE_IN", "Ease In", "Only on the end closest to the next keyframe.", 1),
        ("EASE_OUT", "Ease Out", "Only on the end closest to the first keyframe.", 2),
        ("EASE_IN_OUT", "Ease In-Out", "Segment between both keyframes.", 3)]
    key_keytype_out = EnumProperty(
        name="Mode",
        description="Easing Type",
        items=mode_list,
        default="AUTO",
    )
    # used
    key_frame = BoolProperty(
        name="Live Update",
        description="Update mesh every time the frame is chaged",
        update=chkBox_autoUpdateFrame,
        default=False
    )


# Utility functions
def refresh_ui_keyframes():
    """ UI keyframe types """
    try:
        for area in bpy.context.screen.areas:
            if area.type in ("TIMELINE", "GRAPH_EDITOR", "DOPESHEET_EDITOR"):
                area.tag_redraw()
    except print("ERROR: refresh_ui_keyframes"):
        pass


##############
# key frames #
def insert_key(data, key, group=None):
    """ data.keyframe_insert(key, group=group)"""
    try:
        if group is not None:
            data.keyframe_insert(key, group=group)
        else:
            data.keyframe_insert(key)
    except print("ERROR: insert_key"):
        pass


def delete_key(data, key):
    """ data.keyframe_delete(key) """
    try:
        data.keyframe_delete(key)
    except print("ERROR: delete_key"):
        pass


def deleteKey_kp(context, allVerts=False):
    # kp_tool_anim = context.window_manager.kp_anim_

    edit_mode, _, sel_obj = set_mode_get_obj(context)
    sel_obj = get_mesh_objects(sel_obj)

    for obj in sel_obj:
        data = obj.data
        sk_data = kpc.get_shapekey_data(obj)
        is_vertex = not sk_data

        # if obj.type == "MESH":
        # if kp_anim_.key_points:
        if is_vertex:
            for vert in data.vertices:
                if allVerts or vert.select:
                    delete_key(vert, "co")
        elif not sk_data.use_relative:  # sk absolute
            delete_key(sk_data, "eval_time")
        else:
            for v_i, vert in enumerate(obj.active_shape_key.data):
                if allVerts or data.vertices[v_i].select:
                    delete_key(vert, "co")

    bpy.ops.object.mode_set(mode=edit_mode)
    refresh_ui_keyframes()


def delete_all_anims(self, context):
    """ delete all animations """

    edit_mode, _, sel_objs = set_mode_get_obj(context)
    # frame = bpy.context.scene.frame_current

    if not is_selected_mesh(self, sel_objs):
        return  # {"FINISHED"}

    for obj in sel_objs:
        if not obj.data:
            continue
        set_select_state(obj, False)  # select object

        vArray = []
        # get vertex pos at current frame
        mesh = getMeshArrays_fn([obj], global_cords=False)
        for v in mesh[0][IDX_XYZ_V]:
            vArray.append(v)

        # remove parent
        if obj.parent:
            # mat_copy = obj.matrix_world.copy()
            obj.parent = None
            # obj.matrix_world = mat_copy

        # clear the animation data
        obj.data.animation_data_clear()
        obj.animation_data_clear()
        # clear shapekey data
        sk_data = kpc.get_shapekey_data(obj)
        if sk_data:
            obj.active_shape_key_index = 0
            obj.data.update()
            sk_data.animation_data_clear()
            keyblocks = reversed(sk_data.key_blocks)
            for sk in keyblocks:
                obj.shape_key_remove(sk)

        # apply current position to vertex
        for i, v in enumerate(obj.data.vertices):
            v.co = Vector(vArray[i])
        obj.data.update()

    for obj in sel_objs:
        if not obj.data:
            continue
        set_select_state(obj, True)

    # return to edit mode if neded
    bpy.ops.object.mode_set(mode=edit_mode)

    refresh_ui_keyframes()
    self.report({"INFO"}, "Clear Animation: Done")


# GUI (Panel)
class KINGPIN_PT_animall_KP(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = set_ui_panel_string()
    bl_category = "Kingpin"
    bl_label = "KEY FRAMES"
    bl_options = {"DEFAULT_CLOSED"}
    # bl_options = {"HEADER_LAYOUT_EXPAND"}

    # @classmethod
    # def poll(self, context):
    #     return context.active_object and context.active_object.type in {"MESH"}

    def draw(self, context):
        """ _ """
        layout = self.layout
        obj = context.active_object
        if not obj or obj.type != "MESH":

            col = layout.column(align=True)
            row = col.row(align=True)
            row.label(text="No Active Object")
            return

        kp_tool_anim = context.window_manager.kp_anim_
        sk_activ = obj.active_shape_key
        sk_data = kpc.get_shapekey_data(obj)
        is_vertex = not sk_data

        if is_vertex:
            box1 = layout.box()
            boxFlow1 = box1.column_flow(columns=1, align=True)  # start 1 row box flow
            boxFlow1.label(text="Selected Vertex")
            row = boxFlow1.column_flow(columns=2, align=True)
            row.scale_y = 1.2
            row.operator("anim.insert_keyframe_animall_kp", icon="KEY_HLT")
            row.operator("anim.delete_keyframe_animall_kp", icon="KEY_DEHLT")
            boxFlow1.label(text="All Vertex")
            row = boxFlow1.column_flow(columns=2, align=True)
            row.scale_y = 1.2
            row.operator("anim.insert_keyframe_animall_all_kp", icon="KEYINGSET")
            row.operator("anim.delete_keyframe_animall_all_kp", icon="KEY_DEHLT")
            boxFlow1.separator() #factor=1.2) #b2.79
            boxFlow1.operator("kp.ui_btn_driver_clear", icon="X")
            # end box1

            box2 = layout.box()
            boxFlow2 = box2.column_flow(columns=1, align=True)  # start 1 row box flow
            boxFlow2.label(text="Interpolation", icon="IPO_CONSTANT")
            boxFlow2.prop(kp_tool_anim, "key_keytype_in")
            boxFlow2.prop(kp_tool_anim, "key_keytype_out")
            # end box2

        # frame change box. fix for vertex animation bug
        box3 = layout.box()
        # row = box3.row(align=True)  # row 1. mode
        # row.alignment = "LEFT"
        if is_vertex:
            box3.row().label(text="Vertex Mode", icon="VERTEXSEL")
        else:
            box3.row().label(text="Shape Key Mode", icon="SHAPEKEY_DATA")

        # arrows
        boxFlow3 = box3.column_flow(columns=3, align=True)
        boxFlow3.alignment = "EXPAND"
        boxFlow3.operator("anim.frame_prev_kp")  # left arrow
        boxFlow3.operator("anim.frame_next_kp")  # right arror
        boxFlow3.operator("anim.frame_sync_kp")  # update/sync button
        boxFlow3 = box3.column_flow(columns=1, align=True)
        boxFlow3.alignment = "LEFT"
        # frame number
        str_row = "Fr: %i" % (bpy.context.scene.frame_current)

        # new objects wint have this updated yet
        sk_name = "Error:" if sk_activ is None else sk_activ.name

        if not is_vertex:
            sk_index = obj.active_shape_key_index

            ####################
            # absalute shapekeys
            if not sk_data.use_relative:  # sk absolute
                boxFlow3.label(text="%s   SK: %s" % (str_row, sk_name))  # , icon="SHAPEKEY_DATA")
                eval_time = sk_data.eval_time

                if (sk_data and sk_data.key_blocks):
                    sk_frame = sk_data.key_blocks[sk_index].frame
                    # val = float(bpy.context.scene.frame_current * 10)
                    frame_min = eval_time - 0.01  # find close float
                    frame_max = eval_time + 0.01  #
                    if not (sk_frame > frame_min and sk_frame < frame_max):
                        boxFlow3.label(text="Shape Key Not sync\'d", icon="INFO")
            ####################
            # relative shapekeys
            elif sk_index > 0:
                boxFlow3.label(text="%s   SK: %s" % (str_row, sk_name))  # , icon="SHAPEKEY_DATA")
                if sk_activ.value < 1:
                    boxFlow3.label(text="sKey not 1.0? sync?", icon="INFO")
            elif sk_activ or sk_data:
                key0_Name = sk_data.key_blocks[0].name if sk_data else sk_name
                boxFlow3.label(text="%s   SK: %s (Base)" % (str_row, key0_Name))  # icon="SHAPEKEY_DATA"
                boxFlow3.label(text="sKey: Index 0", icon="ERROR")  # index invalid
        # else:
        #    boxFlow3.label(text="Vertex Mode", icon="VERTEXSEL")


def seekFrame(context, offset):
    obj = context.active_object
    sk_data = kpc.get_shapekey_data(obj)
    is_vertex = not sk_data

    fr_curr = bpy.context.scene.frame_current
    fr_dest = fr_curr + offset
    if fr_dest >= 0:
        obj_mode = context.object.mode
        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.scene.frame_set(fr_dest, subframe=0.0)
        # select shapekey
        if not is_vertex:
            kpc.sync_shapekey_to_frame(obj, sk_data)
        bpy.ops.object.mode_set(mode=obj_mode)


# button frame "prev"
class KP_UI_BTN_ANIM_FRAME_NEXT(Operator):
    bl_label = "-->"
    bl_idname = "anim.frame_next_kp"
    bl_description = "Move timeline to next frame. Auto Sync"
    bl_options = {"REGISTER"}  # , "UNDO"}

    def execute(self, context):
        seekFrame(context, 1)
        return {"FINISHED"}


# button frame "next"
class KP_UI_BTN_ANIM_FRAME_PREV(Operator):
    bl_label = "<--"
    bl_idname = "anim.frame_prev_kp"
    bl_description = "Move timeline to previous frame. Auto Sync"
    bl_options = {"REGISTER"}  # , "UNDO"}

    def execute(self, context):
        seekFrame(context, -1)
        return {"FINISHED"}


# button frame update/sync
class KP_UI_BTN_ANIM_FRAME_SYNC(Operator):
    """ _ """
    bl_label = "Sync"
    bl_idname = "anim.frame_sync_kp"
    bl_description = (
        "Update/Sync Mesh. Use This after changing the Timeline\n"
        "Shape key mode: will search for SK with 1.0 value, to match current frame\n"
        "Vertex mode: will goto object mode, advance 1 frame then return to previous frame")
    bl_options = {"REGISTER"}  # , "UNDO"}

    def execute(self, context):
        obj = context.active_object
        sk_data = kpc.get_shapekey_data(obj)
        is_vertex = not sk_data

        obj_mode = context.object.mode
        fr_curr = bpy.context.scene.frame_current

        if context.mode != "OBJECT":
            obj.update_from_editmode()
            bpy.ops.object.mode_set(mode="OBJECT")

        if is_vertex:
            # set frame +1 then -1
            bpy.context.scene.frame_set(fr_curr + 1)# TODO work out blender update().
            bpy.context.scene.frame_set(fr_curr)
        else:
            kpc.sync_shapekey_to_frame(obj, sk_data) #, fr_curr)
        bpy.ops.object.mode_set(mode=obj_mode)
        return {"FINISHED"}


def insertKey_kp(context, allVerts=False):
    animProp_KP = context.window_manager.kp_anim_
    frame = bpy.context.scene.frame_current
    frame_min = bpy.context.scene.frame_current - 0.01  # find close float
    frame_max = bpy.context.scene.frame_current + 0.01  #
    kf_type_in = animProp_KP.key_keytype_in
    kf_type_out = animProp_KP.key_keytype_out

    edit_mode, _, sel_objs = set_mode_get_obj(context)
    sel_objs = get_mesh_objects(sel_objs)


    for obj in sel_objs:  # [o for o in objects if o.type in {"MESH"}]:
        sk_data = kpc.get_shapekey_data(obj)
        is_vertex = not sk_data

        data = obj.data
        selVerts = [False] * len(data.vertices)

        # if obj.type == "MESH":
        ########################
        # vertex keyframe mode #
        if is_vertex:
            # if kp_anim_.key_points:
            for v_i, vert in enumerate(data.vertices):
                if allVerts or vert.select:
                    insert_key(vert, "co", group="Vertex %d" % (v_i))
                    selVerts[v_i] = True

            # set interpolation TODO move to function
            if kf_type_in != "NONE":
                anim = obj.data.animation_data
                if anim is not None and anim.action is not None:
                    for fcu in kpc.fcurves_iter(anim.action):  #b44+
                        # get number in 'vertices[2].co'
                        v_idx = int(fcu.data_path[9:fcu.data_path.find("]", 10)])
                        if not selVerts[v_idx]:
                            continue
                        for v_i, kf in enumerate(fcu.keyframe_points):
                            v_time = kf.co[0]
                            if v_time > frame_min and v_time < frame_max:
                                kf.interpolation = kf_type_in
                                kf.easing = kf_type_out
                                break  # found match
                        fcu.update()

        #############################
        # shape key mode (absolute) #
        elif not sk_data.use_relative:  # sk absolute
            sk_data.eval_time = frame * 10
            sk_data.keyframe_insert(data_path="eval_time")  # , frame=frame)

            # set interpolation TODO move to function
            if kf_type_in != "NONE":
                anim = obj.data.shape_keys.animation_data
                if anim is not None and anim.action is not None:
                    for fcu in kpc.fcurves_iter(anim.action):  #b44+
                        for v_i, kf in enumerate(fcu.keyframe_points):
                            v_time = kf.co[0]
                            if (v_time > frame_min and v_time < frame_max):
                                kf.interpolation = kf_type_in
                                kf.easing = kf_type_out
                        fcu.update()

        ###################################
        # shape key mode (multi/relative) #
        else:
            if obj.active_shape_key_index > 0:  # TODO ok?
                sk_name = obj.active_shape_key.name
                for v_i, vert in enumerate(obj.active_shape_key.data):
                    if allVerts or data.vertices[v_i].select:
                        insert_key(vert, "co", group="%s Vertex %s" % (sk_name, v_i))

    bpy.ops.object.mode_set(mode=edit_mode)
    refresh_ui_keyframes()


# button insert key "selected"
class KP_UI_BTN_ANIM_ADD_KEY(Operator):
    bl_label = "Add"
    bl_idname = "anim.insert_keyframe_animall_kp"
    bl_description = "Insert Keys for selected vertex"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        insertKey_kp(context, False)

        return {"FINISHED"}


# button insert key "all"
class KP_UI_BTN_ANIM_ADD_KEY_ALL(Operator):
    bl_label = "Add"
    bl_idname = "anim.insert_keyframe_animall_all_kp"
    bl_description = "Insert Keys for all vertex"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        insertKey_kp(context, True)

        return {"FINISHED"}


# delete keys on "selected" vertex
class KP_UI_BTN_ANIM_DEL_KEY(Operator):
    bl_label = "Delete"
    bl_idname = "anim.delete_keyframe_animall_kp"
    bl_description = "Delete Key for selected vertex"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        deleteKey_kp(context, False)

        return {"FINISHED"}


# delete keys on "all" vertex
class KP_UI_BTN_ANIM_DEL_KEY_ALL(Operator):
    bl_label = "Delete"
    bl_idname = "anim.delete_keyframe_animall_all_kp"
    bl_description = "Delete Key for all vertex"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        deleteKey_kp(context, True)

        return {"FINISHED"}


# button remove animation
class KP_UI_BTN_ANIM_DEL_ALL_ANIM(Operator):
    """remove all animation data"""
    bl_idname = "kp.ui_btn_driver_clear"
    bl_label = "Clear All Anim"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Remove all animations and shape keys"

    def execute(self, context):
        delete_all_anims(self, context)

        return {"FINISHED"}


classes = (
    KP_UI_BTN_ANIM_ADD_KEY,
    KP_UI_BTN_ANIM_ADD_KEY_ALL,
    KP_UI_BTN_ANIM_DEL_KEY,
    KP_UI_BTN_ANIM_DEL_KEY_ALL,
    KP_UI_BTN_ANIM_DEL_ALL_ANIM,
    KP_UI_BTN_ANIM_FRAME_NEXT,
    KP_UI_BTN_ANIM_FRAME_PREV,
    KP_UI_BTN_ANIM_FRAME_SYNC,
    KINGPIN_PT_animall_KP,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
