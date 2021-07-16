/* Python C extension of the engine
   This does not work very well, presumably because the GIL has more
   effect upon it than anticipated, keeping it around in case the situation
   improves later
*/
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "_main.h"
#include "stargate.h"

static PyObject *StargateEngineError;

PyObject *UI_CALLBACK;

extern void pymod_ui_callback_wrapper(char* key, char* value){
	PyObject *k = PyBytes_FromString(key);
	PyObject *v = PyBytes_FromString(value);
	PyObject *args = PyTuple_New(2);
	PyTuple_SetItem(args, 0, k);
	PyTuple_SetItem(args, 1, v);
    printf("Calling UI_CALLBACK\n");
	PyObject_CallObject(UI_CALLBACK, args);
}

static PyObject* stargateengine_init(
    PyObject *self,
    PyObject *args
){
    if(PyCallable_Check(args)){
        Py_XINCREF(args);
        UI_CALLBACK = args;
        //Py_XDECREF(UI_CALLBACK);
		v_set_ui_callback(pymod_ui_callback_wrapper);
    } else {
        PyErr_SetString(PyExc_ValueError, "arg 0 was not callable");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject* stargateengine_configure(
    PyObject *self,
    PyObject *args
){
    int argc = 0;
    PyObject *obj;
    PyObject *next;
    PyObject *temp_bytes;
    char *arg_cstr[3];

    if(!PyArg_ParseTuple(args, "O", &obj)){
        PyErr_SetString(PyExc_ValueError, "Failed to parse configure args");
        return NULL;
    }

    PyObject *iter = PyObject_GetIter(obj);
    if (!iter){
        PyErr_SetString(PyExc_ValueError, "Configure args are not a tuple");
        return NULL;
    }

    for(argc = 0; argc < 3; ++argc){
        next = PyIter_Next(iter);
        if (!next) {
            break;
        }

        if (PyUnicode_Check(next)) {
            temp_bytes = PyUnicode_AsEncodedString(
                next,
                "UTF-8",
                "strict"
            ); // Owned reference
            if (temp_bytes != NULL) {
                // Borrowed pointer
                arg_cstr[argc] = PyBytes_AS_STRING(temp_bytes);
                arg_cstr[argc] = strdup(arg_cstr[argc]);
                Py_DECREF(temp_bytes);
            } else {
                PyErr_SetString(
                    PyExc_ValueError,
                    "temp_bytes was NULL"
                );
                return NULL;
            }
        }
    }
    if(argc != 3){
        PyErr_SetString(PyExc_ValueError, "arg count was not 3");
        return NULL;
    }
    printf(
        "v_configure: '%s' '%s' '%s'\n",
        arg_cstr[0],
        arg_cstr[1],
        arg_cstr[2]
    );
    v_configure(
        arg_cstr[0],
        arg_cstr[1],
        arg_cstr[2]
    );
    Py_RETURN_NONE;
}

static PyObject* stargateengine_start(
    PyObject *self,
    PyObject *args
){
    const char *project_path;
    int retval;

    if (!PyArg_ParseTuple(args, "s", &project_path)){
        PyErr_SetString(PyExc_ValueError, "Failed to parse project_path");
        return NULL;
    }
    printf("Starting the engine with args: %s\n", project_path);
    retval = start_engine(project_path);
    return PyLong_FromLong(retval);
}

static PyObject* stargateengine_stop(){
    stop_engine();
    Py_RETURN_NONE;
}

static PyMethodDef StargateEngineMethods[] = {
    {
        "init",
        stargateengine_init,
        METH_O,
        "Initialize variables required before starting the engine"
    },
    {
        "configure",
        stargateengine_configure,
        METH_VARARGS,
        "Send a configure message to the engine"
    },
    {
        "start",
        stargateengine_start,
        METH_VARARGS,
        "Start the audio and MIDI hardware"
    },
    {
        "stop",
        stargateengine_stop,
        METH_VARARGS,
        "Stop the audio and MIDI hardware"
    },
    {NULL, NULL, 0, NULL}  // Sentinel
};

static struct PyModuleDef stargateenginemodule = {
    PyModuleDef_HEAD_INIT,
    "stargateengine",  // name of module
    NULL, // module documentation, may be NULL
    -1,  // size of per-interpreter state of the module
         //  or -1 if the module keeps state in global variables.
    StargateEngineMethods
};

PyMODINIT_FUNC PyInit_stargateengine(void){
    PyObject *m;

    m = PyModule_Create(&stargateenginemodule);
    if(m == NULL){
        return NULL;
    }

    StargateEngineError = PyErr_NewException(
        "stargateengine.error",
        NULL,
        NULL
    );
    Py_XINCREF(StargateEngineError);
    if(PyModule_AddObject(m, "error", StargateEngineError) < 0){
        Py_XDECREF(StargateEngineError);
        Py_CLEAR(StargateEngineError);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}

