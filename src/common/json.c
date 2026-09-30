#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <limits.h>
#include "cJSON.h"
#include "logger.h"
#include "sundry.h"
#include "to_json.h"
#include "constant.h"
#include "structure.h"

uint8_t is_json_suffix(const char *file_name) { // whether file name end with `.json` suffix
    if (strlen(file_name) <= 5) { // file name shorter than `.json`
        return FALSE;
    }
    if (!strcmp(file_name + strlen(file_name) - 5, ".json")) { // xxx.json
        return TRUE;
    }
    return FALSE;
}

char* to_json_format(const char *content) { // convert JSON / TOML / YAML to json format (failed -> NULL)
    const char *json_string = to_json(content); // convert to json format
    if (json_string == NULL) {
        log_warn("JSON convert error ->\n%s", content);
        return NULL; // convert failed
    }
    char *json_content = strdup(json_string); // load string into owner heap
    free_rust_string(json_string); // free rust string
    log_debug("JSON convert result ->\n%s", json_content);
    return json_content;
}

cJSON* json_field_get(cJSON *entry, const char *key) { // fetch key from json map (create when key not exist)
    cJSON *sub = entry->child;
    while (sub != NULL) { // traverse all keys
        if (!strcmp(sub->string, key)) { // target key found
            return sub;
        }
        sub = sub->next;
    }
    cJSON *new = cJSON_CreateObject(); // create new json key
    cJSON_AddItemToObject(entry, key, new);
    return new;
}

void json_field_replace(cJSON *entry, const char *key, cJSON *content) {
    if (!cJSON_ReplaceItemInObject(entry, key, content)) { // key not exist
        cJSON_AddItemToObject(entry, key, content); // add new json key
    }
}

int json_int_value(char *caption, cJSON *json) { // json int or string value -> int (overflow-safe)
    long long int_ret = 0;
    if (cJSON_IsNumber(json)) {
        double d = json->valuedouble;
        if (d < (double)INT32_MIN || d > (double)INT32_MAX) { // out of int32 range
            log_fatal("`%s` number out of range", caption);
        }
        int_ret = (long long)d;
    } else if (cJSON_IsString(json)) {
        char *p;
        errno = 0;
        int_ret = strtoll(json->valuestring, &p, 10);
        if (errno == ERANGE || p == json->valuestring || *p != '\0') { // overflow / non-numeric / trailing junk
            log_fatal("`%s` not a valid number", caption);
        }
        if (int_ret < INT32_MIN || int_ret > INT32_MAX) {
            log_fatal("`%s` number out of range", caption);
        }
    } else {
        log_fatal("`%s` must be number or string", caption);
    }
    return (int)int_ret; // never reach on error
}

uint8_t json_bool_value(char *caption, cJSON *json) { // json bool value -> bool
    if (!cJSON_IsBool(json)) {
        log_fatal("`%s` must be boolean", caption);
    }
    return json->valueint;
}

char* json_string_value(char* caption, cJSON *json) { // json string value -> string
    if (!cJSON_IsString(json)) {
        log_fatal("`%s` must be string", caption);
    }
    return strdup(json->valuestring);
}

char** json_string_list_value(char *caption, cJSON *json, char **string_list) { // json string array
    if (cJSON_IsString(json)) {
        string_list_append(&string_list, json->valuestring);
    } else if (cJSON_IsArray(json)) {
        json = json->child;
        while (json != NULL) {
            if (!cJSON_IsString(json)) {
                log_fatal("`%s` must be string array", caption);
            }
            string_list_append(&string_list, json->valuestring);
            json = json->next; // next key
        }
    } else if (!cJSON_IsNull(json)) { // allow null -> empty string list
        log_fatal("`%s` must be array or string", caption);
    }
    return string_list;
}

uint32_t** json_uint32_list_value(char *caption, cJSON *json, uint32_t **uint32_list) { // json uint32 array
    if (cJSON_IsNumber(json)) {
        uint32_list_append(&uint32_list, json->valueint);
    } else if (cJSON_IsArray(json)) {
        json = json->child;
        while (json != NULL) {
            if (!cJSON_IsNumber(json)) {
                log_fatal("`%s` must be number array", caption);
            }
            uint32_list_append(&uint32_list, json->valueint);
            json = json->next; // next key
        }
    } else if (!cJSON_IsNull(json)) { // allow null -> empty uint32 list
        log_fatal("`%s` must be array or number", caption);
    }
    return uint32_list;
}
