#include <stdlib.h>
#include <string.h>
#include "bcrypt.h"
#include "logger.h"
#include "constant.h"

char* bcrypt_hash(const char *data) {
    char salt[BCRYPT_HASHSIZE];
    log_debug("BCrypt data -> *** (len=%zu)", strlen(data));
    if (bcrypt_gensalt(10, salt)) {
        log_fatal("BCrypt generate salt error");
    }
    char *hash = (char *)malloc(BCRYPT_HASHSIZE);
    if (bcrypt_hashpw(data, salt, hash)) {
        log_fatal("BCrypt generate hash error");
    }
    log_debug("BCrypt hash generated");
    return hash;
}

int bcrypt_verify(const char *data, const char *hash) {
    if (bcrypt_checkpw(data, hash) == 0) {
        return TRUE;
    }
    return FALSE;
}
