class Event:
    def __init__(self):
        self._observers = []

    def subscribe(self, observer):
        self._observers.append(observer)

    def unsubscribe(self, observer):
        self._observers.remove(observer)

    async def notify(self, *args, **kwargs):
        for observer in self._observers:
            await observer(*args, **kwargs)

# Usage
# event = Event()

# def observer(*args, **kwargs):
#     print('Observer called with:', args, kwargs)

# event.subscribe(observer)
# event.notify('test', key='value')