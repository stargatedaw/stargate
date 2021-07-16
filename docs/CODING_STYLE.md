# Coding Style
Please adhere to the style described in this document when adding new code.
Note that some of the code is older and does not follow these conventions,
any lines of code that you modify should be brought into compliance with
the coding style guide.

# Casing
- class or struct identifier: CamelCase, MyClassName
- function, method, variable: use\_underscores, my\_var\_name
- global variable, C `#define`: ALL\_CAPS, GLOBAL\_VARIABLE, C\_MACRO

# Wrap lines at 80 characters
Always.

## Functions
If defining or calling a function that will be more than 80 characters and/or
has more than 2 arguments (or any keyword arguments in Python), use this
convention:
```python
my_func(
    'arg1',
    2,
    keywordarg='somevalue',
)
```
```c
my_func(
    "arg1",
    2,
    &third_arg
);
```

## If statements
Complex if statements should be written like this:
```python
if(
    condition1 is None
    or (
        condition2 != 0
        and
        condition3 > condition4
    )
):
    ...
```
```c
if(
    condition1 == 1
    || (
        condition2 != 0
        &&
        condition3 > condition4
    )
){
    ...
}
```
