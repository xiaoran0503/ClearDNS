#include <string.h>
#include <stdlib.h>
#include "json.h"
#include "config.h"
#include "logger.h"
#include "sundry.h"
#include "system.h"

void cache_parser(cache_config *config, cJSON *json) { // cache options parser
    if (!cJSON_IsObject(json)) {
        log_fatal("`cache` must be object");
    }
    json = json->child;
    while (json != NULL) {
        if (!strcmp(json->string, "size")) {
            int size = json_int_value("cache.size", json);
            if (size <= 0 || size > (1 << 30)) { // reject zero/negative/oversized cache (OOM guard)
                log_fatal("`cache.size` must be in (0, 1073741824]");
            }
            config->size = (uint32_t)size;
        }
        if (!strcmp(json->string, "enable")) {
            config->enable = json_bool_value("cache.enable", json);
        }
        if (!strcmp(json->string, "optimistic")) {
            config->optimistic = json_bool_value("cache.optimistic", json);
        }
        json = json->next; // next field
    }
}

void upstream_parser(char *caption, upstream_config *config, cJSON *json) { // upstream options parser
    if (!cJSON_IsObject(json)) {
        log_fatal("`%s` must be object", caption);
    }
    char *key_name;
    json = json->child;
    while (json != NULL) {
        if (!strcmp(json->string, "port")) {
            key_name = string_join(caption, ".port");
            int port = json_int_value(key_name, json);
            if (port <= 0 || port > 65535) { // reject out-of-range before uint16 truncation
                log_fatal("`%s` must be in (0, 65535]", key_name);
            }
            config->port = (uint16_t)port;
            free(key_name);
        }
        if (!strcmp(json->string, "ipv6")) {
            key_name = string_join(caption, ".ipv6");
            config->ipv6 = json_bool_value(key_name, json);
            free(key_name);
        }
        if (!strcmp(json->string, "verify")) {
            key_name = string_join(caption, ".verify");
            config->verify = json_bool_value(key_name, json);
            free(key_name);
        }
        if (!strcmp(json->string, "parallel")) {
            key_name = string_join(caption, ".parallel");
            config->parallel = json_bool_value(key_name, json);
            free(key_name);
        }
        if (!strcmp(json->string, "bootstrap")) {
            key_name = string_join(caption, ".bootstrap");
            config->bootstrap = json_string_list_value(key_name, json, config->bootstrap);
            free(key_name);
        }
        if (!strcmp(json->string, "fallback")) {
            key_name = string_join(caption, ".fallback");
            config->fallback = json_string_list_value(key_name, json, config->fallback);
            free(key_name);
        }
        if (!strcmp(json->string, "primary")) {
            key_name = string_join(caption, ".primary");
            config->primary = json_string_list_value(key_name, json, config->primary);
            free(key_name);
        }
        json = json->next; // next field
    }
}

void diverter_parser(diverter_config *config, cJSON *json) { // diverter options parser
    if (!cJSON_IsObject(json)) {
        log_fatal("`diverter` must be object");
    }
    json = json->child;
    while (json != NULL) {
        if (!strcmp(json->string, "port")) {
            int diverter_port = json_int_value("diverter.port", json);
            if (diverter_port <= 0 || diverter_port > 65535) {
                log_fatal("`diverter.port` must be in (0, 65535]");
            }
            config->port = (uint16_t)diverter_port;
        }
        if (!strcmp(json->string, "gfwlist")) {
            config->gfwlist = json_string_list_value("diverter.gfwlist", json, config->gfwlist);
        }
        if (!strcmp(json->string, "china-ip")) {
            config->china_ip = json_string_list_value("diverter.china-ip", json, config->china_ip);
        }
        if (!strcmp(json->string, "chinalist")) {
            config->chinalist = json_string_list_value("diverter.chinalist", json, config->chinalist);
        }
        json = json->next; // next field
    }
}

void adguard_parser(adguard_config *config, cJSON *json) { // adguard options parser
    if (!cJSON_IsObject(json)) {
        log_fatal("`adguard` must be object");
    }
    json = json->child;
    while (json != NULL) {
        if (!strcmp(json->string, "port")) {
            int adguard_port = json_int_value("adguard.port", json);
            if (adguard_port <= 0 || adguard_port > 65535) {
                log_fatal("`adguard.port` must be in (0, 65535]");
            }
            config->port = (uint16_t)adguard_port;
        }
        if (!strcmp(json->string, "enable")) {
            config->enable = json_bool_value("adguard.enable", json);
        }
        if (!strcmp(json->string, "username")) {
            free(config->username);
            config->username = json_string_value("adguard.username", json);
        }
        if (!strcmp(json->string, "password")) {
            free(config->password);
            config->password = json_string_value("adguard.password", json);
        }
        json = json->next; // next field
    }
}

void assets_parser(assets_config *config, cJSON *json) { // assets options parser
    if (!cJSON_IsObject(json)) {
        log_fatal("`assets` must be object");
    }
    json = json->child;
    while (json != NULL) {
        if (!strcmp(json->string, "disable")) {
            config->disable = json_bool_value("assets.disable", json);
        }
        if (!strcmp(json->string, "cron")) {
            free(config->cron); // release default from config_init() before overwrite
            config->cron = json_string_value("assets.cron", json);
        }
        if (!strcmp(json->string, "update")) {
            if (!cJSON_IsObject(json)) {
                log_fatal("`%s` must be map", "assets.update");
            }
            cJSON *asset_item = json->child;
            while (asset_item != NULL) { // traverse all json field
                asset *res = asset_init(asset_item->string);
                char *caption = string_join("assets.update.", asset_item->string);
                res->sources = json_string_list_value(caption, asset_item, res->sources);
                free(caption);
                assets_append(&config->resources, res);
                asset_item = asset_item->next;
            }
        }
        json = json->next; // next field
    }
}

void cleardns_parser(cleardns_config *config, const char *config_content) { // JSON format configure
    cJSON *root = cJSON_Parse(config_content);
    if (root == NULL) {
        log_fatal("ClearDNS configure format error");
    }
    if (!cJSON_IsObject(root)) {
        log_fatal("ClearDNS configure root must be an object");
    }
    cJSON *json = root->child;
    while (json != NULL) {
        if (!strcmp(json->string, "port")) {
            int main_port = json_int_value("port", json);
            if (main_port <= 0 || main_port > 65535) {
                log_fatal("`port` must be in (0, 65535]");
            }
            config->port = (uint16_t)main_port;
        }
        if (!strcmp(json->string, "cache")) {
            cache_parser(&config->cache, json);
        }
        if (!strcmp(json->string, "domestic")) {
            upstream_parser("domestic", &config->domestic, json);
        }
        if (!strcmp(json->string, "foreign")) {
            upstream_parser("foreign", &config->foreign, json);
        }
        if (!strcmp(json->string, "diverter")) {
            diverter_parser(&config->diverter, json);
        }
        if (!strcmp(json->string, "adguard")) {
            adguard_parser(&config->adguard, json);
        }
        if (!strcmp(json->string, "assets")) {
            assets_parser(&config->assets, json);
        }
        if (!strcmp(json->string, "reject")) {
            config->reject = json_uint32_list_value("reject", json, config->reject);
        }
        if (!strcmp(json->string, "hosts")) {
            config->hosts = json_string_list_value("hosts", json, config->hosts);
        }
        if (!strcmp(json->string, "ttl")) {
            config->ttl = json_string_list_value("ttl", json, config->ttl);
        }
        if (!strcmp(json->string, "custom")) {
            config->script = json_string_list_value("custom", json, config->script);
        }
        json = json->next; // next field
    }
    cJSON_Delete(root); // recursive free whole tree (cJSON_free only frees the root node)
}

void config_parser(cleardns_config *config, const char *config_file) {
    char *config_content = read_file(config_file);

    if (is_json_suffix(config_file)) { // JSON format
        log_info("Start JSON configure parser");
    } else { // YAML or TOML format
        log_info("Start configure parser");
        char *convert_ret = to_json_format(config_content);
        if (convert_ret == NULL) { // convert failed
            log_fatal("Configure parser error");
        }
        free(config_content);
        config_content = convert_ret;
    }

    cleardns_parser(config, config_content); // configure parser
    free(config_content);
    log_info("Configure parser success");
}
