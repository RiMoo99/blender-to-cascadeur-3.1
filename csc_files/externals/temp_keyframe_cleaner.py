import csc
import os
import json
import time
import tempfile
import configparser


def command_name():
    return "B2C.Temp Keyframe Cleaner"


def run(scene):
    # Đọc cấu hình
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.cfg")
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
    trigger_folder = os.path.join(exchange_folder, "cascadeur_triggers")
    if not os.path.exists(trigger_folder):
        os.makedirs(trigger_folder)
        scene.info("Created triggers folder: " + trigger_folder)
        return

    # Tìm trigger file mới nhất
    newest_trigger = None
    newest_time = 0
    
    for filename in os.listdir(trigger_folder):
        if filename.startswith("trigger_clean_keyframes_") and filename.endswith(".json"):
            filepath = os.path.join(trigger_folder, filename)
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
            
            # Lấy dữ liệu keyframe
            data = trigger_data.get("data", {})
            keyframes = data.get("keyframes", {})
            
            # Chuyển đổi các key từ string về integer
            marked_frames = [int(frame) for frame in keyframes.keys()]
            
            if not marked_frames:
                scene.error("No marked keyframes received")
                return
            
            # Thông báo số lượng keyframe được đánh dấu
            scene.info(f"Received {len(marked_frames)} marked keyframes: {', '.join(str(f) for f in sorted(marked_frames)[:10])}{', ...' if len(marked_frames) > 10 else ''}")
            
            # Xử lý keyframe
            removed_count = keep_only_marked_keyframes(scene, marked_frames)
            scene.info(f"Keyframe cleaning completed. Removed {removed_count} keyframes. Kept {len(marked_frames)} marked keyframes.")
            
        except Exception as e:
            scene.error(f"Error processing trigger file: {str(e)}")
    else:
        scene.info("No new trigger files found.")


def keep_only_marked_keyframes(scene, marked_frames):
    """Xóa tất cả keyframe không được đánh dấu trong các layer"""
    lv = scene.layers_viewer()
    removed_count = 0
    
    def mod(model, update, scene):
        nonlocal removed_count
        le = model.layers_editor()
        all_layer_ids = lv.all_layer_ids()
        
        for layer_id in all_layer_ids:
            # Lấy frames_count để biết số lượng frame tối đa
            max_frame = lv.frames_count([layer_id])
            
            # Xóa các frame không nằm trong danh sách đánh dấu
            for frame in range(0, max_frame + 1):
                if frame not in marked_frames:
                    try:
                        # Chỉ xóa khi frame không nằm trong danh sách đánh dấu
                        le.unset_section(frame, layer_id)
                        removed_count += 1
                    except Exception as e:
                        # Bỏ qua lỗi - có thể frame không có section
                        pass
    
    scene.modify('Keep only marked keyframes', mod)
    return removed_count