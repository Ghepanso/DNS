import io


def parse_address(data):
    if type(data) == bytearray:
        data = io.BytesIO(data)
    name = bytearray()
    while True:
        n = data.read(1)[0]
        if n & 0xC0:
            m = data.read(1)[0]
            offset = ((n & 0x3F) << 8) | m
            current_offset = data.tell()
            data.seek(offset)
            sub_name = parse_address(data)
            data.seek(current_offset)
            name.extend(sub_name)
            return name
        if not n:
            break
        name.extend(data.read(n))
        name.extend(b'.')
    return name

def pack_address(data):
    result = bytearray()
    sub_names = data.split('.')
    for sub_name in sub_names:
        result.append(len(sub_name))
        result.extend(sub_name.encode())
    return result
