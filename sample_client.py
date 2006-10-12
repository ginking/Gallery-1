import sys
import xmlrpclib

rpc_srv = xmlrpclib.ServerProxy("http://192.168.0.118:8000/gallery/xmlrpc/",
                                #verbose=1
                                )

#tags = rpc_srv.get_tags()
#print tags

print '-' * 80

photos = rpc_srv.get_photos_for_tag(18)
print photos
