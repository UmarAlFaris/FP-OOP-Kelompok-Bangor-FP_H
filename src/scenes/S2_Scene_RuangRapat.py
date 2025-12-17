from scenes.video_scene_base import VideoScene

class Scene2(VideoScene):
    def __init__(self, manager, screen_size):
        super().__init__(manager, screen_size,
            video_name="replacable_cut_scene.png",
            next_scene="scene_3"
        )
