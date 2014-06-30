CC ?= gcc
CFLAGS ?= -Wall -Wextra -O3

all:
	$(CC) $(CFLAGS) mandel.c -o mandel -fopenmp

clean:
	rm -fr *~ *.o mandel
