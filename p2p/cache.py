# (almost) pure python
from copy import deepcopy
import utils


class BaseCache(object):
    """
    Base cache object for P2P. All P2P caching objects need to
    extend this class and implement its methods.
    """
    content_items_hits = 0
    content_items_gets = 0
    content_items_by_slug = dict()
    content_items_by_id = dict()

    collections_hits = 0
    collections_gets = 0
    collections_by_slug = dict()
    collections_by_id = dict()

    collection_layouts_hits = 0
    collection_layouts_gets = 0
    collection_layouts_by_slug = dict()
    collection_layouts_by_id = dict()

    sections_hits = 0
    sections_gets = 0
    sections_by_path = dict()

    def get_content_item(self, slug=None, id=None, query=None):
        raise NotImplementedError()

    def save_content_item(self, content_item, query=None):
        raise NotImplementedError()

    def get_collection(self, slug=None, id=None, query=None):
        raise NotImplementedError()

    def save_collection(self, collection, query=None):
        raise NotImplementedError()

    def get_collection_layout(self, slug=None, id=None):
        raise NotImplementedError()

    def save_collection_layout(self, collection_layout, query=None):
        raise NotImplementedError()

    def get_section(self, path=None):
        raise NotImplementedError()

    def save_section(self, section, path=None):
        raise NotImplementedError()

    def get_stats(self):
        return {
            "content_item_gets": self.content_items_gets,
            "content_item_hits": self.content_items_hits,
            "collections_gets": self.collections_gets,
            "collections_hits": self.collections_hits,
            "collection_layouts_gets": self.collection_layouts_gets,
            "collection_layouts_hits": self.collection_layouts_hits,
            "sections_gets": self.sections_gets,
            "sections_hits": self.sections_hits,
        }


class DictionaryCache(BaseCache):
    """
    Cache object for P2P that stores stuff in dictionaries. Essentially
    a local memory cache.
    """
    def get_content_item(self, slug=None, id=None, query=None):
        self.content_items_gets += 1
        try:
            if slug:
                ret = deepcopy(self.content_items_by_slug[slug])
            elif id:
                ret = deepcopy(self.content_items_by_id[id])
            else:
                raise TypeError("get_content_item() takes either a slug or id keyword argument")
            self.content_items_hits += 1
            return ret
        except (KeyError, IndexError), e:
            return None

    def save_content_item(self, content_item, query=None):
        cache_copy = deepcopy(content_item)
        self.content_items_by_slug[content_item['slug']] = cache_copy
        self.content_items_by_id[content_item['id']] = cache_copy

    def get_collection(self, slug=None, id=None, query=None):
        self.collections_gets += 1
        try:
            if slug:
                ret = deepcopy(self.collections_by_slug[slug])
            elif id:
                ret = deepcopy(self.collections_by_id[id])
            else:
                raise TypeError("get_collection() takes either a slug or id keyword argument")
            self.collections_hits += 1
            return ret
        except (KeyError, IndexError), e:
            return None

    def save_collection(self, collection, query=None):
        cache_copy = deepcopy(collection)
        self.collections_by_slug[collection['code']] = cache_copy
        self.collections_by_id[collection['id']] = cache_copy

    def get_collection_layout(self, slug, query=None):
        self.collection_layouts_gets += 1
        try:
            ret = deepcopy(self.collection_layouts_by_slug[slug])
            ret['code'] = slug
            self.collection_layouts_hits += 1
            return ret
        except (KeyError, IndexError), e:
            return None

    def save_collection_layout(self, collection_layout, query=None):
        cache_copy = deepcopy(collection_layout)
        self.collection_layouts_by_slug[collection_layout['code']] = cache_copy
        self.collection_layouts_by_id[collection_layout['id']] = cache_copy


class NoCache(BaseCache):
    """
    Caching object for P2P that doesn't cache anything. For testing and
    development and such.
    """
    def get_content_item(self, slug=None, id=None, query=None):
        return None

    def save_content_item(self, content_item, query=None):
        pass

    def get_collection(self, slug=None, id=None, query=None):
        return None

    def save_collection(self, collection, query=None):
        pass

    def get_collection_layout(self, slug=None, id=None, query=None):
        return None

    def save_collection_layout(self, collection_layout, query=None):
        pass

    def get_section(self, path=None):
        pass

    def save_section(self, section, path=None):
        pass


try:
    from django.core.cache import cache

    class DjangoCache(BaseCache):
        """
        Cache object for P2P that stores stuff using Django's cache API.
        """
        def __init__(self, prefix='p2p'):
            """
            Takes one parameter, the name of this cache
            """
            self.prefix = prefix

        def get_content_item(self, slug=None, id=None, query=None):
            self.content_items_gets += 1

            if slug:
                key = "_".join([self.prefix, 'content_item',
                                slug,
                                self.query_to_key(query)])
            elif id:
                key = "_".join([self.prefix, 'content_item',
                                str(id),
                                self.query_to_key(query)])
            else:
                raise TypeError("get_content_item() takes either a slug or "
                                "id keyword argument")
            ret = cache.get(key)
            if ret:
                self.content_items_hits += 1
            return ret

        def save_content_item(self, content_item, query=None):
            key = "_".join([self.prefix, 'content_item',
                            content_item['slug'],
                            self.query_to_key(query)])
            cache.set(key, content_item)

            key = "_".join([self.prefix, 'content_item',
                            str(content_item['id']),
                            self.query_to_key(query)])
            cache.set(key, content_item)

        def get_collection(self, slug=None, id=None, query=None):
            self.collections_gets += 1

            if slug:
                key = "_".join([self.prefix, 'collection',
                                slug,
                                self.query_to_key(query)])
            elif id:
                key = "_".join([self.prefix, 'collection',
                                str(id), self.query_to_key(query)])
            else:
                raise TypeError("get_collection() takes either a slug or id keyword argument")
            ret = cache.get(key)
            if ret:
                self.collections_hits += 1
            return ret

        def save_collection(self, collection, query=None):
            key = "_".join([self.prefix, 'collection',
                            collection['code'],
                            self.query_to_key(query)])
            cache.set(key, collection)

            key = "_".join([self.prefix, 'collection',
                            str(collection['id']),
                            self.query_to_key(query)])
            cache.set(key, collection)

        def get_collection_layout(self, slug, query=None):
            self.collection_layouts_gets += 1

            key = "_".join([self.prefix, 'collection_layout',
                            slug, self.query_to_key(query)])
            ret = cache.get(key)
            if ret:
                ret['code'] = slug
                self.collection_layouts_hits += 1
            return ret

        def save_collection_layout(self, collection_layout, query=None):
            key = "_".join([self.prefix, 'collection_layout',
                           collection_layout['code'],
                           self.query_to_key(query)])
            cache.set(key, collection_layout)

        def query_to_key(self, query):
            if query is None:
                return ''

            return utils.dict_to_qs(query)


except ImportError, e:
    pass

try:
    import redis
    import pickle

    class RedisCache(BaseCache):
        """
        Cache object for P2P that stores stuff in Redis.
        """
        def __init__(self, prefix='p2p', host='localhost', port=6379, db=0):
            """
            Takes one parameter, the name of this cache
            """
            self.prefix = prefix
            self.r = redis.StrictRedis(host=host, port=port, db=db)

        def get_content_item(self, slug=None, id=None, query=None):
            self.content_items_gets += 1

            if slug:
                key = "_".join([self.prefix, 'content_item',
                                slug,
                                self.query_to_key(query)])
            elif id:
                key = "_".join([self.prefix, 'content_item',
                                str(id),
                                self.query_to_key(query)])
            else:
                raise TypeError("get_content_item() takes either a slug or "
                                "id keyword argument")
            ret = self.r.get(key)
            if ret:
                self.content_items_hits += 1
                return pickle.loads(ret)
            return ret

        def save_content_item(self, content_item, query=None):
            key = "_".join([self.prefix, 'content_item',
                            content_item['slug'],
                            self.query_to_key(query)])
            self.r.set(key, pickle.dumps(content_item))

            key = "_".join([self.prefix, 'content_item',
                            str(content_item['id']),
                            self.query_to_key(query)])
            self.r.set(key, pickle.dumps(content_item))

        def get_collection(self, slug=None, id=None, query=None):
            self.collections_gets += 1

            if slug:
                key = "_".join([self.prefix, 'collection',
                                slug,
                                self.query_to_key(query)])
            elif id:
                key = "_".join([self.prefix, 'collection',
                                str(id), self.query_to_key(query)])
            else:
                raise TypeError("get_collection() takes either a slug or id keyword argument")
            ret = self.r.get(key)
            if ret:
                self.collections_hits += 1
                return pickle.loads(ret)
            return ret

        def save_collection(self, collection, query=None):
            key = "_".join([self.prefix, 'collection',
                            collection['code'],
                            self.query_to_key(query)])
            self.r.set(key, pickle.dumps(collection))

            key = "_".join([self.prefix, 'collection',
                            str(collection['id']),
                            self.query_to_key(query)])
            self.r.set(key, pickle.dumps(collection))

        def get_collection_layout(self, slug, query=None):
            self.collection_layouts_gets += 1

            key = "_".join([self.prefix, 'collection_layout',
                            slug, self.query_to_key(query)])
            ret = self.r.get(key)
            if ret:
                ret = pickle.loads(ret)
                ret['code'] = slug
                self.collection_layouts_hits += 1
            return ret

        def save_collection_layout(self, collection_layout, query=None):
            key = "_".join([self.prefix, 'collection_layout',
                           collection_layout['code'],
                           self.query_to_key(query)])
            self.r.set(key, pickle.dumps(collection_layout))

        def query_to_key(self, query):
            if query is None:
                return ''

            return utils.dict_to_qs(query)


except ImportError, e:
    pass
