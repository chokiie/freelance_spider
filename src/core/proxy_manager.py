from itertools import cycle

class ProxyManager:
    """
    Handles proxy rotation.
    """
    def __init__(self, proxies=None):
        self.proxies = proxies or []
        self.proxy_pool = cycle(self.proxies) if self.proxies else None

    def get_proxy(self):
        """
        Return the next available proxy.
        """
        if not self.proxy_pool:
            return None
        return next(self.proxy_pool)

    def has_proxies(self):
        return bool(self.proxies)

    def reset(self):
        self.proxy_pool = cycle(self.proxies)

    ###################
    # Future methods
    ###################
    def mark_bad_proxy(self, proxy):
        pass

    def remove_proxy(self, proxy):
        pass

    def add_proxy(self, proxy):
        pass