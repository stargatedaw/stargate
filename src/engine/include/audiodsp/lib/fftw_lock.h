/*
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#ifndef FFTW_LOCK_H
#define FFTW_LOCK_H

#include <pthread.h>
#include "compiler.h"


extern pthread_mutex_t FFTW_LOCK;

#endif /* FFTW_LOCK_H */

