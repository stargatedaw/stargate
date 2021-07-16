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

#ifndef LMALLOC_H
#define LMALLOC_H

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#include "compiler.h"

#ifdef __linux__
    #include <sys/mman.h>
#endif


//allocate 100MB at a time and slice it up on request
#define HUGEPAGE_ALLOC_SIZE (1024 * 1024 * 100)
#define HUGEPAGE_MIN_ALIGN 16

typedef struct
{
    char * start;
    char * pos;
    char * end;
}huge_page_data;

/* void lmalloc(void ** a_ptr, size_t a_size)
 *
 * Custom memory allocator
 */
void lmalloc(void**, size_t);
void small_page_aligned_alloc(void ** a_ptr, size_t a_size, int a_alignment);

extern int USE_HUGEPAGES;
extern int HUGE_PAGE_DATA_COUNT;
extern huge_page_data HUGE_PAGE_DATA[50];

/* Ensure that any pointers carved out of hugepages meet minimum
 * alignment for SIMD instructions (or maybe cache lines eventually) */
char * hugepage_align(char * a_pos, int a_alignment);
int alloc_hugepage_data();

/* Only use for things that do not free their memory and get reclaimed
   when the process goes away.
 */
void hp_aligned_alloc(void ** a_ptr, size_t a_size, int a_alignment);
void hpalloc(void ** a_ptr, size_t a_size);
void clalloc(void ** a_ptr, size_t a_size);

#endif /* LMALLOC_H */

