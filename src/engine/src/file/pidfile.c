#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

#include "compiler.h"
#include "file/pidfile.h"
#include "files.h"


char* pidfile_path(){
    char* path = (char*)malloc(1024);
    snprintf(
        path,
        600,
        "%s/stargate/engine.pid",
        get_home_dir()
    );
    return path;
}

void create_pidfile(char* path){
    pid_t pid = getpid();
    char pidstr[128];
    sprintf(pidstr, "%i", (int)pid);
    v_write_to_file(path, pidstr);
}

