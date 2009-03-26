import os
import mimetypes
from zope import event
from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultKeys

from Products.Archetypes.interfaces import IBaseObject
from Products.Archetypes.event import ObjectInitializedEvent
from Products.Archetypes.event import ObjectEditedEvent

def _compare(fieldval, itemval):
    """Compare a AT Field value with an item value
    
    Because AT fields return utf8 instead of unicode and item values may be 
    unicode, and most of all because python tries to decode bytes when 
    comparing a str and a unicode value, we need to special-case this
    comparison. In case of a UnicodeDecodeError, fieldval being a str and
    itemval being a unicode value, we'll decode fieldval and assume utf8 and
    retry the comparison.
    
    """
    try:
        return fieldval == itemval
    except UnicodeDecodeError:
        if isinstance(fieldval, str) and isinstance(itemval, unicode):
            return fieldval.decode('utf8', 'replace') == itemval
        raise

class ATSchemaUpdaterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context
        
        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)
    
    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            
            if not pathkey:         # not enough info
                yield item; continue
            
            path = item[pathkey]
            
            obj = self.context.unrestrictedTraverse(path.lstrip('/'), None)
            if obj is None:         # path doesn't exist
                yield item; continue
            
            if IBaseObject.providedBy(obj):
                changed = False
                is_new_object = obj.checkCreationFlag()
                for k,v in item.iteritems():
                    if k == '_type' and v in ['File', 'Image']:
                        if not '_filepath' in item.keys():
                            continue
                        filepath = item['_filepath']
                        if not os.path.isfile(filepath):
                            continue
                        file = open(filepath, 'rb')
                        data = file.read()
                        file.close()
                        if not data:
                            continue
                        field = v.lower()
                        mutator = obj.getField(field).getMutator(obj)
                        filename = path.rsplit('/')[-1]
                        mimetype, encoding = mimetypes.guess_type(filename)
                        mutator(data, filename=filename, mimetype=mimetype)
                    if k.startswith('_'):
                        continue
                    field = obj.getField(k)
                    if field is None:
                        continue
                    if not _compare(field.get(obj), v):
                        field.set(obj, v)
                        changed = True
                obj.unmarkCreationFlag()
                
                if is_new_object:
                    event.notify(ObjectInitializedEvent(obj))
                    obj.at_post_create_script()
                elif changed:
                    event.notify(ObjectEditedEvent(obj))
                    obj.at_post_edit_script()
            
            yield item
