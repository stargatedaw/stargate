#ifndef CDS_COMPARATOR_H
#define CDS_COMPARATOR_H

/* Less-Than, Greater-Than, Equal-To comparator function
 *
 * A function that accepts a pointer to 2 different instances of
 * the type associated with this data structure, and returns:
 * * -1 if the first is less than the 2nd
 * *  0 if the first is equal to the 2nd
 * *  1 if the first is greater than the 2nd
 * */
typedef int (*CDSComparatorLTGTET)(void*, void*);

/* Comparator function to determine if 2 objects (potentially of different
 * types) match.
 * Arg 1:   A pointer to the object being stored in the data structure
 * Arg 2:   A pointer to the arbitrary object passed from the calling code
 *          to the data structure method's "match" argument
 * @return: 1 if the objects match, 0 if not
 */
typedef int (*CDSComparatorMatch)(void*, void*);

#endif
