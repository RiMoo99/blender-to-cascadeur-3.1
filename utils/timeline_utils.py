import bpy

# Frame change handler to update timeline markers
@bpy.app.handlers.persistent
def frame_change_handler(scene):
    """Handler called on frame change"""
    # Only update if markers are enabled
    if hasattr(scene, "btc_show_markers") and scene.btc_show_markers:
        update_timeline_markers(scene)

def mark_update_callback(self, context):
    """Callback when a keyframe's marked status changes"""
    # Update timeline markers if enabled
    if hasattr(context.scene, "btc_show_markers") and context.scene.btc_show_markers:
        update_timeline_markers(context.scene)

def update_timeline_markers(scene):
    """Update timeline markers based on marked keyframes"""
    # Ensure property exists
    if not hasattr(scene, "btc_show_markers"):
        bpy.types.Scene.btc_show_markers = bpy.props.BoolProperty(
            name="Show Timeline Markers", 
            default=True
        )
        scene.btc_show_markers = True
    
    # Check if markers should be shown
    if not scene.btc_show_markers:
        # Remove all B2C markers
        for marker in list(scene.timeline_markers):
            if marker.name.startswith("Key:"):
                scene.timeline_markers.remove(marker)
        return
    
    # Get list of marked frames
    marked_frames = get_marked_frames(scene)
    
    # First remove old markers
    for marker in list(scene.timeline_markers):
        if marker.name.startswith("Key:"):
            scene.timeline_markers.remove(marker)
    
    # Create new markers for each marked frame
    for frame in marked_frames:
        # Create marker with frame number as name
        marker = scene.timeline_markers.new(f"Key:{frame}", frame=frame)
        # Set marker color (green)
        marker.color = (0.2, 0.8, 0.2)

def get_marked_frames(scene):
    """Get list of marked frames"""
    marked_frames = []
    
    if hasattr(scene, "btc_keyframes"):
        for item in scene.btc_keyframes:
            if item.is_marked:
                marked_frames.append(item.frame)
    
    return marked_frames

def is_auto_rig_pro_armature(armature):
    """Check if armature is an Auto-Rig Pro rig"""
    if not armature or armature.type != 'ARMATURE':
        return False
    
    # Method 1: Check name pattern
    if armature.name.endswith("_rig") or armature.name.startswith("rig_") or "auto_rig" in armature.name.lower():
        return True
    
    # Method 2: Check custom properties
    for prop in ["arp_rig_type", "arp_rig", "auto_rig"]:
        if prop in armature:
            return True
    
    # Method 3: Check bone structure
    if armature.data and armature.data.bones:
        arp_bone_names = ["c_root", "c_pos", "c_traj", "root.x", "root"]
        for name in arp_bone_names:
            if name in armature.data.bones:
                return True
    
    return False