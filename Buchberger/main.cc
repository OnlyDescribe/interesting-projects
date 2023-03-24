// #include "kernel/GBEngine/kutil.h"
#include <iostream>
#include <sstream>

#include "coeffs/coeffs.h"
#include "factory/factory.h"
#include "kernel/GBEngine/kstd1.h"
#include "kernel/GBEngine/syz.h"
#include "kernel/structs.h"
#include "polys/monomials/p_polys.h"
#include "polys/monomials/ring.h"
#include "polys/simpleideals.h"
#include "resources/feResource.h"

#include "auxiliary.h"

namespace test
{
int Main(int argc, char *argv[]);
int SPolyTest(int argc, char *argv[]);
int ReduceTest(int argc, char *argv[]);
int GBTest(int argc, char *argv[]);
int GBTest2(int argc, char *argv[]);
} // namespace test

enum
{
    Main,
    SPolyTest,
    ReduceTest,
    GBTest,
    GBTest2
};

int main(int argc, char *argv[])
{

    int test = Main;
    // int test = GBTest;

    switch (test)
    {
    case Main:
        test::Main(argc, argv);
        break;
    case SPolyTest:
        test::SPolyTest(argc, argv);
        break;
    case ReduceTest:
        test::ReduceTest(argc, argv);
        break;
    case GBTest:
        test::GBTest(argc, argv);
        break;
    case GBTest2:
        test::GBTest2(argc, argv);
        break;
    default:
        std::cout << "Something may be wrong. " << std::endl;
    }

    return 0;
}
