import bpy
import os
import shutil
import configparser

# Importamos desde el paquete padre
from .. import addon_info


class BTC_OT_OpenCascadeur(bpy.types.Operator):
    bl_idname = "btc.open_cascadeur"
    bl_label = "Open Cascadeur"
    bl_description = "Open Cascadeur application"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        from ..utils.csc_handling import CascadeurHandler
        return CascadeurHandler().is_csc_exe_path_valid
    
    def execute(self, context):
        from ..utils.csc_handling import CascadeurHandler
        ch = CascadeurHandler()
        
        if not ch.is_csc_exe_path_valid:
            self.report({'ERROR'}, f"Cascadeur executable not found at: {ch.csc_exe_path_addon_preference}")
            return {'CANCELLED'}
        
        try:
            # Mở Cascadeur
            if ch.start_cascadeur():
                self.report({'INFO'}, "Cascadeur opened successfully")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Failed to open Cascadeur")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open Cascadeur: {str(e)}")
            return {'CANCELLED'}

class BTC_OT_InstallCascadeurAddon(bpy.types.Operator):
    bl_idname = "btc.install_cascadeur_addon"
    bl_label = "Install Cascadeur Add-on"
    bl_description = "Install the required add-on files in Cascadeur"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        from ..utils.csc_handling import CascadeurHandler
        return CascadeurHandler().is_csc_exe_path_valid
    
    def execute(self, context):
        # Importamos las funciones que necesitamos en el ámbito de la función
        from ..utils.csc_handling import CascadeurHandler
        from ..utils import preferences
        
        # Función interna para asegurar que un directorio existe
        def ensure_dir_exists(directory):
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            return directory
            
        ch = CascadeurHandler()
        
        if not ch.is_csc_exe_path_valid:
            self.report({'ERROR'}, f"Cascadeur executable not found at: {ch.csc_exe_path_addon_preference}")
            return {'CANCELLED'}
        
        try:
            # Xác định thư mục cài đặt Cascadeur
            csc_dir = ch.csc_dir
            if not csc_dir:
                self.report({'ERROR'}, "Cascadeur directory not found")
                return {'CANCELLED'}
                
            # Xác định thư mục commands
            commands_path = ch.commands_path
            if not commands_path:
                self.report({'ERROR'}, "Cascadeur commands path not found")
                return {'CANCELLED'}
            
            # Thư mục đích cho addon Cascadeur
            target_dir = os.path.join(commands_path, "externals")
            ensure_dir_exists(target_dir)
            
            # Thư mục nguồn của addon Cascadeur
            addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            source_dir = os.path.join(addon_dir, "csc_files", "externals")
            
            if not os.path.exists(source_dir):
                self.report({'ERROR'}, "Source files for Cascadeur add-on not found")
                return {'CANCELLED'}
            
            # Sao chép các file cần thiết
            # Danh sách các file cần sao chép
            files_to_copy = os.listdir(source_dir)
            
            # Sao chép từng file
            success = True
            for file_name in files_to_copy:
                source_file = os.path.join(source_dir, file_name)
                target_file = os.path.join(target_dir, file_name)
                
                try:
                    if os.path.isfile(source_file):
                        shutil.copy2(source_file, target_file)
                except Exception as e:
                    success = False
                    self.report({'ERROR'}, f"Failed to copy {file_name}: {str(e)}")
            
            if not success:
                self.report({'ERROR'}, "You don't have permission to copy all files to Cascadeur")
                self.report({'INFO'}, "Please restart Blender as Admin and try again")
                return {'CANCELLED'}
            
            # Cập nhật file settings.cfg với đường dẫn exchange folder
            settings_file = os.path.join(target_dir, "settings.cfg")
            if os.path.exists(settings_file):
                exchange_folder = preferences.get_exchange_folder(context)
                
                config = configparser.ConfigParser()
                config.read(settings_file)
                
                if not config.has_section("Addon Settings"):
                    config.add_section("Addon Settings")
                
                # Đặt cổng và thư mục trao đổi
                port = preferences.get_port_number()
                config.set("Addon Settings", "port", str(port))
                config.set("Addon Settings", "exchange_folder", exchange_folder)
                
                try:
                    with open(settings_file, 'w') as f:
                        config.write(f)
                except Exception as e:
                    self.report({'WARNING'}, f"Could not update settings.cfg: {str(e)}")
            
            self.report({'INFO'}, "Cascadeur add-on installed successfully")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to install Cascadeur add-on: {str(e)}")
            return {'CANCELLED'}

# Danh sách các lớp để đăng ký
classes = [
    BTC_OT_OpenCascadeur,
    BTC_OT_InstallCascadeurAddon,
]