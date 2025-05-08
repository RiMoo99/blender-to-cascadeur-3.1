import bpy
import json
import os
import time
import tempfile
from bpy.types import Operator
from bpy.props import StringProperty
from ..utils import file_utils, preferences

# Export Object
class BTC_OT_ExportObject(Operator):
    bl_idname = "btc.export_object"
    bl_label = "Export Object"
    bl_description = "Export selected object to Cascadeur"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.btc_armature is not None
    
    def execute(self, context):
        armature = context.scene.btc_armature
        
        if not armature:
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}
        
        # Get preferences settings
        prefs = preferences.get_preferences(context)
        exchange_folder = preferences.get_exchange_folder(context)
        
        # Create export path
        export_path = file_utils.get_export_path(file_type="fbx", use_temp=True)
        
        try:
            # Export FBX
            if not self.export_fbx(context, export_path):
                self.report({'ERROR'}, "Failed to export FBX")
                return {'CANCELLED'}
            
            # Copy file to exchange folder
            fbx_path = file_utils.copy_file_to_exchange(export_path, exchange_folder, "fbx")
            if not fbx_path:
                self.report({'ERROR'}, "Failed to copy FBX to exchange folder")
                return {'CANCELLED'}
            
            # Create trigger file
            trigger_data = {
                "action": "import_object",
                "data": {
                    "fbx_path": fbx_path,
                    "object_name": armature.name
                }
            }
            
            trigger_path = file_utils.create_trigger_file(exchange_folder, "import_object", trigger_data)
            if not trigger_path:
                self.report({'ERROR'}, "Failed to create trigger file")
                return {'CANCELLED'}
            
            # Auto open Cascadeur if option enabled
            if prefs.auto_open_cascadeur:
                bpy.ops.btc.open_cascadeur()
            
            self.report({'INFO'}, f"Exported object to {fbx_path}")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Export error: {str(e)}")
            return {'CANCELLED'}
def export_fbx(self, context, filepath):
        """Export armature to FBX"""
        try:
            # Save current selection state
            original_selection = context.selected_objects.copy()
            active_object = context.active_object
            
            # Select armature
            bpy.ops.object.select_all(action='DESELECT')
            context.scene.btc_armature.select_set(True)
            context.view_layer.objects.active = context.scene.btc_armature
            
            # Export FBX
            bpy.ops.export_scene.fbx(
                filepath=filepath,
                use_selection=True,
                object_types={'ARMATURE', 'MESH'},
                use_mesh_modifiers=True,
                use_mesh_modifiers_render=True,
                add_leaf_bones=False
            )
            
            # Restore selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_selection:
                obj.select_set(True)
            if active_object:
                context.view_layer.objects.active = active_object
                
            return True
        
        except Exception as e:
            print(f"FBX export error: {str(e)}")
            return False

# Export Animation
class BTC_OT_ExportAnimation(Operator):
    bl_idname = "btc.export_animation"
    bl_label = "Export Animation"
    bl_description = "Export animation with marked keyframes to Cascadeur"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        name="Save Path",
        description="Path to save the metadata file",
        default="//",
        subtype='FILE_PATH'
    )
    
    @classmethod
    def poll(cls, context):
        # Check if armature is selected and some keyframes are marked
        if not context.scene.btc_armature:
            return False
            
        # Check if any keyframes are marked
        for item in context.scene.btc_keyframes:
            if item.is_marked:
                return True
                
        return False
    
    def invoke(self, context, event):
        # Save current frame
        self.current_frame = context.scene.frame_current
        
        # Get default filename from preferences
        addon_prefs = preferences.get_preferences(context)
        if addon_prefs:
            directory = addon_prefs.export_path
            filename = addon_prefs.export_filename
            if directory and filename:
                self.filepath = os.path.join(directory, f"{filename}_keyframes.json")
            else:
                # Fallback to Blender file name
                blend_path = bpy.data.filepath
                if blend_path:
                    dir_path = os.path.dirname(blend_path)
                    filename = os.path.splitext(os.path.basename(blend_path))[0]
                    self.filepath = os.path.join(dir_path, f"{filename}_keyframes.json")
        
        # Show file browser for metadata JSON
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        try:
            # Restore current frame before file browser
            if hasattr(self, 'current_frame'):
                context.scene.frame_current = self.current_frame
            
            # Export metadata JSON
            marked_keyframes = self.get_marked_keyframes(context)
            
            # Add .json extension if missing
            filepath = self.filepath
            if not filepath.lower().endswith('.json'):
                filepath += '.json'
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Write metadata file
            with open(filepath, 'w') as f:
                json.dump(marked_keyframes, f, indent=2)
            
            self.report({'INFO'}, f"Exported keyframe metadata to {filepath}")
            
            # Get preferences
            prefs = preferences.get_preferences(context)
            exchange_folder = preferences.get_exchange_folder(context)
            
            # Copy file to exchange folder for later use
            json_path = file_utils.copy_file_to_exchange(filepath, exchange_folder, "json")
            if not json_path:
                self.report({'WARNING'}, "Failed to copy JSON to exchange folder, but file was saved locally")
            
            # Make sure we're in object mode before continuing
            if context.object and context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Call ARP export with delay using timer
            def open_arp_export_delayed():
                self.open_arp_export(context)
                return None  # Remove timer
                
            bpy.app.timers.register(open_arp_export_delayed, first_interval=0.5)
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error exporting metadata: {e}")
            return {'CANCELLED'}
    
    def get_marked_keyframes(self, context):
        """Get list of marked keyframes"""
        marked_keyframes = {}
        
        for item in context.scene.btc_keyframes:
            if item.is_marked:
                marked_keyframes[str(item.frame)] = {}
        
        return marked_keyframes
    
    def open_arp_export(self, context):
        """Open Auto-Rig Pro export panel"""
        try:
            # Save current frame
            current_frame = context.scene.frame_current
            
            # Select armature
            armature = context.scene.btc_armature
            if not armature:
                self.report({'WARNING'}, "No armature selected. Please select an armature first.")
                return
            
            # Make sure we're in Object mode
            if context.object and context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Deselect all objects and select only armature
            bpy.ops.object.select_all(action='DESELECT')
            armature.select_set(True)
            context.view_layer.objects.active = armature
            
            # Try to open ARP export panel
            success = False
            
            # Try different methods
            arp_methods = [
                ("arp.arp_export_fbx_panel", "Opened ARP export panel"),
                ("arp_export_fbx_panel", "Opened ARP export panel (method 2)"),
                ("arp.export_fbx_panel", "Opened ARP export panel (method 3)"),
                ("auto_rig_pro.export_fbx_panel", "Opened ARP export panel (method 4)")
            ]
            
            for op_name, success_msg in arp_methods:
                try:
                    getattr(bpy.ops, op_name)('INVOKE_DEFAULT')
                    self.report({'INFO'}, success_msg)
                    success = True
                    break
                except Exception as e:
                    print(f"ARP export attempt failed with {op_name}: {e}")
            
            # If all attempts fail, show guide
            if not success:
                def draw_guide(self, context):
                    layout = self.layout
                    layout.label(text="Auto-Rig Pro Export Guide:", icon='INFO')
                    box = layout.box()
                    box.label(text="1. Make sure your armature is selected")
                    box.label(text="2. Open the Auto-Rig Pro panel in the 'N' sidebar")
                    box.label(text="3. Click on 'Export' tab or button")
                    box.label(text="4. Configure export settings")
                    box.label(text="5. Click 'Export FBX' to save your file")
                    box.label(text="6. Export to the exchange folder for Cascadeur")
                
                context.window_manager.popup_menu(draw_guide, title="Auto-Rig Pro Export Guide", icon='HELP')
                self.report({'INFO'}, "Please follow the guide to export with Auto-Rig Pro")
                
                # Show message about exchange folder
                exchange_folder = preferences.get_exchange_folder(context)
                self.report({'INFO'}, f"Export the FBX to: {exchange_folder}/fbx")
            
            # Restore original frame
            context.scene.frame_current = current_frame
                
        except Exception as e:
            self.report({'ERROR'}, f"Error opening ARP export: {e}")

# Auto-Rig Pro Export
class BTC_OT_ExportAutoRigPro(Operator):
    bl_idname = "btc.export_auto_rig_pro"
    bl_label = "Export Auto-Rig Pro"
    bl_description = "Export using Auto-Rig Pro exporter"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # Check if armature is selected
        return context.scene.btc_armature is not None
    
    def execute(self, context):
        # Call the same open_arp_export method
        try:
            # Save current frame
            current_frame = context.scene.frame_current
            
            # Select armature
            armature = context.scene.btc_armature
            if not armature:
                self.report({'WARNING'}, "No armature selected. Please select an armature first.")
                return {'CANCELLED'}
            
            # Make sure we're in Object mode
            if context.object and context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Deselect all objects and select only armature
            bpy.ops.object.select_all(action='DESELECT')
            armature.select_set(True)
            context.view_layer.objects.active = armature
            
            # Try to open ARP export panel
            success = False
            
            # Try different methods
            arp_methods = [
                ("arp.arp_export_fbx_panel", "Opened ARP export panel"),
                ("arp_export_fbx_panel", "Opened ARP export panel (method 2)"),
                ("arp.export_fbx_panel", "Opened ARP export panel (method 3)"),
                ("auto_rig_pro.export_fbx_panel", "Opened ARP export panel (method 4)")
            ]
            
            for op_name, success_msg in arp_methods:
                try:
                    getattr(bpy.ops, op_name)('INVOKE_DEFAULT')
                    self.report({'INFO'}, success_msg)
                    success = True
                    break
                except Exception as e:
                    print(f"ARP export attempt failed with {op_name}: {e}")
            
            # If all attempts fail, show guide
            if not success:
                def draw_guide(self, context):
                    layout = self.layout
                    layout.label(text="Auto-Rig Pro Export Guide:", icon='INFO')
                    box = layout.box()
                    box.label(text="1. Make sure your armature is selected")
                    box.label(text="2. Open the Auto-Rig Pro panel in the 'N' sidebar")
                    box.label(text="3. Click on 'Export' tab or button")
                    box.label(text="4. Configure export settings")
                    box.label(text="5. Click 'Export FBX' to save your file")
                
                context.window_manager.popup_menu(draw_guide, title="Auto-Rig Pro Export Guide", icon='HELP')
                self.report({'INFO'}, "Please follow the guide to export with Auto-Rig Pro")
            
            # Restore original frame
            context.scene.frame_current = current_frame
            
            return {'FINISHED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Error opening ARP export: {e}")
            return {'CANCELLED'}

# Export Complete
class BTC_OT_ExportComplete(Operator):
    bl_idname = "btc.export_complete"
    bl_label = "Export Complete"
    bl_description = "Create trigger file to export to Cascadeur"
    bl_options = {'REGISTER', 'UNDO'}
    
    fbx_path: StringProperty(
        name="FBX Path",
        description="Path to the exported FBX file",
        default="",
        subtype='FILE_PATH'
    )
    
    json_path: StringProperty(
        name="JSON Path",
        description="Path to the exported JSON metadata file",
        default="",
        subtype='FILE_PATH'
    )
    
    def execute(self, context):
        # Get preferences
        prefs = preferences.get_preferences(context)
        exchange_folder = preferences.get_exchange_folder(context)
        
        # Check if FBX path is valid
        if not self.fbx_path or not os.path.exists(self.fbx_path):
            self.report({'ERROR'}, "Invalid FBX path")
            return {'CANCELLED'}
        
        # Check if JSON path is valid
        if not self.json_path or not os.path.exists(self.json_path):
            self.report({'ERROR'}, "Invalid JSON path")
            return {'CANCELLED'}
        
        try:
            # Copy files to exchange folder
            fbx_path = file_utils.copy_file_to_exchange(self.fbx_path, exchange_folder, "fbx")
            if not fbx_path:
                self.report({'ERROR'}, "Failed to copy FBX to exchange folder")
                return {'CANCELLED'}
                
            json_path = file_utils.copy_file_to_exchange(self.json_path, exchange_folder, "json")
            if not json_path:
                self.report({'ERROR'}, "Failed to copy JSON to exchange folder")
                return {'CANCELLED'}
            
            # Create trigger file
            trigger_data = {
                "action": "import_animation",
                "data": {
                    "fbx_path": fbx_path,
                    "json_path": json_path,
                    "object_name": context.scene.btc_armature.name if context.scene.btc_armature else "Unknown"
                }
            }
            
            trigger_path = file_utils.create_trigger_file(exchange_folder, "import_animation", trigger_data)
            if not trigger_path:
                self.report({'ERROR'}, "Failed to create trigger file")
                return {'CANCELLED'}
            
            # Auto open Cascadeur if option enabled
            if prefs.auto_open_cascadeur:
                bpy.ops.btc.open_cascadeur()
            
            self.report({'INFO'}, f"Created trigger for Cascadeur at {trigger_path}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Export error: {str(e)}")
            return {'CANCELLED'}

# List of classes to register
classes = [
    BTC_OT_ExportObject,
    BTC_OT_ExportAnimation,
    BTC_OT_ExportAutoRigPro,
    BTC_OT_ExportComplete,
]