import pickle
import random
import socket
import threading

from main import DnsCache
from packet import DNSPacket, DNSQuestion
from tools import parse_address

TIMEOUT = 25
GOOGLE_DNS = '8.8.8.8'


def rand_id():
    return random.randint(0, 0xffff)


class DnsServer(threading.Thread):
    def __init__(self):
        super().__init__(name='Server')
        self.forwarder = GOOGLE_DNS
        self.cache = DnsCache()

        self.serve_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serve_socket.settimeout(TIMEOUT)
        self.serve_socket.bind(('127.0.0.1', 53))

        self.running = False
        self.forwarding = True

    def run(self):
        self.running = True
        while self.running:
            try:
                data, address = self.serve_socket.recvfrom(1024)
            except socket.error:
                continue
            print(' <-- {}'.format(address))
            threading.Thread(target=self.serve_client, args=(address, data)).start()

    def stop(self):
        self.serve_socket.close()


    def save_cache(self, save_file_name):
        # self.cache.update()
        if len(self.cache.cache) != 0:
            with open(save_file_name, 'wb') as file:
                pickle.dump(self.cache, file)

    def get_from_forwarder(self, question):
        if not self.forwarding:
            return []  # TODO: check if eryn' ok

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(TIMEOUT)
        request = DNSPacket(rand_id(), 0x0100, [question], [], [], [])
        sock.sendto(request.pack(), (self.forwarder, 53))

        try:
            data, _ = sock.recvfrom(1024)
        except socket.error as e:
            return []

        response = DNSPacket.unpack(data)
        for category in (response.answer, response.authority, response.additional):
            for resource in category:
                self.cache.put_resource(resource)

        return self.get_from_cache(question)

    def get_from_cache(self, question):
        c_name_question = DNSQuestion(
            question.q_name, 5, question.q_class)
        c_name_resources = self.cache.get_resources(c_name_question)
        for c_name_resource in c_name_resources:
            canonical_name = parse_address(c_name_resource.r_data).decode()
            result = self.get_from_cache(DNSQuestion(canonical_name, question.q_type, question.q_class))
            if result:
                result.append(c_name_resource)
                return result
        return self.cache.get_resources(question)

    def serve_client(self, address, raw_packet):
        packet = DNSPacket.unpack(raw_packet)
        response = DNSPacket(
            packet.packet_id, 0x8000,
            packet.question, [], [], []
        )
        for question in packet.question:
            resources = self.get_from_cache(question)
            q_str = question.to_string()
            if resources:
                print(f'--> from cache: {q_str}')
            else:
                print(f'--> from forwarder: {q_str}')
                resources = self.get_from_forwarder(question)
            response.answer.extend(resources)
        raw_response = response.pack()
        self.serve_socket.sendto(raw_response, address)

