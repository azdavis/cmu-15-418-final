#include <stdio.h>
#include "lib/test_ispc.h"

int main(void) {
    int x = 2;
    int y = 3;
    printf("func(%d, %d) = %d\n", x, y, func(x, y));
    return 0;
}
