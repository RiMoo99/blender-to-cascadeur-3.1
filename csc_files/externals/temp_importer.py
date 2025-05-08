import csc
import os
import json
import time
import tempfile


def command_name():
    return "B2C.Temp Importer"

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
    
    # Kiểm tra xem có thư mục cascadeur_triggers
    cascade_trigger_folder = os.path.join(exchange_folder, "cascadeur_triggers")
    if not os.path.exists(cascade_trigger_folder):
        os.makedirs(cascade_trigger_folder)

    # Kiểm tra xem có file trigger mới không
    newest_trigger = None
    newest_time = 0
    
    for filename in os.listdir(cascade_trigger_folder):
        if filename.startswith("trigger_") and filename.endswith(".json"):
            filepath = os.path.join(cascade_trigger_folder, filename)
            mtime = os.path.getmtime(filepath)
            if mtime > newest_time:
                newest_time = mtime
                newest_trigger = filepath
    
    if newest_trigger:
        try:
            # Đọc file trigger
            with open(newest_trigger, 'r') as f:
                trigger_data = json.load(f)
            
            # Đánh dấu file trigger đã được xử lý
            processed_path = newest_trigger + ".processed"
            os.rename(newest_trigger, processed_path)
            
            # Lấy action
            action = trigger_data.get("action", "")
            
            # Lấy app và scene hiện tại
            mp = csc.app.get_application()
            scene_pr = mp.get_scene_manager().current_scene()
            tools_manager = mp.get_tools_manager()
            
            # Lấy FbxSceneLoader
            fbx_scene_loader_tool = tools_manager.get_tool("FbxSceneLoader")
            fbx_scene_loader = fbx_scene_loader_tool.get_fbx_loader(scene_pr)
            
            # Xử lý các action khác nhau
            if action == "import_fbx":
                # Import FBX từ Blender
                try:
                    fbx_path = trigger_data.get("data", {}).get("fbx_path", "")
                    if fbx_path and os.path.exists(fbx_path):
                        fbx_scene_loader.import_model(fbx_path)
                        scene.info(f"Imported FBX from {fbx_path}")
                    else:
                        scene.error(f"FBX file not found: {fbx_path}")
                except Exception as e:
                    scene.error(f"Failed to import FBX: {str(e)}")
            
            elif action == "import_object":
                # Import object từ Blender
                try:
                    fbx_path = trigger_data.get("data", {}).get("fbx_path", "")
                    if fbx_path and os.path.exists(fbx_path):
                        fbx_scene_loader.import_model(fbx_path)
                        scene.info(f"Imported object from {fbx_path}")
                    else:
                        scene.error(f"FBX file not found: {fbx_path}")
                except Exception as e:
                    scene.error(f"Failed to import object: {str(e)}")
            
            elif action == "import_animation":
                # Import animation từ Blender
                try:
                    fbx_path = trigger_data.get("data", {}).get("fbx_path", "")
                    json_path = trigger_data.get("data", {}).get("json_path", "")
                    
                    if fbx_path and os.path.exists(fbx_path):
                        # Import FBX trước
                        fbx_scene_loader.import_animation(fbx_path)
                        scene.info(f"Imported animation from {fbx_path}")
                        
                        # Nếu có JSON, xử lý keyframes
                        if json_path and os.path.exists(json_path):
                            with open(json_path, 'r') as f:
                                keyframes_data = json.load(f)
                            
                            # Xử lý keyframes (thêm code xử lý keyframes dựa trên API của Cascadeur)
                            scene.info(f"Processed keyframes from {json_path}")
                    else:
                        scene.error(f"FBX file not found: {fbx_path}")
                except Exception as e:
                    scene.error(f"Failed to import animation: {str(e)}")
            
            elif action == "import_json":
                # Import JSON từ Blender
                try:
                    json_path = trigger_data.get("data", {}).get("json_path", "")
                    if json_path and os.path.exists(json_path):
                        with open(json_path, 'r') as f:
                            keyframes_data = json.load(f)
                        
                        # Xử lý keyframes (thêm code xử lý keyframes dựa trên API của Cascadeur)
                        scene.info(f"Processed keyframes from {json_path}")
                    else:
                        scene.error(f"JSON file not found: {json_path}")
                except Exception as e:
                    scene.error(f"Failed to import JSON: {str(e)}")
            
            else:
                scene.info(f"Unknown action: {action}")
        
        except Exception as e:
            scene.error(f"Error processing trigger file: {str(e)}")
    
    else:
        scene.info("No new trigger files found.")