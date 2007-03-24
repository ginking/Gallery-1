import sys
import xmlrpclib

rpc_srv = xmlrpclib.ServerProxy(sys.argv[1],
                                #verbose=1
                                )



#tags = rpc_srv.get_tags()
#print tags

print '-' * 80

photos = rpc_srv.get_photos_for_tag(25)
print photos

lieux = rpc_srv.get_sub_tags(4)
print lieux


categs = rpc_srv.get_root_categories()
print categs
