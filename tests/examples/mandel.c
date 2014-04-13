#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define X_RESN 1024
#define Y_RESN 1024
#define X_MIN -2.0
#define X_MAX 2.0
#define Y_MIN -2.0
#define Y_MAX 2.0

typedef struct complextype
{
  float real, imag;
} Compl;

int main()
{
  int i, j, k;
  Compl z, c;
  float lensq, temp;
  int iters;
  int res[X_RESN][Y_RESN];

  iters = 1024;
  if (getenv("N"))
    iters = atoi(getenv("N"));

#pragma omp parallel for shared(res, iters) private(i, j, z, c, k, temp, lensq)
  for (i = 0; i < Y_RESN; i++)
    for (j = 0; j < X_RESN; j++)
      {
	z.real = z.imag = 0.0;
	c.real = X_MIN + j * (X_MAX - X_MIN) / X_RESN;
	c.imag = Y_MAX - i * (Y_MAX - Y_MIN) / Y_RESN;
	k = 0;

	do
	  {
	    temp = z.real * z.real - z.imag * z.imag + c.real;
	    z.imag = 2.0 * z.real * z.imag + c.imag;
	    z.real = temp;
	    lensq = z.real * z.real + z.imag * z.imag;
	    k++;
	  }
	while (lensq < 4.0 && k < iters);

	if (k >= iters)
	  res[i][j] = 0;
	else
	  res[i][j] = 1;

      }

  assert(res[0][0]);

  return 0;
}
