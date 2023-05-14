#include "stargate.h"
#include "daw.h"
#include "files.h"

void v_daw_update_track_send(
    t_daw * self,
    int a_lock
){
    t_daw_routing_graph * f_graph = g_daw_routing_graph_get(self);
    t_daw_routing_graph * f_old = self->routing_graph;

    if(a_lock){
        pthread_spin_lock(&STARGATE->main_lock);
    }

    self->routing_graph = f_graph;

    if(a_lock){
        pthread_spin_unlock(&STARGATE->main_lock);
    }

    if(f_old){
        v_daw_routing_graph_free(f_old);
    }
}

void v_daw_routing_graph_free(t_daw_routing_graph * self)
{
    free(self);
}

t_daw_routing_graph * g_daw_routing_graph_get(t_daw * self)
{
    t_daw_routing_graph * f_result = NULL;
    lmalloc((void**)&f_result, sizeof(t_daw_routing_graph));

    int f_i = 0;
    int f_i2 = 0;

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i)
    {
        for(f_i2 = 0; f_i2 < MAX_WORKER_THREADS; ++f_i2)
        {
            f_result->track_pool_sorted[f_i2][f_i] = 0;
            f_result->bus_count[f_i] = 0;
        }

        for(f_i2 = 0; f_i2 < MAX_ROUTING_COUNT; ++f_i2)
        {
            f_result->routes[f_i][f_i2].active = 0;
        }
    }

    f_result->track_pool_sorted_count = 0;

    SGPATHSTR f_tmp[1024];
    sg_path_snprintf(
        f_tmp,
        1024,
#if SG_OS == _OS_WINDOWS
        L"%ls/projects/daw/routing.txt",
#else
        "%s/projects/daw/routing.txt",
#endif
        STARGATE->project_folder
    );

    if(i_file_exists(f_tmp)){
        t_2d_char_array * f_2d_array = g_get_2d_array_from_file(
        f_tmp, LARGE_STRING);
        while(1){
            v_iterate_2d_char_array(f_2d_array);
            if(f_2d_array->eof){
                break;
            }

            if(f_2d_array->current_str[0] == 't'){
                v_iterate_2d_char_array(f_2d_array);
                int f_track_num = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_index = atoi(f_2d_array->current_str);

                for(f_i = 0; f_i < MAX_WORKER_THREADS; ++f_i){
                    f_result->track_pool_sorted[f_i][f_index] = f_track_num;
                }
            } else if(f_2d_array->current_str[0] == 's'){
                v_iterate_2d_char_array(f_2d_array);
                int f_track_num = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_index = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_output = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_sidechain = atoi(f_2d_array->current_str);

                v_track_routing_set(
                    &f_result->routes[f_track_num][f_index],
                    f_output,
                    f_sidechain
                );
                ++f_result->bus_count[f_output];
            } else if(f_2d_array->current_str[0] == 'c'){
                v_iterate_2d_char_array(f_2d_array);
                int f_count = atoi(f_2d_array->current_str);
                f_result->track_pool_sorted_count = f_count;
            } else {
                sg_assert(
                    0,
                    "g_daw_routing_graph_get, unknown field: %s",
                    f_2d_array->current_str
                );
            }
        }
        g_free_2d_char_array(f_2d_array);
    }

    return f_result;
}

void g_daw_midi_routing_list_init(t_daw_midi_routing_list * self)
{
    int f_i;

    for(f_i = 0; f_i < DN_TRACK_COUNT; ++f_i)
    {
        self->routes[f_i].on = 0;
        self->routes[f_i].output_track = -1;
    }
}

void v_track_routing_set(
    t_track_routing* self,
    int a_output,
    int a_type
){
    self->output = a_output;
    self->type = a_type;

    if(a_output >= 0){
        self->active = 1;
    } else {
        self->active = 0;
    }
}

void v_track_routing_free(t_track_routing * self){
    free(self);
}
