cmake_minimum_required(VERSION 4.2)

add_library(blowfish crypt_blowfish.c crypt_gensalt.c wrapper.c)
