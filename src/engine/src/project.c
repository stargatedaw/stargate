#include <time.h>

#include "stargate.h"
#include "daw.h"
#include "files.h"
#include "wave_edit.h"


void v_open_tracks(){
    v_we_open_tracks();
}

void v_open_project(const char* a_project_folder, int a_first_load){
#if SG_OS == _OS_LINUX
    struct timespec f_start, f_finish;
    clock_gettime(CLOCK_REALTIME, &f_start);
#endif

    char stargate_dot_project[1024];
    sg_snprintf(
        stargate_dot_project,
        1024,
        "%s%sstargate.project",
        a_project_folder,
        PATH_SEP
    );
    if(!i_file_exists(stargate_dot_project)){
        log_error(
            "Project folder %s does not contain a stargate.project file, "
            "it is not a Stargate DAW project, exiting.",
            a_project_folder
        );
        exit(321);
    }
    log_info("Setting files and folders");
    sg_snprintf(
        STARGATE->project_folder,
        1024,
        "%s",
        a_project_folder
    );
    sg_snprintf(
        STARGATE->plugins_folder,
        1024,
        "%s%sprojects%splugins%s",
        STARGATE->project_folder,
        PATH_SEP,
        PATH_SEP,
        PATH_SEP
    );
    sg_snprintf(
        STARGATE->samples_folder,
        1024,
        "%s%saudio%ssamples",
        STARGATE->project_folder,
        PATH_SEP,
        PATH_SEP
    );  //No trailing slash
    sg_snprintf(
        STARGATE->samplegraph_folder,
        1024,
        "%s%saudio%ssamplegraph",
        STARGATE->project_folder,
        PATH_SEP,
        PATH_SEP
    );  //No trailing slash

    sg_snprintf(
        STARGATE->audio_pool->samples_folder,
        1024,
        "%s",
        STARGATE->samples_folder
    );

    sg_snprintf(
        STARGATE->audio_pool_file,
        1024,
        "%s%saudio%saudio_pool",
        STARGATE->project_folder,
        PATH_SEP,
        PATH_SEP
    );
    sg_snprintf(
        STARGATE->audio_folder,
        1024,
        "%s%saudio",
        STARGATE->project_folder,
        PATH_SEP
    );
    sg_snprintf(
        STARGATE->audio_tmp_folder,
        1024,
        "%s%saudio%sfiles%stmp%s",
        STARGATE->project_folder,
        PATH_SEP,
        PATH_SEP,
        PATH_SEP,
        PATH_SEP
    );

    if(a_first_load && i_file_exists(STARGATE->audio_pool_file)){
        log_info("Loading wave pool");
        v_audio_pool_add_items(
            STARGATE->audio_pool,
            STARGATE->audio_pool_file,
            STARGATE->audio_folder
        );
    }

    log_info("Opening wave editor project");
    v_we_open_project();
    log_info("Opening DAW project");
    v_daw_open_project(a_first_load);
    log_info("Finished opening projects");

#if SG_OS == _OS_LINUX
    clock_gettime(CLOCK_REALTIME, &f_finish);
    v_print_benchmark("v_open_project", f_start, f_finish);
#endif
}


