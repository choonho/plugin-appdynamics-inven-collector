from spaceone.core.manager import BaseManager
from spaceone.inventory.libs.connector import AppdynamicsConnector
from spaceone.inventory.libs.schema.resource import ErrorResourceResponse
from spaceone.inventory.error.custom import *
from collections.abc import Iterable
import json
import logging


_LOGGER = logging.getLogger(__name__)


class AppdynamicsManager(BaseManager):
    connector_name = None
    cloud_service_types = []
    response_schema = None

    def verify(self, options, secret_data, **kwargs):
        """ Check collector's status.
        """
        connector: AppdynamicsConnector = self.locator.get_connector('AppdynamicsConnector', secret_data=secret_data)
        params = {'secret_data': secret_data}
        connector.verify(**params)

    def collect_cloud_service_type(self, params):
        options = params.get('options', {})

        for cloud_service_type in self.cloud_service_types:
            if 'service_code_mappers' in options:
                svc_code_maps = options['service_code_mappers']
                if getattr(cloud_service_type.resource, 'service_code') and \
                        cloud_service_type.resource.service_code in svc_code_maps:
                    cloud_service_type.resource.service_code = svc_code_maps[cloud_service_type.resource.service_code]

            if 'custom_asset_url' in options:
                _tags = cloud_service_type.resource.tags

                if 'spaceone:icon' in _tags:
                    _icon = _tags['spaceone:icon']
                    _tags['spaceone:icon'] = f'{options["custom_asset_url"]}/{_icon.split("/")[-1]}'

            yield cloud_service_type

    def collect_cloud_service(self, params) -> list:
        raise NotImplemented

    def collect_resources(self, params) -> list:
        total_resources = []

        try:
            total_resources.extend(self.collect_cloud_service_type(params))
            resources, error_resources = self.collect_cloud_service(params)

            total_resources.extend(resources)
            total_resources.extend(error_resources)

        except Exception as e:
            error_resource_response = self.generate_error_response(e, self.cloud_service_types[0].resource.group, self.cloud_service_types[0].resource.name)
            total_resources.append(error_resource_response)
            _LOGGER.error(f'[collect] {e}', exc_info=True)

        return total_resources

    def convert_nested_dictionary(self, cloud_svc_object):
        cloud_svc_dict = {}
        if hasattr(cloud_svc_object, '__dict__'):  # if cloud_svc_object is not a dictionary type but has dict method
            cloud_svc_dict = cloud_svc_object.__dict__
        elif isinstance(cloud_svc_object, dict):
            cloud_svc_dict = cloud_svc_object
        elif not isinstance(cloud_svc_object, list):  # if cloud_svc_object is one of type like int, float, char, ...
            return cloud_svc_object

        # if cloud_svc_object is dictionary type
        for key, value in cloud_svc_dict.items():
            if 'appdynamics' in str(type(value)):
                cloud_svc_dict[key] = self.convert_nested_dictionary(value)
            elif isinstance(value, list):
                value_list = []
                for v in value:
                    value_list.append(self.convert_nested_dictionary(v))
                cloud_svc_dict[key] = value_list

        return cloud_svc_dict

    @staticmethod
    def convert_tag_format(tags):
        convert_tags = []

        if tags:
            for k, v in tags.items():
                convert_tags.append({
                    'key': k,
                    'value': v
                })

        return convert_tags

    @staticmethod
    def convert_dictionary(obj):
        return vars(obj)

    @staticmethod
    def get_resource_group_from_id(dict_id):
        resource_group = dict_id.split('/')[4]
        return resource_group

    @staticmethod
    def generate_error_response(e, cloud_service_group, cloud_service_type):
        if type(e) is dict:
            error_resource_response = ErrorResourceResponse({'message': json.dumps(e),
                                                             'resource': {'cloud_service_group': cloud_service_group,
                                                                          'cloud_service_type': cloud_service_type}})
        else:
            error_resource_response = ErrorResourceResponse({'message': str(e),
                                                             'resource': {'cloud_service_group': cloud_service_group,
                                                                          'cloud_service_type': cloud_service_type}})
        return error_resource_response

    @staticmethod
    def generate_resource_error_response(e, cloud_service_group, cloud_service_type, resource_id):
        if type(e) is dict:
            error_resource_response = ErrorResourceResponse({'message': json.dumps(e),
                                                             'resource': {'cloud_service_group': cloud_service_group,
                                                                          'cloud_service_type': cloud_service_type,
                                                                          'resource_id': resource_id}})
        else:
            error_resource_response = ErrorResourceResponse({'message': str(e),
                                                             'resource': {'cloud_service_group': cloud_service_group,
                                                                          'cloud_service_type': cloud_service_type,
                                                                          'resource_id': resource_id}})
        return error_resource_response
