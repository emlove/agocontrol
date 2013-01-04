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
LDFLAGS	:= $(DEBUG_LDFLAGS)

INCLUDES	:= 

%.o : %.cpp
	$(CXX) $(CFLAGS) $(INCLUDES) -o $@ $<

all: agoresolver

agoresolver: agoresolver.o schema.o ../../devices/agozwave/CDataFile.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -lyaml-cpp

clean:
	rm -f agoresolver agoresolver.o schema.o ../../devices/agozwave/CDataFile.o
