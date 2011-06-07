'''
Created on May 17, 2011

@author: Alendit
'''
from django.contrib.auth.decorators import login_required
from exeapp.shortcuts import get_package_by_id_or_error
from exeapp import shortcuts
from django.http import HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response
from exeapp.views.blocks.blockfactory import block_factory
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django import forms
from exeapp.models.data_package import Package

@login_required
@get_package_by_id_or_error
def authoring(request, package):
    '''Handles calls to authoring iframe. Renders exe/authoring.html'''
    
    if "idevice_id" in request.GET:
        try:
            idevice = package.get_idevice_for_partial\
                        (request.GET['idevice_id'])
            if request.GET.get("media", "") == "true":
                json = simplejson.dumps(get_unique_media_list(
                                        idevice.parent_node, idevice))
                return HttpResponse(json, content_type="text/javascript")
            
            idevice_html = shortcuts.render_idevice(idevice)
            return HttpResponse(idevice_html)
        except ObjectDoesNotExist, e:
            raise Http404(e)
    # if partial is set return only content of body
    partial = "partial" in request.GET and request.GET['partial'] == "true"
    data_package = package
    return render_to_response('exe/authoring.html', locals())


    
    
@login_required
@get_package_by_id_or_error
def handle_action(request, package):
    '''Handles post action sent from authoring'''
    if request.method == "POST":
        post_dict = dict(request.POST)
        if 'content' in request.POST:
            content = request.POST['content']
        idevice_id = post_dict.pop('idevice_id')[0]
        action = post_dict.pop('idevice_action')[0]
        response = package.handle_action(idevice_id,
                                          action, request.POST)
        return HttpResponse(response)
    return HttpResponse()

def get_media_list(node):
    '''Returns the idevice-specific media list for a given node. Always
includes tinymce compressor, since it can't be loaded dynamically'''
    # always load tinymce compressor
    media = forms.Media(js=[reverse('tinymce-compressor')])
    for idevice in node.idevices.all():
        idevice = idevice.as_child()
        block = block_factory(idevice) 
        media += block.media
    return str(media)

def get_unique_media_list(node, idevice):
    '''Returns a list of media which is used only by this idevice'''
    block = block_factory(idevice.as_child())
    media = block.media._js
    # compressor is always loaded per default
    media.remove(reverse('tinymce-compressor'))
    for idevice in node.idevices.exclude(id=idevice.id):
        block = block_factory(idevice.as_child()) 
        for js in block.media:
            if js in media:
                media.remove(js)
    return media