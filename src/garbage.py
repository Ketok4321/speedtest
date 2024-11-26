import os
import io

UPLOAD_SIZE = 20

garbage = os.urandom(UPLOAD_SIZE * 1000 * 1000)

class GarbageReader(io.IOBase):
    def __init__(self, read_callback=None):
        self.__read_callback = read_callback
        super().__init__()
        self.length = len(garbage)
        self.pos = 0

    def seekable(self):
        return False

    def writable(self):
        return False

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def read(self, size=None):
        if not size:
            size = self.length - self.tell()

        old_pos = self.tell()
        self.pos = old_pos + size

        if self.__read_callback:
            self.__read_callback(size)

        return garbage[old_pos:self.pos]
