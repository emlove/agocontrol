#

.SUFFIXES:	.cpp .o .a .s

CC     := gcc
CXX    := g++
LD     := g++
AR     := ar rc
RANLIB := ranlib

DEBUG_CFLAGS    := -Wall -Wno-format -g -DDEBUG
RELEASE_CFLAGS  := -Wall -Wno-unknown-pragmas -Wno-format -O3

DEBUG_LDFLAGS	:= -g

# Change for DEBUG or RELEASE
CFLAGS	:= -c $(DEBUG_CFLAGS)
LDFLAGS	:= $(DEBUG_LDFLAGS) -L../../shared

INCLUDES	:= -I../../shared

%.o : %.cpp
	$(CXX) $(CFLAGS) $(INCLUDES) -o $@ $<

all: enoceanlib agoEnOcean

enoceanlib:
	$(CC) -c -fPIC -D_GNU_SOURCE -o cssl.o libEnOcean/cssl.c
	$(CC) -c -fPIC -o EnOceanPort.o libEnOcean/EnOceanPort.c
	$(CC) -c -fPIC -o TCM120.o libEnOcean/TCM120.c

agoEnOcean: agoEnOcean.o
	$(LD) -o $@ cssl.o EnOceanPort.o TCM120.o $(LDFLAGS) $^ -lagoclient

clean:
	rm -f agoEnOcean agoEnOcean.o TCM120.o EnOceanPort.o cssl.o
