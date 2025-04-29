## Beautiful Code

This document is available here: [https://wiki.lustre.org/Lustre_Coding_Style_Guidelines](https://wiki.lustre.org/Lustre_Coding_Style_Guidelines)

_A note from Eric Barton, a Lustre pioneer:_

More important than the physical layout of code (which is covered in detail below) is the idea that the code should be _beautiful_ to read.

What makes code beautiful to me? Fundamentally, it's readability and obviousness. The code must not have secrets but should flow easily, pleasurably and _accurately_ off the page and into the mind of the reader.

How do I think beautiful code is written? Like this...

-   The author must be confident and knowledgeable and proud of her work. She must understand what the code should do, the environment it must work in, all the combinations of inputs, all the valid outputs, all the possible races and all the reachable states. She must grok it.

-   Names must be well chosen. The meaning a human reader attaches to a name can be orthogonal to what the compiler does with it, so it's just as easy to mislead as it is to inform. "Does exactly what it says on the tin" is a popular UK English expression describing something that does _exactly_ what it tells you it's going to do, no more and no less. For example, if I open a tin labeled "soap", I expect the contents to help me wash and maybe even smell nice. If it's no good at removing dirt, I'll be disappointed. If it removes the dirt but burns off a layer of skin with it, I'll be positively upset. The name of a procedure, a variable or a structure member should tell you something informative about the entity without misleading - just "what it says on the tin".

-   Names must be well chosen. Local, temporary variables can almost always remain relatively short and anonymous, while names in global scope must be unique. In general, the wider the context you expect to use the name in, the more unique and informative the name should be. Don't be scared of long names if they help to `make_the_code_clearer`, but `do_not_let_things_get_out_of_hand` either - we don't write COBOL. Related names should be obvious, unambiguous and avoid naming conflicts with other unrelated names, e.g. by using a consistent prefix. This applies to all API procedures (if not all procedures period) within a given subsystem. Similarly, unique member names for global structures, using a prefix to identify the parent structure type, helps readability.

-   Names must be well chosen. Don't choose names that are easily confused - especially not if the compiler can't even tell the difference when you make a spelling mistake. `i` and `j` aren't the worst example - `rq_reqmsg` and `rq_repmsg` are much worse (and taken from our own code!!!). "Generic" variable names like `flags` and `mode` are easily mistaken between different parts of the code and should be avoided.

-   Names must be well chosen. I can't emphasize this issue enough - I hope you get the point.

-   Assertions must be used intelligently. They combine the roles of _active comment_ and _software fuse_. As an _active comment_ they tell you something about the program that you can trust more than a comment. And as a _software fuse_, they provide fault isolation between subsystems by letting you know when and where invariant assumptions are violated. Overuse must be avoided - it hurts performance without helping readability - and any other use is just plain wrong. For example, assertions must **never** be used to validate data read from disk or the network. Network and disk hardware _does_ fail and Lustre has to handle that - it can't just crash. The same goes for user input. Checking data copied in from userspace with assertions just opens the door for a denial of service attack.

-   Formatting and indentation rules should be followed intelligently. The visual layout of the code on the page should lend itself to being read easily and accurately - it just looks clean and good.
    -   Separate "ideas" should be separated clearly in the code layout using blank lines that group related statements and separate unrelated statements.
    -   Procedures should not ramble on. You must be able to take in the meaning of a procedure without scrolling past page after page of code or parsing deeply nested conditionals and loops. The 80-column rule is there for a reason.
    -   Declarations are easier to refer to while scanning the code if placed in a block locally to, but visually separate from, the code that uses them. Readability is further enhanced by limiting variable declarations to one per line and avoiding complex initializations in the declaration that may be missed.
    -   Parameters in multi-line procedure calls should be aligned so that they are visually contained by their brackets.
    -   Brackets should be used in complex expressions to make operator precedence clear, but not excessively.
    -   Formatting and indentation rules should not be followed slavishly. If you're faced with either breaking the 80-chars-per-line rule or the parameter indentation rule or creating an obscure helper function, then the 80-chars-per-line rule might have to suffer. The overriding consideration is how the code reads.

I could go on, but I hope you get the idea. Just think about the poor reader when you're writing, and whether your code will convey its meaning naturally, quickly and accurately, without room for misinterpretation.

I didn't mention _clever_ as a feature of beautiful code because it's only one step from _clever_ to _tricky_ - consider...

```
t = a; a = b; b = t; /* dumb swap */
a ^= b; b ^= a; a ^= b; /* clever swap */

```

You could feel quite pleased that the clever swap avoids the need for a local temporary variable - but is that such a big deal compared with how quickly, easily and accurately the reader will read it? This is a very minor example which can almost be excused because the "cleverness" is confined to a tiny part of the code. But when _clever_ code gets spread out, it becomes much harder to modify without adding defects. You can only work on code without screwing up if you understand the code _and_ the environment it works in completely. Or to put it more succinctly...

> _Debugging is twice as hard as writing the code in the first place. Therefore, if you write the code as cleverly as possible, you are, by definition, not smart enough to debug it._ - Brian W. Kernighan

IMHO, beautiful code helps code quality because it improves communication between the code author and the code reader. Since everyone maintaining and developing the code is a code reader as well as a code author, the quality of this communication can lead either to a virtuous circle of improving quality, or a vicious circle of degrading quality. You, dear reader, will determine which.

## Style and Formatting Guidelines

All of our rules for formatting, wrapping, parenthesis, brace placement, etc., are derived from the Linux kernel rules, which are basically K&R style. Some of these rules are automatically verified at commit time by the `contrib/scripts/checkpatch.pl` script (formerly `build/checkpatch.pl`) included with newer versions of the Lustre code, but many depend on the good judgment of the coder and inspector. Note that there is also Lustre Script Coding Style that describes the formatting for shell scripts used for userspace utilities and testing.


### Whitespace and Comments

Whitespace gets its own section because it is critical to helping the reader understand the logic of the code, and if there are inconsistencies between the whitespace used by different coders it can lead to confusion and hidden defects. Please ensure that you comply with the guidelines in this section to avoid these issues. We've included default formatting rules for emacs and vim to help make it easier.

#### Use Tabs Instead of Spaces

-   Tabs should be used for indentation in all `lustre/,` `lnet/` and `libcfs/` files, including test scripts. This matches the upstream Linux kernel coding style, and is the default method of code indentation.
-   This is being done in order to facilitate code integration with the Linux kernel. All patches should be submitted using tabs for ALL modified lines in the patch (`checkpatch.pl` will complain if not). If there are 6 or fewer lines using spaces for indentation between two lines changed by a patch, or between modified lines and the start or end of the function/structure or a nearby tab-indented line, then \*all\* of the in-between lines should also have the indentation changed to use tabs. Similarly, if there are only a handful of lines (6-8) remaining in a modified function or test that are still using spaces for indentation, convert \*all\* of the lines in that function or test to use tabs. In this manner, we can migrate the remaining chunks of code over to tabs without having huge patches breaking the commit history of every line of code, and also avoid breaking code that is in existing branches/patches that still need to merge. The conversion to tabs is 95% complete in the 2.15.0 release, so the preference is to convert more lines to tabs rather than just the minimum, including entire modified functions when practical.

-   Tabs are preferred to align variable names in **structure and enum declarations** and their descriptive comments. This may _temporarily_ misalign them with other variable names in the structure that are using spaces for indentation, or consider fixing up the whole struct in the same patch if there aren't too many of them. In some cases (long variable names, long comments, nested unions) it isn't practical to use full tabs to align the fields, so spaces can be used for partial indentation.
-   Only a **single space** should separate the variable type and variable name for **local function declarations**. This is to match upstream Linux kernel coding style.
-   All lines should wrap at 80 characters. This is to avoid the need to have extra-wide terminal windows for the few lines of code that exceed 80 columns, and avoids nesting functions and conditionals too deeply. Exceptions to this rule in the upstream kernel include long text strings. If it's getting too hard to wrap at 80 characters, you probably need to rearrange conditional order or break it up into more functions.

```
right:
void func_helper(...)
{
        struct foobar_counter *foo;
        unsigned long last;
        int rc = 0;
 
        do_sth2_1;
 
        if (cond3)
                do_sth_which_needs_a_very_long_line(and, lots, of, arguments);
 
        do_sth2_2;
}
 
void func(...)
{
        long first;
        int i;
 
        if (!cond1) {
                CERROR("some error message that is long but kept on one line\n");
                return;
        }
 
        do_sth1_1;
 
        if (cond 2)
                func_helper(...)
 
        do_sth1_2;
}

wrong:
void func(...)
{
        int rc;
        struct foobar_counter *foo;
        unsigned long last;
 
        if (cond1) {
                do_sth1_1;
                if (cond2) {
                        do_sth2_1;
                        if (cond3) {
                                do_sth_which_needs_a_very_long(and, lots, of, arguments);
                                CERROR("some error message "
                                       "that is continued\n");
                        }
                        do_sth2_2;
                }
                do_sth1_2;
        }
}


```

-   Do not include spaces or tabs on blank lines or at the end of lines. Please ensure you remove all instances of these in any patches you submit to Gerrit. You can find them with `grep` or in `vim` using the following regexps `/\[ \t\]$/` or use git `git diff --check`. Alternatively, if you use `vim`, you can put this line in your `.vimrc` file, which will highlight whitespace at the end of lines and spaces followed by tabs in indentation (only works for C/C++ files) `let c_space_errors=1`. Or you can use this command, which will make tabs and whitespace at the end of lines visible for all files (but a bit more discretely) `set list listchars=tab:>\ ,trail:$`. In `emacs`, you can use `(whitespace-mode)` or `(whitespace-visual-mode)` depending on the version. You could also consider using `(flyspell-prog-mode)`.
-   Functions that are more than a few lines long should be declared with a leading comment block that describes what the function does, any assumptions for the caller (locks already held, locks that should _not_ be held, etc), and return values. Lustre uses the [DOxygen](https://en.wikipedia.org/wiki/Doxygen) markup style for formatting the code comments, as shown in the example here. `\a argument` can be used in the descriptive text to name a function argument. `\param argument definition` should be used to define each of the function parameters, and can be followed by `[in]`, `[out]`, or `[in,out]` to indicate whether each parameter is used for input, output, or both. `\retval` should be used to define the function return values.

```
right:
/**
 * Initialize or update CLIO structures for the regular file \a inode
 * when new meta-data arrives from the server.
 *
 * \param[in] inode regular file inode
 * \param[in] md    new file metadata from MDS
 * - the \a md->body must have a valid FID (valid & OBD_MD_FLID)
 * - allocates cl_object if necessary,
 * - updated layout, if object was already here.
 *
 * \retval 0 if the inode was initialized/updated properly
 * \retval negative errno if there was a problem
 */
int cl_file_inode_init(struct inode *inode, struct lustre_md *md)
{

right:
/**
 * Implements cl_page_operations::cpo_make_ready() method for Linux.
 *
 * This is called to yank a page referred to by \a slice from the transfer
 * cache and to send it out as a part of transfer. This function try-locks
 * the page. If try-lock failed, page is owned by some concurrent IO, and
 * should be skipped (this is bad, but hopefully rare situation, as it usually
 * results in transfer being shorter than possible).
 *
 * \param[in] env     lu environment for large temporary stack variables
 * \param[in] slice   per-layer page structure being prepared
 *
 * \retval    0       success, page can be placed into transfer
 * \retval -EAGAIN    page either used by concurrent IO or was truncated. Skip it.
 */
static int vvp_page_make_ready(const struct lu_env *env,
                               const struct cl_page_slice *slice)
{

wrong:
 
/* finish inode */
void
cl_inode_fini(struct inode *inode)
{


```

#### Misc

-   Don't use `inline` unless you're doing something so performance critical that the function call overhead will make a difference -- in other words - almost never. It makes debugging harder and overuse can actually hurt performance by causing instruction cache thrashing or crashes due to stack overflow.
-   Do not use `typedef` for new declarations, as this hides the type of a field for very little benefit, and is against Linux kernel coding stye. _Never_ typedef pointers, as the `*` makes C pointer declarations obvious. Hiding it inside a typedef just obfuscates the code.
-   Do not embed assignments inside Boolean expressions or error messages. Although this can make the code one line shorter, it doesn't make it more understandable and you increase the risk of confusing `=` with `==` or getting operator precedence wrong if you skimp on brackets. It's even easier to make mistakes when reading the code, so it's much safer simply to avoid it altogether.

```
right:
        ptr = malloc(size);
        if (ptr) {
                ...

wrong:
        if ((ptr = malloc(size)) != NULL) {
                ...


```

#### Conditional Expressions

-   Conditional expressions should be implicit for Boolean, non-Boolean, and pointer expressions. However, consecutive conditional checks should not mix implicit and explicit expressions. Explicit conditional expressions for function return values are still preferred in all cases.

```
right:
        void *pointer = NULL;
        bool writing = false;
        int retval = 0;
 
        if (!writing &&     /* not writing? */
            pointer &&      /* valid pointer? */
            !reval)         /* no error is returned? */
                do_this();

right:
        if (retval < 0)
              do_something();

        if (retval == 0) 
              do_something_else();

right:
        if (strcmp(...) == 0)
              do_something();

wrong:
        if (writing == 0 &&        /* not writing? */
            pointer != NULL &&     /* valid pointer? */
            retval == 0)           /* no error is returned? */
               do_that();

wrong:
        if (retval < 0)
              do_something();

        if (!reval)         /* avoid mixing implicit and explicit expressions */
              do_something_else();

wrong:
        if (!strcmp(...))
              do_something();


```

-   Use parentheses to help readability and reduce the chance of operator precedence errors, but not so heavily that it is difficult to determine which parentheses are a matched pair or accidentally hide bugs (e.g., the aforementioned assignments inside Boolean expressions).

```
right:
        if (a->a_field == 3 &&
            ((bar & BAR_MASK_1) || (bar & BAR_MASK_2)))
                do this();

wrong:
        if (((a == 1) && (b == 2) && ((c == 3) && (d = 4))))
                maybe_do_this()

wrong:
        if (a->a_field == 3 || b->b_field & BITMASK1 && c->c_field & BITMASK2)
                maybe_do_this()

wrong:
        if ((((a->a_field) == 3) || (((b->b_field) & (BITMASK1)) &&
           ((c->c_field) & (BITMASK2)))))
                maybe_do_this()


```

#### Avoid Mixing NULL and ERR\_PTR()

-   Function return values should not mix `NULL` and `ERR_PTR()` values. This avoids complexity and bugs in each of the callers of that function, since `IS_ERR(ERR_PTR(NULL))` is false (i.e. `IS_ERR()` does not consider `NULL` an error).

```
right:
struct foo *foo_init()
{
        struct foo *foo;
        int rc;
 
        OBD_ALLOC_PTR(foo);
        if (!foo)
               RETURN(ERR_PTR(-ENOMEM));
 
        rc = init_foo(foo);
        if (rc) {
                OBD_FREE_PTR(foo);
                RETURN(ERR_PTR(rc));
        }
 
        RETURN(foo);
}

wrong:
struct foo *foo_init()
{
        struct foo *foo;
        int rc;
 
        OBD_ALLOC_PTR(foo);
        if (!foo)
                RETURN(NULL);
        rc = init_foo(foo);
        if (rc)
                RETURN(ERR_PTR(rc));
 
        RETURN(foo);
}


```

### Layout

-   Code can be much more readable and efficient if the simple or common actions are taken first in a set of tests. Re-ordering conditions like this also eliminates excessive nesting and helps avoid overflowing the 80-column limit.

#### No else After return

-   Do not place `else` blocks after terminal statements like `return`, `continue`, `break`, or `goto` in the `if` block.

```
right:
        list_for_each_entry(...) {
                if (!condition1) {
                        do_sth1;
                        continue;
                }
 
                do_sth2_1;
                do_sth2_2;
                ...
                do_sth2_N;
 
                if (!condition2)
                        break;
 
                do_sth3_1;
                do_sth3_2;
                if (!condition3)
                        break;
                ...
                do_sth3_N;
        }

wrong:
        list_for_each_entry(...) {
                if (condition1) {
                        do_sth2_1;
                        do_sth2_2;
                        ...
                        do_sth2_N;
                        if (condition2) {
                                do_sth3_1;
                                do_sth3_2;
                                if (condition3) {
                                        ...
                                        do_sth3_N;
                                        continue;
                                }
                        }
                        break;
                } else {
                        do_sth1;
                }
        }


```

#### Use Common Cleanup and Return for Error Handling

-   Function bodies that have complex state to clean up in case of an error should do so only once at the end of the function with a single `RETURN()`, and use `GOTO()` to jump there in case of an error:

```
right:
struct bar *bar_init(...)
{
        foo = alloc_foo();
        if (!foo)
                RETURN(-ENOMEM);
        rc = setup_foo(foo);
        if (rc)
                GOTO(free_foo, rc);
        bar = init_bar(foo);
        if (IS_ERR(bar))
                GOTO(cleanup_foo, rc = PTR_ERR(bar));
        :
        :
        RETURN(bar);
 
cleanup_foo:
        cleanup_foo(foo);
free_foo:
        free_foo(foo);
 
        return ERR_PTR(rc);
}

wrong
struct bar *bad_func(...)
{
        foo = alloc_foo();
        if (!foo)
                RETURN(NULL);
        rc = setup_foo(foo);
        if (rc) {
                free_foo(foo);
                RETURN(ERR_PTR(rc));
        bar = init_bar(foo);
        if (IS_ERR(bar)) {
                cleanup_foo(foo);
                free_foo(foo);
                RETURN(PTR_ERR(bar));
        }
        :
        :
        RETURN(bar);
}


```

#### About Variable Declarations

-   Variable should be declared one per line, type and name, even if there are multiple variables of the same type.
-   There should be one space between the variable type and the variable name to match upstream kernel coding guidelines (this is new since 2015-06 due to upstream kernel requirements).
-   For maximum readability, longer and more important declarations should be at the top, and roughly in order of usage otherwise.
-   There should always be an empty line after the variable declarations, before the start of the code.
-   There shouldn't be complex variable initializers (e.g. function calls) in the declaration block, since this may be easily missed by the reader and make it confusing to debug.

```
right:
        struct inode *dir_inode;
        int count;
        int len;
 
        len = path_name(mnt, dir_inode);
 
wrong:
        int max, count, flag;
        int len = path_name(mnt, dir_inode);
        struct inode  *dir_inode;

wrong (old style):
        int  max, count, flag;
        int                    end;
        struct inode           *dir_inode;
        struct file_operations *long_declaration 


```

-   Variable declarations should be kept to the most internal scope, if practical and reasonable, to simplify understanding of where these variables are accessed and modified, and to avoid errors of using/reusing variables that only have meaning if certain branches are used:

```
right:
        int len;
 
        if (len > 0) {
                struct inode *inode;
                int count;

                inode = iget(foo);
 
                count = inode->i_size;
 
                if (count > 32) {
                        int left = count;
 
                        :
                }
        }

wrong:
        int len = path_length(bar), count, ret;
        struct inode *inode = iget(foo);
 
        if (len > 0) {
                count = inode->i_size;
                if (count > 42)
                       ret = 0;
        } else if (len == 0) {
                ret = -ENODATA;
        } else {
                CERROR("count is bad: %d\n", count);
        }

        return ret;


```

#### Wrapping Long Lines

-   Even for short conditionals, the operation should be on a separate line:

```
right:
        if (foo)
                bar();

wrong:
        if (foo) bar();


```

-   When you wrap a line containing parenthesis, start the continued line after the parenthesis so that the expression or argument is visually bracketed.

```
right:
        variable = do_something_complicated(long_argument, longer_argument,
                                            longest_argument(sub_argument,
                                                             foo_argument),
                                            last_argument);
 
        if (some_long_condition(arg1, arg2, arg3) < some_long_value &&
            another_long_condition(very_long_argument_name,
                                   another_long_argument_name) >
            second_long_value) {
                do_something();
                ...
 
wrong:
        variable = do_something_complicated(long_argument, longer_argument,
                longest_argument(sub_argument, foo_argument),
                last_argument);
 
        if (some_long_condition(arg1, arg2, arg3) < some_long_value &&
                another_long_condition(very_long_argument_name,
                another_long_argument_name) >
                second_long_value) {
                do_something();
                ...


```

-   If you're wrapping an expression, put the operator at the end of the line. If there are no parentheses to which to align the start of the next line, just indent one more tab stop.

```
       off = le32_to_cpu(fsd->fsd_client_start) +
               cl_idx * le16_to_cpu(fsd->fsd_client_size);

```

-   Binary and ternary (but not unary) operators should be separated from their arguments by one space.

```
right:
        a++;
        b |= c;
        d = (f > g) ? 0 : 1;


```

#### Function Calls and Spaces

-   Function calls should be nestled against the parentheses, the parentheses should crowd the arguments, and one space should appear after commas:

```
right:
       do_foo(bar, baz);

wrong:
       do_foo ( bar,baz );

```

-   Put a space between if, for, while, etc. and the following parenthesis. Put a space after each semicolon in a for statement.

```
right:
        for (a = 0; a < b; a++)
        if (a < b || a == c)
        while (1)

wrong:
        for( a=0; a<b; a++ )
        if( a<b || a==c )
        while( 1 )


```

-   Opening braces should be on the same line as the line that introduces the block, except for function calls. Bare closing braces (i.e. not else or while in do/while) get their own line.

```
int foo(void)
{
        if (bar) {
                this();
                that();
        } else if (baz) {
                stuff();
        } else {
                other_stuff();
        }
     
        do {
                cow();
        } while (condition);
}


```

#### Consistent if and else Blocks

-   If one part of a compound if block has braces, all should.

```
right:
        if (foo) {
                bar();
                baz();
        } else {
                salmon();
        }

wrong:
        if (foo) {
                bar();
                baz();
        } else
                moose();


```

#### Safe Preprocessor Usage

-   When you define a macro, protect callers by placing parentheses round every parameter reference in the body.
-   Line up the backslashes of multi-line macros one tabstop from the end of the line to help readability.
-   Use a do/while (0) block with no trailing semicolon to ensure multi-statement macros are syntactically equivalent to procedure calls.

```
right:
#define DO_STUFF(a)                                     \
do {                                                    \
        int b = (a) + MAGIC;                            \
        do_other_stuff(b);                              \
} while (0)

wrong:
#define DO_STUFF(a) \
do { \
        int b = a + MAGIC; \
        do_other_stuff(b); \
} while (0);


```

-   If you write conditionally compiled code in a procedure body, make sure you do not create unbalanced braces, quotes, etc. This really confuses editors that navigate expressions or use fonts to highlight language features. It can often be much cleaner to put the conditionally compiled code in its own helper function which, by good choice of name, documents itself, and makes it transparent to the reader which kernel is being used. More importantly, it avoids increasingly complex conditional blocks that need to work with multiple kernels. The conditional blocks should preferably be written in a manner that uses the new kernel function name, so that code doesn't need to be modified again when removing support for old kernels.

```
right:
static inline int invalid_dentry(struct dentry *d)
{
#ifdef DCACHE_LUSTRE_INVALID
        return d->d_flags & DCACHE_LUSTRE_INVALID;
#else
        return d_unhashed(d);
#endif
}

int do_stuff(struct dentry *parent)
{
        if (invalid_dentry(parent)) {
                ...

wrong:
int do_stuff(struct dentry *parent
#ifdef HAVE_FOO_FEATURE
             struct foo_extra *foo)
#else
             )
#endif
{
#ifdef DCACHE_LUSTRE_INVALID
        if (parent->d_flags & DCACHE_LUSTRE_INVALID) {
#else
        if (d_unhashed(parent)) {
#endif
                ...
        }
}


```

-   If you nest preprocessor commands, use spaces to visually delineate:

```
#ifdef __KERNEL__
# include <goose>
# define MOOSE steak
#else /* !__KERNEL__ \*/
# include <mutton>
# define MOOSE prancing
#endif


```

-   For long or nested `#ifdef` blocks, include the conditional as a comment with each `#else` and `#endif` to make it clear which block is being terminated:

```
#ifdef __KERNEL__
# if HAVE_SOME_KERNEL_API
/* lots
   of
   stuff */
# endif /* HAVE_SOME_KERNEL_API */
#else /* !__KERNEL__ */
# if HAVE_ANOTHER_FEATURE
/* more
 * stuff */
# endif /* HAVE_ANOTHER_FEATURE */
#endif /* __KERNEL__ */


```

-   Single-line comments should have the leading `/*` and trailing `*/` on the same line as the comment. Multi-line comments should have the leading `/*` and trailing `*/` on their own lines, to match the upstream kernel coding style. Intermediate lines should start with a `*` aligned with the `*` on the first line:

```
/* This is a short comment */
 
/*
 * This is a multi-line comment.  I wish the line would wrap already,
 * as I don't have much to write about.
 */


```

#### Function Declarations

-   External function declarations absolutely should \*NEVER\* go into .c files. The only exception is forward declarations for static functions in the same file that can't otherwise be moved before the caller. Instead, the declaration should go into the most "local" header available (e.g. `_subsystem__internal.h` for a given subdirectory). Having external function declarations in .c files can cause very difficult to diagnose runtime bugs, because the compiler takes the local declaration as correct, can not compare it to the actual function declared in a different file, and does not have a declaration in a header to compare it against, but the linker does not check that the number and type of function arguments match.

-   Function declarations in header files should include the variable names for the parameters, so that they are self explanatory in the header without having to look at the code to see what the parameter is:

```
right:
void ldlm_lock_addref_internal(struct ldlm_lock *lock, enum ldlm_lock_mode lock_mode, int refcount, int rc);

wrong:
    void ldlm_lock_addref_internal(struct ldlm_lock *, int, int, int)


```

-   Place `EXPORT_SYMBOL()` line immediately after the function that is being exported. Having the `EXPORT_SYMBOL()` immediately following the function makes it clear to the reader whether there are users of this function outside this module and it can not be declared static.

```
int foo_stuff(int arg, char *buf)
{
        struct ldlm_lock *lock;
        int bar;
 
        do_stuff();
}
EXPORT_SYMBOL(foo_stuff);


```

#### Declaring Structures

-   Structure fields should have a common prefix derived from the structure name, so that they are easily found in the code and tag-jump works properly. This avoids problems with generic field names like page or count that have dozens or hundreds of potential matches in the code.
-   Structure and constant declarations should not be declared in multiple places. Put the struct into the most "local" header possible.
-   Structures that are passed over the wire need to be declared in `lustre_idl.h`, into the `wirecheck.c` and `wiretest.c` files, and needs to be correctly swabbed when the RPC message is unpacked. On-disk structures should be declared in `lustre_disk.h` if they are not also passed over the network. All protocol/disk structures should correctly align 64-bit values and supply explicit padding for alignment to avoid compiler-generated holes in the data structures.

-   Structure initialization should be done by field names instead of using positional arguments:

```
struct foo {
        int     foo_val;
        int     foo_flag;
        int     foo_count;
        void   *foo_ptr;
        void   *foo_bar_ptr;
        void   *foo_baz_ptr;
};

right:
void func(void *data)
{
        struct foo fooz = { .foo_val = 1, .foo_flag = 0x20, .foo_ptr = data, .foo_baz_ptr = param };
}

wrong:
void func(void *data)
{
        /* not sure which field is being initialized, breaks (maybe silently) if structure adds a new field */
        struct foo fooz = { 1, 0x20, data, param };
}


```

#### Printing Functions

-   Functions that take variable parameters for `printk()`\-style argument processing should be declared with `__attribute__ ((format (printf,,) ))` so that the format string can be verified against the argument list by GCC:

```
void _debug_req(struct ptlrpc_request *req, __u32 mask,
                struct libcfs_debug_msg_data *data, const char *fmt, ...)
        __attribute__ ((format (printf, 4, 5)));


```

### Lustre Specific Guidelines

These guidelines are more specific to Lustre and not necessarily specific to the upstream kernel.

#### Lustre Variable Types

-   The types and `printf()`/`printk()` formats used by Lustre code are:

```
__u64                %llu/%llx/%lld (unsigned, hex, signed)
__u32/int            %u/%x/%d (unsigned, hex, signed)
(unsigned)long long  %llu/%llx/%lld
loff_t               %lld after a cast to long long (unfortunately)
struct lu_fid        PFID, DFID
struct ost_id        POSTID, DOSTID


```

-   Use `list_for_each_entry()` or `list_for_each_entry_safe()` instead of `list_for_each()` followed by `list_entry()`
-   When using `sizeof()` it should be used on the variable itself, rather than specifying the type of the variable, so that if the variable changes type/size then `sizeof()` will remain correct:

```
right:
        char buf[PATH_MAX];
        int *array;
 
        OBD_ALLOC(array, 10 * sizeof(*array));
        rc = strncpy(buf, src, sizeof(buf));

wrong:
        OBD_ALLOC(array, 40);                   /* This is just a random number, who knows what it means? */
        OBD_ALLOC(array, 10 * sizeof(int));     /* silently breaks if array becomes __u64 */
        OBD_ALLOC(array, 10 * sizeof(array));   /* This is the pointer size, not array size */
        rc = strncpy(buf, src, sizeof(*buf));   /* This is the character size, not array size */


```

#### Memory Allocation

-   When allocating/freeing a single struct, use `OBD_ALLOC_PTR()` for clarity:

```
right:
        OBD_ALLOC_PTR(mds_body);
        OBD_FREE_PTR(mds_body);

wrong:
        OBD_ALLOC(mds_body, sizeof(*mds_body));
        OBD_FREE(mds_body, sizeof(*mds_body));


```

-   When allocating a large variable (pretty much anything above 8KiB, use `OBD_ALLOC_LARGE` and `OBD_FREE_LARGE()` in order to avoid allocation failures. This will first try to use `kmalloc()` for the fastest allocation, but if this fails (or is too large for `kmalloc()`) then it will fall back to using `vmalloc()` as needed. This makes it easier to see which allocations may consume a lot of RAM, and avoids errors hit on long-running systems when memory is fragmented that are not seen during short-lived test runs or right after mount.
-   When allocating/freeing an array, use `OBD_ALLOC_ARRAY()` or `OBD_ALLOC_PTR_ARRAY()` or `OBD_ALLOC_ARRAY_LARGE()` and corresponding `*FREE*()` function to avoid overflow during calculation of array size.

#### Proper use of LASSERT()

-   Do not embed operations inside assertions. If assertions are disabled for performance reasons this code will not be executed.

```
right:
        len = strcat(foo, bar);
        LASSERT(len > 0);

wrong:
        LASSERT(strcat(foo, bar) > 0);


```

#### Console Error Messages

-   Messages on the console (`CERROR()`, `CWARN()`, `LCONSOLE_*()`) should be written so they provide useful information to the \*administrator\* and/or support person in case of a \*significant event\* or \*failure condition\*. They should not print "debugging" information in cases that might be hit under normal usage or user-generated race conditions, since verbose console error messages lose the important messages in a flood of noise. Consider that there may be thousands of servers and tens of thousands of clients hitting some failure at the same time.
-   Console messages should print the Lustre device or filesystem name at the start of the message, since there are usually multiple targets running on a single server or multiple mountpoints on a client.
-   Error messages that print a numeric error value should print it at the end of the line in a consistent format using `": rc = %d\n"`. This makes it more clear what error was returned to the client/application, to make it easier to correlate server messages with application errors. This will also allow automatic replacement of the numeric error numbers with error names/strings.

```
right:
        CERROR("%s: error invoking upcall %s %s %s: rc = %d",
        CERROR("%s: cannot open/create O: rc = %d\n", obd->obd_name,rc);

wrong:
        CERROR("err %d on param %s\n", rc, ptr);
        CERROR("Can't get index (%d)\n", rc);


```

-   Error messages should also include enough information to make some useful diagnosis of the problem (e.g. FID and/or filename, client NID, actual values that caused failures, etc). Otherwise, there is little value in having printed an error, but then needing to reproduce the problem to diagnose it:

```
right:
        LCONSOLE_INFO("%s: %s now active, deleting orphans objects from "DFID" to "DFID\n",
                      obd->obd_name, obd_uuid2str(uuid), PFID(start_fid), PFID(end_fid));
        LCONSOLE_WARN("%s: new disk, initializing\n", obd->obd_name);
        CERROR("%s: unsupported incompat filesystem feature(s) %x: rc = %d\n", obd->obd_name, incompat, rc);
        CERROR("%s: cannot create root dentry: rc = %d\n", ll_get_fsname(sb, NULL, 0), rc);
        CERROR("%s: error initializing 'fid' object: rc = %d\n",
               mdd2obd_dev(m)->obd_name, rc);
        CERROR("%s: cannot start coordinator thread: rc = %d\n", mdt_obd_name(mdt), rc);

wrong:
        CERROR("Cannot get thandle\n");
        CERROR("NULL bitmap!\n");
        CERROR("invalid event\n");
        CERROR("allocation failed\n");


```

#### Configure Checks for Kernels

-   Configure checks should be annotated with the kernel version and Git commit hash (as returned by `git describe`) where the change was introduced, so that it is easier to know when the checks are obsolete and can be removed. It also simplifies efforts to investigate that change again in the future if needed.
-   Configure checks should check for the _new_ feature being added rather than the _old_ feature being removed. This ensures that the conditional code will only use the newly detected feature, and will not break if the old feature has undergone changes between different kernels and the configure check itself might fail on various older kernels (e.g. struct moved between headers that didn't affect operations in the past).
-   Configure checks can be written to run in parallel and in serial. The result of serial test runs can be used immediately following the test running. Parallel tests run significanly (~5x) faster and are preferred where possible. Since configure test results can affect future tests some parallel tests are run early (See: LIBCFS\_SRC\_HAVE\_MMAP\_LOCK). In general parallel tests are preferred.

**right parallel:**

```
 #
 # LIBCFS_HAVE_MMAP_LOCK
 #
 # kernel 5.8 commit v5.8-rc1~83^2~24
 #   mmap locking API: rename mmap_sem to mmap_lock
 #
 AC_DEFUN([LIBCFS_SRC_HAVE_MMAP_LOCK], [
 LB2_LINUX_TEST_SRC([mmap_write_lock], [
 #include <linux/mm.h>
 ],[
 mmap_write_lock(NULL);
 ],[])
 ])
 AC_DEFUN([LIBCFS_HAVE_MMAP_LOCK], [
 LB2_MSG_LINUX_TEST_RESULT([if mmap_lock API is available],
 [mmap_write_lock], [
 AC_DEFINE(HAVE_MMAP_LOCK, 1,
 [mmap_lock API is available.])
 ])
 ]) # LIBCFS_HAVE_MMAP_LOCK


```

**right serial:**

```
#
# LIBCFS_HAVE_MMAP_LOCK
#
# kernel 5.8 commit v5.8-rc1~83^2~24
#   mmap locking API: rename mmap_sem to mmap_lock
#
AC_DEFUN([LIBCFS_HAVE_MMAP_LOCK], [
LB_CHECK_COMPILE([if mmap_lock API is available],
  [mmap_write_lock], [
#include <linux/mm.h>
],[
mmap_write_lock(NULL);
],[
AC_DEFINE(HAVE_MMAP_LOCK, 1,
[mmap_lock API is available.])
])
])


```

**wrong:**

```
#
# LIBCFS_HAVE_MMAP_LOCK
#
AC_DEFUN([LIBCFS_SRC_HAVE_MMAP_LOCK], [
LB2_LINUX_TEST_SRC([mmap_write_lock], [
#include <linux/mm.h>
],[
mmap_write_lock(NULL);
],[])
])
AC_DEFUN([LIBCFS_HAVE_MMAP_LOCK], [
LB2_MSG_LINUX_TEST_RESULT([if mmap_lock API is available],
[mmap_write_lock], [
AC_DEFINE(HAVE_MMAP_LOCK, 1,
[mmap_lock API is available.])
])
]) # LIBCFS_HAVE_MMAP_LOCK


```

-   For Autoconf macros, follow the style suggested in the autoconf manual.

```
AC_CACHE_CHECK([for EMX OS/2 environment], [ac_cv_emxos2],
[AC_COMPILE_IFELSE([AC_LANG_PROGRAM([], [return __EMX__;])],
                   [ac_cv_emxos2=yes],
                   [ac_cv_emxos2=no])])


```

or alternately:

```
AC_CACHE_CHECK([for EMX OS/2 environment],
               [ac_cv_emxos2],
               [AC_COMPILE_IFELSE([AC_LANG_PROGRAM([],
                                                   [return __EMX__;])],
                                  [ac_cv_emxos2=yes],
                                  [ac_cv_emxos2=no])])


```

## Bash Style

-   Bash is a programming language. It includes functions. Shell code outside of functions is effectively code in an implicit main() function. An entire function should be fully seen on one page (~70-90 lines) and be readily comprehensible. If you have any doubts, then it is too complicated. Make it easier to understand by separating it into subroutines.
-   The total length of a line (including comment) must not exceed 80 characters. Take advantage of bash's `+=` operator for constants or linefeed escapes `\`.
    -   Lines can be split without the need for a linefeed escape after `|`, `||`, `&` and `&&` operators.
-   The indentation must use 8-column tabs and not spaces. For line continuation, an additional tab should be used to indent the continued line, or align after `[` or `(` for continued logic operations.
-   Comments are just as important in a shell script as in C code.
-   Use `$(...)` instead of `` `...` `` for subshell commands:
    -   `$(...)` is easier to see the start and end of the subshell command
    -   `$(...)` avoids confusion between `'...'` and `` `...` `` with a small font
    -   `$(...)` can be nested
-   Use the subshell syntax only when you have to:
    -   When you need to capture the output of a separate program
    -   Using the construct with functions leads to stray output and/or convoluted code struggling to avoid output pollution
    -   It is more computationally efficient to not fork() the Bash process. Bash is slow enough already.
-   Use "here string" like `function <<<$var` instead of `echo $var | function` to avoid forking a subshell and pipe
-   Use file arguments like `awk '...' $file` or input redirection like `function << $file` instead of a useless use of `cat`
-   Use built-in Bash Parameter Expansion for variable/string manipulation rather than forking `sed/tr`:
    -   Use `${VAR#prefix}` or `${VAR%suffix}` to remove `prefix` or `suffix` respectively
    -   Use `${VAR/pattern/string}` to replace `pattern` with string
-   Avoid use of "`grep foo | awk '{ print $2 }'`" since "`awk '/foo/ { print $2 }'` works just as well and avoids a separate fork + pipe
-   If a variable is intended to be used as a boolean, then it must be assigned as follows:

```
        local mybool=false         # or true
        
        if $mybool; then
                do_stuff
        fi
```

-   for loops it is possible to avoid a subshell for `$(seq 10)` using the built-in iterator for fixed-length loops:
    -   Unfortunately, `{1..$var}` does not work, so use `(( ... ))` arithmetic operator

```
        for ((i=0; i < $var; i++)); do
                something_with $i
        done
```

-   Use `export FOOBAR=val` instead of `FOOBAR=val; export FOOBAR` for clarity and simplicity
-   Use `[[ expr ]]` instead of `[ expr ]`
    -   The `[[` test understands regular expression matching with the `=~` operator
    -   The easiest way to use it is by putting the expression in a variable and expanding it after the operator without quotes.

-   Use `(( expr ))` instead of `[ expr ]` or `let expr` when evaluating numerical expressions
    -   This can include mathematical operators like `$((...))`
    -   Will properly compare numeric values, unlike `[...]` that is comparing strings
```
        # wrong: this is surprisingly "true" because '5' > '3' and the rest of the string is ignored
        [[ 5 > 33 ]] && echo "y" || echo "n"
        y
        # right: this is what you expect for the '>' operator
        (( 5 > 33 )) && echo "y" || echo "n"
        n
```
-   -   This uses normal `<=`, `>=`, `==` comparisons instead of `-lt`, `-eq`, `-gt`
    -   Can use `for (( i=0; i <= END; i++ )); do` and other numerical expressions instead of an external subshell for `seq`

-   Use `$((...))` for arithmetic expressions instead of `expr ...`
    -   No need for `$` when referencing variable names inside `$((...))`
    -   `$((...))` can handle hex values and common math operators
-   Error checks should prefer the form `[[ check ]] || action` to avoid leaving a dangling "false" on the return stack
    -   Otherwise, `[[ check ]] && action` will leave a dangling "false" on the stack if `check` fails and an immediately following return/end of function will return an error

## Test Framework

### Variables

-   Names of variables local to current test function which are not exported to the environment should be declared with "`local`" and use lowercase letters
-   Names of global variables or variables that exported to the environment should be UPPERCASE letters
-   Use `$TMP/` for temporary non-Lustre files instead of `/tmp/`
-   Use `$SECONDS` to get the current time when measuring test _durations_ instead of `$(date +%s)` fork+exec:
```
    local start=$SECONDS
    
    do something
    local elapsed=$((SECONDS - start))
```

### Functions

-   Each function must have a section describing what it does and explain the list of parameters
```
# One line description of this function's purpose
#
# More detailed description of what the function is doing if necessary
#
# usage: function_name [--option argument] {required_argument} ...
# option: meaning of "option" and its argument
# required_argument: meaning of "required_argument"
# 
# expected output and/or return value(s)
```
-   Function arguments should be given local variable names for clarity, rather than being used as `$1 $2 $3` in the function

```
    local facet=$1
    local file="$2"
    local size=$3
```
-   Use `sleep 0.1` instead of `usleep 100000`, since `usleep` is RHEL-specific

### Tests and Libraries

-   To avoid clustering a single `test-framework.sh` file, there should be a `<test-lib>.sh` file for each test that contains specific functions and variables for that test.
-   Any functions, variables that global to all tests should be put in `test-framework.sh`
-   A test file only need to source `test-framework.sh` and necessary `<test-lib>.sh` file

### Subtests

-   test files should be named `$tfile` for the filename, or base name like `$tfile.1` or `$tfile.source` to simplify debugging
-   test directories should be named `$tdir`, and should be used if a large number of files are created for the subtest
-   small/few test files/dirs do not need to be explicitly deleted at the end of the test, that is done by test-framework.sh at the start/end of each test script
-   large (over 1MB)/many (over 50) test files/dirs in a subtest should be cleaned up explicitly with a `stack_trap` so that they are always cleaned up even if the test exits with an error, and do not fill the test filesystem
```
    stack_trap "rm -f $DIR/$tfile.big"
    fallocate -l 100M $DIR/$tfile.big || error "$tfile.big create failed"
    
    stack_trap "unlinkmany $DIR/$tdir/$tfile- 1000"
    createmany -o $DIR/$tdif/$tfile- 1000 || error "$tfile creation failed"
```
-   creating large test files is by far the fastest with "fallocate" \*when supported\* (ldiskfs only), as determined by `check_set_fallocate`
-   use `test_mkdir` to add some variety to directory creation (random local, striped, remote) if directory location is not critical to the test
-   ensure that directory location and MDS facet are aligned. Since 2.14.54 directories may be created on any MDT, so "`do_facet mds1 ...`" may be on the wrong MDS.
-   Use "`mkdir_on_mdt0 $DIR/$tdir`" to create directories on MDT0000 for use with `mds1`, or "`$LFS getdirstripe -m $DIR/$tdir`" to determine MDT index, and "`mds$((idx+1))`" for facet name.
-   the `error` messages in a subtest should be unique so that it is easy to determine which check failed
```
    lfs migrate -c3 $tfile || error "'lfs migrate -c3' failed"
    lfs migrate -c1 $tfile || error "second 'lfs migrate -c1' failed"
```
-   use `skip` to skip subtests that should not run because of permanent functional deficiency (e.g. non-existent functionality in backing filesystem, older version of client/server, wrong configuration)
```
    (( MDS1_VERSION_CODE >= $(version_code 2.15.53) )) ||
        skip "need MDS >= 2.15.53 to check foobar works"
    [[ $mds1_FSTYPE == "ldiskfs" ]] || skip "MDS is not ldiskfs"
```
-   use `skip_env` for minor environmental deficiency in developer test environment (e.g. missing binary) that \_should\_ exist in autotest:
```
    kinit || skip_env "Kerberos not installed"
```

## When adding new #include files

Includes should be ordered in the following way:

1.  linux headers
2.  libcfs headers
3.  lnet headers
4.  lustre/include/lustre/\* headers
5.  lustre/include/\*
6.  \*\_internal.h and any other "local.h" files

Each group shall be sorted alphanumerically.

The rationale for this is that Lustre is a strict superset of LNet functionality so there shouldn't be any LNet code that depends on Lustre headers, and Lustre headers should not override or otherwise conflict with kernel headers. Sorting alphabetically makes it easier to avoid duplicate header include and reduces the chance of patch conflicts if new headers are added at the end in separate patches.