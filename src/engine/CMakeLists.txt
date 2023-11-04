cmake_minimum_required(VERSION 3.1.0)

project(
    stargate-engine
    VERSION 1.0
    DESCRIPTION "boom chi boom chi"
    LANGUAGES C
)
FILE(
    GLOB_RECURSE
    src
    ${PROJECT_SOURCE_DIR}/src/*.c
)

add_executable(stargate-engine cli/main.c ${src})
target_include_directories(stargate-engine PRIVATE include)
target_compile_features(stargate-engine PRIVATE c_std_17)
set_target_properties(stargate-engine PROPERTIES LINKER_LANGUAGE C)
target_compile_options(
    stargate-engine
    PRIVATE
	-flto
	-fno-stack-protector
	-fprefetch-loop-arrays
)

execute_process(
    COMMAND
    /bin/sh -c "getconf LEVEL1_DCACHE_LINESIZE || echo 64"
    OUTPUT_VARIABLE CACHE_LINE_SIZE
)

target_compile_definitions(
    stargate-engine
    PRIVATE
    SG_THREAD_LOCAL=__thread
	CACHE_LINE_SIZE=${CACHE_LINE_SIZE}
	_GNU_SOURCE
	__USE_GNU
)

if (CMAKE_SYSTEM_NAME STREQUAL "Windows")
    target_compile_options(
        stargate-engine
        PRIVATE
        -I/mingw64/include
        -lws2_32
        -lDbgHelp
        -lavrt
        -lshlwapi
    )
elseif (CMAKE_SYSTEM_NAME STREQUAL "Linux")
    # target_compile_options(myApp PRIVATE -Wall -Wextra -Wpedantic)
elseif (CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    # other macOS-specific flags for Clang
else()
    message(SEND_ERROR "Unknown platform ${CMAKE_SYSTEM_NAME}")
endif()

target_link_libraries(stargate-engine m)
target_link_libraries(stargate-engine fftw3)
target_link_libraries(stargate-engine fftw3f)
target_link_libraries(stargate-engine portaudio)
target_link_libraries(stargate-engine portmidi)
target_link_libraries(stargate-engine pthread)
target_link_libraries(stargate-engine sndfile)
