/*
https://github.com/Davipb/utf8-utf16-converter

Copyright 2019 Davipb

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

#pragma once
#include <stdint.h>
#include <stddef.h>


typedef uint8_t utf8_t; // The type of a single UTF-8 character
typedef uint16_t utf16_t; // The type of a single UTF-16 character

/*
 * Converts a UTF-16 string to a UTF-8 string.
 *
 * utf16:
 * The UTF-16 string, not null-terminated.
 *
 * utf16_len:
 * The length of the UTF-16 string, in 16-bit characters.
 *
 * utf8:
 * The buffer where the resulting UTF-8 string will be stored.
 * If set to NULL, indicates that the function should just calculate
 * the required buffer size and not actually perform any conversions.
 *
 * utf8_len:
 * The length of the UTF-8 buffer, in 8-bit characters.
 * Ignored if utf8 is NULL.
 *
 * return:
 * If utf8 is NULL, the size of the required UTF-8 buffer.
 * Otherwise, the number of characters written to the utf8 buffer.
 *
 */
size_t utf16_to_utf8(
    utf16_t const* utf16, size_t utf16_len,
    utf8_t* utf8,         size_t utf8_len
);

/*
 * Converts a UTF-8 string to a UTF-16 string.
 *
 * utf8:
 * The UTF-8 string, not null-terminated.
 *
 * utf8_len:
 * The length of the UTF-8 string, in 8-bit characters.
 *
 * utf16:
 * The buffer where the resulting UTF-16 string will be stored.
 * If set to NULL, indicates that the function should just calculate
 * the required buffer size and not actually perform any conversions.
 *
 * utf16_len:
 * The length of the UTF-16 buffer, in 16-bit characters.
 * Ignored if utf16 is NULL.
 *
 * return:
 * If utf16 is NULL, the size of the required UTF-16 buffer,
 * in 16-bit characters.
 * Otherwise, the number of characters written to the utf8 buffer, in
 * 16-bit characters.
 *
 */
size_t utf8_to_utf16(
    utf8_t const* utf8, size_t utf8_len,
    utf16_t* utf16,     size_t utf16_len
);
