from struct import pack


class Writer:
    def __init__(self):
        super(Writer, self).__init__()
        self.buffer = b''

    def writeUInt64(self, integer: int):
        self.buffer += pack('>Q', integer)

    def writeInt64(self, integer: int):
        self.buffer += pack('>q', integer)

    def writeUInt32(self, integer: int):
        self.buffer += pack('>I', integer)

    def writeInt32(self, integer: int):
        self.buffer += pack('>i', integer)

    def writeUInt16(self, integer: int):
        self.buffer += pack('>H', integer)

    def writeInt16(self, integer: int):
        self.buffer += pack('>h', integer)

    def writeUInt8(self, integer: int):
        self.buffer += pack('>B', integer)

    def writeInt8(self, integer: int):
        self.buffer += pack('>b', integer)

    writeULong = writeUInt64
    writeLong = writeInt64

    writeUShort = writeUInt16
    writeShort = writeInt16

    writeUByte = writeUInt8
    writeByte = writeInt8

    def writeString(self, string: str):
        encoded = string.encode('utf-8')
        self.writeUInt32(len(encoded))
        self.buffer += encoded
