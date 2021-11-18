#include <stdlib.h>
#include <stdlib.h>

#include "audiodsp/lib/lmalloc.h"
#include "compiler.h"

#if SG_OS == _OS_LINUX
    #include <sys/mman.h>
#endif


void small_page_aligned_alloc(void ** a_ptr, size_t a_size, int a_alignment){
#if SG_OS == _OS_LINUX
    int result = posix_memalign(a_ptr, a_alignment, a_size);
    sg_assert(
        (int)(result == 0),
        "posix_memalign failed with %i, size: %zu alignment: %i",
        result,
        a_size,
        a_alignment
    );
#else
    *a_ptr = (void*)malloc(a_size);  //unaligned, but completely portable
#endif
}

/* void lmalloc(void ** a_ptr, size_t a_size)
 *
 * Custom memory allocator
 */
void lmalloc(void ** a_ptr, size_t a_size)
{
    small_page_aligned_alloc(a_ptr, a_size, HUGEPAGE_MIN_ALIGN);
}


int USE_HUGEPAGES = 1;
int HUGE_PAGE_DATA_COUNT = 0;
huge_page_data HUGE_PAGE_DATA[50];

/* Ensure that any pointers carved out of hugepages meet minimum
 * alignment for SIMD instructions (or maybe cache lines eventually) */
char * hugepage_align(char * a_pos, int a_alignment)
{
    return a_pos + (a_alignment - ((size_t)a_pos % a_alignment));
}

int alloc_hugepage_data()
{
#if SG_OS == _OS_LINUX
    huge_page_data * f_data = &HUGE_PAGE_DATA[HUGE_PAGE_DATA_COUNT];
    f_data->start = (char*)mmap(NULL, HUGEPAGE_ALLOC_SIZE,
        PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS |
        MAP_POPULATE | MAP_HUGETLB, -1, 0);
    if(f_data->start == MAP_FAILED)
    {
        log_info(
            "Attempt to allocate hugepages failed, falling back to "
            "normal pages"
        );
        USE_HUGEPAGES = 0;
        return 0;
    }
    log_info("Successfully allocated 100MB of hugepages");
    ++HUGE_PAGE_DATA_COUNT;
    f_data->pos = hugepage_align(f_data->start, HUGEPAGE_MIN_ALIGN);
    f_data->end = f_data->start + HUGEPAGE_ALLOC_SIZE;
#endif

    return 1;
}

/* Only use for things that do not free their memory and get reclaimed
   when the process goes away.
 */

void hp_aligned_alloc(void ** a_ptr, size_t a_size, int a_alignment)
{
#if SG_OS == _OS_LINUX
    if(USE_HUGEPAGES)
    {
        if(!HUGE_PAGE_DATA_COUNT && !alloc_hugepage_data())
        {
            small_page_aligned_alloc(a_ptr, a_size, a_alignment);
            return;
        }

        // TODO:  Allocate huge pages just for this that can be
        // munmapped...
        if(a_size >= HUGEPAGE_ALLOC_SIZE)
        {
            small_page_aligned_alloc(a_ptr, a_size, a_alignment);
            return;
        }

        int f_i;
        for(f_i = 0; f_i < HUGE_PAGE_DATA_COUNT; ++f_i)
        {
            huge_page_data * f_data = &HUGE_PAGE_DATA[f_i];
            if((f_data->end - f_data->pos) > a_size)
            {
                *a_ptr = f_data->pos;
                f_data->pos = hugepage_align(a_size + f_data->pos, a_alignment);
                return;
            }
        }

        if(alloc_hugepage_data())
        {
            huge_page_data * f_data = &HUGE_PAGE_DATA[f_i];

            *a_ptr = assume_aligned(f_data->pos, a_alignment);

            f_data->pos = hugepage_align(a_size + f_data->pos, a_alignment);
        }
        else
        {
            small_page_aligned_alloc(a_ptr, a_size, a_alignment);
        }
    }
    else
    {
        small_page_aligned_alloc(a_ptr, a_size, a_alignment);
    }

#else
    small_page_aligned_alloc(a_ptr, a_size, a_alignment);
#endif

}

void hpalloc(void ** a_ptr, size_t a_size)
{
    hp_aligned_alloc(a_ptr, a_size, HUGEPAGE_MIN_ALIGN);
}

void clalloc(void ** a_ptr, size_t a_size)
{
    hp_aligned_alloc(a_ptr, a_size, CACHE_LINE_SIZE);
}

