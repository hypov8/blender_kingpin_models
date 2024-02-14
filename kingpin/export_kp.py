'''
md2/mdx exporter

'''


import os
import struct
import bpy
from bpy.types import Operator, PropertyGroup
from bpy.props import (
    BoolProperty,
    EnumProperty,
    StringProperty,
    IntProperty
)
from bpy_extras.io_utils import ExportHelper
from . common_kp import (
    BL_VER,
    MD2_MAX_TRIANGLES,
    MD2_MAX_VERTS,
    MD2_MAX_FRAMES,
    MD2_MAX_SKINS,
    MD2_MAX_SKINNAME,
    MD2_VN,
    MDX5_MAX_TRIANGLES,
    MDX5_MAX_VERTS,
    IDX_IDC_V,
    IDX_IDC_UV,
    IDX_XYZ_V,
    IDX_XYZ_VN,
    IDX_XY_UV,
    IDX_I_FACE,
    IDX_I_VERT,
    IDX_I_UV,
    KINGPIN_FileSelect_folder_Params,
    KINGPIN_FileSelect_md2_Params,
    printStart_fn,
    printProgress_fn,
    printDone_fn,
    getMeshArrays_fn,
    is_selected_mesh,
    get_mesh_objects,
    get_objects_all,
    get_objects_selected,
    get_addon_preferences,
    set_mode_get_obj,
    set_select_state,
    # MDX5_VERSION
)


# -|GUI|- Export Properties
class KINGPIN_Export_props(PropertyGroup):
    ''' export properties '''
    # skin name selector
    ui_opt_tex_name = EnumProperty(
        name="Skin",
        description="Skin naming method",
        items=(
            ('SKIN_MAT_NAME', "1.Material Name",
             "Use material name for skin.\n" +
             "Must include the file extension\n" +
             "eg.. models/props/test.tga\n" +
             "Image dimensions are sourced from nodes. 256 is use if no image exists"
            ),
            ('SKIN_TEX_NAME', "2.Image Name",
             "Use image name from Material nodes\n" +
             "Must include the file extension\n" +
             "\"material name\" will be used if no valid textures are found\n" +
             "Image dimensions are sourced from nodes. 256 is use if no image exists"
            ),
            ('SKIN_TEX_PATH', "3.Image Path",
             "Use image path name from Material nodes\n" +
             "Path must contain a folder models/ or players/ or textures/ \n" +
             "\"material name\" will be used if no valid textures are found\n" +
             "Image dimensions are sourced from nodes. 256 is use if no image exists"
            ),
        ),
        default='SKIN_MAT_NAME'
    )
    # misc options
    ui_opt_apply_modify = BoolProperty(
        name="Apply Modifiers",
        description="Apply Modifiers or use the original base mesh",
        default=True
    )
    ui_opt_is_hd = BoolProperty(
        name="HD Version",
        description=("Export HD version. Backward compatable with engine and some viewers.\n" +
                     "Needs MH patch to view. without the wobble :)\n" +
                     "Rember to store files in main/hires/models folders."),
        default=True
    )
    ui_opt_cust_vn = BoolProperty(
        name="Custom Vertex Normals",
        description=(
            "Use custom vertex normals instead of average normal.\n" +
            "Normals should be combined so each vertex has only 1 direction.\n"+
            "Note: Vertex are not split on hard edges."),
        default=True
    )
    ui_opt_is_player = BoolProperty(
        name="Seam Fix (Player etc.)",
        description=(
            "Fix 'multi-part' models that share a common seam.\n"
            "This works by using all visable objects in the scene to generate a bbox (shared 256 grid)\n"
            "Each model will use a common grid for compression, so vertex location will match.\n"
            "This can reduce model rez/quality, so only use when needed\n"
            "Usage: Show head, body, legs. Select each object(eg. head), then export(eg. head.mdx)"),
        default=False,
    )
    # animation group
    ui_opt_animated = BoolProperty(
        name="Export animation",
        description=("Export all animation frames.\n" +
                     "Note: Start/End frame initially comes from timeline range."),
        default=False
    )
    ui_opt_fr_start = IntProperty(
        name="Start Frame",
        description="Animated model start frame",
        min=0, max=MD2_MAX_FRAMES - 1,
        default=0
    )
    ui_opt_fr_end = IntProperty(
        name="End Frame",
        description="Animated model end frame",
        min=0, max=MD2_MAX_FRAMES - 1,
        default=40
    )
    ui_opt_use_hitbox = BoolProperty(
        name="Player HitBox",
        description=(
            "Use when exporting .mdx player models.\n" +
            "If multiple objects are selected, a separate hitbox is created for each object.\n" +
            "HitBox are used in multiplayer when \"dm_locational_damage 1\" is set on the server\n" +
            "Default: disabled. This will create 1 large hitbox."),
        default=False
    )
    ui_opt_share_bbox = BoolProperty(
        name="Shared Bounding Box",
        description=(
            "Calculate a shared bounding box from all frames.\n" +
            "Used to avoid wobble in static vertices but wastes resolution"),
        default=False
    )
    # gui panel extra
    ui_opt_model_ext = EnumProperty(
        name="Format",
        description="Choose which format to export",
        items=((".md2", "MD2", ""), (".mdx", "MDX", "")),
        default=".md2"
    )
    ui_opt_export_name = StringProperty(
        name="File",
        description="File name for model",
        default='tris',
        maxlen=1024,
        subtype='FILE_NAME' # 'FILE_PATH'
    )
    ui_opt_export_path = StringProperty(
        name="Path",
        description="Folder path to MD2/X file",
        options={'HIDDEN'},
        default='',
        maxlen=1024,
        subtype='NONE'
    )


class KINGPIN_Export_Button(Operator, KINGPIN_FileSelect_md2_Params):
    ''' Export selection to Kingpin file format (md2/mdx) '''
    bl_idname = "kp.export_button_model"
    bl_label = "Export model"
    filename_ext = {".mdx", ".md2"}  # md2 used later
    check_extension = True  # 2.8 allow typing md2/mdx

    def execute(self, context):
        kp_export_ = context.window_manager.kp_export_

        merg_path = os.path.join(
            kp_export_.ui_opt_export_path,
            kp_export_.ui_opt_export_name)

        self.filepath = bpy.path.abspath(
            bpy.path.ensure_ext(
            merg_path,
            kp_export_.ui_opt_model_ext))
        execute_export(self, context)
        return {'FINISHED'}


class KINGPIN_Export_Button_File(Operator):
    ''' Copy object name to filename '''
    bl_idname = "kp.export_button_file"
    bl_label = ""
    check_extension = True  # 2.8 allow typing md2/mdx

    def execute(self, context):
        kp_export_ = context.window_manager.kp_export_

        act_obj = get_objects_all(context).active

        if act_obj:
            kp_export_.ui_opt_export_name = os.path.splitext(act_obj.name)[0]
        else:
            sel_obj = [o for o in get_objects_selected(context)]
            if len(sel_obj):
                kp_export_.ui_opt_export_name = os.path.splitext(sel_obj[0].name)[0]
        return {'FINISHED'}


class KINGPIN_Export_Button_Folder(Operator, KINGPIN_FileSelect_folder_Params):
    ''' export folder selector '''
    bl_idname = "kp.export_button_folder"
    bl_label = "Select Folder" # icon
    check_extension = True

    def execute(self, context):
        ui_export_ = context.window_manager.kp_export_
        ui_export_.ui_opt_export_path = self.directory
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def draw_export(self, context):
    ui_export_ = context.window_manager.kp_export_
    layout = self.layout

    # skin chooser box
    layout.prop(ui_export_, "ui_opt_tex_name")  # testure source (dropdown)

    # misc options box
    box = layout.box()
    miscBox = box.column_flow(columns=1, align=True)
    # miscBox.prop(ui_export_, "ui_opt_apply_modify")  # apply movifiers
    # if ui_export_.ui_opt_apply_modify:
    miscBox.prop(ui_export_, "ui_opt_cust_vn")   # custom vertex normals
    miscBox.prop(ui_export_, "ui_opt_is_hd")         # HD version
    miscBox.prop(ui_export_, "ui_opt_use_hitbox")    # merge hitbox
    miscBox.prop(ui_export_, "ui_opt_is_player")     # playermodel

    # animation box
    box = layout.box()
    animBox = box.column_flow(columns=1, align=True)
    animBox.prop(ui_export_, "ui_opt_animated")   # export animation
    sub = animBox.column_flow(columns=1, align=True)
    sub.prop(ui_export_, "ui_opt_fr_start")           # frame start number
    sub.prop(ui_export_, "ui_opt_fr_end")             # frame end number
    sub.enabled = ui_export_.ui_opt_animated

    sub2 = animBox.column()
    sub2.prop(ui_export_, "ui_opt_share_bbox")
    if  ui_export_.ui_opt_is_player or not ui_export_.ui_opt_animated:
        sub2.enabled = False
        ui_export_.ui_opt_share_bbox = False


def execute_export(self, context):
    ''' export selected models '''
    # print headder
    ver = BL_VER # bl_info.get("version")
    print("=======================\n" +
          "Kingpin Model Exporter.\n" +
          "Version: (%i.%i.%i)\n" % (ver[0], ver[1], ver[2]) +
          "=======================")

    #store current frame
    cur_frame = bpy.context.scene.frame_current

    # store selected objects
    cur_mode, act_obj, sel_obj = set_mode_get_obj(context)
    self.objects_sel = get_mesh_objects(sel_obj)
    # store all scene objects
    self.objects_vis = get_mesh_objects(context.visible_objects)
    # valid mesh?
    if not is_selected_mesh(self, self.objects_sel):
        return {'FINISHED'}

    # deselect any objects
    for obj in sel_obj: # .selected:  # bpy.data.objects:
        set_select_state(context=obj, opt=False)
    # for ob in act_obj: # .active: # bpy.data.objects:
    set_select_state(context=act_obj, opt=False)

    # set output type
    ext = os.path.splitext(os.path.basename(self.filepath))[1]
    if ext == '.mdx':
        # filePath = bpy.path.ensure_ext(filepath, self.filename_ext[0])
        self.isMdx = True
    elif ext == '.md2':
        # filePath = bpy.path.ensure_ext(filepath, self.filename_ext[1])
        self.isMdx = False
    else:
        self.report({'WARNING'}, "Incorrect file extension. Not md2 or mdx")
        return {'FINISHED'}

    Export_MD2_fn(self, context, self.filepath)

    #######################
    # done.
    for obj in sel_obj:# select inital objects
        set_select_state(context=obj, opt=True)
    # set current frame
    bpy.context.scene.frame_set(cur_frame)
    # return to edit mode
    if act_obj:
        get_objects_all(bpy.context).active = act_obj
        bpy.ops.object.mode_set(mode=cur_mode)

    self.report({'INFO'}, "Export Model: Done")
    print("=======================")


class KINGPIN_Export_Dialog(Operator, ExportHelper, KINGPIN_FileSelect_md2_Params):
    ''' Export selection to Kingpin file format (md2/mdx) '''
    bl_idname = "kp.export_model_dialog"
    bl_label = "Export md2/mdx"
    filename_ext = {".mdx", ".md2"}  # md2 used later
    check_extension = False  # 2.8 allow typing md2/mdx

    def execute(self, context):
        execute_export(self, context)
        return {'FINISHED'}

    def draw(self, context):
        draw_export(self, context)

    def invoke(self, context, event):
        ''' check selected objets.
            get scene start/end from timeline
        '''
        ui_export_ = context.window_manager.kp_export_
        ui_export_.ui_opt_fr_start = context.scene.frame_start
        ui_export_.ui_opt_fr_end = context.scene.frame_end

        obj_sel = get_objects_selected(context)
        if len(obj_sel) == 0: #not context.selected_objects:
            self.report({'ERROR'}, "Please, select an object to export!")
            return {'CANCELLED'}

        user_prefs = get_addon_preferences(context)
        if user_prefs.pref_kp_filename:
            fname = os.path.splitext(obj_sel[0].name)
            if fname[1] == '.mdx':
                self.filepath = obj_sel[0].name
            elif fname[1] == '.md2':
                self.filepath = obj_sel[0].name
            else:
                if user_prefs.pref_kp_file_ext:
                    self.filepath = bpy.path.ensure_ext(obj_sel[0].name, '.mdx')
                else:
                    self.filepath = bpy.path.ensure_ext(obj_sel[0].name, '.md2')
            # filePath = bpy.path.ensure_ext(filepath, self.filename_ext[0])

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


def setupInternalArrays_fn(self):
    '''get selected mesh data and store
       also store all viewable mesh for player models
    '''
    self.start_time = printStart_fn()  # reset timmer
    obj_sel = self.objects_sel
    obj_vis = self.objects_vis
    scene = bpy.context.scene
    start_frame = self.ui_opt_fr_start
    custom_vn = self.ui_opt_cust_vn
    apply_modifyer = self.ui_opt_apply_modify
    is_player = self.ui_opt_is_player or self.ui_opt_share_bbox

    prefix = "Getting mesh data"
    for frame in range(self.numFrames):
        if self.numFrames < 50 or (frame % 20) == 0:
            printProgress_fn(frame, self.numFrames, prefix)  # print progress

        # --------------------------------------------
        # TODO find why this is taking lots of time...
        # 5 seconds with no items to seek 700 frames
        frame_idx = start_frame + frame
        scene.frame_set(frame_idx)
        # --------------------------------------------
        self.frameData.append(
            getMeshArrays_fn(
                obj_sel,
                getUV=1 if frame == 0 else 0, # ignore uv for animated frames
                apply_modifyer=apply_modifyer,
                custom_vn=custom_vn)
        )
        if is_player:
            # get all visable scene ebjects for bbox
            self.frameDataBBox.append(getMeshArrays_fn(obj_vis))

    printDone_fn(self.start_time, prefix)  # Done.
# end setupInternalArrays_fn


def write_frame_fn(self, file, frame, frameName="frame"):
    ''' build frame data '''
    if not self.ui_opt_share_bbox or self.ui_opt_is_player:  # .options
        min = self.bbox_min[frame]
        max = self.bbox_max[frame]
    else:
        min = self.bbox_min[0]
        max = self.bbox_max[0]

    # BL: some caching to speed it up:
    # -> sd_ gets the vertices between [0 and 255]
    #    which is our important quantization.
    xMax = max[0] - min[0]  # bbox size
    yMax = max[1] - min[1]  # bbox size
    zMax = max[2] - min[2]  # bbox size
    sdx = xMax / 255.0  # write default scale to file
    sdy = yMax / 255.0  # write default scale to file
    sdz = zMax / 255.0  # write default scale to file

    isdx = float(65280.0 / xMax) if xMax != 0.0 else 0.0
    isdy = float(65280.0 / yMax) if yMax != 0.0 else 0.0
    isdz = float(65280.0 / zMax) if zMax != 0.0 else 0.0

    # note about the scale: self.object.scale is already applied via matrix_world
    data = struct.pack(
        "<6f16s",
        sdx, sdy, sdz,  # write scale of the model
        min[0], min[1], min[2],  # write offset (= min of bounding box)
        bytes(frameName[0:15], encoding="utf8"))  # write frame name.
    file.write(data)  # frame header

    ###########################
    # write vertex X,Y,Z,lightNormalID
    ofsetVertID = 0  # multi object
    # frames
    v8 = [0] * 3
    v16 = [0] * 3
    for mIdx, tmp_mesh in enumerate(self.frameData[frame]):  #object/s
        #vertex data
        for vIdx, vert in enumerate(tmp_mesh[IDX_XYZ_V]):
            # find the closest normal for every vertex
            bestNormalIndex = self.vNormData[frame][mIdx][vIdx]
            # write vertex pos and normal. (compressed position. 256 units)
            v16[0] = int((vert[0] - min[0]) * isdx + 0.5)  # MH: compresion
            v16[1] = int((vert[1] - min[1]) * isdy + 0.5)  # MH: compresion
            v16[2] = int((vert[2] - min[2]) * isdz + 0.5)  # MH: compresion
            v8[0] = (v16[0] + 128) >> 8  # MH: compresion
            v8[1] = (v16[1] + 128) >> 8  # MH: compresion
            v8[2] = (v16[2] + 128) >> 8  # MH: compresion
            data = struct.pack('<4B', v8[0], v8[1], v8[2], bestNormalIndex)
            file.write(data)  # write vertex and normal
        ofsetVertID += len(tmp_mesh[IDX_XYZ_V])  # TODO

    # HD model
    if self.ui_opt_is_hd == True:  # 'VERSION5':
        for mIdx, tmp_mesh in enumerate(self.frameData[frame]):
            for vert in tmp_mesh[IDX_XYZ_V]:
                v16[0] = int((vert[0] - min[0]) * isdx + 0.5)  # MH: compresion
                v16[1] = int((vert[1] - min[1]) * isdy + 0.5)  # MH: compresion
                v16[2] = int((vert[2] - min[2]) * isdz + 0.5)  # MH: compresion
                v8[0] = (v16[0] + 128) >> 8  # MH: compresion
                v8[1] = (v16[1] + 128) >> 8  # MH: compresion
                v8[2] = (v16[2] + 128) >> 8  # MH: compresion
                data = struct.pack(  # HD vertex. 256 subdivision
                    '<3b',
                    v16[0] - (v8[0] << 8),  # MH: compresion
                    v16[1] - (v8[1] << 8),  # MH: compresion
                    v16[2] - (v8[2] << 8))  # MH: compresion
                file.write(data)
        ofsetVertID += len(tmp_mesh[IDX_XYZ_V])  # TODO not used

# end write_frame_fn


def setup_data_fn(self, context):
    ''' build a valid model and export '''

    def buildGLcommands_fn(self):
        ''' build gl commands '''
        self.start_time = printStart_fn()  # reset timmer
        prefix = "Building GLCommands"
        printProgress_fn(0, 1, prefix)  # print progress

        def findStripLength_fn(usedFace, mesh, startTri, startVert, numFaces,
                            cmdTris, cmdVerts, cmdUV):
            ''' triangle strips '''
            # usedFace_ = copy.copy(usedFace)  # duplicate

            face_data = mesh[IDX_IDC_V]
            uv_data = mesh[IDX_IDC_UV]  # get_uv_data(mesh)
            usedFace[startTri] = 2  # make tri as currently testing

            # copy edge
            m1 = face_data[startTri * 3 + ((startVert + 2) % 3)]
            m2 = face_data[startTri * 3 + ((startVert + 1) % 3)]
            u1 = uv_data[startTri * 3 + ((startVert + 2) % 3)]
            u2 = uv_data[startTri * 3 + ((startVert + 1) % 3)]

            # store first tri
            cmdVerts.append(face_data[startTri * 3 + ((startVert + 0) % 3)])  # vIdc
            cmdVerts.append(m1)
            cmdVerts.append(m2)
            cmdUV.append(uv_data[startTri * 3 + ((startVert + 0) % 3)])
            cmdUV.append(u1)
            cmdUV.append(u2)

            cmdTris.append(startTri)

            cmdLength = 1  # stripCount
            for triIdx in range(startTri + 1, numFaces):
                if usedFace[triIdx] == 0:
                    for k in range(3):
                        # find 2 vertex that share vertex/UV data
                        if((m1 == face_data[triIdx * 3 + k]) and  # compare vertex indices
                        (m2 == face_data[triIdx * 3 + ((k + 1) % 3)]) and
                        (u1 == uv_data[triIdx * 3 + k]) and  # compare texture indices
                        (u2 == uv_data[triIdx * 3 + ((k + 1) % 3)])):

                            # move to next vertex loop
                            if cmdLength % 2 == 1:  # flip?
                                m1 = face_data[triIdx * 3 + ((k + 2) % 3)]
                                u1 = uv_data[triIdx * 3 + ((k + 2) % 3)]
                            else:
                                m2 = face_data[triIdx * 3 + ((k + 2) % 3)]
                                u2 = uv_data[triIdx * 3 + ((k + 2) % 3)]

                            cmdVerts.append(face_data[triIdx * 3 + ((k + 2) % 3)])  # vIdx

                            cmdUV.append(uv_data[triIdx * 3 + ((k + 2) % 3)])
                            cmdLength += 1
                            cmdTris.append(triIdx)

                            usedFace[triIdx] = 2
                            triIdx = startTri + 1  # restart looking?

            # clear used counter
            for fc in range(startTri, numFaces):
                if usedFace[fc] == 2:
                    usedFace[fc] = 0
            # for fIdx, f in enumerate(usedFace):
            #     if f == 2:
            #         usedFace[fIdx] = 0

            return cmdLength
        #  end findStripLength_fn

        def findFanLength_fn(usedFace, mesh, startTri, startVert, numFaces,
                             cmdTris, cmdVerts, cmdUV):
            ''' triangle strips '''
            # usedFace_ = copy.copy(usedFace)  # duplicate

            face_data = mesh[IDX_IDC_V]
            uv_data = mesh[IDX_IDC_UV]
            usedFace[startTri] = 2

            # copy edge
            m2 = face_data[startTri * 3 + ((startVert + 0) % 3)]
            m1 = face_data[startTri * 3 + ((startVert + 1) % 3)]
            u2 = uv_data[startTri * 3 + ((startVert + 0) % 3)]
            u1 = uv_data[startTri * 3 + ((startVert + 1) % 3)]

            # store first tri
            cmdVerts.append(m2)
            cmdVerts.append(face_data[startTri * 3 + ((startVert + 2) % 3)])
            cmdVerts.append(m1)
            cmdUV.append(u2)
            cmdUV.append(uv_data[startTri * 3 + ((startVert + 2) % 3)])
            cmdUV.append(u1)

            cmdLength = 1  # fanCount
            cmdTris.append(startTri)

            for triIdx in range(startTri + 1, numFaces):
                if usedFace[triIdx] == 0:
                    for k in range(3):
                        # find 2 vertex that share vertex/UV data
                        if((m1 == face_data[triIdx * 3 + k]) and  # compare vertex...
                           (m2 == face_data[triIdx * 3 + ((k + 1) % 3)]) and
                           (u1 == uv_data[triIdx * 3 + k]) and  # compare texture indices
                           (u2 == uv_data[triIdx * 3 + ((k + 1) % 3)])):

                            # move to next vertex loop
                            m1 = face_data[triIdx * 3 + ((k + 2) % 3)]
                            u1 = uv_data[triIdx * 3 + ((k + 2) % 3)]

                            cmdVerts.append(face_data[triIdx * 3 + ((k + 2) % 3)])
                            cmdUV.append(uv_data[triIdx * 3 + ((k + 2) % 3)])
                            cmdLength += 1
                            cmdTris.append(triIdx)

                            usedFace[triIdx] = 2
                            triIdx = startTri + 1  # restart looking
                            # hypo TODO: check this. go back n test all tri again?

            # clear used counter
            for fc in range(startTri, numFaces):
                if usedFace[fc] == 2:
                    usedFace[fc] = 0
            # for fIdx, f in enumerate(usedFace):
            #     if f == 2:
            #         usedFace[fIdx] = 0

            return cmdLength
        # end findFanLength_fn

        cmdTris = []
        cmdVerts = []
        cmdUV = []
        bestVerts = []
        bestTris = []
        bestUV = []
        mdxID = 0  # mdx hitbox index number
        ofsetVertID = 0   # multi object offset
        numCommands = 1  # add 1 for final NULL at end
        # loop through selected mesh/s
        for tmp_mesh in self.frameData[0]:
            numFaces = tmp_mesh[IDX_I_FACE]
            usedFace = [0] * numFaces  # has face been used. array
            # break up mesh for quicker processing. SPEED
            for startIdx in range(0, numFaces, 256):
                curMax = 256 if (numFaces - startIdx) >= 256 else (numFaces - startIdx)
                curMax = startIdx + curMax
                # loop through face range
                for triIdx in range(startIdx, curMax):
                    #for triIdx in range(numFaces):
                    if not usedFace[triIdx]:
                        # intialization
                        bestLength = 0
                        bestType = 0
                        bestVerts = []
                        bestTris = []
                        bestUV = []

                        for startVert in range(3):
                            cmdVerts = []
                            cmdTris = []
                            cmdUV = []
                            cmdLength = findFanLength_fn(
                                usedFace, tmp_mesh, triIdx, startVert, curMax,  # numFaces,
                                cmdTris, cmdVerts, cmdUV)
                            if cmdLength > bestLength:
                                bestType = 1
                                bestLength = cmdLength
                                bestVerts = cmdVerts
                                bestTris = cmdTris
                                bestUV = cmdUV

                            cmdVerts = []
                            cmdTris = []
                            cmdUV = []
                            cmdLength = findStripLength_fn(
                                usedFace, tmp_mesh, triIdx, startVert, curMax,  # numFaces,
                                cmdTris, cmdVerts, cmdUV)
                            if cmdLength > bestLength:
                                bestType = 0
                                bestLength = cmdLength
                                bestVerts = cmdVerts
                                bestTris = cmdTris
                                bestUV = cmdUV

                        # mark tringle as used
                        for usedCounter in range(bestLength):
                            usedFace[bestTris[usedCounter]] = 1

                        cmd = []
                        if bestType == 0:   # strip
                            num = bestLength + 2
                        else:               # fan
                            num = (-(bestLength + 2))

                        numCommands += 1
                        if self.isMdx:  # mdx
                            numCommands += 1  # sub-object number

                        uv_layer = tmp_mesh[IDX_XY_UV]  # uv_cords
                        for cmdCounter in range(bestLength + 2):
                            cmd.append((0.0 + uv_layer[bestUV[cmdCounter]][0],  # X uv cords
                                        1.0 - uv_layer[bestUV[cmdCounter]][1],  # Y uv cords
                                        bestVerts[cmdCounter] + ofsetVertID))   # vertex number
                            numCommands += 3

                        self.glCmdList.append((
                            num,   # fan/strip count
                            mdxID,  # object number
                            cmd))   # S, T, vIdx

                printProgress_fn(startIdx, numFaces, prefix)  # print progress
            #  multi part object offset
            ofsetVertID += len(tmp_mesh[IDX_XYZ_V])
            mdxID += 1 if self.ui_opt_use_hitbox else 0
            del usedFace

        printDone_fn(self.start_time, prefix)  # Done.
        # print("GLCommands. (Count: {})".format(numCommands))
        del cmdVerts, cmdUV, cmdTris, bestVerts, bestUV, bestTris
        return numCommands

    # TODO
    def getSkins_fn(self, obj_sel, method):
        '''TODO change this
        SKIN_MAT_NAME = get materal names, then check for valid images for size
        SKIN_TEX_NAME = get texture names, then check for valid image for size
        SKIN_TEX_PATH = use texture image path and size.
        TODO: UV image?
        '''
        def check_skip_material(mat):
            """Simple helper to check whether we actually support exporting that material or not"""
            return mat.type not in {'SURFACE'} or mat.use_nodes

        def stripLeadingPath(path):
            tmpPath = bpy.path.abspath(path)  # , library=n.image.library)
            tmpPath = os.path.normpath(tmpPath)
            tmpPath = tmpPath.replace('\\', '/')
            texname = ""
            modelIdx = tmpPath.find("models" + os.sep)
            plyerIdx = tmpPath.find("players" + os.sep)
            textrIdx = tmpPath.find("textures" + os.sep)
            if modelIdx >= 0:
                texname = tmpPath[modelIdx:]
            elif plyerIdx >= 0:
                texname = tmpPath[plyerIdx:]
            elif textrIdx >= 0:
                texname = tmpPath[textrIdx:]
            else:
                texname = tmpPath
            return texname

        def appendSkins(skins, texname):
            if texname and len(texname) > 0:
                if texname not in skins and len(skins) <= MD2_MAX_SKINS:
                    skins.append(texname)

        def updateWH(size, found, outW, outH):
            if size[0] > 0 and size[1] > 0:
                width = size[0]
                height = size[1]
                if not found:
                    outW = width
                    outH = height
                    found = True
                else:
                    if width > outW:
                        outW = width
                    if height > outH:
                        outH = height
            return outW, outH, found

        self.start_time = printStart_fn()  # reset timmer
        prefix = "Getting Skins"
        printProgress_fn(0, 1, prefix)  # print progress
        skins = []
        width = height = 256
        foundWH = False  # find largest image

        for obj in obj_sel:
            materials = obj.data.materials[:]
            # material_names = [m.name if m else None for m in materials]
            for m_idx, mat in enumerate(materials):
                if not mat:
                    continue
                texname = mat.name
                if method == 'SKIN_MAT_NAME':
                    appendSkins(skins, texname)

                # use nodes
                if mat.use_nodes:
                    # search node images for dimensions/name
                    for n in mat.node_tree.nodes:
                        if n and n.type == 'TEX_IMAGE' and n.image:
                            image = n.image
                            width, height, foundWH = updateWH(
                                image.size, foundWH, width, height)  # set image size
                            # set skin
                            if method == "SKIN_TEX_NAME":
                                texname = image.name
                                appendSkins(skins, texname)
                            elif method == "SKIN_TEX_PATH":
                                texname = stripLeadingPath(image.filepath)
                                appendSkins(skins, texname)
                            # elif method == 'SKIN_MAT_NAME':
                # B2.7 use 'texture'
                elif hasattr(mat, "texture_slots"):
                    # search texture slots for dimensions/name
                    for mtex in mat.texture_slots:
                        if mtex and mtex.texture.type == 'IMAGE' and mtex.texture.image:
                            image = mtex.texture.image
                            if mtex.use_map_color_diffuse:
                                width, height, foundWH = updateWH(
                                    image.size, foundWH, width, height)  # set image size
                                # set skin
                                if method == "SKIN_TEX_NAME":
                                    appendSkins(skins, image.name)
                                elif method == "SKIN_TEX_PATH":
                                    texname = stripLeadingPath(image.filepath)
                                    appendSkins(skins, texname)
                                # elif method == 'SKIN_MAT_NAME':
                '''else:  # TODO no nodes? use uv name?
                    # use uv name/texture?'''

        printDone_fn(self.start_time, prefix)  # Done.
        print("Count:  {}\n".format(len(skins)) +
            "Width:  {}\n".format(width) +
            "Height: {}".format(height))
        for idx, skin in enumerate(skins):
            print("skin{}:  {}".format(idx + 1, skin[0:MD2_MAX_SKINNAME]))
        if height > 480 or width > 480:
            print("WARNING: found texture larger than kingpin max 480px")

        print("===============")
        # set min/max (kp crashes with more then 480, but is not use by opengl render)
        if width < 16:
            width = 16
        if height < 16:
            height = 16
        if height > 480:
            height = 480
        if width > 480:
            width = 480

        self.skinWidth = width
        self.skinHeight = height
        self.skins = skins

    def buildFrameNames_fn(self):
        '''
        sort the markers. The marker with the frame number closest to 0 will be the first marker in the list.
        The marker with the biggest frame number will be the last marker in the list'''
        name = []
        timeLineMarkers = []
        for marker in bpy.context.scene.timeline_markers:
            timeLineMarkers.append(marker)

        timeLineMarkers.sort(key=lambda marker: marker.frame)
        markerIdx = 0
        # delete markers at same frame positions
        if len(timeLineMarkers) > 1:
            markerFrame = timeLineMarkers[len(timeLineMarkers) - 1].frame
            for i in range(len(timeLineMarkers) - 2, -1, -1):
                if timeLineMarkers[i].frame == markerFrame:
                    del timeLineMarkers[i]
                else:
                    markerFrame = timeLineMarkers[i].frame
        for frame in range(self.numFrames):
            frame_idx = frame - self.ui_opt_fr_start + 1
            # build frame names
            if len(timeLineMarkers) != 0:
                fNameIdx = 1
                if markerIdx + 1 != len(timeLineMarkers):
                    if frame >= timeLineMarkers[markerIdx + 1].frame:
                        markerIdx += 1
                        fNameIdx = 1
                    else:
                        fNameIdx += 1
                name.append(timeLineMarkers[markerIdx].name + ('%02d' % fNameIdx))
            else:
                name.append("frame_" + str(frame_idx))
        return name

    def calcSharedBBox_fn(self):
        ''' option to make bbox size across all frames the same
            this fixes vertex wobble in parts of mesh that dont move
        '''
        self.bbox_min = []
        self.bbox_max = []  # clear bbox
        min = [9999.0, 9999.0, 9999.0]
        max = [-9999.0, -9999.0, -9999.0]

        for frame in range(self.numFrames):
            if not self.ui_opt_share_bbox:  # .options
                # reset bounding box
                min = [9999.0, 9999.0, 9999.0]
                max = [-9999.0, -9999.0, -9999.0]
            meshes = self.frameDataBBox[frame] if self.ui_opt_is_player else self.frameData[frame]
            for tmp_mesh in meshes:
                for vert in tmp_mesh[IDX_XYZ_V]:
                    for i in range(3):
                        if vert[i] < min[i]:
                            min[i] = vert[i]
                        if vert[i] > max[i]:
                            max[i] = vert[i]

            # add new bbox for each frame
            if not self.ui_opt_share_bbox or self.ui_opt_is_player:  # .options
                self.bbox_min.append(min)
                self.bbox_max.append(max)

        # store only 1 bbox
        if self.ui_opt_share_bbox:  # .options
            self.bbox_min.append(min)
            self.bbox_max.append(max)

    def calculateHitBox_fn(self):
        ''' mdx hitbox '''
        # if self.isMdx:
        for frame in range(self.numFrames):
            hitboxTmp = []
            hitboxMin = [9999, 9999, 9999]
            hitboxMax = [-9999, -9999, -9999]
            for tmp_mesh in self.frameData[frame]:
                if self.ui_opt_use_hitbox:  # option: seperate hitbox for players
                    hitboxMin = [9999, 9999, 9999]
                    hitboxMax = [-9999, -9999, -9999]

                for vert in tmp_mesh[IDX_XYZ_V]:
                    for i in range(3):
                        if vert[i] < hitboxMin[i]:
                            hitboxMin[i] = vert[i]
                        if vert[i] > hitboxMax[i]:
                            hitboxMax[i] = vert[i]

                if self.ui_opt_use_hitbox:
                    hitboxTmp.append([hitboxMin[0], hitboxMin[1], hitboxMin[2],
                                    hitboxMax[0], hitboxMax[1], hitboxMax[2]])

            if not self.ui_opt_use_hitbox:
                hitboxTmp.append([hitboxMin[0], hitboxMin[1], hitboxMin[2],
                                hitboxMax[0], hitboxMax[1], hitboxMax[2]])

            self.hitbox.append(hitboxTmp)

    # TODO speed boost VN list
    def calculateVNornIndex_fn(self):
        '''find the closest normal for every vertex on all frames
            TODO speed this up somehow?
            162*MD2_MAX_VERTS*MD2_MAX_FRAMES = 339mil
        '''
        # import numpy as np  # todo test

        # self.vNormData = [None] * self.numFrames
        self.start_time = printStart_fn()  # reset timmer
        # print('=====')
        prefix = "Calculate vertex normals"
        for frame in range(self.numFrames):
            if self.numFrames < 50 or (frame % 20) == 0:
                printProgress_fn(frame, self.numFrames, prefix)  # print progress
            m_tmp = []
            for tmp_mesh in self.frameData[frame]:
                vn_tmp = [0] * tmp_mesh[IDX_I_VERT]
                for i, vn in enumerate(tmp_mesh[IDX_XYZ_VN]):
                    maxDot = vn[0] * MD2_VN[0][0] + vn[1] * MD2_VN[0][1] + vn[2] * MD2_VN[0][2]
                    bestIdx = 0
                    for iN in range(1, 162):
                        # dot = np.dot(vnorm, MD2_VN[iN])
                        # dot = sum(vnorm[j] * MD2_VN[iN][j] for j in range(3))
                        dot = vn[0] * MD2_VN[iN][0] + vn[1] * MD2_VN[iN][1] + vn[2] * MD2_VN[iN][2]
                        if dot > maxDot:
                            maxDot = dot
                            bestIdx = iN
                            if maxDot > 0.99:  # stop wasting time
                                break
                    vn_tmp[i] = bestIdx  # normal index
                m_tmp.append(vn_tmp)  # object
                del vn_tmp
            self.vNormData.append(m_tmp)  # frame
        del m_tmp
        printDone_fn(self.start_time, prefix)  # Done.

    def get_numTris(self):
        triCount = 0  # self.numTris
        for tmp_mesh in self.frameData[0]:
            triCount += tmp_mesh[IDX_I_FACE]

        if self.ui_opt_is_hd == True:
            if triCount > MDX5_MAX_TRIANGLES:  # MDX5_VERSION TODO
                raise RuntimeError(
                    "Object has too many (triangulated) faces (%i), at most %i are supported in mdx HD"
                    % (triCount, MDX5_MAX_TRIANGLES))
        else:
            if triCount > MD2_MAX_TRIANGLES:
                raise RuntimeError(
                    "Object has too many (triangulated) faces (%i), at most %i are supported in md2"
                    % (triCount, MD2_MAX_TRIANGLES))
        return triCount

    def get_numVerts(self):
        vertCount = 0  # self.numVerts
        for tmp_mesh in self.frameData[0]:
            vertCount += tmp_mesh[IDX_I_VERT]

        if self.ui_opt_is_hd == True:
            if vertCount > MDX5_MAX_VERTS:  # MDX5_VERSION
                raise RuntimeError(
                    "Object has too many (triangulated) faces (%i), at most %i are supported in mdx HD"
                    % (vertCount, MDX5_MAX_VERTS))
        else:
            if vertCount > MD2_MAX_VERTS:
                raise RuntimeError(
                    "Object has too many (triangulated) faces (%i), at most %i are supported in md2"
                    % (vertCount, MD2_MAX_VERTS))
        return vertCount

    def get_numUV(self):
        uvCount = 0
        for tmp_mesh in self.frameData[0]:
            uvCount += tmp_mesh[IDX_I_UV]
        return uvCount

    self.obj_array = []
    self.frameData = []
    self.frameDataBBox = []
    self.hitbox = []  # mdx hitbox
    self.vertCounter = []
    self.glCmdList = []
    self.vNormData = []

    self.vertices = -1
    self.faces = 0
    self.status = ('', '')
    self.numFrames = 1 if not self.ui_opt_animated else (1 + self.ui_opt_fr_end - self.ui_opt_fr_start)
    if self.numFrames > MD2_MAX_FRAMES:
        raise RuntimeError(
            "There are too many frames (%i), at most %i are supported in md2/mdx"
            % (self.numFrames, MD2_MAX_FRAMES))

    getSkins_fn(self, self.objects_sel, self.ui_opt_tex_name)  # get texture names
    self.frameNames = buildFrameNames_fn(self)  # setup frame names
    setupInternalArrays_fn(self)  # generate mesh/objects
    calcSharedBBox_fn(self)       # get min/max dimensions
    calculateVNornIndex_fn(self)  # slow

    self.numSkins = len(self.skins)
    self.numVerts = get_numVerts(self)
    self.numTris = get_numTris(self)
    self.numGLCmds = buildGLcommands_fn(self)
    if self.ui_opt_is_hd == False:
        self.frameSize = struct.calcsize("<6f16s") + (struct.calcsize("<4B") * self.numVerts)
    else:
        self.frameSize = struct.calcsize("<6f16s") + (struct.calcsize("<7B") * self.numVerts)

    # setup md2/mdx header
    if self.isMdx:
        self.ident = 1481655369
        self.version = 4
        calculateHitBox_fn(self)
        self.numSfxDefines = 0  # mdx
        self.numSfxEntries = 0  # mdx
        self.numSubObjects = 1 if not self.ui_opt_use_hitbox else len(self.objects_sel)
        # offsets
        self.ofsSkins = struct.calcsize("<23i")
        self.ofsTris = self.ofsSkins + struct.calcsize("<64s") * self.numSkins
        self.ofsFrames = self.ofsTris + struct.calcsize("<6H") * self.numTris
        self.ofsGLCmds = self.ofsFrames + self.frameSize * self.numFrames
        self.ofsVertexInfo = self.ofsGLCmds + struct.calcsize("<i") * self.numGLCmds  # mdx
        self.ofsSfxDefines = self.ofsVertexInfo + struct.calcsize("<i") * (self.numVerts)  # mdx
        self.ofsSfxEntries = self.ofsSfxDefines  # mdx
        self.ofsBBoxFrames = self.ofsSfxEntries  # mdx
        self.ofsDummyEnd = (
            self.ofsBBoxFrames + struct.calcsize("<6i") *
            (self.numFrames * self.numSubObjects))  # mdx
        self.ofsEnd = self.ofsDummyEnd
    else:
        self.ident = 844121161
        self.version = 8
        self.numUV = get_numUV(self)
        # offsets
        self.ofsSkins = struct.calcsize("<17i")
        self.ofsUV = self.ofsSkins + struct.calcsize("<64s") * self.numSkins
        self.ofsTris = self.ofsUV + struct.calcsize("<2h") * self.numUV
        self.ofsFrames = self.ofsTris + struct.calcsize("<6H") * self.numTris
        self.ofsGLCmds = self.ofsFrames + self.frameSize * self.numFrames
        self.ofsEnd = self.ofsGLCmds + struct.calcsize("<i") * self.numGLCmds


def write_fn(self, filePath):
    ''' write file '''

    self.start_time = printStart_fn()  # reset timmer
    prefix = "Writing file"
    #
    file = open(filePath, "wb")
    try:
        # ####################
        # ### write header ###
        if self.isMdx:  # mdx
            data = struct.pack(
                "<23i", self.ident, self.version,
                self.skinWidth, self.skinHeight,
                self.frameSize,
                self.numSkins, self.numVerts, self.numTris, self.numGLCmds, self.numFrames,
                self.numSfxDefines, self.numSfxEntries, self.numSubObjects,  # mdx
                self.ofsSkins, self.ofsTris, self.ofsFrames, self.ofsGLCmds,
                self.ofsVertexInfo, self.ofsSfxDefines, self.ofsSfxEntries, self.ofsBBoxFrames,  # mdx
                self.ofsDummyEnd,  # mdx
                self.ofsEnd)
        else:  # ms2
            data = struct.pack(
                "<17i", self.ident, self.version,
                self.skinWidth, self.skinHeight,
                self.frameSize,
                self.numSkins, self.numVerts, self.numUV, self.numTris, self.numGLCmds, self.numFrames,
                self.ofsSkins, self.ofsUV, self.ofsTris, self.ofsFrames, self.ofsGLCmds,
                self.ofsEnd)
        file.write(data)

        # #############################
        # ### write skin file names ###
        for skinName in self.skins:  # enumerate(# TODO file path?
            data = struct.pack("<64s", bytes(skinName[0:(MD2_MAX_SKINNAME - 1)], encoding="utf8"))
            file.write(data)  # skin name
        del self.skins  # TODO

        # ###############################
        # ### write software uv byte ###
        if not self.isMdx:  # MD2
            for tmp_mesh in self.frameData[0]:
                # tmp_mesh[IDX_I_UV]
                for uv in tmp_mesh[IDX_XY_UV]:
                    data = struct.pack(
                        "<2h",
                        int(uv[0] * self.skinWidth),
                        int((1 - uv[1]) * self.skinHeight))  # TODO check invalid 0-1 uv space
                    file.write(data)  # uv

        # #################################
        # ### write triangle index data ###
        ofsetVertID = 0
        objIdx = 0
        for tmp_mesh in self.frameData[0]:
            face = tmp_mesh[IDX_IDC_V]
            uv = tmp_mesh[IDX_IDC_UV]
            for idx in range(tmp_mesh[IDX_I_FACE]):
                # 0,2,1 for good cw/ccw
                data = struct.pack(
                    "<3H",  # ### write vert indices ###
                    face[idx * 3 + 0] + ofsetVertID,
                    face[idx * 3 + 2] + ofsetVertID,
                    face[idx * 3 + 1] + ofsetVertID)
                file.write(data)  # vert uv index data

                data = struct.pack(
                    "<3H",  # ### write tex cord indices ###
                    uv[idx * 3 + 0] + ofsetVertID,  # (uv idc)
                    uv[idx * 3 + 2] + ofsetVertID,  # (uv idc)
                    uv[idx * 3 + 1] + ofsetVertID)  # (uv idc)
                file.write(data)  # uv index

            ofsetVertID += len(tmp_mesh[IDX_IDC_V])
            self.vertCounter.append(len(tmp_mesh[IDX_XYZ_V]))

        # ####################
        # ### write frame/s ###
        for frame in range(self.numFrames):
            if self.numFrames < 50 or (frame % 20) == 0:
                printProgress_fn(frame, self.numFrames, prefix)  # print progress

            # output frames to file
            write_frame_fn(self, file, frame, self.frameNames[frame])
        ###########################
        # ### write GL Commands ###
        for glCmd in self.glCmdList:
            if self.isMdx:
                data = struct.pack(
                    "<iL",
                    glCmd[0],  # TrisTypeNum
                    glCmd[1])  # SubObjectID
            else:
                data = struct.pack(
                    "<i",
                    glCmd[0])  # TrisTypeNum
            file.write(data)

            for cmd in glCmd[2]:
                data = struct.pack(
                    "<ffI",
                    cmd[0],  # texture X
                    cmd[1],  # texture Y
                    cmd[2])  # vertex index
                file.write(data)
        # NULL GLCommand
        data = struct.pack("<I", 0)
        file.write(data)

        ###################
        # ### mdx stuff ###
        if self.isMdx:
            # ofsVertexInfo #mdx
            for mdxObj, tmp_mesh in enumerate(self.frameData[0]):
                for vert in range(tmp_mesh[IDX_I_VERT]):
                    if self.ui_opt_use_hitbox:
                        bits = (1 << mdxObj)
                    else:
                        bits = 1
                    data = struct.pack("<i", bits)  # fill as object #1 TODO
                    file.write(data)  # vert index

            # ofsSfxDefines #mdx
            # ofsSfxEntries #mdx
            # ofsBBoxFrames #mdx
            for mdxObj in range(self.numSubObjects):
                for i in range(self.numFrames):
                    data = struct.pack(
                        "<6f",
                        self.hitbox[i][mdxObj][0],
                        self.hitbox[i][mdxObj][1],
                        self.hitbox[i][mdxObj][2],
                        self.hitbox[i][mdxObj][3],
                        self.hitbox[i][mdxObj][4],
                        self.hitbox[i][mdxObj][5])
                    file.write(data)
    finally:
        file.close()

    printDone_fn(self.start_time, prefix)  # Done.
    # print("Model exported.")
    # TODO cleanup arrays
    del self.frameNames, self.frameData, self.frameDataBBox, self.vNormData


def Export_MD2_fn(self, context, filepath):
    '''    Export model    '''
    startTime = printStart_fn() # total time
    self.start_time = startTime

    ui_export_ = context.window_manager.kp_export_
    self.ui_opt_animated = ui_export_.ui_opt_animated
    self.ui_opt_is_player = ui_export_.ui_opt_is_player
    self.ui_opt_share_bbox = ui_export_.ui_opt_share_bbox
    self.ui_opt_use_hitbox = ui_export_.ui_opt_use_hitbox
    self.ui_opt_tex_name = ui_export_.ui_opt_tex_name
    self.ui_opt_fr_start = ui_export_.ui_opt_fr_start
    self.ui_opt_fr_end = ui_export_.ui_opt_fr_end
    self.ui_opt_apply_modify = True #ui_export_.ui_opt_apply_modify
    self.ui_opt_is_hd = ui_export_.ui_opt_is_hd
    self.ui_opt_cust_vn = ui_export_.ui_opt_cust_vn

    # fix invalid state
    if self.ui_opt_is_player:
        self.ui_opt_share_bbox = False
    if self.ui_opt_apply_modify == False:
        self.ui_opt_cust_vn = False

    try:
        setup_data_fn(self, context)
        write_fn(self, filepath)
        # total time
        printDone_fn(startTime, "Total time")  # Done.
    except Exception as e:
        print("Caught error exporting model")
        print(e)
        # raise RuntimeError("Only mesh objects can be exported")
