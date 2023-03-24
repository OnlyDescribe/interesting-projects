#ifndef _AUXILIARY_H_
#define _AUXILIARY_H_

#include <iostream>
#include <sstream>

#include "omalloc/omAllocDecl.h"
#include "singular/coeffs/coeffs.h"
#include "singular/kernel/GBEngine/ringgb.h"
#include "singular/kernel/polys.h"
#include "singular/polys/monomials/p_polys.h"
#include "singular/polys/monomials/ring.h"
#include "singular/polys/simpleideals.h"
#include "singular/reporter/reporter.h"

static inline std::string _2S(poly a, const ring r)
{
    p_Test(a, r);
    StringSetS("");
    p_Write(a, r);

    std::stringstream ss;
    {
        char *s = StringEndS();
        ss << s;
        omFree(s);
    }

    return ss.str();
}

static inline std::string _2S(number a, const coeffs r)
{
    n_Test(a, r);
    StringSetS("");
    n_Write(a, r);

    std::stringstream ss;
    {
        char *s = StringEndS();
        ss << s;
        omFree(s);
    }

    return ss.str();
}

static inline void PrintSized(/*const*/ poly a, const ring r)
{
    std::clog << _2S(a, r) << std::endl;
}

static inline void PrintSized(/*const*/ number a, const coeffs r)
{
    std::clog << _2S(a, r) << ", of size: " << n_Size(a, r) << std::endl;
}

// inline void idShow(const ideal id, const ring lmRing, const ring tailRing)
// {
//     if (id == NULL)
//         PrintS("(NULL)");
//     else
//     {
//         // Print("Module of rank %ld,real rank %ld and %d generators.\n", id->rank,
//         //       id_RankFreeModule(id, lmRing, tailRing), IDELEMS(id));

//         int j = (id->ncols * id->nrows) - 1;
//         while ((j > 0) && (id->m[j] == NULL))
//             j--;
//         for (int i = 0; i <= j; i++)
//         {
//             Print("generator %d: ", i);
//             // p_wrp(id->m[i], lmRing, tailRing);
//             p_Write(id->m[i], lmRing, tailRing);
//             PrintLn();
//         }
//     }
// }

#endif