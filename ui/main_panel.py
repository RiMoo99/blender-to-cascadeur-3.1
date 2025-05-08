import bpy
import os  
from bpy.types import Panel
from ..utils import timeline_utils
from ..operators.keyframe_operators import BTC_UL_KeyframeList

# Base class for all panels
class PanelBasics:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "B2C"  # Sidebar tab name

# Main panel: Blender to Cascadeur
class BTC_PT_BlenderToCascadeurPanel(PanelBasics, Panel):
    bl_idname = "BTC_PT_blender_to_cascadeur"
    bl_label = "Blender to Cascadeur"
    
    def draw_header(self, context):
        self.layout.label(text="", icon="EXPORT")
    
    def draw(self, context):
        layout = self.layout
        # Main panel is empty, sub-panels will be used

# Panel con - Character Selection
class BTC_PT_CharacterPanel(PanelBasics, Panel):
    bl_idname = "BTC_PT_character"
    bl_label = "Choose Character"
    bl_parent_id = "BTC_PT_blender_to_cascadeur"
    
    def draw(self, context):
        layout = self.layout
        
        # Simple armature info - just show the selected armature
        if context.scene.btc_armature:
            box = layout.box()
            row = box.row()
            row.label(text=f"Selected: {context.scene.btc_armature.name}")
        else:
            box = layout.box()
            row = box.row()
            row.label(text="No armature selected")
        
        # Pick Armature button
        row = layout.row()
        row.operator("btc.pick_armature", text="Pick Armature", icon="ARMATURE_DATA")
        
        # Add Auto-Rig Pro detection from v2.3
        if context.scene.btc_armature:
            is_auto_rig = timeline_utils.is_auto_rig_pro_armature(context.scene.btc_armature)
            if is_auto_rig:
                row = layout.row()
                row.label(text="Auto-Rig Pro: Detected", icon='CHECKMARK')

# Panel con - Keyframe Markers
class BTC_PT_KeyframeMarkersPanel(PanelBasics, Panel):
    bl_idname = "BTC_PT_keyframe_markers"
    bl_label = "Keyframe Markers"
    bl_parent_id = "BTC_PT_blender_to_cascadeur"
    
    @classmethod
    def poll(cls, context):
        return context.scene.btc_armature is not None
    
    def draw(self, context):
        layout = self.layout
        
        # Show current frame
        row = layout.row()
        row.label(text=f"Current Frame: {context.scene.frame_current}")
        
        # Mark/Clear current keyframe
        row = layout.row(align=True)
        row.operator("btc.mark_current_keyframe", text="Mark Current", icon="KEYFRAME")
        row.operator("btc.clear_current_keyframe", text="Clear Current", icon="KEYFRAME_HLT")
        
        # Mark/Clear all keyframes
        row = layout.row(align=True)
        row.operator("btc.mark_all_keyframes", text="Mark All", icon="KEYFRAME_HLT")
        row.operator("btc.clear_all_keyframes", text="Clear All", icon="X")
        
        # Add Toggle Timeline Markers button from v2.3
        row = layout.row()
        # Kiểm tra xem thuộc tính có tồn tại không
        has_markers = hasattr(context.scene, "btc_show_markers")
        show_markers = context.scene.btc_show_markers if has_markers else False
        icon = 'HIDE_OFF' if show_markers else 'HIDE_ON'
        text = "Hide Timeline Markers" if show_markers else "Show Timeline Markers"
        row.operator("btc.toggle_markers", text=text, icon=icon)

# Panel con - Marked Keyframes
class BTC_PT_MarkedKeyframesPanel(PanelBasics, Panel):
    bl_idname = "BTC_PT_marked_keyframes"
    bl_label = "Marked Keyframes"
    bl_parent_id = "BTC_PT_blender_to_cascadeur"
    
    @classmethod
    def poll(cls, context):
        return context.scene.btc_armature is not None
    
    def draw(self, context):
        layout = self.layout
        
        # Add filter from v2.3
        box = layout.box()
        row = box.row(align=True)
        row.prop(context.scene.btc_filter, "filter_string", text="", icon='VIEWZOOM')
        row.prop(context.scene.btc_filter, "filter_state", text="")
        
        # Count marked keyframes
        marked_count = 0
        total_count = len(context.scene.btc_keyframes)
        for item in context.scene.btc_keyframes:
            if item.is_marked:
                marked_count += 1
        
        # Marked count and refresh button
        row = layout.row()
        row.label(text=f"Marked: {marked_count} / Total: {total_count}")
        row.operator("btc.refresh_keyframe_list", text="", icon='FILE_REFRESH')
        
        # Keyframe list with filter
        row = layout.row()
        row.template_list(
            "BTC_UL_KeyframeList", "", 
            context.scene, "btc_keyframes", 
            context.scene, "btc_keyframe_index", 
            rows=6
        )
        
        # Add list manipulation buttons
        col = row.column(align=True)
        col.operator("btc.keyframe_add", icon='ADD', text="")
        col.operator("btc.keyframe_remove", icon='REMOVE', text="")
        col.separator()
        col.operator("btc.keyframe_move", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("btc.keyframe_move", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # Jump to frame button
        if context.scene.btc_keyframe_index >= 0 and context.scene.btc_keyframe_index < len(context.scene.btc_keyframes):
            selected_frame = context.scene.btc_keyframes[context.scene.btc_keyframe_index].frame
            row = layout.row()
            op = row.operator("screen.frame_jump", text=f"Jump to Frame {selected_frame}", icon="TIME")
            op.end = False

# Panel con - Export
class BTC_PT_ExportPanel(PanelBasics, Panel):
    bl_idname = "BTC_PT_export"
    bl_label = "Export"
    bl_parent_id = "BTC_PT_blender_to_cascadeur"
    
    @classmethod
    def poll(cls, context):
        return context.scene.btc_armature is not None
    
    def draw(self, context):
        layout = self.layout
        
        # Check if any keyframes are marked
        has_marked_keyframes = False
        for item in context.scene.btc_keyframes:
            if item.is_marked:
                has_marked_keyframes = True
                break
        
        # Show warning if no keyframes are marked
        if not has_marked_keyframes:
            box = layout.box()
            box.label(text="No keyframes are marked", icon="ERROR")
            box.label(text="Mark keyframes before exporting")
        
        # Export Object button
        row = layout.row()
        row.scale_y = 1.2
        row.operator("btc.export_object", text="Export Object", icon="OBJECT_DATA")
        
        # Export Animation button
        row = layout.row()
        row.scale_y = 1.2
        row.enabled = has_marked_keyframes
        row.operator("btc.export_animation", text="Export Animation", icon="ARMATURE_DATA")
        
        # Add Export Auto-Rig Pro button from v2.3
        row = layout.row()
        row.scale_y = 1.2
        row.operator("btc.export_auto_rig_pro", text="Export Auto-Rig Pro", icon="ARMATURE_DATA")

# Panel chính: Cascadeur Cleaner
class BTC_PT_CascadeurCleanerPanel(PanelBasics, Panel):
    bl_idname = "BTC_PT_cascadeur_cleaner"
    bl_label = "Cascadeur Cleaner"
    
    def draw_header(self, context):
        self.layout.label(text="", icon="BRUSH_DATA")
    
    def draw(self, context):
        layout = self.layout
        
        # Cascadeur executable status
        from ..utils.csc_handling import CascadeurHandler
        handler = CascadeurHandler()
        
        if handler.is_csc_exe_path_valid:
            box = layout.box()
            box.label(text="Cascadeur Found", icon="CHECKMARK")
            box.label(text=os.path.basename(handler.csc_exe_path_addon_preference))
        else:
            box = layout.box()
            box.label(text="Cascadeur Not Found", icon="ERROR")
            box.label(text="Set path in Addon Preferences")
            box.operator("preferences.addon_show", text="Open Preferences").module=__package__.split(".")[0]
        
        # Open Cascadeur button
        row = layout.row()
        row.scale_y = 1.2
        row.enabled = handler.is_csc_exe_path_valid
        row.operator("btc.open_cascadeur", text="Open Cascadeur", icon="MESH_UVSPHERE")
        
        # Import FBX and JSON buttons
        col = layout.column(align=True)
        col.enabled = handler.is_csc_exe_path_valid
        
        row = col.row(align=True)
        row.operator("btc.import_fbx", text="Import FBX", icon="IMPORT")
        row.operator("btc.import_json", text="Import JSON", icon="FILE_TEXT")
        
        # Clean Keyframes button
        row = col.row()
        row.operator("btc.clean_keyframes_cascadeur", text="Clean Keyframes", icon="BRUSH_DATA")

# Panel chính: Cascadeur to Blender
class BTC_PT_CascadeurToBlenderPanel(PanelBasics, Panel):
    bl_idname = "BTC_PT_cascadeur_to_blender"
    bl_label = "Cascadeur to Blender"
    
    def draw_header(self, context):
        self.layout.label(text="", icon="IMPORT")
    
    def draw(self, context):
        layout = self.layout
        
        # Cascadeur executable status
        from ..utils.csc_handling import CascadeurHandler
        handler = CascadeurHandler()
        
        # Import from Cascadeur
        col = layout.column()
        col.enabled = handler.is_csc_exe_path_valid
        
        row = col.row()
        row.scale_y = 1.2
        row.operator("btc.import_scene", text="Import Scene", icon="SCENE_DATA")
        
        row = col.row()
        row.scale_y = 1.2
        row.operator("btc.import_all_scenes", text="Import All Scenes", icon="DOCUMENTS")
        
        # Clean Keyframes in Blender
        box = layout.box()
        box.label(text="Cleanup Tools:", icon="BRUSH_DATA")
        
        row = box.row()
        row.operator("btc.clean_keyframes", text="Clean Keyframes", icon="BRUSH_DATA")

# List of classes to register
classes = [
    BTC_PT_BlenderToCascadeurPanel,
    BTC_PT_CharacterPanel,
    BTC_PT_KeyframeMarkersPanel,
    BTC_PT_MarkedKeyframesPanel,
    BTC_PT_ExportPanel,
    BTC_PT_CascadeurCleanerPanel,
    BTC_PT_CascadeurToBlenderPanel,
]