import time
import logging
import concurrent.futures
from spaceone.inventory.libs.manager import AppdynamicsManager
from spaceone.core.service import *
from spaceone.inventory.conf.cloud_service_conf import *

_LOGGER = logging.getLogger(__name__)


@authentication_handler
class CollectorService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)

    @check_required(['options'])
    def init(self, params):
        """ init plugin by options
        """
        capability = {
            'filter_format': FILTER_FORMAT,
            'supported_resource_type': SUPPORTED_RESOURCE_TYPE,
            'supported_features': SUPPORTED_FEATURES,
            'supported_schedules': SUPPORTED_SCHEDULES
        }
        return {'metadata': capability}

    @transaction
    @check_required(['options', 'secret_data'])
    def verify(self, params):
        """
        Args:
              params:
                - options
                - secret_data
        """
        options = params['options']
        secret_data = params.get('secret_data', {})
        if secret_data != {}:
            appd_manager = AppdynamicsManager()
            active = appd_manager.verify({}, secret_data=secret_data)

        return {}

    @transaction
    @check_required(['options', 'secret_data', 'filter'])
    def collect(self, params):
        """
        Args:
            params:
                - options
                - schema
                - secret_data
                - filter
        """

        start_time = time.time()
        secret_data = params.get('secret_data', {})

        _LOGGER.debug("[ EXECUTOR START: Appdynamics Cloud Service ]")
        target_execute_managers = self._get_target_execute_manger(params.get('options', {}))

        # Thread per cloud services
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
            future_executors = []

            for execute_manager in target_execute_managers:
                _LOGGER.info(f'@@@ {execute_manager} @@@')
                _manager = self.locator.get_manager(execute_manager)
                future_executors.append(executor.submit(_manager.collect_resources, params))

            for future in concurrent.futures.as_completed(future_executors):
                for result in future.result():
                    yield result

        _LOGGER.debug(f'TOTAL TIME : {time.time() - start_time} Seconds')

    def _get_target_execute_manger(self, options):
        if 'cloud_service_types' in options:
            execute_managers = self._match_execute_manager(options['cloud_service_types'])
        else:
            execute_managers = list(CLOUD_SERVICE_GROUP_MAP.values())

        return execute_managers

    @staticmethod
    def _match_execute_manager(cloud_service_groups):
        return [CLOUD_SERVICE_GROUP_MAP[_cloud_service_group] for _cloud_service_group in cloud_service_groups
                if _cloud_service_group in CLOUD_SERVICE_GROUP_MAP]
