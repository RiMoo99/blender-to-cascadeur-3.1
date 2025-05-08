import csc
import tempfile
import os


def set_export_settings(preferences=None):
    """
    Setting the fbx export settings in Cascadeur.
    
    Args:
        preferences: Dictionary with settings
    
    Returns:
        FbxSettings object
    """
    if preferences is None:
        preferences = {}
        
    settings = csc.fbx.FbxSettings()
    settings.mode = csc.fbx.FbxSettingsMode.Binary

    settings.apply_euler_filter = preferences.get("euler_filter", False)
        
    if preferences.get("up_axis") == "Z":
        settings.up_axis = csc.fbx.FbxSettingsAxis.Z
    else:
        settings.up_axis = csc.fbx.FbxSettingsAxis.Y
        
    settings.bake_animation = preferences.get("bake_animation", True)
    
    return settings


def get_export_path(scene_name):
    """
    FBX export path in the temp folder using the scene name.
    
    Args:
        scene_name: Name of the Cascadeur scene
    
    Returns:
        FBX export path
    """
    temp_dir = tempfile.gettempdir()
    file_name = scene_name.replace(".casc", "") + ".fbx"
    return os.path.join(temp_dir, file_name)


def ensure_dir_exists(directory):
    """
    Ensure directory exists, create if not.
    
    Args:
        directory: Directory path
    
    Returns:
        Directory path
    """
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    return directory