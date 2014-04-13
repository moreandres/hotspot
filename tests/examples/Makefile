CC ?= gcc
CFLAGS ?= -Wall -Wextra -O3

all:
	$(CC) $(CFLAGS) matrix.c -o matrix -fopenmp
	$(CC) $(CFLAGS) heat2d.c -o heat2d -fopenmp
	$(CC) $(CFLAGS) mandel.c -o mandel -fopenmp

clean:
	rm -fr *~ *.o matrix heat2d mandel
