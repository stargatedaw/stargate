#include <time.h>

#include "stargate.h"
#include "daw.h"
#include "files.h"
#include "wave_edit.h"


void v_open_tracks(){
    v_we_open_tracks();
}

void v_open_project(const char* a_project_folder, int a_first_load){
#ifdef __linux__
    struct timespec f_start, f_finish;
    clock_gettime(CLOCK_REALTIME, &f_start);
#endif

    printf("Setting files and folders\n");
    sprintf(STARGATE->project_folder, "%s", a_project_folder);
    sprintf(
        STARGATE->plugins_folder,
        "%s%sprojects%splugins%s",
        STARGATE->project_folder,
        PATH_SEP,
        PATH_SEP,
        PATH_SEP
    );
    sprintf(
        STARGATE->samples_folder,
        "%s%saudio%ssamples",
        STARGATE->project_folder,
        PATH_SEP,
        PATH_SEP
    );  //No trailing slash
    sprintf(
        STARGATE->samplegraph_folder,
        "%s%saudio%ssamplegraph",
        STARGATE->project_folder,
        PATH_SEP,
        PATH_SEP
    );  //No trailing slash

    sprintf(
        STARGATE->audio_pool->samples_folder,
        "%s",
        STARGATE->samples_folder
    );

    sprintf(
        STARGATE->audio_pool_file,
        "%s%saudio%saudio_pool",
        STARGATE->project_folder,
        PATH_SEP,
        PATH_SEP
    );
    sprintf(
        STARGATE->audio_folder,
        "%s%saudio%sfiles",
        STARGATE->project_folder,
        PATH_SEP,
        PATH_SEP
    );
    sprintf(
        STARGATE->audio_tmp_folder,
        "%s%saudio%sfiles%stmp%s",
        STARGATE->project_folder,
        PATH_SEP,
        PATH_SEP,
        PATH_SEP,
        PATH_SEP
    );

    if(a_first_load && i_file_exists(STARGATE->audio_pool_file)){
        printf("Loading wave pool\n");
        v_audio_pool_add_items(
            STARGATE->audio_pool,
            STARGATE->audio_pool_file
        );
    }

    printf("Opening wave editor project\n");
    v_we_open_project();
    printf("Opening DAW project\n");
    v_daw_open_project(a_first_load);
    printf("Finished opening projects\n");

#ifdef __linux__
    clock_gettime(CLOCK_REALTIME, &f_finish);
    v_print_benchmark("v_open_project", f_start, f_finish);
#endif
}


