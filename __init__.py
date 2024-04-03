import bpy
import io

bl_info = {
    "name": "Voyage GLTF extension",
    "category": "Generic",
    "version": (1, 0, 0),
    "blender": (3, 4, 0),
    'location': 'File > Export > glTF 2.0',
    'description': 'Encode textures in GPU ready formats inside GLTF Binary files. Requires PIL.',
    'tracker_url': "https://github.com/voyage-vr/blender-glb-extension-gpu-formats",  # Replace with your issue tracker
    'isDraft': False,
    'developer': "Voyage Voyage", # Replace this
    'url': 'https://github.com/voyage-vr/blender-glb-extension-gpu-formats',  # Replace this
}

# glTF extensions are named following a convention with known prefixes.
# See: https://github.com/KhronosGroup/glTF/tree/main/extensions#about-gltf-extensions
# also: https://github.com/KhronosGroup/glTF/blob/main/extensions/Prefixes.md
glTF_extension_name = "EXT_voyage_exporter"

# Support for an extension is "required" if a typical glTF viewer cannot be expected
# to load a given model without understanding the contents of the extension.
# For example, a compression scheme or new image format (with no fallback included)
# would be "required", but physics metadata or app-specific settings could be optional.
extension_is_required = True

class ExampleExtensionProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name=bl_info["name"],
        description='Include this extension in the exported glTF file.',
        default=True
        )

def _install_wand() -> None:
    import ensurepip
    ensurepip.bootstrap()
    from pip import _internal
    _internal.main(['install', 'pip', 'setuptools', 'wheel', '-U', '--user'])
    _internal.main(['install', 'wand', '--user'])

def _install_wand_if_not_exist() -> None:
    try:
        from wand.image import Image
    except ImportError:
        _install_wand()

def register():
    _install_wand_if_not_exist()
    bpy.utils.register_class(ExampleExtensionProperties)
    bpy.types.Scene.ExampleExtensionProperties = bpy.props.PointerProperty(type=ExampleExtensionProperties)

def register_panel():
    # Register the panel on demand, we need to be sure to only register it once
    # This is necessary because the panel is a child of the extensions panel,
    # which may not be registered when we try to register this extension
    try:
        bpy.utils.register_class(GLTF_PT_UserExtensionPanel)
    except Exception:
        pass

    # If the glTF exporter is disabled, we need to unregister the extension panel
    # Just return a function to the exporter so it can unregister the panel
    return unregister_panel


def unregister_panel():
    # Since panel is registered on demand, it is possible it is not registered
    try:
        bpy.utils.unregister_class(GLTF_PT_UserExtensionPanel)
    except Exception:
        pass

def unregister():
    unregister_panel()
    bpy.utils.unregister_class(ExampleExtensionProperties)
    del bpy.types.Scene.ExampleExtensionProperties

class GLTF_PT_UserExtensionPanel(bpy.types.Panel):

    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Enabled"
    bl_parent_id = "GLTF_PT_export_user_extensions"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "EXPORT_SCENE_OT_gltf"

    def draw_header(self, context):
        props = bpy.context.scene.ExampleExtensionProperties
        self.layout.prop(props, 'enabled')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        props = bpy.context.scene.ExampleExtensionProperties
        layout.active = props.enabled

        box = layout.box()
        box.label(text=glTF_extension_name)


class glTF2ExportUserExtension:

    
    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        self.Extension = Extension
        self.properties = bpy.context.scene.ExampleExtensionProperties
        

    def gather_image_hook(self, gltf2_image, blender_shader_sockets, export_settings):
        print(f'Texture Name = {gltf2_image.name}')
        print(f'Texture URI = {gltf2_image.uri}')
        
        from wand.image import Image
        with Image(blob=gltf2_image.buffer_view.data) as img:
            img.format = "dds"
            img.compression = "dxt5"
            img.alpha_channel = True

            output = io.BytesIO()
            img.save(file=output)

            gltf2_image.buffer_view.data = output.getbuffer().tobytes()[128:]

            gltf2_image.mime_type = "image/dds"
            gltf2_image.extensions[glTF_extension_name] = self.Extension(
                name=glTF_extension_name,
                extension={"width": img.width, "height": img.height, "format": "DXT5"},
                required=True
            )

