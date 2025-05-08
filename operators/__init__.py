# Import các modules trong operators
modules = [
    'keyframe_operators',
    'export_operators',
    'import_operators',
    'clean_operators',
    'csc_operators'
]

# Reload module nếu đã được import
if "bpy" in locals():
    import importlib
    for module in modules:
        module_name = f"{__name__}.{module}"
        if module_name in globals():
            importlib.reload(globals()[module_name])
else:
    # Import lần đầu
    for module in modules:
        exec(f"from . import {module}")