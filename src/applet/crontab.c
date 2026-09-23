#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include "logger.h"
#include "sundry.h"
#include "system.h"
#include "crontab.h"
#include "process.h"
#include "constant.h"

uint8_t check_cron_expression(const char *exp) { // 5 whitespace-separated fields, [0-9*,/-] only
    if (exp == NULL || strlen(exp) == 0 || strlen(exp) > 256) {
        return FALSE;
    }
    if (strchr(exp, '\t') != NULL) { // no embedded tabs
        return FALSE;
    }
    int fields = 0;
    for (const char *p = exp;;) {
        while (*p == ' ') {
            ++p;
        }
        if (*p == '\0') {
            break;
        }
        ++fields;
        const char *start = p;
        while (*p != '\0' && *p != ' ') {
            if (strchr("0123456789*,/-", *p) == NULL) {
                return FALSE;
            }
            ++p;
        }
        if (p == start) { // consecutive spaces produce empty field
            return FALSE;
        }
    }
    return fields == 5; // minute hour day month weekday
}

void crontab_dump(crontab *info);

void crontab_free(crontab *info) { // free crontab options
    free(info->cron);
    free(info);
}

crontab* crontab_init() { // init crontab options
    crontab *info = (crontab *)malloc(sizeof(crontab));
    info->debug = FALSE;
    info->cron = strdup(UPDATE_CRON);
    return info;
}

void crontab_dump(crontab *info) { // show crontab options in debug log
    log_debug("Crontab debug -> %s", show_bool(info->debug));
    log_debug("Crontab expression -> `%s`", info->cron);
}

process* crontab_load(crontab *info) { // load crontab options
    crontab_dump(info);
    create_folder("/var/spool/cron/");
    create_folder("/var/spool/cron/crontabs/");
    if (!check_cron_expression(info->cron)) { // reject injection before writing root crontab
        log_fatal("Invalid crontab expression `%s` (expect 5 fields: minute hour day month weekday)", info->cron);
    }
    char *my_pid = uint32_to_string(getpid());
    char *cron_cmd = string_join("\tkill -14 ", my_pid); // SIGALRM -> 14
    free(my_pid);
    char *cron_exp = string_load("%s%s\n", info->cron, cron_cmd); // vixie-cron requires trailing '\n'
    free(cron_cmd);
    save_file("/var/spool/cron/crontabs/root", cron_exp);
    free(cron_exp);
    // vixie-cron requires spool crontab mode 0600 root:root (save_file uses fopen "w" -> 0644 under umask 022, cron ignores it)
    if (chmod("/var/spool/cron/crontabs/root", S_IRUSR | S_IWUSR)) {
        log_perror("Chmod `%s` failed -> ", "/var/spool/cron/crontabs/root");
    }
    if (chown("/var/spool/cron/crontabs/root", 0, 0)) {
        log_perror("Chown `%s` failed -> ", "/var/spool/cron/crontabs/root");
    }

    process *proc = process_init("Crontab", "crond");
    process_add_arg(proc, "-f"); // foreground
    if (info->debug) {
        process_add_arg(proc, "-l");
        process_add_arg(proc, "0"); // verbose mode
    }
    return proc;
}
