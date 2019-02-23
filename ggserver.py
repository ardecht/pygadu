from logger import create_logger
from socketserver import ThreadingTCPServer, BaseRequestHandler
import libgadu
import struct
import hashlib
import time
from database import Database
import traceback
import random

logger = create_logger("GGServer")
client_list = []


class ResponsePacket:
    def __init__(self, packet_type):
        self.packet_type = packet_type
        self.packet_body = bytes()

    def write_int8(self, data):
        self.packet_body += data.to_bytes(1, byteorder="little")

    def write_int16(self, data):
        self.packet_body += data.to_bytes(2, byteorder="little")

    def write_int32(self, data):
        self.packet_body += data.to_bytes(4, byteorder="little")

    def write_string(self, data, encoding="utf-8"):
        self.packet_body += bytes(data, encoding)

    def get_bytes(self):
        return self.packet_type.to_bytes(4, byteorder="little") + \
               len(self.packet_body).to_bytes(4, byteorder="little") + \
               self.packet_body


class Client:
    def __init__(self, handler):
        self.handler = handler
        self.database = Database()
        self.client_seed = random.randint(1000, 9999)  # Random seed
        self.is_logged = False
        self.uin = 0
        self.status = 0
        self.description = ""
        self.buddies = []

        self.send_hello()

    def send_hello(self):
        hello_packet = ResponsePacket(libgadu.GG_WELCOME)
        hello_packet.write_int32(self.client_seed)  # Seed
        self.handler.send(hello_packet)

    def authorize(self, data):
        login_struct = libgadu.gg_login80(data)

        if not login_struct.version.startswith("Gadu-Gadu Client build 8.0.0"):
            return False

        user = self.database.find_user(login_struct.uin)

        if user is not None:
            (id, uin, password, status, description) = user
            crypto = hashlib.sha1()
            crypto.update(bytes(password, "utf-8"))
            crypto.update(int(self.client_seed).to_bytes(4, byteorder="little"))
            crypto_pass = crypto.digest()

            if crypto_pass == login_struct.hash[:len(crypto_pass)]:
                self.uin = login_struct.uin
                self.status = login_struct.status
                self.description = login_struct.description
                self.is_logged = True

                self.database.update_user_status(self.uin, self.status, self.description)

                self.send_my_change_status_to_my_buddies()
                return True

        return False

    def change_status(self, data):
        status_struct = libgadu.gg_new_status80(data)

        if status_struct.status == 0x0001 or status_struct.status == 0x4015:
            self.send_disconnect()

        self.status = status_struct.status
        self.description = status_struct.description

        self.database.update_user_status(self.uin, self.status, self.description)

        self.send_my_change_status_to_my_buddies()

    def send_my_change_status_to_my_buddies(self):
        change_status_packet = ResponsePacket(libgadu.GG_STATUS80)
        change_status_packet.write_int32(self.uin)
        change_status_packet.write_int32(self.status)
        change_status_packet.write_int32(0)
        change_status_packet.write_int32(0)
        change_status_packet.write_int16(0)
        change_status_packet.write_int8(0x00)
        change_status_packet.write_int8(0x00)
        change_status_packet.write_int32(0)
        change_status_packet.write_int32(len(self.description))
        change_status_packet.write_string(self.description, "ISO-8859-2")

        for client in client_list:
            if client.is_logged and 0 < client.uin != self.uin and self.uin in client.buddies:
                client.handler.send(change_status_packet)

    def store_my_buddies(self, data):
        for buddy in [data[i:i+5] for i in range(0, len(data), 5)]:
            buddy_struct = libgadu.gg_notify(buddy)
            self.buddies.append(buddy_struct.uin)

    def remove_my_buddies(self, data):
        for buddy in [data[i:i+5] for i in range(0, len(data), 5)]:
            buddy_struct = libgadu.gg_notify(buddy)
            self.buddies.remove(buddy_struct.uin)

    def check_my_buddies_status(self):
        buddies_result_packet = ResponsePacket(libgadu.GG_NOTIFY_REPLY80)
        found_buddies_count = 0

        found_buddies = []

        for buddy in self.buddies:
            for client in client_list:
                if client.is_logged and 0 < client.uin == buddy:
                    found_buddies_count += 1
                    buddies_result_packet.write_int32(client.uin)
                    buddies_result_packet.write_int32(client.status)
                    buddies_result_packet.write_int32(0)
                    buddies_result_packet.write_int32(0)
                    buddies_result_packet.write_int16(0)
                    buddies_result_packet.write_int8(0x00)
                    buddies_result_packet.write_int8(0x00)
                    buddies_result_packet.write_int32(0)
                    buddies_result_packet.write_int32(len(client.description))
                    buddies_result_packet.write_string(client.description, "ISO-8859-2")
                    found_buddies.append(client.uin)

        no_active_buddies = set(self.buddies) - set(found_buddies)

        for no_active_buddy in no_active_buddies:
            no_active_buddy_db = self.database.find_user(no_active_buddy)

            if no_active_buddy_db is not None:
                (id, uin, password, status, description) = no_active_buddy_db
                found_buddies_count += 1
                buddies_result_packet.write_int32(uin)
                buddies_result_packet.write_int32(status)
                buddies_result_packet.write_int32(0)
                buddies_result_packet.write_int32(0)
                buddies_result_packet.write_int16(0)
                buddies_result_packet.write_int8(0x00)
                buddies_result_packet.write_int8(0x00)
                buddies_result_packet.write_int32(0)
                if not description:
                    buddies_result_packet.write_int32(0)
                else:
                    buddies_result_packet.write_int32(len(description))
                    buddies_result_packet.write_string(description, "ISO-8859-2")

        if found_buddies_count > 0:
            self.handler.send(buddies_result_packet)

    def send_msg_to_client(self, data):
        my_msg_packet = libgadu.gg_send_msg80(data)

        for client in client_list:
            if client.is_logged and client.uin > 0 and client.uin == my_msg_packet.recipient:
                recv_msg_packet = ResponsePacket(libgadu.GG_RECV_MSG)
                recv_msg_packet.write_int32(self.uin)
                recv_msg_packet.write_int32(my_msg_packet.seq)
                recv_msg_packet.write_int32(int(time.time()))
                recv_msg_packet.write_int32(my_msg_packet.cls)
                recv_msg_packet.write_string(my_msg_packet.plain_message, "ISO-8859-2")
                client.handler.send(recv_msg_packet)

                logger.info("[SEND] [GG_RECV_MSG] {}".format(client.handler.client_address))
                return

        self.database.add_user_message_to_queue(self.uin, my_msg_packet.recipient, my_msg_packet.plain_message)

    def send_disconnect(self):
        disconnect_packet = ResponsePacket(libgadu.GG_DISCONNECTING)
        self.handler.send(disconnect_packet)
        self.handler.closed = True

    def send_client_queued_messages(self):
        queued_messages = self.database.find_and_delete_user_queued_messages(self.uin)

        for queued_message in queued_messages:
            (sender, recipient, message) = queued_message
            recv_msg_packet = ResponsePacket(libgadu.GG_RECV_MSG)
            recv_msg_packet.write_int32(sender)
            recv_msg_packet.write_int32(123)
            recv_msg_packet.write_int32(int(time.time()))
            recv_msg_packet.write_int32(0x0001)
            recv_msg_packet.write_string(message, "ISO-8859-2")
            self.handler.send(recv_msg_packet)

            logger.info("[SEND] [GG_RECV_MSG] {}".format(self.handler.client_address))

    def handle(self, packet_type, packet_size, data):
        if not self.is_logged:
            if packet_type == libgadu.GG_LOGIN80:
                logger.info("[RECV] [GG_LOGIN80] {}".format(self.handler.client_address))

                if self.authorize(data):
                    login_result_packet = ResponsePacket(libgadu.GG_LOGIN80_OK)
                    login_result_packet.write_int32(1)
                    self.handler.send(login_result_packet)

                    logger.info("[SEND] [GG_LOGIN80] Success {}".format(self.handler.client_address))

                    self.send_client_queued_messages()
                else:
                    login_result_packet = ResponsePacket(libgadu.GG_LOGIN_FAILED)
                    login_result_packet.write_int32(1)
                    self.handler.send(login_result_packet)

                    self.is_logged = False
                    logger.error("[SEND] [GG_LOGIN80] Failed {}".format(self.handler.client_address))
                    self.send_disconnect()
            else:
                logger.error("[RECV] Invalid packed {} (size: {}) from {}".format(hex(packet_type), packet_size, self.handler.client_address))
        else:
            if packet_type == libgadu.GG_NEW_STATUS80:
                logger.info("[RECV] [GG_NEW_STATUS80] {}".format(self.handler.client_address))
                self.change_status(data)

            elif packet_type == libgadu.GG_NOTIFY_FIRST or packet_type == libgadu.GG_NOTIFY_LAST:
                logger.info("[RECV] [GG_NOTIFY_FIRST/GG_NOTIFY_LAST] {}".format(self.handler.client_address))
                self.store_my_buddies(data)

                if packet_type == libgadu.GG_NOTIFY_LAST:
                    self.check_my_buddies_status()

            elif packet_type == libgadu.GG_LIST_EMPTY:
                logger.info("[RECV] [GG_LIST_EMPTY] {}".format(self.handler.client_address))

            elif packet_type == libgadu.GG_SEND_MSG80:
                logger.info("[RECV] [GG_SEND_MSG80] {}".format(self.handler.client_address))
                self.send_msg_to_client(data)

            elif packet_type == libgadu.GG_PING:
                logger.info("[RECV] [GG_PING] {}".format(self.handler.client_address))

            elif packet_type == libgadu.GG_ADD_NOTIFY:
                logger.info("[RECV] [GG_ADD_NOTIFY] {}".format(self.handler.client_address))
                self.store_my_buddies(data)
                self.check_my_buddies_status()

            elif packet_type == libgadu.GG_REMOVE_NOTIFY:
                logger.info("[RECV] [GG_REMOVE_NOTIFY] {}".format(self.handler.client_address))
                self.remove_my_buddies(data)
                self.check_my_buddies_status()

            else:
                logger.error("[RECV] Invalid packed {} (size: {}) from {}".format(hex(packet_type), packet_size, self.handler.client_address))


class ClientHandler(BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.closed = False
        super().__init__(request, client_address, server)

    def handle(self):
        logger.info("New client connected {}".format(self.client_address))

        client = Client(self)

        try:
            client_list.append(client)
        except Exception as e:
            logger.error("Can not add client to client list! {}".format(e))

        while not self.closed:
            try:
                data = self.request.recv(1024)  # Maybe try read more?

                if not data:  # Catch eof
                    break

                # Parse data
                (packet_type, packet_size) = struct.unpack("<ii", data[:8])
                packet_body = data[8:]

                if packet_size == len(packet_body):
                    client.handle(packet_type, packet_size, packet_body)
                else:
                    raise Exception("Invalid packet length! Packet size should be {} but is {}".format(packet_size, len(packet_body)))
            except Exception as e:
                logger.error("Client exception! {}".format(e))
                traceback.print_tb(e.__traceback__)
                break

        try:
            client_list.remove(client)
        except Exception as e:
            logger.error("Can not remove client from client list! {}".format(e))

        logger.info("Client disconnected connected {}".format(self.client_address))

    def send(self, data):
        if isinstance(data, ResponsePacket):
            data = data.get_bytes()

        self.request.send(data)


class GGServer:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.server = ThreadingTCPServer((self.addr, self.port), ClientHandler)
        pass

    def listen(self):
        try:
            logger.info("Server is listening at {}:{}".format(self.addr, self.port))
            self.server.serve_forever()
            logger.error("Server stopped.")
        except Exception as e:
            logger.critical("GG server exception! {}".format(e))
