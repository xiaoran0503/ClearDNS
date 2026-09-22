cmake_minimum_required(VERSION 4.2)

add_library(applet adguard.c dnsproxy.c overture.c crontab.c)
target_link_libraries(applet bcrypt utils)
