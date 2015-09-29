# -*- coding: utf-8 -*-

__author__ = "Ildar Nikolaev"
__email__ = "nildar@users.sourceforge.net"

import bpy
import nodeitems_utils
from bpy.props import BoolProperty

from . import ArnoldRenderEngine


@ArnoldRenderEngine.register_class
class ArnoldNodeOutput(bpy.types.Node):
    bl_label = "Output"
    bl_icon = 'MATERIAL'

    def _get_active(self):
        return not self.mute

    def _set_active(self, value=True):
        for node in self.id_data.nodes:
            if type(node) is ArnoldNodeOutput:
                node.mute = (self != node)

    is_active = BoolProperty(
        name="Active",
        description="Active Output",
        get=_get_active,
        set=_set_active
    )

    def init(self, context):
        self._set_active()
        sock = self.inputs.new("NodeSocketShader", "Shader")

    def draw_buttons(self, context, layout):
        layout.prop(self, "is_active", icon='RADIOBUT_ON' if self.is_active else 'RADIOBUT_OFF')


class ArnoldNode:
    @property
    def ai_properties(self):
        return {}


@ArnoldRenderEngine.register_class
class ArnoldNodeLambert(bpy.types.Node, ArnoldNode):
    bl_label = "Lambert"
    bl_icon = 'MATERIAL'

    AI_NAME = "lambert"

    def init(self, context):
        sock = self.inputs.new("NodeSocketFloat", "Kd")
        sock.default_value = 0.7
        sock = self.inputs.new("NodeSocketColor", "Kd_color")
        sock.default_value = (1, 1, 1, 1)
        sock = self.inputs.new("NodeSocketColor", "Opacity", "opacity")
        sock.default_value = (1, 1, 1, 1)

        self.outputs.new("NodeSocketShader", "Output", "output")


@ArnoldRenderEngine.register_class
class ArnoldNodeImage(bpy.types.Node, ArnoldNode):
    bl_label = "Image"
    bl_icon = 'IMAGEFILE'

    AI_NAME = "image"

    texture = bpy.props.StringProperty(
        name="Texture"
    )

    def init(self, context):
        self.outputs.new("NodeSocketColor", "RGBA", "output")

    def draw_buttons(self, context, layout):
        layout.prop_search(self, "texture", context.blend_data, "textures", text="")

    @property
    def ai_properties(self):
        return {
            "filename": ('TEXTURE', self.texture)
        }


@ArnoldRenderEngine.register_class
class ArnoldNodeMixRGB(bpy.types.Node, ArnoldNode):
    bl_label = "Mix RGB"
    bl_icon = 'MATERIAL'

    AI_NAME = "BArnoldMixRGB"

    blend_type = bpy.props.EnumProperty(
        name="Blend Type",
        items=[
            ('mix', "Mix", "Mix"),
            ('add', "Add", "Add"),
            ('multiply', "Multiply", "Multiply"),
            ('screen', "Screen", "Screen"),
            ('overlay', "Overlay", "Overlay"),
            ('subtract', "Subtract", "Subtract"),
            ('divide', "Divide", "Divide"),
            ('difference', "Difference", "Difference"),
            ('darken', "Darken", "Darken Only"),
            ('lighten', "Lighten", "Lighten Only"),
            ('dodge', "Dodge", "Dodge"),
            ('burn', "Burn", "Burn"),
            ('hue', "Hue", "Hue"),
            ('saturation', "Saturation", "Saturation"),
            ('value', "Value", "Value"),
            ('color', "Color", "Color"),
            ('soft', "Soft Light", "Soft Light"),
            ('linear', "Linear Light", "Linear Light")
        ],
        default='mix'
    )

    def init(self, context):
        sock = self.inputs.new("NodeSocketColor", "Color1", "color1")
        sock.default_value = (0.8, 0.8, 0.8, 1)
        sock = self.inputs.new("NodeSocketColor", "Color2", "color2")
        sock.default_value = (0.8, 0.8, 0.8, 1)
        sock = self.inputs.new("NodeSocketFloat", "Factor", "factor")
        sock.default_value = 0.5

        self.outputs.new("NodeSocketColor", "Color", "output")

    def draw_buttons(self, context, layout):
        layout.prop(self, "blend_type", text="")

    @property
    def ai_properties(self):
        return {
            "blend": ('STRING', self.blend_type)
        }


class ArnoldNodeCategory(nodeitems_utils.NodeCategory):
    @classmethod
    def poll(cls, context):
        return (
            ArnoldRenderEngine.is_active(context) and
            context.space_data.tree_type == 'ShaderNodeTree'
        )


def register():
    from nodeitems_builtins import ShaderNewNodeCategory, ShaderOldNodeCategory

    # HACK: hide BI and Cycles nodes from 'Add' menu in Node editor
    def _poll(fn):
        @classmethod
        def _fn(cls, context):
            return (
                not ArnoldRenderEngine.is_active(context) and
                fn(context)
            )
        return _fn

    ShaderNewNodeCategory.poll = _poll(ShaderNewNodeCategory.poll)
    ShaderOldNodeCategory.poll = _poll(ShaderOldNodeCategory.poll)

    node_categories = [
        ArnoldNodeCategory("ARNOLD_OUTPUT_NODES", "Output", items=[
            nodeitems_utils.NodeItem("ArnoldNodeOutput")
        ]),
        ArnoldNodeCategory("ARNOLD_SHADERS_NODES", "Shaders", items=[
            nodeitems_utils.NodeItem("ArnoldNodeLambert"),
            nodeitems_utils.NodeItem("ArnoldNodeImage")
        ]),
        ArnoldNodeCategory("ARNOLD_COLOR_NODES", "Color", items=[
            nodeitems_utils.NodeItem("ArnoldNodeMixRGB")
        ]),
    ]
    nodeitems_utils.register_node_categories("ARNOLD_NODES", node_categories)


def unregister():
    nodeitems_utils.unregister_node_categories("ARNOLD_NODES")