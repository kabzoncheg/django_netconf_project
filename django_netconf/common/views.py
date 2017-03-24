import json

from django.views import View
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist


class JsonDeleteByIDView(View):

    model = None
    json_array_name = 'objects_id_array'

    def get(self, request, model):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if not request.is_ajax():
            return HttpResponseBadRequest()
        if not self.model:
            raise AttributeError('View {} modelattribute is not set'.format(self.__class__.__name__))
        if not hasattr(model, 'user_id'):
            raise AttributeError('Model {} has not user_id attribute'.format(self.model.__name__))
        try:
            json_data = json.loads(request.GET[self.json_array_name])
        except KeyError:
            raise AttributeError('View {} json_array_name {} improperly configured,'
                                 'or recieved'.format(self.__class__.__name__, self.json_array_name))

        result = {}
        for element in json_data:
            try:
                instance = model.objects.get(id=element)
                if request.user.id == instance.user_id:
                    instance.delete()
                    result[element] = True
                else:
                    result[element] = False
            except ObjectDoesNotExist:
                pass
        return JsonResponse(result)

