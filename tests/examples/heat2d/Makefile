CC ?= gcc
CFLAGS ?= -Wall -Wextra -O3 -g

all:
	@$(CC) $(CFLAGS) heat2d.c -o heat2d -fopenmp

clean:
	@rm -fr *~ *.o heat2d
