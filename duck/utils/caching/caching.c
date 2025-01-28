#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DEFAULT_CACHE_SIZE 100

typedef struct {
    char key[256];
    char value[1024]; // Adjust size as needed
} CacheItem;

CacheItem* cache;
int cache_size = DEFAULT_CACHE_SIZE;
int cache_count = 0;

void initialize_cache(int size) {
    cache_size = size;
    cache = (CacheItem*)malloc(cache_size * sizeof(CacheItem));
    cache_count = 0;
}

void set_cache(const char* key, const char* value) {
    if (cache_count < cache_size) {
        strcpy(cache[cache_count].key, key);
        strcpy(cache[cache_count].value, value);
        cache_count++;
    } else {
        printf("Cache is full.\n");
    }
}

const char* get_cache(const char* key) {
    for (int i = 0; i < cache_count; i++) {
        if (strcmp(cache[i].key, key) == 0) {
            return cache[i].value;
        }
    }
    return NULL;
}

void save_cache(const char* filename) {
    FILE* file = fopen(filename, "ab");
    if (file) {
        fwrite(&cache_count, sizeof(int), 1, file);
        fwrite(cache, sizeof(CacheItem), cache_count, file);
        fclose(file);
    }
}

void load_cache(const char* filename) {
    FILE* file = fopen(filename, "rb");
    if (file) {
        int temp_cache_count;
        while (fread(&temp_cache_count, sizeof(int), 1, file)) {
            if (cache_count + temp_cache_count > cache_size) {
                cache_size = cache_count + temp_cache_count;
                cache = (CacheItem*)realloc(cache, cache_size * sizeof(CacheItem));
            }
            fread(&cache[cache_count], sizeof(CacheItem), temp_cache_count, file);
            cache_count += temp_cache_count;
        }
        fclose(file);
    }
}

void free_cache() {
    free(cache);
}
