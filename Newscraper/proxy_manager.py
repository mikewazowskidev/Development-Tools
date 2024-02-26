# proxy_manager.py
import requests

class ProxyRotator:
    def __init__(self, proxies):
        self.proxies = proxies
        self.current_index = 0

    def get_next_proxy(self):
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

class DynamicProxyRotator(ProxyRotator):
    def __init__(self, proxy_source_url):
        self.proxy_source_url = proxy_source_url
        super().__init__(self.load_proxies_from_url())

    def load_proxies_from_url(self):
        response = requests.get(self.proxy_source_url)
        return response.text.split()

    def refresh_proxies(self):
        self.proxies = self.load_proxies_from_url()
        self.current_index = 0

