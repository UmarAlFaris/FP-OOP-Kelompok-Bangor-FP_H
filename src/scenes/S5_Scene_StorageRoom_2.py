from scenes.video_scene_base import VideoScene

class Scene5(VideoScene):
    def __init__(self, manager, screen_size):
        super().__init__(manager, screen_size,
            video_name="Scene5.mp4",
            next_scene="scene_6"
        )
