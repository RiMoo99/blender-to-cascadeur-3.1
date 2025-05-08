import os
import time
import tempfile
import shutil
import json
from datetime import datetime, timedelta

def ensure_dir_exists(directory):
    """Ensure directory exists, create if not."""
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def create_trigger_file(exchange_folder, action, data=None):
    """Create a trigger file to notify Cascadeur to perform an action."""
    ensure_dir_exists(exchange_folder)
    cascadeur_trigger_folder = os.path.join(exchange_folder, "cascadeur_triggers")
    ensure_dir_exists(cascadeur_trigger_folder)
    
    # Prepare data
    trigger_data = {
        "action": action,
        "timestamp": time.time(),
        "data": data or {}
    }
    
    # Create filename with timestamp to avoid conflicts
    timestamp = int(time.time())
    trigger_path = os.path.join(cascadeur_trigger_folder, f"trigger_{action}_{timestamp}.json")
    
    # Write trigger file
    try:
        with open(trigger_path, 'w') as f:
            json.dump(trigger_data, f, indent=2)
        return trigger_path
    except (IOError, PermissionError) as e:
        print(f"Error creating trigger file: {e}")
        return None

def copy_file_to_exchange(source_path, exchange_folder, subfolder=None):
    """Copy file to exchange directory."""
    ensure_dir_exists(exchange_folder)
    
    # Create subfolder if needed
    target_folder = exchange_folder
    if subfolder:
        target_folder = os.path.join(exchange_folder, subfolder)
        ensure_dir_exists(target_folder)
    
    # Get filename from source path
    filename = os.path.basename(source_path)
    target_path = os.path.join(target_folder, filename)
    
    # Copy file
    try:
        shutil.copy2(source_path, target_path)
        return target_path
    except (IOError, PermissionError) as e:
        print(f"Error copying file: {e}")
        return None

def get_export_path(file_type="fbx", use_temp=True, exchange_folder=None):
    """
    Create path for exporting files.
    
    Args:
        file_type: File type (fbx, json, ...)
        use_temp: Use temporary directory or not
        exchange_folder: Exchange directory (if not using temp)
    """
    current_time = time.strftime("%Y%m%d%H%M%S")
    filename = f"blender_to_cascadeur_{current_time}.{file_type}"
    
    if use_temp:
        temp_dir = tempfile.gettempdir()
        return os.path.join(temp_dir, filename)
    
    if exchange_folder:
        subfolder = file_type
        folder = os.path.join(exchange_folder, subfolder)
        ensure_dir_exists(folder)
        return os.path.join(folder, filename)
    
    # Fallback to temp dir if no exchange folder
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, filename)

def mark_trigger_as_processed(trigger_path):
    """Mark trigger file as processed by renaming it."""
    if os.path.exists(trigger_path):
        processed_path = trigger_path + ".processed"
        try:
            os.rename(trigger_path, processed_path)
            return processed_path
        except (IOError, PermissionError):
            # Fallback to removal if rename fails
            try:
                os.remove(trigger_path)
            except (IOError, PermissionError):
                pass
    return None

def cleanup_old_triggers(exchange_folder, hours=24):
    """Clean up old trigger files."""
    if not exchange_folder or not os.path.exists(exchange_folder):
        return
    
    # Calculate cutoff time
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    folders = [
        os.path.join(exchange_folder, "blender_triggers"),
        os.path.join(exchange_folder, "cascadeur_triggers")
    ]
    
    for folder in folders:
        if not os.path.exists(folder):
            continue
            
        for filename in os.listdir(folder):
            if filename.endswith(".json.processed"):
                filepath = os.path.join(folder, filename)
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_mtime < cutoff_time:
                        os.remove(filepath)
                except (OSError, IOError):
                    pass