#include <assert.h>
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "compiler.h"
#include "file/path.h"
#include "files.h"

#ifdef __linux__
    #include <sys/types.h>
    #include <unistd.h>

    /* Change file ownership if running as as a setuid binary
     * changed ownership to root  */
    void chown_file(const char *file_name){
        if(!geteuid()){
            uid_t user_id = getuid();
            gid_t group_id = getgid();
            chown(file_name, user_id, group_id);
        }
    }
#endif

void get_string_from_file(
    const char* a_file,
    int a_size,
    char* a_buf
){
    //char log_buff[200];
    //sprintf(log_buff, "get_string_from_file: a_file: \"%s\" a_size: %i \n",
    //a_file, a_size);
    //write_log(log_buff);
    FILE * f_file;
    f_file = fopen(a_file, "r");
    if(!f_file){
        printf("Failed to open '%s'\n", a_file);
        assert(f_file);
    }
    size_t f_char_count = fread(
        a_buf,
        sizeof(char),
        sizeof(char) * a_size,
        f_file
    );
    assert((int)f_char_count < a_size);
    a_buf[f_char_count] = '\0';
    fclose(f_file);
}

void v_write_to_file(char * a_file, char * a_string){
    FILE* pFile = fopen(a_file, "w");
    assert(pFile);
    fprintf(pFile, "%s",a_string);
    fclose(pFile);

    char mode[] = "0777";
    int i = strtol(mode, 0, 8);

    if (chmod (a_file,i) < 0)
    {
        printf("Error chmod'ing file %s.\n", a_file);
    }
}

void v_append_to_file(char * a_file, char * a_string){
    FILE* pFile = fopen(a_file, "a");
    assert(pFile);
    fprintf(pFile, "%s", a_string);
    fclose(pFile);
}

int i_file_exists(char * f_file_name){
    struct stat sts;

    //TODO:  Determine if there is a better way to do this
    if ((stat(f_file_name, &sts)) == -1)
    {
        return 0;
    }
    else
    {
        return 1;
    }
}

t_dir_list* g_get_dir_list(char * a_dir){
    t_dir_list * f_result = (t_dir_list*)malloc(sizeof(t_dir_list));
    f_result->dir_count = 0;

    int f_resize_factor = 256;
    int f_current_max = 256;

    f_result->dir_list = (char**)malloc(sizeof(char*) * f_current_max);

    DIR *dir;
    struct dirent *ent;
    dir = opendir (a_dir);

    assert(dir != NULL);
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
    char * a_name,
    char * a_default
){
    char f_path[2048];
    char * f_home = get_home_dir();
    char f_filename[256];

    sprintf(f_filename, "%s.txt", a_name);

    char * path_list[4] = {
        f_home, STARGATE_VERSION, "config", f_filename
    };

    path_join(f_path, 4, path_list);

    printf("get_file_setting:  %s \n", f_path);

    if(i_file_exists(f_path))
    {
        get_string_from_file(f_path, TINY_STRING, a_dest);
    }
    else
    {
        sprintf(a_dest, "%s", a_default);
    }
}

void delete_file(char* path){
    int retcode = remove(path);
    if(retcode == 0){
        printf("Deleted file '%s'\n", path);
    } else {
        printf(
            "Failed to delete file '%s'. remove() returned %i\n",
            path,
            retcode
        );
    }
}