from typing import List, Literal, Union

from pydantic import BaseModel, Field

from runner.live.pipelines import BaseParams


class WeightedPrompt(BaseModel):
    """Configuration for a single prompt with weight."""

    text: str
    weight: int = 100


class ScopeParams(BaseParams):
    """
    Scope pipeline parameters for longlive text-to-video generation.
    """

    pipeline: Literal["longlive", "krea_realtime_video", "streamdiffusionv2", "reward_forcing", "memflow"] = "krea_realtime_video"
    """The scope pipeline to use. Supported: 'longlive', 'krea_realtime_video', 'streamdiffusionv2', 'reward_forcing', 'memflow'."""

    prompts: List[Union[str, WeightedPrompt]] = Field(
        default_factory=lambda: [
            WeightedPrompt(
                text="A 3D animated scene. A **panda** walks along a path towards the camera in a park on a spring day.",
                weight=100,
            )
        ]
    )
    """List of prompts with weights for generation."""

    seed: int = 42
    """Random seed for reproducible generation."""

