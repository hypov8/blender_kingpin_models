'''
importer class/func

class KP_Util_Import

class Import_MD2(Operator, ImportHelper)
'''

import struct
import os
import bpy
from bpy.props import (
    StringProperty,
    CollectionProperty,
    BoolProperty,
    EnumProperty,
    )
from bpy.types import Operator, PropertyGroup
from bpy_extras.io_utils import ImportHelper
from bpy_extras.io_utils import unpack_list #, ImportHelper
from bpy_extras.image_utils import load_image
from mathutils import Vector
from . pcx_file import read_pcx_file
from . common_kp import (
    BL_VER,
    MDX_IDENT,
    MDX_VERSION,
    MD2_IDENT,
    MD2_VERSION,
    MD2_VN,
    DATA_V_BYTE,
    DATA_F_SCALE,
    DATA_F_COUNT,
    DATA_V_COUNT,
    get_addon_preferences,
    printStart_fn,
    printProgress_fn,
    printDone_fn,
    set_object_link,
    get_uv_data_new,
    get_objects_all,
    get_layers,
    set_select_state
)

# -|GUI|- import Properties
class KINGPIN_Import_props(PropertyGroup):
    ui_opt_store_pcx = BoolProperty(
        name="Store .pcx Internaly",
        description=(
            "Loading .pcx files are not suported by blender.\n"+
            "This will store the image into the blend file so it can be loaded.\n" +
            "Note: you will need to manualy remove data to reduce file size later."),
        default=True,
    )
    ui_opt_anim = BoolProperty(
        name="Import Animations",
        description="Import animation frame names to time line",
        default=True,
    )
    ui_opt_anim_type = EnumProperty(
        name="Type",
        description="Import all frames",
        items=(
            #('NONE', "None", "No animations", 0),  # force no animation
            ('SK_VERTEX', "1.Vertex Keys", "Animate using vertex data", 1),
            ('SK_ABS', "2.Shape Key (absolute)", "Use action graph for animations", 2),
            # ('SK_SINGLE', "Shape Keys (Single)", "Animate using only 1 shape key", 3),
            ('SK_MULTI', "3.Shape Keys (Relative)",
             "Add shape key's for every frame.\n" +
             "Import speed is faster, but mesh is harder to edit.\n" +
             "Note: this is the old plugin method.", 3)
        ),
        default="SK_VERTEX",
    )
    ui_opt_frame_names = BoolProperty(
        name="Import Frame Names",
        description="Import animation frame names to time line\n" +
        "WARNING: Removes all existing marker frame names",
        default=False,
    )
    ui_dupe_mat = BoolProperty(
        name="Use Existing Material",
        description="If material name exists, model will use the existing material",
        default=True,
    )
    '''
    # TODO SK_ABS Interpolation
    ui_opt_sk_types = EnumProperty(
        name="key type",
        description="Import all frames",
        items=(
            ('NONE', "None", "", 0),
            ('KEY_LINEAR', "Linear", "", 1),
            ('KEY_CARDINAL', "Cardinal", "", 2),
            ('KEY_CATMULL_ROM', "Catmull-Rom", "", 3),
            ('KEY_BSPLINE', "BSpline", "", 4),
        ),
        default="NONE",
    )
    '''
    ui_skip_cleanup = BoolProperty(
        name="Skip Mesh Cleanup",
        description=(
            "Blender does some error checking on mesh before importing.\n"
            "This may delete some faces/vertex. "
            "Enabled: Stops any mesh validation checks.\n"
            "  Use if you find mesh is missing valuable data.\n" +
            "  Make sure you fix model before exporting"),
        default=False,
    )


class KINGPIN_Import_Button(Operator):
    ''' Export selection to Kingpin file format (md2/mdx) '''
    bl_idname = "kp.import_model_button"
    bl_label = "Import md2/mdx"
    filename_ext = {".mdx", ".md2"}  # md2 used later
    check_extension = True

    if bpy.app.version < (2, 80):
        filter_glob = StringProperty(default="*.md2;*.mdx", options={'HIDDEN'})
        files = CollectionProperty(type=PropertyGroup)
        filepath = StringProperty(maxlen=1024, subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    else:
        filter_glob: StringProperty(default="*.md2;*.mdx", options={'HIDDEN'})
        files: CollectionProperty(type=PropertyGroup)
        filepath: StringProperty(maxlen=1024, subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        # kp_import_ = context.window_manager.kp_import_
        user_prefs = get_addon_preferences(context)
        if user_prefs.pref_kp_import_button_use_dialog:
            self.filepath = ""
        else:
            self.filepath = ""

        execute_import(self, context)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def draw_import(self, context):
    ''' draw input gui '''
    layout = self.layout
    ui_import_ = context.window_manager.kp_import_
    # general options
    misc_box = layout.box()
    misc_box.prop(ui_import_, "ui_dupe_mat")
    misc_box.prop(ui_import_, "ui_opt_store_pcx")
    misc_box.prop(ui_import_, "ui_skip_cleanup")

    # animation options
    anim_box = layout.box()
    anim_box.prop(ui_import_, "ui_opt_anim")
    if ui_import_.ui_opt_anim:
        anim_box.prop(ui_import_, "ui_opt_anim_type")
        # sub.prop(ui_import_, "ui_opt_sk_types")
        # show 'frame name' option when importing animation
        anim_box.prop(ui_import_, "ui_opt_frame_names")
        if ui_import_.ui_opt_frame_names:
            anim_box.label(text="WARNING: Removes existing names")


# TODO file picker...
def execute_import(self, context):
    ver = BL_VER # bl_info.get("version")
    # ui_import_ = context.window_manager.kp_import_

    print("===============================================\n" +
            "Kingpin Model Importer v%i.%i.%i" % (ver[0], ver[1], ver[2]))

    if not bpy.context.mode == 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')  # , toggle=False)
    # deselect any objects
    for ob in bpy.data.objects:
        set_select_state(context=ob, opt=False)

    # multiple 'selected' file loader
    valid = 1
    folder = os.path.dirname(os.path.abspath(self.filepath))
    for f in self.files:
        fPath = (os.path.join(folder, f.name))
        print("===============================================")
        ret = load_kp_model(self, context, fPath)

        if ret == 2:
            valid = 2  # stop print
        if not ret:
            print("Error: in %s" % fPath)
            return {'FINISHED'}

    get_layers(bpy.context).update()  # v1.2.2
    if valid == 1:
        self.report({'INFO'}, "File '%s' imported" % self.filepath)
    else:
        self.report({'WARNING'}, "Warning: see console")


class KINGPIN_Import_Dialog(Operator, ImportHelper):
    '''Import Kingpin format file (md2/mdx)'''
    bl_idname = "kp.import_model_dialog"
    bl_label = "Import md2/mdx"
    filename_ext = {".mdx", ".md2"}

    if bpy.app.version < (2, 80):
        filter_glob = StringProperty(default="*.md2;*.mdx", options={'HIDDEN'})
        files = CollectionProperty(type=PropertyGroup)
        filepath = StringProperty(maxlen=1024, subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    else:
        filter_glob: StringProperty(default="*.md2;*.mdx", options={'HIDDEN'})
        files: CollectionProperty(type=PropertyGroup)
        filepath: StringProperty(maxlen=1024, subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    def invoke(self, context, event):
        print("invoke")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        execute_import(self, context)
        return {'FINISHED'}

    def draw(self, context):
        draw_import(self, context)


class Kingpin_Model_Reader:
    ''' Kingpin Model Reader '''

    def makeObject(self):

        self.start_time = printStart_fn()  # reset timmer
        prefix = "Generating Mesh"
        printProgress_fn(0, self.numFrames, prefix)  # print progress

        int_frame = bpy.context.scene.frame_current
        bpy.context.scene.frame_set(0)

        # ###################
        # 2.8 Create the mesh
        md2_mesh = bpy.data.meshes.new(self.name)
        md2_mesh.from_pydata(self.v_pos[0], [], self.tris)  # new 2.8 method
        printDone_fn(self.start_time, prefix)  # Finish mesh data

        print("num poly=%i" % (len(md2_mesh.polygons)))
        print("num vert=%i" % (len(md2_mesh.vertices)))

        # ##########
        # skins data
        image_array = []
        if self.numSkins > 0:
            self.start_time = printStart_fn()  # reset timmer
            prefix = ""
            suffix = "Generating Materials"
            print("========")
            #      "Generate Materials:")
            print("skins: %i" % len(self.skins))  # print count

            for skin in self.skins:
                # print("skin_%i: %s" % (idx + 1, skin), end='')  # print name
                prefix = str("%s%s" % (prefix, skin))

                if self.ui_dupe_mat:  # use old material if it exists
                    foundMat = False
                    for mat in bpy.data.materials[:]:
                        if mat.name == skin:
                            md2_mesh.materials.append(mat)
                            foundMat = True
                            break
                    if foundMat:
                        prefix = str("%s  Existing material\n" % prefix)  # " Existing material"
                        continue

                mat_id = bpy.data.materials.new(skin)  # new material
                md2_mesh.materials.append(mat_id)  # asign materal to mesh

                # get materal node/links
                mat_id.use_nodes = True
                mat_nodes = mat_id.node_tree.nodes
                mat_links = mat_id.node_tree.links
                # delete existing node
                while mat_nodes:
                    mat_nodes.remove(mat_nodes[0])

                # create diffuse/texture/output nodes
                node_tex = mat_nodes.new("ShaderNodeTexImage")  # image texture
                node_diff = mat_nodes.new(type='ShaderNodeBsdfDiffuse')  # simple shader
                node_out_mat = mat_nodes.new(type='ShaderNodeOutputMaterial')  # output Cycles
                # move nodes
                node_tex.location = Vector((-350, -80))
                node_out_mat.location = Vector((250, 0))  # output Cycles
                # create links
                mat_links.new(node_diff.outputs['BSDF'], node_out_mat.inputs['Surface'])
                mat_links.new(node_tex.outputs['Color'], node_diff.inputs['Color'])

                if bpy.app.version < (2, 80, 0):  # output blender render v2.79
                    node_output = mat_nodes.new(type='ShaderNodeOutput')
                    mat_links.new(node_tex.outputs['Color'], node_output.inputs['Color'])
                    node_output.location = Vector((250, -120))

                # try to load tga/pcx image
                skinImg = load_kingpin_image(mdxPath=skin,
                                             filePath=self.filePath,
                                             check_dupe=self.ui_dupe_mat,
                                             store_image=self.ui_opt_store_pcx)  # KP_Util_Import
                if skinImg is None:
                    skinImg = bpy.data.images.new(skin, self.skinWidth, self.skinHeight)
                    prefix = str("%s  Missing\n" % prefix)  # print(" Missing")
                else:
                    prefix = str("%s  OK\n" % prefix)  # print(" OK")
                # skinImg. mapping = 'UV' #2.7
                skinImg.name = skin
                image_array.append(skinImg)

                # link image to diffuse color
                node_tex.image = skinImg

            # Materials Done
            print(prefix, end='')
            print("========")
            printDone_fn(self.start_time, suffix)

        # #######
        # uv data
        self.start_time = printStart_fn()  # reset timmer
        prefix = "Generating UV"
        printProgress_fn(0, self.numFrames, prefix)  # print progress

        uv_type, uv_layer = get_uv_data_new(md2_mesh, uv_name="UVMap_0")  # v1.2.2
        image = None  # asign first image. TODO: cleanup
        for im in image_array:
            if im is not None:
                image = im
                break
        if uv_type == 1:  # B2.79 v1.2.2
            blen_uvs = md2_mesh.uv_layers[0]
            for i, pl in enumerate(md2_mesh.polygons):
                face = self.tris_uv[i]
                v1, v2, v3 = face
                blen_uvs.data[pl.loop_start + 0].uv = self.uv_cords[v1]
                blen_uvs.data[pl.loop_start + 1].uv = self.uv_cords[v2]
                blen_uvs.data[pl.loop_start + 2].uv = self.uv_cords[v3]
                pl.use_smooth = True  # smooth all faces
                md2_mesh.uv_textures[0].data[i].image = image  # set face texture
        elif uv_type == 2:  # B2.8 v1.2.2
            for i, face in enumerate(md2_mesh.polygons):
                face.use_smooth = True
                uv_x = self.tris_uv[i]
                # dat = md2_mesh.uv_layers[0].data[i].image = imag
                for uvid, (vert_idx, loop_idx) in enumerate(zip(face.vertices, face.loop_indices)):
                    uv_layer.data[loop_idx].uv = (self.uv_cords[uv_x[uvid]][0],
                                                  self.uv_cords[uv_x[uvid]][1])
        # Done.
        printDone_fn(self.start_time, prefix)  # Finish uv data

        #######################
        # validate/update model
        if not self.ui_skip_cleanup:
            err = md2_mesh.validate(verbose=True, clean_customdata=False)  # print errors
            if err:
                print("--------\n" +
                      "WARNING: Found invalid mesh data.\n"
                      "  Enable \"Skip checks\" Cleanup if required\n" +
                      "--------\n")
                self.valid = 2
        md2_mesh.update()

        # create new object from mesh
        self.start_time = printStart_fn()  # reset timmer
        prefix = "Generating Object"
        printProgress_fn(0, self.numFrames, prefix)  # print progress

        obj = bpy.data.objects.new(md2_mesh.name, md2_mesh)
        set_object_link(bpy.context, obj)  # v1.2.2
        # select object
        set_select_state(context=obj, opt=True)  # 1.2.2
        # Print Done.
        printDone_fn(self.start_time, prefix)

        # ############
        # Animate mesh
        if self.numFrames > 1 and self.ui_opt_anim:
            self.start_time = printStart_fn()  # reset timmer
            prefix = "Generating Frames"

            # setup shape keys
            sk_type = 0
            sk_blocks = None
            sk_data = []
            obj_dat = obj.data
            ob_verts = obj.data.vertices
            # fCurvID = [None] * len(ob_verts)

            if self.ui_opt_anim_type == 'SK_VERTEX':
                sk_type = 1
            elif self.ui_opt_anim_type == 'SK_SINGLE':
                sk_type = 2
            elif self.ui_opt_anim_type == 'SK_MULTI':
                sk_type = 3
            elif self.ui_opt_anim_type == 'SK_ACTION':
                sk_type = 4
            elif self.ui_opt_anim_type == 'SK_ABS':
                sk_type = 5

            #######################
            # create key frames for vertex
            if sk_type == 1:
                '''ob_verts.foreach_set("co", unpack_list(self.v_pos[i]))
                for k, vert in enumerate(ob_verts):
                    vert.keyframe_insert(data_path="co", frame=i, group="V%s" % k)'''
                obj_dat.animation_data_create()
                obj_dat.animation_data.action = bpy.data.actions.new("KP_Anim")
                obj_act = obj_dat.animation_data.action

                for v in obj_dat.vertices:
                    fcurves = [obj_act.fcurves.new(
                        "vertices[%d].co" % v.index,
                        index=i,
                        action_group="V%s" % v.index) for i in range(3)]

                    for i in range(3):
                        fcurves[i].keyframe_points.add(self.numFrames)

                    for fr in range(self.numFrames):
                        v_co = self.v_pos[fr][v.index]
                        for i in range(3):
                            fcurves[i].keyframe_points[fr].co = fr, v_co[i]

                    for i in range(3):
                        fcurves[i].update()

                    printProgress_fn(v.index, self.numVerts, prefix)  # print progress
            ##########################
            # animate single shape key
            elif sk_type == 2:
                sk_data.append(obj.shape_key_add(name="Base", from_mix=False))  # hy.new
                sk_data.append(obj.shape_key_add(name="SK_0", from_mix=False))  # hy.new
                obj.active_shape_key_index = 1
                sk_data[1].value = 1.0
                obj.use_shape_key_edit_mode = True
                sk_blocks = obj_dat.shape_keys.key_blocks

                for i in range(self.numFrames):
                    sk_data[1].data.foreach_set("co", unpack_list(self.v_pos[i]))
                    for k, vert in enumerate(sk_data[1].data):
                        vert.keyframe_insert(data_path="co", frame=i, group="SK_0 V: %s" % k)

            #############################
            # animate multiple shape keys
            elif sk_type == 3:
                sk_data.append(obj.shape_key_add(name="Base", from_mix=False))  # hy.new
                sk_data.append(obj.shape_key_add(name="SK_0", from_mix=False))  # hy.new
                obj.active_shape_key_index = 1
                sk_data[1].value = 1.0
                obj.use_shape_key_edit_mode = True
                sk_blocks = obj_dat.shape_keys.key_blocks

                sk_i = 1
                for i in range(self.numFrames):
                    if i > 0:
                        sk_data.append(obj.shape_key_add(name=("SK_%i" % i), from_mix=False))
                        sk_i += 1
                    sk_data[sk_i].data.foreach_set("co", unpack_list(self.v_pos[i]))  # move vertex
                    # insert keys.
                    if i > 0:  # dont add keys to <-1> frame
                        sk_blocks[sk_i].value = 0.0
                        sk_blocks[sk_i].keyframe_insert("value", frame=i - 1)
                    sk_blocks[sk_i].value = 1.0
                    sk_blocks[sk_i].keyframe_insert("value", frame=i)
                    if i < (self.numFrames - 1):  # dont add keys to <last+1> frame
                        sk_blocks[sk_i].value = 0.0
                        sk_blocks[sk_i].keyframe_insert("value", frame=i + 1)
                    printProgress_fn(i, self.numFrames, prefix)  # print progress

            #############################
            # absolute shape keys
            elif sk_type == 5:
                # isSetInter = 0 if self.ui_opt_sk_types == 'NONE' else 1
                for i in range(self.numFrames):
                    # create shape key
                    sk_data.append(obj.shape_key_add(name=("skFrame_%i" % i), from_mix=False))
                    sk_data[i].data.foreach_set("co", unpack_list(self.v_pos[i]))  # move vertex
                    # insert keyframe.
                    # 2.7 buggy. when you press Re-Time Shape Keys (+ 10)
                    obj_dat.shape_keys.eval_time = (i * 10)
                    obj_dat.shape_keys.keyframe_insert(data_path='eval_time', frame=i)
                    # if (isSetInter):
                    # obj_dat.shape_keys.interpolation = self.ui_opt_sk_types
                    # obj_dat.shape_keys.keyframe_insert(data_path='interpolation', frame=i)
                    printProgress_fn(i, self.numFrames, prefix)  # print progress

                obj_dat.shape_keys.use_relative = False
                obj.use_shape_key_edit_mode = True
                obj.active_shape_key_index = 1  # updates display
                # bpy.ops.object.shape_key_retime()  # fix values

            ####################
            # import frame names
            if self.ui_opt_frame_names:  # reset frame names
                lastFName = ""
                mark = bpy.data.scenes[0].timeline_markers  # TODO scene
                mark.clear()
                fNames = self.frame_names
                for i in range(self.numFrames):
                    tmp_str = fNames[i].rstrip(b'0123456789')  # remove numbers
                    if not lastFName == tmp_str:
                        mark.new(tmp_str.decode('utf-8'), frame=i)
                        lastFName = tmp_str

            # set sceen timeline to match imported model
            bpy.context.scene.frame_start = 0
            bpy.context.scene.frame_end = self.numFrames - 1
            obj_dat.update()
            # Frames Done
            printDone_fn(self.start_time, prefix)

        # set frame back to old position
        bpy.context.scene.frame_set(int_frame)

        # add custom data
        obj.data[DATA_V_BYTE] = self.fr_v_idx
        obj.data[DATA_F_SCALE] = self.fr_scale
        obj.data[DATA_F_COUNT] = self.numFrames
        obj.data[DATA_V_COUNT] = self.numVerts

        get_objects_all(bpy.context).active = obj  # v1.2.2
        get_layers(bpy.context).update()  # v1.2.2
        print("Model imported.\n" +
              "===============================================")

    def read_file(self, filePath):
        ''' open .md2 file and read contents '''
        print("Reading %s" % filePath, end='')
        startTime = printStart_fn()  # reset timmer

        self.filePath = filePath
        self.name = os.path.splitext(os.path.basename(filePath))[0]
        self.ext = os.path.splitext(os.path.basename(filePath))[1]
        self.skins = []
        self.tris = []  # store triangle vertex index (idx1, idx2, idx3)
        self.tris_uv = []  # store triangles UV index (idx1, idx2, idx3)
        self.uv_cords = []  # UV float cordanates (X,Y)
        self.v_pos = []     # vertex position (X,Y,Z)
        self.v_norms = []   # vertex normal index
        self.frame_names = []

        # stored custom data
        self.fr_v_idx = []
        self.fr_scale = []

        inFile = open(file=self.filePath, mode="rb")
        try:
            print('.', end='')
            if self.isMdx:
                buff = inFile.read(struct.calcsize("<23i"))
                data = struct.unpack("<23i", buff)
                if not data[0] == MDX_IDENT:
                    raise NameError("Invalid MDX file (id)")
                if not data[1] == MDX_VERSION:
                    raise NameError("Invalid MDX file(version)")
                # fill header details
                self.skinWidth = max(1, data[2])
                self.skinHeight = max(1, data[3])
                self.framesize = data[4]
                self.numSkins = data[5]
                self.numVerts = data[6]
                self.numTris = data[7]
                self.numGLCmds = data[8]
                self.numFrames = 1 if not self.ui_opt_anim else data[9]
                self.ofsSkins = data[13]
                self.ofsTris = data[14]
                self.ofsFrames = data[15]
                self.ofsGLCmds = data[16]
            else:
                buff = inFile.read(struct.calcsize("<17i"))
                data = struct.unpack("<17i", buff)
                if not data[0] == MD2_IDENT:
                    raise NameError("Invalid MD2 file (id)")
                if not data[1] == MD2_VERSION:
                    raise NameError("Invalid MD2 file(version)")
                # fill header details
                self.skinWidth = max(1, data[2])
                self.skinHeight = max(1, data[3])
                self.framesize = data[4]
                self.numSkins = data[5]
                self.numVerts = data[6]
                self.numUV = data[7]
                self.numTris = data[8]
                self.numGLCmds = data[9]
                self.numFrames = 1 if not self.ui_opt_anim else data[10]
                self.ofsSkins = data[11]
                self.ofsUV = data[12]
                self.ofsTris = data[13]
                self.ofsFrames = data[14]
                self.ofsGLCmds = data[15]

            self.isHDmodel = True if (self.framesize == (40 + self.numVerts*7)) else False
            print('.', end='')

            # Skins
            if self.numSkins > 0:
                inFile.seek(self.ofsSkins, 0)
                for i in range(self.numSkins):
                    buff = inFile.read(struct.calcsize("<64s"))
                    data = struct.unpack("<64s", buff)
                    dataEx1 = data[0].decode("utf-8", "replace")
                    # dataEx1 = dataEx1 + "\x00"  # append null.
                    self.skins.append(asciiz(dataEx1))
            print('.')  # Done. #3

            # UV (software 1byte texture cords)
            if self.isMdx is False and self.numGLCmds <= 1:
                #
                self.start_time = printStart_fn()  # reset timmer
                prefix = "Reading Software UV"
                printProgress_fn(0, self.numFrames, prefix)  # print progress

                inFile.seek(self.ofsUV, 0)
                for i in range(self.numUV):
                    buff = inFile.read(struct.calcsize("<2h"))
                    data = struct.unpack("<2h", buff)
                    # self.uv_cords.append((data[0] / self.skinWidth, 1-(data[1]/self.skinHeight)))
                    # hypo add: index0
                    self.uv_cords.insert(
                        i, (data[0] / self.skinWidth, 1 - (data[1] / self.skinHeight)))

                # Tris (non GLCommand)
                inFile.seek(self.ofsTris, 0)
                for i in range(self.numTris):
                    buff = inFile.read(struct.calcsize("<6H"))
                    data = struct.unpack("<6H", buff)
                    self.tris.append((data[0], data[2], data[1]))
                    self.tris_uv.append((data[3], data[5], data[4]))  # 2.8 seperate uv
                # Done
                printDone_fn(self.start_time, prefix)  # Reading SW Texture cords

            else:
                self.start_time = printStart_fn()  # reset timmer
                prefix = "Reading GLCommands"
                printProgress_fn(0, self.numFrames, prefix)  # print progress

                # ====================================================================
                # UV GLCommands (float texture cords)
                inFile.seek(self.ofsGLCmds, 0)
                uvIdx = 0

                def readGLVertex(inFile):
                    buff = inFile.read(struct.calcsize("<2f1l"))
                    data = struct.unpack("<2f1l", buff)
                    s = data[0]
                    t = 1.0 - data[1]  # flip Y
                    idx = data[2]
                    return (s, t, idx)

                # for glx in range(self.numGLCmds): #wont get to this number
                while 1:
                    if self.isMdx is True:
                        buff = inFile.read(struct.calcsize("<2l"))
                        data = struct.unpack("<2l", buff)
                    else:  #md2
                        buff = inFile.read(struct.calcsize("<l"))
                        data = struct.unpack("<l", buff)
                    # read strip
                    if data[0] >= 1:
                        numStripVerts = data[0]
                        v2 = readGLVertex(inFile)
                        v3 = readGLVertex(inFile)
                        self.uv_cords.append((v2[0], v2[1]))
                        self.uv_cords.append((v3[0], v3[1]))
                        uvIdx += 2
                        for i in range(1, (numStripVerts - 1), 1):
                            v1 = v2[:]  # new ref
                            v2 = v3[:]  # new ref
                            v3 = readGLVertex(inFile)
                            self.uv_cords.append((v3[0], v3[1]))
                            uvIdx += 1
                            if (i % 2) == 0:
                                self.tris.append((v1[2], v2[2], v3[2]))
                                self.tris_uv.append((uvIdx - 3, uvIdx - 2, uvIdx - 1))
                            else:
                                self.tris.append((v3[2], v2[2], v1[2]))
                                self.tris_uv.append((uvIdx - 1, uvIdx - 2, uvIdx - 3))
                    # read fan
                    elif data[0] <= -1:
                        numFanVerts = -data[0]
                        v1 = readGLVertex(inFile)
                        v3 = readGLVertex(inFile)
                        centreVert = uvIdx
                        self.uv_cords.append((v1[0], v1[1]))
                        self.uv_cords.append((v3[0], v3[1]))
                        uvIdx += 2
                        for i in range(1, (numFanVerts - 1), 1):
                            v2 = v3[:]  # new ref
                            v3 = readGLVertex(inFile)
                            uvIdx += 1
                            self.uv_cords.append((v3[0], v3[1]))
                            self.tris.append((v3[2], v2[2], v1[2]))
                            self.tris_uv.append((uvIdx - 1, uvIdx - 2, centreVert))
                    else:
                        break
                # Done
                printDone_fn(self.start_time, prefix)  # Reading GLCommands
                # ====================================================================

            # Frames
            self.start_time = printStart_fn()  # reset timmer
            prefix = "Reading Frames"
            printProgress_fn(0, self.numFrames, prefix)  # print progress
            #inFile.seek(self.ofsFrames, 0)
            for fr in range(self.numFrames):
                inFile.seek(self.ofsFrames + self.framesize*fr, 0)
                # read frame headder
                buff = inFile.read(struct.calcsize("<6f16s"))
                data = struct.unpack("<6f16s", buff)
                minXYZ = (data[0], data[1], data[2])  # scale
                maxXYZ = (data[3], data[4], data[5])  # model XYZ location
                self.fr_scale.append(float(data[0]))
                self.fr_scale.append(float(data[1]))
                self.fr_scale.append(float(data[2]))
                verts = []
                norms = []
                for j in range(self.numVerts):
                    buff = inFile.read(struct.calcsize("<4B"))
                    vert = struct.unpack("<4B", buff)
                    verts.append([vert[0], vert[1], vert[2]])
                    norms.append((MD2_VN[vert[3]][0], MD2_VN[vert[3]][1], MD2_VN[vert[3]][2]))
                    self.fr_v_idx.append(int(vert[0]))
                    self.fr_v_idx.append(int(vert[1]))
                    self.fr_v_idx.append(int(vert[2]))
                # custom data
                # add 2nd byte precision in mdx5
                if self.isHDmodel == True:  # self.version == MDX5_VERSION:
                    for j, v in enumerate(verts):
                        buff = inFile.read(struct.calcsize("<3b"))
                        vert = struct.unpack("<3b", buff)
                        for k, xyz in enumerate(v):
                            dWord = ((xyz << 8) + vert[k])
                            dWord /= 256
                            verts[j][k] = minXYZ[k] * dWord + maxXYZ[k]
                else:
                    for j, v in enumerate(verts):
                        for k, xyz in enumerate(v):
                            verts[j][k] = minXYZ[k] * xyz + maxXYZ[k]
                self.v_pos.append(verts)  # append all vertex pos for frame
                self.v_norms.append(norms)  # vertexnormal index
                tmp_str = data[6].split(b'\x00')  # tmp_str[0].decode('utf-8')
                self.frame_names.append(tmp_str[0])  # frame names
            printDone_fn(self.start_time, prefix)  # Reading Frames Done
        finally:
            inFile.close()


        # print total time
        printDone_fn(startTime, "Reading File")


def load_kingpin_image(mdxPath, filePath, check_dupe, store_image):
    ''' load image file
        pcx loader added to view textures in 2.8+
    '''
    fileName = os.path.basename(mdxPath)
    f_ext = os.path.splitext(fileName)[1]

    # try internal mdx path first
    dir_name = os.path.dirname(mdxPath)
    if f_ext == '.pcx': # 2.8?
        image = read_pcx_file(fileName, dirname=dir_name,
                              check_existing=check_dupe, md2_name=mdxPath,
                              store_image=store_image)
    else:
        image = load_image(fileName, dirname=dir_name, recursive=False,
                           check_existing=check_dupe, force_reload=True)
    if image is not None:
        return image

    # try .mdx file path
    dir_name = os.path.dirname(filePath)
    if f_ext == '.pcx':
        image = read_pcx_file(fileName, dirname=dir_name,
                              check_existing=check_dupe,
                              md2_name=mdxPath,
                              store_image=store_image)
    else:
        image = load_image(fileName, dirname=dir_name, recursive=False,
                           check_existing=check_dupe, force_reload=True)
    if image is not None:
        return image

    strFolder = ["models", "players", "textures"]  # TODO main/baseq2?
    for dir in strFolder:
        idxPath = filePath.find(dir + os.sep)
        if idxPath >= 1:
            filePath = filePath[0:idxPath]
            break

    fullpath = bpy.path.native_pathsep(filePath + mdxPath)
    dir_name = os.path.dirname(fullpath)
    if f_ext == '.pcx':
        image = read_pcx_file(fileName, dirname=dir_name,
                              check_existing=check_dupe,
                              md2_name=mdxPath,
                              store_image=store_image)
    else:
        image = load_image(fileName, dirname=dir_name, recursive=False,
                           check_existing=check_dupe, force_reload=True)
    # return image
    return image


def asciiz(s):
    '''search hex null'''
    for i, c in enumerate(s):
        if ord(c) == 0:
            return s[:i]
    return s


# def Import_MD2_fn(self, filename):
def load_kp_model(self, context, filepath):

    ui_import_ = context.window_manager.kp_import_
    ext = os.path.splitext(os.path.basename(filepath))[1]
    if not ext == '.md2' and not ext == '.mdx':
        raise RuntimeError("ERROR: Incorrect file extension. Only md2 or mdx")

    md2 = Kingpin_Model_Reader()
    md2.object = None
    md2.ui_opt_anim = ui_import_.ui_opt_anim
    md2.ui_opt_anim_type = ui_import_.ui_opt_anim_type
    md2.ui_opt_frame_names = ui_import_.ui_opt_frame_names
    md2.ui_dupe_mat = ui_import_.ui_dupe_mat
    md2.ui_skip_cleanup = ui_import_.ui_skip_cleanup
    # md2.ui_opt_sk_types = ui_import_.ui_opt_sk_types
    md2.ui_opt_store_pcx = ui_import_.ui_opt_store_pcx
    md2.self = self

    if ext == '.mdx':
        md2.isMdx = True
        md2.ident = 0
        md2.version = 0
    else:
        md2.isMdx = False
        md2.ident = 0
        md2.version = 0

    md2.valid = 1  # disable "done"
    md2.read_file(filepath)
    md2.makeObject()

    return md2.valid
