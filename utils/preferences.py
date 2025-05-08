import bpy
import os
import tempfile
from bpy.types import AddonPreferences
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty

class BTCAddonPreferences(AddonPreferences):
    bl_idname = __package__.split(".")[0]
    
    # Đường dẫn đến Cascadeur executable
    csc_exe_path: StringProperty(
        name="Cascadeur Executable",
        subtype='FILE_PATH',
        description="Path to Cascadeur executable"
    )
    
    # Thư mục dùng cho trao đổi file
    exchange_folder: StringProperty(
        name="Exchange Folder",
        subtype='DIR_PATH',
        description="Folder used for file exchange between Blender and Cascadeur"
    )
    
    # Tùy chọn vị trí lưu file
    exchange_folder_location: EnumProperty(
        name="Exchange Folder Location",
        items=[
            ('CASCADEUR', "Cascadeur Folder", "Create a subfolder in Cascadeur installation directory"),
            ('ADDON', "Add-on Folder", "Create a subfolder in the add-on directory"),
            ('CUSTOM', "Custom Location", "Use a custom folder location"),
            ('TEMP', "Temporary Folder", "Use system's temporary folder")
        ],
        default='TEMP',
        description="Choose where to store exchange files"
    )
    
    # Thời gian tự động dọn dẹp các file cũ
    cleanup_interval: IntProperty(
        name="Cleanup Interval (hours)",
        description="Automatically clean up processed trigger files older than this many hours",
        default=24,
        min=1,
        max=168
    )
    
    # Tự động mở Cascadeur khi export
    auto_open_cascadeur: BoolProperty(
        name="Auto-open Cascadeur",
        description="Automatically open Cascadeur when exporting",
        default=False
    )
    
    # Port cho socket communication (fallback)
    socket_port: IntProperty(
        name="Socket Port",
        description="Port for socket communication (fallback method)",
        default=48152,
        min=1024,
        max=65535
    )
    
    def draw(self, context):
        layout = self.layout
        
        # Cascadeur Executable
        box = layout.box()
        box.label(text="Cascadeur Settings:", icon="PREFERENCES")
        row = box.row()
        row.prop(self, "csc_exe_path")
        
        # Kiểm tra tính hợp lệ của đường dẫn Cascadeur
        from ..utils.csc_handling import CascadeurHandler
        handler = CascadeurHandler()
        if handler.is_csc_exe_path_valid:
            row = box.row()
            row.label(text="Cascadeur found ✓", icon="CHECKMARK")
        else:
            row = box.row()
            row.label(text="Cascadeur not found ✗", icon="ERROR")
            row = box.row()
            row.label(text="Please select Cascadeur executable file:")
            row = box.row()
            row.label(text="Windows: cascadeur.exe")
            row = box.row()
            row.label(text="macOS: Cascadeur.app")
            row = box.row() 
            row.label(text="Linux: cascadeur")
        
        # Exchange Folder
        box = layout.box()
        box.label(text="File Exchange Settings:", icon="FOLDER_REDIRECT")
        row = box.row()
        row.prop(self, "exchange_folder_location")
        
        # Only show custom folder field if CUSTOM is selected
        if self.exchange_folder_location == 'CUSTOM':
            row = box.row()
            row.prop(self, "exchange_folder")
            
            if not self.exchange_folder:
                row = box.row()
                row.label(text="Please select a folder", icon="ERROR")
        
        # Display the actual exchange folder path
        exchange_folder = get_exchange_folder(context)
        row = box.row()
        row.label(text=f"Current exchange folder:")
        row = box.row()
        row.label(text=exchange_folder)
        
        # Check if exchange folder exists and is writable
        if exchange_folder:
            if not os.path.exists(exchange_folder):
                try:
                    os.makedirs(exchange_folder)
                    row = box.row()
                    row.label(text="Created exchange folder ✓", icon="CHECKMARK")
                except (OSError, PermissionError):
                    row = box.row()
                    row.label(text="Cannot create exchange folder", icon="ERROR")
            elif not os.access(exchange_folder, os.W_OK):
                row = box.row()
                row.label(text="Exchange folder not writable", icon="ERROR")
        
        # Cleanup settings
        row = box.row()
        row.prop(self, "cleanup_interval")
        
        # Options
        box = layout.box()
        box.label(text="Options:", icon="SETTINGS")
        row = box.row()
        row.prop(self, "auto_open_cascadeur")
        
        # Socket settings (fallback)
        box = layout.box()
        box.label(text="Advanced Settings:", icon="TOOL_SETTINGS")
        row = box.row()
        row.prop(self, "socket_port")
        
        # Installation
        box = layout.box()
        box.label(text="Cascadeur Add-on Installation:", icon="PLUGIN")
        row = box.row()
        op = row.operator("btc.install_cascadeur_addon", text="Install Cascadeur Add-on")
        row.enabled = handler.is_csc_exe_path_valid
        
        # Only show install button if Cascadeur was found
        if not handler.is_csc_exe_path_valid:
            row = box.row()
            row.label(text="Set Cascadeur path first", icon="INFO")
        
        # Info
        box = layout.box()
        box.label(text="How to use:", icon="HELP")
        col = box.column()
        col.label(text="1. Set the Cascadeur executable path")
        col.label(text="2. Set the exchange folder location")
        col.label(text="3. Install the add-on in Cascadeur")
        col.label(text="4. Start using the B2C panel in the 3D viewport")
        
        # Version info
        from .. import addon_info
        if hasattr(addon_info, 'ADDON_VERSION'):
            box = layout.box()
            box.label(text=f"Version: {'.'.join(str(v) for v in addon_info.ADDON_VERSION)}")

# Danh sách các lớp để đăng ký
classes = [
    BTCAddonPreferences,
]

def get_preferences(context):
    """Helper function to get add-on preferences"""
    try:
        return context.preferences.addons[__package__.split(".")[0]].preferences
    except (KeyError, AttributeError):
        return None

def get_exchange_folder(context):
    """Get the exchange folder path based on preferences"""
    prefs = get_preferences(context)
    if not prefs:
        # Fallback to temp folder if preferences not available
        return os.path.join(tempfile.gettempdir(), "blender_to_cascadeur_exchange")
    
    if prefs.exchange_folder_location == 'CUSTOM' and prefs.exchange_folder:
        return prefs.exchange_folder
    
    if prefs.exchange_folder_location == 'CASCADEUR' and prefs.csc_exe_path:
        # Get Cascadeur directory
        from .csc_handling import CascadeurHandler
        csc_handler = CascadeurHandler()
        csc_dir = csc_handler.csc_dir
        if csc_dir:
            return os.path.join(csc_dir, "exchange")
        
        # Fallback to temp if Cascadeur dir not found
        return os.path.join(tempfile.gettempdir(), "blender_to_cascadeur_exchange")
    
    if prefs.exchange_folder_location == 'ADDON':
        # Get addon directory
        addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(addon_dir, "exchange")
    
    # Default to temp folder
    return os.path.join(tempfile.gettempdir(), "blender_to_cascadeur_exchange")

def get_port_number():
    """Get the port number from preferences"""
    try:
        import configparser
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings.cfg")
        config = configparser.ConfigParser()
        
        if os.path.exists(config_path):
            config.read(config_path)
            if config.has_section("Addon Settings") and config.has_option("Addon Settings", "port"):
                return config.getint("Addon Settings", "port")
    except Exception:
        pass
    
    # Default port
    from ..addon_info import DEFAULT_PORT
    return DEFAULT_PORT