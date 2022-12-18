'''
importer class/func

class KP_Util_Import

class Import_MD2(Operator, ImportHelper)
'''

import os
import bpy
import struct

from bpy.types import Operator  # B2.8
from bpy_extras.io_utils import ImportHelper, unpack_list
from bpy_extras.image_utils import load_image
from math import pi
from timeit import default_timer as timer
from mathutils import (
    Matrix,
    Vector,
)

# import random
# import shutil

from .common_kp import (
    MD2_VN,
    printProgress_fn,
    printDone_fn,
    get_collection,
    get_uv_data_new,
    get_objects,
    get_layers,
    set_uv_data_active,
    # set_uv_data,
    set_select_state,

)


class Kingpin_Model_Reader:
    ''' Kingpin Model Reader '''
    def makeObject(self):
        if bpy.app.version >= (2, 80):  # nodes
            from bpy_extras import node_shader_utils

        self.time = timer()  # reset timmer
        prefix = "Generating Mesh"
        printProgress_fn(self, 0, self.numFrames, prefix)  # print progress

        int_frame = bpy.context.scene.frame_current
        bpy.context.scene.frame_set(0)

        # ###################
        # 2.8 Create the mesh
        md2_mesh = bpy.data.meshes.new(self.name)
        md2_mesh.from_pydata(self.v_pos[0], [], self.tris)  # new 2.8 method
        printDone_fn(self, prefix)  # Finish mesh data

        # ##########
        # skins data
        image_array = []
        if self.numSkins > 0:
            self.time = timer()  # reset timmer
            prefix = ""
            suffix = "Generating Materials"
            # printProgress_fn(self, 0, prefix)  # print progress
            print("========")
            #      "Generate Materials:")
            print("skins: %i" % len(self.skins))  # print count

            for idx, skin in enumerate(self.skins):
                # print("skin_%i: %s" % (idx + 1, skin), end='')  # print name
                prefix = str("%s%s" % (prefix, skin))

                mat_id = bpy.data.materials.new(skin)  # new material
                md2_mesh.materials.append(mat_id)  # asign materal to mesh

                # get materal node/links
                mat_id.use_nodes = True
                mat_nodes = mat_id.node_tree.nodes
                mat_links = mat_id.node_tree.links
                # delete existing node
                while(mat_nodes):
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

                if bpy.app.version < (2, 80):  # output blender render v2.79
                    node_output = mat_nodes.new(type='ShaderNodeOutput')
                    mat_links.new(node_tex.outputs['Color'], node_output.inputs['Color'])
                    node_output.location = Vector((250, -120))

                # try to load tga/pcx image
                skinImg = loadImage(skin, self.filePath)  # KP_Util_Import
                if skinImg is None:
                    skinImg = bpy.data.images.new(skin, self.skinWidth, self.skinHeight)
                    prefix = str("%s  Missing\n" % prefix)  # print(" Missing")
                else:
                    prefix = str("%s  OK\n" % prefix)  # print(" OK")
                # TODO check duplicates?
                # skinImg. mapping = 'UV' #2.7
                skinImg.name = skin
                image_array.append(skinImg)

                # link image to diffuse color
                node_tex.image = skinImg

            # Materials Done
            print(prefix, end='')
            print("========")
            printDone_fn(self, suffix)

        # #######
        # uv data
        self.time = timer()  # reset timmer
        prefix = "Generating UV"
        printProgress_fn(self, 0, self.numFrames, prefix)  # print progress

        uv_type, uv_layer = get_uv_data_new(md2_mesh, uv_name="UVMap_0")  # v1.2.2
        image = None  # asign first image. TODO: cleanup
        for im in image_array:
            if (im is not None):
                image = im
                break
        if (uv_type == 1):  # B2.79 v1.2.2
            blen_uvs = md2_mesh.uv_layers[0]
            for i, pl in enumerate(md2_mesh.polygons):
                face = self.tris_uv[i]
                v1, v2, v3 = face
                blen_uvs.data[pl.loop_start + 0].uv = self.uv_cords[v1]
                blen_uvs.data[pl.loop_start + 1].uv = self.uv_cords[v2]
                blen_uvs.data[pl.loop_start + 2].uv = self.uv_cords[v3]
                pl.use_smooth = True  # smooth all faces
                md2_mesh.uv_textures[0].data[i].image = image  # set face texture
        elif (uv_type == 2):  # B2.8 v1.2.2
            for i, face in enumerate(md2_mesh.polygons):
                face.use_smooth = True
                uv_x = self.tris_uv[i]
                # dat = md2_mesh.uv_layers[0].data[i].image = imag
                for uvid, (vert_idx, loop_idx) in enumerate(zip(face.vertices, face.loop_indices)):
                    uv_layer.data[loop_idx].uv = (self.uv_cords[uv_x[uvid]][0], self.uv_cords[uv_x[uvid]][1])
        # Done.
        printDone_fn(self, prefix)  # Finish uv data

        # validate/update model
        md2_mesh.validate()
        md2_mesh.update()

        # create new object from mesh
        self.time = timer()  # reset timmer
        prefix = "Generating Object"
        printProgress_fn(self, 0, self.numFrames, prefix)  # print progress

        obj = bpy.data.objects.new(md2_mesh.name, md2_mesh)
        get_collection(bpy.context).link(obj)  # v1.2.2
        # select object
        set_select_state(context=obj, opt=True)  # 1.2.2
        # Print Done.
        printDone_fn(self, prefix)

        # ############
        # Animate mesh
        if (self.numFrames > 1) and not (self.fImportAnimation == 'NONE'):
            self.time = timer()  # reset timmer
            prefix = "Generating Frames"

            # setup shape keys
            sk_type = 0
            sk_blocks = None
            sk_data = []
            obj_dat = obj.data
            ob_verts = obj.data.vertices
            # fCurvID = [None] * len(ob_verts)

            if (self.fImportAnimation == 'SK_VERTEX'):
                sk_type = 1
            elif (self.fImportAnimation == 'SK_SINGLE'):
                sk_type = 2
            elif (self.fImportAnimation == 'SK_MULTI'):
                sk_type = 3
            elif (self.fImportAnimation == 'SK_ACTION'):
                sk_type = 4
            elif (self.fImportAnimation == 'SK_ABS'):
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

                    printProgress_fn(self, v.index, self.numVerts, prefix)  # print progress
            ##########################
            # animate single shape key
            elif sk_type == 2:
                sk_data.append(obj.shape_key_add(name="Base", from_mix=False))  # hy.new
                sk_data.append(obj.shape_key_add(name="SK_0", from_mix=False))  # hy.new
                obj.active_shape_key_index = 1
                sk_data[1].value = 1.0
                obj.use_shape_key_edit_mode = True
                sk_blocks = obj.data.shape_keys.key_blocks

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
                sk_blocks = obj.data.shape_keys.key_blocks

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
                    printProgress_fn(self, i, self.numFrames, prefix)  # print progress

            #############################
            # absolute shape keys
            elif sk_type == 5:
                # isSetInter = 0 if self.filter_SK_Inter == 'NONE' else 1
                for i in range(self.numFrames):
                    # create shape key
                    sk_data.append(obj.shape_key_add(name=("skFrame_%i" % i), from_mix=False))
                    sk_data[i].data.foreach_set("co", unpack_list(self.v_pos[i]))  # move vertex
                    # insert keyframe.
                    obj.data.shape_keys.eval_time = (i * 10)  # 2.7 is buggy when you press Re-Time Shape Keys (+ 10)
                    obj.data.shape_keys.keyframe_insert(data_path='eval_time', frame=i)
                    # if (isSetInter):
                    # obj.data.shape_keys.interpolation = self.filter_SK_Inter
                    # obj.data.shape_keys.keyframe_insert(data_path='interpolation', frame=i)
                    printProgress_fn(self, i, self.numFrames, prefix)  # print progress

                obj.data.shape_keys.use_relative = False
                obj.use_shape_key_edit_mode = True
                obj.active_shape_key_index = 1  # updates display
                # bpy.ops.object.shape_key_retime()  # fix values

            ####################
            # import frame names
            if self.fAddTimeline:  # reset frame names
                lastFName = ""
                mark = bpy.data.scenes[0].timeline_markers
                mark.clear()
                fNames = self.frame_names
                for i in range(self.numFrames):
                    tmp_str = fNames[i].rstrip(b'0123456789')  # remove numbers
                    if not (lastFName == tmp_str):
                        mark.new(tmp_str.decode('utf-8'), frame=i)
                        lastFName = tmp_str

            # set sceen timeline to match imported model
            bpy.context.scene.frame_start = 0
            bpy.context.scene.frame_end = self.numFrames - 1
            obj.data.update()
            # Frames Done
            printDone_fn(self, prefix)

        # set frame back to old position
        bpy.context.scene.frame_set(int_frame)

        get_objects(bpy.context).active = obj  # v1.2.2
        get_layers(bpy.context).update()  # v1.2.2
        print("Model imported.\n" +
              "===============================================")

    def read_file(self, filePath):
        ''' open .md2 file and read contents '''
        print("Reading %s" % filePath, end='')
        startTime = timer()  # reset timmer

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

        inFile = open(file=self.filePath, mode="rb")
        try:
            print('.', end='')
            if self.isMdx:
                buff = inFile.read(struct.calcsize("<23i"))
                data = struct.unpack("<23i", buff)
                if not (data[0] == self.ident) or not (data[1] == self.version):
                    raise NameError("Invalid MDX file")
                self.skinWidth = max(1, data[2])
                self.skinHeight = max(1, data[3])
                # framesize
                self.numSkins = data[5]
                self.numVerts = data[6]
                self.numTris = data[7]
                self.numGLCmds = data[8]
                if self.fImportAnimation:
                    self.numFrames = data[9]
                else:
                    self.numFrames = 1
                self.ofsSkins = data[13]
                self.ofsTris = data[14]
                self.ofsFrames = data[15]
                self.ofsGLCmds = data[16]
            else:
                buff = inFile.read(struct.calcsize("<17i"))
                data = struct.unpack("<17i", buff)
                if not (data[0] == self.ident) or not (data[1] == self.version):
                    raise NameError("Invalid MD2 file")
                self.skinWidth = max(1, data[2])
                self.skinHeight = max(1, data[3])
                # framesize
                self.numSkins = data[5]
                self.numVerts = data[6]
                self.numUV = data[7]
                self.numTris = data[8]
                self.numGLCmds = data[9]
                if self.fImportAnimation:
                    self.numFrames = data[10]
                else:
                    self.numFrames = 1
                self.ofsSkins = data[11]
                self.ofsUV = data[12]
                self.ofsTris = data[13]
                self.ofsFrames = data[14]
                self.ofsGLCmds = data[15]
            print('.', end='')

            # Skins
            if self.numSkins > 0:
                inFile.seek(self.ofsSkins, 0)
                for i in range(self.numSkins):
                    buff = inFile.read(struct.calcsize("<64s"))
                    data = struct.unpack("<64s", buff)
                    dataEx1 = data[0].decode("utf-8", "replace")
                    dataEx1 = dataEx1 + "\x00"  # append null.
                    self.skins.append(asciiz(dataEx1))
            print('.')  # Done. #3

            # UV (software 1byte texture cords)
            if self.isMdx is False and self.numGLCmds <= 1:
                #
                self.time = timer()  # reset timmer
                prefix = "Reading Software UV"
                printProgress_fn(self, 0, self.numFrames, prefix)  # print progress

                inFile.seek(self.ofsUV, 0)
                for i in range(self.numUV):
                    buff = inFile.read(struct.calcsize("<2h"))
                    data = struct.unpack("<2h", buff)
                    # self.uv_cords.append((data[0] / self.skinWidth, 1 - (data[1] / self.skinHeight)))
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
                printDone_fn(self, prefix)  # Reading SW Texture cords

            else:
                self.time = timer()  # reset timmer
                prefix = "Reading GLCommands"
                printProgress_fn(self, 0, self.numFrames, prefix)  # print progress

                # =====================================================================================
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
                    else:
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
                printDone_fn(self, prefix)  # Reading GLCommands
                # ===================================================================================

            # Frames
            self.time = timer()  # reset timmer
            prefix = "Reading Frames"
            printProgress_fn(self, 0, self.numFrames, prefix)  # print progress
            #
            inFile.seek(self.ofsFrames, 0)
            for i in range(self.numFrames):
                buff = inFile.read(struct.calcsize("<6f16s"))
                data = struct.unpack("<6f16s", buff)
                verts = []
                norms = []
                for j in range(self.numVerts):
                    buff = inFile.read(struct.calcsize("<4B"))
                    vert = struct.unpack("<4B", buff)
                    verts.append((data[0] * vert[0] + data[3],
                                  data[1] * vert[1] + data[4],
                                  data[2] * vert[2] + data[5]))
                    norms.append((MD2_VN[vert[3]][0],
                                  MD2_VN[vert[3]][1],
                                  MD2_VN[vert[3]][2]))
                self.v_pos.append(verts)  # todo append
                self.v_norms.append(norms)  # vertexnormal index
                tmp_str = data[6].split(b'\x00')
                # tmp_str[0].decode('utf-8')
                self.frame_names.append(tmp_str[0])  # frame names
            printDone_fn(self, prefix)  # Reading Frames Done
        finally:
            inFile.close()

        self.timer = startTime
        printDone_fn(self, "Reading File")


def loadImage(mdxPath, filePath):
    fileName = os.path.basename(mdxPath)

    image = load_image(fileName, dirname=os.path.dirname(mdxPath), recursive=False)
    if image is not None:
        return image
    image = load_image(fileName, dirname=os.path.dirname(filePath), recursive=False)
    if image is not None:
        return image

    # build game base/mod dir
    idxModels = filePath.find("models" + os.sep)
    idxPlayer = filePath.find("players" + os.sep)
    idxTextur = filePath.find("textures" + os.sep)

    if filePath[0] == os.sep:
        filePath = filePath[1:]

    if idxModels >= 1:
        filePath = filePath[0:idxModels]
    elif idxPlayer >= 1:
        filePath = filePath[0:idxPlayer]
    elif idxTextur >= 1:
        filePath = filePath[0:idxTextur]

    fullpath = filePath + mdxPath
    fullpath = bpy.path.native_pathsep(fullpath)
    image = load_image(fileName, dirname=os.path.dirname(
        fullpath), recursive=False)
    if image is not None:
        return image

    return None


def asciiz(s):
    for i, c in enumerate(s):
        if ord(c) == 0:
            return s[:i]


# def Import_MD2_fn(self, filename):
def load(self,
         filepath,
         *,
         fImportAnimation=False,
         fAddTimeline=False,
         filter_SK_Inter=False,
         relpath=None
         ):

    ext = os.path.splitext(os.path.basename(filepath))[1]
    if not (ext == '.md2') and not (ext == '.mdx'):
        raise RuntimeError("ERROR: Incorrect file extension. Only md2 or mdx")
        return False
    else:
        md2 = Kingpin_Model_Reader()
        md2.object = None
        md2.fImportAnimation = fImportAnimation
        md2.fAddTimeline = fAddTimeline
        md2.filter_SK_Inter = filter_SK_Inter
        if ext == '.mdx':
            md2.isMdx = True
            md2.ident = 1481655369
            md2.version = 4
        else:
            md2.isMdx = False
            md2.ident = 844121161
            md2.version = 8

        md2.read_file(filepath)
        md2.makeObject()

        return True
