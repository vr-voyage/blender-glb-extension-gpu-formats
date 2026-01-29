import bpy
from . import voyage_texture_converter

bl_info = {
    "name": "Voyage GLTF extension",
    "category": "Generic",
    "version": (1, 0, 2),
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

class VoyageGltfExtensionProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name=bl_info["name"],
        description='Include this extension in the exported glTF file.',
        default=True
        )
    
    compression_format: bpy.props.EnumProperty(
        name="Compression Format",
        description="Select a GPU friendly compression format",
        items=[
            ('DXT5', "DXT5", "Popular format, Adreno compatible, known as BC3"),
            ('BC7', "BC7", "Best compression format but PC only"),
            ('RGBA8', "RGBA8", "Literally zero compression. Avoid this one"),
        ],
        default='BC7')

def is_blender_4_3_or_lower() -> bool:
    [blender_major_version, blender_minor_version, _] = bpy.app.version

    if blender_major_version < 4:
        return True
    
    if blender_major_version == 4 and blender_minor_version <= 3:
        return True

def register():
    bpy.utils.register_class(VoyageGltfExtensionProperties)
    bpy.types.Scene.VoyageGltfExtensionProperties = bpy.props.PointerProperty(type=VoyageGltfExtensionProperties)
    if is_blender_4_3_or_lower():
        return

    from io_scene_gltf2 import exporter_extension_layout_draw
    exporter_extension_layout_draw[bl_info["name"]] = draw_export

def unregister():
    bpy.utils.unregister_class(VoyageGltfExtensionProperties)
    del bpy.types.Scene.VoyageGltfExtensionProperties

    if is_blender_4_3_or_lower():
        return

    from io_scene_gltf2 import exporter_extension_layout_draw
    del exporter_extension_layout_draw[bl_info["name"]]

def draw_export(context, layout):
    header, body = layout.panel("GLTF_addon_voyage_exporter", default_closed=False)
    header.use_property_split = False

    props = bpy.context.scene.VoyageGltfExtensionProperties

    header.prop(props, 'enabled')
    if body != None:
        body.prop(props, 'compression_format', text="Compression format")

class glTF2ExportUserExtension:
    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        self.Extension = Extension
        self.properties = bpy.context.scene.VoyageGltfExtensionProperties
        
    def gather_image_hook(self, *args):
        gltf2_image = args[0]

        print(f'Texture Name = {gltf2_image.name}')
        print(f'Texture URI = {gltf2_image.uri}')
        print(self.properties.compression_format)

        width, height, converted_data, compression_format = voyage_texture_converter.convert_image_content_in(
            gltf2_image.buffer_view.data,
            self.properties.compression_format)
        gltf2_image.buffer_view.data = converted_data

        gltf2_image.mime_type = "image/dds"
        gltf2_image.extensions[glTF_extension_name] = self.Extension(
            name=glTF_extension_name,
            extension={"width": width, "height": height, "format": self.properties.compression_format },
            required=True
        )

