import os
import json
import time
import threading
import bpy
from bpy.app.handlers import persistent
from . import file_utils
from . import preferences

class FileWatcher:
    """Theo dõi thư mục trao đổi file và xử lý khi có file mới."""
    
    def __init__(self, exchange_folder, callback):
        self.exchange_folder = exchange_folder
        self.callback = callback
        self.is_running = False
        self.thread = None
        self.processed_files = set()
        self.last_error_time = 0
    
    def start(self):
        """Khởi động thread theo dõi."""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_watcher)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Dừng thread theo dõi."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def _run_watcher(self):
        """Hàm chính để theo dõi thư mục."""
        if not os.path.exists(self.exchange_folder):
            try:
                os.makedirs(self.exchange_folder)
            except (OSError, PermissionError) as e:
                self._log_error(f"Failed to create exchange folder: {e}")
                return
        
        trigger_folder = os.path.join(self.exchange_folder, "blender_triggers")
        if not os.path.exists(trigger_folder):
            try:
                os.makedirs(trigger_folder)
            except (OSError, PermissionError) as e:
                self._log_error(f"Failed to create trigger folder: {e}")
                return
        
        print(f"Watching folder: {trigger_folder}")
        
        error_cooldown = 10  # seconds between error reports
        
        while self.is_running:
            try:
                self._check_for_triggers(trigger_folder)
                
                # Dọn dẹp các file cũ nếu cần
                try:
                    # Kiểm tra context có sẵn không
                    if hasattr(bpy, "context") and bpy.context:
                        prefs = preferences.get_preferences(bpy.context)
                        # Kiểm tra xem prefs có thuộc tính cleanup_interval không
                        if prefs and hasattr(prefs, "cleanup_interval"):
                            file_utils.cleanup_old_triggers(self.exchange_folder, prefs.cleanup_interval)
                        else:
                            # Fallback to default cleanup interval
                            file_utils.cleanup_old_triggers(self.exchange_folder, 24)
                    else:
                        # Fallback to default cleanup interval
                        file_utils.cleanup_old_triggers(self.exchange_folder, 24)
                except Exception as e:
                    # Only log cleanup errors occasionally to avoid spamming
                    current_time = time.time()
                    if current_time - self.last_error_time > error_cooldown:
                        self._log_error(f"Cleanup error: {e}")
                        self.last_error_time = current_time
                    
                    # Fallback to default cleanup interval
                    file_utils.cleanup_old_triggers(self.exchange_folder, 24)
                
                time.sleep(1.0)  # Kiểm tra mỗi giây
            except Exception as e:
                current_time = time.time()
                if current_time - self.last_error_time > error_cooldown:
                    self._log_error(f"File watcher error: {e}")
                    self.last_error_time = current_time
                time.sleep(5.0)  # Longer delay after error
    
    def _check_for_triggers(self, folder):
        """Kiểm tra và xử lý các file trigger."""
        if not os.path.exists(folder):
            return
        
        for filename in os.listdir(folder):
            if not filename.startswith("trigger_") or not filename.endswith(".json"):
                continue
            
            filepath = os.path.join(folder, filename)
            
            # Bỏ qua nếu đã xử lý
            if filepath in self.processed_files:
                continue
            
            # Kiểm tra xem file có đang được ghi không
            try:
                # Thử mở file với mode 'a+' để kiểm tra xem nó có bị lock không
                with open(filepath, 'a+') as f:
                    # Di chuyển con trỏ về đầu file
                    f.seek(0)
                    # Đọc file trigger
                    trigger_data = json.load(f)
                
                # Đánh dấu đã xử lý
                self.processed_files.add(filepath)
                
                # Gọi callback để xử lý
                if self.callback:
                    self.callback(trigger_data)
                
                # Đánh dấu file đã xử lý (đổi tên thay vì xóa)
                file_utils.mark_trigger_as_processed(filepath)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON in file {filepath}: {e}")
                # Đánh dấu file bị lỗi
                self.processed_files.add(filepath)
                file_utils.mark_trigger_as_processed(filepath)
            except (OSError, PermissionError) as e:
                # File đang được ghi, bỏ qua
                pass
            except Exception as e:
                print(f"Error processing trigger file {filepath}: {e}")
                # Đánh dấu file bị lỗi
                self.processed_files.add(filepath)
                file_utils.mark_trigger_as_processed(filepath)
    
    def _log_error(self, message):
        """Log một thông báo lỗi và hiển thị thông báo trong Blender nếu có thể."""
        print(f"FileWatcher Error: {message}")
        
        # Cố gắng hiển thị thông báo trong Blender UI nếu có thể
        try:
            def show_message():
                if hasattr(bpy.ops, "wm") and hasattr(bpy.ops.wm, "report_info"):
                    bpy.ops.wm.report_info({'ERROR'}, f"B2C FileWatcher: {message}")
                return None
            
            bpy.app.timers.register(show_message, first_interval=0.1)
        except:
            pass  # Bỏ qua nếu không thành công

# Timer handler để khởi động FileWatcher khi Blender bắt đầu
@persistent
def load_handler(dummy):
    """Handler được gọi khi Blender khởi động."""
    # Khởi động FileWatcher với addon preferences
    try:
        # Đảm bảo context đã sẵn sàng
        if not hasattr(bpy, "context") or not bpy.context:
            print("Context not ready, skipping file watcher initialization")
            return
            
        exchange_folder = preferences.get_exchange_folder(bpy.context)
        
        # Khởi động watcher với callback xử lý trigger
        watcher = FileWatcher(exchange_folder, process_trigger)
        watcher.start()
        
        # Lưu watcher vào WindowManager
        if not hasattr(bpy.types, "WindowManager"):
            print("WindowManager not found, skipping file watcher registration")
            return
            
        # Kiểm tra xem thuộc tính btc_file_watcher đã được đăng ký chưa
        if not hasattr(bpy.types.WindowManager, "btc_file_watcher"):
            # Add property dynamically
            bpy.types.WindowManager.btc_file_watcher = bpy.props.PointerProperty(
                type=bpy.types.PropertyGroup
            )
            
        # Store watcher reference - this is not a proper way to store Python objects,
        # but we're just using it as a temporary reference holder
        if hasattr(bpy.context, "window_manager"):
            bpy.context.window_manager["btc_file_watcher"] = watcher
        
        print("B2C File watcher started")
    except Exception as e:
        print(f"Error starting file watcher: {str(e)}")

def process_trigger(trigger_data):
    """Xử lý dữ liệu trigger từ Cascadeur."""
    # Safety check
    if not trigger_data or not isinstance(trigger_data, dict):
        print("Invalid trigger data received")
        return
        
    action = trigger_data.get("action")
    data = trigger_data.get("data", {})
    
    print(f"Received trigger: {action}")
    
    # Xử lý các hành động khác nhau - đảm bảo an toàn khi thêm vào hàng đợi
    if action == "import_scene":
        # Thêm vào hàng đợi xử lý của Blender
        try:
            bpy.app.timers.register(lambda: process_import_scene(data))
        except Exception as e:
            print(f"Error registering import_scene timer: {e}")
    elif action == "import_all_scenes":
        try:
            bpy.app.timers.register(lambda: process_import_all_scenes(data))
        except Exception as e:
            print(f"Error registering import_all_scenes timer: {e}")
    elif action == "clean_keyframes":
        try:
            bpy.app.timers.register(lambda: process_clean_keyframes(data))
        except Exception as e:
            print(f"Error registering clean_keyframes timer: {e}")
    else:
        print(f"Unknown action: {action}")

def process_import_scene(data):
    """Xử lý import scene từ Cascadeur."""
    fbx_path = data.get("fbx_path") if data else None
    if not fbx_path or not os.path.exists(fbx_path):
        print(f"FBX file not found: {fbx_path}")
        return None
    
    try:
        # Import FBX
        bpy.ops.import_scene.fbx(filepath=fbx_path)
        print(f"Imported scene from {fbx_path}")
        
        # Hiển thị thông báo thành công
        def show_message():
            if hasattr(bpy, "context") and bpy.context and hasattr(bpy.context, "window_manager"):
                bpy.context.window_manager.popup_menu(
                    lambda self, context: self.layout.label(text=f"Imported scene from Cascadeur"),
                    title="Import Successful", 
                    icon='INFO'
                )
            return None
        
        bpy.app.timers.register(show_message, first_interval=0.5)
    except Exception as e:
        print(f"Error importing scene: {e}")
        
        # Hiển thị thông báo lỗi
        def show_error():
            if hasattr(bpy, "context") and bpy.context and hasattr(bpy.context, "window_manager"):
                bpy.context.window_manager.popup_menu(
                    lambda self, context: self.layout.label(text=f"Error importing scene: {str(e)}"),
                    title="Import Failed", 
                    icon='ERROR'
                )
            return None
        
        bpy.app.timers.register(show_error, first_interval=0.5)
    
    return None  # Required for bpy.app.timers

def process_import_all_scenes(data):
    """Xử lý import tất cả scene từ Cascadeur."""
    fbx_paths = data.get("fbx_paths", []) if data else []
    
    if not fbx_paths:
        print("No FBX paths provided for import_all_scenes")
        return None
        
    success_count = 0
    error_count = 0
    
    # Import each FBX one by one
    for fbx_path in fbx_paths:
        if not os.path.exists(fbx_path):
            print(f"FBX file not found: {fbx_path}")
            error_count += 1
            continue
            
        try:
            bpy.ops.import_scene.fbx(filepath=fbx_path)
            print(f"Imported scene from {fbx_path}")
            success_count += 1
        except Exception as e:
            print(f"Error importing scene from {fbx_path}: {e}")
            error_count += 1
    
    # Display summary message
    def show_summary():
        message = f"Imported {success_count} scenes"
        if error_count > 0:
            message += f", {error_count} failed"
            
        if hasattr(bpy, "context") and bpy.context and hasattr(bpy.context, "window_manager"):
            bpy.context.window_manager.popup_menu(
                lambda self, context: self.layout.label(text=message),
                title="Import Summary", 
                icon='INFO' if error_count == 0 else 'ERROR'
            )
        return None
    
    if success_count > 0 or error_count > 0:
        bpy.app.timers.register(show_summary, first_interval=0.5)
    
    return None  # Required for bpy.app.timers

def process_clean_keyframes(data):
    """Xử lý clean keyframes dựa trên JSON từ Cascadeur."""
    if not data or not isinstance(data, dict):
        print("Invalid data for clean_keyframes")
        return None
        
    # Try to get keyframes from data
    keyframes_data = data.get("keyframes", {})
    
    if not keyframes_data:
        print("No keyframes data found")
        return None
    
    # Convert keyframe keys from strings to integers
    keyframes = {int(frame): value for frame, value in keyframes_data.items()}
    
    # Update UI keyframes list
    try:
        # Kiểm tra context có sẵn không
        if not hasattr(bpy, "context") or not bpy.context:
            print("Context not available for clean_keyframes")
            return None
            
        # Match keyframes in UI list
        scene = bpy.context.scene
        if hasattr(scene, "btc_keyframes"):
            # Mark keyframes that exist in the received data
            for item in scene.btc_keyframes:
                item.is_marked = item.frame in keyframes
            
            print(f"Updated {len(keyframes)} keyframes in UI")
            
            # Cập nhật timeline markers nếu cần thiết
            if hasattr(scene, "btc_show_markers") and scene.btc_show_markers:
                from . import timeline_utils
                timeline_utils.update_timeline_markers(scene)
            
            # Show notification
            def show_notification():
                if hasattr(bpy.context, "window_manager"):
                    bpy.context.window_manager.popup_menu(
                        lambda self, context: self.layout.label(text=f"Updated {len(keyframes)} keyframes from Cascadeur"),
                        title="Keyframes Updated", 
                        icon='INFO'
                    )
                return None
            
            bpy.app.timers.register(show_notification, first_interval=0.5)
    except Exception as e:
        print(f"Error processing keyframes: {e}")
    
    return None  # Required for bpy.app.timers