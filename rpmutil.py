import struct
import sys
from rpm_extended_tags import RPM_TAGS

LEAD_SIZE = 96
LEAD_MAGIC = b'\xed\xab\xee\xdb'
HDR_MAGIC = b'\x8e\xad\xe8'
ALIGN = 8

# RPM tag types
RPM_NULL = 0
RPM_CHAR = 1
RPM_INT8 = 2
RPM_INT16 = 3
RPM_INT32 = 4
RPM_INT64 = 5
RPM_STRING = 6
RPM_BIN = 7
RPM_STRING_ARRAY = 8
RPM_I18NSTRING = 9

def align(offset, alignment=ALIGN):
    remainder = offset % alignment
    if remainder == 0:
        return offset
    return offset + (alignment - remainder)

def type_size(type_):
    if type_ in (RPM_NULL, RPM_CHAR, RPM_INT8):
        return 1
    elif type_ == RPM_INT16:
        return 2
    elif type_ == RPM_INT32:
        return 4
    elif type_ == RPM_INT64:
        return 8
    elif type_ in (RPM_STRING, RPM_BIN, RPM_STRING_ARRAY, RPM_I18NSTRING):
        return 1
    else:
        raise ValueError(f"Unknown RPM type {type_}")

def getstring(raw:bytes, ofs) -> tuple[str, int]:
    ends = ofs

    while raw[ends] != 0:
        ends = ends + 1

    return (raw[ofs:ends].decode(), ends+1)

def unpacktype(type):
    cases = {

    }


def decode_value(raw, fieldtype, offset, count):
    # NULL
    if fieldtype == RPM_NULL:
        return None

    # STRING (single null-terminated)
    elif fieldtype == RPM_STRING:
        return getstring(raw, offset)

    # STRING_ARRAY or I18NSTRING (multiple null-terminated)
    elif fieldtype in (RPM_STRING_ARRAY, RPM_I18NSTRING):
        strings = []
        pos = offset
        for _ in range(count):
            s, pos = getstring(raw, pos)
            strings.append(s)
        return strings

    # BIN (raw bytes)
    elif fieldtype == RPM_BIN:
        return raw[offset : offset + count]

    # Numeric types
    else:
        fmt_map = {
            RPM_CHAR: "b",
            RPM_INT8: "b",
            RPM_INT16: "h",
            RPM_INT32: "i",
            RPM_INT64: "q",
        }

        if fieldtype not in fmt_map:
            raise ValueError(f"Unsupported RPM type {fieldtype}")

        size = type_size(fieldtype)
        piece = raw[offset : offset + count * size]
        fmt = f">{count}{fmt_map[fieldtype]}"
        unpacked = struct.unpack(fmt, piece)

        return unpacked[0] if count == 1 else list(unpacked)


def read_header(f, section_name,align_after=True):
    header_raw = f.read(16)
    if len(header_raw) != 16:
        raise ValueError(f"[{section_name}] Could not read 16-byte header intro")

    magic = header_raw[0:3]
    version = header_raw[3]
    reserved = header_raw[4:8]
    index_count = struct.unpack(">I", header_raw[8:12])[0]
    data_size = struct.unpack(">I", header_raw[12:16])[0]

    if magic != HDR_MAGIC:
        raise ValueError(f"[{section_name}] Invalid magic {magic}")

    indexes = []

    needtags = False

    for _ in range(index_count):
        idx_raw = f.read(16)
        if len(idx_raw) != 16:
            raise ValueError(f"[{section_name}] Could not read full index entry")
        tag, tagtype, offset, count = struct.unpack(">IIII", idx_raw)

        if not tag in RPM_TAGS:
            print (f"tag: {tag} not found")
            needtags = True

        indexes.append({"tag": tag, "type": tagtype, "offset": offset, "count": count})

    if needtags:
        raise "There are missing rpm tags, see above."
    
    data_section = f.read(data_size)
    
    if len(data_section) != data_size:
        raise ValueError(f"[{section_name}] Could not read full data section")

    cur_pos = f.tell()

    if align_after:
        oldpos = cur_pos
        pos = align(cur_pos)
        f.seek(align(cur_pos))

    values = {}
    for idx in indexes:
        tag = idx["tag"]
        tagtype = idx["type"]
        offset = idx["offset"]
        count = idx["count"]

        if offset >= len(data_section):
            raise "Offset specified in indexes is large than data section specified."      

        # place the index values and attributes in the results
        values[tag] ={ 
                      'tagname':RPM_TAGS[tag],
                      'tag':tag,
                      'tagtype':tagtype, 
                      'offset':offset, 
                      'count':count,
                      'value': decode_value(data_section, tagtype, offset,count)
                      }

    return values

def extract_rpm_keywords_and_offset(rpm_path):
    with open(rpm_path, "rb") as f:
        leadbytes = f.read(LEAD_SIZE)
        magic = leadbytes[:4]

        if magic != LEAD_MAGIC:
            raise ValueError(f"Invalid RPM lead magic: {magic}")
        
        signature_values = read_header(f, "Signature Header")
        main_values = read_header(f, "Main Header",False)
        payload_offset = f.tell()
        
        compression_magics = {
            "gzip": b"\x1f\x8b",
            "xz": b"\xfd\x37\x7a\x58\x5a\x00",
            "zstd": b"\x28\xb5\x2f\xfd",
            "bzip2": b"\x42\x5a\x68",
            "lzma": b"\x5d\x00\x00",
        }

        longest = 0

        for comptype in compression_magics:
            if len(compression_magics[comptype]) > longest:
                longest = len(compression_magics[comptype])

        compmagicarray = f.read(longest)
        payloadcomptype = None

        for comptype in compression_magics:
            if compmagicarray.startswith(compression_magics[comptype]):
                payloadcomptype = comptype
                break
              
    return {"signature": signature_values, "main": main_values,'payload_offset': payload_offset, 'payload_compression_type': payloadcomptype}

if __name__ == "__main__":
    rpm_path = "dbeaver-ce-25.0.5-stable.x86_64.rpm"

    try:
        keywords = extract_rpm_keywords_and_offset(rpm_path)
        print(f"[+] Payload starts at byte offset: {keywords['payload_offset']}\n")
        print(f"[+] Payload compression type: {keywords['payload_compression_type']}")

        print("[+] Signature Header Keywords:")

        for k, v in keywords["signature"].items():
            print(f"{k}: {v['tagname']} contains {v['count']} items " )

        print("\n[+] Main Header Keywords:")
        for k, v in keywords["main"].items():
              print(f"{k}: {v['tagname']} contains {v['count']} items " )

    except Exception as e:
        print(f"[!] Error: {e}")
