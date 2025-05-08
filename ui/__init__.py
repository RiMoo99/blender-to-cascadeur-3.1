import bpy
import importlib

# Import main_panel module
from . import main_panel
from ..operators.keyframe_operators import BTC_UL_KeyframeList

# Định nghĩa danh sách classes để đăng ký
classes = [
    main_panel.PanelBasics,
    main_panel.BTC_PT_BlenderToCascadeurPanel,
    main_panel.BTC_PT_CharacterPanel,
    main_panel.BTC_PT_KeyframeMarkersPanel,
    main_panel.BTC_PT_MarkedKeyframesPanel,
    main_panel.BTC_PT_ExportPanel,
    main_panel.BTC_PT_CascadeurCleanerPanel,
    main_panel.BTC_PT_CascadeurToBlenderPanel,
    BTC_UL_KeyframeList,  # Đăng ký lớp UIList ở đây
]

# Hàm reload module khi Blender tải lại addon
def reload_modules():
    if 'main_panel' in globals():
        importlib.reload(main_panel)