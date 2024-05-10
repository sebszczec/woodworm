import threading

class Timer:
    def __init__(self, timeout, callback, one_shot=True):
        self.timeout = timeout
        self.callback = callback
        self.one_shot = one_shot
        self.timer = None

    def start(self):
        if self.one_shot:
            self.timer = threading.Timer(self.timeout, self.callback)
            self.timer.start()
        else:
            self.timer = threading.Timer(self.timeout, self._repeat_callback)
            self.timer.start()

    def stop(self):
        if self.timer:
            self.timer.cancel()

    def _repeat_callback(self):
        self.callback()
        self.timer = threading.Timer(self.timeout, self._repeat_callback)
        self.timer.start()