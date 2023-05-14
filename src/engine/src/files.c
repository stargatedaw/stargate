#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "compiler.h"
#include "file/path.h"
#include "files.h"

#if SG_OS == _OS_WINDOWS
    #include <windows.h>
    #include <shlwapi.h>
#endif

#if SG_OS == _OS_LINUX
    #include <sys/types.h>
    #include <unistd.h>

    /* Change file ownership if running as as a setuid binary
     * changed ownership to root  */
    void chown_file(const char *file_name){
        if(!geteuid()){
            uid_t user_id = getuid();
            gid_t group_id = getgid();
            int result = chown(file_name, user_id, group_id);
            sg_assert(result == 0, "chown failed with %i", result);
        }
    }
#endif

void get_string_from_file(
    const SGPATHSTR* a_file,
    int a_size,
    char* a_buf
){
    //char log_buff[200];
    //sprintf(log_buff, "get_string_from_file: a_file: \"%s\" a_size: %i \n",
    //a_file, a_size);
    //write_log(log_buff);
    FILE * f_file;
#if SG_OS == _OS_WINDOWS
    f_file = _wfopen(a_file, L"r");
    sg_assert_ptr(
        f_file,
        "get_string_from_file: fopen returned NULL: '%ls'",
        a_file
    );
#else
    f_file = fopen(a_file, "r");
    sg_assert_ptr(
        f_file,
        "get_string_from_file: fopen returned NULL: '%s'",
        a_file
    );
#endif
    size_t f_char_count = fread(
        a_buf,
        sizeof(char),
        sizeof(char) * a_size,
        f_file
    );
    sg_assert(
        (int)((int)f_char_count < a_size),
        "get_string_from_file: length %i >= size %i",
        (int)f_char_count,
        a_size
    );
    a_buf[f_char_count] = '\0';
    fclose(f_file);
}

void v_write_to_file(SGPATHSTR* a_file, char * a_string){
#if SG_OS == _OS_WINDOWS
    FILE* pFile = _wfopen(a_file, L"w");
    sg_assert_ptr(
        pFile,
        "v_write_to_file: _wfopen(%ls) returned NULL ptr",
        a_file
    );
#else
    FILE* pFile = fopen(a_file, "w");
    sg_assert_ptr(
        pFile,
        "v_write_to_file: fopen(%s) returned NULL ptr",
        a_file
    );
#endif
    fprintf(pFile, "%s", a_string);
    fclose(pFile);

    char mode[] = "0777";
    int i = strtol(mode, 0, 8);

#if SG_OS != _OS_WINDOWS
    if(chmod(a_file,i) < 0){
        log_error("Error chmod'ing file %s.", a_file);
    }
#endif
}

void v_append_to_file(SGPATHSTR * a_file, char * a_string){
#if SG_OS == _OS_WINDOWS
    FILE* pFile = _wfopen(a_file, L"a");
    sg_assert_ptr(
        pFile,
        "v_append_to_file: fopen(%ls) returned NULL ptr",
        a_file
    );
#else
    FILE* pFile = fopen(a_file, "a");
    sg_assert_ptr(
        pFile,
        "v_append_to_file: fopen(%s) returned NULL ptr",
        a_file
    );
#endif
    fprintf(pFile, "%s", a_string);
    fclose(pFile);
}

int i_file_exists(SGPATHSTR* path){
#if SG_OS == _OS_WINDOWS
    if(PathFileExists(path)){
	return 1;
    } else {
        return 0;
    }
#else
    struct stat sts;

    if ((stat(path, &sts)) == -1){
        return 0;
    } else {
        return 1;
    }
#endif
}

t_dir_list* g_get_dir_list(char * a_dir){
    t_dir_list * f_result = (t_dir_list*)malloc(sizeof(t_dir_list));
    f_result->dir_count = 0;

    int f_resize_factor = 256;
    int f_current_max = 256;

    f_result->dir_list = (char**)malloc(sizeof(char*) * f_current_max);

    DIR *dir;
    struct dirent *ent;
    dir = opendir(a_dir);

    sg_assert_ptr(
        dir,
        "g_get_dir_list: opendir(%s) returned NULL",
        a_dir
    );
    //if (dir != NULL)
    //{
      while ((ent = readdir (dir)) != NULL)
      {
          if((!strcmp(ent->d_name, ".")) || (!strcmp(ent->d_name, "..")))
          {
              continue;
          }

          f_result->dir_list[(f_result->dir_count)] =
                  (char*)malloc(sizeof(char) * TINY_STRING);

            strcpy(f_result->dir_list[(f_result->dir_count)], ent->d_name);

          ++f_result->dir_count;

          if((f_result->dir_count) >= f_current_max)
          {
              f_current_max += f_resize_factor;
              f_result->dir_list =
                  (char**)realloc(f_result->dir_list,
                      sizeof(char*) * f_current_max);
          }
      }
      closedir (dir);
    /*
    }
    else
    {
      return 0;
    }
    */
    return f_result;
}

void get_file_setting(
    char * a_dest,
    SGPATHSTR * a_name,
    char * a_default
){
    SGPATHSTR path[2048];
    SGPATHSTR* f_home = get_home_dir();

    sg_path_snprintf(
        path, 
        2048, 
#if SG_OS == _OS_WINDOWS
        L"%ls/%s/config/%ls.txt", 
#else
        "%s/%s/config/%s.txt", 
#endif
        f_home, 
	STARGATE_VERSION,
        a_name
    );

#if SG_OS == _OS_WINDOWS
    log_info("get_file_setting:  %ls", path);
#else
    log_info("get_file_setting:  %s", path);
#endif

    if(i_file_exists(path)){
        get_string_from_file(path, TINY_STRING, a_dest);
    } else {
        sprintf(a_dest, "%s", a_default);
    }
}

void delete_file(SGPATHSTR* path){
#if SG_OS == _OS_WINDOWS
    int retcode = _wremove(path);
    if(retcode == 0){
        log_info("Deleted file '%ls'", path);
    } else {
        log_info(
            "Failed to delete file '%ls'. remove() returned %i",
            path,
            retcode
        );
    }
#else
    int retcode = remove(path);
    if(retcode == 0){
        log_info("Deleted file '%s'", path);
    } else {
        log_info(
            "Failed to delete file '%s'. remove() returned %i",
            path,
            retcode
        );
    }
#endif
}
