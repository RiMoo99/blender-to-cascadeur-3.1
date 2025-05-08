import os

# Đừng quên bl_info để tránh cảnh báo hiệu suất
bl_info = {
    "name": "Blender to Cascadeur",
    "author": "Ri x Claude",
    "version": (2, 3, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > B2C",
    "description": "Mark keyframes for Cascadeur export with extended features",
    "category": "Animation",
}

# Paths
PACKAGE_NAME = __package__
ADDON_PATH = os.path.dirname(os.path.abspath(__file__))

# Version
ADDON_VERSION = (2, 3, 1)

# Globals
operation_completed = True

# Default port for network communication
DEFAULT_PORT = 48152