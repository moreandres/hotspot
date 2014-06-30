#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define CRESN   302		/* x, y resolution */
#define RESN    300
#define MAX_COLORS 8
#define MAX_HEAT  20.0

double solution[2][CRESN][CRESN], diff_constant;
int cur_gen, next_gen;

double sim_time, final = 10000.0, time_step = 0.1, diff = 10000.0;

void compute_one_iteration();
void setup();

int main()
{
  final = 1024;
  if (getenv("N"))
    final = atoi(getenv("N"));

  int temp;

  setup ();

  for (sim_time = 0; sim_time < final; sim_time += time_step)
    {
      compute_one_iteration (sim_time);
      temp = cur_gen;
      cur_gen = next_gen;
      next_gen = temp;
    }

  return 0;
}

void setup()
{
  int i, j;

#pragma omp parallel for shared(solution) private(i,j)
  for (i = 0; i < CRESN; i++)
    for (j = 0; j < CRESN; j++)
      solution[0][i][j] = solution[1][i][j] = 0.0;

  cur_gen = 0;
  next_gen = 1;
  diff_constant = diff * time_step / ((float) RESN * (float) RESN);
}

void compute_one_iteration()
{
  int i, j;
  /* set boundary values */
  for (i = 0; i < CRESN; i++)
    {
      if (i < 256 || i > 768)
	solution[cur_gen][i][0] = solution[cur_gen][i][1];
      else
	solution[cur_gen][i][0] = MAX_HEAT;
    }
  for (i = 0; i < CRESN; i++)
    {
      solution[cur_gen][i][CRESN - 1] = solution[cur_gen][i][CRESN - 2];
    }
  for (i = 0; i < CRESN; i++)
    {
      solution[cur_gen][0][i] = solution[cur_gen][1][i];
      solution[cur_gen][CRESN - 1][i] = solution[cur_gen][CRESN - 2][i];
    }
  /* corners ? */

#pragma omp parallel for shared(solution,cur_gen,next_gen,diff_constant) private(i,j)
  for (i = 1; i <= RESN; i++)
    for (j = 1; j <= RESN; j++)
      solution[next_gen][i][j] = solution[cur_gen][i][j] +
	(solution[cur_gen][i + 1][j] +
	 solution[cur_gen][i - 1][j] +
	 solution[cur_gen][i][j + 1] +
	 solution[cur_gen][i][j - 1] -
	 4.0 * solution[cur_gen][i][j]) * diff_constant;
}
