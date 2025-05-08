import bpy
import os
import json
from bpy.types import Operator

# Clean Keyframes trong Blender
class BTC_OT_CleanKeyframes(Operator):
    bl_idname = "btc.clean_keyframes"
    bl_label = "Clean Keyframes"
    bl_description = "Remove all keyframes except those marked in metadata"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and 
                context.active_object.animation_data and 
                context.active_object.animation_data.action)
    
    def execute(self, context):
        armature = context.active_object
        
        # Lấy danh sách keyframe được đánh dấu từ metadata
        marked_keyframes = self.get_marked_keyframes(context)
        
        if not marked_keyframes:
            self.report({'WARNING'}, "No marked keyframes found in metadata")
            return {'CANCELLED'}
        
        # Xóa các keyframe không nằm trong danh sách đã đánh dấu
        cleaned_count = self.clean_keyframes(armature, marked_keyframes)
        
        self.report({'INFO'}, f"Cleaned keyframes. Kept {len(marked_keyframes)} marked keyframes, removed {cleaned_count} keyframes")
        return {'FINISHED'}
    
    def get_marked_keyframes(self, context):
        # Lấy danh sách keyframe từ metadata
        marked_frames = []
        
        # Nếu có danh sách keyframe đã đánh dấu từ UI
        if hasattr(context.scene, "btc_keyframes"):
            for item in context.scene.btc_keyframes:
                if item.is_marked:
                    marked_frames.append(item.frame)
        
        return marked_frames
    
    def clean_keyframes(self, armature, marked_keyframes):
        # Lưu frame hiện tại
        current_frame = bpy.context.scene.frame_current
        
        action = armature.animation_data.action
        fcurves = action.fcurves
        
        removed_count = 0
        
        # Lặp qua từng fcurve và xóa các keyframe không được đánh dấu
        for fcurve in fcurves:
            # Lặp qua từng keyframe trong fcurve theo thứ tự ngược lại
            # vì chúng ta sẽ xóa một số keyframe
            keyframe_points = fcurve.keyframe_points
            i = len(keyframe_points) - 1
            
            while i >= 0:
                keyframe = keyframe_points[i]
                frame = int(keyframe.co[0])
                
                # Nếu frame không nằm trong danh sách được đánh dấu, xóa nó
                if frame not in marked_keyframes:
                    keyframe_points.remove(keyframe)
                    removed_count += 1
                
                i -= 1
        
        # Cập nhật animation để áp dụng các thay đổi
        action.fcurves.update()
        
        # Khôi phục frame hiện tại
        bpy.context.scene.frame_current = current_frame
        
        return removed_count

# Clean Keyframes trong Cascadeur
class BTC_OT_CleanKeyframesCascadeur(Operator):
    bl_idname = "btc.clean_keyframes_cascadeur"
    bl_label = "Clean Keyframes Cascadeur"
    bl_description = "Execute keyframe manager in Cascadeur"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # Kiểm tra xem đường dẫn exe Cascadeur có hợp lệ không
        from ..utils.csc_handling import CascadeurHandler
        return CascadeurHandler().is_csc_exe_path_valid
    
    def execute(self, context):
        # Lấy danh sách keyframe được đánh dấu
        marked_keyframes = {}
        count = 0
        for item in context.scene.btc_keyframes:
            if item.is_marked:
                marked_keyframes[str(item.frame)] = {}
                count += 1
        
        if not marked_keyframes:
            self.report({'WARNING'}, "No marked keyframes found")
            return {'CANCELLED'}
        
        # Lấy thư mục trao đổi
        from ..utils import file_utils, preferences
        exchange_folder = preferences.get_exchange_folder(context)
        
        # Tạo trigger file
        trigger_data = {
            "action": "clean_keyframes",
            "data": {
                "keyframes": marked_keyframes
            }
        }
        
        try:
            trigger_path = file_utils.create_trigger_file(exchange_folder, "clean_keyframes", trigger_data)
            if not trigger_path:
                self.report({'ERROR'}, "Failed to create trigger file")
                return {'CANCELLED'}
                
            # Chạy lệnh trong Cascadeur
            from ..utils.csc_handling import CascadeurHandler
            handler = CascadeurHandler()
            
            if not handler.execute_csc_command("commands.externals.temp_keyframe_cleaner"):
                self.report({'ERROR'}, "Failed to execute command in Cascadeur")
                return {'CANCELLED'}
                
            self.report({'INFO'}, f"Keyframe cleaning request sent to Cascadeur. {count} marked keyframes")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}

# Danh sách các lớp để đăng ký
classes = [
    BTC_OT_CleanKeyframes,
    BTC_OT_CleanKeyframesCascadeur,
]