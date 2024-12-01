import bpy
from . import voyage_texture_converter

bl_info = {
    "name": "Voyage GLTF extension",
    "category": "Generic",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    'location': 'File > Export > glTF 2.0',
    'description': 'Encode textures in GPU ready formats inside GLTF Binary files.',
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
    
    export_as_dxt5: bpy.props.BoolProperty(
        name="Convert to DXT5 instead of BC7",
        description='For more compatibility but severe banding artefacts',
        default=False)

def register():
    bpy.utils.register_class(ExampleExtensionProperties)
    bpy.types.Scene.ExampleExtensionProperties = bpy.props.PointerProperty(type=ExampleExtensionProperties)

def unregister():
    bpy.utils.unregister_class(ExampleExtensionProperties)
    del bpy.types.Scene.ExampleExtensionProperties

def draw_export(context, layout):
    header, body = layout.panel("GLTF_addon_voyage_exporter", default_closed=False)
    header.use_property_split = False

    props = bpy.context.scene.ExampleExtensionProperties

    header.prop(props, 'enabled')
    if body != None:
        body.prop(props, 'export_as_dxt5', text="Choose DXT5 instead of BC7")

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
        print(self.properties.export_as_dxt5)

        width, height, converted_data = voyage_texture_converter.convert_image_content_in(
            gltf2_image.buffer_view.data,
            self.properties.export_as_dxt5)
        gltf2_image.buffer_view.data = converted_data

        gltf2_image.mime_type = "image/dds"
        gltf2_image.extensions[glTF_extension_name] = self.Extension(
            name=glTF_extension_name,
            extension={"width": width, "height": height, "format": "DXT5" if self.properties.export_as_dxt5 else "BC7" },
            required=True
        )

