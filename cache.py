import os
import pickle
from time import time


class DnsCache:
    def __init__(self):
        self.cache = []

    def update(self):
        to_remove = []
        for cache_item in self.cache:
            add_time, resource = cache_item
            if resource.r_ttl - (time() - add_time) < 0:
                to_remove.append(cache_item)
        for cache_item in to_remove:
            self.cache.remove(cache_item)

    def get_resources(self, question):
        self.update()
        result = []
        for _, resource in self.cache:
            if question.is_true_resource(resource):
                result.append(resource)
        return result

    def put_resource(self, resource):
        self.update()
        if resource not in map(lambda c: c[1], self.cache):
            self.cache.append((time(), resource))

    def get_status(self):
        self.update()
        for add_time, resource in self.cache:
            print('Time: {}s \tResource: {}'.format(int(resource.r_ttl - (time() - add_time)), resource.to_string()))

    def clear(self):
        self.cache = []
        with open('cache', 'w') as file:
            pass  # TODO: stage stuff

    def load(self):
        if os.path.getsize('cache') <= 0:
            return
        with open('cache', 'rb') as file:
            self.cache = pickle.load(file)

        print(self.cache.cache)
        self.update()
