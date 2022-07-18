#ifndef CDS_BYTESTR_H
#define CDS_BYTESTR_H

#include <stddef.h>

#include "./types.h"

/* Generic byte string
 *
 * @data:     The underlying string, null-terminated for compatibility with
 *            C stdlib functions
 * @len:      The length of the string
 * @freeDAta: 1 to free @data when the byte string is freed, 0 to not free
 */
struct CDSByteStr{
    char*  data;
    size_t len;
    char   freeData;
};

/* Instantiate a pointer to a new byte string on the heap
 *
 * @data:     The string data
 * @assign:   1 to assign @data to this string, 0 to copy @data to this string
 * @freeDAta: 1 to free @data when the string is freed, 0 to not free @data.
 *            This is ignored and set to 1 regardless if @assign is 0
 */
struct CDSByteStr* CDSByteStrNew(
    char* data,
    char assign,
    char freeData
);

/* Initialize an existing string on the heap or stack
 *
 * @self:     The string to initialize
 * @data:     The string data
 * @assign:   1 to assign @data to this string, 0 to copy @data to this string
 * @freeDAta: 1 to free @data when the string is freed, 0 to not free @data.
 *            This is ignored and set to 1 regardless if @assign is 0
 */
void CDSByteStrInit(
    struct CDSByteStr* self,
    char* data,
    char assign,
    char freeData
);

/* Free a byte string and it's underlying data
 *
 * @self:     The string to free
 * @freeData: 1 to also call free on @self, otherwise 0
 */
void CDSByteStrFree(
    struct CDSByteStr* self,
    int freePtr
);

/* Create a slice of another string
 *
 * This is similar to Python slices, with the main difference that @end is
 * inclusive, for example:
 *    s = "abcde"
 *    Python:
 *      s[1:-1] == "bcd"
 *    libcds:
 *      Slice(self, 1, -1, 1) == "bcde"
 *
 * @self:  The string to create a slice from
 * @start: The index of @self to start slicing from.
 *         Must be >= @end if @step > 0, else must be less than @end
 *         Negative indieces will wrap to the end of the string.
 * @end:   The index of @self to stop slicing at (inclusive)
 *         Negative indieces will wrap to the end of the string.
 * @step:  1 to copy every char, 2 to copy every other char, -1 to copy every
 *         char backwards (@start must be >= @end), etc...
 */
struct CDSByteStr* CDSByteStrSlice(
    struct CDSByteStr* self,
    long start,
    long end,
    long step
);

/* Return a string that is joined from a list of strings, ie:
 *     join(", ", ["a", "b", "c"]) -> "a, b, c"
 *
 * @self:    The string to join on, an empty string will simply concatenate
 *           the strings in @strings
 * @strings: The list of strings to join
 */
struct CDSByteStr* CDSByteStrJoin(
    struct CDSByteStr* self,
    struct CDSList*    strings
);

/* Find a substring in a string
 *
 * @self:   The string to search
 * @substr: The string to look for
 * @start:  The starting index of @self to search from
 * @return: The index of the first occurrence of the substring,
 *          or -1 if not found
 */
long CDSByteStrSearch(
    struct CDSByteStr* self,
    struct CDSByteStr* substr,
    long start
);

/* Check if a string starts with another string
 *
 * @self:   The string to check if starts with @substr
 * @substr: The string to check if @self starts with
 * @return: 1 if @self starts with @substr, else 0
 */
int CDSByteStrStartsWith(
    struct CDSByteStr* self,
    struct CDSByteStr* substr
);

/* Check if a string ends with another string
 *
 * @self:   The string to check if ends with @substr
 * @substr: The string to check if @self ends with
 * @return: 1 if @self ends with @substr, else 0
 */
int CDSByteStrEndsWith(
    struct CDSByteStr* self,
    struct CDSByteStr* substr
);

/* Return a new string with any ' ', '\t', '\n', '\r' chars stripped from
 * the beginning and end
 *
 * @self: The string to strip
 */
struct CDSByteStr* CDSByteStrStrip(
    struct CDSByteStr* self
);

#endif
