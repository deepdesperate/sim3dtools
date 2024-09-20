bl_info = {
    "name": "Simple 3D Tools",
    "author": "Naman Deep",
    "version": (1, 0),
    "blender": (4, 00, 0),
    "location": "Object > Sim3DTools",
    "description": "Set of 3D Tools for game artists",
    "category": "Learning",
}

"""
1. Add Material option for the group?

"""

from typing import Set
import bpy
import bmesh
import mathutils

from bpy.props import ( IntProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       PointerProperty,
                       EnumProperty )
from bpy.types import Context


class tagItem(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(
        type= bpy.types.Object
    )

def rem_mat(obj):
    if obj.data.materials:
        obj.data.materials.clear()

def add_mat(obj, mat_name, mat) :
    exist_mat = False

    if ( mat is None) :
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        
        else:
            mat = bpy.data.materials.new(mat_name)
            mat.use_nodes = True
    
    assign = True
    # Checking if the material already exists in the object mats
    if mat_name not in [m.name for m in obj.data.materials]:
        obj.data.materials.append(mat)
        print(f"Assigned material: {mat.name}")

    
    mat_index = obj.data.materials.find(mat.name)

    if mat_index != -1:
        for poly in obj.data.polygons:
            poly.material_index = mat_index
    
    return {"FINISHED"}



class markUVUnwrapped(bpy.types.Operator):
    """ Mark object as UV unwrapped"""
    bl_idname = "sim3dtools.mkuvunwrap"
    bl_label = "Mark UV Done Operator"
    bl_options = {"REGISTER","UNDO"}


    mat_name: bpy.props.StringProperty(name = "Material Name",default= "MarkUV")

    @classmethod
    def poll(cls, context):
        obj = context.object
        if len(bpy.context.selected_objects) < 1:
            return False
        if obj.type != 'MESH':
            return False
        return True

    def execute(self, context):
        
        mat_name = self.mat_name

        # Get Properties
        remove_old = context.scene.s3dtool_remMat
        mat = context.scene.s3dtool_mat

        if len(bpy.context.selected_objects) < 1:
            self.report({'ERROR'}, "Please select some objects")
            return {'CANCELLED'}
        if mat is not None:
            mat_name = mat.name
        all_objs = context.selected_objects
        for obj in all_objs:
            if remove_old:
                rem_mat(obj)
            if obj.type == 'MESH':
                add_mat(obj, mat_name, mat)
        
        return {'FINISHED'}

    
    def invoke(self, context, event):
        # Show Pop up only if the mat is not selected
        if (context.scene.s3dtool_mat == None):
            return context.window_manager.invoke_props_dialog(self) 
        
        else:
            # Material already selected
            return self.execute(context)


# ------------------- Color Palette ---------------------------



class ColorItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name = "Color Name", default= "New Color")
    color: bpy.props.FloatVectorProperty(name = "Color", size = 4, subtype= "COLOR", default= (1.0, 1.0, 1.0,1.0) , min = 0.0, max = 1.0)
    objects: bpy.props.CollectionProperty(type= tagItem)


class ColorPalleteGroup(bpy.types.PropertyGroup):
    presets: bpy.props.CollectionProperty(type = ColorItem)


class COLOR_PALETTE_OT_AddColor(bpy.types.Operator):
    bl_idname = "sim3dtools.cp_add_color"
    bl_label = "Add Color"
    bl_description = "Adds a new color to Color Palette"

    def execute(self, context: Context):
        color_item = context.scene.sim3d_color_palette.presets.add()
        color_item.name = "Color {}".format(len(context.scene.sim3d_color_palette.presets))
        return {'FINISHED'}



class COLOR_PALETTE_OT_RemoveColor(bpy.types.Operator):
    bl_idname = "sim3dtools.cp_rem_color"
    bl_label = "Remove Color"
    bl_description = "Removes a Color from the color pallete"

    index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.sim3d_color_palette.presets.remove(self.index)
        return {'FINISHED'}

def get_vertex_color(obj, name):
    if not obj or obj.type != 'MESH':
        return None

    if not obj.data.vertex_colors:
        v_col = obj.data.vertex_colors.new()
        v_col.name = name
        return v_col
    
    flag = False
    for col in obj.data.vertex_colors:
        if col.name == name:
            flag = True
            v_col = col
            obj.data.vertex_colors.active = v_col
            return obj.data.vertex_colors.active
    
    if not flag:
        v_col = obj.data.vertex_colors.new()
        v_col.name = name
        return v_col
    

def get_color_attribute(obj, name):
    if name not in obj.data.color_attributes:
        obj.data.color_attributes.new(name = name, type = 'FLOAT_COLOR', domain = 'CORNER')
    return obj.data.color_attributes[name]


def get_active_vertex_color(obj):
    if not obj or obj.type != 'MESH': return None

    return obj.data.color_attributes.active_color

def get_vertex_colors(obj):
    if not obj or obj.type != 'MESH': return None
    
    return obj.data.color_attributes

class COLOR_PALETTE_OT_SelectObjects(bpy.types.Operator):
    bl_idname = "sim3dtools.cp_sel_objects"
    bl_label = "Select Objects with VC"
    bl_description = "Select objects using this Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        palette = scene.sim3d_color_palette.presets
        color_item = palette[self.index]

        color = color_item.color
        objects = color_item.objects
        
        for ob in objects:
            obj = ob.object
            if obj.visible_get():
                obj.select_set(True)
            else:
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

        return {'FINISHED'}



class COLOR_PALETTE_OT_ApplyVertexColor(bpy.types.Operator):
    bl_idname = "sim3dtools.cp_add_vc"
    bl_label = "Apply Vertex Color"
    bl_description = "Apply vertex Color from the color palette"
    bl_options = {'REGISTER', 'UNDO'}

    color_index: bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        if not len(context.selected_objects) >= 1:
            return False
        return True
    
    def execute(self, context):
        scene = context.scene
        palette = scene.sim3d_color_palette.presets
        color_item = palette[self.color_index]
        color = color_item.color

        is_in_edit_mode = (context.object.mode == 'EDIT' ) 

        objects_count = 0

        activeGrpObjects = [obj.object for obj in color_item.objects]

        if is_in_edit_mode:
            all_objects = context.objects_in_mode

            for obj in all_objects:
                if obj.type != 'MESH':
                    continue
                
                if obj not in activeGrpObjects:
                    append_obj = color_item.objects.add()
                    append_obj.object = obj

                objects_count += 1

                mesh = obj.data
                bm = bmesh.from_edit_mesh(mesh)

                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                bm.faces.ensure_lookup_table()

                loop_indices = []
                for face in bm.faces:
                    if face.select:
                        for loop in face.loops:
                            loop_indices.append(loop.index)

                # Setting object mode seems to fix the indexing issue

                bpy.ops.object.mode_set(mode = 'OBJECT')
                
                vcol = get_color_attribute(obj, 'COLOR_ID')

                if len(loop_indices) > 0:
                    for i, loop_index in enumerate(loop_indices):
                        vcol.data[loop_index].color = color
                bpy.ops.object.mode_set(mode = 'EDIT')

        else:
            all_objects = [ obj for obj in bpy.context.selected_objects]

            for obj in all_objects:
                if obj.type != 'MESH':
                    continue
                    
                # Objects detail menu

                if obj not in activeGrpObjects:
                    append_obj = color_item.objects.add()
                    append_obj.object = obj
                objects_count += 1
                
                vcol = get_color_attribute(obj, 'COLOR_ID')

                for poly in obj.data.polygons:
                    for loop_index in poly.loop_indices:
                        vcol.data[loop_index].color = color
                
        self.report({'INFO'}, f"Added Vertex Color to {str(objects_count)} objects")
        return {'FINISHED'}



                        
# -------------- Storing Faces --------------------




class FaceIndex(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(name = "Face_Index")

class StoreFaceData(bpy.types.PropertyGroup):
    object_ref: bpy.props.PointerProperty(type = bpy.types.Object)
    face_indices: bpy.props.CollectionProperty(type = FaceIndex)

class FacePresetGroup(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name = "Face Grp" , default= "Face Group")
    stored_faces: bpy.props.CollectionProperty( type = StoreFaceData)

def upd_facePreset_list(self, context):
    presets = context.scene.sim3d_faceGroups
    items = [ (str(i), preset.name, "") for i,preset in enumerate(presets)]
    if not items:
        items = [('0', 'No Groups', '')]
    return items



class FG_AddFaces(bpy.types.Operator):
    bl_idname = "sim3dtools.fg_addfaces"
    bl_label = "Add Selected Faces to the group"
    bl_description = "Add selected faces to the preset group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: Context):
        scene = context.scene
        preset = scene.sim3d_faceGroups[int(scene.sim3d_active_fg)]

        start_mode = context.object.mode
        bpy.ops.object.mode_set(mode = 'OBJECT')

        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode = 'EDIT')
                bpy.ops.mesh.select_mode(type= 'FACE')
                bpy.ops.object.mode_set(mode = 'OBJECT')

                # Store selected Faces
                selected_faces = {f.index for f in obj.data.polygons if f.select}

                exist_faceGroup = next((fd for fd in preset.stored_faces if fd.object_ref == obj), None)

                if exist_faceGroup:
                    stored_indices = { f.index for f in exist_faceGroup.face_indices}
                    new_faces = selected_faces - stored_indices

                    for face_idx in new_faces:
                        new_face = exist_faceGroup.face_indices.add()
                        new_face.index = face_idx
                else:
                    face_data = preset.stored_faces.add()
                    face_data.object_ref = obj

                    for face_idx in selected_faces:
                        new_face = face_data.face_indices.add()
                        new_face.index = face_idx

        bpy.ops.object.mode_set(mode = start_mode)
        self.report( {'INFO'}, "Selected Faces stored and appended")

        return {'FINISHED'}
    
class FG_Remove_SelectedFaces(bpy.types.Operator):
    bl_idname = "sim3dtools.fg_rem_faces"
    bl_label = "Remove Selected Faces"
    bl_description = "Remove selected faces from the active group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: Context):
        scene = context.scene
        preset = scene.sim3d_faceGroups[int(scene.sim3d_active_fg)]
        active_obj = context.active_object

        start_mode = active_obj.mode
        bpy.ops.object.mode_set(mode = 'OBJECT')

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            for face_data in preset.stored_faces:
                if face_data.object_ref == obj:
                    selected_faces = {f.index for f in obj.data.polygons if f.select}
                    remaining_faces = {f.index for f in face_data.face_indices if f.index not in selected_faces}

                    face_data.face_indices.clear()

                    for idx in remaining_faces:
                        new_face = face_data.face_indices.add()
                        new_face.index = idx
        
        bpy.ops.object.mode_set(mode = start_mode)

        self.report({'INFO'}, "Selected Faces removed from preset.")

        return {'FINISHED'}
    


class FG_SelectFaces(bpy.types.Operator):
    bl_idname = "sim3dtools.fg_select_faces"
    bl_label = "Select Faces"
    bl_description = "Select Faces stored in active Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        preset = scene.sim3d_faceGroups[int(scene.sim3d_active_fg)]

        for face_data in preset.stored_faces:
            obj = face_data.object_ref
            if obj and obj.type == 'MESH':

                if obj.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode = 'OBJECT')

                    mesh = obj.data
                    mesh.update()

                    for poly in mesh.polygons:
                        poly.select = False
                    
                    face_indices = {f.index for f in face_data.face_indices}
                    for poly in mesh.polygons:
                        if poly.index in face_indices:
                            poly.select = True
                    
                    mesh.update()

                    if obj.mode != 'EDIT':
                        bpy.ops.object.mode_set(mode = 'EDIT')
                    
                    self.report({'INFO'}, "Faces selected from preset.")
        
        return {'FINISHED'}





class FG_AddPreset( bpy.types.Operator):
    bl_idname = "sim3dtools.fg_create_preset"
    bl_label = "New Face Group"
    bl_description = "Create New Face Group"

    def execute(self, context):
        scene = context.scene
        new_preset = scene.sim3d_faceGroups.add()
        new_preset.name = f"Group {len(scene.sim3d_faceGroups)}"

        scene.sim3d_active_fg = str(len(scene.sim3d_faceGroups) - 1)
        
        self.report({'INFO'}, "Add New Preset")
        return {'FINISHED'}

class FG_RemPreset(bpy.types.Operator):
    bl_idname = "sim3dtools.fg_remove_preset"
    bl_label = "Delete Face Group"
    bl_description = "Delete Face Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        presets = scene.sim3d_faceGroups

        if len(presets) > 0:
            preset_index = int(scene.sim3d_active_fg)
            presets.remove(preset_index)

            scene.sim3d_active_fg = str(max(0, len(presets) - 1 ))
            self.report({'INFO'}, "Preset removed")
        else:
            scene.sim3d_active_fg = '0'
        
        return {'FINISHED'}
    






class FriendsCollection(bpy.types.Operator):
    """Move selected objects to active object's collection """
    bl_idname = "sim3dtools.movetofriend"
    bl_label = "Move To Active"
    bl_description = "Move selected objects to active object's collection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        if not len(context.selected_objects) > 1:
            return False
        return True
    
    def execute(self, context):
        my_obj = bpy.context.active_object
        my_cols = []
        for col in my_obj.users_collection:
            my_cols.append(col)

        for obj in bpy.context.selected_objects:
            if not (obj == my_obj):
                old_cols = []
                for o in obj.users_collection:
                    old_cols.append(o)
                    
                for c in my_cols:
                    if c not in old_cols:
                        c.objects.link(obj)
                        print("MOVED {obj.name} to {c.name}")
                
                for old in old_cols:
                    if old not in my_cols:
                        old.objects.unlink(obj)

        return {'FINISHED'}
    



    
# def obj_menu_func(self, context):
#     self.layout.separator()
#     self.layout.operator(FriendsCollection.bl_idname, text = FriendsCollection.bl_label)


# --------------- Presets Algorithm Starting --------------------

# --------------- Update -------------------

def update_presets( self, context):
    items = [ (str(i), context.scene.my_tagGroups.presets[i].tag_Name, "") for i in range(len( context.scene.my_tagGroups.presets))]
    if not items:
        items = [('0', 'No Presets', '')]
    return items



class tagProperties( bpy.types.PropertyGroup):

    tag_Name: bpy.props.StringProperty(name = "Group Name")

    leader: bpy.props.PointerProperty(type= bpy.types.Object)

    objects: bpy.props.CollectionProperty(type = tagItem)

class tagGroups(bpy.types.PropertyGroup):
    presets: bpy.props.CollectionProperty(type= tagProperties)

class activeTagGroup(bpy.types.PropertyGroup):
    selected_preset: bpy.props.EnumProperty(name = "Select Group", items = update_presets )




"""
Preset Operators
    1. Create a Preset <>
    2. Delete a Preset


Preset Sub Operators
    1. Mark Leader Object
    2. Add selected Objects to group
    3. Select group Objects ( select leader / or not? )
    4. Remove selected objects from group
    5. Print(' Show groups objects in the info menu ' )
"""

# ---------------- Create Preset ------------------

def createTagPreset():
    tagGroups = bpy.context.scene.my_tagGroups
    new_preset = tagGroups.presets.add()
    new_preset.tag_Name = f"Preset {len(tagGroups.presets)}"

    if( bpy.context.active_object ):
        new_preset.leader = bpy.context.active_object
    
    if bpy.context.selected_objects:
        for obj in bpy.context.selected_objects:
            if obj == bpy.context.active_object:
                continue
            new_preset.objects.add().object = obj

    return new_preset


class createPresetOperator(bpy.types.Operator):
    bl_idname = "sim3dtools.create_tag_preset"
    bl_label = "Create Tag Group"
    bl_description = "Add a new tag Group"
    bl_options = {"REGISTER","UNDO"}


    def execute(self, context):
        tagGroups = context.scene.my_tagGroups

        activeGroup = createTagPreset()

        context.scene.active_tagGroup.selected_preset = str( len(tagGroups.presets) - 1)

        return {'FINISHED'}

        
        
            
# ------------- Delete a Preset -----------------
class deletePresetOperator(bpy.types.Operator):
    bl_idname = "sim3dtools.delete_tag_preset"
    bl_label = "Remove Tag Group"
    bl_description = "Remove the active tag Group"
    bl_options = {"REGISTER","UNDO"}


    def execute(self, context):
        tagGroups = context.scene.my_tagGroups
        groupIndex = int(context.scene.active_tagGroup.selected_preset)
        tagGroups.presets.remove(groupIndex)

        # Update the selected preset index
        if len( tagGroups.presets ) > 0:
            context.scene.active_tagGroup.selected_preset = str(min( groupIndex, len( tagGroups.presets) - 1))
        else:
            context.scene.active_tagGroup.selected_preset = '0'

        return {'FINISHED'}
    
# ---------------- Mark as Leader Object
    
        
#  ----------------- Add Secondary Objects

def removeObjFromGroup(collection, item):
    collection.remove( collection.find(item) ) 


class addGroupObjectsOperator(bpy.types.Operator):
    bl_idname = "sim3dtools.add_grp_object"
    bl_label = "Add Object to Group"
    bl_description = "Add the selected object(s) to the Group"
    bl_options = {"REGISTER","UNDO"}


    def execute(self, context):
        tagGroups = context.scene.my_tagGroups
        groupIndex = int(context.scene.active_tagGroup.selected_preset)
        activeGroup = tagGroups.presets[groupIndex]

        flag = False

        all_objects = [obj for obj in bpy.context.selected_objects]
        activeGrpObjects = [obj.object for obj in activeGroup.objects]

        final_objects = [obj for obj in all_objects if obj not in activeGrpObjects ]

        if len(final_objects) < len(all_objects) :
            flag = True
 
        # Check if the Preset is empty or not
        if len( tagGroups.presets ) == 0:
            activeGroup = createTagPreset
            # Create a new Preset if not present
        else:
            for obj in final_objects:
                if obj == bpy.context.active_object: 
                    if activeGroup.leader == None:
                        activeGroup.leader = obj
                        continue
                # activeGroup.objects.add().object = obj
                append_obj = activeGroup.objects.add()
                append_obj.object = obj

        if flag:
            self.report({'INFO'}, "Some objects were already in group")
        
        return {'FINISHED'}

# ---------------- Add to a new Group
 
class addObjectToNewGroup(bpy.types.Operator):
    bl_idname = "sim3dtools.add_new_preset_with_object" 
    bl_label = "Add New Group with the selected objects"
    bl_description = "Add selected objects to new group regardless of group selected"
    bl_options = {"REGISTER","UNDO"}


    def execute(self, context):
        tagGroups = context.scene.my_tagGroups

        # Adds selected object and active object to the objects col
        activeGroup = createTagPreset()
        context.scene.active_tagGroup.selected_preset = str( len(tagGroups.presets) - 1)

        return {'FINISHED'}



class remFromGrpOperator(bpy.types.Operator):
    bl_idname = "sim3dtools.rem_from_active"
    bl_label = "Remove from active group"
    bl_description = "Remove the obj from grp from it's current group"
    bl_options = {"REGISTER","UNDO"}


    def execute(self, context):
        tagGroups = context.scene.my_tagGroups

        grpIndex = int(context.scene.active_tagGroup.selected_preset)
        activeGroup = tagGroups.presets[grpIndex]

        objs_to_remove = [obj for obj in bpy.context.selected_objects]

        items_to_remove = [item for item in activeGroup.objects if item.object in objs_to_remove ]

        for item in items_to_remove:
            activeGroup.objects.remove(item)

        return {'FINISHED'}
    
class unGrpObjOperator(bpy.types.Operator):
    bl_idname = "sim3dtools.untag_object"
    bl_label = "Remove object from all group"
    bl_description = "Remove the tag from the object from all group it belongs to"
    bl_options = {"REGISTER","UNDO"}


    def execute(self, context):
        tagGroups = context.scene.my_tagGroups

        for obj in bpy.context.selected_objects:
            for grp in tagGroups:
                if obj in grp.objects:
                    grp.objects.remove(  grp.objects.find(obj))

        return {'FINISHED'}
    

class selectGrpObjOperator(bpy.types.Operator):
    bl_idname = "sim3dtools.sel_grp_obj"
    bl_label = "Select Group Objects"
    bl_description = "Select the group objects and make the leader as active object"
    bl_options = {"REGISTER","UNDO"}


    def execute(self, context):
        tagGroups = context.scene.my_tagGroups
        grpIndex = int(context.scene.active_tagGroup.selected_preset)

        # Deselect original objects
        activeGroup = tagGroups.presets[grpIndex]

        for item in activeGroup.objects:
            if item.object.type == 'MESH':
                item.object.select_set(True)

        leader = activeGroup.leader

        if leader != None:
            leader.select_set(True)
            bpy.context.view_layer.objects.active = leader
        
        return {'FINISHED'}


# ----------------- Presets Algorithm Ending ------------------



# ------------------- Panels ----------------------

# ------------ Simple3DTools ---------------------

class simple3DToolPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sim3DTools"
    bl_idname = "sim3dtools.mpanel"
    bl_label = "Simple 3D Tools"

    def draw(self, context):
        column = self.layout.column()

        b1 = column.box()
        b1.label( text = "3D Tools")
        r1 = b1.row()
        r2 = b1.row()
        r1.prop(context.scene,"s3dtool_remMat", text = "Remove Old Mats" , icon = "BLANK1")
        r1.prop(context.scene, "s3dtool_mat", text = "Material")
        r2.operator( "sim3dtools.mkuvunwrap" , text = "Mark UVed")

        #---- Tag Group -------

        b2 = column.box()
        b2.label( text = "Tag Group")
        row = b2.row()


        tagGroups = bpy.context.scene.my_tagGroups

        row.prop(context.scene.active_tagGroup , "selected_preset")

        row1 = b2.row()
        row1_1 = b2.row()
        row1_2 = b2.row()
        row1_3 = b2.row()
        row1_4 = b2.row()
        row1_5 = b2.row()

        row1.operator("sim3dtools.create_tag_preset", text = "New Group")
        row1.operator("sim3dtools.delete_tag_preset", text = "Delete Group")

        row1_1.operator("sim3dtools.add_grp_object", text = "Append")
        row1_1.operator("sim3dtools.rem_from_active", text = "Remove")

        row1_2.operator("sim3dtools.sel_grp_obj", text = "Select Objects")


        if len(tagGroups.presets) > 0:
            preset_index = int(bpy.context.scene.active_tagGroup.selected_preset)
            group = tagGroups.presets[preset_index]

            row1_3.prop(group, "tag_Name")
            row1_4.prop(group,"leader")

            cnt_String = f"Objects: {len(group.objects)}"
            row1_5.label(text = cnt_String)


        # ------- Face Groups --------------
        presets = context.scene.sim3d_faceGroups
        
        b3 = column.box()
        b3.label(text = "Face Groups")
        row = b3.row()

        row.prop(context.scene, "sim3d_active_fg")
        if len(presets) > 0:
            row11 = b3.row()
            preset_index = int(context.scene.sim3d_active_fg)
            group = presets[preset_index]

            row11.prop(group, "name")

        row1 = b3.row()
        row1_1 = b3.row()
        row1_2 = b3.row()
        row1_3 = b3.row()

        row1.operator("sim3dtools.fg_create_preset", text = "New Group")
        row1.operator("sim3dtools.fg_remove_preset", text = "Delete Group")

        row1_1.operator("sim3dtools.fg_addfaces", text = "Add Faces")
        row1_1.operator("sim3dtools.fg_rem_faces", text = "Remove Faces")
        
        row1_2.operator("sim3dtools.fg_select_faces", text = "Select Faces")


        

        # ------- Color Palette -------------

        palette = context.scene.sim3d_color_palette.presets
        show_hex = context.scene.sim3d_cp_show_hex

        b4 = column.box()
        row = b4.row()
        row1 = b4.row()
        row2 = b4.row()

        row.label(text = "Color Palette & Vertex Colors")

        row1.operator("sim3dtools.cp_add_color", text = "Add Color", icon = 'PLUS')
        row2.prop(context.scene,"sim3d_cp_show_hex", text = "Extra Details" )

        for i, color in enumerate(palette):
            row = b4.row(align= True)
            row.prop(color, "name", text = "")
            row.prop(color, "color", text = "")
            row.operator('sim3dtools.cp_add_vc', text = "Apply", icon = 'BRUSH_DATA').color_index = i
            row.operator('sim3dtools.cp_rem_color', text= "", icon='X').index = i

            if show_hex:
                hex_color = "#{:02X}{:02X}{:02X}".format(
                    int(color.color[0] * 255),
                    int(color.color[1] * 255),
                    int(color.color[2] * 255)
                )

                row = b4.row()
                row.operator('sim3dtools.cp_sel_objects', text = "Select Objects").index = i
                row.label(text = f"Hex: {hex_color},  Objects: {str(len(color.objects))} ")




classes = [
    FriendsCollection,
    markUVUnwrapped,
    simple3DToolPanel,

    # Grouping operators

    tagItem,
    tagProperties,
    tagGroups,
    activeTagGroup,
    createPresetOperator,
    deletePresetOperator,
    addGroupObjectsOperator,
    addObjectToNewGroup,
    remFromGrpOperator,
    unGrpObjOperator,
    selectGrpObjOperator,

    # Color Palette
    ColorItem,
    ColorPalleteGroup,
    COLOR_PALETTE_OT_AddColor,
    COLOR_PALETTE_OT_RemoveColor,
    COLOR_PALETTE_OT_ApplyVertexColor,
    COLOR_PALETTE_OT_SelectObjects,

    # Face Groups
    FaceIndex,
    StoreFaceData,
    FacePresetGroup,
    FG_AddFaces,
    FG_Remove_SelectedFaces,
    FG_SelectFaces,
    FG_AddPreset,
    FG_RemPreset



]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tagGroups = bpy.props.PointerProperty( type= tagGroups)
    bpy.types.Scene.active_tagGroup = bpy.props.PointerProperty(type = activeTagGroup)


    bpy.types.Scene.s3dtool_remMat = BoolProperty(
        name = "Remove Materials",
        description= "Remove old materials of the object",
        default= False
    )

    bpy.types.Scene.s3dtool_mat = PointerProperty( type = bpy.types.Material)

    # --------------Color Pallete-----------------

    bpy.types.Scene.sim3d_color_palette = bpy.props.PointerProperty(type = ColorPalleteGroup)
    bpy.types.Scene.sim3d_cp_show_hex = bpy.props.BoolProperty(name = "Show Hex Codes", default= False)

    # --------------Face Groups ------------------
    bpy.types.Scene.sim3d_faceGroups = bpy.props.CollectionProperty(type= FacePresetGroup)
    bpy.types.Scene.sim3d_active_fg = bpy.props.EnumProperty( items = upd_facePreset_list, name= "Active Preset")
    

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.s3dtool_mat
    del bpy.types.Scene.s3dtool_remMat

    del bpy.types.Scene.active_tagGroup
    del bpy.types.Scene.my_tagGroups

    del bpy.types.Scene.s3dtool_remMat

    del bpy.types.Scene.sim3d_color_palette
    del bpy.types.Scene.sim3d_cp_show_hex

if __name__ == "__main__":
    register()
    
    