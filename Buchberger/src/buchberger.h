#include <algorithm>
#include <deque>
#include <tuple>
#include <vector>

#include "singular/kernel/GBEngine/kutil.h"
#include "singular/kernel/ideals.h"
#include "singular/kernel/polys.h"
#include "singular/polys/simpleideals.h"

#include "auxiliary.h"

// assumes that LM(a) = LM(b)*m, for some monomial m,
// returns the multiplicant m,
inline poly MDivide(poly a, poly b, const ring r)
{
    poly result = p_ISet(1, r);

    for (int i = (int)r->N; i; i--) // N is the number of vars
        p_SetExp(result, i, p_GetExp(a, i, r) - p_GetExp(b, i, r), r);
    p_SetComp(result, p_GetComp(a, r) - p_GetComp(b, r), r); // set component
    p_Setm(result, r);
    return result;
}

// Find multiplicant m, and index i , such that
// LT(f) = m * LT(G[i]) has a solution(if i=-1 then it means f is reduced)
inline std::pair<poly, int> FindRingSolver(poly f, ideal G, ring r)
{
    if (f == nullptr)
        return std::make_pair(nullptr, -1);

    poly g, m;
    number cf, cg, coeff;

    while (f != nullptr)
    {
        for (int i = 0; i < idElem(G); i++)
        {
            g = G->m[i];
            if (g != nullptr && p_LmDivisibleBy(g, f, r))
            {
                m = MDivide(f, g, r);
                cf = n_Copy(pGetCoeff(f), r->cf);
                cg = n_Copy(pGetCoeff(g), r->cf);
                coeff = n_Div(cf, cg, r->cf);
                p_SetCoeff(m, coeff, r);

                // PrintS("m in FindRingSolver: ");
                // p_Write(m, r);

                n_Delete(&cf, r->cf);
                n_Delete(&cg, r->cf);
                return std::make_pair(m, i);
            }
        }
        // Maybe it's not necessary? I think it's also correct to reduce f only by HT/HM(f).
        f = f->next;
    }
    return std::make_pair(nullptr, -1);
}

// not destroy f and G
inline std::pair<poly, ideal> PolyRed(poly f, ideal G, ring r)
{
    // If f = 0, then normal form is also 0
    if (f == nullptr)
    {
        return std::make_pair(nullptr, nullptr);
    }
    poly m, g;
    int index;

    ideal Q = idInit(idElem(G), 1);
    poly nform = p_Copy(f, r);
    for (int i = 0, gen = 0; i < idElem(G); i++)
    {
        poly q = nullptr;
        MATELEM(Q, 1, ++gen) = q;
    }

    std::tie(m, index) = FindRingSolver(nform, G, r);

#if DEBUG
    int c = 1;
    PrintS("poly to reduce: ");
    p_Write(nform, r);
#endif
    while (index != -1 && nform != nullptr) // if f is not reduced and f != 0
    {
        g = G->m[index];

#if DEBUG
        {
            Print("%d-step PolyRed\n", c++);
            PrintS("poly in G: ");
            p_Write(g, r);
            PrintS("multiplicant: ");
            p_Write(m, r);
            // PrintLn();
        }
#endif

        nform = p_Sub(nform, pp_Mult_mm(g, m, r), r); // reduce F modulo g
        Q->m[index] = p_Add_q(Q->m[index], m, r);

#if DEBUG
        PrintS("reduction => ");
        p_Write(nform, r);
        PrintLn();
#endif

        std::tie(m, index) = FindRingSolver(nform, G, r);
    }
#if DEBUG
    PrintS("normal form: ");
    p_Write(nform, r);
    PrintS("ideal Q: \n");
    idShow(Q, r, r);
#endif
    return std::make_pair(nform, Q);
}

// get S-polynomial(do not destroy f and g)
inline poly SPoly(poly f, poly g, ring r)
{
    // get fm = LCM(LM(f), LM(g))/LM(f)
    //     gm = LCM(LM(f), LM(g))/LM(g)
    poly fm, gm;
    k_GetLeadTerms(f, g, r, fm, gm, r);
    // set fm's coeff is HC(g)
    //     gm's coeff is HC(f)
    // Leads to coefficient expansion, it's better to use gcd and zero divisors
    number cf = n_Copy(pGetCoeff(f), r->cf), cg = n_Copy(pGetCoeff(g), r->cf);
    p_SetCoeff(fm, cg, r);
    p_SetCoeff(gm, cf, r);
    // S-Polynomial
    poly sp = p_Sub(pp_Mult_mm(f, fm, r), pp_Mult_mm(g, gm, r), r);

    p_Delete(&fm, r);
    p_Delete(&gm, r);
    return sp;
}

inline ideal GroebnerBasis(ideal F, ring r)
{
    ideal G = id_Copy(F, r);
    // std::vector<std::pair<poly, poly>> L;
    std::deque<std::pair<poly, poly>> L;
    for (int i = 0; i < idElem(G); i++)
    {
        for (int j = i + 1; j < idElem(G); j++)
        {
            if (G->m[i] != nullptr && G->m[j] != nullptr)
            {
                L.push_back(std::make_pair(G->m[i], G->m[j]));
            }
        }
    }
    poly nform;
    ideal Q;
    std::pair<poly, poly> l;

#if defined(DEBUG)
    int count = 1;
#endif

    while (!L.empty())
    {
        // l = L.back(); // maybe front is better????
        l = L.front();

#if defined(DEBUG)
        PrintS("/* ----------------------------------------------------------------- */\n");
        std::cout << "iteration: " << count++ << std::endl;
        std::cout << "L.size(): " << L.size() << std::endl;

        PrintS("\nG: \n");
        idShow(G, r, r);

        PrintS("l.first: ");
        PrintSized(l.first, r);
        PrintS("l.second: ");
        PrintSized(l.second, r);
        PrintS("SPoly: ");
        PrintSized(SPoly(l.first, l.second, r), r);
#endif

        std::tie(nform, Q) = PolyRed(SPoly(l.first, l.second, r), G, r);
        id_Delete(&Q, r);

        // L.pop_back(); // maybe pop_front is better?
        L.pop_front();

        // if (!(p_IsConstant(R, r) && n_IsZero(p_GetCoeff(R, r), r->cf)))
        if (!(nform == 0))
        {
            for (int i = 0; i < idElem(G); i++)
            {
                if (G->m[i] != nullptr)
                {
                    L.push_back(std::make_pair(G->m[i], nform));
                }
            }
            idInsertPoly(G, nform);
        }
    }

#if defined(DEBUG)
    PrintS("/* ----------------------------------------------------------------- */\n");
    PrintS("Groebner basis: \n");
    idShow(G, r, r);
#endif

    return G;
}
