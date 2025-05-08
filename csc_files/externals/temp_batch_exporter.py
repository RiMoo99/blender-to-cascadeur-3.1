import csc
import os
import json
import time
import tempfile


def command_name():
    return "B2C.Temp Batch Exporter"


def run(scene):
    # Cấu hình
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.cfg")
        import configparser
        config = configparser.ConfigParser()
        config.read(config_path)
        
        exchange_folder = config.get("Addon Settings", "exchange_folder", fallback=tempfile.gettempdir())
    except:
        # Fallback to temp dir
        exchange_folder = tempfile.gettempdir()
    
    # Đảm bảo thư mục tồn tại
    if not os.path.exists(exchange_folder):
        os.makedirs(exchange_folder)
    
    # Thư mục trigger cho Blender
    blender_trigger_folder = os.path.join(exchange_folder, "blender_triggers")
    if not os.path.exists(blender_trigger_folder):
        os.makedirs(blender_trigger_folder)

    # Thư mục cho FBX
    fbx_folder = os.path.join(exchange_folder, "fbx")
    if not os.path.exists(fbx_folder):
        os.makedirs(fbx_folder)

    # Lấy đường dẫn tạm cho export
    current_time = time.strftime("%Y%m%d%H%M%S")
    
    # Lấy app và scene hiện tại
    mp = csc.app.get_application()
    scene_manager = mp.get_scene_manager()
    tools_manager = mp.get_tools_manager()
    
    # Export tất cả scene
    try:
        scenes = scene_manager.scenes()
        fbx_paths = []
        
        for i, s in enumerate(scenes):
            fbx_path = os.path.join(fbx_folder, f"cascadeur_to_blender_{current_time}_scene{i}.fbx")
            fbx_loader = tools_manager.get_tool("FbxSceneLoader").get_fbx_loader(s)
            fbx_loader.export_all_objects(fbx_path)
            fbx_paths.append(fbx_path)
            scene.info(f"Exported scene {i} to {fbx_path}")
        
        # Tạo trigger cho Blender
        trigger_data = {
            "action": "import_all_scenes",
            "data": {
                "fbx_paths": fbx_paths
            }
        }
        
        # Ghi file trigger
        trigger_path = os.path.join(blender_trigger_folder, f"trigger_import_all_scenes_{current_time}.json")
        with open(trigger_path, 'w') as f:
            json.dump(trigger_data, f, indent=2)
        
        scene.info(f"Created trigger for Blender at {trigger_path}")
    except Exception as e:
        scene.error(f"Failed to export all scenes: {str(e)}")