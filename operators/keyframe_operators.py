import bpy
from bpy.types import Operator, PropertyGroup, UIList
from bpy.props import BoolProperty, IntProperty, StringProperty, EnumProperty
from ..utils import timeline_utils

# Define PropertyGroup for keyframe
class KeyframeItem(PropertyGroup):
    frame: IntProperty(name="Frame")
    is_marked: BoolProperty(
        name="Marked", 
        default=False,
        update=lambda self, context: timeline_utils.mark_update_callback(self, context)
    )

# Define PropertyGroup for filter
class KeyframeListFilter(PropertyGroup):
    filter_string: StringProperty(
        name="Search",
        description="Filter keyframes by frame number",
        default=""
    )
    filter_state: EnumProperty(
        name="Filter",
        description="Filter keyframes by state",
        items=[
            ('ALL', "All", "Show all keyframes"),
            ('MARKED', "Marked", "Show only marked keyframes"),
            ('UNMARKED', "Unmarked", "Show only unmarked keyframes")
        ],
        default='ALL'
    )

# Handle armature selection
class BTC_OT_PickArmature(Operator):
    bl_idname = "btc.pick_armature"
    bl_label = "Pick Armature"
    bl_description = "Select an armature from the scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'
    
    def execute(self, context):
        # Save current armature to scene
        context.scene.btc_armature = context.active_object
        self.report({'INFO'}, f"Selected armature: {context.active_object.name}")
        
        # Update keyframe list with new armature
        self.update_keyframe_list(context)
        
        return {'FINISHED'}
    
    def update_keyframe_list(self, context):
        # Clear old list
        context.scene.btc_keyframes.clear()
        
        # If no armature, return
        if not context.scene.btc_armature:
            return
            
        armature = context.scene.btc_armature
        
        # Find all keyframes from armature
        if armature.animation_data and armature.animation_data.action:
            keyframes = set()
            
            for fcurve in armature.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    # Add frame to set
                    frame = int(keyframe.co[0])
                    keyframes.add(frame)
            
            # Add keyframes to list
            for frame in sorted(list(keyframes)):
                item = context.scene.btc_keyframes.add()
                item.frame = frame
                item.is_marked = False  # Default is not marked

# Mark current keyframe
class BTC_OT_MarkCurrentKeyframe(Operator):
    bl_idname = "btc.mark_current_keyframe"
    bl_label = "Mark Current"
    bl_description = "Mark the current keyframe"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.btc_armature is not None
    
    def execute(self, context):
        current_frame = context.scene.frame_current
        
        # Check if keyframe exists in list
        for item in context.scene.btc_keyframes:
            if item.frame == current_frame:
                item.is_marked = True
                # Update timeline markers
                timeline_utils.update_timeline_markers(context.scene)
                self.report({'INFO'}, f"Marked keyframe at frame {current_frame}")
                return {'FINISHED'}
        
        # If keyframe doesn't exist, add to list
        item = context.scene.btc_keyframes.add()
        item.frame = current_frame
        item.is_marked = True
        
        # Update timeline markers
        timeline_utils.update_timeline_markers(context.scene)
        
        self.report({'INFO'}, f"Added and marked keyframe at frame {current_frame}")
        return {'FINISHED'}

# Clear current keyframe marking
class BTC_OT_ClearCurrentKeyframe(Operator):
    bl_idname = "btc.clear_current_keyframe"
    bl_label = "Clear Current"
    bl_description = "Clear the current keyframe"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.btc_armature is not None
    
    def execute(self, context):
        current_frame = context.scene.frame_current
        
        # Find and clear keyframe marking
        for item in context.scene.btc_keyframes:
            if item.frame == current_frame:
                item.is_marked = False
                # Update timeline markers
                timeline_utils.update_timeline_markers(context.scene)
                self.report({'INFO'}, f"Cleared keyframe at frame {current_frame}")
                return {'FINISHED'}
        
        self.report({'WARNING'}, f"No keyframe found at frame {current_frame}")
        return {'CANCELLED'}

# Mark all keyframes
class BTC_OT_MarkAllKeyframes(Operator):
    bl_idname = "btc.mark_all_keyframes"
    bl_label = "Mark All"
    bl_description = "Mark all keyframes"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.btc_armature is not None and len(context.scene.btc_keyframes) > 0
    
    def execute(self, context):
        count = 0
        for item in context.scene.btc_keyframes:
            if not item.is_marked:
                item.is_marked = True
                count += 1
        
        # Update timeline markers
        timeline_utils.update_timeline_markers(context.scene)
        
        self.report({'INFO'}, f"Marked {count} keyframes")
        return {'FINISHED'}

# Clear all keyframe markings
class BTC_OT_ClearAllKeyframes(Operator):
    bl_idname = "btc.clear_all_keyframes"
    bl_label = "Clear All"
    bl_description = "Clear all keyframes"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.btc_armature is not None and len(context.scene.btc_keyframes) > 0
    
    def execute(self, context):
        count = 0
        for item in context.scene.btc_keyframes:
            if item.is_marked:
                item.is_marked = False
                count += 1
        
        # Update timeline markers
        timeline_utils.update_timeline_markers(context.scene)
        
        self.report({'INFO'}, f"Cleared {count} keyframes")
        return {'FINISHED'}

# Toggle timeline markers
class BTC_OT_ToggleMarkers(Operator):
    bl_idname = "btc.toggle_markers"
    bl_label = "Toggle Timeline Markers"
    bl_description = "Show/hide markers on the timeline for marked keyframes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Check if property exists
        if not hasattr(context.scene, "btc_show_markers"):
            # Create property if it doesn't exist
            bpy.types.Scene.btc_show_markers = bpy.props.BoolProperty(
                name="Show Timeline Markers", 
                default=True
            )
            context.scene.btc_show_markers = True
        else:
            # Toggle the property
            context.scene.btc_show_markers = not context.scene.btc_show_markers
        
        # Update timeline markers
        timeline_utils.update_timeline_markers(context.scene)
        
        if context.scene.btc_show_markers:
            self.report({'INFO'}, "Timeline markers visible")
        else:
            self.report({'INFO'}, "Timeline markers hidden")
            
        return {'FINISHED'}

# Refresh keyframe list
class BTC_OT_RefreshKeyframeList(Operator):
    bl_idname = "btc.refresh_keyframe_list"
    bl_label = "Refresh"
    bl_description = "Refresh the keyframe list"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.btc_armature is not None
    
    def execute(self, context):
        # Store marked keyframes
        marked_frames = {}
        for item in context.scene.btc_keyframes:
            if item.is_marked:
                marked_frames[item.frame] = True
        
        # Update keyframe list
        armature = context.scene.btc_armature
        context.scene.btc_keyframes.clear()
        
        if armature and armature.animation_data and armature.animation_data.action:
            keyframes = set()
            
            for fcurve in armature.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    frame = int(keyframe.co[0])
                    keyframes.add(frame)
            
            # Add keyframes to list, restoring mark status
            for frame in sorted(list(keyframes)):
                item = context.scene.btc_keyframes.add()
                item.frame = frame
                item.is_marked = frame in marked_frames
        
        # Update timeline markers
        timeline_utils.update_timeline_markers(context.scene)
        
        self.report({'INFO'}, "Keyframe list refreshed")
        return {'FINISHED'}

# Add keyframe
class BTC_OT_KeyframeAdd(Operator):
    bl_idname = "btc.keyframe_add"
    bl_label = "Add Keyframe"
    bl_description = "Add current frame to keyframe list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        current_frame = context.scene.frame_current
        
        # Check if already exists
        for item in context.scene.btc_keyframes:
            if item.frame == current_frame:
                self.report({'INFO'}, f"Frame {current_frame} already in list")
                return {'CANCELLED'}
        
        # Add new keyframe
        item = context.scene.btc_keyframes.add()
        item.frame = current_frame
        item.is_marked = True
        
        # Update timeline markers
        timeline_utils.update_timeline_markers(context.scene)
        
        self.report({'INFO'}, f"Added keyframe at frame {current_frame}")
        return {'FINISHED'}

# Remove keyframe
class BTC_OT_KeyframeRemove(Operator):
    bl_idname = "btc.keyframe_remove"
    bl_label = "Remove Keyframe"
    bl_description = "Remove selected keyframe from list"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.scene.btc_keyframe_index >= 0 and
                context.scene.btc_keyframe_index < len(context.scene.btc_keyframes))
    
    def execute(self, context):
        idx = context.scene.btc_keyframe_index
        frame = context.scene.btc_keyframes[idx].frame
        
        # Remove keyframe
        context.scene.btc_keyframes.remove(idx)
        
        # Adjust index if needed
        if idx >= len(context.scene.btc_keyframes):
            context.scene.btc_keyframe_index = max(0, len(context.scene.btc_keyframes) - 1)
        
        # Update timeline markers
        timeline_utils.update_timeline_markers(context.scene)
        
        self.report({'INFO'}, f"Removed keyframe at frame {frame}")
        return {'FINISHED'}

# Move keyframe in list
class BTC_OT_KeyframeMove(Operator):
    bl_idname = "btc.keyframe_move"
    bl_label = "Move Keyframe"
    bl_description = "Move keyframe up or down in the list"
    bl_options = {'REGISTER', 'UNDO'}
    
    direction: StringProperty(
        name="Direction",
        default="UP"
    )
    
    @classmethod
    def poll(cls, context):
        return (context.scene.btc_keyframe_index >= 0 and
                context.scene.btc_keyframe_index < len(context.scene.btc_keyframes))
    
    def execute(self, context):
        idx = context.scene.btc_keyframe_index
        keyframes = context.scene.btc_keyframes
        
        if self.direction == "UP" and idx > 0:
            keyframes.move(idx, idx - 1)
            context.scene.btc_keyframe_index -= 1
            self.report({'INFO'}, "Moved keyframe up")
            return {'FINISHED'}
        elif self.direction == "DOWN" and idx < len(keyframes) - 1:
            keyframes.move(idx, idx + 1)
            context.scene.btc_keyframe_index += 1
            self.report({'INFO'}, "Moved keyframe down")
            return {'FINISHED'}
        
        return {'CANCELLED'}

# UI List with filtering capability
class BTC_UL_KeyframeList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            # Display frame number
            row.label(text=f"Frame: {item.frame}")
            
            # Add checkbox 
            checkbox_icon = 'CHECKBOX_HLT' if item.is_marked else 'CHECKBOX_DEHLT'
            row.prop(item, "is_marked", text="", icon=checkbox_icon, emboss=False)
            
            # Add jump to frame button
            op = row.operator("screen.frame_jump", text="", icon="TIME")
            op.end = False
        
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=str(item.frame))
    
    # Filtering function
    def filter_items(self, context, data, propname):
        # Get all items
        items = getattr(data, propname)
        
        # Get filter settings
        filter_name = context.scene.btc_filter.filter_string.lower()
        filter_state = context.scene.btc_filter.filter_state
        
        # Create flags list with default value of hidden (0)
        flags = [0] * len(items)
        
        # Filter by search string and mark state
        for i, item in enumerate(items):
            # Check search string - show if no search or frame starts with search
            search_ok = not filter_name or str(item.frame).startswith(filter_name)
            
            # Check mark state - show if ALL or matches filter
            state_ok = (filter_state == 'ALL') or \
                      (filter_state == 'MARKED' and item.is_marked) or \
                      (filter_state == 'UNMARKED' and not item.is_marked)
            
            # If both conditions met, show item
            if search_ok and state_ok:
                flags[i] |= self.bitflag_filter_item
        
        # Create ordering list
        ordering = []
        for i, item in enumerate(items):
            if flags[i] & self.bitflag_filter_item:
                ordering.append((i, item.frame))
        
        # Sort by frame number
        ordering.sort(key=lambda item: item[1])
        
        # Extract only the indices
        order = [x[0] for x in ordering]
        
        return flags, order

# List of classes to register
classes = [
    KeyframeItem,
    KeyframeListFilter,
    BTC_OT_PickArmature,
    BTC_OT_MarkCurrentKeyframe,
    BTC_OT_ClearCurrentKeyframe,
    BTC_OT_MarkAllKeyframes,
    BTC_OT_ClearAllKeyframes,
    BTC_OT_ToggleMarkers,
    BTC_OT_RefreshKeyframeList,
    BTC_OT_KeyframeAdd,
    BTC_OT_KeyframeRemove,
    BTC_OT_KeyframeMove,
    BTC_UL_KeyframeList,
]

# Đăng ký các lớp
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

# Hủy đăng ký các lớp
def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass