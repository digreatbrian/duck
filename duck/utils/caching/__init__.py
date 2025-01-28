"""
Caching module which leverages the use of diskcache python library. Essential methods mandatory to any Cache class: [set, get, delete, clear]
"""

import datetime
import os
import random
import shutil
import string
import time
import uuid
from collections import defaultdict, deque
from functools import lru_cache
from pathlib import Path
from typing import Any

import diskcache


class CacheBase:
    """Base class for caching"""

    def set(self, key: str, value: Any, expiry: int | float = None):
        """Set a value in the cache."""
        raise NotImplementedError

    def get(self, key: str) -> Any:
        """Get a value from the cache. Returns None if the key is not found."""
        raise NotImplementedError

    def delete(self, key: str):
        """Delete a value from the cache."""
        raise NotImplementedError

    def save(self):
        pass

    def clear(self):
        """Clear all values from the cache."""
        raise NotImplementedError


class InMemoryCache(CacheBase):

    def __init__(self, maxkeys=None, *_):
        self.expiry_map = defaultdict()
        self.cache = dict()
        self.maxkeys = maxkeys

    def set(self, key: str, value: Any, expiry=None):
        """Set a value in the cache."""

        if self.maxkeys and len(self.cache.keys()) >= self.maxkeys:
            self.cache.popitem()
        if expiry:
            self.expiry_map.setdefault(
                key,
                datetime.datetime.now() + datetime.timedelta(seconds=expiry),
            )
        self.cache[key] = value

    def get(self, key: str) -> Any:
        """
        Get a value from the cache.

        Returns:
                None if the key is not found or expired.
        """
        if key in self.expiry_map.keys():
            expiry_date = self.expiry_map.get(key)
            if datetime.datetime.now() >= expiry_date:
                self.cache.pop(key)
                return
        value = self.cache.get(key)
        return value

    def delete(self, key: str):
        """Delete a value from the cache."""
        if key in self.cache:
            self.cache.pop(key)

    def clear(self):
        """Clear all values from the cache."""
        self.cache.clear()
        self.expiry_map.clear()

    def close(self):
        """This closes the cache"""
        self.clear()


class PersistentFileCache(CacheBase):
    """Implementation of caching using diskcache library"""

    def __init__(self, path: str, cache_size: int = None):
        if os.path.isfile(path):
            raise FileExistsError(
                f"Path should be a directory, not a file: {path}")
        self.path = path
        self.cache_size = cache_size
        self._cache = (diskcache.Cache(
            path, size_limit=cache_size, sqlite_timeout=30) if cache_size else
                       diskcache.Cache(path, sqlite_timeout=30))
        self._closed = False

    @property
    def closed(self):
        """Checks whether the cache is closed"""
        return self._closed

    def set(self, key: str, _obj: Any, expiry: int | float = None):
        """Sets the cache with an optional expiry in seconds"""
        if not isinstance(key, str):
            raise KeyError(
                f"Key should be an instance of str, not {type(key)}")
        self._cache.set(key, _obj, expire=expiry)

    def get(self, key: str):
        """Retrieves the cache"""
        if not isinstance(key, str):
            raise KeyError(
                f"Key should be an instance of str, not {type(key)}")
        return self._cache.get(key)

    def delete(self, key: str):
        """Delete a value from the cache."""
        self._cache.delete(key)

    def clear(self):
        """Clear all values from the cache."""
        self._cache.clear()

    def close(self):
        """This closes the cache"""
        self._closed = True
        self._cache.close()


class DynamicFileCache(CacheBase):
    """
    Manages a cache of files, dynamically creating new files when existing ones reach a size limit.
    """

    def __init__(
        self,
        cache_dir: str,
        cache_limit=1e9,
        cached_objs_limit: int = 128
    ):  # Default file limit is 1GB and number of objects to be cached is 128
        self.cache_dir = cache_dir
        self.cache_limit = cache_limit

        if not os.path.isdir(self.cache_dir):
            raise FileNotFoundError(f"Directory {cache_dir} not found")
        self._loaded_cache_objs = deque(maxlen=cached_objs_limit)
        self._reload_cache_files()

    def _reload_cache_files(self):
        """This reloads existing cache files in a directory"""
        self._cache_files = [
            Path(dir_entry.path) for dir_entry in os.scandir(self.cache_dir)
            if dir_entry.is_dir()
        ]
        self._cache_files.sort()

    def _get_cache_path(self) -> str:
        """Returns the path to a cache dir that is not at the size limit."""
        for dir_entry in self._cache_files:
            size = sum(f.stat().st_size for f in dir_entry.iterdir())
            if size < self.cache_limit:
                return str(dir_entry)

        new_path = self._create_new_cache_path()
        self._cache_files.append(Path(new_path))
        return new_path

    def _create_new_cache_path(self):
        """This retrieves new cache path with a unique name using uuid module"""
        name = f"{len(self._cache_files)}-{str(uuid.uuid4())[:5]}"
        path = os.path.join(self.cache_dir, name)
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def cache_obj(self):
        """This returns the Cache object for the current cache file that is not at its limit"""
        current_cache_path = self._get_cache_path()

        for obj in self._loaded_cache_objs:
            if os.path.samefile(obj.path, current_cache_path):
                return obj

        prev_obj = (self._loaded_cache_objs[-1]
                    if self._loaded_cache_objs else None)

        # closing prev obj cache if not closed
        if prev_obj:
            prev_obj.close() if not prev_obj.closed else 0

        cache_obj = self.get_cache_obj(current_cache_path)
        self._loaded_cache_objs.append(cache_obj)  # add new cache object

        return cache_obj

    def set(self, key: str, data: Any, expiry: float | int = None):
        """Set cache data with persistence"""
        self.cache_obj.set(key, data, expiry=expiry)

    def get(self, key: str) -> Any:
        """Retrieve cache data"""
        data = self.cache_obj.get(key)
        if data is not None:
            return data

        for dir_entry in reversed(self._cache_files):
            if dir_entry.samefile(self.cache_obj.path):
                continue
            cache = PersistentFileCache(str(dir_entry))
            data = cache.get(key)
            if data:
                return data
        return None

    @staticmethod
    @lru_cache(maxsize=128)
    def get_cache_obj(path: str) -> PersistentFileCache:
        return PersistentFileCache(path)

    def delete(self, key: str):
        """Delete a key pair from the cache."""
        for p in self._cache_files:
            try:
                obj = self.get_cache_obj(p)
                obj.delete(key)
            except:
                pass

    def clear(self):
        """Clear all data from the cache."""
        for p in self._cache_files:
            try:
                obj = self.get_cache_obj(p)
                obj.clear()
            except:
                pass

    def close(self):
        """Close the cache"""
        for p in self._cache_files:
            try:
                obj = self.get_cache_obj(p)
                obj.close()
            except:
                pass


class KeyAsFolderCache(CacheBase):
    """Caching which stores cache data in folders with the name of cache keys"""

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        if not os.path.isdir(self.cache_dir):
            raise FileNotFoundError(f"Directory {cache_dir} not found")

    def set(self, key: str, data: Any, expiry: int | float = None):
        """Set some cache data"""
        cache_data_path = os.path.join(self.cache_dir, key)
        cache_obj = self.get_cache_obj(cache_data_path)
        cache_obj.set(key, data, expiry=expiry)

    @staticmethod
    @lru_cache(maxsize=128)
    def get_cache_obj(path: str) -> PersistentFileCache:
        return PersistentFileCache(path)

    def get(self, key: str) -> Any:
        """This lookup for a folder in cache_dir with the name of the parsed key and returns the cache data"""
        cache_data_path = os.path.join(self.cache_dir, key or "")

        if not os.path.isdir(cache_data_path):
            # no cache data with provided key
            return None

        cache_obj = self.get_cache_obj(cache_data_path)
        cache_data = cache_obj.get(key)

        if cache_data is None:
            # remove cache data folder because the key might have expired
            try:
                shutil.rmtree(cache_data_path)
            except OSError:
                pass
        else:
            return cache_data

    @staticmethod
    @lru_cache
    def get_cache_files(d: str):
        """This gets the directories in cache_dir"""
        return [
            Path(dir_entry.path) for dir_entry in os.scandir(d)
            if dir_entry.is_dir()
        ]

    def delete(self, key: str):
        """Delete a key pair from the cache."""
        key_cache_dir = os.path.join(self.cache_dir, key)

        if not os.path.isdir(key_cache_dir):
            return

        try:
            obj = self.get_cache_obj(key_cache_dir)
            obj.clear()
        except:
            pass

    def clear(self):
        """Clear all data from the cache."""
        for p in self.get_cache_files(self.cache_dir):
            try:
                obj = self.get_cache_obj(p)
                obj.clear()
            except:
                pass

    def close(self):
        """Close the cache"""
        for p in self.get_cache_files(self.cache_dir):
            try:
                obj = self.get_cache_obj(p)
                obj.close()
            except:
                pass


class CacheSpeedTest:
    """This class performs speed test of Cache classes"""

    instances = [
        InMemoryCache,
        DynamicFileCache,
        KeyAsFolderCache,
    ]

    def __init__(self, repeat: int = 1):
        self.repeat = repeat
        self.key = self.generate_random_string(32)
        self.results = {}  # Store results for comparison

    @staticmethod
    def generate_random_string(length):
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(length))

    def test_create(self, instance):
        start = time.time()
        instance = instance("./test")
        stop = time.time()
        elapse = stop - start
        # cleanup
        instance.clear()
        return elapse

    def test_set(self, instance):
        data = self.generate_random_string(1024)
        instance = instance("./test")
        start = time.time()
        instance.set(self.key, data)
        stop = time.time()
        elapse = stop - start
        return elapse

    def test_get(self, instance):
        instance = instance("./test")
        start = time.time()
        value = instance.get(self.key)
        stop = time.time()
        elapse = stop - start
        return elapse

    def test_del(self, instance):
        instance = instance("./test")
        start = time.time()
        value = instance.delete(self.key)
        stop = time.time()
        elapse = stop - start
        return elapse

    def test_clear(self, instance):
        instance = instance("./test")
        start = time.time()
        value = instance.clear()
        stop = time.time()
        elapse = stop - start
        return elapse

    def run_test(self, instance):
        create_t = 0
        set_t = 0
        get_t = 0
        del_t = 0
        clear_t = 0

        for i in range(self.repeat):
            create_t += self.test_create(instance)
            set_t += self.test_set(instance)
            get_t += self.test_get(instance)
            del_t += self.test_del(instance)
            clear_t += self.test_clear(instance)
            self.key = self.generate_random_string(32)

        # Store results
        self.results[instance.__name__] = {
            "create": create_t / self.repeat,
            "set": set_t / self.repeat,
            "get": get_t / self.repeat,
            "delete": del_t / self.repeat,
            "clear": clear_t / self.repeat,
        }

    def execute_all(self):
        print("Running caching speed tests...")
        os.makedirs("./test", exist_ok=True)
        for instance in self.instances:
            self.run_test(instance)
        self.print_summary()
        self.compare_performance()

    def print_summary(self):
        print("\nOverall Performance Summary:")
        for instance_name, result in self.results.items():
            print(f"\n[{instance_name}]")
            print(
                f"Create  for {self.repeat} item(s): {result['create']} seconds"
            )
            print(
                f"Set     for {self.repeat} item(s): {result['set']} seconds")
            print(
                f"Get     for {self.repeat} item(s): {result['get']} seconds")
            print(
                f"Delete  for {self.repeat} item(s): {result['delete']} seconds"
            )
            print(
                f"Clear   for {self.repeat} item(s): {result['clear']} seconds"
            )

    def compare_performance(self):
        fastest_instance = {}

        for operation in ["create", "set", "get", "delete", "clear"]:
            min_time = float("inf")
            fastest = None

            for instance_name, times in self.results.items():
                if times[operation] < min_time:
                    min_time = times[operation]
                    fastest = instance_name

            fastest_instance[operation] = (fastest, min_time)

        print("\nFastest Instances for Each Operation:")
        for operation, (instance_name, min_time) in fastest_instance.items():
            print(
                f"{operation.capitalize():<6}: {instance_name} with {min_time:.6f} seconds"
            )
