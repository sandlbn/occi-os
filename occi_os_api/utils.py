from nova import compute
from nova.image import glance
from oslo.config import cfg

CONF = cfg.CONF

def get_openstack_api(api):
    """
    return openstack api
    """
    if api == 'security':
        return compute.API().security_group_api
    elif api == 'compute':
        return compute.API()
    elif api == 'neutron':
        return compute.API().network_api
    elif api == 'volume':
        return compute.API().volume_api
    elif api == 'image':
        return glance.get_default_image_service()
    else:
        raise ValueError('{0} API not found'.format(str(api)))

def get_neutron_url():
    return CONF.neutron.url
