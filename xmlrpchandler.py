# Patchless XMLRPC Service for Django
# Kind of hacky, and stolen from Crast on irc.freenode.net:#django
# Self documents as well, so if you call it from outside of an XML-RPC Client
# it tells you about itself and its methods
#
# Brendan W. McAdams <brendan.mcadams@thewintergrp.com>

# SimpleXMLRPCDispatcher lets us register xml-rpc calls w/o
# running a full XMLRPC Server.  It's up to us to dispatch data

from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from django.http import HttpResponse
from xmlrpc import exported_functions
import xmlrpc

# Create a Dispatcher; this handles the calls and translates info to
# function maps
dispatcher = SimpleXMLRPCDispatcher()


def rpc_handler(request):
    """
    the actual handler:
    if you setup your urls.py properly, all calls to the xml-rpc service
    should be routed through here.
    If post data is defined, it assumes it's XML-RPC and tries to process as such
    Empty post assumes you're viewing from a browser and tells you about the service.
    """

    response = HttpResponse()
    if request.POST:
        response.write(dispatcher._marshaled_dispatch(request.raw_post_data))
    else:
        response.write("<b>This is an XML-RPC Service.</b><br>")
        response.write("You need to invoke it using an XML-RPC Client!<br>")
        response.write("The following methods are available:<ul>")
        methods = dispatcher.system_listMethods()

        for method in methods:
            # right now, my version of SimpleXMLRPCDispatcher always
            # returns "signatures not supported"... :(
            # but, in an ideal world it will tell users what args are expected
            sig = dispatcher.system_methodSignature(method)

            # this just reads your docblock, so fill it in!
            help =  dispatcher.system_methodHelp(method)

            response.write("<li><b>%s</b>: [%s] %s" % (method, sig, help))

        response.write("</ul>")
        response.write('<a href="http://www.djangoproject.com/"><img src="http://media.djangoproject.com/img/badges/djangomade124x25_grey.gif" border="0" alt="Made with Django." title="Made with Django."></a>')

    response['Content-length'] = str(len(response.content))
    return response

# you have to manually register all functions that are xml-rpc-able
# with the dispatcher the dispatcher then maps the args down.  The
# first argument is the actual method, the second is what to call it
# from the XML-RPC side...

for function_name in exported_functions:
    function = getattr(xmlrpc, function_name)
    dispatcher.register_function(function, function_name)
