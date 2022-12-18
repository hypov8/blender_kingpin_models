# Quake 2 and Kingpin .md2 .mdx import/export add-on for Blender

Tested to work in blender 2.79, 2.80, 2.92, 3.2.1

Skins can be set using image textures or materials. if it is longer than 63 characters it is truncated.

Import mesh animation as vertex or shapekey

Frame names can be read/set for timeline

## Using animation driver
-    if you have a complete mesh with animated data, you cant delets faces/vertex. so use this to re-animate
-    first set scene frame. preferabl frame 0
-    Duplicate mesh(the one that has the full animation)
-    on the duplicated mesh, remove all animation data (use button Clear Anim)
-    in edit mode, delete parts of the mesh you dont want.
-    in kp tools, select 'target'(the original mesh you cloned)
-    in kp tools, press 'Animate mesh'
-    if model was aligned properly, the closest vertex from target will drive vertex in the selected object/s
-    scrub through timeline to confirm animation. remove any 'modifiers' that may effect animation

## Quake 3 .md3 conversion to Kingpin
-    Using the 'Quake 3 Model (.md3)-hy-' Import script.
-    Import lower.md3, upper.md3, head.md3 and shotgun.md3.
-    Option: Select the Leg Idle animations type(static/animated)
-    Option: Change the leg rotation angles(for running sidways)
-    Option: Change Crouch Death anim to use stand death anim 1/2/3.
-    Option: Change Scale to match a kingpin player model size.
-    Press the 'Animation.cfg' folder Button.
-    Select the .cfg file matching the imported Q3 models.
-    Hide any non Q3 scene objects.
-    Press the 'Convert to Kingpin' Button.
-    You can now export the head/body/legs models to Kingpin.
-    Note:
-    Animation.cfg may need tweeking to get the animations correct.
-    Death animations order are used based on time, to suit KP.-


## Thanks to:
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

## hypov8 plugin update log
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
- added quake3 to kingpin player model converter
- added kingpin tool to toolbar: Build grid. used to align vertex, for better exported model compresion
- import image will no longer duplicate existing images
- added a mesh driver function. so animated meshes can be split into sections
