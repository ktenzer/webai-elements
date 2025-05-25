from uuid import UUID

from webai_element_sdk.comms.messages import Frame
from webai_element_sdk.element import Context, Element
from webai_element_sdk.element.variables import Input, ElementInputs
from webai_element_sdk.comms.messages import Frame
from webai_element_sdk.element.settings import (
    BoolSetting,
    ElementSettings,
    NumberSetting,
    TextSetting,
    equals,
)

class Inputs(ElementInputs):
    """
    Each input can be either a single frame or a stream of frames.
    Inputs are how your element receives data from other elements.
    """
    input = Input[Frame]()


class Settings(ElementSettings):
    """
    Settings allow users to configure your element's behavior.
    You can create Text, Number, or Boolean settings with validation rules.
    """
    # Text Setting
    text_setting = TextSetting(
        name="hellowolrd",
        display_name="HelloWorld",
        default="HelloWorld"
    )

    # Number Setting
    number_setting = NumberSetting[int](
        name="number",
        display_name="A Number",
        description="This is a number",
        default=10,
        min_value=1,
        step=1,
    )

    # Bool Setting
    bool_setting = BoolSetting(
        name="bool_setting",
        display_name="A Dropdown Toggle",
        default=True,
        description="Whether Dropdown should be displayed",
        required=False,
    )

    # Dropdown Text Setting
    dropdown_setting = TextSetting(
        name="dropdown_setting",
        display_name="Dropdown Setting",
        default="item1",
        description="An Item",
        valid_values=[
            "item1",
            "item2",
            "item3",
        ],
        hints=["dropdown"],
        required=False,
        depends_on=equals("bool_setting", True),
    )

    # Folder Setting    
    folder_setting = TextSetting(
        name="folder_setting",
        display_name="A Folder Path",
        description="A folder location",
        default="",
        required=True,
        hints=["folder_path"],
    )

element: Element = Element(
    id=UUID("c382bdae-6680-4c64-a647-4b89fcba860b"),
    name="helloworld",
    display_name="helloworld",
    description="",
    version="0.1.6",
    settings=Settings(),
    inputs=Inputs(),
)


@element.startup
async def startup(ctx: Context[Inputs, None, Settings]):
    # Called when the element starts up.
    # Use this to initialize any resources your element needs.
    # This is a good place to set up connections, load models, or prepare data.

    print("***** HelloWorld Element Startup *****")


@element.shutdown
async def shutdown(ctx: Context[Inputs, None, Settings]):
    # Called when the element shuts down.
    # Use this to clean up any resources your element created.
    # This is a good place to close connections, save state, or clean up.

    print("***** HelloWorld Element Shutdown *****")


@element.executor
async def run(ctx: Context[Inputs, None, Settings]):
    # Main execution function that processes inputs and produces outputs.
    # Implement your element's core functionality here.
    input_frame = ctx.inputs.input.value

    print(f"Settings: {ctx.settings.text_setting} {ctx.settings.number_setting} {ctx.settings.bool_setting} {ctx.settings.dropdown_setting} {ctx.settings.folder_setting}")
    
    print(f"Frame: {input_frame.frame_id} {input_frame.headers} {input_frame.content_type} {input_frame.as_text} {input_frame.ndframe} {input_frame.other_data}")

    