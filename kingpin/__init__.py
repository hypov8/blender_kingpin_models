# ***** BEGIN GPL LICENSE BLOCK *****

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

# ***** END GPL LICENCE BLOCK *****

'''
This script is an importer and exporter for Kingpin Models .md2 and .mdx.

The frames are named <frameName><N> with :<br>
- <N> the frame number<br>
- <frameName> the name choosen at the last marker
                (or 'frame' if the last marker has no name or if there is no last marker)

Skins can be set using image textures or materials. if it is longer than 63 characters it is truncated.

Thanks to:
-   DarkRain
-   Bob Holcomb. for MD2_NORMALS taken from his exporter.
-   David Henry. for the documentation about the MD2 file format.
-   Bob Holcomb
-   Sebastian Lieberknecht
-   Dao Nguyen
-   Bernd Meyer
-   Damien Thebault
-   Erwan Mathieu
-   Takehiko Nawata
-   Daniel Salazar. AnimAll
-   Patrick W. Crawford. theduckcow.com 2.7/2.8 support


hypov8 plugin update log
========================
v1.1.1 (blender 2.79)
- fix teture bug
- added importing of GL commands. for enhanced uv pricision
- added skin search path for texcture not im nodel folder
- added multi part player model bbox fix. all parts must be visable in sceen
- fixed texture issue in glCommands. not checking for uv match, just vertex id

v1.2.0 (blender 2.80) jan 2020
- updated to work with new blender
- merged md2/mdx into 1 script
- loading/saving allows selection of both file types
- option for imported models to set timeline range if animated
- multi model selection support for exports
- hitbox will be created for each selected object

v1.2.1 (blender 2.80) nov 2020
- fixed a texture missing bug
- fixed texture string formatting
- export no longer fails if a skin was not found
- fixed skin string issue being null
- added matrix for non shape key exports

v1.2.2 (blender 2.79+2.80) sep 2022
- import using 1 shape key (using animall plugin method to set keys)
- option to switch keyframe import modes ()
- merge blender 2.7 into 1 script
- 2.79. import textures using nodes
- using blenders .obj addon as a base for mesh data

v1.2.3 (blender 2.79+2.80) oct 2022
- added animation toolbar, based on animall plugin. for editing shape keys and vertex animation
- importing of multiple selected models added
- added new shape key import method.(absolute mode)

v1.2.4
- added quake3 to kingpin player model cconverter
- added kingpin tool to toolbar: Build grid. used to align vertex, for better exported model compresion
- import image will no longer duplicate existing images
- added a mesh driver function. so animated meshes can be split into sections


notes
=====
- setup textures (2.80)
    in Material click the 'New' button
    make sure 'use nodes' button is enabled
    Click the circle next to 'base color' and pick 'image texture'
    click 'Open' to browse for texture file
- using driver
    if you have a cmplete mesh with animated data, you cant delets faces/vertex. so use this to re-animate
    first set scene frame. preferabl frame 0
    Duplicate mesh(the one that has the full animation)
    on the duplicated mesh, remove all animation data (use button Clear Anim)
    in edit mode, delete parts of the mesh you dont want.
    in kp tools, select 'target'(the original mesh you cloned)
    in kp tools, press 'Animate mesh'
    if model was aligned properly, the closest vertex from target will drive vertex in the selected object/s
    scrub through timeline to confirm animation. remove any 'modifiers' that may effect animation

todo:
- import. split model into mdx groups
- interpolation selector. for animated mesh import
- import key reduction
- pcx support
'''


bl_info = {
    "name": "Kingpin Models (md2, mdx)",
    "description": "Import/export Kingpin compatible model (md2/mdx)",
    "author": "Update by HypoV8. See _init_.py for contributors",
    "version": (1, 2, 4),
    "blender": (2, 80, 0),
    "location": "File > Import/Export > Kingpin Models",
    "warning": "",  # used for warning icon and text in addons panel
    "tracker_url": "https://github.com/hypov8/blender_kingpin_models",
    "wiki_url": "https://kingpin.info/",
    "doc_url": "https://kingpin.info/",
    "support": 'COMMUNITY',
    "category": "Import-Export"
}


if "bpy" in locals():
    import importlib
    importlib.reload(import_kp)
    importlib.reload(export_kp)
    importlib.reload(animall_toolbar)
    importlib.reload(common_kp)
    importlib.reload(q3_to_kp)
    importlib.reload(tools)
else:
    from . import (
        import_kp,
        export_kp,
        animall_toolbar,
        common_kp,
        q3_to_kp,
        tools
    )

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    StringProperty,
    IntProperty,
    CollectionProperty,
    PointerProperty,
)
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper, ImportHelper  # , unpack_list, unpack_face_list

from .common_kp import (
    MD2_MAX_FRAMES,
    get_preferences,
    make_annotations,
    get_menu_import,
    get_menu_export,
    set_select_state,
    get_layers,
)

'''from .q3_to_kp import (
    KINGPIN_Q3_to_KP_Properties,  # toolbar
    KINGPIN_MD3_to_KP,
)'''

'''from .animall_toolbar import (
    AnimallProperties_KP,  # toolbar
    VIEW3D_PT_animall_KP,
    ANIM_OT_insert_keyframe_animall_KP,
    ANIM_OT_insert_keyframe_animall_all_KP,
    ANIM_OT_delete_keyframe_animall_KP,
    ANIM_OT_delete_keyframe_animall_all_KP,
    ANIM_OT_clear_animation_animall_KP,
    ANIM_OT_frame_prev_KP,
    ANIM_OT_frame_next_KP,
    ANIM_OT_frame_update_KP,
)'''


if bpy.app.version < (2, 80):
    bl_info["blender"] = (2, 79, 0)


class cls_KP_Import(bpy.types.Operator, ImportHelper):  # B2.8
    # class cls_KP_Import(bpy.types.Operator, ImportHelper): #B2.79
    '''Import Kingpin format file (md2/mdx)'''
    bl_idname = "import_kingpin.mdx"
    bl_label = "Import Kingpin model (md2/mdx)"
    filename_ext = ".mdx"

    fImportAnimation = EnumProperty(
        name="",
        description="Import all frames",
        items=[('NONE', "None", "No animations", 0),  # force no animation
               ('SK_VERTEX', "Vertex Keys", "Animate using vertex data", 1),
               ('SK_ABS', "Shape Key (absolute)", "Use action graph for animations", 2),
               # ('SK_SINGLE', "Shape Keys (Single)", "Animate using only 1 shape key", 3),
               ('SK_MULTI', "Shape Keys (Multi)",
                            "Add shape key's for every frame.\n" +
                            "Import speed is faster, but mesh is harder to edit.\n" +
                            "Note: this is the old plugin method.", 3)],
        default="SK_VERTEX",
    )
    fAddTimeline = BoolProperty(
        name="Import Frame Names",
        description="Import animation frame names to time line\n" +
        "WARNING: Removes all existing marker frame names",
        default=False,
    )
    filter_glob = StringProperty(
        default="*.md2;*.mdx",
        options={'HIDDEN'},
    )
    # TODO SK_ABS Interpolation
    # Linear, Cardinal, Catmull-Rom, B-Spline
    filter_SK_Inter = EnumProperty(
        name="key type",
        description="Import all frames",
        items=[
            ('NONE', "None", "", 0),
            ('KEY_LINEAR', "Linear", "", 1),
            ('KEY_CARDINAL', "Cardinal", "", 2),
            ('KEY_CATMULL_ROM', "Catmull-Rom", "", 3),
            ('KEY_BSPLINE', "BSpline", "", 4),
        ],
        default="NONE",
    )
    # Selected files
    files = CollectionProperty(
        type=bpy.types.PropertyGroup
    )
    ui_skip_cleanup = BoolProperty(
        name="Skip checks",
        description="Blender does some error checking on mesh before importing.\n"
                    "This may delete some faces/vertex. "
                    "Enabled: Stops any mesh validation checks.\n"
                    "  Use if you find mesh is missing valuable data. Make sure you fix model before exporting",
        default=True,
    )

    def execute(self, context):
        from . import import_kp
        import os

        ver = bl_info.get("version")
        print("===============================================\n" +
              "Kingpin Model Importer v%i.%i.%i" % (ver[0], ver[1], ver[2]))

        if not (bpy.context.mode == 'OBJECT'):
            bpy.ops.object.mode_set(mode='OBJECT')  # , toggle=False)
        # deselect any objects
        for ob in bpy.data.objects:
            set_select_state(context=ob, opt=False)

        keywords = self.as_keywords(ignore=(
            "filter_glob",
            "files",
        ))

        # TODO
        if bpy.data.is_saved and get_preferences(context).filepaths.use_relative_paths:
            keywords["relpath"] = os.path.dirname(bpy.data.filepath)  # TODO..

        # multiple 'selected' file loader
        valid = 1
        folder = (os.path.dirname(self.filepath))
        for f in self.files:
            fPath = (os.path.join(folder, f.name))
            keywords["filepath"] = fPath
            print("===============================================")
            ret = import_kp.load(self, **keywords)
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

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "ui_skip_cleanup")
        layout.label(text="Import Animation Type:")
        layout.prop(self, "fImportAnimation")
        # show 'frame name' option when importing animation
        if not (self.fImportAnimation == 'NONE'):
            # TODO add key reduction option
            # if not (self.fImportAnimation == 'NONE'):
            #    sub = layout.row()
            #    sub.prop(self, "filter_SK_Inter")
            sub = layout.row()
            sub.prop(self, "fAddTimeline")
            if self.fAddTimeline:
                layout.label(text="WARNING: Removes existing names")


class cls_KP_Export(bpy.types.Operator, ExportHelper):  # B2.8
    '''Export selection to Kingpin file format (md2/md2)'''
    bl_idname = "export_kingpin.mdx"
    bl_label = "Export Kingpin Model (md2, mdx)"
    filename_ext = ".md2"  # md2 used later

    # fTextureNameMethod: int

    filter_glob = StringProperty(
        default="*.md2;*.mdx",
        options={'HIDDEN'})
    fTextureNameMethod = EnumProperty(
        name="Skin",
        description="Skin naming method",
        items=(
            ('SKIN_MAT_NAME',
             "Material Name",
                "Use material name for skin.\n" +
                "Must include the file extension\n" +
                "eg.. models/props/test.tga\n" +
                "Image dimensions are sourced from nodes. 256 is use if no image exists"
             ),
            ('SKIN_TEX_NAME',
             "Image Name",
                "Use image name from Material nodes\n" +
                "Must include the file extension\n" +
                "\"material name\" will be used if no valid textures are found\n" +
                "Image dimensions are sourced from nodes. 256 is use if no image exists"
             ),
            ('SKIN_TEX_PATH',
             "Image Path",
                "Use image path name from Material nodes\n" +
                "Path must contain a folder models/ or players/ or textures/ \n" +
                "\"material name\" will be used if no valid textures are found\n" +
                "Image dimensions are sourced from nodes. 256 is use if no image exists"
             ),
        ),
        default='SKIN_MAT_NAME')
    fExportAnimation = BoolProperty(
        name="Export animation",
        description="Export all animation frames.\n" +
                    "Note: Start/End frame initially comes from timeline range.",
        default=False)
    fStartFrame = IntProperty(
        name="Start Frame",
        description="Animated model start frame",
        min=0,
        max=MD2_MAX_FRAMES - 1,
        default=0)
    fEndFrame = IntProperty(
        name="End Frame",
        description="Animated model end frame",
        min=0,
        max=MD2_MAX_FRAMES - 1,
        default=40)
    fSeparateHitbox = BoolProperty(
        name="Player HitBox",
        description="Use when exporting .mdx player models.\n" +
                    "If multiple objects are selected, a separate hitbox is created for each object.\n" +
                    "HitBox are used in multiplayer when \"dm_locational_damage 1\" is set on the server\n" +
                    "Default: disabled. This will create 1 large hitbox.",
        default=False)
    fIsPlayerModel = BoolProperty(
        name="Fix Seams (Player etc.)",  # fix seam
        default=False,
        description=(
            "Fix 'multi-part' models that share a common seam.\n"
            "This works by using all visable objects in the scene to generate a bbox (setup compresion grid)\n"
            "Then each vertex will land on the correct position when loaded by the engine\n"
            "This can reduce model rez/quality, so only use if needed\n"
            "Usage: Show head, body, legs. Select each object(eg. head), then export head.mdx\n"
        )
    )
    fUseSharedBoundingBox = BoolProperty(
        name="Use shared bounding box",
        description="Calculate a shared bounding box from all frames.\n" +
                    "Used to avoid wobble in static vertices but wastes resolution",
        default=False)
    fApply_modifiers = BoolProperty(  # TODO
        name="Apply Modifiers",
        description="Apply Modifiers or use the original base mesh",
        default=True)

    check_extension = False  # 2.8 allow typing md2/mdx

    def execute(self, context):
        print("__execute kp__")
        from .export_kp import Export_MD2_fn
        # print headder
        ver = bl_info.get("version")
        print("=======================\n" +
              "Kingpin Model Exporter.\n" +
              "Version: (%i.%i.%i)\n" % (ver[0], ver[1], ver[2]) +
              "=======================")

        # if not (bpy.context.mode == 'OBJECT'):
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')  # , toggle=False)

        # store selected/sceen objects
        self.objects = context.selected_objects
        self.objectsVis = context.visible_objects

        # deselect any objects
        for ob in bpy.data.objects:
            set_select_state(context=ob, opt=False)

        keywords = self.as_keywords(ignore=(
            'filter_glob',
            'check_existing',
            'fExportAnimation',
            'fIsPlayerModel',
            'fUseSharedBoundingBox',
            'fSeparateHitbox',
            'fTextureNameMethod',
            'fStartFrame',
            'fEndFrame',
            'fApply_modifiers',
        ))

        Export_MD2_fn(self, context, **keywords)

        # select inital objects
        for obj in self.objects:
            set_select_state(context=obj, opt=True)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "fTextureNameMethod")  # testure source (dropdown)
        layout.prop(self, "fExportAnimation")   # export animation
        sub = layout.column()
        sub.enabled = self.fExportAnimation
        sub.prop(self, "fStartFrame")           # frame start number
        sub.prop(self, "fEndFrame")             # frame end number
        layout.prop(self, "fSeparateHitbox")    # merge hitbox
        layout.prop(self, "fIsPlayerModel")     # playermodel
        if not self.fIsPlayerModel and self.fExportAnimation:
            sub2 = layout.column()
            sub2.prop(self, "fUseSharedBoundingBox")

    def invoke(self, context, event):
        print("__invoke kp__")
        if not context.selected_objects:
            self.report({'ERROR'}, "Please, select an object to export!")
            return {'CANCELLED'}

        self.fStartFrame = context.scene.frame_start
        self.fEndFrame = context.scene.frame_end

        wm = context.window_manager
        wm.fileselect_add(self)

        return {'RUNNING_MODAL'}


# blender UI
def menu_func_export(self, context):
    self.layout.operator(cls_KP_Export.bl_idname, text="Kingpin Models (md2, mdx)")


def menu_func_import(self, context):
    self.layout.operator(cls_KP_Import.bl_idname, text="Kingpin Models (md2, mdx)")


classes = [
    cls_KP_Import,
    cls_KP_Export,
]


def register():
    animall_toolbar.register()
    q3_to_kp.register()
    tools.register()
    for cls in classes:
        make_annotations(cls)  # v1.2.2
        bpy.utils.register_class(cls)

    get_menu_export().append(menu_func_export)  # v1.2.2
    get_menu_import().append(menu_func_import)  # v1.2.2


def unregister():
    # bpy.app.handlers.frame_change_post.remove(post_frame_change)
    get_menu_export().remove(menu_func_export)  # v1.2.2
    get_menu_import().remove(menu_func_import)  # v1.2.2
    for cls in classes:
        bpy.utils.unregister_class(cls)

    q3_to_kp.unregister()
    animall_toolbar.unregister()
    tools.unregister()


if __name__ == "__main__":
    register()
