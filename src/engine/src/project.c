#include <time.h>

#include "stargate.h"
#include "daw.h"
#include "files.h"
#include "wave_edit.h"


void v_open_project(const SGPATHSTR* a_project_folder, int a_first_load){
#if SG_OS == _OS_LINUX
    struct timespec f_start, f_finish;
    clock_gettime(CLOCK_REALTIME, &f_start);
#endif

    SGPATHSTR stargate_dot_project[1024];
    sg_path_snprintf(
        stargate_dot_project,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/stargate.project",
#else
        "%s/stargate.project",
#endif
        a_project_folder
    );
    if(!i_file_exists(stargate_dot_project)){
#if SG_OS == _OS_WINDOWS
        log_error(
            "Project folder %ls does not contain a stargate.project file, "
            "it is not a Stargate DAW project, exiting.",
            a_project_folder
        );
#else
        log_error(
            "Project folder %s does not contain a stargate.project file, "
            "it is not a Stargate DAW project, exiting.",
            a_project_folder
        );
#endif
        exit(321);
    }
    log_info("Setting files and folders");
    sg_path_snprintf(
        STARGATE->project_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls",
#else
        "%s",
#endif
        a_project_folder
    );
    sg_path_snprintf(
        STARGATE->plugins_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/projects/plugins/",
#else
        "%s/projects/plugins/",
#endif
        STARGATE->project_folder
    );
    sg_path_snprintf(
        STARGATE->samples_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/audio/samples",
#else
        "%s/audio/samples",
#endif
        STARGATE->project_folder
    );  //No trailing slash
    sg_path_snprintf(
        STARGATE->samplegraph_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/audio/samplegraph",
#else
        "%s/audio/samplegraph",
#endif
        STARGATE->project_folder
    );  //No trailing slash

    sg_path_snprintf(
        STARGATE->audio_pool->samples_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls",
#else
        "%s",
#endif
        STARGATE->samples_folder
    );

    sg_path_snprintf(
        STARGATE->audio_pool_file,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/audio/audio_pool",
#else
        "%s/audio/audio_pool",
#endif
        STARGATE->project_folder
    );
    sg_path_snprintf(
        STARGATE->audio_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/audio",
#else
        "%s/audio",
#endif
        STARGATE->project_folder
    );
    sg_path_snprintf(
        STARGATE->audio_tmp_folder,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/audio/files/tmp/",
#else
        "%s/audio/files/tmp/",
#endif
        STARGATE->project_folder
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


