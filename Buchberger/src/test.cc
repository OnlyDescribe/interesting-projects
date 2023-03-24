#include "buchberger.h"

#include <iostream>
#include <map>
#include <sstream>
#include <vector>

// #include "factory/timing.h"
#include "factory/factory.h"
#include "resources/feResource.h"
#include "singular/coeffs/coeffs.h"
#include "singular/kernel/GBEngine/kstd1.h"
#include "singular/kernel/GBEngine/syz.h"
#include "singular/kernel/structs.h"
#include "singular/polys/monomials/p_polys.h"
#include "singular/polys/monomials/ring.h"
#include "singular/polys/simpleideals.h"

#include "auxiliary.h"

namespace test
{

// TIMING_DEFINE_PRINT(PROC_GB)

int initTest(int argc, char *argv[])
{
    assume(sizeof(long) == SIZEOF_LONG);

    if (sizeof(long) != SIZEOF_LONG)
    {
        WerrorS("Bad config.h: wrong size of long!");

        return (1);
    }
    feInitResources(argv[0]);
#if 0
    StringSetS("ressources in use (as reported by feStringAppendResources(0):\n");
    feStringAppendResources(0);

    PrintLn();
    {
        char *s = StringEndS();
        PrintS(s);
        omFree(s);
    }
#endif
    return 0;
}

ring initRing(int coeff_char, std::vector<const char *> variables, rRingOrder_t ring_order = ringorder_lp)
{
    const short N = variables.size();
    char **n = (char **)omalloc(N * sizeof(char *));
    for (int i = 0; i < variables.size(); i++)
    {
        n[i] = omStrDup(variables[i]);
    }

    const int D = 3;
    rRingOrder_t *order = (rRingOrder_t *)omAlloc0(D * sizeof(rRingOrder_t));
    int *block0 = (int *)omAlloc0(D * sizeof(int));
    int *block1 = (int *)omAlloc0(D * sizeof(int));

    // sort polynomial vectors by the monomial ordering first, then by components
    order[0] = ring_order; // monomial ordering
    block0[0] = 1;
    block1[0] = N;

    order[1] = ringorder_C; // module ordering
    block0[1] = 1;
    block1[1] = N;

    ring R = rDefault(coeff_char, N, n, D, order, block0, block1);
    return R;
}

poly initTerm(int coeff, std::map<short, int> n_exp, const ring R)
{
    poly p = p_ISet(coeff, R); // returns a polynomial representing the integer coeff
    for (const auto &i : n_exp)
    {
        p_SetExp(p, i.first, i.second, R); // set (i.first)^th exponent (i.second) for a monomial
    }
    p_Setm(p, R);
    return p;
};

int Main(int argc, char *argv[])
{
    initTest(argc, argv);

    enum Variable
    {
        w = 1,
        t = 2,
        s = 3,
        y = 4,
        x = 5,
        z = 6
    };
    ring R = initRing(0, {"w", "t", "s", "y", "x", "z"});

    ideal I = idInit(4, 1);

    auto plusTerm = [](poly &p, int coeff, std::map<short, int> n_exp, const ring &R) -> void {
        poly p1 = initTerm(coeff, n_exp, R);
        p = p_Add_q(p, p1, R);
    };

    int gen = 0;

    // st2x-st2+t
    poly p1 = initTerm(1, {{s, 1}, {t, 2}, {x, 1}}, R); // p1=st2x
    plusTerm(p1, -1, {{s, 1}, {t, 2}}, R);              // p1=st2x-st2
    plusTerm(p1, 1, {{t, 1}}, R);                       // p1=st2x-st2+t
    MATELEM(I, 1, ++gen) = p1;
    // PrintSized(p1, R);

    // st2y-st-s
    poly p2 = initTerm(1, {{s, 1}, {t, 2}, {y, 1}}, R); // p2=st2y
    plusTerm(p2, -1, {{s, 1}, {t, 1}}, R);              // p2=st2y-st
    plusTerm(p2, -1, {{s, 1}}, R);                      // p2=st2y-st-s
    MATELEM(I, 1, ++gen) = p2;
    // PrintSized(p2, R);

    // st2z-2s+2t
    poly p3 = initTerm(1, {{s, 1}, {t, 2}, {z, 1}}, R); // p2=st2z
    plusTerm(p3, -2, {{s, 1}}, R);                      // p2=st2z-2s
    plusTerm(p3, 2, {{t, 1}}, R);                       // p2=st2z-2s+2t
    MATELEM(I, 1, ++gen) = p3;
    // PrintSized(p3, R);

    // wst2-1
    poly p4 = initTerm(1, {{w, 1}, {s, 1}, {t, 2}}, R); // p2=wst2
    plusTerm(p4, -1, {}, R);                            // p2=wst2-1
    MATELEM(I, 1, ++gen) = p4;
    // PrintSized(p4, R);

    PrintS("I: \n");
    idShow(I, R, R);

    // TIMING_START(PROC_GB)
    ideal G = GroebnerBasis(I, R);
    // TIMING_END_AND_PRINT(PROC_GB, "time for experiment_01 : ")
    // TIMING_END(PROC_GB)

    PrintS("Groebner basis: \n");
    idShow(G, R, R);

    // TIMING_PRINT(PROC_GB, (char *)"time for experiment_01 : ")
    // PolyRed(p1, G, R);
    // should cleanup every belonging polynomial
    id_Delete(&I, R);
    id_Delete(&G, R);
    rDelete(R);

    PrintLn();

    return 0;
}

int GBTest(int argc, char *argv[])
{
    initTest(argc, argv);

    enum Variable
    {
        z = 1,
        y = 2,
        x = 3
    };
    ring R = initRing(0, {"z", "y", "x"});

    auto plusTerm = [](poly &p, int coeff, std::map<short, int> n_exp, const ring &R) -> void {
        poly p1 = initTerm(coeff, n_exp, R);
        p = p_Add_q(p, p1, R);
    };

    PrintS("Experiment: \n");

    ideal I = idInit(2, 1);
    int gen = 0;
    poly Q1 = initTerm(1, {{x, 2}}, R);
    plusTerm(Q1, 1, {{y, 2}}, R);
    plusTerm(Q1, 1, {{z, 2}}, R);
    plusTerm(Q1, -1, {}, R);

    MATELEM(I, 1, ++gen) = Q1;
    // PrintSized(Q1, R);

    poly Q2 = initTerm(1, {{x, 1}, {y, 1}, {z, 1}}, R);
    plusTerm(Q2, -1, {}, R);

    MATELEM(I, 1, ++gen) = Q2;
    // PrintSized(Q2, R);
    PrintS("I: \n");
    idShow(I, R, R);

    // make R the default ring:
    // rChangeCurrRing(R);

    ideal G = GroebnerBasis(I, R);
    // PrintS("G: \n");
    // idShow(G, R, R);

    id_Delete(&I, R);
    return 0;
}

int GBTest2(int argc, char *argv[])
{
    initTest(argc, argv);

    enum Variable
    {
        y = 2,
        x = 1
    };
    ring R = initRing(0, {"x", "y"});

    auto plusTerm = [](poly &p, int coeff, std::map<short, int> n_exp, const ring &R) -> void {
        poly p1 = initTerm(coeff, n_exp, R);
        p = p_Add_q(p, p1, R);
    };

    PrintS("Experiment: \n");

    ideal I = idInit(2, 1);
    int gen = 0;
#if 1
    poly Q1 = initTerm(4, {{y, 2}}, R);
    plusTerm(Q1, -2, {{y, 1}}, R);

    MATELEM(I, 1, ++gen) = Q1;
    // PrintSized(Q1, R);

    poly Q2 = initTerm(3, {{x, 1}, {y, 1}}, R);
    plusTerm(Q2, 4, {{y, 2}}, R);
    plusTerm(Q2, 6, {}, R);

    MATELEM(I, 1, ++gen) = Q2;
    // PrintSized(Q2, R);
#endif

#if 0
    poly Q1 = initTerm(4, {{y, 2}}, R);
    plusTerm(Q1, -2, {{y, 1}}, R);

    MATELEM(I, 1, ++gen) = Q1;
    // PrintSized(Q1, R);

    poly Q2 = initTerm(3, {{x, 1}, {y, 1}}, R);
    plusTerm(Q2, 4, {{y, 2}}, R);
    plusTerm(Q2, 6, {}, R);

    MATELEM(I, 1, ++gen) = Q2;
    // PrintSized(Q2, R);
#endif
    PrintS("I: \n");
    idShow(I, R, R);

    // make R the default ring:
    // rChangeCurrRing(R);

    ideal G = GroebnerBasis(I, R);
    // PrintS("G: \n");
    // idShow(G, R, R);

    id_Delete(&I, R);
    return 0;
}

int ReduceTest(int argc, char *argv[])
{
    initTest(argc, argv);

    enum Variable
    {
        x = 1,
        y = 2
    };

    ring R = initRing(0, {"x", "y"});

    auto plusTerm = [](poly &p, int coeff, std::map<short, int> n_exp, const ring &R) -> void {
        poly p1 = initTerm(coeff, n_exp, R);
        p = p_Add_q(p, p1, R);
    };

#if 1
    {
        PrintS("Experiment 1:\n");
        poly F = initTerm(1, {{x, 1}, {y, 2}}, R);
        plusTerm(F, -1, {{x, 1}}, R);
        PrintS("F: ");
        PrintSized(F, R);

        ideal I = idInit(2, 1);
        int gen = 0;
        poly Q1 = initTerm(1, {{x, 1}, {y, 1}}, R);
        plusTerm(Q1, 1, {}, R);
        MATELEM(I, 1, ++gen) = Q1;
        // PrintSized(Q1, R);

        poly Q2 = initTerm(1, {{y, 2}}, R);
        plusTerm(Q2, -1, {}, R);
        MATELEM(I, 1, ++gen) = Q2;
        // PrintSized(Q2, R);
        PrintS("I:\n");
        idShow(I, R, R);

        // // make R the default ring:
        // rChangeCurrRing(R);
        poly norm_form;
        ideal Q;
        std::tie(norm_form, Q) = PolyRed(F, I, R);
        id_Delete(&Q, R);

        // PrintSized(norm_form, R);
        id_Delete(&I, R);
    }
#endif

#if 1
    {
        PrintS("Experiment 2:\n");
        poly F = initTerm(1, {{x, 2}, {y, 3}}, R);
        plusTerm(F, 2, {{x, 1}, {y, 2}}, R);
        plusTerm(F, 1, {{x, 1}}, R);
        plusTerm(F, 1, {}, R);
        PrintS("F: ");
        PrintSized(F, R);

        ideal I = idInit(2, 1);
        int gen = 0;
        poly Q1 = initTerm(2, {{y, 2}}, R);
        MATELEM(I, 1, ++gen) = Q1;
        // PrintSized(Q1, R);

        poly Q2 = initTerm(1, {{x, 1}, {y, 1}}, R);
        plusTerm(Q2, 1, {}, R);
        MATELEM(I, 1, ++gen) = Q2;
        // PrintSized(Q2, R);
        PrintS("I:\n");
        idShow(I, R, R);

        // // make R the default ring:
        // rChangeCurrRing(R);
        poly norm_form;
        ideal Q;
        std::tie(norm_form, Q) = PolyRed(F, I, R);
        id_Delete(&Q, R);

        // PrintSized(norm_form, R);

        id_Delete(&I, R);
    }
#endif
    rDelete(R);
    return 0;
}

int SPolyTest(int argc, char *argv[])
{
    initTest(argc, argv);

    enum Variable
    {
        x = 1,
        y = 2
    };

    ring R = initRing(0, {"x", "y"}, ringorder_lp);

    auto plusTerm = [](poly &p, int coeff, std::map<short, int> n_exp, const ring &R) -> void {
        poly p1 = initTerm(coeff, n_exp, R);
        p = p_Add_q(p, p1, R);
    };
    // rWrite(R);
    poly F = initTerm(2, {{x, 4}, {y, 1}}, R);
    plusTerm(F, -1, {{x, 2}, {y, 1}}, R);
    plusTerm(F, 2, {{x, 1}}, R);
    PrintS("F:\n");
    PrintSized(F, R);

    poly G = initTerm(4, {{x, 3}, {y, 2}}, R);
    plusTerm(G, 1, {{y, 1}}, R);
    PrintS("G:\n");
    PrintSized(G, R);

    // make R the default ring:
    // rChangeCurrRing(R);

    // poly H = plain_spoly(F, G);
    poly S = SPoly(F, G, R);
    PrintS("SPoly:\n");
    PrintSized(S, R);
    return 0;
}

} // namespace test