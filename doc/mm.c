#include <stdlib.h>
#include <stdio.h>
#include <time.h>

int main()
{
  int n = atoi(getenv("N"));

  double *a = malloc(n * sizeof(double));
  double *b = malloc(n * sizeof(double));
  double *c = calloc(n, sizeof(double));

  int i,j,k;
  
  srand(time(NULL));
  for (i = 0; i < n; i++)
    a[i] = rand();
  for (i = 0; i < n; i++)
    b[i] = rand();

  for (i = 0; i < n; i++)
    for (j = 0; j < n; j++)
      for (k = 0; k < n; k++)
	c[i * n + j] += 
	  a[i * n + k] * b[k * n + j];

  printf("N=%d\n", n);

  return EXIT_SUCCESS;
}
