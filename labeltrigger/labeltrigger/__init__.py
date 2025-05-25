from typing import AsyncIterator
from uuid import UUID

from webai_element_sdk.comms.messages import Frame
from webai_element_sdk.element import Context, Element
from webai_element_sdk.element.variables import ElementOutputs, Output, Input, ElementInputs
from webai_element_sdk.element.settings import (
    ElementSettings,
    TextSetting,
    NumberSetting,
    BoolSetting
)

from datetime import datetime

last_empty:   datetime | None = None
last_present: datetime | None = None 
triggered = False
THRESHOLD_SEC = 10                     

class Inputs(ElementInputs):
    input = Input[Frame]()


class Outputs(ElementOutputs):
    output = Output[Frame]()


class Settings(ElementSettings):
    label = TextSetting(
        name="label",
        display_name="Classification Label",
        default="person"
    )

    present = BoolSetting(
        name="present",
        display_name="Label is present",
        default=True,
    )

    repeat = BoolSetting(
        name="repeat",
        display_name="Repeat trigger ever X seconds",
        default=True,
    )

    trigger_seconds = NumberSetting[int](
        name="seconds",
        display_name="Seconds",
        description="Time to wait before firing",
        default=10,
        min_value=1,
        step=1,
    )

element: Element = Element(
    id=UUID("d92c7fca-d087-46b2-ac5a-3887221be247"),
    name="labeltrigger",
    display_name="label_trigger",
    description="",
    version="0.1.4",
    settings=Settings(),
    inputs=Inputs(),
    outputs=Outputs(),
)

def build_output(ctx: Context[Inputs, Outputs, Settings], msg: str) -> Output[Frame]:
    """Return an Output[Frame] carrying `msg` in other_data."""
    return ctx.outputs.output(
        Frame(
            ndframe=None,
            rois=[],
            frame_id=None,
            headers=None,
            other_data={"message": msg},
        )
    )

@element.startup
async def startup(ctx: Context[Inputs, Outputs, Settings]):
    print("**************Startup*******************")


@element.shutdown
async def shutdown(ctx: Context[Inputs, Outputs, Settings]):
    print("**************Shutdown*******************")


last_empty = None

@element.executor
async def run(ctx: Context[Inputs, Outputs, Settings]) -> AsyncIterator[Output[Frame]]:
    global last_empty, last_present, triggered
    now   = datetime.now()
    frame = ctx.inputs.input.value

    # Determine if frame matches label
    is_empty = True
    for roi in frame.rois:
        for cls in roi.classes:
            if cls.label == ctx.settings.label.value:
                is_empty = False
                break
        if not is_empty:
            break

    # Update timer
    if is_empty:
        last_present = None 

        # Transitioned to empty
        if last_empty is None: 
            last_empty = now
            if ctx.settings.present.value:
                triggered = False
    else:
        last_empty = None
        # Transitioned to present              
        if last_present is None:
            last_present = now
            if not ctx.settings.present.value:
                triggered = False

    if ctx.settings.present.value:
        if last_present is not None:
            elapsed = (now - last_present).total_seconds()
            if elapsed >= THRESHOLD_SEC:
                msg = f"Person detected after {elapsed:.0f}s absence"
                last_present = None       
                
                if ctx.settings.repeat.value:
                    print("📢", msg)
                    yield build_output(ctx, msg)
                else:
                    if not triggered:
                        print("📢", msg)
                        triggered = True
                        yield build_output(ctx, msg)              
    else:  
        if last_empty is not None:
            elapsed = (now - last_empty).total_seconds()
            if elapsed >= THRESHOLD_SEC:
                msg = f"Person missing for {elapsed:.0f}s"
                last_empty = None  

                if ctx.settings.repeat.value:
                    print("📢", msg)
                    yield build_output(ctx, msg)
                else:
                    if not triggered:
                        print("📢", msg)
                        triggered = True
                        yield build_output(ctx, msg)