import subprocess
import platform
import os
import bpy

def file_exists(file_path):
    """Check if a file exists."""
    return os.path.exists(file_path)

def get_default_csc_exe_path():
    """
    Returns the default Cascadeur executable path based on the operating system.
    """
    system = platform.system()
    
    paths = []
    if system == "Windows":
        paths = [
            r"C:\Program Files\Cascadeur\cascadeur.exe",
            r"C:\Program Files (x86)\Cascadeur\cascadeur.exe"
        ]
    elif system == "Darwin":  # macOS
        paths = [
            r"/Applications/Cascadeur.app",
            r"~/Applications/Cascadeur.app"
        ]
    elif system == "Linux":
        paths = [
            r"/opt/cascadeur/cascadeur",
            r"~/cascadeur/cascadeur"
        ]
    
    for path in paths:
        expanded_path = os.path.expanduser(path)
        if file_exists(expanded_path):
            return expanded_path
    
    return ""

class CascadeurHandler:
    @property
    def csc_exe_path_addon_preference(self):
        """
        Get the set Cascadeur executable path from the addon's preferences.
        """
        try:
            preferences = bpy.context.preferences
            addon_prefs = preferences.addons[__package__.split(".")[0]].preferences
            return addon_prefs.csc_exe_path
        except (AttributeError, KeyError):
            return ""

    @property
    def csc_dir(self):
        """
        Get the root directory of Cascadeur installation.
        """
        if self.is_csc_exe_path_valid:
            return os.path.dirname(self.csc_exe_path_addon_preference)
        return None

    @property
    def is_csc_exe_path_valid(self):
        """
        Check if the Cascadeur executable path is valid.
        """
        csc_path = self.csc_exe_path_addon_preference
        return bool(csc_path and file_exists(csc_path))

    @property
    def commands_path(self):
        """
        Get the path to the Cascadeur commands directory.
        """
        if not self.csc_dir:
            return None
            
        if platform.system() == "Darwin":  # macOS
            resources_dir = os.path.join(self.csc_dir, "Contents", "MacOS", "resources")
        else:
            resources_dir = os.path.join(self.csc_dir, "resources")
        
        return os.path.join(resources_dir, "scripts", "python", "commands")

    def start_cascadeur(self):
        """
        Start Cascadeur using the specified executable path.
        """
        if not self.is_csc_exe_path_valid:
            raise FileNotFoundError("Cascadeur executable not found")
            
        try:
            subprocess.Popen([self.csc_exe_path_addon_preference])
            return True
        except (subprocess.SubprocessError, OSError) as e:
            print(f"Error starting Cascadeur: {e}")
            return False

    def execute_csc_command(self, command):
        """
        Execute a Cascadeur command using the specified executable path.
        """
        if not self.is_csc_exe_path_valid:
            raise FileNotFoundError("Cascadeur executable not found")
            
        try:
            subprocess.Popen([self.csc_exe_path_addon_preference, "--run-script", command])
            return True
        except (subprocess.SubprocessError, OSError) as e:
            print(f"Error executing Cascadeur command: {e}")
            return False