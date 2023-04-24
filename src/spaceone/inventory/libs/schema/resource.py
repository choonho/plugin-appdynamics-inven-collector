from schematics import Model
from schematics.types import StringType, DictType, ListType, ModelType, PolyModelType
from spaceone.inventory.libs.schema.cloud_service_type import CloudServiceTypeResource


class ErrorResource(Model):
    resource_type = StringType(default='inventory.CloudService')
    provider = StringType(default='appdynamics')
    cloud_service_group = StringType(default='')
    cloud_service_type = StringType(default='')
    resource_id = StringType(serialize_when_none=False)


class ResourceResponse(Model):
    state = StringType()
    message = StringType(default='')
    resource_type = StringType()
    match_rules = DictType(ListType(StringType), serialize_when_none=False)
    resource = DictType(StringType, default={})


class CloudServiceResourceResponse(ResourceResponse):
    state = StringType(default='SUCCESS')
    resource_type = StringType(default='inventory.CloudService')
    match_rules = DictType(ListType(StringType), default={
        '1': ['reference.resource_id', 'provider', 'cloud_service_type', 'cloud_service_group']
    })
    resource = PolyModelType(CloudServiceTypeResource)


class CloudServiceTypeResourceResponse(ResourceResponse):
    state = StringType(default='SUCCESS')
    resource_type = StringType(default='inventory.CloudServiceType')
    match_rules = DictType(ListType(StringType), default={'1': ['name', 'group', 'provider']})
    resource = PolyModelType(CloudServiceTypeResource)


class ErrorResourceResponse(ResourceResponse):
    state = StringType(default='FAILURE')
    resource_type = StringType(default='inventory.ErrorResource')
    resource = ModelType(ErrorResource, default={})

