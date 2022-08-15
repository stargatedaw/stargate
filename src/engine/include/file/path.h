#ifndef UTIL_FILE_PATH_H
#define UTIL_FILE_PATH_H

/* Intended to be similar to Python's os.path.join */
void path_join(
    char * a_result,
    int num,
    char** a_str_list
);

void vpath_join(
	char* result,
    int count,
	...
);

#endif
