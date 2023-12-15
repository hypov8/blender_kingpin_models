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
This script is an importer and exporter for Quake2/Kingpin Models .md2 and .mdx.
Including extra tools for vertex animated models

The frames are named <frameName><N> with :<br>
- <N> the frame number<br>
- <frameName> the name choosen at the last marker
                (or 'frame' if the last marker has no name or if there is no last marker)

Skins can be set using image textures or materials.
    if it is longer than 63 characters it is truncated.

Thanks to:
-   DarkRain
-   Bob Holcomb. For MD2_NORMALS taken from his exporter.
-   David Henry. For the documentation about the MD2 file format.
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
- fix texture bug
- added importing of GL commands. For enhanced uv precision
- added skin search path for texture not im model folder
- added multi part player model bbox fix. All parts must be visible in scene
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
- added animation toolbar, based on animall plugin.
    for editing shape keys and vertex animation
- importing of multiple selected models added
- added new shape key import method.(absolute mode)

v1.2.4
- added quake3 to kingpin player model converter
- added kingpin tool to toolbar: Build grid. used to align vertex,
    for better exported model compression
- import image will no longer duplicate existing images
- added a mesh driver function. so animated meshes can be split into sections

v1.2.5
- added high deff models. 2byte vertex, double vert/poly counts
- updated animation tool to support collections at source
- split up faces into 256 groups when building glcommands. speed boost but...

v1.2.6
- added 2 byte precision import/export (HD, no wobble)
- added pcx support. pcx will be saved to .blend file
- added mesh smooth tool. to try fix md2 compresion wobble. for HD export
- fixed mesh grid to use proper context. compatable with older blender
- removed unused libary and clean up
- retarget animation now supports selecting collections as source
- added custom vertex normal export option (use for players with seams)
- addon preference. export file name as mesh name. with md2/mdx choice
- added import/export butting to tool menu



notes
=====
- setup textures (2.80)
    in Material click the 'New' button
    make sure 'use nodes' button is enabled
    Click the circle next to 'base color' and pick 'image texture'
    click 'Open' to browse for texture file
- using driver
    if you have a complete mesh with animated data, you can't delets faces/vertex.
        so use this to re-animate
    first set scene frame. preferable frame 0
    Duplicate mesh(the one that has the full animation)
    on the duplicated mesh, remove all animation data (use button Clear Anim)
    in edit mode, delete parts of the mesh you dont want.
    in kp tools, select 'target'(the original mesh you cloned)
    in kp tools, press 'Animate mesh'
    if model was aligned properly, the closest vertex from target
        will drive vertex in the selected object/s
    scrub through timeline to confirm animation. Remove any 'modifiers'
        that may effect animation
- Quake 3 .md3 conversion to Kingpin
    Using the 'Quake 3 Model (.md3)-hy-' Import script.
    Import lower.md3, upper.md3, head.md3 and shotgun.md3. (multi select)
    Option: Select the Leg Idle animations type(static/animated)
    Option: Change the leg rotation angles(for running sidways)
    Option: Change Crouch Death anim to use stand death anim 1/2/3.
    Option: Change Scale to match a kingpin player model size.
    Press the 'Animation.cfg' folder Button.
    Select the .cfg file matching the imported Q3 models.
    Hide any non Q3 scene objects.
    Press the 'Convert to Kingpin' Button.
    You can now export the head/body/legs models to Kingpin.
    Note:
    Animation.cfg may need tweaking to get the animations correct.
    Death animations order is used based on Q3 duration, to suit KP.
- smooth mesh
    This only works for newly imported models using vertex animations
    This attempts to smooth vertex wobble by smoothing small changes
    -
    set the frame range(eg 0-31 thug idle).
    choose loop option
    click smooth vertex button
- custom vertex normals.
    This feature makes mesh seams have identical vertex normals so
    seams will be smoothed like its 1 joined mesh
    -
    duplicate mesh, clear animation and merge all parts/seams/vertex
    retarget animation to this new mesh. (use colection mode)
    add the 'Data Transfer' Modifyer to the mesh to be exported
    set source object to the joined/smoothed mesh
    set use face corner data with custom normals(object needs auto smooth enabled)
    use vertex groups if needed, to keep original vertex data
    when exporting mesh, select custom vertex normals


todo:
- import. split model into mdx groups
- interpolation selector. for animated mesh import
- import key reduction
- extend hitbox with all scene objects(player seam)
- optimize gl commands more. run fan first on verts with 6+ edges
- md3 importer
-- export sets file name to mesh name (incomplete)
- q3toKP add jump variations
- fix shape key to not use index0 (absolute)
smooth vertex. using shape keys
'''


bl_info = {
    "name": "Kingpin Models (md2, mdx)",
    "description": "Import/export Kingpin compatible model (md2/mdx)",
    "author": "Update by HypoV8. See _init_.py for contributors",
    "version": (1, 2, 6),
    "blender": (2, 80, 0),
    "location": "File > Import/Export > Kingpin Models",
    "warning": "",  # used for warning icon and text in addons panel
    "tracker_url": "https://github.com/hypov8/blender_kingpin_models",
    "wiki_url": "https://kingpin.info/",
    "doc_url": "https://kingpin.info/",
    "support": 'COMMUNITY',
    "category": "Import-Export"
}

import bpy
from bpy.types import WindowManager, AddonPreferences
from bpy.props import PointerProperty, BoolProperty
from . common_kp import (
    make_annotations,
    get_menu_import,
    get_menu_export
)
from . import  tools, anim, q3_to_kp
from . q3_to_kp import KINGPIN_Q3toKP_props
from . anim import KINGPIN_Anim_props
from . tools import KINGPIN_Tools_props
from . import_kp import (
    KINGPIN_Import_Dialog,
    KINGPIN_Import_props,
    KINGPIN_Import_Button
)
from . export_kp import (
    KINGPIN_Export_Dialog,
    KINGPIN_Export_props,
    KINGPIN_Export_Button,
    KINGPIN_Export_Button_Folder,
    KINGPIN_Export_Button_File
    )

if bpy.app.version < (2, 80): bl_info["blender"] = (2, 79, 0)


class KP_Preferences(AddonPreferences):
    ''' Preferences for addon
    '''
    bl_idname = "kingpin"
    pref_kp_filename = BoolProperty(
        name="Use Mesh Name",
        description="Export file name as object name",
        default=False
    )
    pref_kp_file_ext = BoolProperty(
        name="Default .mdx",
        description="add mdx instead of md2 as default extension(when missing)",
        default=False
    )
    pref_kp_import_button_use_dialog = BoolProperty(
        name="Button Uses Import Window",
        description="Show only an export button in tool panel",
        default=True
    )
    pref_kp_export_button_use_dialog = BoolProperty(
        name="Button Uses Export Window",
        description="Show only an export button in tool panel",
        default=False
    )

    def draw(self, _):
        ''' draw '''
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text='Export Dialog options')
        row = box.row()
        row.prop(self, "pref_kp_filename")
        if self.pref_kp_filename:
            row.prop(self, "pref_kp_file_ext")
        #import options
        box = layout.box()
        row = box.row()
        row.label(text='Import Tool Panel')
        row = box.row()
        row.prop(self, "pref_kp_import_button_use_dialog")
        # export options
        box = layout.box()
        row = box.row()
        row.label(text='Export Tool Panel')
        row = box.row()
        row.prop(self, "pref_kp_export_button_use_dialog")


# blender UI menu.
# file > export
def menu_func_export(self, context):
    self.layout.operator(KINGPIN_Export_Dialog.bl_idname, text="Kingpin Models (md2, mdx)")


# file > import
def menu_func_import(self, context):
    self.layout.operator(KINGPIN_Import_Dialog.bl_idname, text="Kingpin Models (md2, mdx)")


classes = (
    KINGPIN_Import_Dialog,
    KINGPIN_Import_Button,
    KINGPIN_Export_Dialog,
    KINGPIN_Export_Button,
    KINGPIN_Export_Button_File,
    KINGPIN_Export_Button_Folder,
)

classes_props = (  # convert to py3
    KP_Preferences,
    KINGPIN_Import_props,
    KINGPIN_Export_props,
    KINGPIN_Tools_props,
    KINGPIN_Q3toKP_props,
    KINGPIN_Anim_props,
)


def register():
    for cls in classes_props:
        make_annotations(cls)
        bpy.utils.register_class(cls)

    WindowManager.kp_import_ = PointerProperty(type=KINGPIN_Import_props)
    WindowManager.kp_export_ = PointerProperty(type=KINGPIN_Export_props)
    WindowManager.kp_tool_ = PointerProperty(type=KINGPIN_Tools_props)
    WindowManager.kp_q3tokp_ = PointerProperty(type=KINGPIN_Q3toKP_props)
    WindowManager.kp_anim_ = PointerProperty(type=KINGPIN_Anim_props)

    for cls in classes:
        bpy.utils.register_class(cls)

    anim.register()
    tools.register()
    q3_to_kp.register()
    # menu
    get_menu_export().append(menu_func_export)
    get_menu_import().append(menu_func_import)


def unregister():
    get_menu_export().remove(menu_func_export)
    get_menu_import().remove(menu_func_import)
    for cls in classes:
        bpy.utils.unregister_class(cls)
    for cls in classes_props:
        bpy.utils.unregister_class(cls)

    del WindowManager.kp_import_
    del WindowManager.kp_export_

    del WindowManager.kp_tool_
    del WindowManager.kp_q3tokp_
    del WindowManager.kp_anim_

    q3_to_kp.unregister()
    anim.unregister()
    tools.unregister()


if __name__ == "__main__":
    register()
