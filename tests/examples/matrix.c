#include <stdlib.h>
#include <stdio.h>

int main()
{
  int size = 1024;
  if (getenv("N"))
    size = atoi(getenv("N"));

  float *a = malloc(sizeof(float) * size * size);
  float *b = malloc(sizeof(float) * size * size);
  float *c = malloc(sizeof(float) * size * size);
  
  int i, j, k;

  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      a[i+j*size] = (float) (i + j);
      b[i+j*size] = (float) (i - j);
      c[i+j*size] = 0.0f;
    }
  }

#pragma omp parallel for shared(a,b,c) 
  for (i = 0; i < size; ++i) {
    for (j = 0; j < size; ++j) {
      for (k = 0; k < size; ++k) {
	c[i+j*size] += a[i+k*size] * b[k+j*size];
      }
    }
  }

  return 0;
}
