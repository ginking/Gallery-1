

def shotwell_video_id_to_db_id(weird_id):
    # video-0000000000000013 -> base10 number
    return int("0x%s" % weird_id[6:], 16)

def db_id_to_shotwell_video_id(normal_id):
    # base10 number -> video-0000000000000013
    hex_id = hex(normal_id)[2:]
    return 'video-' + (16 - len(hex_id)) * '0' + hex_id
