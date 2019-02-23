# Response types
GG_WELCOME = 0x0001
GG_LOGIN80_OK = 0x0035
GG_LOGIN_FAILED = 0x0009
GG_NOTIFY_REPLY80 = 0x0037
GG_STATUS80 = 0x0036
GG_RECV_MSG80 = 0x002e
GG_RECV_MSG = 0x000a
GG_PONG = 0x0007
GG_DISCONNECTING = 0x000b

# Request types
GG_LOGIN80 = 0x0031
GG_NEW_STATUS80 = 0x0038
GG_NOTIFY_FIRST = 0x000f
GG_NOTIFY_LAST = 0x0010
GG_SEND_MSG80 = 0x002d
GG_PING = 0x0008
GG_ADD_NOTIFY = 0x000d
GG_REMOVE_NOTIFY = 0x000e
GG_LIST_EMPTY = 0x0012


# Structs
class PacketBuffer:
    def __init__(self, data):
        self.__data = data
        self.setup()

    def setup(self):
        pass

    def _skip(self, length):
        self.__data = self.__data[length:]

    def _read(self, length):
        data = self.__data[:length]
        self._skip(length)
        return data

    def _read_int8(self):
        data = self._read(1)
        return int.from_bytes(data, "little")

    def _read_int16(self):
        data = self._read(2)
        return int.from_bytes(data, "little")

    def _read_int32(self):
        data = self._read(4)
        return int.from_bytes(data, "little")

    def _read_string(self, length, encoding="utf-8"):
        data = self._read(length).strip()
        return data.decode(encoding)


class gg_login80(PacketBuffer):
    def __init__(self, data):
        self.uin = 0
        self.language = ""
        self.hash_type = 0x00
        self.hash = bytes()
        self.status = 0
        self.flags = 0
        self.features = 0
        self.local_ip = 0
        self.local_port = 0
        self.external_ip = 0
        self.external_port = 0
        self.image_size = 0x00
        self.unknown1 = 0x64
        self.version_len = 0
        self.version = ""
        self.description_size = 0
        self.description = ""
        super().__init__(data)

    def setup(self):
        self.uin = self._read_int32()
        self.language = self._read_string(2)
        self.hash_type = self._read_int8()
        self.hash = self._read(64)
        self.status = self._read_int32()
        self.flags = self._read_int32()
        self.features = self._read_int32()
        self.local_ip = self._read_int32()
        self.local_port = self._read_int16()
        self.external_ip = self._read_int32()
        self.external_port = self._read_int16()
        self.image_size = self._read_int8()
        self._skip(1)
        self.version_len = self._read_int32()
        self.version = self._read_string(self.version_len)
        self.description_size = self._read_int32()
        self.description = self._read_string(self.description_size, "ISO-8859-2")


class gg_new_status80(PacketBuffer):
    def __init__(self, data):
        self.status = 0
        self.flags = 0
        self.description_size = 0
        self.description = ""
        super().__init__(data)

    def setup(self):
        self.status = self._read_int32()
        self.flags = self._read_int32()
        self.description_size = self._read_int32()
        self.description = self._read_string(self.description_size, "ISO-8859-2")


class gg_notify(PacketBuffer):
    def __init__(self, data):
        self.uin = 0
        self.type = 0x00
        super().__init__(data)

    def setup(self):
        self.uin = self._read_int32()
        self.type = self._read_int8()


class gg_send_msg80(PacketBuffer):
    def __init__(self, data):
        self.recipient = 0
        self.seq = 0
        self.cls = 0
        self.offset_plain = 0
        self.offset_attributes = 0
        self.html_message = ""
        self.plain_message = ""
        self.attributes = ""
        super().__init__(data)

    def setup(self):
        self.recipient = self._read_int32()
        self.seq = self._read_int32()
        self.cls = self._read_int32()
        self.offset_plain = self._read_int32()
        self.offset_attributes = self._read_int32()
        self.html_message = self._read_string(self.offset_plain - 20)
        self.plain_message = self._read_string(self.offset_attributes - self.offset_plain, "ISO-8859-2")
        self.attributes = self._read_string(None)
