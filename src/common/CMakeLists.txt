cmake_minimum_required(VERSION 4.2)

add_library(common json.c sundry.c system.c structure.c)
target_link_libraries(common to_json)
