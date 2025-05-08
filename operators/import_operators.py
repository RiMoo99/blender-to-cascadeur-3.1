import bpy
import os
import json
from bpy.types import Operator
from bpy.props import StringProperty
from ..utils import file_utils, preferences

# Import FBX từ Cascadeur vào Blender
class BTC_OT_ImportScene(Operator):
    bl_idname = "btc.import_scene"
    bl_label = "Import Scene"
    bl_description = "Import the current scene from Cascadeur"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Lấy cài đặt preferences
        prefs = preferences.get_preferences(context)
        exchange_folder = preferences.get_exchange_folder(context)
        
        try:
            # Tạo trigger file để yêu cầu Cascadeur export scene hiện tại
            trigger_data = {"action": "export_current_scene"}
            
            # Tạo thư mục con cho Cascadeur
            cascadeur_trigger_folder = os.path.join(exchange_folder, "cascadeur_triggers")
            file_utils.ensure_dir_exists(cascadeur_trigger_folder)
            
            # Tạo file trigger
            trigger_path = file_utils.create_trigger_file(exchange_folder, "export_current_scene", trigger_data)
            if not trigger_path:
                self.report({'ERROR'}, "Failed to create trigger file")
                return {'CANCELLED'}
            
            # Tự động mở Cascadeur nếu đã bật tùy chọn
            if prefs.auto_open_cascadeur:
                bpy.ops.btc.open_cascadeur()
            
            self.report({'INFO'}, "Requested scene import from Cascadeur")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Import error: {str(e)}")
            return {'CANCELLED'}

# Import tất cả scene từ Cascadeur vào Blender
class BTC_OT_ImportAllScenes(Operator):
    bl_idname = "btc.import_all_scenes"
    bl_label = "Import All Scenes"
    bl_description = "Import all open scenes from Cascadeur"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Lấy cài đặt preferences
        prefs = preferences.get_preferences(context)
        exchange_folder = preferences.get_exchange_folder(context)
        
        try:
            # Tạo trigger file để yêu cầu Cascadeur export tất cả scene
            trigger_data = {"action": "export_all_scenes"}
            
            # Tạo thư mục con cho Cascadeur
            cascadeur_trigger_folder = os.path.join(exchange_folder, "cascadeur_triggers")
            file_utils.ensure_dir_exists(cascadeur_trigger_folder)
            
            # Tạo file trigger
            trigger_path = file_utils.create_trigger_file(exchange_folder, "export_all_scenes", trigger_data)
            if not trigger_path:
                self.report({'ERROR'}, "Failed to create trigger file")
                return {'CANCELLED'}
            
            # Tự động mở Cascadeur nếu đã bật tùy chọn
            if prefs.auto_open_cascadeur:
                bpy.ops.btc.open_cascadeur()
            
            self.report({'INFO'}, "Requested all scenes import from Cascadeur")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Import error: {str(e)}")
            return {'CANCELLED'}

# Import FBX vào Cascadeur
class BTC_OT_ImportFBXToCascadeur(Operator):
    bl_idname = "btc.import_fbx"
    bl_label = "Import FBX"
    bl_description = "Import FBX file to Cascadeur"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        subtype='FILE_PATH',
    )
    
    filter_glob: StringProperty(
        default="*.fbx",
        options={'HIDDEN'},
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}
        
        if not os.path.exists(self.filepath):
            self.report({'ERROR'}, f"File not found: {self.filepath}")
            return {'CANCELLED'}
            
        try:
            # Lấy cài đặt preferences
            prefs = preferences.get_preferences(context)
            exchange_folder = preferences.get_exchange_folder(context)
            
            # Sao chép file sang thư mục trao đổi
            fbx_path = file_utils.copy_file_to_exchange(self.filepath, exchange_folder, "fbx")
            if not fbx_path:
                self.report({'ERROR'}, "Failed to copy FBX to exchange folder")
                return {'CANCELLED'}
            
            # Tạo trigger file
            trigger_data = {
                "action": "import_fbx",
                "data": {
                    "fbx_path": fbx_path
                }
            }
            
            # Tạo file trigger
            trigger_path = file_utils.create_trigger_file(exchange_folder, "import_fbx", trigger_data)
            if not trigger_path:
                self.report({'ERROR'}, "Failed to create trigger file")
                return {'CANCELLED'}
            
            # Tự động mở Cascadeur nếu đã bật tùy chọn
            if prefs.auto_open_cascadeur:
                bpy.ops.btc.open_cascadeur()
            
            self.report({'INFO'}, f"Requested FBX import to Cascadeur: {os.path.basename(self.filepath)}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Import error: {str(e)}")
            return {'CANCELLED'}

# Import JSON vào Cascadeur
class BTC_OT_ImportJSONToCascadeur(Operator):
    bl_idname = "btc.import_json"
    bl_label = "Import JSON"
    bl_description = "Import JSON keyframe data to Cascadeur"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        subtype='FILE_PATH',
    )
    
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}
        
        if not os.path.exists(self.filepath):
            self.report({'ERROR'}, f"File not found: {self.filepath}")
            return {'CANCELLED'}
            
        try:
            # Lấy cài đặt preferences
            prefs = preferences.get_preferences(context)
            exchange_folder = preferences.get_exchange_folder(context)
            
            # Sao chép file sang thư mục trao đổi
            json_path = file_utils.copy_file_to_exchange(self.filepath, exchange_folder, "json")
            if not json_path:
                self.report({'ERROR'}, "Failed to copy JSON to exchange folder")
                return {'CANCELLED'}
            
            # Tạo trigger file
            trigger_data = {
                "action": "import_json",
                "data": {
                    "json_path": json_path
                }
            }
            
            # Tạo file trigger
            trigger_path = file_utils.create_trigger_file(exchange_folder, "import_json", trigger_data)
            if not trigger_path:
                self.report({'ERROR'}, "Failed to create trigger file")
                return {'CANCELLED'}
            
            # Tự động mở Cascadeur nếu đã bật tùy chọn
            if prefs.auto_open_cascadeur:
                bpy.ops.btc.open_cascadeur()
            
            self.report({'INFO'}, f"Requested JSON import to Cascadeur: {os.path.basename(self.filepath)}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Import error: {str(e)}")
            return {'CANCELLED'}

# Danh sách các lớp để đăng ký
classes = [
    BTC_OT_ImportScene,
    BTC_OT_ImportAllScenes,
    BTC_OT_ImportFBXToCascadeur,
    BTC_OT_ImportJSONToCascadeur,
]