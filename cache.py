from collections import OrderedDict


class Cache(OrderedDict):

    def __init__(self, size):
        super().__init__()
        self.size = size

    def __setitem__(self, key, value):
        if len(self) >= self.size:
            self.popitem(last=False)
        return super().__setitem__(key, value)

    def __str__(self):
        return f'Cache({self.items()})'
