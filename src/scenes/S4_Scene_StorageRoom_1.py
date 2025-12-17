from scenes.video_scene_base import VideoScene

class Scene4(VideoScene):
    def __init__(self, manager, screen_size):
        super().__init__(manager, screen_size,
            video_name="Scene2.mp4",
            next_scene="scene_5"
        )
