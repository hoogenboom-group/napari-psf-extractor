from qtpy.QtCore import QTimer


class StatusMessage:
    """
    A class to manage the status bar of the napari viewer.
    """
    def __init__(self, viewer):
        self.viewer = viewer
        self.timer = QTimer()
        self.frame = 0

    def start_loading_animation(self, message):
        """
        Start a loading animation that refreshes every 512 ms.
        """
        self.timer.start(512)
        self.timer.timeout.connect(lambda: self.render(message=message))

    def render(self, message=""):
        """
        Render a loading animation in the status bar.
        """
        text = "[  ]"
        text = message + text[:self.frame+1] + "=" + text[self.frame+1:]

        self.frame = (self.frame + 1) % 3
        self.viewer.status = text

    def stop_animation(self, message=""):
        self.viewer.status = message

        self.frame = 0
        self.timer.stop()
