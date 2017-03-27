import json

from django.views import View
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist


class JsonDeleteByIDView(View):
    """
    JsonDeleteByIDView class.
    Performs django model objects deletion by id.
    Accepts only AJAX requests from authenticated users
    AJAX request must be following format:
        {
            'objects_id_array ': ['["1","2"]']
        }
    :attr model
        Is a mandotory. Model Class

    :attr json_array_name
        Specifies array name in AJAX request

    :user_id_check
        When set to True checks model for user_id attribute
        if check sucseeds, only objects with user_id same as request.user.id
        will be deleted.

    """
    model = None
    json_array_name = 'id_array'
    user_id_check = False

    def get(self, request):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if not request.is_ajax():
            return HttpResponseBadRequest()
        if not self.model:
            raise AttributeError('View {} model attribute is not set'.format(self.__class__.__name__))
        if self. user_id_check and not hasattr(self.model, 'user'):
            raise AttributeError('Model {} has not user_id attribute'.format(self.model.__name__))
        try:
            json_data = json.loads(request.GET[self.json_array_name])
        except KeyError:
            raise AttributeError('View {} json_array_name {} improperly configured,'
                                 'or recieved'.format(self.__class__.__name__, self.json_array_name))

        result = {}
        for element in json_data:
            result[element] = True
            try:
                instance = self.model.objects.get(id=element)
                if self.user_id_check and request.user.id == instance.user_id:
                    instance.delete()
                elif self.user_id_check and request.user.id != instance.user_id:
                    result[element] = False
                else:
                    instance.delete()
            except ObjectDoesNotExist:
                pass
        return JsonResponse(result)

