#include <assert.h>

#include "test_va1.h"
#include "plugin.h"
#include "plugins/va1.h"

t_audio_pool_item * mock_host_audio_pool_func(int val){
    return NULL;
}
void mock_queue_message(char* a, char* b){}

void TestVA1e2e(){
    PluginDescriptor* descriptor = va1_plugin_descriptor();
    t_va1* plugin_data = (t_va1*)g_va1_instantiate(
        descriptor,
        44100,
        mock_host_audio_pool_func,
        0,
        mock_queue_message
    );
    assert(plugin_data);
}
