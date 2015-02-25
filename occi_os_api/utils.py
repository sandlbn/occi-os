from nova import compute
from nova.image import glance

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
        return ValueError('{0} API not found'.format(str(api)))

