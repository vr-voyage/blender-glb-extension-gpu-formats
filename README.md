## BETA STAGE ##

[demo-vrchat-blender.webm](https://github.com/user-attachments/assets/7937a0db-808a-4735-b7de-033ae9986b31)

An extension made to be export textures in GPU ready formats.
Used in conjunction with the VRChat GLB Loader I'm currently making.

Since I couldn't use PNG/JPEG formats in VRChat (no conversion methods
available at runtime), I made an extension to export textures in GPU
ready formats.

At the moment only DXT5 and BC7 (default) are supported.

This uses the following library : [Voyage Image Data Converter](https://github.com/vr-voyage/python-voyage-image-data-converter)

## Known issues

### Texture with sizes that are not multiple of 4 are not supported

This is a limitation of the format. Please ensure that the textures have the right size.  
A downscaler will be implemented afterwards.  
"Padding" the texture would only generate weird artefacts on the texture.