#include "compiler.h"
#include "_main.h"


#if SG_OS == _OS_WINDOWS
    #include <shlwapi.h>
    #include <windows.h>

    int main(){
	int argc;
	LPWSTR* argv = CommandLineToArgvW(GetCommandLine(), &argc);
        return _main(argc, argv);
    }
#else
    NO_OPTIMIZATION int main(int argc, char** argv){
        return _main(argc, argv);
    }
#endif

