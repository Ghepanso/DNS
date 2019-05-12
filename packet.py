import struct
import io

from tools import parse_address, pack_address

HEADER_FORMAT = '>HHHHHH'
CODES = {
    1: 'A',
    2: 'NS',
    5: 'CNAME',
    6: 'SOA',
    12: 'PTR',
    15: 'MX',
    28: 'AAAA'
}

# def parse_address(data):
#     if type(data) == bytearray:
#         data = io.BytesIO(data)
#     name = bytearray()
#     while True:
#         n = data.read(1)[0]
#         if n & 0xC0:
#             m = data.read(1)[0]
#             offset = ((n & 0x3F) << 8) | m
#             current_offset = data.tell()
#             data.seek(offset)
#             sub_name = parse_address(data)
#             data.seek(current_offset)
#             name.extend(sub_name)
#             return name
#         if not n:  # ery'n' readed?
#             break
#         name.extend(data.read(n))
#         name.extend(b'.')
#     return name
#
# def pack_address(data):
#     result = bytearray()
#     sub_names = data.split('.')
#     for sub_name in sub_names:
#         result.append(len(sub_name))
#         result.extend(sub_name.encode())
#     return result

def unpack_rr_data(r_type, r_len, data):
    if r_type in [2, 5]:
        return pack_address(parse_address(data).decode())
    return data.read(r_len)


class DNSPacket:
    def __init__(self, packet_id, flags, question, answer, authority, additional):
        self.packet_id = packet_id
        self.flags = flags
        self.question = question
        self.answer = answer
        self.authority = authority
        self.additional = additional


    @staticmethod
    def unpack(data):
        stream = io.BytesIO(data)
        header = struct.unpack(HEADER_FORMAT, stream.read(12))
        packet_id, flags = header[:2]
        questions = [DNSQuestion.unpack(stream) for _ in range(header[2])]
        answers, authority, additional = \
            [[DNSResource.unpack(stream) for _ in range(count)] for count in header[3:]]
        return DNSPacket(packet_id, flags, questions, answers, authority, additional)

    def pack(self):
        header = struct.pack(
            HEADER_FORMAT, self.packet_id, self.flags,
            len(self.question), len(self.answer),
            len(self.authority), len(self.additional)
        )
        result = bytearray()
        # result = bytearray(header)
        result.extend(header)

        for category in (self.question, self.answer, self.authority, self.additional):
            for resource in category:
                result.extend(resource.pack())
        #
        # for question in self.question:
        #     result.extend(question.pack())
        # for answer in self.answer:
        #     result.extend(answer.pack())
        # for authority in self.authority:
        #     result.extend(authority.pack())
        # for additional in self.additional:
        #     result.extend(additional.pack())
        return result


class DNSQuestion:
    def __init__(self, q_name, q_type, q_class):
        self.q_name = q_name
        self.q_type = q_type
        self.q_class = q_class

    @staticmethod
    def unpack(data):
        q_name = parse_address(data).decode()
        q_type, q_class = struct.unpack('>HH', data.read(4))
        return DNSQuestion(q_name, q_type, q_class)

    def pack(self):
        result = bytearray()
        result.extend(pack_address(self.q_name))
        result.extend(struct.pack('>HH', self.q_type, self.q_class))
        return result

    def is_true_resource(self, resource):
        return (self.q_name == resource.r_name
                and self.q_type == resource.r_type
                and self.q_class == resource.r_class)

    def __eq__(self, other):
        if type(other) == DNSQuestion:
            return (self.q_name == other.q_name
                    and self.q_type == other.q_type
                    and self.q_class == other.q_class)
        return False

    def to_string(self):
        fmt = '{:20s} {:04X} {:04X}'
        return fmt.format(self.q_name, self.q_type, self.q_class)


class DNSResource:
    def __init__(self, r_name, r_type, r_class, r_ttl, r_data):
        self.r_name = r_name
        self.r_type = r_type
        self.r_class = r_class
        self.r_ttl = r_ttl
        self.r_len = len(r_data)
        self.r_data = r_data

    def pack(self):
        result = bytearray()
        result.extend(pack_address(self.r_name))
        result.extend(struct.pack('>HHIH', self.r_type, self.r_class, self.r_ttl, self.r_len))
        result.extend(self.r_data)
        return result

    @staticmethod
    def unpack(data):
        r_name = parse_address(data).decode()
        r_type, r_class, r_ttl, r_len = struct.unpack('>HHIH', data.read(10))
        r_data = unpack_rr_data(r_type, r_len, data)
        return DNSResource(r_name, r_type, r_class, r_ttl, r_data)

    def __eq__(self, other):
        if type(other) == DNSResource:
            return (self.r_name == other.r_name
                    and self.r_type == other.r_type
                    and self.r_class == other.r_class
                    and self.r_data == other.r_data)
        return False

    def to_string(self):
        fmt = '{:20s} {} {:04X} {} {}'
        t = self.r_type
        if self.r_type in CODES:
            t = CODES[self.r_type]
        return fmt.format(self.r_name, t, self.r_class, self.r_ttl, self.r_data)

